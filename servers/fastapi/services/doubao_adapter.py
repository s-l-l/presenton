import asyncio
import json
import re
from typing import AsyncGenerator, List, Optional, Dict, Any, Iterator
from fastapi import HTTPException

from models.llm_message import (
    LLMMessage,
    LLMSystemMessage,
    LLMUserMessage,
    OpenAIAssistantMessage,
    OpenAIToolCallMessage
)
from models.llm_tool_call import OpenAIToolCall, OpenAIToolCallFunction
from models.llm_tools import LLMDynamicTool, LLMTool
from utils.get_env import get_doubao_api_key_env, get_disable_thinking_env
from utils.schema_utils import ensure_strict_json_schema, ensure_array_schemas_have_items
from utils.parsers import parse_bool_or_none
from utils.dummy_functions import do_nothing_async
import dirtyjson

class DoubaoAdapter:
    def __init__(self, client):
        self.api_key = get_doubao_api_key_env()
        if not self.api_key:
            raise HTTPException(
                status_code=400,
                detail="Doubao API Key is not set",
            )
        try:
            from volcenginesdkarkruntime import Ark
        except ModuleNotFoundError as e:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Doubao SDK is not installed. Please install "
                    "'volcengine-python-sdk[ark]' and restart the service."
                ),
            ) from e
        # Initialize the Ark client
        self.ark_client = Ark(api_key=self.api_key)
        self.client = client

    @property
    def tool_calls_handler(self):
        return self.client.tool_calls_handler

    def disable_thinking(self) -> bool:
        return parse_bool_or_none(get_disable_thinking_env()) or False

    def _prepare_messages(self, messages: List[LLMMessage]) -> List[dict]:
        return [message.model_dump(exclude_none=True) for message in messages]

    @staticmethod
    def _next_chunk_or_none(stream: Iterator[Any]) -> Any | None:
        """Read next stream chunk without leaking StopIteration into Future."""
        try:
            return next(stream)
        except StopIteration:
            return None

    @staticmethod
    def _parse_json_object(raw: str) -> dict | None:
        if not raw:
            return None
        candidates: list[str] = [raw]

        # Prefer fenced json payload if present.
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, flags=re.IGNORECASE)
        if fence_match:
            candidates.append(fence_match.group(1))

        # Try from first "{" as a fallback when model adds prose around JSON.
        start = raw.find("{")
        if start >= 0:
            candidates.append(raw[start:])

        for candidate in candidates:
            try:
                parsed = dirtyjson.loads(candidate)
                if isinstance(parsed, dict):
                    return dict(parsed)
            except Exception:
                continue
        return None

    async def generate(
        self,
        model: str,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        depth: int = 0,
    ) -> str | None:
        kwargs = {
            "model": model,
            "messages": self._prepare_messages(messages),
            "stream": False,
        }
        
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools:
            kwargs["tools"] = tools
        if self.disable_thinking():
            kwargs["thinking"] = {"type": "disabled"}

        try:
            print(f"DoubaoAdapter.generate: Sending request to Doubao (Ark SDK) with model={model}")
            # Run the synchronous Ark client call in a thread executor
            response = await asyncio.to_thread(
                self.ark_client.chat.completions.create, **kwargs
            )
            
            if not response.choices:
                return None

            choice = response.choices[0]
            message = choice.message
            content = message.content
            tool_calls_data = message.tool_calls

            if tool_calls_data:
                parsed_tool_calls = [
                    OpenAIToolCall(
                        id=tc.id,
                        type=tc.type,
                        function=OpenAIToolCallFunction(
                            name=tc.function.name,
                            arguments=tc.function.arguments,
                        ),
                    )
                    for tc in tool_calls_data
                ]
                tool_call_messages = await self.tool_calls_handler.handle_tool_calls_openai(
                    parsed_tool_calls
                )
                assistant_message = OpenAIAssistantMessage(
                    role="assistant",
                    content=content,
                    tool_calls=[tc.model_dump() for tc in parsed_tool_calls],
                )
                new_messages = [
                    *messages,
                    assistant_message,
                    *tool_call_messages,
                ]
                return await self.generate(
                    model=model,
                    messages=new_messages,
                    max_tokens=max_tokens,
                    tools=tools,
                    depth=depth + 1,
                )

            return content

        except Exception as e:
            print(f"DoubaoAdapter.generate: Request failed - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Doubao API error: {str(e)}")

    async def generate_structured(
        self,
        model: str,
        messages: List[LLMMessage],
        response_format: dict,
        strict: bool = False,
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        depth: int = 0,
    ) -> dict | None:
        response_schema = response_format
        all_tools = [*tools] if tools else []

        if strict and depth == 0:
            response_schema = ensure_strict_json_schema(
                response_schema,
                path=(),
                root=response_schema,
            )
        response_schema = ensure_array_schemas_have_items(response_schema)

        # Ark structured output is enforced via tool-calling in this adapter.
        use_tool_calls = True

        if depth == 0:
            all_tools.append(
                self.tool_calls_handler.parse_tool_openai(
                    LLMDynamicTool(
                        name="ResponseSchema",
                        description="Provide response to the user",
                        parameters=response_schema,
                        handler=do_nothing_async,
                    ),
                    strict=strict,
                )
            )

        kwargs = {
            "model": model,
            "messages": self._prepare_messages(messages),
            "stream": True, # Use streaming to prevent timeouts for long generations
        }

        if all_tools:
            kwargs["tools"] = all_tools
            
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        disable_thinking = self.disable_thinking()
        print(
            f"DoubaoAdapter.generate_structured: disable_thinking={disable_thinking} "
            f"(DISABLE_THINKING={get_disable_thinking_env()})"
        )
        print("disable_thinking:", disable_thinking)
        if disable_thinking:
            kwargs["thinking"] = {"type": "disabled"}

        final_content = ""
        tool_calls: List[OpenAIToolCall] = []
        current_index = 0
        current_id = None
        current_name = None
        current_arguments = None
        has_response_schema_tool_call = False

        try:
            print(f"DoubaoAdapter.generate_structured: Sending request to Doubao (Ark SDK)")
            print(f"DoubaoAdapter.generate_structured: kwargs keys={list(kwargs.keys())}")
            # Create stream in thread
            stream = await asyncio.to_thread(
                self.ark_client.chat.completions.create, **kwargs
            )

            # Iterate stream in thread-safe way
            while True:
                try:
                    chunk = await asyncio.to_thread(self._next_chunk_or_none, stream)
                    if chunk is None:
                        break
                    if not chunk.choices:
                        continue
                        
                    delta = chunk.choices[0].delta
                    
                    if delta.content:
                        final_content += delta.content
                        
                    if delta.tool_calls:
                        tc_chunk = delta.tool_calls[0]
                        tool_index = tc_chunk.index
                        tool_id = tc_chunk.id
                        tool_name = tc_chunk.function.name
                        tool_arguments = tc_chunk.function.arguments

                        if current_index != tool_index:
                            tool_calls.append(
                                OpenAIToolCall(
                                    id=current_id,
                                    type="function",
                                    function=OpenAIToolCallFunction(
                                        name=current_name,
                                        arguments=current_arguments,
                                    ),
                                )
                            )
                            current_index = tool_index
                            current_id = tool_id
                            current_name = tool_name
                            current_arguments = tool_arguments
                        else:
                            current_name = tool_name or current_name
                            current_id = tool_id or current_id
                            if current_arguments is None:
                                current_arguments = tool_arguments
                            elif tool_arguments:
                                current_arguments += tool_arguments

                        if current_name == "ResponseSchema":
                            has_response_schema_tool_call = True

                except Exception as e:
                    print(f"DoubaoAdapter.generate_structured: Stream iteration error - {str(e)}")
                    break

        except Exception as e:
            print(f"DoubaoAdapter.generate_structured: Request failed - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Doubao API error: {str(e)}")

        if current_id is not None:
            tool_calls.append(
                OpenAIToolCall(
                    id=current_id,
                    type="function",
                    function=OpenAIToolCallFunction(
                        name=current_name,
                        arguments=current_arguments,
                    ),
                )
            )

        content = final_content
        if tool_calls:
            for tc in tool_calls:
                if tc.function.name == "ResponseSchema":
                    content = tc.function.arguments
                    break

            if not has_response_schema_tool_call:
                parsed_tool_calls = tool_calls
                tool_call_messages = await self.tool_calls_handler.handle_tool_calls_openai(
                    parsed_tool_calls
                )
                assistant_message = OpenAIAssistantMessage(
                    role="assistant",
                    content=final_content,
                    tool_calls=[tc.model_dump() for tc in parsed_tool_calls],
                )
                new_messages = [
                    *messages,
                    assistant_message,
                    *tool_call_messages,
                ]
                content = await self.generate_structured(
                    model=model,
                    messages=new_messages,
                    response_format=response_schema,
                    strict=strict,
                    max_tokens=max_tokens,
                    tools=tools,
                    depth=depth + 1,
                )

        if content:
            if depth == 0 and isinstance(content, str):
                parsed = self._parse_json_object(content)
                if parsed is not None:
                    return parsed
                preview = content[:800].replace("\n", "\\n")
                print(
                    "DoubaoAdapter.generate_structured: invalid structured raw="
                    f"{preview}"
                )
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Doubao returned invalid structured output "
                        "(expected JSON object for response schema)."
                    ),
                )
            return content
        return None

    async def stream(
        self,
        model: str,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        depth: int = 0,
    ) -> AsyncGenerator[str, None]:
        kwargs = {
            "model": model,
            "messages": self._prepare_messages(messages),
            "stream": True,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools:
            kwargs["tools"] = tools
        if self.disable_thinking():
            kwargs["thinking"] = {"type": "disabled"}

        tool_calls: List[OpenAIToolCall] = []
        current_index = 0
        current_id = None
        current_name = None
        current_arguments = None

        try:
            # Create stream in thread
            stream = await asyncio.to_thread(
                self.ark_client.chat.completions.create, **kwargs
            )

            while True:
                try:
                    chunk = await asyncio.to_thread(self._next_chunk_or_none, stream)
                    if chunk is None:
                        break
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    
                    content_chunk = delta.content
                    if content_chunk:
                        yield content_chunk
                        
                    if delta.tool_calls:
                        tc_chunk = delta.tool_calls[0]
                        tool_index = tc_chunk.index
                        tool_id = tc_chunk.id
                        tool_name = tc_chunk.function.name
                        tool_arguments = tc_chunk.function.arguments

                        if current_index != tool_index:
                            tool_calls.append(
                                OpenAIToolCall(
                                    id=current_id,
                                    type="function",
                                    function=OpenAIToolCallFunction(
                                        name=current_name,
                                        arguments=current_arguments,
                                    ),
                                )
                            )
                            current_index = tool_index
                            current_id = tool_id
                            current_name = tool_name
                            current_arguments = tool_arguments
                        else:
                            current_name = tool_name or current_name
                            current_id = tool_id or current_id
                            if current_arguments is None:
                                current_arguments = tool_arguments
                            elif tool_arguments:
                                current_arguments += tool_arguments

                except Exception as e:
                    # Log error but don't crash stream if possible
                    print(f"DoubaoAdapter.stream: Error iterating stream - {str(e)}")
                    break

            if current_id is not None:
                tool_calls.append(
                    OpenAIToolCall(
                        id=current_id,
                        type="function",
                        function=OpenAIToolCallFunction(
                            name=current_name,
                            arguments=current_arguments,
                        ),
                    )
                )

            if tool_calls:
                tool_call_messages = await self.tool_calls_handler.handle_tool_calls_openai(
                    tool_calls
                )
                new_messages = [
                    *messages,
                    OpenAIAssistantMessage(
                        role="assistant",
                        content=None,
                        tool_calls=[tc.model_dump() for tc in tool_calls],
                    ),
                    *tool_call_messages,
                ]
                async for chunk in self.stream(
                    model=model,
                    messages=new_messages,
                    max_tokens=max_tokens,
                    tools=tools,
                    depth=depth + 1,
                ):
                    yield chunk

        except Exception as e:
            print(f"DoubaoAdapter.stream: Request failed - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Doubao API error: {str(e)}")

    async def stream_structured(
        self,
        model: str,
        messages: List[LLMMessage],
        response_format: dict,
        strict: bool = False,
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
        depth: int = 0,
    ) -> AsyncGenerator[str, None]:
        response_schema = response_format
        all_tools = [*tools] if tools else []

        if strict and depth == 0:
            response_schema = ensure_strict_json_schema(
                response_schema,
                path=(),
                root=response_schema,
            )
        response_schema = ensure_array_schemas_have_items(response_schema)

        # Ark structured output is enforced via tool-calling in this adapter.
        use_tool_calls = True

        if depth == 0:
            all_tools.append(
                self.tool_calls_handler.parse_tool_openai(
                    LLMDynamicTool(
                        name="ResponseSchema",
                        description="Provide response to the user",
                        parameters=response_schema,
                        handler=do_nothing_async,
                    ),
                    strict=strict,
                )
            )

        kwargs = {
            "model": model,
            "messages": self._prepare_messages(messages),
            "stream": True,
        }
        
        if all_tools:
            kwargs["tools"] = all_tools
        
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if self.disable_thinking():
            kwargs["thinking"] = {"type": "disabled"}

        tool_calls: List[OpenAIToolCall] = []
        current_index = 0
        current_id = None
        current_name = None
        current_arguments = None
        has_response_schema_tool_call = False

        try:
            stream = await asyncio.to_thread(
                self.ark_client.chat.completions.create, **kwargs
            )

            while True:
                try:
                    chunk = await asyncio.to_thread(self._next_chunk_or_none, stream)
                    if chunk is None:
                        break
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                        
                    content_chunk = delta.content
                    if content_chunk and not use_tool_calls:
                        yield content_chunk

                    if delta.tool_calls:
                        tc_chunk = delta.tool_calls[0]
                        tool_index = tc_chunk.index
                        tool_id = tc_chunk.id
                        tool_name = tc_chunk.function.name
                        tool_arguments = tc_chunk.function.arguments

                        if current_index != tool_index:
                            tool_calls.append(
                                OpenAIToolCall(
                                    id=current_id,
                                    type="function",
                                    function=OpenAIToolCallFunction(
                                        name=current_name,
                                        arguments=current_arguments,
                                    ),
                                )
                            )
                            current_index = tool_index
                            current_id = tool_id
                            current_name = tool_name
                            current_arguments = tool_arguments
                        else:
                            current_name = tool_name or current_name
                            current_id = tool_id or current_id
                            if current_arguments is None:
                                current_arguments = tool_arguments
                            elif tool_arguments:
                                current_arguments += tool_arguments

                        if current_name == "ResponseSchema":
                            if tool_arguments:
                                yield tool_arguments
                            has_response_schema_tool_call = True

                except Exception as e:
                    print(f"DoubaoAdapter.stream_structured: Error iterating stream - {str(e)}")
                    break

            if current_id is not None:
                tool_calls.append(
                    OpenAIToolCall(
                        id=current_id,
                        type="function",
                        function=OpenAIToolCallFunction(
                            name=current_name,
                            arguments=current_arguments,
                        ),
                    )
                )

            if tool_calls and not has_response_schema_tool_call:
                tool_call_messages = await self.tool_calls_handler.handle_tool_calls_openai(
                    tool_calls
                )
                new_messages = [
                    *messages,
                    OpenAIAssistantMessage(
                        role="assistant",
                        content=None,
                        tool_calls=[tc.model_dump() for tc in tool_calls],
                    ),
                    *tool_call_messages,
                ]
                async for chunk in self.stream_structured(
                    model=model,
                    messages=new_messages,
                    response_format=response_schema,
                    strict=strict,
                    max_tokens=max_tokens,
                    tools=tools,
                    depth=depth + 1,
                ):
                    yield chunk

        except Exception as e:
            print(f"DoubaoAdapter.stream_structured: Request failed - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Doubao API error: {str(e)}")

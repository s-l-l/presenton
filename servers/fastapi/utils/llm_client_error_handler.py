from fastapi import HTTPException
from anthropic import APIError as AnthropicAPIError
from openai import APIError as OpenAIAPIError
from google.genai.errors import APIError as GoogleAPIError
import traceback


def handle_llm_client_exceptions(e: Exception) -> HTTPException:
    traceback.print_exc()
    if isinstance(e, HTTPException):
        print(
            f"LLM_ERROR_HTTP: status={e.status_code}, detail={e.detail}"
        )
        return e
    if isinstance(e, OpenAIAPIError):
        err = HTTPException(status_code=500, detail=f"OpenAI API error: {e.message}")
        print(f"LLM_ERROR_HTTP: status={err.status_code}, detail={err.detail}")
        return err
    if isinstance(e, GoogleAPIError):
        err = HTTPException(status_code=500, detail=f"Google API error: {e.message}")
        print(f"LLM_ERROR_HTTP: status={err.status_code}, detail={err.detail}")
        return err
    if isinstance(e, AnthropicAPIError):
        err = HTTPException(
            status_code=500, detail=f"Anthropic API error: {e.message}"
        )
        print(f"LLM_ERROR_HTTP: status={err.status_code}, detail={err.detail}")
        return err
    err = HTTPException(status_code=500, detail=f"LLM API error: {e}")
    print(f"LLM_ERROR_HTTP: status={err.status_code}, detail={err.detail}")
    return err

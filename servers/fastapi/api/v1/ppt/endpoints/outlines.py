import asyncio
import json
import math
import traceback
import uuid
import dirtyjson
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from models.presentation_outline_model import PresentationOutlineModel
from models.sql.presentation import PresentationModel
from models.sse_response import (
    SSECompleteResponse,
    SSEErrorResponse,
    SSEResponse,
    SSEStatusResponse,
)
from services.temp_file_service import TEMP_FILE_SERVICE
from services.database import get_async_session
from services.documents_loader import DocumentsLoader
from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
from utils.ppt_utils import get_presentation_title_from_outlines

OUTLINES_ROUTER = APIRouter(prefix="/outlines", tags=["Outlines"])


@OUTLINES_ROUTER.get("/stream/{id}")
async def stream_outlines(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    print(f"[{id}] OUTLINES_STREAM_START: Handling outline stream request for presentation")
    presentation = await sql_session.get(PresentationModel, id)

    if not presentation:
        print(f"[{id}] OUTLINES_STREAM_ERROR: Presentation not found")
        raise HTTPException(status_code=404, detail="Presentation not found")

    temp_dir = TEMP_FILE_SERVICE.create_temp_dir()

    async def inner():
        import time
        start_time = time.time()
        print(f"[{id}] OUTLINES_STREAM_GENERATING: Started generating outlines")
        
        yield SSEStatusResponse(
            status="Generating presentation outlines..."
        ).to_string()

        additional_context = ""
        try:
            if presentation.file_paths:
                documents_loader = DocumentsLoader(file_paths=presentation.file_paths)
                await documents_loader.load_documents(temp_dir)
                documents = documents_loader.documents
                if documents:
                    additional_context = "\n\n".join(documents)
        except Exception as e:
            traceback.print_exc()
            yield SSEErrorResponse(
                detail=f"Error loading documents: {str(e)}"
            ).to_string()
            # Don't return, try to generate without documents if possible, 
            # or return if context is critical. 
            # Here we choose to continue without context but warn the user.
            yield SSEStatusResponse(
                status="Warning: Failed to load documents, generating without context..."
            ).to_string()

        presentation_outlines_text = ""

        n_slides_to_generate = presentation.n_slides
        if presentation.include_table_of_contents:
            needed_toc_count = math.ceil((presentation.n_slides - 1) / 10)
            n_slides_to_generate -= math.ceil(
                (presentation.n_slides - needed_toc_count) / 10
            )

        try:
            async for chunk in generate_ppt_outline(
                presentation.content,
                n_slides_to_generate,
                presentation.language,
                additional_context,
                presentation.tone,
                presentation.verbosity,
                presentation.instructions,
                presentation.include_title_slide,
                presentation.web_search,
            ):
                # Give control to the event loop
                await asyncio.sleep(0)

                if isinstance(chunk, HTTPException):
                    yield SSEErrorResponse(detail=chunk.detail).to_string()
                    return

                yield SSEResponse(
                    event="response",
                    data=json.dumps({"type": "chunk", "chunk": chunk}),
                ).to_string()

                presentation_outlines_text += chunk
        except Exception as e:
            print(f"[{id}] OUTLINES_STREAM_ERROR: Error generating outline: {str(e)}")
            traceback.print_exc()
            yield SSEErrorResponse(
                detail=f"Error generating outline: {str(e)}"
            ).to_string()
            return

        try:
            presentation_outlines_json = dict(
                dirtyjson.loads(presentation_outlines_text)
            )
        except Exception as e:
            print(f"[{id}] OUTLINES_STREAM_ERROR: Failed to parse outline JSON: {str(e)}")
            traceback.print_exc()
            yield SSEErrorResponse(
                detail=f"Failed to generate presentation outlines. Please try again. {str(e)}",
            ).to_string()
            return

        presentation_outlines = PresentationOutlineModel(**presentation_outlines_json)

        presentation_outlines.slides = presentation_outlines.slides[
            :n_slides_to_generate
        ]

        presentation.outlines = presentation_outlines.model_dump()
        presentation.title = get_presentation_title_from_outlines(presentation_outlines)

        sql_session.add(presentation)
        await sql_session.commit()

        end_time = time.time()
        print(f"[{id}] OUTLINES_STREAM_SUCCESS: Successfully generated {len(presentation_outlines.slides)} outlines in {end_time - start_time:.2f}s")

        yield SSECompleteResponse(
            key="presentation", value=presentation.model_dump(mode="json")
        ).to_string()

    return StreamingResponse(inner(), media_type="text/event-stream")

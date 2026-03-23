from typing import Annotated, List, Dict, Any
import logging
import traceback
from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from services.third_party_ppt_service import ThirdPartyPptService
from services.database import get_async_session
from pydantic import BaseModel
import os
import json
import asyncio

THIRD_PARTY_ROUTER = APIRouter(prefix="/third-party", tags=["Third-Party PPT"])
logger = logging.getLogger("uvicorn.error")

# Initialize service
third_party_ppt_service = ThirdPartyPptService()

@THIRD_PARTY_ROUTER.post("/generate")
async def generate_third_party_ppt(
    content: Annotated[str, Body()],
    n_slides: Annotated[int, Body()],
    language: Annotated[str, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        logger.info(
            "third-party.generate content_len=%s n_slides=%s language=%s",
            len(content) if content else 0,
            n_slides,
            language,
        )
        print(f"third-party.generate start n_slides={n_slides} language={language} content_len={len(content) if content else 0}")
        return await third_party_ppt_service.generate_outlines(content, n_slides, language, sql_session)
    except HTTPException as e:
        logger.warning("third-party.generate http_error status=%s detail=%s", e.status_code, e.detail)
        raise e
    except Exception as e:
        logger.exception("third-party.generate failed")
        raise HTTPException(status_code=500, detail=str(e))

class BuildPptRequest(BaseModel):
    presentation_id: str
    outlines: List[Dict[str, Any]]

@THIRD_PARTY_ROUTER.post("/build")
async def build_third_party_ppt(
    request: BuildPptRequest,
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        logger.info(
            "third-party.build presentation_id=%s outlines_count=%s",
            request.presentation_id,
            len(request.outlines) if request.outlines else 0,
        )
        print(f"third-party.build start presentation_id={request.presentation_id} outlines_count={len(request.outlines) if request.outlines else 0}")
        return await third_party_ppt_service.build_presentation(request.presentation_id, request.outlines, sql_session)
    except HTTPException as e:
        logger.warning("third-party.build http_error status=%s detail=%s", e.status_code, e.detail)
        raise e
    except Exception as e:
        logger.exception("third-party.build failed")
        raise HTTPException(status_code=500, detail=str(e))

@THIRD_PARTY_ROUTER.post("/build/stream")
async def build_third_party_ppt_stream(
    request: BuildPptRequest,
    sql_session: AsyncSession = Depends(get_async_session),
):
    queue: asyncio.Queue = asyncio.Queue()

    async def progress_callback(payload: Dict[str, Any]) -> None:
        await queue.put(("progress", payload))

    async def run_build() -> None:
        try:
            result = await third_party_ppt_service.build_presentation(
                request.presentation_id,
                request.outlines,
                sql_session,
                progress_callback=progress_callback,
            )
            await queue.put(("done", result))
        except HTTPException as e:
            await queue.put(("error", {"status_code": e.status_code, "detail": e.detail}))
        except Exception as e:
            logger.exception("third-party.build.stream failed")
            await queue.put(("error", {"status_code": 500, "detail": str(e)}))
        finally:
            await queue.put(("close", None))

    asyncio.create_task(run_build())

    async def event_generator():
        while True:
            event, payload = await queue.get()
            if event == "close":
                break
            if event == "progress":
                yield f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            elif event == "done":
                done_payload = {"stage": "done", "result": payload}
                yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
            elif event == "error":
                err_payload = {"stage": "error", **payload}
                yield f"event: error\ndata: {json.dumps(err_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@THIRD_PARTY_ROUTER.get("/download/{presentation_id}")
async def download_third_party_ppt(
    presentation_id: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    try:
        file_path = await third_party_ppt_service.get_pptx_path(presentation_id, sql_session)
        filename = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("third-party.download failed presentation_id=%s", presentation_id)
        raise HTTPException(status_code=500, detail=str(e))

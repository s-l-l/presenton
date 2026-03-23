import os
import uuid
import json
import asyncio
import math
import traceback
import glob
from typing import Optional, Dict, Any, List, Callable, Awaitable
from fastapi import HTTPException
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pathvalidate import sanitize_filename

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.presentation_outline_model import PresentationOutlineModel, SlideOutlineModel
from models.presentation_layout import PresentationLayoutModel
from services.database import get_async_session
from services.image_generation_service import ImageGenerationService
from services.pptx_presentation_creator import PptxPresentationCreator
from utils.asset_directory_utils import get_exports_directory, get_images_directory
from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
from utils.llm_calls.generate_presentation_structure import generate_presentation_structure
from utils.llm_calls.generate_slide_content import get_slide_content_from_type_and_outline
from utils.get_layout_by_name import get_layout_by_name
from utils.ppt_utils import get_presentation_title_from_outlines, select_toc_or_list_slide_layout_index
from utils.process_slides import process_slide_and_fetch_assets
import dirtyjson

logger = logging.getLogger(__name__)

class ThirdPartyPptService:
    def __init__(self):
        self.exports_directory = get_exports_directory()
        self.images_directory = get_images_directory()

    async def _emit_progress(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
        stage: str,
        message: str,
        percent: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not progress_callback:
            return
        payload: Dict[str, Any] = {
            "stage": stage,
            "message": message,
            "percent": percent,
        }
        if extra:
            payload.update(extra)
        await progress_callback(payload)

    async def generate_outlines(self, content: str, n_slides: int, language: str, sql_session: AsyncSession) -> Dict[str, Any]:
        """
        Step 1: Generate outlines from content.
        """
        presentation_id = uuid.uuid4()
        
        # Calculate slides to generate (considering TOC if needed, but here we simplify)
        n_slides_to_generate = n_slides
        
        presentation_outlines_text = ""
        try:
            async with asyncio.timeout(240):
                async for chunk in generate_ppt_outline(
                    content=content,
                    n_slides=n_slides_to_generate,
                    language=language,
                    additional_context="",
                    tone="default",
                    verbosity="standard",
                    instructions=None,
                    include_title_slide=True,
                    web_search=False,
                ):
                    if isinstance(chunk, HTTPException):
                        raise chunk
                    presentation_outlines_text += chunk
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Outline generation timed out")

        try:
            presentation_outlines_json = dict(dirtyjson.loads(presentation_outlines_text))
        except Exception:
            traceback.print_exc()
            raise HTTPException(status_code=400, detail="Failed to parse outlines")

        # Save presentation model
        presentation = PresentationModel(
            id=presentation_id,
            content=content,
            n_slides=n_slides,
            language=language,
            outlines=presentation_outlines_json,
        )
        sql_session.add(presentation)
        await sql_session.commit()

        return {
            "presentation_id": str(presentation_id),
            "outlines": presentation_outlines_json.get("slides", [])
        }

    async def build_presentation(
        self,
        presentation_id: str,
        outlines: List[Dict[str, Any]],
        sql_session: AsyncSession,
        progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """
        Step 2: Build the PPT from outlines.
        """
        pid = uuid.UUID(presentation_id)
        presentation = await sql_session.get(PresentationModel, pid)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")

        if not outlines:
            raise HTTPException(status_code=400, detail="outlines are required")
        await self._emit_progress(progress_callback, "validated", "参数校验完成", 10)

        try:
            presentation_outline_model = PresentationOutlineModel(
                slides=[SlideOutlineModel(**o) for o in outlines]
            )
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid outlines: {str(e)}")

        presentation.outlines = presentation_outline_model.model_dump()
        presentation.title = get_presentation_title_from_outlines(presentation_outline_model)

        layout_name = os.getenv("THIRD_PARTY_DEFAULT_TEMPLATE") or "general"
        logger.info("third-party.build fetching layout=%s presentation_id=%s", layout_name, presentation_id)
        layout_model = await get_layout_by_name(layout_name)
        presentation.set_layout(layout_model)
        await self._emit_progress(progress_callback, "layout_ready", "模板加载完成", 20, {"layout": layout_name})

        logger.info("third-party.build generating structure presentation_id=%s", presentation_id)
        presentation_structure = await generate_presentation_structure(
            presentation_outline_model,
            layout_model,
            presentation.instructions
        )
        await self._emit_progress(progress_callback, "structure_ready", "页面结构生成完成", 35)

        total_slide_layouts = len(layout_model.slides)
        total_outlines = len(presentation_outline_model.slides)
        presentation_structure.slides = presentation_structure.slides[:total_outlines]
        for index in range(total_outlines):
            if index >= len(presentation_structure.slides):
                presentation_structure.slides.append(0)
                continue
            slide_idx = presentation_structure.slides[index]
            if slide_idx is None or slide_idx < 0 or slide_idx >= total_slide_layouts:
                presentation_structure.slides[index] = 0

        presentation.set_structure(presentation_structure)
        
        sql_session.add(presentation)
        await sql_session.commit()

        logger.info(
            "third-party.build generating slides presentation_id=%s slides=%s",
            presentation_id,
            len(presentation_structure.slides),
        )
        image_gen_service = ImageGenerationService(self.images_directory)
        slide_layout_indices = presentation_structure.slides
        slide_layouts = [layout_model.slides[idx] for idx in slide_layout_indices]
        
        slides: List[SlideModel] = []
        asset_tasks = []

        for i, slide_layout in enumerate(slide_layouts):
            slide_content = await get_slide_content_from_type_and_outline(
                slide_layout,
                presentation_outline_model.slides[i],
                presentation.language,
                presentation.tone,
                presentation.verbosity,
                presentation.instructions
            )
            
            slide = SlideModel(
                presentation=pid,
                layout_group=layout_model.name,
                layout=slide_layout.id,
                index=i,
                speaker_note=slide_content.get("__speaker_note__", ""),
                content=slide_content
            )
            slides.append(slide)
            asset_tasks.append(asyncio.create_task(process_slide_and_fetch_assets(image_gen_service, slide)))
            if i > 0 and i % 3 == 0:
                approx = min(55, 35 + int((i / max(1, len(slide_layouts))) * 20))
                await self._emit_progress(progress_callback, "slides_generating", f"已生成 {i + 1}/{len(slide_layouts)} 页内容", approx)

        generated_assets = []
        if asset_tasks:
            logger.info(
                "third-party.build fetching assets presentation_id=%s tasks=%s",
                presentation_id,
                len(asset_tasks),
            )
            generated_assets_list = await asyncio.gather(*asset_tasks, return_exceptions=True)
            for assets in generated_assets_list:
                if isinstance(assets, Exception):
                    logger.warning(
                        "third-party.build asset_task_failed presentation_id=%s error=%s",
                        presentation_id,
                        str(assets),
                    )
                    continue
                generated_assets.extend(assets)
        await self._emit_progress(progress_callback, "assets_ready", "素材处理完成", 70)

        # Save slides and assets
        sql_session.add_all(slides)
        sql_session.add_all(generated_assets)
        await sql_session.commit()
        await self._emit_progress(progress_callback, "persisted", "页面与素材已入库", 80)

        # Export to PPTX
        from utils.export_utils import export_presentation
        export_title = f"{presentation.title or 'presentation'}-{presentation_id}"
        await self._emit_progress(progress_callback, "exporting", "开始导出 PPTX", 90)
        export_result = await export_presentation(pid, export_title, "pptx")
        await self._emit_progress(
            progress_callback,
            "completed",
            "PPT 生成完成",
            100,
            {
                "presentation_id": presentation_id,
                "download_url": f"/api/v1/ppt/third-party/download/{presentation_id}",
                "path": export_result.path,
            },
        )
        
        return {
            "presentation_id": presentation_id,
            "download_url": f"/api/v1/ppt/third-party/download/{presentation_id}"
        }

    async def get_pptx_path(self, presentation_id: str, sql_session: AsyncSession) -> str:
        """
        Resolve the exported PPTX path for a presentation id.
        """
        candidates: List[str] = []

        # Legacy naming fallback: {presentation_id}.pptx
        candidates.append(os.path.join(self.exports_directory, f"{presentation_id}.pptx"))

        # Current export naming: sanitize_filename(f"{title}-{presentation_id}").pptx
        try:
            pid = uuid.UUID(presentation_id)
            presentation = await sql_session.get(PresentationModel, pid)
            if presentation:
                expected_name = sanitize_filename(
                    f"{presentation.title or 'presentation'}-{presentation_id}"
                )
                candidates.append(os.path.join(self.exports_directory, f"{expected_name}.pptx"))
        except Exception:
            # Keep searching by glob below even if DB/title lookup fails.
            pass

        for path in candidates:
            if os.path.exists(path):
                return path

        # Broad fallback for historical/alternative naming.
        matched = glob.glob(os.path.join(self.exports_directory, f"*{presentation_id}*.pptx"))
        if not matched:
            compact_id = presentation_id.replace("-", "")
            matched = glob.glob(os.path.join(self.exports_directory, f"*{compact_id}*.pptx"))

        if not matched:
            raise HTTPException(status_code=404, detail="File not found")

        # Return most recently modified candidate if multiple files exist.
        matched.sort(key=os.path.getmtime, reverse=True)
        return matched[0]

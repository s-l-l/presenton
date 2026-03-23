from fastapi import APIRouter, HTTPException
import aiohttp
from typing import List, Any
from utils.get_layout_by_name import get_layout_by_name
from models.presentation_layout import PresentationLayoutModel
from utils.get_env import get_nextjs_api_base_url_env

LAYOUTS_ROUTER = APIRouter(prefix="/layouts", tags=["Layouts"])

@LAYOUTS_ROUTER.get("/", summary="Get available layouts")
async def get_layouts():
    base_url = (get_nextjs_api_base_url_env() or "http://localhost:3000").rstrip("/")
    url = f"{base_url}/api/layouts"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                error_text = await response.text()
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to fetch layouts from {url}: {error_text}",
                )
            layouts_json = await response.json()
    # Optionally, parse into a Pydantic model if you have one matching the structure
    return layouts_json


@LAYOUTS_ROUTER.get("/{layout_name}", summary="Get layout details by ID")
async def get_layout_detail(layout_name: str) -> PresentationLayoutModel:
    return await get_layout_by_name(layout_name)

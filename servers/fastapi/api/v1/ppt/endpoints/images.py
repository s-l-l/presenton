import asyncio
from typing import List
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from services.database import get_async_session
from services.image_generation_service import ImageGenerationService
from utils.asset_directory_utils import get_images_directory, to_public_image_url
import os
import uuid
from utils.file_utils import get_file_name_with_random_uuid

IMAGES_ROUTER = APIRouter(prefix="/images", tags=["Images"])


async def _download_remote_image_to_local(url: str, images_directory: str):
    try:
        timeout = httpx.Timeout(20.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None

            parsed = urlparse(url)
            original_name = os.path.basename(parsed.path) or "generated.jpg"
            ext = os.path.splitext(original_name)[1] or ".jpg"
            local_name = f"{uuid.uuid4().hex}{ext}"
            local_path = os.path.join(images_directory, local_name)

            with open(local_path, "wb") as f:
                f.write(resp.content)
            return local_path
    except Exception:
        return None


@IMAGES_ROUTER.get("/proxy")
async def proxy_image(url: str):
    """
    Proxy remote image bytes through backend to avoid browser-side CORS restrictions.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid url")

    try:
        timeout = httpx.Timeout(20.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch image")

            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image proxy error: {str(e)}")


@IMAGES_ROUTER.get("/generate")
async def generate_image(
    prompt: str,
    count: int = 1,
    presentation_id: uuid.UUID = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    images_directory = get_images_directory()
    image_generation_service = ImageGenerationService(images_directory)
    safe_count = max(1, min(count, 8))

    tasks = [
        image_generation_service.generate_image(ImagePrompt(prompt=prompt))
        for _ in range(safe_count)
    ]
    generated = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[str] = []
    for item in generated:
        if isinstance(item, Exception):
            continue
        if isinstance(item, ImageAsset):
            item.presentation_id = presentation_id
            sql_session.add(item)
            results.append(to_public_image_url(item.path))
        elif isinstance(item, str):
            local_path = await _download_remote_image_to_local(item, images_directory)
            final_path = local_path or item
            new_asset = ImageAsset(path=final_path, is_uploaded=False, presentation_id=presentation_id, extras={"prompt": prompt})
            sql_session.add(new_asset)
            results.append(to_public_image_url(final_path))

    await sql_session.commit()
    if safe_count == 1:
        return results[0] if results else "/static/images/placeholder.jpg"
    return results


@IMAGES_ROUTER.get("/generated", response_model=List[ImageAsset])
async def get_generated_images(
    presentation_id: uuid.UUID = None,
    sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(ImageAsset).where(ImageAsset.is_uploaded == False)
        if presentation_id:
            query = query.where(ImageAsset.presentation_id == presentation_id)

        images = await sql_session.scalars(
            query.order_by(ImageAsset.created_at.desc())
        )
        result = list(images)
        for image in result:
            image.path = to_public_image_url(image.path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve generated images: {str(e)}"
        )


@IMAGES_ROUTER.post("/upload")
async def upload_image(
    file: UploadFile = File(...), sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        new_filename = get_file_name_with_random_uuid(file)
        image_path = os.path.join(
            get_images_directory(), os.path.basename(new_filename)
        )

        with open(image_path, "wb") as f:
            f.write(await file.read())

        image_asset = ImageAsset(path=image_path, is_uploaded=True)

        sql_session.add(image_asset)
        await sql_session.commit()

        image_asset.path = to_public_image_url(image_asset.path)
        return image_asset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@IMAGES_ROUTER.get("/uploaded", response_model=List[ImageAsset])
async def get_uploaded_images(sql_session: AsyncSession = Depends(get_async_session)):
    try:
        images = await sql_session.scalars(
            select(ImageAsset)
            .where(ImageAsset.is_uploaded == True)
            .order_by(ImageAsset.created_at.desc())
        )
        result = list(images)
        for image in result:
            image.path = to_public_image_url(image.path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve uploaded images: {str(e)}"
        )


@IMAGES_ROUTER.get("/generate/batch")
async def generate_images_batch(
    prompt: str,
    count: int = 4,
    presentation_id: uuid.UUID = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Generate multiple images concurrently for the same prompt.
    Returns a list of image URLs/paths that frontend can render directly.
    """
    safe_count = max(1, min(count, 8))
    images_directory = get_images_directory()
    image_generation_service = ImageGenerationService(images_directory)

    tasks = [
        image_generation_service.generate_image(ImagePrompt(prompt=prompt))
        for _ in range(safe_count)
    ]
    generated = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[str] = []
    for item in generated:
        if isinstance(item, Exception):
            continue
        if isinstance(item, ImageAsset):
            item.presentation_id = presentation_id
            sql_session.add(item)
            results.append(to_public_image_url(item.path))
        elif isinstance(item, str):
            local_path = await _download_remote_image_to_local(item, images_directory)
            final_path = local_path or item
            new_asset = ImageAsset(path=final_path, is_uploaded=False, presentation_id=presentation_id, extras={"prompt": prompt})
            sql_session.add(new_asset)
            results.append(to_public_image_url(final_path))

    await sql_session.commit()
    return results


@IMAGES_ROUTER.delete("/{id}", status_code=204)
async def delete_uploaded_image_by_id(
    id: uuid.UUID, sql_session: AsyncSession = Depends(get_async_session)
):
    try:
        image = await sql_session.get(ImageAsset, id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        os.remove(image.path)

        await sql_session.delete(image)
        await sql_session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

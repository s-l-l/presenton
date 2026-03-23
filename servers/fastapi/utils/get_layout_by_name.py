import aiohttp
import json
import logging
from pathlib import Path
from fastapi import HTTPException
from models.presentation_layout import PresentationLayoutModel
from utils.get_env import (
    get_nextjs_api_base_url_env,
    get_template_local_dir_env,
    get_template_preload_env,
    get_template_remote_fallback_env,
    get_template_source_env,
)

logger = logging.getLogger(__name__)

_LAYOUT_CACHE: dict[str, PresentationLayoutModel] = {}
_PRELOADED = False


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _template_source() -> str:
    source = (get_template_source_env() or "local").strip().lower()
    if source not in {"local", "remote"}:
        return "local"
    return source


def _templates_dir() -> Path:
    configured = get_template_local_dir_env()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "templates"


def _read_layout_file(layout_name: str) -> PresentationLayoutModel | None:
    file_path = _templates_dir() / f"{layout_name}.json"
    if not file_path.exists():
        return None
    try:
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return PresentationLayoutModel(**payload)
    except Exception as e:
        logger.warning("template.local.read_failed group=%s file=%s error=%s", layout_name, file_path, str(e))
        return None


def preload_layout_cache(force: bool = False) -> int:
    global _PRELOADED
    if _PRELOADED and not force:
        return len(_LAYOUT_CACHE)

    templates_dir = _templates_dir()
    if not templates_dir.exists():
        logger.warning("template.local.dir_missing path=%s", templates_dir)
        _PRELOADED = True
        return len(_LAYOUT_CACHE)

    loaded = 0
    for file_path in templates_dir.glob("*.json"):
        layout_name = file_path.stem
        layout_model = _read_layout_file(layout_name)
        if layout_model is None:
            continue
        _LAYOUT_CACHE[layout_name] = layout_model
        loaded += 1

    _PRELOADED = True
    logger.info("template.local.preload_done loaded=%s dir=%s", loaded, templates_dir)
    return loaded


async def _fetch_remote_layout(layout_name: str) -> PresentationLayoutModel:
    base_url = (get_nextjs_api_base_url_env() or "http://localhost:3000").rstrip("/")
    url = f"{base_url}/api/template?group={layout_name}"
    timeout = aiohttp.ClientTimeout(total=30)
    last_error = ""

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(3):
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=404,
                            detail=f"Template '{layout_name}' not found: {error_text}",
                        )
                    payload = await response.json()
                    layout_model = PresentationLayoutModel(**payload)
                    _LAYOUT_CACHE[layout_name] = layout_model
                    return layout_model
            except HTTPException:
                raise
            except Exception as e:
                last_error = str(e)
                continue

    raise HTTPException(
        status_code=503,
        detail=f"Failed to fetch template '{layout_name}' from {url}: {last_error}",
    )


async def get_layout_by_name(layout_name: str) -> PresentationLayoutModel:
    if _to_bool(get_template_preload_env(), True):
        preload_layout_cache()

    source = _template_source()
    allow_remote_fallback = _to_bool(get_template_remote_fallback_env(), False)

    # Local-first path.
    if source == "local":
        layout = _LAYOUT_CACHE.get(layout_name)
        if layout is None:
            layout = _read_layout_file(layout_name)
            if layout is not None:
                _LAYOUT_CACHE[layout_name] = layout
        if layout is not None:
            return layout
        if not allow_remote_fallback:
            raise HTTPException(status_code=404, detail=f"Template '{layout_name}' not found in local templates")

    # Remote primary path or local fallback path.
    try:
        return await _fetch_remote_layout(layout_name)
    except HTTPException:
        if source == "local":
            # local mode with remote fallback enabled but remote failed
            raise
        # remote mode: fallback to local only when remote fails and local exists
        layout = _LAYOUT_CACHE.get(layout_name) or _read_layout_file(layout_name)
        if layout is not None:
            _LAYOUT_CACHE[layout_name] = layout
            return layout
        raise


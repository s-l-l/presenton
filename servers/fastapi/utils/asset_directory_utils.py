import os
from typing import Optional
from urllib.parse import urlparse, unquote, quote

from utils.get_env import get_app_data_directory_env


def resolve_image_path_to_filesystem(path_or_url: str) -> Optional[str]:
    """
    Resolve an image path or URL to an actual filesystem path.

    Handles:
    - Path strings: /app_data/images/..., /static/..., absolute paths, relative
    - HTTP URLs whose path component is an absolute filesystem path (Mac/Electron):
      When img src is /Users/.../images/xxx.png, browser resolves to
      http://origin/Users/.../images/xxx.png. Next.js returns 404 for these.

    Returns the filesystem path if the file exists, else None.
    """
    if not path_or_url:
        return None
    # Extract path from HTTP URL if needed
    path = path_or_url
    if path_or_url.startswith("http"):
        try:
            parsed = urlparse(path_or_url)
            path = unquote(parsed.path)
        except Exception:
            return None
    # Handle /app_data/images/
    if path.startswith("/app_data/images/"):
        relative = path[len("/app_data/images/"):]
        app_data = get_app_data_directory_env()
        if app_data:
            actual = os.path.join(app_data, "images", relative)
            if os.path.isfile(actual):
                return actual
        # Fallback: get_images_directory() + relative
        actual = os.path.join(get_images_directory(), relative)
        return actual if os.path.isfile(actual) else None
    # Handle /app_data/ (other subdirs)
    if path.startswith("/app_data/"):
        relative = path[len("/app_data/"):]
        app_data = get_app_data_directory_env()
        if app_data:
            actual = os.path.join(app_data, relative)
            return actual if os.path.isfile(actual) else None
    # Handle absolute filesystem path (e.g. from HTTP URL path on Mac)
    if path.startswith("/Users/") or path.startswith("/home/") or path.startswith("/var/"):
        return path if os.path.isfile(path) else None
    if "Application Support" in path or ("Library" in path and "images" in path):
        return path if os.path.isfile(path) else None
    # Handle /static/
    if path.startswith("/static/"):
        relative = path[len("/static/"):]
        actual = os.path.join("static", relative)
        return actual if os.path.isfile(actual) else None
    # Absolute path as-is
    if os.path.isabs(path):
        return path if os.path.isfile(path) else None
    # Relative to images directory
    actual = os.path.join(get_images_directory(), path)
    return actual if os.path.isfile(actual) else None


def _get_base_app_data_dir():
    app_data_dir = get_app_data_directory_env()
    if not app_data_dir:
        # Cross-platform fallback
        app_data_dir = os.path.join(os.environ.get("APPDATA") or os.environ.get("HOME") or os.getcwd(), ".presenton")
    return app_data_dir


def get_images_directory():
    images_directory = os.path.join(_get_base_app_data_dir(), "images")
    os.makedirs(images_directory, exist_ok=True)
    return images_directory


def get_exports_directory():
    export_directory = os.path.join(_get_base_app_data_dir(), "exports")
    os.makedirs(export_directory, exist_ok=True)
    return export_directory

def get_uploads_directory():
    uploads_directory = os.path.join(_get_base_app_data_dir(), "uploads")
    os.makedirs(uploads_directory, exist_ok=True)
    return uploads_directory


def to_public_image_url(path_or_url: str) -> str:
    """
    Convert local filesystem image paths to web-safe paths consumed by frontend.
    - Keep http(s) URLs as-is
    - Keep /static and /app_data paths as-is
    - Convert files under app_data/images to /app_data/images/<relative>
    - Otherwise return original string
    """
    if not path_or_url:
        return path_or_url
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        # Route remote images through same-origin proxy to avoid browser CORS issues
        # when images are used in canvas/export flows.
        encoded = quote(path_or_url, safe="")
        return f"/api/v1/ppt/images/proxy?url={encoded}"
    if path_or_url.startswith("file://"):
        parsed = urlparse(path_or_url)
        path_or_url = unquote(parsed.path).lstrip("/")
    if path_or_url.startswith("/static/") or path_or_url.startswith("/app_data/"):
        return path_or_url

    try:
        normalized = os.path.abspath(path_or_url)
        images_dir = os.path.abspath(get_images_directory())
        if normalized.startswith(images_dir):
            relative = os.path.relpath(normalized, images_dir).replace("\\", "/")
            return f"/app_data/images/{relative}"
        normalized_unix = normalized.replace("\\", "/").lower()
        marker = "/app_data/images/"
        if marker in normalized_unix:
            idx = normalized_unix.index(marker) + len(marker)
            tail = normalized.replace("\\", "/")[idx:]
            return f"/app_data/images/{tail}"
    except Exception:
        pass
    return path_or_url

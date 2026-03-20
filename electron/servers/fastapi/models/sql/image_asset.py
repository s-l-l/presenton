from datetime import datetime
from typing import Optional
import os
import uuid

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from utils.datetime_utils import get_current_utc_datetime
from utils.get_env import get_app_data_directory_env
from utils.path_helpers import get_resource_path


class ImageAsset(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=get_current_utc_datetime
        ),
    )
    is_uploaded: bool = Field(default=False)
    path: str
    extras: Optional[dict] = Field(sa_column=Column(JSON), default=None)
    
    @property
    def file_url(self) -> str:
        """
        Returns a web path suitable for FastAPI static serving.
        - HTTP(S) URLs are returned as-is.
        - Files under APP_DATA are exposed under /app_data.
        - Files under the packaged static directory are exposed under /static.
        """
        path = self.path

        # Already an absolute web URL
        if path.startswith("http://") or path.startswith("https://"):
            return path

        # Normalize filesystem path
        real_path = os.path.realpath(path)

        # Map APP_DATA files to /app_data/...
        app_data_dir = get_app_data_directory_env()
        if app_data_dir:
            app_data_dir_real = os.path.realpath(app_data_dir)
            if real_path.startswith(app_data_dir_real):
                rel = os.path.relpath(real_path, app_data_dir_real)
                rel_web = rel.replace(os.sep, "/")
                return f"/app_data/{rel_web}"
            # Robust fallback: if absolute path contains an app_data segment,
            # still expose it as /app_data/... to avoid leaking filesystem paths.
            marker = f"{os.sep}app_data{os.sep}"
            normalized_real = real_path.replace("/", os.sep)
            lowered_real = normalized_real.lower()
            lowered_marker = marker.lower()
            if lowered_marker in lowered_real:
                start_idx = lowered_real.index(lowered_marker) + len(lowered_marker)
                relative_from_app_data = normalized_real[start_idx:]
                rel_web = relative_from_app_data.replace(os.sep, "/")
                return f"/app_data/{rel_web}"

        # Map packaged static assets to /static/...
        static_root = get_resource_path("static")
        static_root_real = os.path.realpath(static_root)
        if real_path.startswith(static_root_real):
            rel = os.path.relpath(real_path, static_root_real)
            rel_web = rel.replace(os.sep, "/")
            return f"/static/{rel_web}"

        # Last fallback: for an absolute local path under an images folder,
        # map to /app_data/images/<filename> so browser can fetch it via FastAPI.
        if os.path.isabs(real_path):
            images_marker = f"{os.sep}images{os.sep}"
            normalized_real = real_path.replace("/", os.sep)
            lowered_real = normalized_real.lower()
            if images_marker.lower() in lowered_real:
                start_idx = lowered_real.index(images_marker.lower()) + len(images_marker)
                tail = normalized_real[start_idx:]
                tail_web = tail.replace(os.sep, "/")
                return f"/app_data/images/{tail_web}"

        # Keep relative/unmapped values unchanged.
        return path

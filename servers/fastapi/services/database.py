from collections.abc import AsyncGenerator
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text
from sqlmodel import SQLModel

from models.sql.async_presentation_generation_status import (
    AsyncPresentationGenerationTaskModel,
)
from models.sql.image_asset import ImageAsset
from models.sql.key_value import KeyValueSqlModel
from models.sql.ollama_pull_status import OllamaPullStatus
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.sql.presentation_layout_code import PresentationLayoutCodeModel
from models.sql.template import TemplateModel
from models.sql.webhook_subscription import WebhookSubscription
from utils.db_utils import get_database_url_and_connect_args
from utils.get_env import get_container_db_path_env, get_app_data_directory_env


database_url, connect_args = get_database_url_and_connect_args()

sql_engine: AsyncEngine = create_async_engine(database_url, connect_args=connect_args)
async_session_maker = async_sessionmaker(sql_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


container_db_path = get_container_db_path_env()
if not container_db_path:
    app_data_dir = get_app_data_directory_env()
    if not app_data_dir:
        app_data_dir = os.path.join(
            os.environ.get("APPDATA") or os.environ.get("HOME") or os.getcwd(),
            ".presenton",
        )
    container_db_path = str(Path(app_data_dir) / "container.db")

container_db_path_obj = Path(container_db_path).expanduser().resolve()
container_db_path_obj.parent.mkdir(parents=True, exist_ok=True)
container_db_path_normalized = str(container_db_path_obj).replace("\\", "/")
container_db_url = f"sqlite+aiosqlite:///{container_db_path_normalized}"
container_db_engine: AsyncEngine = create_async_engine(
    container_db_url, connect_args={"check_same_thread": False}
)
container_db_async_session_maker = async_sessionmaker(
    container_db_engine, expire_on_commit=False
)


async def get_container_db_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with container_db_async_session_maker() as session:
        yield session


# Create Database and Tables
async def create_db_and_tables():
    async with sql_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: SQLModel.metadata.create_all(
                sync_conn,
                tables=[
                    PresentationModel.__table__,
                    SlideModel.__table__,
                    KeyValueSqlModel.__table__,
                    ImageAsset.__table__,
                    PresentationLayoutCodeModel.__table__,
                    TemplateModel.__table__,
                    WebhookSubscription.__table__,
                    AsyncPresentationGenerationTaskModel.__table__,
                ],
            )
        )
        # Lightweight schema migration for existing DBs: ensure `presentations.theme` exists.
        if database_url.startswith("sqlite"):
            result = await conn.execute(text("PRAGMA table_info(presentations)"))
            column_names = {row[1] for row in result.fetchall()}
            if "theme" not in column_names:
                await conn.execute(text("ALTER TABLE presentations ADD COLUMN theme JSON"))

    async with container_db_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: SQLModel.metadata.create_all(
                sync_conn,
                tables=[OllamaPullStatus.__table__],
            )
        )

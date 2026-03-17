from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from migrations import migrate_database_on_startup
from services.database import create_db_and_tables
from utils.get_env import get_app_data_directory_env
from utils.model_availability import (
    check_llm_and_image_provider_api_or_model_availability,
)


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Initializes the application data directory, runs Alembic migrations when
    MIGRATE_DATABASE_ON_STARTUP=true, creates any missing tables, and checks
    LLM model availability.
    """
    app_data_dir = get_app_data_directory_env()
    if app_data_dir:
        os.makedirs(app_data_dir, exist_ok=True)
    await migrate_database_on_startup()
    await create_db_and_tables()
    await check_llm_and_image_provider_api_or_model_availability()
    yield

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from utils.db_utils import get_database_url_and_connect_args
from utils.get_env import get_migrate_database_on_startup_env


async def migrate_database_on_startup() -> None:
    # 默认开启自动迁移，如果显式设置为 "false" 才跳过
    if get_migrate_database_on_startup_env() in ["false", "False", "0"]:
        print("Skipping database migrations as MIGRATE_DATABASE_ON_STARTUP is disabled.")
        return

    try:
        await asyncio.to_thread(_run_migrations)
        print("Migrations run successfully", flush=True)
    except Exception as exc:
        print(f"Error running migrations: {exc}", flush=True)


def _run_migrations() -> None:
    # migrations.py lives at servers/fastapi/migrations.py
    # so parents[0] = servers/fastapi/, where alembic/ lives alongside it.
    base_dir = Path(__file__).resolve().parents[0]
    config = Config()
    config.set_main_option("script_location", str(base_dir / "alembic"))

    database_url, _ = get_database_url_and_connect_args()

    # Alembic uses synchronous engines; strip async driver prefixes.
    database_url = (
        database_url
        .replace("sqlite+aiosqlite://", "sqlite:///")
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("mysql+aiomysql://", "mysql://")
    )

    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

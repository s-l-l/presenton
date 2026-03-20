import os
import platform
from pathlib import Path
from utils.get_env import get_app_data_directory_env, get_database_url_env
from urllib.parse import urlsplit, urlunsplit, parse_qsl
import ssl


def get_database_url_and_connect_args() -> tuple[str, dict]:
    db_url_env = get_database_url_env()
    
    if db_url_env:
        database_url = db_url_env
    else:
        # Fallback to local sqlite db in app data directory
        app_data_dir = get_app_data_directory_env()
        if not app_data_dir:
            # Cross-platform fallback directory
            app_data_dir = os.path.join(os.environ.get("APPDATA") or os.environ.get("HOME") or os.getcwd(), ".presenton")
            os.makedirs(app_data_dir, exist_ok=True)
            
        db_path = Path(app_data_dir) / "fastapi.db"
        # Ensure correct sqlite url format for absolute paths on Windows vs Linux
        db_path_str = str(db_path.absolute()).replace('\\', '/')
        database_url = f"sqlite:///{db_path_str}"

    if database_url.startswith("sqlite://"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+aiomysql://", 1)
    else:
        database_url = database_url

    connect_args = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False

    try:
        split_result = urlsplit(database_url)
        if split_result.query:
            query_params = parse_qsl(split_result.query, keep_blank_values=True)
            driver_scheme = split_result.scheme
            for k, v in query_params:
                key_lower = k.lower()
                if key_lower == "sslmode" and "postgresql+asyncpg" in driver_scheme:
                    if v.lower() != "disable" and "sqlite" not in database_url:
                        connect_args["ssl"] = ssl.create_default_context()

            database_url = urlunsplit(
                (
                    split_result.scheme,
                    split_result.netloc,
                    split_result.path,
                    "",
                    split_result.fragment,
                )
            )
    except Exception:
        pass

    return database_url, connect_args

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import os
import sys
import time

# Load .env file explicitly
load_dotenv()

root_logger = logging.getLogger()
if not root_logger.handlers:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
else:
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

from api.lifespan import app_lifespan
from api.middlewares import UserConfigEnvUpdateMiddleware
from api.v1.ppt.router import API_V1_PPT_ROUTER
from api.v1.webhook.router import API_V1_WEBHOOK_ROUTER
from api.v1.mock.router import API_V1_MOCK_ROUTER


app = FastAPI(lifespan=app_lifespan)
error_logger = logging.getLogger("uvicorn.error")


# Routers
app.include_router(API_V1_PPT_ROUTER)
app.include_router(API_V1_WEBHOOK_ROUTER)
app.include_router(API_V1_MOCK_ROUTER)

# Middlewares
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(UserConfigEnvUpdateMiddleware)


@app.middleware("http")
async def log_requests(request, call_next):
    start_ts = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_ts) * 1000
    logging.getLogger("uvicorn.access").info(
        '%s "%s %s" %s %.2fms',
        request.client.host if request.client else "-",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.middleware("http")
async def log_unhandled_exceptions(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        error_logger.exception(
            "Unhandled exception during request: %s %s",
            request.method,
            request.url.path,
        )
        raise

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port number to run the server on"
    )
    parser.add_argument(
        "--reload", type=str, default="false", help="Reload the server on code changes"
    )
    parser.add_argument(
        "--access-log",
        type=str,
        default=os.getenv("ACCESS_LOG", "true"),
        help="Enable access log (request path/status logging)",
    )
    args = parser.parse_args()
    reload = args.reload.lower() == "true"
    access_log = str(args.access_log).lower() == "true"

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=args.port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=access_log,
        reload=reload,
    )

import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import Response

from .api import router
from .config import settings
from .exceptions import register_exception_handlers
from .logger import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        'API started, database: %s:%s/%s',
        settings.host,
        settings.port,
        settings.db,
    )
    yield


app = FastAPI(title='Okkam test task API', lifespan=lifespan)

app.include_router(router)

register_exception_handlers(app)


@app.middleware('http')
async def log_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Логируем каждый запрос: метод, путь, статус и длительность."""
    start = time.perf_counter()
    response = await call_next(request)
    query = f'?{request.url.query}' if request.url.query else ''
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        '%s %s%s -> %s (%.1f ms)',
        request.method,
        request.url.path,
        query,
        response.status_code,
        elapsed_ms,
    )
    return response

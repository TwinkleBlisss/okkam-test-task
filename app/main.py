import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from .db import get_db_connection
from .percent import get_audience_percent
from .schemas import GetPercentRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('app')

app = FastAPI(title='Okkam test task API')

ConnectionDep = Annotated[Connection, Depends(get_db_connection)]


@app.exception_handler(SQLAlchemyError)
def database_unavailable(request: Request, exc: SQLAlchemyError):
    """Ошибка БД (соединение или запрос) -> 503 вместо 500."""
    logger.exception('database error')
    return JSONResponse(
        status_code=503,
        content={'detail': 'database unavailable'},
    )


@app.get('/getPercent')
def get_percent(
    params: Annotated[GetPercentRequest, Depends()],
    conn: ConnectionDep,
):
    """Процент вхождения второй аудитории в первую"""
    return {
        'percent': get_audience_percent(conn, params.audience1, params.audience2)
    }


@app.get('/health')
def health(conn: ConnectionDep):
    conn.execute(text('SELECT 1'))
    return {'app': True, 'database': True}

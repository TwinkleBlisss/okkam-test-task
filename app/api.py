from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .db import get_db_connection
from .schemas import GetPercentRequest
from .service import get_audience_percent

router = APIRouter()

ConnectionDep = Annotated[Connection, Depends(get_db_connection)]


@router.get('/getPercent')
def get_percent(
    params: Annotated[GetPercentRequest, Depends()],
    conn: ConnectionDep,
):
    """Процент вхождения второй аудитории в первую"""
    return {
        'percent': get_audience_percent(conn, params.audience1, params.audience2)
    }


@router.get('/health')
def health(conn: ConnectionDep):
    conn.execute(text('SELECT 1'))
    return {'app': True, 'database': True}

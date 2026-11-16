from collections.abc import Iterator
from decimal import Decimal
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .config import settings
from .constants import PERCENT_QUERY
from .exceptions import DatabaseInvalidResponseError
from .logger import logger

engine: Engine = create_engine(settings.database_url)


def get_db_connection() -> Iterator[Connection]:
    with engine.connect() as conn:
        yield conn


def get_audience_sums(
    conn: Connection,
    filter1: str,
    filter2: str,
) -> tuple[Decimal, Decimal]:
    """(сумма avg_weight первой аудитории, сумма по пересечению)"""
    query = PERCENT_QUERY.format(filter1=filter1, filter2=filter2)
    row = conn.execute(text(query)).fetchone()

    if row is None:
        raise DatabaseInvalidResponseError('database returned an invalid response')

    sum_audience1, sum_intersection = row
    logger.info(
        'sum_audience1=%s, sum_intersection=%s',
        sum_audience1,
        sum_intersection,
    )
    return sum_audience1, sum_intersection


@lru_cache(maxsize=128)
def cached_audience_sums(
    audience1: str,
    audience2: str,
) -> tuple[Decimal, Decimal]:
    """Кешируемый запрос к БД"""
    with engine.connect() as conn:
        return get_audience_sums(conn, audience1, audience2)

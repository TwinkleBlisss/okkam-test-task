"""Доступ к БД (SQLAlchemy Core).

В запрос подставляются фильтры, прошедшие валидацию app.schemas
(белый список колонок age/sex, без подзапросов и функций),
поэтому прямая подстановка безопасна.
"""

from collections.abc import Iterator
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from .config import Settings
from .constants import PERCENT_QUERY

# create_engine не подключается сразу — импорт безопасен без БД.
engine: Engine = create_engine(Settings().database_url, pool_pre_ping=True)


def get_db_connection() -> Iterator[Connection]:
    """FastAPI-зависимость: соединение из пула на время запроса."""
    with engine.connect() as conn:
        yield conn


def get_audience_sums(
    conn: Connection,
    filter1: str,
    filter2: str,
) -> tuple[Decimal, Decimal]:
    """(сумма avg_weight первой аудитории, сумма по пересечению)."""
    query = PERCENT_QUERY.format(filter1=filter1, filter2=filter2)
    row = conn.execute(text(query)).fetchone()
    return row[0], row[1]

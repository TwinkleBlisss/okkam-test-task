"""Бизнес-логика: процент вхождения второй аудитории в первую."""

from decimal import Decimal

from sqlalchemy.engine import Connection

from .constants import PERCENT_PLACES
from .db import get_audience_sums


def compute_percent(sum_audience1: Decimal, sum_intersection: Decimal) -> float:
    """Процент в диапазоне 0..1; пустая первая аудитория -> 0.0."""
    if sum_audience1 == 0:
        return 0.0
    return float(round(sum_intersection / sum_audience1, PERCENT_PLACES))


def get_audience_percent(
    conn: Connection,
    audience1: str,
    audience2: str,
) -> float:
    """Запрос в БД -> процент. Аудитории приходят уже валидными (app.schemas)."""
    sum1, sum_intersection = get_audience_sums(conn, audience1, audience2)
    return compute_percent(sum1, sum_intersection)

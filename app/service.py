from decimal import Decimal

from sqlalchemy.engine import Connection

from .constants import PERCENT_PLACES
from .db import get_audience_sums
from .logger import logger


def compute_percent(sum_audience1: Decimal, sum_intersection: Decimal) -> float:
    """Процент в диапазоне 0..1"""
    if sum_audience1 == 0:
        return 0.0
    return float(round(sum_intersection / sum_audience1, PERCENT_PLACES))


def get_audience_percent(
    conn: Connection,
    audience1: str,
    audience2: str,
) -> float:
    """Расчёт процента вхождения audience2 в audience1"""
    sum1, sum_intersection = get_audience_sums(conn, audience1, audience2)
    percent = compute_percent(sum1, sum_intersection)
    logger.info(f'percent({audience1}, {audience2}) = {percent}')
    return percent

from functools import lru_cache
from typing import Annotated

import sqlglot
from pydantic import AfterValidator, BaseModel, Field
from sqlglot import exp

from .constants import ALLOWED_COLUMNS
from .logger import logger


def _validate_where(v: str) -> None:
    """Проверка WHERE-фильтра аудитории; при ошибке - ValueError."""
    if ';' in v:
        raise ValueError('Множественные запросы запрещены')

    try:
        # Оборачиваем условие в фиктивный SELECT для корректного парсинга
        parsed = sqlglot.parse_one(
            f'SELECT 1 FROM dummy WHERE {v}',
            read='postgres',
        )
    except sqlglot.errors.ParseError as e:
        raise ValueError('Ошибка синтаксиса в WHERE') from e

    if not isinstance(parsed, exp.Select):
        raise ValueError(  # noqa: TRY004
            'Фильтр должен быть одним WHERE-выражением'
        )

    where_node = parsed.find(exp.Where)
    if where_node is None:
        raise ValueError('Условие WHERE не распознано')

    # Запрещаем подзапросы (SELECT внутри WHERE)
    if where_node.find(exp.Select):
        raise ValueError('Подзапросы в фильтрах запрещены')

    # Запрещаем вызовы функций (например, pg_sleep, version и т.д.)
    # Исключаем And/Or: sqlglot относит их к Func
    if any(
        not isinstance(node, (exp.And, exp.Or))
        for node in where_node.find_all(exp.Func)
    ):
        raise ValueError('Вызов SQL-функций запрещён')

    # Белый список колонок
    for col in where_node.find_all(exp.Column):
        if col.table:
            raise ValueError(f'Недопустимое поле для фильтрации: {col.sql()}')
        if col.name.lower() not in ALLOWED_COLUMNS:
            raise ValueError(f'Недопустимое поле для фильтрации: {col.name}')


@lru_cache(maxsize=256)
def check_where_clause(audience: str) -> str:
    """Кешируемая валидация WHERE-фильтра аудитории."""
    try:
        _validate_where(audience)
    except ValueError as e:
        logger.warning('rejected audience filter %s: %s', audience[:100], e)
        raise
    return audience


Audience = Annotated[
    str,
    Field(min_length=3, max_length=500),
    AfterValidator(check_where_clause),
]


class GetPercentRequest(BaseModel):
    audience1: Audience = Field(examples=['Age BETWEEN 18 AND 35'])
    audience2: Audience = Field(examples=['Sex = 2 AND Age >= 18'])

"""Pydantic-модель запроса: валидация аудиторий.

Правила фильтра: одно WHERE-выражение (без stacked/UNION), без подзапросов
и функций, только колонки из ALLOWED_COLUMNS (sqlglot, postgres-диалект).
"""

from typing import Annotated

import sqlglot
from pydantic import AfterValidator, BaseModel, Field
from sqlglot import exp

from .constants import ALLOWED_COLUMNS


def check_where_clause(v: str) -> str:
    """Проверить WHERE-фильтр аудитории; при ошибке - ValueError."""
    if ';' in v:
        raise ValueError('Множественные запросы запрещены')

    try:
        # Оборачиваем условие в фиктивный SELECT для корректного парсинга
        parsed = sqlglot.parse_one(f'SELECT 1 FROM dummy WHERE {v}', read='postgres')
    except sqlglot.errors.ParseError as e:
        raise ValueError(f'Ошибка синтаксиса в WHERE: {e}') from e

    # UNION/stacked statements парсятся как узел, не Select
    if not isinstance(parsed, exp.Select):
        raise ValueError('Фильтр должен быть одним WHERE-выражением')

    where_node = parsed.find(exp.Where)
    if where_node is None:
        raise ValueError('Условие WHERE не распознано')

    # Запрещаем подзапросы (SELECT внутри WHERE)
    if where_node.find(exp.Select):
        raise ValueError('Подзапросы в фильтрах запрещены')

    # Запрещаем вызовы функций (например, pg_sleep, version и т.д.).
    # Исключаем And/Or: sqlglot относит их к Func как бинарные операторы.
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

    return v


Audience = Annotated[
    str,
    Field(min_length=3, max_length=500),
    AfterValidator(check_where_clause),
]


class GetPercentRequest(BaseModel):
    """Параметры GET /getPercent: обе аудитории валидируются при разборе."""

    audience1: Audience = Field(examples=['Age BETWEEN 18 AND 35'])
    audience2: Audience = Field(examples=['Sex = 2 AND Age >= 18'])

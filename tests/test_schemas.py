"""Юнит-тесты валидации аудиторий (app/schemas.py)."""

import pytest
from pydantic import ValidationError

from app.schemas import GetPercentRequest

# Валидный фильтр-ссылка для парной проверки обеих аудиторий.
REFERENCE = 'age = 1'

# Валидные фильтры: проходят валидацию и возвращаются без изменений.
VALID_CASES = [
    'Age BETWEEN 18 AND 35',  # пример из ТЗ
    'Sex = 2 AND Age >= 18',  # пример из ТЗ
    'age >= 18',
    'AGE <> 18',
    'sex in (1, 2)',
    'age NOT IN (18, 20)',
    'age < 18 OR age > 65',
    '(age = 1 OR age = 2) AND sex = 1',
    'NOT sex = 2',
    'not not sex = 2',
    'age = 1 AND age = 2 AND sex = 1',
    'Age between 18 and 35 AND Sex IN (1)',
    'age = -1',
    'age = 21.5',
    'age = 0',
    'age = 2147483647',
    'age is null',
    '1 = 1',
]

# (фильтр, причина отклонения)
INVALID_CASES = [
    ('', 'пустая строка'),
    ('   ', 'только пробелы'),
    ('age =', 'незавершённый предикат'),
    ('age = 1 OR', 'висящий OR'),
    ('(age = 1', 'незакрытая скобка'),
    ('Weight = 1', 'чужая колонка'),
    ('date = 20211213', 'чужая колонка'),
    ('respondent = 1', 'чужая колонка'),
    ('statistics.age = 1', 'квалифицированная колонка'),
    ('age = 1; DROP TABLE statistics', 'stacked queries'),
    ('age = 1 UNION SELECT 1', 'UNION'),
    (
        '1 = 1 UNION SELECT respondent, avg_weight FROM respondent_agg',
        'UNION с подходящими колонками',
    ),
    ('age > (SELECT max(age) FROM statistics)', 'подзапрос'),
    ('age IN (SELECT age FROM statistics)', 'подзапрос в IN'),
    ('pg_sleep(10)', 'вызов функции'),
    ('age = version()', 'вызов функции'),
]


@pytest.mark.parametrize('raw', VALID_CASES)
def test_valid_audience_accepted(raw: str) -> None:
    params = GetPercentRequest(audience1=raw, audience2=REFERENCE)
    assert params.audience1 == raw


@pytest.mark.parametrize(('raw', 'reason'), INVALID_CASES)
def test_invalid_audience_rejected(raw: str, reason: str) -> None:
    with pytest.raises(ValidationError):
        GetPercentRequest(audience1=raw, audience2=REFERENCE)
    with pytest.raises(ValidationError):
        GetPercentRequest(audience1=REFERENCE, audience2=raw)


def test_error_message_is_readable() -> None:
    with pytest.raises(ValidationError, match='Подзапросы'):
        GetPercentRequest(
            audience1='age > (SELECT max(age) FROM statistics)',
            audience2=REFERENCE,
        )

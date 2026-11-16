# Тестовое задание Okkam

API, вычисляющее процент вхождения одной аудитории в другую по
среднему Weight респондентов.

## Запуск

```bash
docker compose up
```

Без дополнительных действий: БД создаётся и наполняется сама
(`init-data/`), API стартует после готовности БД и слушает **80-й порт**.

```bash
curl "http://localhost/getPercent?audience1=Age%20BETWEEN%2018%20AND%2035&audience2=Sex%20=%202%20AND%20Age%20%3E=%2018"
# {"percent":0.4395}
```

## API

`GET /getPercent?audience1=...&audience2=...` — аудитории в формате
SQL-синтаксиса по колонкам `age`/`sex` (без подзапросов и функций),
ответ `{"percent": float}` в диапазоне 0..1.

| Код | Когда |
|-----|-------|
| 200 | результат |
| 422 | фильтр невалиден (синтаксис, чужая колонка, подзапрос, функция, stacked/UNION) / отсутствует параметр / нарушены ограничения длины |
| 503 | база данных недоступна |

Граничные случаи: идентичные аудитории → `1.0`; не пересекаются →
`0.0`; первая подмножество второй → `1.0`; первая аудитория пуста →
`0.0`. Инвариант: `0 <= percent <= 1`.

## Структура

```
app/
  main.py     FastAPI: сборка app, роутер из api.py; 503 при ошибках БД; логирование запросов
  api.py      хендлеры /getPercent, /health (APIRouter)
  service.py  бизнес-логика: запрос в БД -> процент
  schemas.py  pydantic-модель запроса: валидация аудиторий (sqlglot + whitelist)
  db.py       SQLAlchemy Core: пул, соединение (Depends), агрегирующий запрос, кэш-обёртка (lru_cache)
  exceptions.py кастомные исключения и их HTTP-обработчики (некорректный ответ БД -> 500)
  logger.py   логирование: общий логгер приложения (формат, уровень)
  config.py   настройки (pydantic-settings, POSTGRES_*)
init-data/
  01-schema.sql          таблица statistics
  02-copy.sql            загрузка data.csv (500 000 строк)
  03-respondent_agg.sql  предвычисленная respondent_agg
tests/
  test_schemas.py        юнит-тесты валидации аудиторий (модель)
  test_api.py            тесты эндпоинтов (TestClient, без БД)
```

Один запрос: pydantic-модель валидирует обе аудитории как query-параметры
(422 при ошибке) → SQL-запрос по `respondent_agg` — `SUM(avg_weight)
FILTER (WHERE …)` по сумме первой аудитории и по пересечению
(`filter1 AND filter2`; результат кэшируется парой аудиторий) →
`percent = sum_intersection / sum_audience1` (0.0 при сумме 0).

Ключевые моменты:

- **Расчёт выполняет БД** — валидированные фильтры подставляются в
  единый запрос с условной агрегацией (`SUM … FILTER`); данные в
  Python не переносятся.
- **`respondent_agg`** — avg(weight) по каждому респонденту,
  предвычислена на инициализации (age/sex константны на респондента),
  запрос идёт по 17k строк, а не по 500k.
- **Фильтры валидируются sqlglot** (postgres-диалект): разбор в AST,
  запрет подзапросов и функций, белый список колонок `age`/`sex`.
- **Кэш агрегатов** — отдельная обёртка `db.cached_audience_sums`
  (`lru_cache`) поверх обычного запроса: ключ — пара аудиторий, данные
  статичные, поэтому повторные условия не бьют по БД. Очистка:
  `cached_audience_sums.cache_clear()`.

## Тесты

```bash
uv sync
uv run pytest
```

## Линт и проверка типов

```bash
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
```

## Нагрузочное тестирование

Нагрузочный тест на [Locust](loadtest/README.md): пул ~70 разнообразных
условий (возраст/пол, AND/OR, длинные фильтры, граничные случаи),
статистика по каждому типу запроса (RPS, p50/p95/p99, ошибки).

```bash
uv run locust -f loadtest/locustfile.py --headless \
    -u 50 -r 10 --run-time 60s --host http://localhost:80 \
    --csv loadtest/report --html loadtest/report.html
```

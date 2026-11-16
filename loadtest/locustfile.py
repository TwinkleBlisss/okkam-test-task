"""Load test GET /getPercent (Locust).

Генерирует пул разнообразных пар (audience1, audience2), покрывающий
разные условия запросов: простые фильтры по age/sex, комбинации AND/OR,
длинные условия (почти до лимита 500 символов) и граничные случаи
(идентичные, не пересекающиеся и пустые аудитории). У каждого сценария
свой лейбл, поэтому в отчёте Locust видна статистика по типам запросов
отдельно (p50/p95/p99, RPS, ошибки).

Web UI (http://localhost:8089, задаётся число пользователей):
    uv run locust -f loadtest/locustfile.py --host http://localhost:80

Headless (50 юзеров, спавн 10/с, 60 секунд, CSV+HTML-отчёт):
    uv run locust -f loadtest/locustfile.py --headless \\
        -u 50 -r 10 --run-time 60s --host http://localhost:80 \\
        --csv loadtest/report --html loadtest/report.html
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from locust import HttpUser, between, task

AGE_MIN = 12
AGE_MAX = 99
SEED = 42  # воспроизводимый набор сценариев


@dataclass(frozen=True)
class Scenario:
    label: str
    audience1: str
    audience2: str


def _between(rng: random.Random) -> str:
    a = rng.randint(AGE_MIN, AGE_MAX)
    b = rng.randint(a, AGE_MAX)
    return f'Age BETWEEN {a} AND {b}'


def _long_or(rng: random.Random, limit: int = 480) -> str:
    """Длинное OR-условие из age-диапазонов, почти до лимита 500 символов."""
    parts: list[str] = []
    total = 0
    while True:
        a = rng.randint(AGE_MIN, AGE_MAX)
        b = rng.randint(a, AGE_MAX)
        part = f'Age >= {a} AND Age < {b}'
        add = len(part) + (len(' OR ') if parts else 0)
        if total + add > limit:
            break
        total += add
        parts.append(part)
    return ' OR '.join(parts)


def _in_list(rng: random.Random, count: int) -> str:
    values = ', '.join(str(rng.randint(AGE_MIN, AGE_MAX)) for _ in range(count))
    return f'Age IN ({values})'


def build_scenarios(seed: int = SEED) -> list[Scenario]:
    """Пул пар аудиторий с разными условиями запроса."""
    rng = random.Random(seed)
    scenarios: list[Scenario] = []

    sex = lambda: f'Sex = {rng.choice((1, 2))}'

    # Простые фильтры по возрасту
    for _ in range(10):
        x = rng.randint(AGE_MIN, AGE_MAX)
        scenarios.append(Scenario('age_eq', f'Age = {x}', _between(rng)))
    for _ in range(10):
        scenarios.append(Scenario('age_range', _between(rng), _between(rng)))
    for _ in range(10):
        scenarios.append(
            Scenario(
                'age_bounds',
                f'Age >= {rng.randint(AGE_MIN, AGE_MAX)}',
                f'Age <= {rng.randint(AGE_MIN, AGE_MAX)}',
            )
        )

    # Пол
    for _ in range(5):
        scenarios.append(Scenario('sex', sex(), sex()))

    # Комбинации AND / OR
    for _ in range(10):
        scenarios.append(
            Scenario('combined_and', f'{sex()} AND {_between(rng)}', _between(rng))
        )
    for _ in range(10):
        scenarios.append(
            Scenario(
                'or_cond',
                f'{sex()} OR Age >= {rng.randint(AGE_MIN, AGE_MAX)}',
                f'Age <= {rng.randint(AGE_MIN, AGE_MAX)}',
            )
        )

    # Тяжёлые по длине фильтры (почти до max_length=500)
    for _ in range(5):
        scenarios.append(Scenario('long_or', _long_or(rng), _between(rng)))
    for _ in range(5):
        scenarios.append(
            Scenario('in_list', _in_list(rng, rng.randint(10, 25)), _between(rng))
        )

    # Граничные случаи: идентичные -> 1.0, не пересекающиеся -> 0.0,
    # пустая первая аудитория -> 0.0, полная против полной -> 1.0
    same = _between(rng)
    scenarios.append(Scenario('edge_identical', same, same))
    scenarios.append(Scenario('edge_disjoint', 'Sex = 1 AND Age >= 50', 'Sex = 2'))
    scenarios.append(Scenario('edge_empty', f'Age < {AGE_MIN}', _between(rng)))
    scenarios.append(Scenario('edge_full', f'Age >= {AGE_MIN}', f'Age <= {AGE_MAX}'))
    return scenarios


SCENARIOS = build_scenarios()


class PercentUser(HttpUser):
    """Виртуальный пользователь: жмёт /getPercent на случайных сценариях."""

    wait_time = between(0, 0.1)

    @task(10)
    def get_percent(self):
        s = random.choice(SCENARIOS)
        res = self.client.get(
            '/getPercent',
            params={'audience1': s.audience1, 'audience2': s.audience2},
            name=f'/getPercent[{s.label}]',
            catch_response=True,
        )
        with res:
            if res.status_code != 200:
                res.failure(f'HTTP {res.status_code}')
                return
            percent = res.json().get('percent')
            if not isinstance(percent, (int, float)) or not 0.0 <= percent <= 1.0:
                res.failure(f'percent вне диапазона 0..1: {percent!r}')

    @task(1)
    def health(self):
        self.client.get('/health', name='/health')

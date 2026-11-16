"""Тесты эндпоинтов через TestClient (реальная БД и пул не нужны)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app import api as api_module
from app import db as db_module
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_audience_cache():
    """Каждый тест работает с пустым кэшем аудиторий (lru_cache)."""
    db_module.cached_audience_sums.cache_clear()
    yield
    db_module.cached_audience_sums.cache_clear()


def test_invalid_audience_rejected() -> None:
    resp = client.get(
        '/getPercent',
        params={'audience1': 'pg_sleep(10)', 'audience2': 'age = 1'},
    )
    assert resp.status_code == 422


def test_missing_audience_rejected() -> None:
    resp = client.get('/getPercent', params={'audience1': 'age = 1'})
    assert resp.status_code == 422


def test_valid_audience_returns_percent(monkeypatch) -> None:
    monkeypatch.setattr(api_module, 'get_audience_percent', lambda *args: 0.4395)
    resp = client.get(
        '/getPercent',
        params={
            'audience1': 'Age BETWEEN 18 AND 35',
            'audience2': 'Sex = 2 AND Age >= 18',
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {'percent': 0.4395}


def test_database_unavailable_returns_500(monkeypatch) -> None:
    class _BrokenEngine:
        def connect(self) -> None:
            raise SQLAlchemyError('no database')

    monkeypatch.setattr(db_module, 'engine', _BrokenEngine())
    resp = client.get(
        '/getPercent', params={'audience1': 'age = 1', 'audience2': 'age = 1'}
    )
    assert resp.status_code == 500
    assert resp.json() == {'message': 'An unexpected error has occurred.'}

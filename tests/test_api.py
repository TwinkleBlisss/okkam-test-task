"""Тесты эндпоинтов через TestClient (БД и реальный пул не нужны)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app import main as main_module
from app.db import get_db_connection
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _connection_override():
    """Подменяем зависимость соединения: тесты не трогают реальный пул/БД."""

    def _fake_connection() -> Iterator[object]:
        yield object()

    app.dependency_overrides[get_db_connection] = _fake_connection
    yield
    app.dependency_overrides.pop(get_db_connection, None)


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
    monkeypatch.setattr(main_module, 'get_audience_percent', lambda *args: 0.4395)
    resp = client.get(
        '/getPercent',
        params={
            'audience1': 'Age BETWEEN 18 AND 35',
            'audience2': 'Sex = 2 AND Age >= 18',
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {'percent': 0.4395}


def test_database_unavailable_returns_503() -> None:
    def _broken_connection() -> Iterator[None]:
        raise SQLAlchemyError('no database')
        yield

    app.dependency_overrides[get_db_connection] = _broken_connection
    resp = client.get(
        '/getPercent', params={'audience1': 'age = 1', 'audience2': 'age = 1'}
    )
    assert resp.status_code == 503
    assert resp.json() == {'detail': 'database unavailable'}

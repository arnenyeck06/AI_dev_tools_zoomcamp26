from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import dates
from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def _pinned_today(monkeypatch: pytest.MonkeyPatch):
    # Seed data assumes "today" is partway through September 2026 (see
    # app/store.py's 2026-09 rows). Pin it so trends/suggestions tests
    # are deterministic regardless of the real wall-clock date.
    monkeypatch.setattr(dates, "today", lambda: date(2026, 9, 16))


@pytest.fixture(autouse=True)
def _reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

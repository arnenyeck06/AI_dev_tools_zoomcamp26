# Small date helpers mirroring frontend/src/lib/date.ts, so the mock
# backend's month math (trends, recurring-bill suggestions) matches the
# frontend exactly. `today()` is a seam tests monkeypatch to pin "now".

from __future__ import annotations

from calendar import monthrange
from datetime import date


def today() -> date:
    return date.today()


def month_key_of(date_iso: str) -> str:
    return date_iso[:7]


def current_month_key() -> str:
    return today().strftime("%Y-%m")


def add_months(month_key: str, delta: int) -> str:
    year, month = (int(p) for p in month_key.split("-"))
    total = year * 12 + (month - 1) + delta
    year, month = divmod(total, 12)
    return f"{year:04d}-{month + 1:02d}"


def days_in_month(month_key: str) -> int:
    year, month = (int(p) for p in month_key.split("-"))
    return monthrange(year, month)[1]


def date_in_month(month_key: str, day: int) -> str:
    clamped = min(max(day, 1), days_in_month(month_key))
    return f"{month_key}-{clamped:02d}"

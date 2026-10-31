"""Rule thresholds (spec §F6): each rule just below and just above its threshold."""
from datetime import datetime, timedelta, timezone

import pytest

from flags import long_wait_flag, placement_flags

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def ago(**kwargs):
    return NOW - timedelta(**kwargs)


def severities(flags):
    return [severity for _, severity in flags]


def test_no_flags_for_a_normal_first_order():
    assert placement_flags(quantity=2, item="Burger", placed_at=NOW, earlier=[]) == []


@pytest.mark.parametrize("quantity, flagged", [(20, False), (21, True)])
def test_large_quantity(quantity, flagged):
    flags = placement_flags(quantity=quantity, item="Burger", placed_at=NOW, earlier=[])
    assert severities(flags) == (["medium"] if flagged else [])


@pytest.mark.parametrize("earlier, flagged", [
    ([("Fries", ago(minutes=9))], False),                              # 2 orders: below
    ([("Fries", ago(minutes=9)), ("Salad", ago(minutes=5))], True),    # 3 orders in 10 min
    ([("Fries", ago(minutes=11)), ("Salad", ago(minutes=5))], False),  # one is outside the window
])
def test_burst(earlier, flagged):
    flags = placement_flags(quantity=1, item="Burger", placed_at=NOW, earlier=earlier)
    assert severities(flags) == (["high"] if flagged else [])


@pytest.mark.parametrize("earlier, flagged", [
    ([("Burger", ago(seconds=119))], True),
    ([("Burger", ago(seconds=121))], False),
    ([("Fries", ago(seconds=30))], False),   # same phone, different item
    ([("burger ", ago(seconds=30))], True),  # case and spacing don't matter
])
def test_duplicate(earlier, flagged):
    flags = placement_flags(quantity=1, item="Burger", placed_at=NOW, earlier=earlier)
    assert severities(flags) == (["medium"] if flagged else [])


def test_reasons_do_not_contain_customer_data():
    earlier = [("Burger", ago(minutes=1)), ("Burger", ago(minutes=2))]
    flags = placement_flags(quantity=50, item="Burger", placed_at=NOW, earlier=earlier)

    assert severities(flags) == ["high", "medium", "medium"]
    assert all("555" not in reason for reason, _ in flags)


@pytest.mark.parametrize("waited, usual, flagged", [
    (timedelta(minutes=16), [timedelta(minutes=7)], True),    # > 15 min and > 2x median
    (timedelta(minutes=15), [timedelta(minutes=5)], False),   # not over 15 min
    (timedelta(minutes=20), [timedelta(minutes=10)], False),  # not over 2x median
    (timedelta(minutes=21), [timedelta(minutes=10)], True),
    (timedelta(minutes=16), [], True),                        # no history yet: 15 min applies
    (timedelta(minutes=30), [timedelta(minutes=2), timedelta(minutes=10), timedelta(minutes=20)], True),
])
def test_long_wait(waited, usual, flagged):
    flag = long_wait_flag(waited, usual)
    assert (flag is not None) == flagged
    if flag:
        assert flag[1] == "low"

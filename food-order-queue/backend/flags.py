"""Rule-based anomaly flags (spec §F6).

Pure functions: the caller passes the data and the current time, so the thresholds
are easy to test. A flag is (reason, severity). Reasons never include customer data.
"""
from datetime import timedelta
from statistics import median

BURST_ORDERS = 3
BURST_WINDOW = timedelta(minutes=10)
DUPLICATE_WINDOW = timedelta(minutes=2)
LARGE_QUANTITY = 20
LONG_WAIT_MINIMUM = timedelta(minutes=15)
LONG_WAIT_FACTOR = 2


def same_item(a, b):
    return a.strip().casefold() == b.strip().casefold()


def placement_flags(quantity, item, placed_at, earlier):
    """Flags for a new order. `earlier` is [(item, created_at)] of the same phone's previous orders."""
    flags = []
    recent = sum(1 for _, at in earlier if placed_at - at <= BURST_WINDOW) + 1  # including this one
    if recent >= BURST_ORDERS:
        flags.append((f"{recent} orders from the same phone in {BURST_WINDOW.seconds // 60} minutes", "high"))
    if any(same_item(item, other) and placed_at - at <= DUPLICATE_WINDOW for other, at in earlier):
        flags.append((f"Same item ordered by the same phone within {DUPLICATE_WINDOW.seconds // 60} minutes", "medium"))
    if quantity > LARGE_QUANTITY:
        flags.append((f"Large quantity: {quantity} (more than {LARGE_QUANTITY})", "medium"))
    return flags


def long_wait_flag(waited, usual_waits):
    """Flag for an order still waiting much longer than usual, or None.

    `usual_waits` are the waits of recently served orders. With no history yet,
    only the 15-minute minimum applies.
    """
    usual = median(usual_waits) if usual_waits else timedelta(0)
    if waited > LONG_WAIT_MINIMUM and waited > LONG_WAIT_FACTOR * usual:
        return (f"Waiting {minutes(waited)} min, usual wait is {minutes(usual)} min", "low")
    return None


def minutes(delta):
    return int(delta.total_seconds() // 60)

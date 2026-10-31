from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "engine", create_engine(f"sqlite:///{tmp_path / 'test.db'}"))
    with TestClient(main.app) as test_client:
        yield test_client


def place(client, name, **extra):
    order = {"customer_name": name, "phone": "555-0100", "item": "Burger", **extra}
    response = client.post("/api/orders", json=order)
    assert response.status_code == 201, response.text
    return response.json()


def test_new_orders_get_queue_positions(client):
    first, second = place(client, "Ana"), place(client, "Ben")

    assert (first["position"], second["position"]) == (1, 2)
    assert first["status"] == "waiting"


def test_staff_serve_orders_first_in_first_out(client):
    ana, ben, cy = place(client, "Ana"), place(client, "Ben"), place(client, "Cy")

    served = client.post("/api/orders/next").json()

    assert served["id"] == ana["id"]
    assert served["status"] == "in_progress"
    assert client.get(f"/api/orders/{ben['id']}").json()["position"] == 1
    assert client.get(f"/api/orders/{cy['id']}").json()["position"] == 2
    assert client.post("/api/orders/next").json()["id"] == ben["id"]


def test_complete_order(client):
    order = place(client, "Ana")
    assert client.post(f"/api/orders/{order['id']}/done").status_code == 409  # not started yet

    client.post("/api/orders/next")
    done = client.post(f"/api/orders/{order['id']}/done")

    assert done.status_code == 200
    assert done.json()["status"] == "done"


def test_list_waiting_orders_in_arrival_order(client):
    for name in ("Ana", "Ben", "Cy"):
        place(client, name)
    client.post("/api/orders/next")

    waiting = client.get("/api/orders", params={"status": "waiting"}).json()

    assert [o["customer_name"] for o in waiting] == ["Ben", "Cy"]
    assert [o["position"] for o in waiting] == [1, 2]


def test_empty_queue(client):
    assert client.post("/api/orders/next").status_code == 404


@pytest.mark.parametrize("bad", [
    {"customer_name": ""},
    {"phone": "12"},
    {"quantity": 0},
    {"quantity": 101},
])
def test_rejects_invalid_orders(client, bad):
    order = {"customer_name": "Ana", "phone": "555-0100", "item": "Burger", **bad}
    assert client.post("/api/orders", json=order).status_code == 422


def test_missing_order(client):
    assert client.get("/api/orders/999").status_code == 404


@pytest.fixture
def clock(monkeypatch):
    """Lets a test move time forward: clock.now += timedelta(...)."""
    class Clock:
        now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(main, "utcnow", lambda: Clock.now)
    return Clock


def flag_reasons(order):
    return [(f["source"], f["severity"]) for f in order["flags"]]


def test_large_order_is_flagged_and_flag_is_saved(client):
    order = place(client, "Ana", quantity=21)

    assert flag_reasons(order) == [("rule", "medium")]
    assert client.get(f"/api/orders/{order['id']}").json()["flags"] == order["flags"]
    assert client.get("/api/orders").json()[0]["flags"] == order["flags"]


def test_repeat_orders_from_one_phone_are_flagged(client):
    first = place(client, "Ana")
    second = place(client, "Ana")         # same item within 2 minutes
    third = place(client, "Ana", item="Fries")  # third order in 10 minutes
    other = place(client, "Ben", phone="555-0199")

    assert first["flags"] == []
    assert flag_reasons(second) == [("rule", "medium")]
    assert flag_reasons(third) == [("rule", "high")]
    assert other["flags"] == []
    assert all("555" not in f["reason"] and "Ana" not in f["reason"] for f in second["flags"] + third["flags"])


def test_flags_never_change_fifo_order(client):
    normal = place(client, "Ana")
    flagged = place(client, "Ben", phone="555-0199", quantity=50)
    later = place(client, "Cy", phone="555-0142")

    assert flagged["position"] == 2
    assert [client.post("/api/orders/next").json()["id"] for _ in range(3)] == [
        normal["id"], flagged["id"], later["id"],
    ]


def test_long_wait_flag_compares_with_usual_wait(client, clock):
    served = place(client, "Ana")
    waiting = place(client, "Ben", phone="555-0199")
    clock.now += timedelta(minutes=5)
    client.post("/api/orders/next")  # usual wait is now 5 minutes

    clock.now += timedelta(minutes=9)  # Ben has waited 14 minutes
    assert client.get(f"/api/orders/{waiting['id']}").json()["flags"] == []

    clock.now += timedelta(minutes=2)  # 16 minutes: over 15 and over 2 x 5
    assert flag_reasons(client.get(f"/api/orders/{waiting['id']}").json()) == [("rule", "low")]
    assert client.get(f"/api/orders/{served['id']}").json()["flags"] == []  # only waiting orders

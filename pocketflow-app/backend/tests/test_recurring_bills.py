def test_list_recurring_bills_returns_the_three_templates(client):
    resp = client.get("/recurring-bills")
    assert resp.status_code == 200
    body = resp.json()
    assert [b["id"] for b in body] == ["rb1", "rb2", "rb3"]


def test_suggestions_are_pending_for_current_month_seed(client):
    # September (the pinned "today") deliberately has no rent/utilities/
    # streaming expenses seeded -- they should show up as pending.
    resp = client.get("/recurring-bills/suggestions", params={"month": "2026-09"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    statuses = {s["bill"]["id"]: s["status"] for s in body}
    assert statuses == {"rb1": "pending", "rb2": "pending", "rb3": "pending"}

    by_id = {s["bill"]["id"]: s for s in body}
    assert by_id["rb1"]["suggestedDate"] == "2026-09-01"
    assert by_id["rb2"]["suggestedDate"] == "2026-09-20"
    assert by_id["rb3"]["suggestedDate"] == "2026-09-03"


def test_suggestions_are_confirmed_for_a_month_with_a_linked_expense(client):
    resp = client.get("/recurring-bills/suggestions", params={"month": "2026-08"})
    assert resp.status_code == 200
    by_id = {s["bill"]["id"]: s for s in resp.json()}

    assert by_id["rb1"]["status"] == "confirmed"
    assert by_id["rb1"]["expenseAmount"] == 1800
    assert by_id["rb1"]["expenseDate"] == "2026-08-01"
    assert by_id["rb1"]["expenseId"]


def test_confirm_creates_expense_and_flips_status(client):
    resp = client.post(
        "/recurring-bills/rb2/confirm",
        params={"month": "2026-09"},
        json={"amount": 101.25, "date": "2026-09-20", "payerId": "m2", "note": "AC"},
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["categoryId"] == "utilities"
    assert created["amount"] == 101.25
    assert created["sourceBillId"] == "rb2"

    suggestions = client.get(
        "/recurring-bills/suggestions", params={"month": "2026-09"}
    ).json()
    rb2 = next(s for s in suggestions if s["bill"]["id"] == "rb2")
    assert rb2["status"] == "confirmed"
    assert rb2["expenseId"] == created["id"]


def test_confirm_unknown_bill_returns_404(client):
    resp = client.post(
        "/recurring-bills/does-not-exist/confirm",
        params={"month": "2026-09"},
        json={"amount": 10, "date": "2026-09-01", "payerId": "m1"},
    )
    assert resp.status_code == 404


def test_dismiss_then_undo_round_trips_to_pending(client):
    month = "2026-09"
    dismiss = client.post("/recurring-bills/rb3/dismiss", params={"month": month})
    assert dismiss.status_code == 204

    suggestions = client.get(
        "/recurring-bills/suggestions", params={"month": month}
    ).json()
    rb3 = next(s for s in suggestions if s["bill"]["id"] == "rb3")
    assert rb3["status"] == "dismissed"

    undo = client.post("/recurring-bills/rb3/undo", params={"month": month})
    assert undo.status_code == 204

    suggestions = client.get(
        "/recurring-bills/suggestions", params={"month": month}
    ).json()
    rb3 = next(s for s in suggestions if s["bill"]["id"] == "rb3")
    assert rb3["status"] == "pending"


def test_undo_confirmed_bill_removes_its_expense(client):
    month = "2026-09"
    confirmed = client.post(
        "/recurring-bills/rb1/confirm",
        params={"month": month},
        json={"amount": 1800, "date": "2026-09-01", "payerId": "m1"},
    ).json()

    undo = client.post("/recurring-bills/rb1/undo", params={"month": month})
    assert undo.status_code == 204

    listed = client.get("/expenses", params={"month": month}).json()
    assert all(e["id"] != confirmed["id"] for e in listed)

    suggestions = client.get(
        "/recurring-bills/suggestions", params={"month": month}
    ).json()
    rb1 = next(s for s in suggestions if s["bill"]["id"] == "rb1")
    assert rb1["status"] == "pending"

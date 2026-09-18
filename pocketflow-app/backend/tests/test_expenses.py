def test_list_expenses_returns_seeded_data(client):
    resp = client.get("/expenses")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 55  # 10*4 + 9 (May) + 6 (Sept partial)


def test_list_expenses_filters_by_month(client):
    resp = client.get("/expenses", params={"month": "2026-09"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 6
    assert all(e["date"].startswith("2026-09") for e in body)


def test_list_expenses_for_month_with_no_data_is_empty(client):
    resp = client.get("/expenses", params={"month": "2026-01"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_rejects_malformed_month(client):
    resp = client.get("/expenses", params={"month": "September"})
    assert resp.status_code == 422


def test_create_expense_assigns_id_and_persists(client):
    payload = {
        "amount": 12.5,
        "categoryId": "dining",
        "date": "2026-09-10",
        "payerId": "m1",
        "note": "Coffee",
    }
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"]
    assert created["amount"] == 12.5
    assert created["categoryId"] == "dining"
    assert created["date"] == "2026-09-10"
    assert created["payerId"] == "m1"
    assert created["note"] == "Coffee"
    assert created.get("sourceBillId") is None

    listed = client.get("/expenses", params={"month": "2026-09"}).json()
    assert any(e["id"] == created["id"] for e in listed)


def test_create_expense_rejects_invalid_category(client):
    payload = {
        "amount": 12.5,
        "categoryId": "not-a-category",
        "date": "2026-09-10",
        "payerId": "m1",
    }
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 422


def test_create_expense_rejects_non_positive_amount(client):
    payload = {
        "amount": 0,
        "categoryId": "dining",
        "date": "2026-09-10",
        "payerId": "m1",
    }
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 422


def test_update_expense_patches_only_given_fields(client):
    created = client.post(
        "/expenses",
        json={
            "amount": 20,
            "categoryId": "dining",
            "date": "2026-09-10",
            "payerId": "m1",
        },
    ).json()

    resp = client.patch(f"/expenses/{created['id']}", json={"amount": 25})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["amount"] == 25
    assert updated["categoryId"] == "dining"
    assert updated["date"] == "2026-09-10"
    assert updated["payerId"] == "m1"


def test_update_missing_expense_returns_404(client):
    resp = client.patch("/expenses/does-not-exist", json={"amount": 5})
    assert resp.status_code == 404


def test_delete_expense_removes_it(client):
    created = client.post(
        "/expenses",
        json={
            "amount": 20,
            "categoryId": "dining",
            "date": "2026-09-10",
            "payerId": "m1",
        },
    ).json()

    resp = client.delete(f"/expenses/{created['id']}")
    assert resp.status_code == 204

    listed = client.get("/expenses", params={"month": "2026-09"}).json()
    assert all(e["id"] != created["id"] for e in listed)


def test_delete_missing_expense_returns_404(client):
    resp = client.delete("/expenses/does-not-exist")
    assert resp.status_code == 404

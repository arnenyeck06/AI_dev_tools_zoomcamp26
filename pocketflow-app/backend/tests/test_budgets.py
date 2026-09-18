def test_list_budgets_returns_all_eight_categories(client):
    resp = client.get("/budgets")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 8
    by_id = {b["categoryId"]: b["amount"] for b in body}
    assert by_id["rent"] == 1800
    assert by_id["groceries"] == 500


def test_set_budget_updates_existing_category(client):
    resp = client.put("/budgets/groceries", json={"amount": 550})
    assert resp.status_code == 200
    assert resp.json() == {"categoryId": "groceries", "amount": 550}

    listed = client.get("/budgets").json()
    by_id = {b["categoryId"]: b["amount"] for b in listed}
    assert by_id["groceries"] == 550
    assert len(listed) == 8  # replaced, not duplicated


def test_set_budget_rejects_unknown_category(client):
    resp = client.put("/budgets/not-a-category", json={"amount": 100})
    assert resp.status_code == 422

def test_list_categories_returns_all_eight_in_fixed_order(client):
    resp = client.get("/categories")
    assert resp.status_code == 200

    body = resp.json()
    assert len(body) == 8
    assert [c["id"] for c in body] == [
        "rent", "utilities", "groceries", "dining",
        "transport", "entertainment", "health", "other",
    ]
    assert [c["slot"] for c in body] == list(range(1, 9))

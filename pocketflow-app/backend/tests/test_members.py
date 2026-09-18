def test_list_members_returns_the_household(client):
    resp = client.get("/members")
    assert resp.status_code == 200

    body = resp.json()
    assert body == [
        {"id": "m1", "name": "Alex"},
        {"id": "m2", "name": "Sam"},
    ]

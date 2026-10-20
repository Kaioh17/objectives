from tests.conftest import CREDS, bearer

API = "/api/v1"
NEW = {"title": "Read", "description": "20 pages", "minutes": 30, "mode": "daily"}


def test_crud(signed_in):
    created = signed_in.post(f"{API}/objectives", json=NEW)
    assert created.status_code == 201
    obj = created.json()
    assert obj["archived"] is False and obj["event_id"] is None
    assert obj["created_at"].endswith("Z") or obj["created_at"].endswith("+00:00")

    signed_in.post(f"{API}/objectives", json={**NEW, "title": "Run", "mode": "weekly"})
    titles = [o["title"] for o in signed_in.get(f"{API}/objectives").json()]
    assert titles == ["Run", "Read"]
    weekly = signed_in.get(f"{API}/objectives", params={"mode": "weekly"}).json()
    assert [o["title"] for o in weekly] == ["Run"]

    patched = signed_in.patch(f"{API}/objectives/{obj['id']}", json={"archived": True})
    assert patched.json()["archived"] is True
    assert patched.json()["title"] == "Read"
    active = signed_in.get(f"{API}/objectives", params={"archived": False}).json()
    assert [o["title"] for o in active] == ["Run"]

    assert signed_in.delete(f"{API}/objectives/{obj['id']}").status_code == 204
    assert signed_in.get(f"{API}/objectives/{obj['id']}").status_code == 404


def test_validation(signed_in):
    for bad in (
        {**NEW, "minutes": 4},
        {**NEW, "minutes": 1441},
        {**NEW, "title": ""},
        {**NEW, "mode": "yearly"},
    ):
        assert signed_in.post(f"{API}/objectives", json=bad).status_code == 422


def test_cannot_touch_another_users_objective(signed_in, client):
    obj = signed_in.post(f"{API}/objectives", json=NEW).json()
    signed_in.post(f"{API}/auth/logout")
    other = {"email": "b@example.com", "password": "supersecret"}
    bearer(client, client.post(f"{API}/auth/register", json=other).json()["access_token"])

    url = f"{API}/objectives/{obj['id']}"
    assert client.get(url).status_code == 404
    assert client.patch(url, json={"title": "mine"}).status_code == 404
    assert client.delete(url).status_code == 404
    assert client.get(f"{API}/objectives").json() == []
    assert CREDS["email"] != other["email"]

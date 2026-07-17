"""Tests for /api/v1/rounds endpoints."""


def _create_season(client, api_key_header, year=2026):
    resp = client.post("/api/v1/seasons/", json={"year": year}, headers=api_key_header)
    return resp.json()["id"]


def _round_payload(season_id):
    return {
        "season_id": season_id,
        "round_number": 1,
        "name": "Melbourne Round",
        "circuit_name": "Albert Park Circuit",
        "city": "Melbourne",
        "country": "Australia",
        "timezone": "Australia/Melbourne",
    }


def test_create_round(client, api_key_header):
    season_id = _create_season(client, api_key_header)
    resp = client.post(
        "/api/v1/rounds/", json=_round_payload(season_id), headers=api_key_header
    )
    assert resp.status_code == 201
    assert resp.json()["city"] == "Melbourne"


def test_create_round_invalid_season(client, api_key_header):
    resp = client.post(
        "/api/v1/rounds/", json=_round_payload(999), headers=api_key_header
    )
    assert resp.status_code == 404


def test_list_rounds_filter_by_season(client, api_key_header):
    s1 = _create_season(client, api_key_header, 2025)
    s2 = _create_season(client, api_key_header, 2026)

    payload1 = _round_payload(s1)
    payload2 = _round_payload(s2)
    payload2["name"] = "Sakhir Round"

    client.post("/api/v1/rounds/", json=payload1, headers=api_key_header)
    client.post("/api/v1/rounds/", json=payload2, headers=api_key_header)

    resp = client.get(f"/api/v1/rounds/?season_id={s1}")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Melbourne Round"

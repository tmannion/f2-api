"""Tests for /api/v1/results endpoints."""


def _seed_session(client, api_key_header):
    """Create season → round → session, return session_id, driver_id, team_id."""
    season = client.post(
        "/api/v1/seasons/", json={"year": 2026}, headers=api_key_header
    ).json()
    round_obj = client.post(
        "/api/v1/rounds/",
        json={
            "season_id": season["id"],
            "round_number": 1,
            "name": "Test Round",
            "circuit_name": "Test Circuit",
            "city": "TestCity",
            "country": "TestCountry",
            "timezone": "UTC",
        },
        headers=api_key_header,
    ).json()
    session = client.post(
        "/api/v1/sessions/",
        json={
            "round_id": round_obj["id"],
            "type": "SPRINT",
            "scheduled_at_utc": "2026-03-07T03:00:00",
            "status": "COMPLETED",
            "is_reversed_grid": True,
        },
        headers=api_key_header,
    ).json()
    driver = client.post(
        "/api/v1/drivers/",
        json={
            "first_name": "Test",
            "last_name": "Driver",
            "nationality": "British",
            "number": 99,
        },
        headers=api_key_header,
    ).json()
    team = client.post(
        "/api/v1/teams/",
        json={"name": "Test Racing", "nationality": "British"},
        headers=api_key_header,
    ).json()
    return session["id"], driver["id"], team["id"]


def test_create_result(client, api_key_header):
    session_id, driver_id, team_id = _seed_session(client, api_key_header)
    resp = client.post(
        "/api/v1/results/",
        json={
            "session_id": session_id,
            "driver_id": driver_id,
            "team_id": team_id,
            "grid_position": 2,
            "finish_position": 1,
            "status": "FINISHED",
            "points": 10,
            "has_fastest_lap": True,
            "fastest_lap_time": "1:32.000",
        },
        headers=api_key_header,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["finish_position"] == 1
    assert data["points"] == 10
    assert data["has_fastest_lap"] is True


def test_create_result_invalid_session(client, api_key_header):
    _, driver_id, team_id = _seed_session(client, api_key_header)
    resp = client.post(
        "/api/v1/results/",
        json={
            "session_id": 999,
            "driver_id": driver_id,
            "team_id": team_id,
            "grid_position": 1,
            "finish_position": 1,
            "status": "FINISHED",
            "points": 10,
            "has_fastest_lap": False,
        },
        headers=api_key_header,
    )
    assert resp.status_code == 404


def test_create_result_dnf(client, api_key_header):
    session_id, driver_id, team_id = _seed_session(client, api_key_header)
    resp = client.post(
        "/api/v1/results/",
        json={
            "session_id": session_id,
            "driver_id": driver_id,
            "team_id": team_id,
            "grid_position": 3,
            "finish_position": None,
            "status": "DNF",
            "points": 0,
            "has_fastest_lap": False,
        },
        headers=api_key_header,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["finish_position"] is None
    assert data["status"] == "DNF"


def test_list_results_filter_by_session(client, api_key_header):
    session_id, driver_id, team_id = _seed_session(client, api_key_header)
    client.post(
        "/api/v1/results/",
        json={
            "session_id": session_id,
            "driver_id": driver_id,
            "team_id": team_id,
            "grid_position": 1,
            "finish_position": 1,
            "status": "FINISHED",
            "points": 10,
            "has_fastest_lap": False,
        },
        headers=api_key_header,
    )

    resp = client.get(f"/api/v1/results/?session_id={session_id}")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["session_id"] == session_id

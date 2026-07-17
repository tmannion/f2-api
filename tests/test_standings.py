"""Tests for /api/v1/standings endpoint — the calculated standings."""


def _seed_full_round(client, api_key_header):
    """Create a season, round, session, drivers, teams, and results."""
    # Season
    season = client.post(
        "/api/v1/seasons/", json={"year": 2026}, headers=api_key_header
    ).json()

    # Round
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

    # Feature session
    session = client.post(
        "/api/v1/sessions/",
        json={
            "round_id": round_obj["id"],
            "type": "FEATURE",
            "scheduled_at_utc": "2026-03-08T00:00:00",
            "status": "COMPLETED",
            "is_reversed_grid": False,
        },
        headers=api_key_header,
    ).json()

    # Drivers and teams
    driver1 = client.post(
        "/api/v1/drivers/",
        json={
            "first_name": "Nikola",
            "last_name": "Tsolov",
            "nationality": "Bulgarian",
            "number": 6,
        },
        headers=api_key_header,
    ).json()

    driver2 = client.post(
        "/api/v1/drivers/",
        json={
            "first_name": "Rafael",
            "last_name": "Camara",
            "nationality": "Brazilian",
            "number": 1,
        },
        headers=api_key_header,
    ).json()

    team1 = client.post(
        "/api/v1/teams/",
        json={"name": "Campos Racing", "nationality": "Spanish"},
        headers=api_key_header,
    ).json()

    team2 = client.post(
        "/api/v1/teams/",
        json={"name": "Invicta Racing", "nationality": "British"},
        headers=api_key_header,
    ).json()

    # Results — Tsolov P1 (25pts), Camara P2 (18pts)
    client.post(
        "/api/v1/results/",
        json={
            "session_id": session["id"],
            "driver_id": driver1["id"],
            "team_id": team1["id"],
            "grid_position": 5,
            "finish_position": 1,
            "status": "FINISHED",
            "points": 25,
            "has_fastest_lap": False,
            "fastest_lap_time": None,
        },
        headers=api_key_header,
    )
    client.post(
        "/api/v1/results/",
        json={
            "session_id": session["id"],
            "driver_id": driver2["id"],
            "team_id": team2["id"],
            "grid_position": 6,
            "finish_position": 2,
            "status": "FINISHED",
            "points": 18,
            "has_fastest_lap": True,
            "fastest_lap_time": "1:31.500",
        },
        headers=api_key_header,
    )

    return season["id"]


def test_standings_calculates_correctly(client, api_key_header):
    season_id = _seed_full_round(client, api_key_header)

    resp = client.get(f"/api/v1/standings/?season_id={season_id}")
    assert resp.status_code == 200

    data = resp.json()
    assert data["season_year"] == 2026
    assert len(data["standings"]) == 2

    # Tsolov should be P1 with 25 points
    assert data["standings"][0]["position"] == 1
    assert data["standings"][0]["driver_name"] == "Nikola Tsolov"
    assert data["standings"][0]["points"] == 25
    assert data["standings"][0]["wins"] == 1

    # Camara should be P2 with 18 points
    assert data["standings"][1]["position"] == 2
    assert data["standings"][1]["driver_name"] == "Rafael Camara"
    assert data["standings"][1]["points"] == 18
    assert data["standings"][1]["wins"] == 0
    assert data["standings"][1]["podiums"] == 1


def test_standings_season_not_found(client):
    resp = client.get("/api/v1/standings/?season_id=999")
    assert resp.status_code == 404

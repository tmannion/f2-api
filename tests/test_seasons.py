"""Tests for /api/v1/seasons endpoints."""


def test_list_seasons_empty(client):
    resp = client.get("/api/v1/seasons/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_season(client, api_key_header):
    resp = client.post("/api/v1/seasons/", json={"year": 2026}, headers=api_key_header)
    assert resp.status_code == 201
    data = resp.json()
    assert data["year"] == 2026
    assert "id" in data


def test_create_season_duplicate(client, api_key_header):
    client.post("/api/v1/seasons/", json={"year": 2026}, headers=api_key_header)
    resp = client.post("/api/v1/seasons/", json={"year": 2026}, headers=api_key_header)
    assert resp.status_code == 409


def test_get_season(client, api_key_header):
    create_resp = client.post(
        "/api/v1/seasons/", json={"year": 2025}, headers=api_key_header
    )
    season_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/seasons/{season_id}")
    assert resp.status_code == 200
    assert resp.json()["year"] == 2025


def test_get_season_not_found(client):
    resp = client.get("/api/v1/seasons/999")
    assert resp.status_code == 404


def test_list_seasons_paginated(client, api_key_header):
    for year in range(2020, 2026):
        client.post("/api/v1/seasons/", json={"year": year}, headers=api_key_header)

    resp = client.get("/api/v1/seasons/?limit=2&offset=0")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 6
    assert data["limit"] == 2
    assert data["offset"] == 0

    resp2 = client.get("/api/v1/seasons/?limit=2&offset=4")
    data2 = resp2.json()
    assert len(data2["items"]) == 2
    assert data2["total"] == 6

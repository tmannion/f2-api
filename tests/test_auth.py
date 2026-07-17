"""Tests for API key authentication."""


def test_post_without_api_key_returns_401(client):
    resp = client.post("/api/v1/seasons/", json={"year": 2026})
    assert resp.status_code == 401


def test_post_with_wrong_api_key_returns_401(client):
    resp = client.post(
        "/api/v1/seasons/",
        json={"year": 2026},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_post_with_correct_api_key_succeeds(client, api_key_header):
    resp = client.post("/api/v1/seasons/", json={"year": 2026}, headers=api_key_header)
    assert resp.status_code == 201


def test_get_does_not_require_auth(client, api_key_header):
    client.post("/api/v1/seasons/", json={"year": 2026}, headers=api_key_header)
    resp = client.get("/api/v1/seasons/")
    assert resp.status_code == 200

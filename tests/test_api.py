from __future__ import annotations

from api.app.models.tariffs import FreshnessStatus


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "OpenWatt API"


def test_latest_tariffs_default_filters(client):
    response = client.get("/v1/tariffs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data and len(data["items"]) >= 2
    statuses = {item["data_status"] for item in data["items"]}
    assert statuses.issubset({status.value for status in FreshnessStatus})


def test_latest_tariffs_include_stale(client):
    response = client.get("/v1/tariffs", params={"include_stale": True})
    assert response.status_code == 200
    data = response.json()["items"]
    assert any(item["data_status"] == FreshnessStatus.STALE.value for item in data)


def test_tariff_history_filters(client):
    response = client.get(
        "/v1/tariffs/history",
        params={"supplier": "EDF", "option": "BASE", "puissance": 6},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filters"]["supplier"] == "EDF"
    assert all(entry["supplier"] == "EDF" for entry in body["items"])


def test_trve_diff_guard(client):
    response = client.get("/v1/guards/trve-diff")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert {item["status"] for item in payload["items"]}.issubset({"ok", "alert"})

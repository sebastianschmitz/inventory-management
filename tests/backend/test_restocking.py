"""
Tests for the restocking endpoints (POST/GET /api/restock-orders).
"""
from datetime import datetime

import pytest

from mock_data import restock_orders


@pytest.fixture(autouse=True)
def clean_restock_orders():
    """Restock orders live in a module-level list, so clear it around each test
    to keep tests independent."""
    restock_orders.clear()
    yield
    restock_orders.clear()


def _forecast(client, sku):
    return next(f for f in client.get("/api/demand").json() if f["item_sku"] == sku)


class TestDemandForecastCostFields:
    def test_forecasts_include_cost_supplier_lead_time(self, client):
        for f in client.get("/api/demand").json():
            assert f["unit_cost"] > 0
            assert f["supplier"]
            assert f["lead_time_days"] > 0


class TestRestockOrderEndpoints:
    def test_list_starts_empty(self, client):
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order_success(self, client):
        wdg = _forecast(client, "WDG-001")
        body = {"budget": 100000, "items": [{"sku": "WDG-001", "quantity": 10}]}
        response = client.post("/api/restock-orders", json=body)
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["budget"] == 100000
        assert abs(order["total_cost"] - 10 * wdg["unit_cost"]) < 0.01
        assert order["items"][0]["sku"] == "WDG-001"
        assert order["lead_time_days"] == wdg["lead_time_days"]

    def test_lead_time_is_max_across_items(self, client):
        a, b = _forecast(client, "FLT-405"), _forecast(client, "CTL-330")
        body = {"budget": 1000000, "items": [
            {"sku": "FLT-405", "quantity": 1},
            {"sku": "CTL-330", "quantity": 1},
        ]}
        order = client.post("/api/restock-orders", json=body).json()
        assert order["lead_time_days"] == max(a["lead_time_days"], b["lead_time_days"])

    def test_expected_delivery_matches_lead_time(self, client):
        body = {"budget": 100000, "items": [{"sku": "WDG-001", "quantity": 1}]}
        order = client.post("/api/restock-orders", json=body).json()
        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert "T" in order["submitted_date"]
        assert (expected - submitted).days == order["lead_time_days"]

    def test_created_order_appears_in_list_newest_first(self, client):
        for sku in ("WDG-001", "BRG-102"):
            client.post("/api/restock-orders",
                        json={"budget": 100000, "items": [{"sku": sku, "quantity": 1}]})
        orders = client.get("/api/restock-orders").json()
        assert len(orders) == 2
        assert orders[0]["items"][0]["sku"] == "BRG-102"

    def test_server_uses_its_own_prices(self, client):
        # Extra client-supplied price fields must be ignored.
        wdg = _forecast(client, "WDG-001")
        body = {"budget": 100000,
                "items": [{"sku": "WDG-001", "quantity": 2, "unit_cost": 0.01}]}
        order = client.post("/api/restock-orders", json=body).json()
        assert order["items"][0]["unit_cost"] == wdg["unit_cost"]

    def test_over_budget_rejected(self, client):
        body = {"budget": 1, "items": [{"sku": "WDG-001", "quantity": 10}]}
        response = client.post("/api/restock-orders", json=body)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restock-orders").json() == []

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restock-orders", json={"budget": 100, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        for qty in (0, -5):
            body = {"budget": 100000, "items": [{"sku": "WDG-001", "quantity": qty}]}
            assert client.post("/api/restock-orders", json=body).status_code == 400

    def test_unknown_sku_returns_404(self, client):
        body = {"budget": 100000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        response = client.post("/api/restock-orders", json=body)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_missing_fields_returns_422(self, client):
        assert client.post("/api/restock-orders", json={"items": []}).status_code == 422

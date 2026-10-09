import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_endpoint_success():
    payload = {
        "client_id": "C1001",
        "income": 180000,
        "monthly_expenses": 85000,
        "risk_profile": "moderate",
        "transactions": [
            {
                "id": "T001",
                "date": "2026-09-01",
                "amount": -1000,
                "category": "groceries",
                "description": "Supermarket"
            }
        ]
    }
    response = client.post("/advisor/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "C1001"
    assert "request_id" in data
    assert "analysis" in data
    assert "insights" in data


def test_analyze_endpoint_validation_error():
    payload = {
        "client_id": "C1001",
        "income": -50000, # Invalid negative income
        "monthly_expenses": 85000,
        "transactions": []
    }
    response = client.post("/advisor/analyze", json=payload)
    assert response.status_code == 422


def test_approve_reject_flow():
    # Analyze client with anomaly to trigger HITL review
    payload = {
        "client_id": "C1002",
        "income": 250000,
        "monthly_expenses": 120000,
        "risk_profile": "aggressive",
        "transactions": [
            {"id": "T101", "date": "2026-09-01", "amount": -1000, "category": "groceries"},
            {"id": "T105", "date": "2026-09-20", "amount": -45000, "category": "travel"}
        ]
    }
    analyze_resp = client.post("/advisor/analyze", json=payload)
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()
    req_id = data["request_id"]

    # Retrieve status by request_id
    get_resp = client.get(f"/advisor/{req_id}")
    assert get_resp.status_code == 200

    # Test HITL Approve
    approve_resp = client.post(f"/advisor/{req_id}/approve", json={"reviewer_comments": "Looks fine."})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["decision"] == "APPROVED"

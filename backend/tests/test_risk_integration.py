def test_risk_analyze_contract_schema(client):
    payload = {
        "sender_id": "alice@upi",
        "recipient_id": "legitimate_merchant@upi",
        "amount": 500.0,
        "timestamp": "2026-08-30T10:00:00Z",
        "context": {}
    }
    response = client.post("/api/v1/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # M5 Contract Schema Fields Check
    assert "personal_risk" in data
    assert "payee_risk" in data
    assert "overall_risk" in data
    assert "risk_level" in data
    assert "decision" in data
    assert "requires_confirmation" in data
    assert "requires_hold" in data
    assert "reasons" in data
    assert isinstance(data["reasons"], list)

    assert data["decision"] == "ALLOW"
    assert data["requires_confirmation"] is False
    assert data["requires_hold"] is False


def test_high_amount_personal_risk_evaluation(client):
    payload = {
        "sender_id": "alice@upi",
        "recipient_id": "legitimate_merchant@upi",
        "amount": 9000.0,
        "context": {}
    }
    response = client.post("/api/v1/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["personal_risk"] >= 70.0
    assert data["requires_confirmation"] is True


def test_suspicious_payee_risk_evaluation(client):
    payload = {
        "sender_id": "alice@upi",
        "recipient_id": "suspicious_phishing@upi",
        "amount": 1000.0,
        "context": {}
    }
    response = client.post("/api/v1/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["payee_risk"] >= 65.0
    assert data["decision"] in ["WARN", "HOLD"]


def test_dual_high_risk_transaction(client):
    payload = {
        "sender_id": "alice@upi",
        "recipient_id": "suspicious_phishing@upi",
        "amount": 8000.0,
        "context": {}
    }
    response = client.post("/api/v1/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk"] >= 70.0
    assert data["decision"] == "HOLD"
    assert data["requires_hold"] is True

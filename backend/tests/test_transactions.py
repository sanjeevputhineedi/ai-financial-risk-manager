import uuid

def test_instant_payment_low_risk(client, alice_auth_headers):
    # ₹500 to legitimate merchant -> Low risk -> instant completion
    payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "recipient_name": "SuperMart Grocery",
        "amount": 500.0,
        "notes": "Weekly groceries",
        "idempotency_key": str(uuid.uuid4())
    }
    response = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["amount"] == 500.0
    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"

    # Check Alice account debited
    acc_res = client.get("/api/v1/accounts/me", headers=alice_auth_headers)
    assert acc_res.status_code == 200
    assert acc_res.json()["balance"] == 24500.0


def test_insufficient_balance_error(client, alice_auth_headers):
    payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "amount": 999999.0,
        "notes": "Cannot afford"
    }
    response = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_BALANCE"


def test_idempotency_duplicate_returns_same_transaction(client, alice_auth_headers):
    key = str(uuid.uuid4())
    payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "amount": 250.0,
        "idempotency_key": key
    }
    res1 = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    res2 = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    
    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["id"] == res2.json()["id"]


def test_high_personal_risk_requires_confirmation(client, alice_auth_headers):
    # ₹9000 -> High personal risk -> CONFIRMATION_REQUIRED
    payload = {
        "recipient_vpa": "legitimate_merchant@upi",
        "amount": 9000.0,
        "notes": "Large unusual purchase"
    }
    response = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "CONFIRMATION_REQUIRED"
    assert data["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]

    tx_id = data["id"]

    # User confirms transaction
    confirm_res = client.post(
        f"/api/v1/transactions/{tx_id}/confirm",
        json={"confirmed": True, "user_notes": "Confirmed by user"},
        headers=alice_auth_headers
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] in ["COMPLETED", "HELD"]


def test_cancel_transaction(client, alice_auth_headers):
    payload = {
        "recipient_vpa": "suspicious_phishing@upi",
        "amount": 8000.0,
        "notes": "Potential scam"
    }
    res = client.post("/api/v1/transactions", json=payload, headers=alice_auth_headers)
    tx_id = res.json()["id"]
    assert res.json()["status"] == "CONFIRMATION_REQUIRED"

    # Cancel
    cancel_res = client.post(
        f"/api/v1/transactions/{tx_id}/cancel",
        json={"reason": "User smelled a scam"},
        headers=alice_auth_headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

def test_fund_manager_hold_and_release(client, alice_auth_headers, admin_auth_headers):
    # Create transaction to suspicious recipient with high amount and bypass to immediately hold
    tx_payload = {
        "recipient_vpa": "suspicious_phishing@upi",
        "amount": 5000.0,
        "bypass_risk_warning": True,
        "notes": "Escrow release test"
    }
    tx_res = client.post("/api/v1/transactions", json=tx_payload, headers=alice_auth_headers)
    assert tx_res.status_code == 201
    assert tx_res.json()["status"] == "HELD"

    # Verify held payments list
    held_list_res = client.get("/api/v1/held-payments")
    assert held_list_res.status_code == 200
    held_records = held_list_res.json()
    assert len(held_records) > 0
    target_held = [h for h in held_records if h["transaction_id"] == tx_res.json()["id"]][0]

    # Admin releases funds
    release_res = client.post(
        f"/api/v1/held-payments/{target_held['id']}/release",
        json={"reason": "Investigated and verified safe by admin"},
        headers=admin_auth_headers
    )
    assert release_res.status_code == 200
    assert release_res.json()["status"] == "RELEASED"

    # Duplicate release should fail
    dup_res = client.post(
        f"/api/v1/held-payments/{target_held['id']}/release",
        json={"reason": "Duplicate release attempt"},
        headers=admin_auth_headers
    )
    assert dup_res.status_code == 400


def test_fund_manager_hold_and_refund(client, alice_auth_headers, admin_auth_headers):
    # Initial balance check
    acc_before = client.get("/api/v1/accounts/me", headers=alice_auth_headers).json()["balance"]

    tx_payload = {
        "recipient_vpa": "suspicious_phishing@upi",
        "amount": 6000.0,
        "bypass_risk_warning": True,
        "notes": "Refund escrow test"
    }
    tx_res = client.post("/api/v1/transactions", json=tx_payload, headers=alice_auth_headers)
    assert tx_res.status_code == 201
    assert tx_res.json()["status"] == "HELD"

    held_records = client.get("/api/v1/held-payments").json()
    target_held = [h for h in held_records if h["transaction_id"] == tx_res.json()["id"]][0]

    # Admin refunds funds
    refund_res = client.post(
        f"/api/v1/held-payments/{target_held['id']}/refund",
        json={"reason": "Fraud confirmed, returning funds to sender"},
        headers=admin_auth_headers
    )
    assert refund_res.status_code == 200
    assert refund_res.json()["status"] == "REFUNDED"

    # Check sender balance restored
    acc_after = client.get("/api/v1/accounts/me", headers=alice_auth_headers).json()["balance"]
    assert acc_after == acc_before

    # Duplicate refund should fail
    dup_res = client.post(
        f"/api/v1/held-payments/{target_held['id']}/refund",
        json={"reason": "Duplicate refund attempt"},
        headers=admin_auth_headers
    )
    assert dup_res.status_code == 400


def test_dynamic_cooling_reevaluation(client, alice_auth_headers):
    reeval_res = client.post("/api/v1/held-payments/reevaluate")
    assert reeval_res.status_code == 200
    assert isinstance(reeval_res.json(), list)

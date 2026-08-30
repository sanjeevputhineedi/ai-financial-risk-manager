def test_submit_fraud_report_updates_reputation(client, alice_auth_headers):
    # Initial payee risk
    init_res = client.get("/api/v1/payees/new_vendor_01@upi/risk")
    assert init_res.status_code == 200

    report_payload = {
        "payee_vpa": "new_vendor_01@upi",
        "category": "SUSPECTED_FRAUD",
        "description": "User never received items after transferring money."
    }
    rep_res = client.post("/api/v1/reports", json=report_payload, headers=alice_auth_headers)
    assert rep_res.status_code == 201
    report_data = rep_res.json()
    assert report_data["category"] == "SUSPECTED_FRAUD"

    # Verify payee reputation elevated
    updated_res = client.get("/api/v1/payees/new_vendor_01@upi/reputation")
    assert updated_res.status_code == 200
    assert updated_res.json()["reported_count"] >= 1
    assert updated_res.json()["risk_score"] > 25.0


def test_invalid_report_category_fails(client, alice_auth_headers):
    report_payload = {
        "payee_vpa": "new_vendor_01@upi",
        "category": "INVALID_CATEGORY_NAME",
        "description": "Some issue"
    }
    rep_res = client.post("/api/v1/reports", json=report_payload, headers=alice_auth_headers)
    assert rep_res.status_code == 400


def test_list_fraud_reports(client):
    res = client.get("/api/v1/reports")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

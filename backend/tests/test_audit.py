def test_audit_logs_retrieval(client, alice_auth_headers, admin_auth_headers):
    # Perform an action that logs an audit entry (e.g. view recipients or initiate transaction)
    client.get("/api/v1/recipients", headers=alice_auth_headers)
    
    # Also log in again to generate LOGIN audit log
    client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"})

    response = client.get("/api/v1/audit", headers=admin_auth_headers)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # Check that secrets are redacted
    for log in logs:
        details_str = str(log["details"])
        assert "password" not in details_str.lower() or "[REDACTED]" in details_str


def test_audit_access_denied_for_regular_user(client, alice_auth_headers):
    response = client.get("/api/v1/audit", headers=alice_auth_headers)
    assert response.status_code == 403

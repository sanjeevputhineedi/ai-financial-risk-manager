def test_dashboard_metrics(client):
    response = client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "risk_distribution" in data
    assert "held_summary" in data
    assert "fraud_reports_count" in data
    assert "average_personal_risk" in data
    assert "average_payee_risk" in data
    assert "escrow_pool_balance" in data

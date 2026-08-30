def test_get_my_account(client, alice_auth_headers):
    response = client.get("/api/v1/accounts/me", headers=alice_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["upi_id"] == "alice@upi"
    assert data["balance"] == 25000.0
    assert data["currency"] == "INR"


def test_add_and_list_recipients(client, alice_auth_headers):
    # Add recipient
    payload = {
        "payee_vpa": "grocery_vendor@upi",
        "payee_name": "Corner Grocery Store",
        "account_number": "ACC_GROCERY_99"
    }
    post_res = client.post("/api/v1/recipients", json=payload, headers=alice_auth_headers)
    assert post_res.status_code == 201
    recipient_data = post_res.json()
    assert recipient_data["payee_vpa"] == "grocery_vendor@upi"

    # List recipients
    list_res = client.get("/api/v1/recipients", headers=alice_auth_headers)
    assert list_res.status_code == 200
    recipients = list_res.json()
    assert any(r["payee_vpa"] == "grocery_vendor@upi" for r in recipients)

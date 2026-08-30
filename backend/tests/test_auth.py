def test_register_new_user(client):
    payload = {
        "email": "david@example.com",
        "username": "david",
        "full_name": "David Miller",
        "password": "securepassword123",
        "initial_balance": 30000.0,
        "upi_id": "david@upi"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "david"
    assert data["email"] == "david@example.com"


def test_register_duplicate_email_fails(client):
    payload = {
        "email": "alice@example.com",
        "username": "alice_duplicate",
        "full_name": "Alice Duplicate",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "EMAIL_EXISTS"


def test_login_success(client):
    payload = {
        "email": "alice@example.com",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "alice@example.com"


def test_login_invalid_password_fails(client):
    payload = {
        "email": "alice@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


def test_get_current_user_profile(client, alice_auth_headers):
    response = client.get("/api/v1/users/me", headers=alice_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "hashed_password" not in data


def test_unauthenticated_request_fails(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

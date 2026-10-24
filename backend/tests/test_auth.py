from datetime import timedelta
from app.core.security import create_access_token

def test_login_valid_credentials(client, test_admin):
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert "access_token" in response.cookies

def test_login_invalid_credentials(client, test_admin):
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "access_token" not in response.cookies

def test_login_nonexistent_user(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123"
    })
    assert response.status_code == 401

def test_get_current_user_valid_token(client, test_admin):
    token = create_access_token(data={"sub": test_admin.email})
    client.cookies.set("access_token", f"Bearer {token}")
    
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == test_admin.email

def test_get_current_user_no_token(client, test_admin):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token(client, test_admin):
    client.cookies.set("access_token", "Bearer invalidtoken")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_sliding_renewal_token_fresh(client, test_admin):
    # Token expires in 30 minutes (> 15)
    token = create_access_token(data={"sub": test_admin.email}, expires_delta=timedelta(minutes=30))
    client.cookies.set("access_token", f"Bearer {token}")
    
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    # The Set-Cookie header should not be present because renewal wasn't needed
    assert "set-cookie" not in response.headers

def test_sliding_renewal_token_expiring(client, test_admin):
    # Token expires in 10 minutes (<= 15)
    token = create_access_token(data={"sub": test_admin.email}, expires_delta=timedelta(minutes=10))
    client.cookies.set("access_token", f"Bearer {token}")
    
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    # New token should be issued
    assert "set-cookie" in response.headers
    assert "access_token" in response.headers["set-cookie"]

def test_logout(client, test_admin):
    token = create_access_token(data={"sub": test_admin.email})
    client.cookies.set("access_token", f"Bearer {token}")
    
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "set-cookie" in response.headers
    assert "Max-Age=0" in response.headers["set-cookie"] or "expires=" in response.headers["set-cookie"].lower()

from app.core.security import verify_password

from app.models.user import User
from app.core.security import create_access_token

def _auth_client(client, user):
    token = create_access_token(data={"sub": user.email})
    client.cookies.set("access_token", f"Bearer {token}")
    return client

def test_get_users_as_admin(client, test_admin, test_recruiter):
    _auth_client(client, test_admin)
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_get_users_as_recruiter(client, test_recruiter):
    _auth_client(client, test_recruiter)
    response = client.get("/api/v1/users/")
    assert response.status_code == 403

def test_get_users_unauthenticated(client):
    response = client.get("/api/v1/users/")
    assert response.status_code == 401

def test_create_user_as_admin(client, test_admin):
    _auth_client(client, test_admin)
    response = client.post("/api/v1/users/", json={
        "email": "newuser@example.com",
        "password": "securepassword",
        "role": "recruiter"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "recruiter"
    assert "password" not in data
    assert "hashed_password" not in data

def test_create_user_as_recruiter(client, test_recruiter):
    _auth_client(client, test_recruiter)
    response = client.post("/api/v1/users/", json={
        "email": "newuser2@example.com",
        "password": "securepassword",
        "role": "recruiter"
    })
    assert response.status_code == 403

def test_create_user_duplicate_email(client, test_admin):
    _auth_client(client, test_admin)
    response = client.post("/api/v1/users/", json={
        "email": test_admin.email,
        "password": "securepassword",
        "role": "recruiter"
    })
    assert response.status_code == 422

def test_update_user_as_admin(client, test_admin, test_recruiter):
    _auth_client(client, test_admin)
    response = client.patch(f"/api/v1/users/{test_recruiter.id}", json={
        "role": "admin"
    })
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

def test_disable_user(client, test_admin, test_recruiter):
    _auth_client(client, test_admin)
    assert test_recruiter.is_active is True
    
    response = client.patch(f"/api/v1/users/{test_recruiter.id}/disable")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

def test_password_hashed_on_creation(client, test_admin, db_session):
    _auth_client(client, test_admin)
    client.post("/api/v1/users/", json={
        "email": "hashed@example.com",
        "password": "plaintextpassword",
        "role": "recruiter"
    })
    
    # Check DB directly
    new_user = db_session.query(User).filter(User.email == "hashed@example.com").first()
    assert new_user is not None
    assert new_user.hashed_password != "plaintextpassword"
    assert verify_password("plaintextpassword", new_user.hashed_password)

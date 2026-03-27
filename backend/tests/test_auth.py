import jwt as pyjwt
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.auth import get_current_user, AuthUser


# Minimal app for testing the auth dependency in isolation
_test_app = FastAPI()


@_test_app.get("/test-auth")
async def test_endpoint(user: AuthUser = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name}


def test_valid_token_returns_user(auth_token):
    client = TestClient(_test_app)
    response = client.get("/test-auth", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "user-id-123"
    assert data["email"] == "jane@acme.com"
    assert data["full_name"] == "Jane Doe"


def test_missing_token_returns_403():
    client = TestClient(_test_app)
    response = client.get("/test-auth")
    assert response.status_code == 403


def test_invalid_token_returns_401():
    client = TestClient(_test_app)
    response = client.get("/test-auth", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


def test_expired_token_returns_401(settings):
    import time

    token = pyjwt.encode(
        {
            "sub": "user-id-123",
            "email": "jane@acme.com",
            "aud": "authenticated",
            "role": "authenticated",
            "exp": int(time.time()) - 3600,
            "user_metadata": {},
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    client = TestClient(_test_app)
    response = client.get("/test-auth", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

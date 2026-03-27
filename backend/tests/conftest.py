import os

# Set test env vars before any app imports
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-must-be-at-least-32-characters-long")

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_supabase
from app.main import app

TEST_USER_ID = str(uuid4())
TEST_USER_EMAIL = "alice@example.com"
TEST_ADMIN_ID = str(uuid4())
TEST_ADMIN_EMAIL = "admin@example.com"

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]


def make_token(user_id: str, email: str) -> str:
    """Create a valid Supabase-style JWT for testing."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "user_metadata": {
            "full_name": email.split("@")[0].title(),
            "avatar_url": None,
        },
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def make_mock_chain(data=None, count=None):
    """Create a chainable mock for Supabase table queries."""
    chain = MagicMock()
    for method in [
        "select", "insert", "update", "delete",
        "eq", "neq", "range", "in_", "order",
    ]:
        getattr(chain, method).return_value = chain
    response = MagicMock()
    response.data = data if data is not None else []
    response.count = count if count is not None else len(response.data)
    chain.execute.return_value = response
    return chain


ACTIVE_PROFILE = {
    "id": TEST_USER_ID,
    "email": TEST_USER_EMAIL,
    "full_name": "Alice",
    "avatar_url": None,
    "role": "employee",
    "status": "active",
    "domain": "example.com",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}

PENDING_PROFILE = {**ACTIVE_PROFILE, "status": "pending"}

ADMIN_PROFILE = {
    "id": TEST_ADMIN_ID,
    "email": TEST_ADMIN_EMAIL,
    "full_name": "Admin",
    "avatar_url": None,
    "role": "admin",
    "status": "active",
    "domain": "example.com",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def client(mock_supabase):
    app.dependency_overrides[get_supabase] = lambda: mock_supabase
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user_token():
    return make_token(TEST_USER_ID, TEST_USER_EMAIL)


@pytest.fixture
def admin_token():
    return make_token(TEST_ADMIN_ID, TEST_ADMIN_EMAIL)

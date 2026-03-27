import os

os.environ.update(
    {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
        "SUPABASE_JWT_SECRET": "test-jwt-secret-minimum-32-characters-long!!",
        "APP_NAME": "Test App",
        "ALLOWED_ORIGINS": "http://localhost:3000",
    }
)

import pytest
from unittest.mock import MagicMock

import jwt as pyjwt

from app.config import get_settings
from app.database import reset_client
import app.database as database


@pytest.fixture(autouse=True)
def mock_supabase():
    """Replace the Supabase client with a mock for all tests."""
    mock_client = MagicMock()
    reset_client()
    database._client = mock_client
    yield mock_client
    reset_client()


@pytest.fixture
def settings():
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def auth_token(settings):
    """A valid JWT for a test user."""
    return pyjwt.encode(
        {
            "sub": "user-id-123",
            "email": "jane@acme.com",
            "aud": "authenticated",
            "role": "authenticated",
            "user_metadata": {
                "full_name": "Jane Doe",
                "avatar_url": "https://example.com/jane.jpg",
            },
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

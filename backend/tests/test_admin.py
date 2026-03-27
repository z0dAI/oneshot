import jwt as pyjwt
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.config import get_settings


def _mock_profile(overrides=None):
    profile = {
        "id": "admin-id-123",
        "email": "admin@acme.com",
        "full_name": "Admin User",
        "avatar_url": None,
        "role": "admin",
        "status": "active",
        "domain": "acme.com",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    if overrides:
        profile.update(overrides)
    return profile


@pytest.fixture
def admin_token():
    settings = get_settings()
    return pyjwt.encode(
        {
            "sub": "admin-id-123",
            "email": "admin@acme.com",
            "aud": "authenticated",
            "role": "authenticated",
            "user_metadata": {"full_name": "Admin User"},
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def employee_token():
    settings = get_settings()
    return pyjwt.encode(
        {
            "sub": "emp-id-456",
            "email": "employee@acme.com",
            "aud": "authenticated",
            "role": "authenticated",
            "user_metadata": {"full_name": "Employee User"},
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def employee_headers(employee_token):
    return {"Authorization": f"Bearer {employee_token}"}


def _setup_admin_profile(mock_supabase):
    profile = _mock_profile()
    mock_response = MagicMock()
    mock_response.data = [profile]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )
    return profile


def _setup_employee_profile(mock_supabase):
    profile = _mock_profile({"id": "emp-id-456", "email": "employee@acme.com", "role": "employee"})
    mock_response = MagicMock()
    mock_response.data = [profile]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )
    return profile


def test_list_domains_as_admin(mock_supabase, admin_headers):
    from app.main import app

    _setup_admin_profile(mock_supabase)

    domains = [{"id": "d1", "domain": "acme.com", "added_by": "admin-id-123", "is_active": True, "created_at": "2026-01-01T00:00:00+00:00"}]
    domain_response = MagicMock()
    domain_response.data = domains
    mock_supabase.table.return_value.select.return_value.execute.return_value = domain_response

    client = TestClient(app)
    response = client.get("/api/admin/domains", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_domains_rejected_for_employee(mock_supabase, employee_headers):
    from app.main import app

    _setup_employee_profile(mock_supabase)
    client = TestClient(app)
    response = client.get("/api/admin/domains", headers=employee_headers)
    assert response.status_code == 403


def test_create_domain(mock_supabase, admin_headers):
    from app.main import app

    _setup_admin_profile(mock_supabase)

    created = {"id": "d2", "domain": "partner.org", "added_by": "admin-id-123", "is_active": True, "created_at": "2026-01-01T00:00:00+00:00"}
    insert_response = MagicMock()
    insert_response.data = [created]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = insert_response

    client = TestClient(app)
    response = client.post(
        "/api/admin/domains",
        headers=admin_headers,
        json={"domain": "partner.org", "activate_existing": False},
    )
    assert response.status_code == 201
    assert response.json()["domain"] == "partner.org"


def test_delete_domain(mock_supabase, admin_headers):
    from app.main import app

    _setup_admin_profile(mock_supabase)

    delete_response = MagicMock()
    delete_response.data = [{"id": "d1"}]
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
        delete_response
    )

    client = TestClient(app)
    response = client.delete("/api/admin/domains/d1", headers=admin_headers)
    assert response.status_code == 204

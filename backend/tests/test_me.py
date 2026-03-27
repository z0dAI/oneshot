from unittest.mock import MagicMock


def _mock_profile(overrides=None):
    """Returns a dict matching a profiles table row."""
    profile = {
        "id": "user-id-123",
        "email": "jane@acme.com",
        "full_name": "Jane Doe",
        "avatar_url": "https://example.com/jane.jpg",
        "role": "employee",
        "status": "active",
        "domain": "acme.com",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    if overrides:
        profile.update(overrides)
    return profile


def _setup_profile_exists(mock_supabase, profile=None):
    """Configure mock so profile lookup returns an existing profile."""
    p = profile or _mock_profile()
    mock_response = MagicMock()
    mock_response.data = [p]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )
    return p


def _setup_profile_not_exists_then_create(mock_supabase, domain_allowed=True):
    """Configure mock for first-login flow: no profile, then create."""
    select_response = MagicMock()
    select_response.data = []

    domain_response = MagicMock()
    domain_response.data = [{"domain": "acme.com"}] if domain_allowed else []

    created_profile = _mock_profile(
        {"status": "active" if domain_allowed else "pending"}
    )
    insert_response = MagicMock()
    insert_response.data = [created_profile]

    call_count = {"n": 0}

    def table_side_effect(name):
        call_count["n"] += 1
        mock_table = MagicMock()
        if name == "profiles" and call_count["n"] == 1:
            mock_table.select.return_value.eq.return_value.execute.return_value = (
                select_response
            )
        elif name == "allowed_domains":
            mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = domain_response
        elif name == "profiles":
            mock_table.insert.return_value.execute.return_value = insert_response
        return mock_table

    mock_supabase.table.side_effect = table_side_effect
    return created_profile


def test_get_me_existing_profile(mock_supabase, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app

    profile = _setup_profile_exists(mock_supabase)
    client = TestClient(app)
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jane@acme.com"
    assert data["role"] == "employee"


def test_get_me_creates_profile_on_first_login(mock_supabase, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app

    _setup_profile_not_exists_then_create(mock_supabase, domain_allowed=True)
    client = TestClient(app)
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_get_me_pending_when_domain_not_allowed(mock_supabase, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app

    _setup_profile_not_exists_then_create(mock_supabase, domain_allowed=False)
    client = TestClient(app)
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"


def test_get_me_no_token():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/me")
    assert response.status_code == 403


def test_update_me(mock_supabase, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app

    _setup_profile_exists(mock_supabase)

    updated = _mock_profile({"full_name": "Jane Smith"})
    update_response = MagicMock()
    update_response.data = [updated]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = update_response

    client = TestClient(app)
    response = client.put("/api/me", headers=auth_headers, json={"full_name": "Jane Smith"})
    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Smith"


def test_update_me_rejected_when_pending(mock_supabase, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app

    _setup_profile_exists(mock_supabase, _mock_profile({"status": "pending"}))
    client = TestClient(app)
    response = client.put("/api/me", headers=auth_headers, json={"full_name": "Jane Smith"})
    assert response.status_code == 403

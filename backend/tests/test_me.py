from tests.conftest import (
    ACTIVE_PROFILE,
    ADMIN_PROFILE,
    PENDING_PROFILE,
    TEST_USER_EMAIL,
    TEST_USER_ID,
    make_mock_chain,
)


def test_get_me_existing_active_user(client, mock_supabase, user_token):
    """Active user fetches their profile successfully."""
    mock_supabase.table.return_value = make_mock_chain(data=[ACTIVE_PROFILE])

    resp = client.get("/api/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == TEST_USER_EMAIL
    assert body["role"] == "employee"
    assert body["status"] == "active"


def test_get_me_pending_user_can_see_status(client, mock_supabase, user_token):
    """Pending users can still call GET /api/me to see their status."""
    mock_supabase.table.return_value = make_mock_chain(data=[PENDING_PROFILE])

    resp = client.get("/api/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_get_me_new_user_allowed_domain(client, mock_supabase, user_token):
    """First login with an allowed domain creates profile with status=active."""
    calls = [
        make_mock_chain(data=[]),  # profiles select: not found
        make_mock_chain(data=[{"id": "d1", "domain": "example.com", "is_active": True}]),  # domain check: found
        make_mock_chain(data=[{**ACTIVE_PROFILE, "status": "active"}]),  # profiles insert
    ]
    mock_supabase.table.side_effect = lambda name: calls.pop(0)

    resp = client.get("/api/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_get_me_new_user_unknown_domain(client, mock_supabase, user_token):
    """First login with an unknown domain creates profile with status=pending."""
    calls = [
        make_mock_chain(data=[]),  # profiles select: not found
        make_mock_chain(data=[]),  # domain check: not found
        make_mock_chain(data=[PENDING_PROFILE]),  # profiles insert
    ]
    mock_supabase.table.side_effect = lambda name: calls.pop(0)

    resp = client.get("/api/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_get_me_no_auth_header(client):
    """Missing auth header returns 401."""
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_put_me_updates_name(client, mock_supabase, user_token):
    """Active user can update their own name."""
    updated = {**ACTIVE_PROFILE, "full_name": "Alice Smith"}
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ACTIVE_PROFILE]),  # get_or_create_profile lookup
        make_mock_chain(data=[updated]),  # update call
    ]

    resp = client.put(
        "/api/me",
        json={"full_name": "Alice Smith"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Alice Smith"


def test_put_me_pending_user_rejected(client, mock_supabase, user_token):
    """Pending users cannot update their profile (403)."""
    mock_supabase.table.return_value = make_mock_chain(data=[PENDING_PROFILE])

    resp = client.put(
        "/api/me",
        json={"full_name": "Nope"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403

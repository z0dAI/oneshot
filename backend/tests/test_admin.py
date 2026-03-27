from tests.conftest import (
    ACTIVE_PROFILE,
    ADMIN_PROFILE,
    TEST_ADMIN_ID,
    TEST_USER_ID,
    make_mock_chain,
)


# --- User Management ---

def test_list_users_as_admin(client, mock_supabase, admin_token):
    """Admin can list all users."""
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin: profile lookup
        make_mock_chain(data=[ACTIVE_PROFILE, ADMIN_PROFILE], count=2),  # list query
    ]

    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["users"]) == 2


def test_list_users_as_non_admin(client, mock_supabase, user_token):
    """Non-admin users get 403."""
    mock_supabase.table.return_value = make_mock_chain(data=[ACTIVE_PROFILE])

    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_list_users_with_role_filter(client, mock_supabase, admin_token):
    """Admin can filter users by role."""
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[ADMIN_PROFILE], count=1),  # filtered query
    ]

    resp = client.get(
        "/api/admin/users?role=admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_update_user_role(client, mock_supabase, admin_token):
    """Admin can change a user's role."""
    updated_user = {**ACTIVE_PROFILE, "role": "recruiter"}
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[updated_user]),  # update
    ]

    resp = client.patch(
        f"/api/admin/users/{TEST_USER_ID}",
        json={"role": "recruiter"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "recruiter"


def test_update_user_status(client, mock_supabase, admin_token):
    """Admin can change a user's status."""
    updated_user = {**ACTIVE_PROFILE, "status": "archived"}
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[updated_user]),  # update
    ]

    resp = client.patch(
        f"/api/admin/users/{TEST_USER_ID}",
        json={"status": "archived"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "archived"


# --- Domain Management ---

def test_list_domains(client, mock_supabase, admin_token):
    """Admin can list all allowed domains."""
    domain = {
        "id": "d1",
        "domain": "acme.com",
        "added_by": TEST_ADMIN_ID,
        "is_active": True,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[domain]),  # list domains
    ]

    resp = client.get("/api/admin/domains", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["domain"] == "acme.com"


def test_add_domain(client, mock_supabase, admin_token):
    """Admin can add an allowed domain."""
    new_domain = {
        "id": "d2",
        "domain": "newco.com",
        "added_by": TEST_ADMIN_ID,
        "is_active": True,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[new_domain]),  # insert domain
    ]

    resp = client.post(
        "/api/admin/domains",
        json={"domain": "newco.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["domain"] == "newco.com"


def test_add_domain_with_bulk_activate(client, mock_supabase, admin_token):
    """Adding a domain with activate_existing bulk-activates pending users."""
    new_domain = {
        "id": "d3",
        "domain": "bulk.com",
        "added_by": TEST_ADMIN_ID,
        "is_active": True,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[new_domain]),  # insert domain
        make_mock_chain(data=[]),  # bulk activate update
    ]

    resp = client.post(
        "/api/admin/domains",
        json={"domain": "bulk.com", "activate_existing": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201


def test_toggle_domain(client, mock_supabase, admin_token):
    """Admin can disable a domain."""
    updated = {
        "id": "d1",
        "domain": "acme.com",
        "added_by": TEST_ADMIN_ID,
        "is_active": False,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[updated]),  # update
    ]

    resp = client.patch(
        "/api/admin/domains/d1",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_delete_domain(client, mock_supabase, admin_token):
    """Admin can delete a domain."""
    mock_supabase.table.side_effect = [
        make_mock_chain(data=[ADMIN_PROFILE]),  # require_admin
        make_mock_chain(data=[]),  # delete
    ]

    resp = client.delete(
        "/api/admin/domains/d1",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204

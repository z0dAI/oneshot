# Clay Talent Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a foundation web app with Supabase Google One Tap auth, role-based user management, and domain allowlisting.

**Architecture:** Next.js frontend handles Google One Tap auth via Supabase JS SDK. All data requests go through a FastAPI backend that validates Supabase JWTs and owns all business logic. Supabase provides auth and Postgres database.

**Tech Stack:** Next.js 15 (App Router, Tailwind CSS), FastAPI, Supabase (JS SDK + Python client), PyJWT, deployed on Render.

**Spec:** `docs/superpowers/specs/2026-03-26-clay-talent-portal-design.md`

## Prerequisites (manual steps)

Before starting implementation, the developer must:

1. **Create a Supabase project** at supabase.com — note the Project URL, anon key, service role key, and JWT secret (Settings > API).
2. **Create Google OAuth credentials** at console.cloud.google.com — create an OAuth 2.0 Client ID (Web application). Add `http://localhost:3000` to authorized JavaScript origins. Note the Client ID.
3. **Enable Google provider in Supabase** — Authentication > Providers > Google. Enter the Google Client ID and Client Secret. Check "Skip nonce checks" if using One Tap without nonce (we use nonces, so leave unchecked).
4. **Create a Render account** at render.com (for deployment).

---

## File Structure

### Backend (`backend/`)

| File | Responsibility |
|------|---------------|
| `app/__init__.py` | Package marker |
| `app/main.py` | FastAPI app, CORS, lifespan, router registration |
| `app/config.py` | Pydantic Settings (env vars) |
| `app/database.py` | Supabase client singleton |
| `app/auth.py` | JWT validation + profile lookup dependencies |
| `app/models.py` | Pydantic request/response schemas |
| `app/routes/__init__.py` | Package marker |
| `app/routes/me.py` | GET/PUT /api/me |
| `app/routes/admin.py` | All /api/admin/* endpoints |
| `app/services/__init__.py` | Package marker |
| `app/services/profiles.py` | Profile CRUD via Supabase |
| `app/services/domains.py` | Domain CRUD via Supabase |
| `requirements.txt` | Python dependencies |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Shared test fixtures |
| `tests/test_auth.py` | Auth dependency tests |
| `tests/test_me.py` | /api/me endpoint tests |
| `tests/test_admin.py` | Admin endpoint tests |

### Frontend (`frontend/`)

| File | Responsibility |
|------|---------------|
| `src/lib/config.ts` | APP_NAME and constants |
| `src/lib/supabase/client.ts` | Browser Supabase client |
| `src/lib/supabase/server.ts` | Server Supabase client |
| `src/lib/api.ts` | FastAPI client wrapper |
| `src/types/google.d.ts` | Google Identity Services type declarations |
| `src/app/layout.tsx` | Root layout |
| `src/app/page.tsx` | Login page + Google One Tap |
| `src/app/dashboard/page.tsx` | Dashboard |
| `src/app/admin/page.tsx` | Admin panel |
| `src/components/Nav.tsx` | Navigation bar |
| `src/middleware.ts` | Route protection |
| `.env.local.example` | Environment variable template |

### Root

| File | Responsibility |
|------|---------------|
| `supabase/migrations/001_schema.sql` | Database migration |
| `render.yaml` | Render Blueprint |
| `.gitignore` | Git ignore rules |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `.gitignore`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/
dist/

# Node
node_modules/
.next/

# Environment
.env
.env.local
!.env.example
!.env.local.example

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Superpowers
.superpowers/
```

- [ ] **Step 2: Create backend/requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
supabase==2.10.0
pydantic-settings==2.5.2
pyjwt==2.9.0
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 3: Create backend/.env.example**

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
APP_NAME=Clay Talent Portal
ALLOWED_ORIGINS=http://localhost:3000
SEED_ADMIN_EMAIL=
```

- [ ] **Step 4: Create empty __init__.py files**

Create empty files at:
- `backend/app/__init__.py`
- `backend/app/routes/__init__.py`
- `backend/app/services/__init__.py`
- `backend/tests/__init__.py`

- [ ] **Step 5: Initialize backend virtual environment**

Run:
```bash
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add .gitignore backend/
git commit -m "feat: scaffold backend project structure"
```

---

### Task 2: Supabase Migration

**Files:**
- Create: `supabase/migrations/001_schema.sql`

- [ ] **Step 1: Write migration SQL**

```sql
-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'recruiter', 'employee');
CREATE TYPE user_status AS ENUM ('active', 'pending', 'archived');

-- Profiles table (1:1 with auth.users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    avatar_url TEXT,
    role user_role NOT NULL DEFAULT 'employee',
    status user_status NOT NULL DEFAULT 'pending',
    domain TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_domain ON public.profiles(domain);
CREATE INDEX idx_profiles_status ON public.profiles(status);
CREATE INDEX idx_profiles_role ON public.profiles(role);

-- Allowed domains table
CREATE TABLE public.allowed_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT UNIQUE NOT NULL,
    added_by UUID REFERENCES public.profiles(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_allowed_domains_domain ON public.allowed_domains(domain);

-- Auto-update updated_at on profiles
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

- [ ] **Step 2: Apply migration**

Run this SQL in the Supabase dashboard (SQL Editor) or via the Supabase CLI:
```bash
supabase db push
```

- [ ] **Step 3: Commit**

```bash
git add supabase/
git commit -m "feat: add database schema for profiles and allowed_domains"
```

---

### Task 3: Backend Config, Database Client, and Models

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`

- [ ] **Step 1: Create config.py**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    app_name: str = "Clay Talent Portal"
    allowed_origins: str = "http://localhost:3000"
    seed_admin_email: str = ""

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Create database.py**

```python
from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        from app.config import get_settings

        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


def reset_client() -> None:
    """Reset the client. Used in tests."""
    global _client
    _client = None
```

- [ ] **Step 3: Create models.py**

```python
from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    admin = "admin"
    recruiter = "recruiter"
    employee = "employee"


class Status(str, Enum):
    active = "active"
    pending = "pending"
    archived = "archived"


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: str | None
    role: Role
    status: Status
    domain: str
    created_at: str
    updated_at: str


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserUpdate(BaseModel):
    role: Role | None = None
    status: Status | None = None


class DomainCreate(BaseModel):
    domain: str
    activate_existing: bool = False


class DomainUpdate(BaseModel):
    is_active: bool


class DomainResponse(BaseModel):
    id: str
    domain: str
    added_by: str | None
    is_active: bool
    created_at: str


class PaginatedUsers(BaseModel):
    users: list[ProfileResponse]
    total: int
    page: int
    per_page: int
```

- [ ] **Step 4: Commit**

```bash
cd backend && git add app/config.py app/database.py app/models.py
git commit -m "feat: add backend config, database client, and pydantic models"
```

---

### Task 4: Backend Auth Dependency (TDD)

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`
- Create: `backend/app/auth.py`

- [ ] **Step 1: Create test fixtures in conftest.py**

```python
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
```

- [ ] **Step 2: Write failing auth tests**

```python
# tests/test_auth.py
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: ImportError (app.auth doesn't exist yet)

- [ ] **Step 4: Implement auth.py**

```python
from dataclasses import dataclass

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

security = HTTPBearer()


@dataclass
class AuthUser:
    id: str
    email: str
    full_name: str = ""
    avatar_url: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_metadata = payload.get("user_metadata", {})
    return AuthUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        full_name=user_metadata.get("full_name", user_metadata.get("name", "")),
        avatar_url=user_metadata.get("avatar_url", user_metadata.get("picture")),
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_auth.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
cd backend && git add app/auth.py tests/conftest.py tests/test_auth.py
git commit -m "feat: add JWT auth dependency with tests"
```

---

### Task 5: Backend Profile Service + /api/me (TDD)

**Files:**
- Create: `backend/app/services/profiles.py`
- Create: `backend/app/routes/me.py`
- Create: `backend/tests/test_me.py`

- [ ] **Step 1: Write failing tests for /api/me**

```python
# tests/test_me.py
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
    # First call: select profile → empty
    select_response = MagicMock()
    select_response.data = []

    # Domain check
    domain_response = MagicMock()
    domain_response.data = [{"domain": "acme.com"}] if domain_allowed else []

    # Insert profile
    created_profile = _mock_profile(
        {"status": "active" if domain_allowed else "pending"}
    )
    insert_response = MagicMock()
    insert_response.data = [created_profile]

    # Chain: table("profiles").select("*").eq("id", ...).execute()
    # Then: table("allowed_domains").select("*").eq("domain", ...).eq("is_active", ...).execute()
    # Then: table("profiles").insert(...).execute()
    call_count = {"n": 0}
    original_table = mock_supabase.table

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

    # Profile lookup for require_active
    _setup_profile_exists(mock_supabase)

    # Update response
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_me.py -v`
Expected: ImportError (app.main, services don't exist yet)

- [ ] **Step 3: Implement services/profiles.py**

```python
from app.database import get_supabase


def get_profile(user_id: str) -> dict | None:
    supabase = get_supabase()
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None


def create_profile(user_id: str, email: str, full_name: str, avatar_url: str | None) -> dict:
    supabase = get_supabase()
    domain = email.split("@")[1] if "@" in email else ""

    # Check domain allowlist
    domain_response = (
        supabase.table("allowed_domains")
        .select("*")
        .eq("domain", domain)
        .eq("is_active", True)
        .execute()
    )
    status = "active" if domain_response.data else "pending"

    profile = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
        "role": "employee",
        "status": status,
        "domain": domain,
    }
    response = supabase.table("profiles").insert(profile).execute()
    return response.data[0]


def get_or_create_profile(
    user_id: str, email: str, full_name: str, avatar_url: str | None
) -> dict:
    profile = get_profile(user_id)
    if profile is None:
        profile = create_profile(user_id, email, full_name, avatar_url)
    return profile


def update_profile(user_id: str, updates: dict) -> dict:
    supabase = get_supabase()
    response = supabase.table("profiles").update(updates).eq("id", user_id).execute()
    return response.data[0]


def list_profiles(
    page: int = 1,
    per_page: int = 20,
    role: str | None = None,
    status: str | None = None,
    domain: str | None = None,
) -> tuple[list[dict], int]:
    supabase = get_supabase()
    query = supabase.table("profiles").select("*", count="exact")

    if role:
        query = query.eq("role", role)
    if status:
        query = query.eq("status", status)
    if domain:
        query = query.eq("domain", domain)

    offset = (page - 1) * per_page
    response = query.range(offset, offset + per_page - 1).execute()
    return response.data, response.count or 0
```

- [ ] **Step 4: Implement routes/me.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthUser, get_current_user
from app.models import ProfileResponse, ProfileUpdate
from app.services.profiles import get_or_create_profile, update_profile

router = APIRouter(prefix="/api")


def _get_profile(user: AuthUser = Depends(get_current_user)) -> dict:
    """Look up or create profile. Used by both GET and PUT."""
    return get_or_create_profile(user.id, user.email, user.full_name, user.avatar_url)


def _require_active(profile: dict = Depends(_get_profile)) -> dict:
    if profile["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {profile['status']}",
        )
    return profile


@router.get("/me", response_model=ProfileResponse)
async def get_me(profile: dict = Depends(_get_profile)):
    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_me(
    body: ProfileUpdate,
    profile: dict = Depends(_require_active),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return profile
    return update_profile(profile["id"], updates)
```

- [ ] **Step 5: Create a minimal app/main.py so tests can import it**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.me import router as me_router

app = FastAPI(title="Clay Talent Portal API")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_me.py -v`
Expected: All 6 tests PASS

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/services/profiles.py app/routes/me.py app/main.py tests/test_me.py
git commit -m "feat: add profile service and /api/me endpoints with tests"
```

---

### Task 6: Backend Domain Service + Admin Domain Endpoints (TDD)

**Files:**
- Create: `backend/app/services/domains.py`
- Modify: `backend/app/routes/admin.py`
- Create: `backend/tests/test_admin.py`

- [ ] **Step 1: Write failing tests for admin domain endpoints**

```python
# tests/test_admin.py
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
    """Make profile lookup return an admin."""
    profile = _mock_profile()
    mock_response = MagicMock()
    mock_response.data = [profile]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )
    return profile


def _setup_employee_profile(mock_supabase):
    """Make profile lookup return an employee."""
    profile = _mock_profile({"id": "emp-id-456", "email": "employee@acme.com", "role": "employee"})
    mock_response = MagicMock()
    mock_response.data = [profile]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        mock_response
    )
    return profile


# --- Domain endpoint tests ---


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_admin.py -v`
Expected: Failures (admin routes don't exist yet)

- [ ] **Step 3: Implement services/domains.py**

```python
from app.database import get_supabase


def list_domains() -> list[dict]:
    supabase = get_supabase()
    response = supabase.table("allowed_domains").select("*").execute()
    return response.data


def create_domain(domain: str, added_by: str, activate_existing: bool = False) -> dict:
    supabase = get_supabase()
    response = (
        supabase.table("allowed_domains")
        .insert({"domain": domain, "added_by": added_by})
        .execute()
    )

    if activate_existing:
        supabase.table("profiles").update({"status": "active"}).eq("domain", domain).eq(
            "status", "pending"
        ).execute()

    return response.data[0]


def update_domain(domain_id: str, updates: dict) -> dict:
    supabase = get_supabase()
    response = (
        supabase.table("allowed_domains").update(updates).eq("id", domain_id).execute()
    )
    return response.data[0]


def delete_domain(domain_id: str) -> None:
    supabase = get_supabase()
    supabase.table("allowed_domains").delete().eq("id", domain_id).execute()
```

- [ ] **Step 4: Implement routes/admin.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthUser, get_current_user
from app.models import (
    DomainCreate,
    DomainResponse,
    DomainUpdate,
    PaginatedUsers,
    ProfileResponse,
    UserUpdate,
)
from app.services.profiles import get_or_create_profile, list_profiles, update_profile
from app.services.domains import list_domains, create_domain, update_domain, delete_domain

router = APIRouter(prefix="/api/admin")


def _require_admin(user: AuthUser = Depends(get_current_user)) -> dict:
    """Dependency: user must be an active admin."""
    profile = get_or_create_profile(user.id, user.email, user.full_name, user.avatar_url)
    if profile["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {profile['status']}",
        )
    if profile["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return profile


# --- Domain endpoints ---


@router.get("/domains", response_model=list[DomainResponse])
async def get_domains(admin: dict = Depends(_require_admin)):
    return list_domains()


@router.post("/domains", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(body: DomainCreate, admin: dict = Depends(_require_admin)):
    return create_domain(body.domain, admin["id"], body.activate_existing)


@router.patch("/domains/{domain_id}", response_model=DomainResponse)
async def patch_domain(
    domain_id: str, body: DomainUpdate, admin: dict = Depends(_require_admin)
):
    return update_domain(domain_id, body.model_dump())


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_domain(domain_id: str, admin: dict = Depends(_require_admin)):
    delete_domain(domain_id)


# --- User management endpoints ---


@router.get("/users", response_model=PaginatedUsers)
async def get_users(
    page: int = 1,
    per_page: int = 20,
    role: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    admin: dict = Depends(_require_admin),
):
    users, total = list_profiles(page, per_page, role, status, domain)
    return PaginatedUsers(users=users, total=total, page=page, per_page=per_page)


@router.patch("/users/{user_id}", response_model=ProfileResponse)
async def patch_user(
    user_id: str, body: UserUpdate, admin: dict = Depends(_require_admin)
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    return update_profile(user_id, updates)
```

- [ ] **Step 5: Register admin router in main.py**

Add to `app/main.py`:

```python
from app.routes.admin import router as admin_router

app.include_router(admin_router)
```

The full `main.py` should now be:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.me import router as me_router
from app.routes.admin import router as admin_router

app = FastAPI(title="Clay Talent Portal API")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(admin_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_admin.py -v`
Expected: All 4 tests PASS

- [ ] **Step 7: Run all backend tests**

Run: `cd backend && python -m pytest -v`
Expected: All tests PASS (auth + me + admin)

- [ ] **Step 8: Commit**

```bash
cd backend && git add app/services/domains.py app/routes/admin.py app/main.py tests/test_admin.py
git commit -m "feat: add domain service and admin endpoints with tests"
```

---

### Task 7: Backend Seed Admin + Lifespan

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add lifespan with seed admin logic**

Replace `backend/app/main.py` with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import get_supabase
from app.routes.me import router as me_router
from app.routes.admin import router as admin_router


def _seed_admin() -> None:
    """Promote the seed admin email to admin role on startup."""
    settings = get_settings()
    if not settings.seed_admin_email:
        return

    supabase = get_supabase()
    response = (
        supabase.table("profiles")
        .select("id, role")
        .eq("email", settings.seed_admin_email)
        .execute()
    )
    if not response.data:
        return

    profile = response.data[0]
    if profile["role"] != "admin":
        supabase.table("profiles").update({"role": "admin", "status": "active"}).eq(
            "id", profile["id"]
        ).execute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_admin()
    yield


app = FastAPI(title="Clay Talent Portal API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(admin_router)
```

- [ ] **Step 2: Run all backend tests**

Run: `cd backend && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
cd backend && git add app/main.py
git commit -m "feat: add seed admin bootstrap on startup"
```

---

### Task 8: Frontend Project Init

**Files:**
- Create: `frontend/` (via create-next-app)

- [ ] **Step 1: Create Next.js project**

Run from the repo root:
```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --turbopack --use-npm
```

When prompted for import alias, accept the default `@/*`.

- [ ] **Step 2: Install Supabase dependencies**

```bash
cd frontend && npm install @supabase/supabase-js @supabase/ssr
```

- [ ] **Step 3: Create .env.local.example**

Create `frontend/.env.local.example`:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
NEXT_PUBLIC_APP_NAME=Clay Talent Portal
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Next.js frontend with Supabase dependencies"
```

---

### Task 9: Frontend Config + Supabase Clients

**Files:**
- Create: `frontend/src/lib/config.ts`
- Create: `frontend/src/lib/supabase/client.ts`
- Create: `frontend/src/lib/supabase/server.ts`
- Create: `frontend/src/types/google.d.ts`

- [ ] **Step 1: Create lib/config.ts**

```typescript
export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Clay Talent Portal"
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
```

- [ ] **Step 2: Create lib/supabase/client.ts**

```typescript
import { createBrowserClient } from "@supabase/ssr"

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

- [ ] **Step 3: Create lib/supabase/server.ts**

```typescript
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

export async function createServerSupabaseClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // setAll is called from Server Components where cookies cannot be set.
            // This can be safely ignored if middleware refreshes the session.
          }
        },
      },
    }
  )
}
```

- [ ] **Step 4: Create types/google.d.ts**

```typescript
interface GoogleCredentialResponse {
  credential: string
  select_by: string
}

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string
    callback: (response: GoogleCredentialResponse) => void
    nonce?: string
    use_fedcm_for_prompt?: boolean
    auto_select?: boolean
  }) => void
  prompt: (notification?: (notification: { getMomentType: () => string }) => void) => void
  renderButton: (
    element: HTMLElement,
    config: { theme?: string; size?: string; text?: string; width?: number }
  ) => void
}

declare const google: {
  accounts: {
    id: GoogleAccountsId
  }
}
```

- [ ] **Step 5: Commit**

```bash
cd frontend && git add src/lib/ src/types/
git commit -m "feat: add frontend config, Supabase clients, and Google type declarations"
```

---

### Task 10: Frontend Login Page + Google One Tap

**Files:**
- Create: `frontend/src/app/page.tsx`

- [ ] **Step 1: Write the login page**

Replace the contents of `frontend/src/app/page.tsx`:

```tsx
"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Script from "next/script"
import { createClient } from "@/lib/supabase/client"
import { APP_NAME } from "@/lib/config"

async function generateNonce(): Promise<[string, string]> {
  const randomValues = crypto.getRandomValues(new Uint8Array(32))
  const nonce = Array.from(randomValues, (byte) => byte.toString(36)).join("")
  const encoder = new TextEncoder()
  const encodedNonce = encoder.encode(nonce)
  const hashBuffer = await crypto.subtle.digest("SHA-256", encodedNonce)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashedNonce = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("")
  return [nonce, hashedNonce]
}

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if already signed in
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        router.replace("/dashboard")
      } else {
        setLoading(false)
      }
    })
  }, [router, supabase])

  async function initializeGoogleOneTap() {
    const [nonce, hashedNonce] = await generateNonce()

    google.accounts.id.initialize({
      client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!,
      callback: async (response: GoogleCredentialResponse) => {
        const { error } = await supabase.auth.signInWithIdToken({
          provider: "google",
          token: response.credential,
          nonce,
        })
        if (error) {
          setError("Sign-in failed. Please try again.")
        } else {
          router.push("/dashboard")
        }
      },
      nonce: hashedNonce,
      use_fedcm_for_prompt: true,
      auto_select: true,
    })

    google.accounts.id.prompt()

    const buttonEl = document.getElementById("google-signin-button")
    if (buttonEl) {
      google.accounts.id.renderButton(buttonEl, {
        theme: "outline",
        size: "large",
        text: "signin_with",
        width: 300,
      })
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-gray-50">
      <Script
        src="https://accounts.google.com/gsi/client"
        onReady={initializeGoogleOneTap}
      />

      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">{APP_NAME}</h1>
        <p className="mt-2 text-gray-600">Sign in to continue</p>
      </div>

      <div id="google-signin-button" />

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify the page builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds (page won't work without env vars, but it should compile)

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/app/page.tsx
git commit -m "feat: add login page with Google One Tap"
```

---

### Task 11: Frontend Middleware (Route Protection)

**Files:**
- Create: `frontend/src/middleware.ts`

- [ ] **Step 1: Write the middleware**

```typescript
import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh the session (important for token refresh)
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const isAuthPage = request.nextUrl.pathname === "/"
  const isProtectedPage =
    request.nextUrl.pathname.startsWith("/dashboard") ||
    request.nextUrl.pathname.startsWith("/admin")

  // Redirect unauthenticated users away from protected pages
  if (!user && isProtectedPage) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    return NextResponse.redirect(url)
  }

  // Redirect authenticated users away from login page
  if (user && isAuthPage) {
    const url = request.nextUrl.clone()
    url.pathname = "/dashboard"
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add src/middleware.ts
git commit -m "feat: add auth middleware for route protection"
```

---

### Task 12: Frontend API Client + Nav Component

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/Nav.tsx`
- Modify: `frontend/src/app/layout.tsx`

- [ ] **Step 1: Create lib/api.ts**

```typescript
import { createClient } from "@/lib/supabase/client"
import { API_URL } from "@/lib/config"

async function getAuthHeaders(): Promise<Record<string, string>> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("Not authenticated")
  }

  return {
    Authorization: `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `API error: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  getMe: () => apiFetch<Profile>("/api/me"),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    apiFetch<Profile>("/api/me", { method: "PUT", body: JSON.stringify(data) }),

  getUsers: (params?: { page?: number; role?: string; status?: string; domain?: string }) => {
    const query = new URLSearchParams()
    if (params?.page) query.set("page", String(params.page))
    if (params?.role) query.set("role", params.role)
    if (params?.status) query.set("status", params.status)
    if (params?.domain) query.set("domain", params.domain)
    const qs = query.toString()
    return apiFetch<PaginatedUsers>(`/api/admin/users${qs ? `?${qs}` : ""}`)
  },
  updateUser: (id: string, data: { role?: string; status?: string }) =>
    apiFetch<Profile>(`/api/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getDomains: () => apiFetch<Domain[]>("/api/admin/domains"),
  createDomain: (data: { domain: string; activate_existing?: boolean }) =>
    apiFetch<Domain>("/api/admin/domains", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateDomain: (id: string, data: { is_active: boolean }) =>
    apiFetch<Domain>(`/api/admin/domains/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteDomain: (id: string) =>
    apiFetch<void>(`/api/admin/domains/${id}`, { method: "DELETE" }),
}

// Types matching backend models
export interface Profile {
  id: string
  email: string
  full_name: string
  avatar_url: string | null
  role: "admin" | "recruiter" | "employee"
  status: "active" | "pending" | "archived"
  domain: string
  created_at: string
  updated_at: string
}

export interface Domain {
  id: string
  domain: string
  added_by: string | null
  is_active: boolean
  created_at: string
}

export interface PaginatedUsers {
  users: Profile[]
  total: number
  page: number
  per_page: number
}
```

- [ ] **Step 2: Create components/Nav.tsx**

```tsx
"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { APP_NAME } from "@/lib/config"
import type { Profile } from "@/lib/api"

export default function Nav({ profile }: { profile: Profile | null }) {
  const router = useRouter()
  const supabase = createClient()

  async function handleSignOut() {
    await supabase.auth.signOut()
    router.push("/")
  }

  const initials = profile?.full_name
    ? profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?"

  return (
    <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
      <Link href="/dashboard" className="text-lg font-bold text-gray-900">
        {APP_NAME}
      </Link>

      <div className="flex items-center gap-4">
        {profile?.role === "admin" && (
          <Link
            href="/admin"
            className="rounded border border-indigo-500 px-3 py-1 text-sm font-medium text-indigo-600 hover:bg-indigo-50"
          >
            Admin Panel
          </Link>
        )}

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
            {initials}
          </div>
          <button
            onClick={handleSignOut}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
```

- [ ] **Step 3: Update app/layout.tsx**

Replace `frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { APP_NAME } from "@/lib/config"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: APP_NAME,
  description: `${APP_NAME} — Sign in to continue`,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

- [ ] **Step 4: Commit**

```bash
cd frontend && git add src/lib/api.ts src/components/Nav.tsx src/app/layout.tsx
git commit -m "feat: add API client, Nav component, and root layout"
```

---

### Task 13: Frontend Dashboard Page

**Files:**
- Create: `frontend/src/app/dashboard/page.tsx`

- [ ] **Step 1: Write the dashboard page**

```tsx
"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Nav from "@/components/Nav"
import { api, type Profile } from "@/lib/api"

export default function DashboardPage() {
  const router = useRouter()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        setProfile(p)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  if (profile && profile.status !== "active") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <div className="text-5xl">&#9203;</div>
        <h1 className="text-xl font-semibold text-gray-900">
          {profile.status === "pending"
            ? "Account Pending Approval"
            : "Account Deactivated"}
        </h1>
        <p className="max-w-sm text-center text-gray-600">
          {profile.status === "pending"
            ? "Your organization hasn't been approved yet. An administrator will review your request."
            : "Your account has been deactivated. Contact an administrator for assistance."}
        </p>
        <div className="rounded bg-gray-100 px-4 py-2 text-sm text-gray-500">
          Signed in as {profile.email}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="text-2xl font-semibold text-gray-900">
          Welcome back, {profile?.full_name || "there"}
        </h1>
        <p className="mt-1 text-gray-500">
          Role: {profile?.role}
        </p>

        <div className="mt-8 rounded-lg border-2 border-dashed border-gray-300 p-10 text-center text-gray-400">
          Future feature content will go here based on role
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/app/dashboard/
git commit -m "feat: add dashboard page with pending/archived states"
```

---

### Task 14: Frontend Admin Panel

**Files:**
- Create: `frontend/src/app/admin/page.tsx`

- [ ] **Step 1: Write the admin panel page**

```tsx
"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Nav from "@/components/Nav"
import { api, type Profile, type Domain } from "@/lib/api"

type Tab = "users" | "domains"

export default function AdminPage() {
  const router = useRouter()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [tab, setTab] = useState<Tab>("users")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getMe()
      .then((p) => {
        if (p.role !== "admin") {
          router.replace("/dashboard")
          return
        }
        setProfile(p)
        setLoading(false)
      })
      .catch(() => router.replace("/dashboard"))
  }, [router])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav profile={profile} />
      <div className="mx-auto max-w-5xl px-6 py-6">
        <div className="flex gap-4 border-b border-gray-200">
          <button
            onClick={() => setTab("users")}
            className={`pb-3 text-sm font-medium ${
              tab === "users"
                ? "border-b-2 border-indigo-600 text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setTab("domains")}
            className={`pb-3 text-sm font-medium ${
              tab === "domains"
                ? "border-b-2 border-indigo-600 text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Domains
          </button>
        </div>

        <div className="mt-6">
          {tab === "users" ? <UsersTab /> : <DomainsTab />}
        </div>
      </div>
    </div>
  )
}

function UsersTab() {
  const [users, setUsers] = useState<Profile[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [roleFilter, setRoleFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .getUsers({
        page,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
      })
      .then((data) => {
        setUsers(data.users)
        setTotal(data.total)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [page, roleFilter, statusFilter])

  async function handleUpdateUser(userId: string, updates: { role?: string; status?: string }) {
    const updated = await api.updateUser(userId, updates)
    setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)))
  }

  return (
    <div>
      <div className="mb-4 flex gap-2">
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1) }}
          className="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="recruiter">Recruiter</option>
          <option value="employee">Employee</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="rounded border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500">
                <th className="pb-2 font-medium">User</th>
                <th className="pb-2 font-medium">Domain</th>
                <th className="pb-2 font-medium">Role</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-100">
                  <td className="py-3">
                    <div className="font-medium text-gray-900">{user.full_name || "—"}</div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </td>
                  <td className="py-3 text-gray-600">{user.domain}</td>
                  <td className="py-3">
                    <select
                      value={user.role}
                      onChange={(e) => handleUpdateUser(user.id, { role: e.target.value })}
                      className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                    >
                      <option value="admin">admin</option>
                      <option value="recruiter">recruiter</option>
                      <option value="employee">employee</option>
                    </select>
                  </td>
                  <td className="py-3">
                    <select
                      value={user.status}
                      onChange={(e) => handleUpdateUser(user.id, { status: e.target.value })}
                      className="rounded border border-gray-200 bg-white px-2 py-1 text-xs"
                    >
                      <option value="active">active</option>
                      <option value="pending">pending</option>
                      <option value="archived">archived</option>
                    </select>
                  </td>
                  <td className="py-3 text-right text-xs text-gray-400">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <span>{total} users total</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={users.length < 20}
                className="rounded border px-3 py-1 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function DomainsTab() {
  const [domains, setDomains] = useState<Domain[]>([])
  const [newDomain, setNewDomain] = useState("")
  const [activateExisting, setActivateExisting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getDomains()
      .then((data) => {
        setDomains(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!newDomain.trim()) return
    const created = await api.createDomain({
      domain: newDomain.trim().toLowerCase(),
      activate_existing: activateExisting,
    })
    setDomains((prev) => [...prev, created])
    setNewDomain("")
    setActivateExisting(false)
  }

  async function handleToggle(domain: Domain) {
    const updated = await api.updateDomain(domain.id, { is_active: !domain.is_active })
    setDomains((prev) => prev.map((d) => (d.id === domain.id ? updated : d)))
  }

  async function handleDelete(domainId: string) {
    await api.deleteDomain(domainId)
    setDomains((prev) => prev.filter((d) => d.id !== domainId))
  }

  if (loading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <form onSubmit={handleAdd} className="mb-6 flex items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Domain</label>
          <input
            type="text"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="acme.com"
            className="rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={activateExisting}
            onChange={(e) => setActivateExisting(e.target.checked)}
          />
          Activate pending users
        </label>
        <button
          type="submit"
          className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Add Domain
        </button>
      </form>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500">
            <th className="pb-2 font-medium">Domain</th>
            <th className="pb-2 font-medium">Status</th>
            <th className="pb-2 font-medium">Added</th>
            <th className="pb-2 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {domains.map((domain) => (
            <tr key={domain.id} className="border-b border-gray-100">
              <td className="py-3 font-medium text-gray-900">{domain.domain}</td>
              <td className="py-3">
                <span
                  className={`rounded px-2 py-0.5 text-xs ${
                    domain.is_active
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {domain.is_active ? "active" : "disabled"}
                </span>
              </td>
              <td className="py-3 text-gray-500">
                {new Date(domain.created_at).toLocaleDateString()}
              </td>
              <td className="py-3 text-right">
                <button
                  onClick={() => handleToggle(domain)}
                  className="mr-3 text-xs text-indigo-600 hover:underline"
                >
                  {domain.is_active ? "Disable" : "Enable"}
                </button>
                <button
                  onClick={() => handleDelete(domain.id)}
                  className="text-xs text-red-600 hover:underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd frontend && git add src/app/admin/
git commit -m "feat: add admin panel with user management and domain management"
```

---

### Task 15: Render Deployment Config

**Files:**
- Create: `render.yaml`

- [ ] **Step 1: Create render.yaml**

```yaml
services:
  - type: web
    name: clay-talent-portal-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: SUPABASE_JWT_SECRET
        sync: false
      - key: APP_NAME
        value: Clay Talent Portal
      - key: SEED_ADMIN_EMAIL
        sync: false
      - key: ALLOWED_ORIGINS
        sync: false

  - type: web
    name: clay-talent-portal-web
    runtime: node
    rootDir: frontend
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NEXT_PUBLIC_SUPABASE_URL
        sync: false
      - key: NEXT_PUBLIC_SUPABASE_ANON_KEY
        sync: false
      - key: NEXT_PUBLIC_GOOGLE_CLIENT_ID
        sync: false
      - key: NEXT_PUBLIC_APP_NAME
        value: Clay Talent Portal
      - key: NEXT_PUBLIC_API_URL
        sync: false
```

- [ ] **Step 2: Commit**

```bash
git add render.yaml
git commit -m "feat: add Render deployment blueprint"
```

---

### Task 16: Final Integration Verification

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && python -m pytest -v
```

Expected: All tests PASS

- [ ] **Step 2: Build frontend**

```bash
cd frontend && npm run build
```

Expected: Build succeeds

- [ ] **Step 3: Manual smoke test (local)**

Start backend:
```bash
cd backend && cp .env.example .env  # Fill in real Supabase values
source .venv/bin/activate && uvicorn app.main:app --reload
```

Start frontend (in a separate terminal):
```bash
cd frontend && cp .env.local.example .env.local  # Fill in real values
npm run dev
```

Verify:
1. Visit http://localhost:3000 — should see login page with Google One Tap
2. Sign in with Google — should redirect to /dashboard
3. If domain is not in allowed_domains — should see pending message
4. Add domain via admin panel (after seed admin setup) — user becomes active

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Clay Talent Portal foundation complete"
```

# Clay Talent Portal — Design Spec

Foundation web app with Supabase authentication (Google One Tap), role-based user management, and domain allowlisting. Built as a starter template to add features on top of.

## Tech Stack

- **Frontend:** Next.js (App Router), Supabase JS SDK (auth only)
- **Backend:** Python FastAPI, Supabase Python client (service role)
- **Database/Auth:** Supabase (hosted)
- **Deployment:** Render (monorepo, two services)

## Architecture

Three layers with a strict data flow rule: the frontend only talks to Supabase for authentication. All data operations go through FastAPI.

```
Browser (Next.js)
  ├── Supabase JS SDK → Google One Tap OAuth → JWT
  └── FastAPI (JWT in Authorization header) → all data reads/writes

FastAPI (Render Web Service)
  ├── JWT validation middleware
  ├── Domain allowlist check
  ├── Role-based authorization
  └── Supabase Python client (service role) → database

Supabase (hosted)
  ├── auth.users (Google OAuth sessions)
  ├── public.profiles (user data, role, status)
  └── public.allowed_domains (admin-managed)
```

## Auth Flow

### Sign-up (new user)

1. User clicks Google One Tap on the Next.js frontend.
2. Supabase JS SDK handles the OAuth flow, creates an `auth.users` entry, returns a JWT.
3. Frontend sends first request to FastAPI with the JWT.
4. FastAPI validates the JWT, extracts the email domain.
5. FastAPI checks `allowed_domains` table:
   - Domain is allowed and active: creates `profiles` row with `role=employee`, `status=active`.
   - Domain is not allowed: creates `profiles` row with `status=pending`.
6. Returns the profile to the frontend.

### Returning user

1. Google One Tap signs them in, Supabase returns JWT.
2. Frontend sends requests to FastAPI with JWT.
3. FastAPI validates JWT, looks up profile, checks status:
   - `active` — proceed normally.
   - `pending` — return 403, frontend shows "Account Pending Approval" message.
   - `archived` — return 403, frontend shows "Account Deactivated" message.

### Admin actions

- Change a user's role (employee / recruiter / admin).
- Change a user's status (active / pending / archived).
- Add/remove/enable/disable entries in `allowed_domains`.
- When a domain is added, optionally bulk-activate pending users from that domain.

## Database Schema

### public.profiles

| Column     | Type        | Notes                                           |
|------------|-------------|-------------------------------------------------|
| id         | uuid        | PK, references auth.users(id)                   |
| email      | text        | From Google, not null                            |
| full_name  | text        | From Google profile                              |
| avatar_url | text        | From Google profile, nullable                    |
| role       | enum        | admin / recruiter / employee, default: employee  |
| status     | enum        | active / pending / archived, default: pending    |
| domain     | text        | Extracted from email, indexed                    |
| created_at | timestamptz | Default: now()                                   |
| updated_at | timestamptz | Auto-updated on change                           |

### public.allowed_domains

| Column     | Type        | Notes                                      |
|------------|-------------|--------------------------------------------|
| id         | uuid        | PK, default: gen_random_uuid()             |
| domain     | text        | Unique, not null (e.g. "acme.com")         |
| added_by   | uuid        | References profiles(id), admin who added it|
| is_active  | boolean     | Default: true, soft-disable without deleting|
| created_at | timestamptz | Default: now()                             |

### Key decisions

- `profiles.id` matches `auth.users.id` — no separate join needed.
- `domain` stored on profile for fast filtering without parsing email every time.
- `allowed_domains` uses `is_active` for soft-disable instead of deleting.
- Role is a column on profiles, not a separate permissions table — expandable later.

## API Endpoints

### Auth/Profile

- `GET /api/me` — Returns current user's profile (role, status). Called after login.
- `PUT /api/me` — User updates their own profile (name, avatar only — not role/status).

### Admin: User management

- `GET /api/admin/users` — List all users with filtering by role, status, domain. Paginated.
- `PATCH /api/admin/users/{id}` — Update a user's role or status.

### Admin: Domain management

- `GET /api/admin/domains` — List all allowed domains.
- `POST /api/admin/domains` — Add a new allowed domain. Optionally bulk-activate pending users.
- `PATCH /api/admin/domains/{id}` — Enable/disable a domain.
- `DELETE /api/admin/domains/{id}` — Hard delete a domain.

### Middleware (all `/api/*` routes)

1. Validate Supabase JWT.
2. Look up profile — if none exists (first login), create one and run domain check.
3. Check status — reject `pending` and `archived` users (except on `GET /api/me` so they can see their status).
4. For `/api/admin/*` routes — verify `role=admin`.

## Frontend Pages

### `/` — Login page

Google One Tap prompt + manual "Sign in with Google" button as fallback.

### Pending/Archived state

Shown after login if user's status is `pending` or `archived`. Displays appropriate message with their email. No access to anything else.

### `/dashboard` — Dashboard (all active roles)

Landing page for all authenticated active users. Shows welcome message with name and role. "Admin Panel" link visible only to admins. Main content area is a placeholder for future role-based features. Advanced roles (recruiter, admin) will see additional content here as features are added.

### `/admin` — Admin Panel (admin only)

Two tabs:
- **Users tab** — Table with name, domain, role, status. Filter dropdowns for role and status. Edit action to change role or status.
- **Domains tab** — List of allowed domains. Add, remove, enable/disable.

## Configuration

The app name `"Clay Talent Portal"` is configurable in one place per service:

- **Frontend:** `NEXT_PUBLIC_APP_NAME` env variable (defaults to `"Clay Talent Portal"`), exposed via `lib/config.ts`.
- **Backend:** `APP_NAME` env variable (defaults to `"Clay Talent Portal"`), exposed via `config.py`.

Both are set in Render's environment config for production.

## Bootstrap

The first admin is a chicken-and-egg problem. Solution: an environment variable `SEED_ADMIN_EMAIL` (e.g. `SEED_ADMIN_EMAIL=jane@acme.com`). On startup, if a profile with that email exists and is not already an admin, FastAPI promotes it to `role=admin, status=active`. This runs once at boot and is the only way to create the initial admin. After that, the seed admin can promote others through the admin panel.

## Project Structure

```
oneshot/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Login page
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx          # Dashboard
│   │   │   ├── admin/
│   │   │   │   └── page.tsx          # Admin panel
│   │   │   └── layout.tsx            # Root layout
│   │   ├── components/
│   │   │   ├── Nav.tsx               # Navigation bar
│   │   │   ├── GoogleOneTap.tsx      # One Tap wrapper
│   │   │   └── AdminUserTable.tsx    # User management table
│   │   ├── lib/
│   │   │   ├── supabase.ts           # Supabase client (auth only)
│   │   │   ├── api.ts                # FastAPI client wrapper
│   │   │   └── config.ts             # APP_NAME and other constants
│   │   └── middleware.ts             # Route protection
│   ├── .env.local
│   ├── package.json
│   └── next.config.js
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, lifespan
│   │   ├── config.py                 # Settings (APP_NAME, Supabase keys)
│   │   ├── auth.py                   # JWT validation dependency
│   │   ├── models.py                 # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── me.py                 # GET/PUT /api/me
│   │   │   └── admin.py              # /api/admin/* endpoints
│   │   └── services/
│   │       ├── profiles.py           # Profile CRUD via Supabase
│   │       └── domains.py            # Domain CRUD via Supabase
│   ├── requirements.txt
│   └── .env
├── render.yaml                       # Render Blueprint (both services)
└── AGENTS.md
```

## Deployment (Render)

Monorepo with two Render services defined in `render.yaml`:

- **backend:** Python Web Service, root directory `backend/`, start command `uvicorn app.main:app`.
- **frontend:** Node Web Service, root directory `frontend/`, build command `npm run build`, start command `npm start`.

Both services share environment variables for Supabase URL/keys and APP_NAME via Render environment groups or per-service config.

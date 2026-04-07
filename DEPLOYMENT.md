# Deployment Guide

## Prerequisites

Before running the app locally or deploying, you need:

1. **Supabase project** — create one at [supabase.com](https://supabase.com). Note the Project URL, anon key, service role key, and JWT secret (Settings > API).
2. **Google OAuth credentials** — create an OAuth 2.0 Client ID (Web application) at [console.cloud.google.com](https://console.cloud.google.com). Add `http://localhost:3000` to authorized JavaScript origins.
3. **Enable Google provider in Supabase** — Authentication > Providers > Google. Enter your Google Client ID and Client Secret.

### Apply the database migration

Run the SQL in `supabase/migrations/001_schema.sql` via the Supabase dashboard (SQL Editor) or the CLI:

```bash
supabase db push
```

This creates the `profiles` and `allowed_domains` tables, enums, indexes, and the `updated_at` trigger.

---

## Local Development

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your Supabase credentials
```

Required variables in `backend/.env`:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (secret, server-side only) |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase Settings > API |
| `APP_NAME` | Display name (default: `Clay Talent Portal`) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (default: `http://localhost:3000`) |
| `SEED_ADMIN_EMAIL` | Email to auto-promote to admin on startup (optional) |

Start the backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Docs are at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your credentials
```

Required variables in `frontend/.env.local`:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (public) key |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `NEXT_PUBLIC_APP_NAME` | Display name (default: `Clay Talent Portal`) |
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

Start the frontend:

```bash
npm install
npm run dev
```

The app runs at `http://localhost:3000`.

### Running tests

```bash
cd backend
source .venv/bin/activate
python -m pytest -v
```

### Bootstrap the first admin

The first admin is a chicken-and-egg problem. To bootstrap:

1. Set `SEED_ADMIN_EMAIL=you@yourdomain.com` in `backend/.env`.
2. Sign in via Google One Tap on the frontend — this creates your profile.
3. Restart the backend — on startup it promotes the matching profile to `role=admin, status=active`.
4. You can now manage users and domains through the admin panel at `/admin`.

---

## Production Deployment (Render)

The repo includes a `render.yaml` Blueprint that defines both services.

### Setup

1. Push this repo to GitHub.
2. In Render, go to **Blueprints** > **New Blueprint Instance** and connect the repo.
3. Render reads `render.yaml` and creates two services:
   - **clay-talent-portal-api** — Python web service (backend)
   - **clay-talent-portal-web** — Node web service (frontend)

### Environment variables

Set the following in Render's dashboard for each service:

**Backend (`clay-talent-portal-api`):**

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key |
| `SUPABASE_JWT_SECRET` | JWT secret |
| `SEED_ADMIN_EMAIL` | Your admin email |
| `ALLOWED_ORIGINS` | Your frontend's Render URL (e.g. `https://clay-talent-portal-web.onrender.com`) |

**Frontend (`clay-talent-portal-web`):**

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth Client ID |
| `NEXT_PUBLIC_API_URL` | Your backend's Render URL (e.g. `https://clay-talent-portal-api.onrender.com`) |

### Google OAuth for production

Add your production frontend URL to the authorized JavaScript origins in the Google Cloud Console (e.g. `https://clay-talent-portal-web.onrender.com`).

### Post-deploy checklist

1. Visit the frontend URL — you should see the login page.
2. Sign in with Google.
3. Check the backend logs to confirm the seed admin was promoted.
4. Go to `/admin` and add your company domain to the allowed domains list.
5. Remove or change `SEED_ADMIN_EMAIL` once the admin is bootstrapped — it only runs on startup and is a no-op if the profile is already an admin.

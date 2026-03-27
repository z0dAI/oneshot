# Deployment Guide

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) 18+
- A [Supabase](https://supabase.com/) project
- A [Google Cloud](https://console.cloud.google.com/) OAuth client ID

## Supabase Setup

### 1. Create the database schema

Open your Supabase Dashboard, go to **SQL Editor**, and run the contents of `backend/supabase/migration.sql`. This creates:

- `user_role` and `user_status` enum types
- `profiles` table (linked to `auth.users`)
- `allowed_domains` table
- An `updated_at` trigger on profiles

### 2. Enable Google OAuth

1. In the Supabase Dashboard, go to **Authentication > Providers > Google**
2. Toggle Google on
3. Enter your Google Cloud OAuth **Client ID** and **Client Secret**
4. Copy the **Callback URL** shown by Supabase — you'll need it in Google Cloud Console

### 3. Configure Google Cloud OAuth

1. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
2. Create (or edit) an OAuth 2.0 Client ID of type **Web application**
3. Under **Authorized JavaScript origins**, add:
   - `http://localhost:3000` (dev)
   - Your production frontend URL
4. Under **Authorized redirect URIs**, add the Supabase callback URL from step 2
5. Note the **Client ID** — you'll need it for the frontend env vars

### 4. Collect credentials

From **Supabase Dashboard > Settings > API**, collect:

| Value | Used by |
|-------|---------|
| Project URL | Backend (`SUPABASE_URL`) + Frontend (`NEXT_PUBLIC_SUPABASE_URL`) |
| `anon` public key | Frontend (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) |
| `service_role` secret key | Backend (`SUPABASE_SERVICE_ROLE_KEY`) |
| JWT Secret | Backend (`SUPABASE_JWT_SECRET`) |

---

## Local Development

### Backend

```bash
cd backend

# Copy env template and fill in real values
cp .env.example .env
# Edit .env with your Supabase credentials

# Install dependencies (uv handles Python version automatically)
uv sync --all-extras

# Run the server
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

### Frontend

```bash
cd frontend

# Copy env template and fill in real values
cp .env.local.example .env.local
# Edit .env.local with your Supabase + Google credentials

# Install dependencies
npm install

# Run the dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Environment Variables

**Backend (`backend/.env`):**

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key (full database access) |
| `SUPABASE_JWT_SECRET` | Yes | Supabase JWT secret (for validating user tokens) |
| `SEED_ADMIN_EMAIL` | No | Email to auto-promote to admin on startup |
| `APP_NAME` | No | Application name (default: "Clay Talent Portal") |
| `FRONTEND_URL` | No | Frontend origin for CORS (default: "http://localhost:3000") |

**Frontend (`frontend/.env.local`):**

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `NEXT_PUBLIC_API_URL` | No | Backend API URL (default: "http://localhost:8000") |
| `NEXT_PUBLIC_APP_NAME` | No | Application name (default: "Clay Talent Portal") |

### Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

### Creating the First Admin

Set `SEED_ADMIN_EMAIL` in `backend/.env` to the Google email of the first admin user. On startup, the backend checks if a profile with that email exists and promotes it to `role=admin, status=active`.

The flow:
1. Set `SEED_ADMIN_EMAIL=you@yourcompany.com` in `.env`
2. Start the backend
3. Sign in with that Google account on the frontend (this creates the profile)
4. Restart the backend (the seed logic runs at startup and promotes the profile)
5. Refresh the frontend — you now have admin access

After the first admin is created, they can promote other users through the Admin Panel.

---

## Production Deployment (Render)

The project includes a `render.yaml` Blueprint that defines both services.

### 1. Connect your repository

1. Push this repo to GitHub
2. In [Render Dashboard](https://dashboard.render.com/), go to **Blueprints > New Blueprint Instance**
3. Connect your GitHub repo and select the branch

Render will detect `render.yaml` and create two services:

- **clay-talent-portal-api** — Python backend
- **clay-talent-portal-web** — Node.js frontend

### 2. Configure environment variables

In the Render Dashboard, set the environment variables for each service. All variables marked `sync: false` in `render.yaml` must be set manually.

**Backend service (`clay-talent-portal-api`):**

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT secret |
| `SEED_ADMIN_EMAIL` | First admin's Google email |
| `APP_NAME` | Your app name |
| `FRONTEND_URL` | Your Render frontend URL (e.g., `https://clay-talent-portal-web.onrender.com`) |

**Frontend service (`clay-talent-portal-web`):**

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `NEXT_PUBLIC_API_URL` | Your Render backend URL (e.g., `https://clay-talent-portal-api.onrender.com`) |
| `NEXT_PUBLIC_APP_NAME` | Your app name |

### 3. Update OAuth redirect URIs

Add your production URLs to:

- **Google Cloud Console**: Add the production frontend URL to Authorized JavaScript origins, and the Supabase callback URL to Authorized redirect URIs
- **Supabase Dashboard > Authentication > URL Configuration**: Add the production frontend URL to Redirect URLs

### 4. Deploy

Render will automatically build and deploy both services. Subsequent pushes to the connected branch trigger redeployments.

### Build commands

| Service | Build | Start |
|---------|-------|-------|
| Backend | `pip install uv && uv sync --frozen` | `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | `npm install && npm run build` | `npm start` |

# Family Office Deal Flow Intelligence

Multi-tenant SaaS that automatically sources, scores, and generates investment memos on companies matching each client's investment thesis.

## Architecture

```
frontend/          Next.js 16 (Vercel)
backend/           FastAPI (Railway)
  ├── routers/     REST endpoints
  ├── services/    ScoringService, MemoService, AlertService, DocumentService
  ├── scrapers/    EDGAR, SBIR, GitHub, RSS, NIH, HN/YC
  ├── tasks/       Celery tasks (pipeline, scoring, memo)
  ├── models/      SQLAlchemy ORM
  └── tests/       pytest suite
prompts/           Claude prompt templates (scoring.txt, memo_generation.txt)
docker-compose.yml Local dev environment
```

**Stack:** Python 3.13 · FastAPI · SQLAlchemy · Alembic · Celery + Redis · PostgreSQL · Next.js 16 · Tailwind v4 · Clerk · Twilio · Anthropic Claude

## Local Development

### Prerequisites

- Python 3.13
- Node.js 20+
- Docker & Docker Compose

### 1 — Clone and configure

```bash
git clone <repo>
cd family-office-agent
```

Copy the backend env file and fill in secrets:

```bash
cp backend/.env.example backend/.env
```

Copy the frontend env file:

```bash
cp frontend/.env.local.example frontend/.env.local
```

### 2 — Start services with Docker Compose

```bash
docker compose up -d postgres redis
```

### 3 — Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn main:app --reload --port 8000

# In a separate terminal: start the Celery worker
celery -A celery_app worker --loglevel=info

# In a separate terminal: start Celery beat (scheduled jobs)
celery -A celery_app beat --loglevel=info
```

Or run everything with Docker Compose:

```bash
docker compose up
```

### 4 — Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✓ | PostgreSQL connection string — e.g. `postgresql://user:pass@localhost/familyoffice` |
| `ANTHROPIC_API_KEY` | ✓ | Claude API key for scoring and memo generation |
| `REDIS_URL` | ✓ | Redis connection string — e.g. `redis://localhost:6379/0` |
| `CLERK_SECRET_KEY` | ✓ | Clerk backend secret key (starts with `sk_`) |
| `TWILIO_ACCOUNT_SID` | ✓ | Twilio account SID for SMS alerts |
| `TWILIO_AUTH_TOKEN` | ✓ | Twilio auth token |
| `TWILIO_FROM_NUMBER` | ✓ | E.164 number alerts are sent from — e.g. `+15551234567` |
| `GITHUB_TOKEN` | — | GitHub personal access token (raises API rate limit from 60→5000 req/hr) |
| `ALLOWED_ORIGINS` | — | Comma-separated CORS origins. Default: `http://localhost:3000` |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | ✓ | Clerk publishable key (starts with `pk_`) |
| `CLERK_SECRET_KEY` | ✓ | Same Clerk secret key as backend |
| `NEXT_PUBLIC_API_URL` | — | Backend URL. Default: `http://localhost:8000` |

## Running Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -q
```

All tests use SQLite in-memory — no running Postgres or Redis needed.

## API Endpoints

The FastAPI server auto-generates interactive docs at `http://localhost:8000/docs`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | DB + Redis health check |
| `POST` | `/api/pipeline/run` | Trigger full scrape→score→memo pipeline for authenticated client |
| `GET` | `/api/pipeline/status/{job_id}` | Poll Celery task status |
| `GET` | `/api/deals` | Paginated deal list with filters (sector, stage, min_score, recommendation) |
| `GET` | `/api/deals/{id}` | Deal detail with latest score and memo |
| `POST` | `/api/deals/{id}/memo` | Generate or regenerate investment memo |
| `GET` | `/api/thesis` | Get client's investment thesis + config |
| `PUT` | `/api/thesis` | Update thesis and alert preferences |
| `GET` | `/api/alerts` | Recent SMS alerts sent for this client |
| `POST` | `/api/documents` | Upload a PDF or text file linked to a company |
| `GET` | `/api/documents` | List documents for a company (`?company_id=`) |

All endpoints require a Clerk JWT in the `Authorization: Bearer <token>` header. The token's `org_id` claim is mapped to the internal client UUID.

Rate limit: **100 requests/minute per IP**.

## Deploying to Railway (Backend)

1. Create a new Railway project and connect your GitHub repo.
2. Set the **root directory** to `backend/`.
3. Railway will detect `railway.json` and use the `Dockerfile` automatically.
4. Add the following environment variables in Railway's dashboard:
   - `DATABASE_URL` — use Railway's PostgreSQL plugin (auto-injected as `${{Postgres.DATABASE_URL}}`)
   - `REDIS_URL` — use Railway's Redis plugin
   - `ANTHROPIC_API_KEY`, `CLERK_SECRET_KEY`, `TWILIO_*`
   - `ALLOWED_ORIGINS` — set to your Vercel frontend URL, e.g. `https://your-app.vercel.app`
5. Add a second Railway service for the **Celery worker**:
   - Same repo + root directory
   - Override start command: `celery -A celery_app worker --loglevel=info`
6. Add a third service for **Celery beat** (scheduled jobs):
   - Start command: `celery -A celery_app beat --loglevel=info`
7. Run migrations via Railway's one-off commands:
   ```
   alembic upgrade head
   ```

## Deploying to Vercel (Frontend)

1. Import the repo into Vercel and set the **root directory** to `frontend/`.
2. Vercel detects Next.js automatically.
3. Add environment variables in the Vercel dashboard:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `NEXT_PUBLIC_API_URL` — your Railway backend URL, e.g. `https://api.your-app.up.railway.app`
4. Deploy. Vercel handles the build and CDN automatically.

## Database Migrations

```bash
# Create a new migration after changing a model
alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

Migration files live in `backend/alembic/versions/`. Current chain:
- `9ec53f6f4f22` — initial schema (clients, companies, scores, memos, pipeline_runs)
- `0002` — add `clerk_org_id` to clients
- `0003` — add `alerts` table
- `0004` — add `documents` table

## Security Notes

- Every database query includes `client_id` in the WHERE clause — enforced in `db/queries.py`
- `client_id` is never taken from the request body — always from the verified Clerk JWT
- Cross-tenant access returns `403 Forbidden` (not 404) to avoid leaking resource existence
- CORS is locked to `ALLOWED_ORIGINS`; credentials are not sent to unknown origins
- Rate limiting: 100 req/min per IP via slowapi
- `ThesisUpdateRequest` uses `extra='forbid'` to reject unknown fields

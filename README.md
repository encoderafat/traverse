# Traverse

Traverse is an AI agent system that reverse-engineers expertise into personalized learning DAGs. It researches real-world signals, builds a dependency graph, and generates realistic challenges that adapt as you learn.

## Features
- Research agent that extracts competencies from real-world sources
- DAG builder that sequences skills with prerequisites
- Challenge generator with realistic, scenario-based tasks
- Adaptive remediation that inserts prerequisite nodes when you struggle
- Progress tracking with blocked/in-progress/completed states
- OPIK tracing + LLM-as-judge evaluation hooks
- Interactive DAG visualization in the frontend

## Screenshot
Place a screenshot at `docs/screenshot.png` and update this section:

```
![Traverse UI](docs/screenshot.png)
```

## Architecture
- Backend: FastAPI API + multi-agent pipeline + SQLAlchemy models
- Frontend: Next.js app with ReactFlow graph rendering
- External services: Gemini, SerpAPI, Supabase auth, OPIK tracing

## Tech Stack
FastAPI, SQLAlchemy, PostgreSQL/Supabase, Next.js, React, ReactFlow, Gemini, SerpAPI, OPIK

## Getting Started (Local)

### Supabase
1. Create a Supabase project and copy the Project URL + anon key.
2. Configure frontend env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
3. Configure backend env vars: `SUPABASE_URL`, `SUPABASE_ANON_KEY`.
4. Enable your preferred auth providers (GitHub/Google) in Supabase if you plan to sign in.
5. If you use a custom JWT audience, set `SUPABASE_JWT_AUDIENCE` in backend `.env`.

### Backend
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Frontend
```
cd frontend
npm install
npm run dev
```

## Configuration

### Backend `.env`
Required:
- `DATABASE_URL`
- `GOOGLE_API_KEY`
- `GEMINI_MODEL`
- `SERPAPI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Optional:
- `OPIK_TRACK_DISABLE` (set to `true` to disable tracing)

### Frontend `.env.local`
Required:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`

## Running Tests
```
cd backend
pytest
```

E2E tests are skipped unless `RUN_E2E_TESTS=true` is set.

## API Reference (Minimal)
- `POST /api/paths`
- `GET /api/paths`
- `GET /api/paths/{id}`
- `POST /api/paths/{id}/nodes/{node_id}/challenges`
- `POST /api/challenges/{id}/submit`
- `POST /api/challenges/{id}/hint`
- `GET /api/paths/{id}/progress`

## Deployment
- Frontend: deploy to Vercel with frontend env vars
- Backend: deploy to Cloud Run with backend env vars
- Ensure the backend URL is configured in `NEXT_PUBLIC_API_URL`

## Observability (OPIK)
OPIK traces are emitted from all agents with prompt versions, A/B variants, and LLM-as-judge evaluation scores. Traces include key metadata (user/path/node context, counts, and parse errors). Disable locally by setting `OPIK_TRACK_DISABLE=true`.

## Roadmap
- Improve interview flow with dynamic follow-ups
- Add richer research grounding and source filtering
- Expand analytics and A/B experimentation


## License
MIT

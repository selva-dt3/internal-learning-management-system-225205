# LMS Backend (FastAPI + Supabase)

This service provides authentication and core APIs for the Internal LMS.

## Quickstart

1. Create `.env` based on `.env.example` and set required variables:
   - SUPABASE_URL
   - SUPABASE_KEY
   - APP_NAME (optional)
   - LOG_LEVEL (optional)
   - ENV (optional)
   - HOST/PORT/RELOAD (optional)
   - ALLOWED_ORIGINS (comma-separated CORS origins; see below)

2. Install dependencies:
   pip install -r requirements.txt

3. Run server (choose one):
   - Using validated module path (recommended):
     uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
   - Using the helper launcher:
     python -m src.api.cli

4. Sanity check:
   - GET http://localhost:3001/api/health
   - GET http://localhost:3001/

5. APIs:
   - GET /api/health
   - POST /api/auth/signup
   - POST /api/auth/login
   - GET /api/auth/me (requires Authorization: Bearer <access_token>)
   - GET /api/onboarding/status (auth required)
   - POST /api/onboarding/acknowledgements (auth required) { "document": "nda" | "coc" }
   - GET /api/analytics/summary (auth required; roles: admin, hr)
   - Users (roles: admin, hr unless noted)
     - GET /api/users
     - GET /api/users/{id}
     - POST /api/users (admin)
     - PUT /api/users/{id}
     - DELETE /api/users/{id} (admin)
   - Lessons (auth required)
     - GET /api/lessons (employees see only published)
     - GET /api/lessons/{id} (employees only published)
     - POST /api/lessons (admin/hr)
     - PUT /api/lessons/{id} (admin/hr)
     - DELETE /api/lessons/{id} (admin/hr)
   
Schema notes (Supabase):
   - onboarding (table): { user_id: uuid/text, nda_acknowledged: boolean, coc_acknowledged: boolean }
   - profiles (table): { user_id: uuid/text, role: text in ['admin','hr','employee'] } used for analytics counts
   - user_progress (optional table for analytics): { user_id, lessons_completed: int }
   - quiz_results (optional table for analytics): { user_id, passed: boolean }

## CORS configuration

The backend reads a comma-separated list of allowed origins from the `ALLOWED_ORIGINS` environment variable and applies it to FastAPI's `CORSMiddleware`.

- For local development:
  `ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000`

- For preview environments, include your preview frontend URL:
  `ALLOWED_ORIGINS=http://localhost:3000,https://<preview-host>:3000`

Example:
```
ALLOWED_ORIGINS=http://localhost:3000,https://vscode-internal-34912-beta.beta01.cloud.kavia.ai:3000
```

Note: Do not log or hardcode secrets. Supabase credentials are read from environment.

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

Note: Do not log or hardcode secrets. Supabase credentials are read from environment.

# Project Repository

This is the initial README file for the project.

## Preview environment configuration

- Backend (FastAPI): set `ALLOWED_ORIGINS` to include the frontend preview origin (e.g., `https://<preview-host>:3000`).
- Frontend (React): set `REACT_APP_BACKEND_API_URL` to the backend preview URL (e.g., `https://<preview-host>:3001`).

These settings ensure CORS allows cross-origin requests between the preview hosts.
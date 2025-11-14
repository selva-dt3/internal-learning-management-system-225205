"""
FastAPI Uvicorn launcher for the LMS backend.

Usage:
    python -m src.api.cli
This will start the server on 0.0.0.0:3001 and import the ASGI app from src.api.main:app.
"""
from __future__ import annotations

import os
import sys

import uvicorn

# Ensure the current working directory is on sys.path so "src" can be imported reliably
# This helps when running via python -m from atypical directories.
cwd = os.path.abspath(os.getcwd())
if cwd not in sys.path:
    sys.path.insert(0, cwd)


def main() -> None:
    """
    Launch uvicorn pointing to src.api.main:app on port 3001.
    """
    # Bind host/port; allow override via environment if provided
    host = os.environ.get("HOST", "0.0.0.0")
    port_str = os.environ.get("PORT", "3001")
    try:
        port = int(port_str)
    except ValueError:
        port = 3001

    # Import check: ensure the ASGI app can be imported before starting
    try:
        # Import and reference the attribute to satisfy linter and validate existence
        from src.api import main as _main  # type: ignore
        _ = getattr(_main, "app")  # ensure 'app' attribute exists
    except Exception as exc:
        # Provide a clear message if import fails
        print("ERROR: Failed to import 'src.api.main:app'. Please verify PYTHONPATH and module path.")
        print(f"Details: {exc}")
        sys.exit(1)

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=os.environ.get("RELOAD", "false").lower() == "true",
        proxy_headers=True,
        forwarded_allow_ips="*",
        factory=False,
    )


if __name__ == "__main__":
    main()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .config import settings
from .logging_config import configure_logging, get_logger
from .errors import (
    register_exception_handlers,
)
from .clients.supabase_client import init_supabase_client, close_supabase_client
from .routers.health import router as health_router
from .routers.auth import router as auth_router
from .routers.onboarding import router as onboarding_router
from .routers.analytics import router as analytics_router
from .routers.users import router as users_router
from .routers.lessons import router as lessons_router

# Configure logging early
configure_logging()
logger = get_logger(__name__)

openapi_tags = [
    {"name": "Health", "description": "Health and monitoring endpoints."},
    {
        "name": "Auth",
        "description": "Authentication endpoints using Supabase as identity provider.",
    },
    {
        "name": "Onboarding",
        "description": "Employee onboarding endpoints (acknowledgements, status).",
    },
    {
        "name": "Analytics",
        "description": "Analytics endpoints restricted to Admin/HR roles.",
    },
    {
        "name": "Users",
        "description": "User management endpoints backed by Supabase 'profiles' table. Admin/HR access.",
    },
    {
        "name": "Lessons",
        "description": "Lessons CRUD backed by Supabase 'lessons' table. Admin/HR manage; Employees read.",
    },
]

# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI app instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Internal LMS Backend API powered by FastAPI and Supabase.",
        openapi_tags=openapi_tags,
    )

    # CORS: parse comma-separated ALLOWED_ORIGINS from environment
    try:
        origins = [o.strip() for o in (settings.ALLOWED_ORIGINS or "").split(",") if o.strip()]
    except Exception:
        origins = ["http://localhost:3000", "https://localhost:3000"]

    if not origins:
        # sensible defaults for local dev
        origins = ["http://localhost:3000", "https://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(onboarding_router, prefix="/api/onboarding", tags=["Onboarding"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(lessons_router, prefix="/api/lessons", tags=["Lessons"])

    # Exception handlers
    register_exception_handlers(app)

    @app.on_event("startup")
    async def on_startup() -> None:
        """Initialize resources on application startup."""
        init_supabase_client()
        logger.info("Application startup complete")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        """Cleanup resources on application shutdown."""
        await close_supabase_client()
        logger.info("Application shutdown complete")

    @app.get(
        "/",
        summary="Root Health Check",
        description="Simple root endpoint to verify the API is up.",
        response_class=JSONResponse,
    )
    def root_health():
        """Return a basic health response."""
        return {"message": "Healthy"}

    return app


# Create default app for ASGI servers
app = create_app()

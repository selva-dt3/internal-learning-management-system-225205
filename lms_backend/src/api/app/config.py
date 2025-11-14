from functools import lru_cache
from pydantic import Field
# Prefer pydantic-settings (v2) import path. If missing, raise a clear error guiding installation.
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
except ImportError as e:
    raise ImportError(
        "pydantic-settings is required. Please install with 'pip install pydantic-settings>=2.0.3,<3.0' "
        "and ensure Pydantic v2 is installed."
    ) from e


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    APP_NAME: str = Field(default="Internal LMS Backend", description="App name")
    ENV: str = Field(default="development", description="Environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # These remain required by application logic; empty default allows startup,
    # and missing values will degrade Supabase features appropriately.
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase service anon/public key")

    # Comma-separated list of allowed origins for CORS. Example:
    # "http://localhost:3000,https://vscode-internal-XXXX.beta01.cloud.kavia.ai:3000"
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,https://localhost:3000",
        description="Comma-separated list of allowed origins for CORS",
    )

    # pydantic-settings v2 configuration:
    # - env_file: load from .env
    # - case_sensitive: False to accept variables regardless of case
    # - extra: "ignore" to avoid ValidationError on unknown env vars
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()  # type: ignore[call-arg]


# Expose settings singleton
settings = get_settings()

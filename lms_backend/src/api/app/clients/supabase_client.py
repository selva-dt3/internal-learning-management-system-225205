from typing import Optional

from supabase import create_client, Client

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)

_supabase_client: Optional[Client] = None


def init_supabase_client() -> Client | None:
    """Initialize the Supabase client as a module-level singleton.

    Returns:
        Client | None: The initialized Supabase client or None if configuration missing.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY

    if not url or not key:
        logger.warning("Supabase configuration missing: URL or KEY not provided")
        _supabase_client = None
        return None

    _supabase_client = create_client(url, key)
    logger.info("Supabase client initialized")
    return _supabase_client


def get_supabase_client() -> Client | None:
    """Get the initialized Supabase client, or None if not configured."""
    return _supabase_client


async def close_supabase_client() -> None:
    """Close the Supabase client if needed (placeholder for interface symmetry)."""
    # supabase-py currently uses httpx under the hood; explicit close not exposed
    logger.info("Supabase client closed (noop)")

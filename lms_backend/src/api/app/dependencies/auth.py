from typing import Annotated, Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..clients.supabase_client import get_supabase_client
from ..errors import ApplicationError, ErrorCode
from ..logging_config import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


# PUBLIC_INTERFACE
async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> dict:
    """Extract and validate current user from Bearer token using Supabase.

    Raises:
        HTTPException: 401 if credentials are missing or invalid.
    Returns:
        dict: Supabase user object.
    """
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization")

    token = credentials.credentials
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not configured")
        raise ApplicationError("Auth service unavailable", status_code=503, code=ErrorCode.EXTERNAL_SERVICE_ERROR)

    try:
        # supabase.auth.get_user requires access token
        res = supabase.auth.get_user(token)
        user = res.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        # Transform to dict for downstream usage
        user_dict = {
            "id": user.id,
            "email": user.email,
            "app_metadata": user.app_metadata or {},
            "user_metadata": user.user_metadata or {},
        }
        return user_dict
    except Exception:
        logger.warning("Token validation failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# PUBLIC_INTERFACE
def require_roles(*roles: str) -> Callable[[dict], dict]:
    """Dependency factory to enforce that the current user has one of the allowed roles.

    Args:
        *roles (str): Allowed role values ('admin' | 'hr' | 'employee').

    Returns:
        Callable: dependency that returns current user if authorized.

    Raises:
        HTTPException: 403 if user lacks required role.
    """

    async def _dep(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        # Role is stored under user.user_metadata.role per spec
        role = (user.get("user_metadata") or {}).get("role")
        if roles and role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _dep

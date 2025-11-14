from fastapi import APIRouter, Depends, HTTPException, status

from ..clients.supabase_client import get_supabase_client
from ..dependencies.auth import get_current_user, require_roles
from ..errors import ApplicationError, ErrorCode
from ..logging_config import get_logger
from ..models.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/signup",
    summary="Sign up a new user",
    description="Create a new user in Supabase with optional role metadata.",
    response_model=UserOut,
    responses={
        201: {"description": "User created"},
        400: {"description": "Validation error"},
        503: {"description": "Auth service unavailable"},
    },
    status_code=201,
)
# PUBLIC_INTERFACE
def signup(payload: SignupRequest) -> UserOut:
    """Register a user using Supabase Auth.

    Args:
        payload (SignupRequest): Contains email, password, and optional role metadata.

    Returns:
        UserOut: Created user information.

    Raises:
        ApplicationError: If Supabase is not configured.
        HTTPException: On validation/auth errors.
    """
    supabase = get_supabase_client()
    if not supabase:
        raise ApplicationError("Auth service unavailable", status_code=503, code=ErrorCode.EXTERNAL_SERVICE_ERROR)

    try:
        metadata = {"role": payload.role or "employee"}
        res = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
                "options": {"data": metadata},
            }
        )
        user = res.user
        if not user:
            logger.warning("Signup failed: No user returned")
            raise HTTPException(status_code=400, detail="Signup failed")

        logger.info("User signed up")
        return UserOut(
            id=user.id,
            email=user.email or "",
            role=(user.user_metadata or {}).get("role"),
            app_metadata=user.app_metadata or {},
            user_metadata=user.user_metadata or {},
        )
    except Exception:
        logger.warning("Signup failed")
        raise HTTPException(status_code=400, detail="Signup failed")


@router.post(
    "/login",
    summary="Login",
    description="Authenticate with email/password and receive access token.",
    response_model=TokenResponse,
    responses={
        200: {"description": "Authenticated"},
        401: {"description": "Invalid credentials"},
        503: {"description": "Auth service unavailable"},
    },
)
# PUBLIC_INTERFACE
def login(payload: LoginRequest) -> TokenResponse:
    """Login via Supabase using email/password.

    Args:
        payload (LoginRequest): Email/password.

    Returns:
        TokenResponse: Access token and token type.
    """
    supabase = get_supabase_client()
    if not supabase:
        raise ApplicationError("Auth service unavailable", status_code=503, code=ErrorCode.EXTERNAL_SERVICE_ERROR)

    try:
        res = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
        session = res.session
        if not session or not session.access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        logger.info("User login success")
        return TokenResponse(access_token=session.access_token, token_type="bearer")
    except Exception:
        logger.warning("User login failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get(
    "/me",
    summary="Get current user profile",
    description="Return current authenticated user's profile using the access token.",
    response_model=UserOut,
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
# PUBLIC_INTERFACE
async def me(user=Depends(get_current_user), _: dict = Depends(require_roles("admin", "hr", "employee"))) -> UserOut:
    """Return current user's profile.

    The route demonstrates role-based dependency usage; currently any valid role is permitted.

    Returns:
        UserOut: Current user profile.
    """
    return UserOut(
        id=user["id"],
        email=user.get("email", ""),
        role=(user.get("user_metadata") or {}).get("role"),
        app_metadata=user.get("app_metadata") or {},
        user_metadata=user.get("user_metadata") or {},
    )

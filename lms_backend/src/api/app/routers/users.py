from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..clients.supabase_client import get_supabase_client
from ..dependencies.auth import require_roles
from ..logging_config import get_logger
from ..models.lms import ProfileCreate, ProfileOut, ProfileUpdate, ProfilesList

router = APIRouter()
logger = get_logger(__name__)


def _row_to_profile_out(row: dict) -> ProfileOut:
    """Map raw DB row to ProfileOut model."""
    return ProfileOut(
        id=str(row.get("id") or row.get("user_id") or ""),
        email=row.get("email", ""),
        role=row.get("role", ""),
        name=row.get("name"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get(
    "",
    summary="List users",
    description="List users from profiles table. Admin and HR only.",
    response_model=ProfilesList,
    responses={200: {"description": "List returned"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)
# PUBLIC_INTERFACE
async def list_users(
    _: dict = Depends(require_roles("admin", "hr")),
    limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    search: str | None = Query(default=None, description="Filter by email contains"),
) -> ProfilesList:
    """Return a paginated list of users (Admin/HR only)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")

    try:
        query = sb.table("profiles").select("*")
        if search:
            # ilike for case-insensitive search
            query = query.ilike("email", f"%{search}%")
        # Use range for pagination: inclusive indexes
        start = offset
        end = offset + limit - 1
        res = query.range(start, end).order("created_at", desc=True).execute()
        rows = getattr(res, "data", []) or []
        items = [_row_to_profile_out(r) for r in rows]
        return ProfilesList(items=items, count=len(items))
    except Exception:
        logger.exception("Failed to list users")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get(
    "/{user_id}",
    summary="Get user",
    description="Get a single user profile by ID. Admin and HR only.",
    response_model=ProfileOut,
    responses={200: {"description": "User found"}, 404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)
# PUBLIC_INTERFACE
async def get_user(
    user_id: str,
    _: dict = Depends(require_roles("admin", "hr")),
) -> ProfileOut:
    """Get a user profile by ID (Admin/HR)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        res = sb.table("profiles").select("*").eq("id", user_id).limit(1).execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")
        return _row_to_profile_out(rows[0])
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch user")
        raise HTTPException(status_code=500, detail="Failed to fetch user")


@router.post(
    "",
    summary="Create user",
    description="Create a new user profile. Admin only.",
    response_model=ProfileOut,
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Created"}, 400: {"description": "Validation error"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)
# PUBLIC_INTERFACE
async def create_user(
    payload: ProfileCreate,
    _: dict = Depends(require_roles("admin")),
) -> ProfileOut:
    """Create a new user profile (Admin only)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        insert = {
            "email": payload.email,
            "role": payload.role,
            "name": payload.name,
        }
        res = sb.table("profiles").insert(insert).execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            # Attempt select by email to return row
            sel = sb.table("profiles").select("*").eq("email", payload.email).limit(1).execute()
            srows = getattr(sel, "data", []) or []
            if not srows:
                raise HTTPException(status_code=400, detail="Create failed")
            rows = srows
        return _row_to_profile_out(rows[0])
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create user")
        raise HTTPException(status_code=400, detail="Failed to create user")


@router.put(
    "/{user_id}",
    summary="Update user",
    description="Update an existing user profile. Admin and HR only.",
    response_model=ProfileOut,
    responses={200: {"description": "Updated"}, 404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)
# PUBLIC_INTERFACE
async def update_user(
    user_id: str,
    payload: ProfileUpdate,
    _: dict = Depends(require_roles("admin", "hr")),
) -> ProfileOut:
    """Update a user profile (Admin/HR)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            # No-op return current
            res0 = sb.table("profiles").select("*").eq("id", user_id).limit(1).execute()
            rows0 = getattr(res0, "data", []) or []
            if not rows0:
                raise HTTPException(status_code=404, detail="User not found")
            return _row_to_profile_out(rows0[0])
        res = sb.table("profiles").update(update_data).eq("id", user_id).execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            # Fetch after update
            sel = sb.table("profiles").select("*").eq("id", user_id).limit(1).execute()
            srows = getattr(sel, "data", []) or []
            if not srows:
                raise HTTPException(status_code=404, detail="User not found")
            rows = srows
        return _row_to_profile_out(rows[0])
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update user")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete(
    "/{user_id}",
    summary="Delete user",
    description="Delete a user profile by ID. Admin only.",
    responses={204: {"description": "Deleted"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
    status_code=status.HTTP_204_NO_CONTENT,
)
# PUBLIC_INTERFACE
async def delete_user(
    user_id: str,
    _: dict = Depends(require_roles("admin")),
) -> None:
    """Delete a user profile (Admin only)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        # Ensure exists
        sel = sb.table("profiles").select("id").eq("id", user_id).limit(1).execute()
        srows = getattr(sel, "data", []) or []
        if not srows:
            raise HTTPException(status_code=404, detail="User not found")
        _ = sb.table("profiles").delete().eq("id", user_id).execute()
        return None
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete user")
        raise HTTPException(status_code=500, detail="Failed to delete user")

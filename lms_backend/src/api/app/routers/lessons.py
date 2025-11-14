from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..clients.supabase_client import get_supabase_client
from ..dependencies.auth import get_current_user, require_roles
from ..logging_config import get_logger
from ..models.lms import LessonCreate, LessonOut, LessonUpdate, LessonsList

router = APIRouter()
logger = get_logger(__name__)


def _row_to_lesson_out(row: dict) -> LessonOut:
    """Map raw DB row to LessonOut."""
    return LessonOut(
        id=str(row.get("id", "")),
        title=row.get("title", ""),
        description=row.get("description"),
        content=row.get("content"),
        published=bool(row.get("published", False)),
        created_by=row.get("created_by"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.get(
    "",
    summary="List lessons",
    description="List lessons. Employees see only published lessons; Admin/HR see all.",
    response_model=LessonsList,
    responses={200: {"description": "List returned"}, 401: {"description": "Unauthorized"}},
)
# PUBLIC_INTERFACE
async def list_lessons(
    user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    search: str | None = Query(default=None, description="Filter by title contains"),
    published: bool | None = Query(default=None, description="Filter by published status (Admin/HR only)"),
) -> LessonsList:
    """List lessons with role-aware filtering."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")

    role = (user.get("user_metadata") or {}).get("role")
    try:
        query = sb.table("lessons").select("*")
        # Role gating for visibility
        if role not in ("admin", "hr"):
            query = query.eq("published", True)
        else:
            if published is not None:
                query = query.eq("published", published)
        if search:
            query = query.ilike("title", f"%{search}%")
        start = offset
        end = offset + limit - 1
        res = query.range(start, end).order("created_at", desc=True).execute()
        rows = getattr(res, "data", []) or []
        items = [_row_to_lesson_out(r) for r in rows]
        return LessonsList(items=items, count=len(items))
    except Exception:
        logger.exception("Failed to list lessons")
        raise HTTPException(status_code=500, detail="Failed to list lessons")


@router.get(
    "/{lesson_id}",
    summary="Get lesson by ID",
    description="Get lesson. Employees can only access published lessons.",
    response_model=LessonOut,
    responses={200: {"description": "Lesson returned"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
)
# PUBLIC_INTERFACE
async def get_lesson(lesson_id: str, user=Depends(get_current_user)) -> LessonOut:
    """Get a single lesson. Role-aware access."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    role = (user.get("user_metadata") or {}).get("role")
    try:
        res = sb.table("lessons").select("*").eq("id", lesson_id).limit(1).execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            raise HTTPException(status_code=404, detail="Lesson not found")
        row = rows[0]
        if role not in ("admin", "hr") and not bool(row.get("published", False)):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return _row_to_lesson_out(row)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch lesson")
        raise HTTPException(status_code=500, detail="Failed to fetch lesson")


@router.post(
    "",
    summary="Create lesson",
    description="Create a new lesson. Admin and HR only.",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Created"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}},
)
# PUBLIC_INTERFACE
async def create_lesson(payload: LessonCreate, user=Depends(require_roles("admin", "hr"))) -> LessonOut:
    """Create a lesson (Admin/HR)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        insert = {
            "title": payload.title,
            "description": payload.description,
            "content": payload.content,
            "published": payload.published,
            "created_by": user["id"],
        }
        res = sb.table("lessons").insert(insert).execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            # Pull latest by created_by/title as fallback
            sel = (
                sb.table("lessons")
                .select("*")
                .eq("created_by", user["id"])
                .ilike("title", payload.title)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            srows = getattr(sel, "data", []) or []
            if not srows:
                raise HTTPException(status_code=400, detail="Create failed")
            rows = srows
        return _row_to_lesson_out(rows[0])
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create lesson")
        raise HTTPException(status_code=400, detail="Failed to create lesson")


@router.put(
    "/{lesson_id}",
    summary="Update lesson",
    description="Update an existing lesson. Admin and HR only.",
    response_model=LessonOut,
    responses={200: {"description": "Updated"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
)
# PUBLIC_INTERFACE
async def update_lesson(lesson_id: str, payload: LessonUpdate, _: dict = Depends(require_roles("admin", "hr"))) -> LessonOut:
    """Update a lesson (Admin/HR)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            # return current
            sel = sb.table("lessons").select("*").eq("id", lesson_id).limit(1).execute()
            srows = getattr(sel, "data", []) or []
            if not srows:
                raise HTTPException(status_code=404, detail="Lesson not found")
            return _row_to_lesson_out(srows[0])
        upd = sb.table("lessons").update(update_data).eq("id", lesson_id).execute()
        rows = getattr(upd, "data", []) or []
        if not rows:
            sel = sb.table("lessons").select("*").eq("id", lesson_id).limit(1).execute()
            srows = getattr(sel, "data", []) or []
            if not srows:
                raise HTTPException(status_code=404, detail="Lesson not found")
            rows = srows
        return _row_to_lesson_out(rows[0])
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update lesson")
        raise HTTPException(status_code=500, detail="Failed to update lesson")


@router.delete(
    "/{lesson_id}",
    summary="Delete lesson",
    description="Delete a lesson by ID. Admin and HR only.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "Deleted"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
)
# PUBLIC_INTERFACE
async def delete_lesson(lesson_id: str, _: dict = Depends(require_roles("admin", "hr"))) -> None:
    """Delete a lesson (Admin/HR)."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")
    try:
        sel = sb.table("lessons").select("id").eq("id", lesson_id).limit(1).execute()
        srows = getattr(sel, "data", []) or []
        if not srows:
            raise HTTPException(status_code=404, detail="Lesson not found")
        _ = sb.table("lessons").delete().eq("id", lesson_id).execute()
        return None
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete lesson")
        raise HTTPException(status_code=500, detail="Failed to delete lesson")

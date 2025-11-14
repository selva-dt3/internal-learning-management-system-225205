from fastapi import APIRouter, Depends, HTTPException
from ..clients.supabase_client import get_supabase_client
from ..dependencies.auth import require_roles
from ..logging_config import get_logger
from ..models.onboarding import AnalyticsSummary

router = APIRouter()
logger = get_logger(__name__)


def _count_roles_via_profiles(sb) -> dict:
    """Attempt to count users by role using a 'profiles' table with 'role' column."""
    try:
        res = sb.table("profiles").select("role").execute()
        rows = getattr(res, "data", []) or []
        total = len(rows)
        counts = {"admin": 0, "hr": 0, "employee": 0}
        for r in rows:
            role = (r or {}).get("role")
            if role in counts:
                counts[role] += 1
        return {"total": total, **counts}
    except Exception:
        return {}


def _lessons_completed_sum(sb) -> int:
    """Sum 'lessons_completed' from a 'user_progress' table if exists, else 0."""
    try:
        res = sb.table("user_progress").select("lessons_completed").execute()
        rows = getattr(res, "data", []) or []
        s = 0
        for r in rows:
            try:
                s += int(r.get("lessons_completed") or 0)
            except Exception:
                continue
        return s
    except Exception:
        return 0


def _quiz_pass_rate(sb) -> float:
    """Compute pass rate from 'quiz_results' table with boolean 'passed'."""
    try:
        res = sb.table("quiz_results").select("passed").execute()
        rows = getattr(res, "data", []) or []
        if not rows:
            return 0.0
        total = len(rows)
        passed = sum(1 for r in rows if bool(r.get("passed")))
        return round(100.0 * passed / total, 2)
    except Exception:
        return 0.0


@router.get(
    "/summary",
    summary="Analytics summary",
    description="Basic LMS analytics for Admin/HR: users by role, lessons completed, quiz pass rate.",
    response_model=AnalyticsSummary,
    responses={
        200: {"description": "Summary returned"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        503: {"description": "Service unavailable"},
    },
)
# PUBLIC_INTERFACE
async def analytics_summary(_: dict = Depends(require_roles("admin", "hr"))) -> AnalyticsSummary:
    """Return basic analytics restricted to Admin and HR roles."""
    sb = get_supabase_client()
    if not sb:
        raise HTTPException(status_code=503, detail="Service unavailable")

    # Attempt to use 'profiles' table for user role counts
    counts = _count_roles_via_profiles(sb)
    total_users = counts.get("total", 0)
    total_admins = counts.get("admin", 0)
    total_hr = counts.get("hr", 0)
    total_employees = counts.get("employee", 0)

    lessons_completed = _lessons_completed_sum(sb)
    quiz_pass_rate = _quiz_pass_rate(sb)

    return AnalyticsSummary(
        total_users=total_users,
        total_admins=total_admins,
        total_hr=total_hr,
        total_employees=total_employees,
        lessons_completed=lessons_completed,
        quiz_pass_rate=quiz_pass_rate,
    )

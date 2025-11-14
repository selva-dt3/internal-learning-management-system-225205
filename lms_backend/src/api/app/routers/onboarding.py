from fastapi import APIRouter, Depends, HTTPException
from ..clients.supabase_client import get_supabase_client
from ..dependencies.auth import get_current_user
from ..logging_config import get_logger
from ..models.onboarding import OnboardingStatus, AcknowledgementRequest

router = APIRouter()
logger = get_logger(__name__)


def _ensure_onboarding_row(supabase, user_id: str) -> dict:
    """Ensure an onboarding row exists for the given user_id, return the row."""
    # Try select
    res = supabase.table("onboarding").select("*").eq("user_id", user_id).limit(1).execute()
    data = getattr(res, "data", []) or []
    if data:
        return data[0]
    # Insert if missing
    insert_res = supabase.table("onboarding").insert(
        {"user_id": user_id, "nda_acknowledged": False, "coc_acknowledged": False}
    ).execute()
    ins_data = getattr(insert_res, "data", []) or []
    if not ins_data:
        # fetch again
        res2 = supabase.table("onboarding").select("*").eq("user_id", user_id).limit(1).execute()
        data2 = getattr(res2, "data", []) or []
        if not data2:
            raise HTTPException(status_code=500, detail="Failed to initialize onboarding row")
        return data2[0]
    return ins_data[0]


@router.get(
    "/status",
    summary="Get current user's onboarding status",
    description="Returns whether the current user acknowledged NDA and Code of Conduct.",
    response_model=OnboardingStatus,
    responses={
        200: {"description": "Status returned"},
        401: {"description": "Unauthorized"},
    },
)
# PUBLIC_INTERFACE
async def get_status(user=Depends(get_current_user)) -> OnboardingStatus:
    """Fetch onboarding status for the current authenticated user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Service unavailable")

    user_id = user["id"]
    row = _ensure_onboarding_row(supabase, user_id)
    return OnboardingStatus(
        user_id=user_id,
        nda_acknowledged=bool(row.get("nda_acknowledged", False)),
        coc_acknowledged=bool(row.get("coc_acknowledged", False)),
    )


@router.post(
    "/acknowledgements",
    summary="Acknowledge NDA or Code of Conduct",
    description="Marks an onboarding acknowledgement for the current user.",
    response_model=OnboardingStatus,
    responses={
        200: {"description": "Acknowledged"},
        400: {"description": "Invalid document"},
        401: {"description": "Unauthorized"},
    },
)
# PUBLIC_INTERFACE
async def post_acknowledgement(payload: AcknowledgementRequest, user=Depends(get_current_user)) -> OnboardingStatus:
    """Acknowledge NDA or CoC for the current user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Service unavailable")

    user_id = user["id"]
    _ = _ensure_onboarding_row(supabase, user_id)

    field_name = "nda_acknowledged" if payload.document == "nda" else "coc_acknowledged"
    try:
        upd = supabase.table("onboarding").update({field_name: True}).eq("user_id", user_id).execute()
        data = getattr(upd, "data", []) or []
        if data:
            row = data[0]
        else:
            # Select after update
            res = supabase.table("onboarding").select("*").eq("user_id", user_id).limit(1).execute()
            d2 = getattr(res, "data", []) or []
            if not d2:
                raise HTTPException(status_code=500, detail="Failed to update onboarding")
            row = d2[0]
        return OnboardingStatus(
            user_id=user_id,
            nda_acknowledged=bool(row.get("nda_acknowledged", False)),
            coc_acknowledged=bool(row.get("coc_acknowledged", False)),
        )
    except Exception:
        logger.exception("Failed to update acknowledgement")
        raise HTTPException(status_code=500, detail="Failed to save acknowledgement")

from typing import Literal
from pydantic import BaseModel, Field


class OnboardingStatus(BaseModel):
    """Represents onboarding status for a user."""
    user_id: str = Field(..., description="Supabase user ID")
    nda_acknowledged: bool = Field(..., description="Whether NDA has been acknowledged")
    coc_acknowledged: bool = Field(..., description="Whether Code of Conduct has been acknowledged")


class AcknowledgementRequest(BaseModel):
    """Payload to acknowledge a policy document."""
    document: Literal["nda", "coc"] = Field(..., description="Document to acknowledge: 'nda' or 'coc'")


class AnalyticsSummary(BaseModel):
    """Basic analytics metrics for admin/hr dashboards."""
    total_users: int = Field(..., description="Total number of registered users")
    total_admins: int = Field(..., description="Number of users with admin role")
    total_hr: int = Field(..., description="Number of users with hr role")
    total_employees: int = Field(..., description="Number of users with employee role")
    lessons_completed: int = Field(..., description="Total lessons completed (sum)")
    quiz_pass_rate: float = Field(..., description="Quiz pass rate as a percentage (0-100)")

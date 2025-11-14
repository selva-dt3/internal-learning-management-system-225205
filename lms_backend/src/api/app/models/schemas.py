from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Payload for signup API endpoint."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    role: Optional[str] = Field(
        default="employee",
        description="User role metadata ('admin' | 'hr' | 'employee'), default 'employee'",
    )


class LoginRequest(BaseModel):
    """Payload for login API endpoint."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")


class TokenResponse(BaseModel):
    """Response containing access token and token type."""

    access_token: str = Field(..., description="Bearer token")
    token_type: str = Field(default="bearer", description="Token type")


class UserOut(BaseModel):
    """User shape returned from /me endpoint."""

    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email")
    role: Optional[str] = Field(default=None, description="Role from user metadata")
    app_metadata: dict[str, Any] = Field(default_factory=dict, description="App metadata")
    user_metadata: dict[str, Any] = Field(default_factory=dict, description="User metadata")

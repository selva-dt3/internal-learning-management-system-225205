from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class ProfileBase(BaseModel):
    """Base fields shared by profile input models."""
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="Role of the user: 'admin' | 'hr' | 'employee'")
    name: Optional[str] = Field(default=None, description="Full name of the user")


class ProfileCreate(ProfileBase):
    """Payload to create a new profile/user."""
    pass


class ProfileUpdate(BaseModel):
    """Payload to update a user/profile."""
    email: Optional[EmailStr] = Field(default=None, description="Email address")
    role: Optional[str] = Field(default=None, description="Role of the user: 'admin' | 'hr' | 'employee'")
    name: Optional[str] = Field(default=None, description="Full name of the user")


class ProfileOut(BaseModel):
    """Response model for a user profile."""
    id: str = Field(..., description="Profile ID (UUID)")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(..., description="Role of the user")
    name: Optional[str] = Field(default=None, description="User full name")
    created_at: Optional[str] = Field(default=None, description="Created timestamp")
    updated_at: Optional[str] = Field(default=None, description="Updated timestamp")


class ProfilesList(BaseModel):
    """List of user profiles with count."""
    items: List[ProfileOut] = Field(..., description="List of profiles")
    count: int = Field(..., description="Total number of profiles returned")


class LessonBase(BaseModel):
    """Base fields for lessons."""
    title: str = Field(..., description="Lesson title")
    description: Optional[str] = Field(default=None, description="Short description")
    content: Optional[str] = Field(default=None, description="Lesson content (markdown/HTML)")
    published: bool = Field(default=False, description="Publication status")


class LessonCreate(LessonBase):
    """Payload for lesson creation."""
    pass


class LessonUpdate(BaseModel):
    """Payload for lesson update."""
    title: Optional[str] = Field(default=None, description="Lesson title")
    description: Optional[str] = Field(default=None, description="Short description")
    content: Optional[str] = Field(default=None, description="Lesson content")
    published: Optional[bool] = Field(default=None, description="Publication status")


class LessonOut(LessonBase):
    """Response model for a lesson."""
    id: str = Field(..., description="Lesson ID (UUID)")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")
    created_at: Optional[str] = Field(default=None, description="Created timestamp")
    updated_at: Optional[str] = Field(default=None, description="Updated timestamp")


class LessonsList(BaseModel):
    """List response for lessons."""
    items: List[LessonOut] = Field(..., description="List of lessons")
    count: int = Field(..., description="Total number of lessons returned")

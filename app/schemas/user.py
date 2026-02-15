"""Pydantic schemas for user-related operations."""
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from app.core.security import hash_pin


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=256)
    pin: Annotated[str, Field(min_length=4, max_length=6)]
    email: Optional[str] = None
    phone_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: int
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    pin: str
    
    class Config:
        from_attributes = True

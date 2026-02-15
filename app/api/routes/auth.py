"""User authentication routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.engine import Result

from app.core.database import get_db
from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="User login",
    description="Authenticate user with username and PIN"
)
async def login(username: str, pin: str, db: DBSession):
    """
    Authenticate a user.
    
    - **username**: User's username
    - **pin**: User's PIN
    
    Returns user details on successful authentication.
    """
    query = select(User).where(User.username == username)
    result: Result = await db.execute(query)
    user = result.scalars().first()
    
    if user and verify_password(pin, user.pin):
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone_number=user.phone_number,
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or PIN"
    )


@router.get(
    "/user/{username}",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Check username",
    description="Check if a username exists and get user details"
)
async def check_username(username: str, db: DBSession):
    """
    Check if a username exists.
    
    - **username**: Username to check
    
    Returns user details if found.
    """
    query = select(User).where(User.username == username)
    result: Result = await db.execute(query)
    user = result.scalars().first()
    
    if user:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone_number=user.phone_number,
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

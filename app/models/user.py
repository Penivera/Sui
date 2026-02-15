"""User model for authentication and profile management."""
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.wallet import Wallet


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class User(Base):
    """User model for storing user credentials and profile information."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    pin: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Relationships
    wallets: Mapped[list["Wallet"]] = relationship("Wallet", back_populates="user", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"

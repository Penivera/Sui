"""Wallet model for managing user cryptocurrency wallets."""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class Wallet(Base):
    """Wallet model for storing SUI wallet information."""
    
    __tablename__ = "wallets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    wallet_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="Main Wallet")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    encrypted_private_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallets")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="wallet", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, address={self.address[:16]}...)>"

"""Transaction model for tracking all wallet transactions."""
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.wallet import Wallet


class TransactionType(str, enum.Enum):
    """Enumeration of transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    OFFRAMP = "offramp"
    BILL_PAYMENT = "bill_payment"
    AIRTIME = "airtime"


class TransactionStatus(str, enum.Enum):
    """Enumeration of transaction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    """Transaction model for recording all wallet activity."""
    
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), nullable=False)
    transaction_hash: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    amount: Mapped[str] = mapped_column(Numeric(precision=36, scale=18), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="SUI")
    recipient_address: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # JSON string for extra data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.transaction_type}, status={self.status})>"

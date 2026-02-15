"""Pydantic schemas for transaction-related operations."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransactionTypeEnum(str, Enum):
    """Enumeration of transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    OFFRAMP = "offramp"
    BILL_PAYMENT = "bill_payment"
    AIRTIME = "airtime"


class TransactionStatusEnum(str, Enum):
    """Enumeration of transaction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    wallet_id: int
    transaction_type: TransactionTypeEnum
    amount: str = Field(..., description="Transaction amount")
    recipient_address: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    wallet_id: int
    transaction_hash: Optional[str]
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum
    amount: str
    currency: str
    recipient_address: Optional[str]
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for listing multiple transactions."""
    transactions: List[TransactionResponse]
    total_count: int
    page: int
    per_page: int
    
    class Config:
        from_attributes = True


class OfframpRequest(BaseModel):
    """Schema for offramp request."""
    wallet_id: int
    amount: str = Field(..., description="Amount to offramp in SUI")
    bank_account: Optional[str] = Field(None, description="Bank account for fiat transfer")
    phone_number: Optional[str] = Field(None, description="Phone number for mobile money")
    
    class Config:
        from_attributes = True


class OfframpResponse(BaseModel):
    """Schema for offramp response."""
    transaction_id: int
    status: TransactionStatusEnum
    amount: str
    estimated_fiat: Optional[str]
    message: str
    
    class Config:
        from_attributes = True

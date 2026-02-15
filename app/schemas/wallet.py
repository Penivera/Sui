"""Pydantic schemas for wallet-related operations."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WalletCreate(BaseModel):
    """Schema for creating a new wallet."""
    wallet_name: Optional[str] = Field(default="Main Wallet", max_length=100)
    is_primary: bool = False
    
    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    """Schema for wallet response."""
    id: int
    address: str
    wallet_name: Optional[str]
    is_primary: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletCreateResponse(BaseModel):
    """Schema for newly created wallet response including sensitive data."""
    wallet: str  # address
    mnemonics: str
    private_key: str
    wallet_id: int
    
    class Config:
        from_attributes = True


class WalletBalance(BaseModel):
    """Schema for wallet balance response."""
    address: str
    balance: str
    currency: str = "SUI"
    
    class Config:
        from_attributes = True


class WalletRecoveryRequest(BaseModel):
    """Schema for wallet recovery using mnemonics."""
    mnemonics: str = Field(..., description="12-word mnemonic phrase")
    wallet_name: Optional[str] = "Recovered Wallet"


class WalletListResponse(BaseModel):
    """Schema for listing multiple wallets."""
    wallets: List[WalletResponse]
    total_count: int
    
    class Config:
        from_attributes = True

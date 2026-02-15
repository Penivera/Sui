"""Wallet API routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.wallet import (
    WalletCreate, WalletResponse, WalletCreateResponse, 
    WalletBalance, WalletListResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.services.wallet_service import wallet_service

router = APIRouter(prefix="/wallet", tags=["Wallet Management"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=WalletCreateResponse,
    summary="Create a new user with wallet",
    description="Creates a new user account and generates a SUI wallet"
)
async def create_wallet(
    username: str,
    pin: str,
    db: DBSession,
    email: str = None,
    phone_number: str = None,
    wallet_name: str = "Main Wallet"
):
    """
    Create a new user with a SUI wallet.
    
    - **username**: Unique username for the account
    - **pin**: 4-6 digit PIN for authentication
    - **email**: Optional email address
    - **phone_number**: Optional phone number
    - **wallet_name**: Name for the wallet (default: "Main Wallet")
    
    Returns the wallet address, mnemonics (save securely!), and private key.
    """
    try:
        result = await wallet_service.create_user_with_wallet(
            db=db,
            username=username,
            pin=pin,
            email=email,
            phone_number=phone_number,
            wallet_name=wallet_name
        )
        return WalletCreateResponse(
            wallet=result["wallet"],
            mnemonics=result["mnemonics"],
            private_key=result["private_key"],
            wallet_id=result["wallet_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post(
    "/add/{user_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=WalletCreateResponse,
    summary="Add wallet to existing user",
    description="Creates an additional wallet for an existing user"
)
async def add_wallet(
    user_id: int,
    db: DBSession,
    wallet_name: str = "Secondary Wallet"
):
    """
    Add a new wallet to an existing user.
    
    - **user_id**: ID of the user
    - **wallet_name**: Name for the new wallet
    
    Returns the new wallet details including mnemonics.
    """
    try:
        result = await wallet_service.add_wallet_to_user(
            db=db,
            user_id=user_id,
            wallet_name=wallet_name
        )
        return WalletCreateResponse(
            wallet=result["wallet"],
            mnemonics=result["mnemonics"],
            private_key=result["private_key"],
            wallet_id=result["wallet_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get(
    "/balance/{address}",
    status_code=status.HTTP_200_OK,
    response_model=WalletBalance,
    summary="Get wallet balance",
    description="Retrieves the SUI balance for a wallet address"
)
async def get_balance(address: str):
    """
    Get the balance of a SUI wallet.
    
    - **address**: SUI wallet address
    
    Returns the balance in MIST (1 SUI = 1e9 MIST).
    """
    try:
        result = await wallet_service.get_wallet_balance(address)
        return WalletBalance(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/list/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=WalletListResponse,
    summary="List user wallets",
    description="Get all wallets for a user"
)
async def list_wallets(user_id: int, db: DBSession):
    """
    Get all wallets for a user.
    
    - **user_id**: ID of the user
    
    Returns a list of all active wallets.
    """
    try:
        wallets = await wallet_service.get_user_wallets(db=db, user_id=user_id)
        return WalletListResponse(
            wallets=[
                WalletResponse(
                    id=w.id,
                    address=w.address,
                    wallet_name=w.wallet_name,
                    is_primary=w.is_primary,
                    is_active=w.is_active,
                    created_at=w.created_at
                )
                for w in wallets
            ],
            total_count=len(wallets)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{wallet_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a wallet",
    description="Soft delete a wallet (primary wallet cannot be deactivated)"
)
async def deactivate_wallet(wallet_id: int, user_id: int, db: DBSession):
    """
    Deactivate a wallet (soft delete).
    
    - **wallet_id**: ID of the wallet to deactivate
    - **user_id**: ID of the wallet owner
    
    Note: Primary wallet cannot be deactivated.
    """
    try:
        await wallet_service.deactivate_wallet(db=db, wallet_id=wallet_id, user_id=user_id)
        return {"message": "Wallet deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{wallet_id}/set-primary",
    status_code=status.HTTP_200_OK,
    summary="Set primary wallet",
    description="Set a wallet as the primary wallet for a user"
)
async def set_primary_wallet(wallet_id: int, user_id: int, db: DBSession):
    """
    Set a wallet as the primary wallet.
    
    - **wallet_id**: ID of the wallet to set as primary
    - **user_id**: ID of the wallet owner
    """
    try:
        await wallet_service.set_primary_wallet(db=db, wallet_id=wallet_id, user_id=user_id)
        return {"message": "Primary wallet updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

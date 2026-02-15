"""Offramp API routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.transaction import OfframpRequest, OfframpResponse, TransactionListResponse
from app.services.offramp_service import offramp_service

router = APIRouter(prefix="/offramp", tags=["Offramp"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/initiate",
    status_code=status.HTTP_201_CREATED,
    response_model=OfframpResponse,
    summary="Initiate offramp",
    description="Convert SUI to fiat currency"
)
async def initiate_offramp(request: OfframpRequest, db: DBSession):
    """
    Initiate an offramp transaction.
    
    - **wallet_id**: Source wallet ID
    - **amount**: Amount of SUI to convert
    - **bank_account**: Bank account for fiat transfer (optional)
    - **phone_number**: Phone number for mobile money (optional)
    
    Returns transaction details and estimated fiat amount.
    """
    try:
        result = await offramp_service.initiate_offramp(
            db=db,
            wallet_id=request.wallet_id,
            amount=request.amount,
            bank_account=request.bank_account,
            phone_number=request.phone_number
        )
        return OfframpResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/process/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Process offramp",
    description="Process a pending offramp transaction"
)
async def process_offramp(transaction_id: int, db: DBSession):
    """
    Process a pending offramp transaction.
    
    - **transaction_id**: ID of the transaction to process
    """
    try:
        result = await offramp_service.process_offramp(db=db, transaction_id=transaction_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/complete/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Complete offramp",
    description="Mark an offramp transaction as completed"
)
async def complete_offramp(transaction_id: int, transaction_hash: str, db: DBSession):
    """
    Mark an offramp transaction as completed.
    
    - **transaction_id**: ID of the transaction
    - **transaction_hash**: Blockchain transaction hash
    """
    try:
        result = await offramp_service.complete_offramp(
            db=db,
            transaction_id=transaction_id,
            transaction_hash=transaction_hash
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/cancel/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel offramp",
    description="Cancel a pending offramp transaction"
)
async def cancel_offramp(transaction_id: int, db: DBSession, reason: str = None):
    """
    Cancel a pending offramp transaction.
    
    - **transaction_id**: ID of the transaction to cancel
    - **reason**: Optional cancellation reason
    """
    try:
        result = await offramp_service.cancel_offramp(
            db=db,
            transaction_id=transaction_id,
            reason=reason
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/history/{wallet_id}",
    status_code=status.HTTP_200_OK,
    summary="Get offramp history",
    description="Get offramp transaction history for a wallet"
)
async def get_offramp_history(
    wallet_id: int,
    db: DBSession,
    page: int = 1,
    per_page: int = 10
):
    """
    Get offramp transaction history.
    
    - **wallet_id**: ID of the wallet
    - **page**: Page number for pagination
    - **per_page**: Number of items per page
    """
    try:
        result = await offramp_service.get_offramp_history(
            db=db,
            wallet_id=wallet_id,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

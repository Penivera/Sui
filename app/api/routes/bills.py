"""Bill payment API routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.bill_service import bill_service

router = APIRouter(prefix="/bills", tags=["Bills & Airtime"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/airtime",
    status_code=status.HTTP_200_OK,
    summary="Buy airtime",
    description="Purchase airtime for a phone number"
)
async def buy_airtime(phone_number: str, amount: str, network: str):
    """
    Purchase airtime (simple API without wallet).
    
    - **phone_number**: Phone number to credit
    - **amount**: Amount of airtime
    - **network**: Mobile network (MTN, Glo, etc.)
    """
    try:
        result = await bill_service.buy_airtime_simple(
            phone_number=phone_number,
            amount=amount,
            network=network
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/airtime/wallet",
    status_code=status.HTTP_200_OK,
    summary="Buy airtime with wallet",
    description="Purchase airtime using wallet balance"
)
async def buy_airtime_with_wallet(
    wallet_id: int,
    phone_number: str,
    amount: str,
    network: str,
    db: DBSession
):
    """
    Purchase airtime using wallet balance.
    
    - **wallet_id**: ID of the wallet to debit
    - **phone_number**: Phone number to credit
    - **amount**: Amount of airtime
    - **network**: Mobile network
    """
    try:
        result = await bill_service.buy_airtime(
            db=db,
            wallet_id=wallet_id,
            phone_number=phone_number,
            amount=amount,
            network=network
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/data",
    status_code=status.HTTP_200_OK,
    summary="Buy data bundle",
    description="Purchase data bundle for a phone number"
)
async def buy_data(
    wallet_id: int,
    phone_number: str,
    network: str,
    product_code: str,
    db: DBSession
):
    """
    Purchase data bundle.
    
    - **wallet_id**: ID of the wallet to debit
    - **phone_number**: Phone number to credit
    - **network**: Mobile network (MTN, Glo)
    - **product_code**: Data plan product code
    """
    try:
        result = await bill_service.purchase_data(
            db=db,
            wallet_id=wallet_id,
            phone_number=phone_number,
            network=network,
            product_code=product_code
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/data-plans",
    status_code=status.HTTP_200_OK,
    summary="Get data plans",
    description="Get available data plans for all networks"
)
async def get_data_plans():
    """
    Get available data plans.
    
    Returns all data plans organized by network.
    """
    return bill_service.get_data_plans()


@router.post(
    "/callback",
    status_code=status.HTTP_200_OK,
    summary="Bill callback",
    description="Callback endpoint for bill provider"
)
async def callback(data: dict):
    """
    Callback endpoint for bill provider.
    
    - **data**: Callback data from provider
    """
    try:
        result = await bill_service.save_callback_data(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/payment-result",
    status_code=status.HTTP_200_OK,
    summary="Get payment result",
    description="Get the latest payment result"
)
async def get_payment_result():
    """
    Get the latest payment result from callback data.
    """
    try:
        result = await bill_service.get_payment_result()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/history/{wallet_id}",
    status_code=status.HTTP_200_OK,
    summary="Get bill history",
    description="Get bill payment history for a wallet"
)
async def get_bill_history(
    wallet_id: int,
    db: DBSession,
    page: int = 1,
    per_page: int = 10
):
    """
    Get bill payment history.
    
    - **wallet_id**: ID of the wallet
    - **page**: Page number for pagination
    - **per_page**: Number of items per page
    """
    try:
        result = await bill_service.get_bill_history(
            db=db,
            wallet_id=wallet_id,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

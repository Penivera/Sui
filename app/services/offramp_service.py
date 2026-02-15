"""Offramp service for handling crypto to fiat conversions."""
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.engine import Result
from sqlalchemy import func
from datetime import datetime, timezone

from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.services.wallet_service import wallet_service
from app.core.config import settings


class OfframpService:
    """Service class for offramp (crypto to fiat) operations."""
    
    def __init__(self):
        """Initialize the offramp service."""
        self.api_key = settings.OFFRAMP_API_KEY
    
    async def initiate_offramp(
        self,
        db: AsyncSession,
        wallet_id: int,
        amount: str,
        bank_account: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> dict:
        """
        Initiate an offramp transaction to convert SUI to fiat.
        
        Args:
            db: Database session
            wallet_id: ID of the source wallet
            amount: Amount of SUI to convert
            bank_account: Bank account for fiat transfer
            phone_number: Phone number for mobile money
            
        Returns:
            Dictionary containing transaction details
        """
        # Verify wallet exists
        query = select(Wallet).where(Wallet.id == wallet_id, Wallet.is_active == True)
        result: Result = await db.execute(query)
        wallet = result.scalars().first()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        # Check wallet balance
        balance_info = await wallet_service.get_wallet_balance(wallet.address)
        current_balance = int(balance_info["balance"])
        requested_amount = int(float(amount) * 1e9)  # Convert SUI to MIST
        
        if current_balance < requested_amount:
            raise ValueError(f"Insufficient balance. Current: {current_balance}, Requested: {requested_amount}")
        
        # Create transaction record
        metadata = {
            "bank_account": bank_account,
            "phone_number": phone_number,
            "exchange_rate": "0.5",  # Placeholder - should be fetched from exchange
            "estimated_fiat": str(float(amount) * 0.5)  # Placeholder calculation
        }
        
        transaction = Transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.OFFRAMP,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency="SUI",
            description=f"Offramp {amount} SUI to fiat",
            extra_data=json.dumps(metadata)
        )
        
        try:
            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating transaction: {str(e)}")
        
        # In a real implementation, this would interact with a liquidity provider
        # For now, we'll return the pending transaction
        return {
            "transaction_id": transaction.id,
            "status": transaction.status.value,
            "amount": amount,
            "estimated_fiat": metadata["estimated_fiat"],
            "message": "Offramp request submitted. Processing will begin shortly."
        }
    
    async def process_offramp(
        self,
        db: AsyncSession,
        transaction_id: int
    ) -> dict:
        """
        Process a pending offramp transaction.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction to process
            
        Returns:
            Dictionary containing updated transaction status
        """
        query = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.transaction_type == TransactionType.OFFRAMP
        )
        result: Result = await db.execute(query)
        transaction = result.scalars().first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError(f"Transaction cannot be processed. Current status: {transaction.status}")
        
        # Update status to processing
        transaction.status = TransactionStatus.PROCESSING
        await db.commit()
        
        # In a real implementation, this would:
        # 1. Execute the SUI transfer to a liquidity pool
        # 2. Wait for confirmation
        # 3. Initiate fiat transfer
        # 4. Update status to completed
        
        return {
            "transaction_id": transaction.id,
            "status": transaction.status.value,
            "message": "Transaction is being processed"
        }
    
    async def complete_offramp(
        self,
        db: AsyncSession,
        transaction_id: int,
        transaction_hash: str
    ) -> dict:
        """
        Mark an offramp transaction as completed.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction
            transaction_hash: Blockchain transaction hash
            
        Returns:
            Dictionary containing completion details
        """
        query = select(Transaction).where(Transaction.id == transaction_id)
        result: Result = await db.execute(query)
        transaction = result.scalars().first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        transaction.status = TransactionStatus.COMPLETED
        transaction.transaction_hash = transaction_hash
        transaction.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {
            "transaction_id": transaction.id,
            "status": transaction.status.value,
            "transaction_hash": transaction_hash,
            "message": "Offramp completed successfully"
        }
    
    async def cancel_offramp(
        self,
        db: AsyncSession,
        transaction_id: int,
        reason: Optional[str] = None
    ) -> dict:
        """
        Cancel a pending offramp transaction.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction to cancel
            reason: Optional cancellation reason
            
        Returns:
            Dictionary containing cancellation details
        """
        query = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.transaction_type == TransactionType.OFFRAMP
        )
        result: Result = await db.execute(query)
        transaction = result.scalars().first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status not in [TransactionStatus.PENDING]:
            raise ValueError(f"Cannot cancel transaction with status: {transaction.status}")
        
        transaction.status = TransactionStatus.CANCELLED
        if reason:
            current_metadata = json.loads(transaction.extra_data) if transaction.extra_data else {}
            current_metadata["cancellation_reason"] = reason
            transaction.extra_data = json.dumps(current_metadata)
        
        await db.commit()
        
        return {
            "transaction_id": transaction.id,
            "status": transaction.status.value,
            "message": f"Transaction cancelled. Reason: {reason or 'Not specified'}"
        }
    
    async def get_offramp_history(
        self,
        db: AsyncSession,
        wallet_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> dict:
        """
        Get offramp transaction history for a wallet.
        
        Args:
            db: Database session
            wallet_id: ID of the wallet
            page: Page number for pagination
            per_page: Number of items per page
            
        Returns:
            Dictionary containing paginated transaction list
        """
        offset = (page - 1) * per_page
        
        query = select(Transaction).where(
            Transaction.wallet_id == wallet_id,
            Transaction.transaction_type == TransactionType.OFFRAMP
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(per_page)
        
        result: Result = await db.execute(query)
        transactions = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Transaction.id)).where(
            Transaction.wallet_id == wallet_id,
            Transaction.transaction_type == TransactionType.OFFRAMP
        )
        count_result: Result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "amount": str(t.amount),
                    "status": t.status.value,
                    "transaction_hash": t.transaction_hash,
                    "created_at": t.created_at.isoformat(),
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None
                }
                for t in transactions
            ],
            "total_count": total_count,
            "page": page,
            "per_page": per_page
        }


# Singleton instance
offramp_service = OfframpService()

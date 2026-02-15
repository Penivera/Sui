"""Bill payment service for handling utility bills and airtime purchases."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.engine import Result
import requests
import json
import aiofiles
import os
from datetime import datetime

from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.core.config import settings


class BillService:
    """Service class for bill payment operations."""
    
    def __init__(self):
        """Initialize the bill service."""
        self.api_key = settings.API_KEY
        self.bill_url = settings.BILL_URL
        self.base_dir = os.path.join(os.getcwd())
        
        # Mobile network data plans
        self.data_plans = {
            "MOBILE_NETWORK": {
                "MTN": [
                    {
                        "ID": "01",
                        "PRODUCT": [
                            {"PRODUCT_CODE": "2", "PRODUCT_ID": "500.0", "PRODUCT_NAME": "500 MB - 30 days (SME)", "PRODUCT_AMOUNT": "337"},
                            {"PRODUCT_CODE": "4", "PRODUCT_ID": "1000.0", "PRODUCT_NAME": "1 GB - 30 days (SME)", "PRODUCT_AMOUNT": "673"},
                            {"PRODUCT_CODE": "5", "PRODUCT_ID": "2000.0", "PRODUCT_NAME": "2 GB - 30 days (SME)", "PRODUCT_AMOUNT": "1346"}
                        ]
                    }
                ],
                "Glo": [
                    {
                        "ID": "02",
                        "PRODUCT": [
                            {"PRODUCT_CODE": "1", "PRODUCT_ID": "200", "PRODUCT_NAME": "200 MB - 14 days (SME)", "PRODUCT_AMOUNT": "92"},
                            {"PRODUCT_CODE": "2", "PRODUCT_ID": "500", "PRODUCT_NAME": "500 MB - 30 days (SME)", "PRODUCT_AMOUNT": "225"}
                        ]
                    }
                ]
            }
        }
    
    async def buy_airtime(
        self,
        db: AsyncSession,
        wallet_id: int,
        phone_number: str,
        amount: str,
        network: str
    ) -> dict:
        """
        Purchase airtime for a phone number.
        
        Args:
            db: Database session
            wallet_id: ID of the wallet to debit
            phone_number: Phone number to credit
            amount: Amount of airtime to purchase
            network: Mobile network (MTN, Glo, etc.)
            
        Returns:
            Dictionary containing purchase result
        """
        # Verify wallet exists
        query = select(Wallet).where(Wallet.id == wallet_id, Wallet.is_active == True)
        result: Result = await db.execute(query)
        wallet = result.scalars().first()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.AIRTIME,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency="NGN",  # Assuming Nigerian Naira for airtime
            recipient_address=phone_number,
            description=f"Airtime purchase - {network} - {phone_number}",
            extra_data=json.dumps({"network": network, "phone_number": phone_number})
        )
        
        try:
            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating transaction: {str(e)}")
        
        # Make API call to bill provider
        params = {
            "UserID": "Penivera",
            "APIKey": self.api_key,
            "MobileNetwork": network,
            "Amount": amount,
            "MobileNumber": phone_number,
            "CallBackURL": f"{settings.BILL_URL}/callback"
        }
        
        try:
            response = requests.get(self.bill_url, params=params, timeout=30)
            response_data = response.json()
            
            # Update transaction status based on response
            if response.status_code == 200:
                transaction.status = TransactionStatus.PROCESSING
            else:
                transaction.status = TransactionStatus.FAILED
                transaction.extra_data = json.dumps({
                    **json.loads(transaction.extra_data),
                    "error": response_data
                })
            
            await db.commit()
            return response_data
            
        except requests.RequestException as e:
            transaction.status = TransactionStatus.FAILED
            await db.commit()
            raise Exception(f"Failed to process airtime request: {str(e)}")
    
    async def buy_airtime_simple(
        self,
        phone_number: str,
        amount: str,
        network: str
    ) -> dict:
        """
        Purchase airtime without wallet (direct API call).
        
        Args:
            phone_number: Phone number to credit
            amount: Amount of airtime to purchase
            network: Mobile network
            
        Returns:
            Dictionary containing purchase result
        """
        params = {
            "UserID": "Penivera",
            "APIKey": self.api_key,
            "MobileNetwork": network,
            "Amount": amount,
            "MobileNumber": phone_number,
            "CallBackURL": "https://cypher-85fk.onrender.com/callback"
        }
        
        try:
            response = requests.get(self.bill_url, params=params, timeout=30)
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to process airtime request: {str(e)}")
    
    async def save_callback_data(self, data: dict) -> dict:
        """
        Save callback data from bill provider.
        
        Args:
            data: Callback data from provider
            
        Returns:
            Success message
        """
        if data:
            file_path = os.path.join(self.base_dir, "data.json")
            async with aiofiles.open(file_path, "w") as file:
                await file.write(json.dumps(data, indent=4))
        return {"message": "Data saved successfully"}
    
    async def get_payment_result(self) -> dict:
        """
        Get the latest payment result from callback data.
        
        Returns:
            Payment result data
        """
        try:
            file_path = os.path.join(self.base_dir, "data.json")
            async with aiofiles.open(file_path, "r") as file:
                data = json.loads(await file.read())
            return data
        except FileNotFoundError:
            return {"message": "No payment data available"}
        except json.JSONDecodeError:
            return {"message": "Error reading payment data"}
    
    def get_data_plans(self) -> dict:
        """
        Get available data plans for all networks.
        
        Returns:
            Dictionary of data plans
        """
        return self.data_plans
    
    async def purchase_data(
        self,
        db: AsyncSession,
        wallet_id: int,
        phone_number: str,
        network: str,
        product_code: str
    ) -> dict:
        """
        Purchase data bundle for a phone number.
        
        Args:
            db: Database session
            wallet_id: ID of the wallet to debit
            phone_number: Phone number to credit
            network: Mobile network
            product_code: Data plan product code
            
        Returns:
            Dictionary containing purchase result
        """
        # Find the product in data plans
        product = None
        amount = "0"
        product_name = ""
        
        if network in self.data_plans["MOBILE_NETWORK"]:
            for provider in self.data_plans["MOBILE_NETWORK"][network]:
                for prod in provider["PRODUCT"]:
                    if prod["PRODUCT_CODE"] == product_code:
                        product = prod
                        amount = prod["PRODUCT_AMOUNT"]
                        product_name = prod["PRODUCT_NAME"]
                        break
        
        if not product:
            raise ValueError(f"Product not found: {product_code} for network {network}")
        
        # Verify wallet exists
        query = select(Wallet).where(Wallet.id == wallet_id, Wallet.is_active == True)
        result: Result = await db.execute(query)
        wallet = result.scalars().first()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet_id,
            transaction_type=TransactionType.BILL_PAYMENT,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency="NGN",
            recipient_address=phone_number,
            description=f"Data purchase - {network} - {product_name}",
            extra_data=json.dumps({
                "network": network,
                "phone_number": phone_number,
                "product_code": product_code,
                "product_name": product_name
            })
        )
        
        try:
            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
            
            return {
                "transaction_id": transaction.id,
                "status": transaction.status.value,
                "amount": amount,
                "product": product_name,
                "phone_number": phone_number,
                "message": "Data purchase initiated"
            }
            
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating transaction: {str(e)}")
    
    async def get_bill_history(
        self,
        db: AsyncSession,
        wallet_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> dict:
        """
        Get bill payment history for a wallet.
        
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
            Transaction.transaction_type.in_([TransactionType.BILL_PAYMENT, TransactionType.AIRTIME])
        ).order_by(Transaction.created_at.desc()).offset(offset).limit(per_page)
        
        result: Result = await db.execute(query)
        transactions = result.scalars().all()
        
        # Get total count
        count_query = select(Transaction).where(
            Transaction.wallet_id == wallet_id,
            Transaction.transaction_type.in_([TransactionType.BILL_PAYMENT, TransactionType.AIRTIME])
        )
        count_result: Result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "type": t.transaction_type.value,
                    "amount": str(t.amount),
                    "status": t.status.value,
                    "recipient": t.recipient_address,
                    "description": t.description,
                    "created_at": t.created_at.isoformat()
                }
                for t in transactions
            ],
            "total_count": total_count,
            "page": page,
            "per_page": per_page
        }


# Singleton instance
bill_service = BillService()

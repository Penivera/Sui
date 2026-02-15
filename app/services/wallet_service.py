"""Wallet service for managing cryptocurrency wallets."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_crypto import create_new_address
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_builders.get_builders import GetCoins

from app.models.user import User
from app.models.wallet import Wallet
from app.core.config import settings
from app.core.security import hash_password, verify_password


class WalletService:
    """Service class for wallet management operations."""
    
    def __init__(self):
        """Initialize the wallet service."""
        self._client = None
        self._config = None
    
    @property
    def config(self):
        """Lazily initialize SUI config."""
        if self._config is None:
            self._config = SuiConfig.user_config(rpc_url=settings.SUI_RPC_URL)
        return self._config
    
    @property
    def client(self):
        """Lazily initialize SUI client."""
        if self._client is None:
            self._client = SuiClient(config=self.config)
        return self._client
    
    async def create_user_with_wallet(
        self,
        db: AsyncSession,
        username: str,
        pin: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        wallet_name: str = "Main Wallet"
    ) -> dict:
        """
        Create a new user with a SUI wallet.
        
        Args:
            db: Database session
            username: User's username
            pin: User's PIN (will be hashed)
            email: Optional email address
            phone_number: Optional phone number
            wallet_name: Name for the wallet
            
        Returns:
            Dictionary containing wallet details and mnemonics
        """
        # Generate new SUI wallet
        wallet_data = create_new_address(word_counts=12, keytype=SignatureScheme.ED25519)
        mnemonics, keypair, address = wallet_data
        
        # Hash the PIN
        hashed_pin = hash_password(pin)
        
        # Create user
        new_user = User(
            username=username,
            pin=hashed_pin,
            email=email,
            phone_number=phone_number
        )
        
        try:
            db.add(new_user)
            await db.flush()  # Get the user ID
            
            # Create wallet associated with user
            new_wallet = Wallet(
                user_id=new_user.id,
                address=address.address,
                wallet_name=wallet_name,
                is_primary=True,
                is_active=True
            )
            
            db.add(new_wallet)
            await db.commit()
            await db.refresh(new_user)
            await db.refresh(new_wallet)
            
        except IntegrityError:
            await db.rollback()
            raise ValueError("User already exists")
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating user: {str(e)}")
        
        return {
            "wallet": address.address,
            "mnemonics": mnemonics,
            "private_key": keypair.private_key.to_b64(),
            "wallet_id": new_wallet.id,
            "user_id": new_user.id
        }
    
    async def add_wallet_to_user(
        self,
        db: AsyncSession,
        user_id: int,
        wallet_name: str = "Secondary Wallet"
    ) -> dict:
        """
        Add a new wallet to an existing user.
        
        Args:
            db: Database session
            user_id: ID of the user
            wallet_name: Name for the new wallet
            
        Returns:
            Dictionary containing wallet details and mnemonics
        """
        # Verify user exists
        query = select(User).where(User.id == user_id)
        result: Result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            raise ValueError("User not found")
        
        # Generate new SUI wallet
        wallet_data = create_new_address(word_counts=12, keytype=SignatureScheme.ED25519)
        mnemonics, keypair, address = wallet_data
        
        # Create wallet
        new_wallet = Wallet(
            user_id=user_id,
            address=address.address,
            wallet_name=wallet_name,
            is_primary=False,
            is_active=True
        )
        
        try:
            db.add(new_wallet)
            await db.commit()
            await db.refresh(new_wallet)
        except IntegrityError:
            await db.rollback()
            raise ValueError("Wallet address already exists")
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating wallet: {str(e)}")
        
        return {
            "wallet": address.address,
            "mnemonics": mnemonics,
            "private_key": keypair.private_key.to_b64(),
            "wallet_id": new_wallet.id
        }
    
    async def get_wallet_balance(self, address: str) -> dict:
        """
        Get the balance of a SUI wallet.
        
        Args:
            address: SUI wallet address
            
        Returns:
            Dictionary containing balance information
        """
        try:
            coins_response = self.client.execute(GetCoins(owner=address))
            if coins_response.is_ok():
                coins = coins_response.result_data.data
                total_balance = sum(int(coin.balance) for coin in coins)
                return {
                    "address": address,
                    "balance": str(total_balance),
                    "currency": "SUI"
                }
            else:
                raise Exception(f"Error fetching balance: {coins_response.result_string}")
        except Exception as e:
            raise Exception(f"Failed to get balance: {str(e)}")
    
    async def get_user_wallets(self, db: AsyncSession, user_id: int) -> List[Wallet]:
        """
        Get all wallets for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of wallet objects
        """
        query = select(Wallet).where(Wallet.user_id == user_id, Wallet.is_active == True)
        result: Result = await db.execute(query)
        return result.scalars().all()
    
    async def get_wallet_by_address(self, db: AsyncSession, address: str) -> Optional[Wallet]:
        """
        Get a wallet by its address.
        
        Args:
            db: Database session
            address: Wallet address
            
        Returns:
            Wallet object or None
        """
        query = select(Wallet).where(Wallet.address == address)
        result: Result = await db.execute(query)
        return result.scalars().first()
    
    async def deactivate_wallet(self, db: AsyncSession, wallet_id: int, user_id: int) -> bool:
        """
        Deactivate a wallet (soft delete).
        
        Args:
            db: Database session
            wallet_id: ID of the wallet
            user_id: ID of the user (for verification)
            
        Returns:
            True if successful
        """
        query = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
        )
        result: Result = await db.execute(query)
        wallet = result.scalars().first()
        
        if not wallet:
            raise ValueError("Wallet not found")
        
        if wallet.is_primary:
            raise ValueError("Cannot deactivate primary wallet")
        
        wallet.is_active = False
        await db.commit()
        return True
    
    async def set_primary_wallet(self, db: AsyncSession, wallet_id: int, user_id: int) -> bool:
        """
        Set a wallet as the primary wallet for a user.
        
        Args:
            db: Database session
            wallet_id: ID of the wallet to set as primary
            user_id: ID of the user
            
        Returns:
            True if successful
        """
        # First, unset any existing primary wallet
        query = select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.is_primary == True
        )
        result: Result = await db.execute(query)
        current_primary = result.scalars().first()
        
        if current_primary:
            current_primary.is_primary = False
        
        # Set the new primary wallet
        query = select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id
        )
        result = await db.execute(query)
        new_primary = result.scalars().first()
        
        if not new_primary:
            raise ValueError("Wallet not found")
        
        new_primary.is_primary = True
        await db.commit()
        return True


# Singleton instance
wallet_service = WalletService()

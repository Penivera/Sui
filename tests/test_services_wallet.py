"""Tests for wallet service."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models.user import User
from app.models.wallet import Wallet
from app.services.wallet_service import WalletService


@pytest.fixture
async def async_db_engine():
    """Create a test async database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine):
    """Create a test async database session."""
    async_session = async_sessionmaker(
        bind=async_db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def wallet_service():
    """Create a wallet service instance."""
    return WalletService()


@pytest.mark.asyncio
async def test_create_user_with_wallet(async_db_session, wallet_service):
    """Test creating a new user with wallet."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        # Mock the SUI wallet creation
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xmock_address_123"
        mock_create.return_value = ("word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234",
            email="test@example.com"
        )
        
        assert "wallet" in result
        assert "mnemonics" in result
        assert "private_key" in result
        assert "wallet_id" in result
        assert "user_id" in result
        assert result["wallet"] == "0xmock_address_123"


@pytest.mark.asyncio
async def test_create_user_duplicate_username(async_db_session, wallet_service):
    """Test creating user with duplicate username fails."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xmock_address_123"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        # Create first user
        await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        
        # Try to create second user with same username
        mock_address.address = "0xdifferent_address"
        with pytest.raises(ValueError, match="User already exists"):
            await wallet_service.create_user_with_wallet(
                db=async_db_session,
                username="testuser",
                pin="5678"
            )


@pytest.mark.asyncio
async def test_add_wallet_to_user(async_db_session, wallet_service):
    """Test adding a wallet to an existing user."""
    # First create a user with wallet
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xmock_address_123"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        user_id = result["user_id"]
        
        # Add a second wallet
        mock_address.address = "0xsecond_wallet_456"
        result2 = await wallet_service.add_wallet_to_user(
            db=async_db_session,
            user_id=user_id,
            wallet_name="Secondary Wallet"
        )
        
        assert result2["wallet"] == "0xsecond_wallet_456"


@pytest.mark.asyncio
async def test_add_wallet_to_nonexistent_user(async_db_session, wallet_service):
    """Test adding wallet to non-existent user fails."""
    with pytest.raises(ValueError, match="User not found"):
        await wallet_service.add_wallet_to_user(
            db=async_db_session,
            user_id=9999
        )


@pytest.mark.asyncio
async def test_get_user_wallets(async_db_session, wallet_service):
    """Test getting all wallets for a user."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xwallet1"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        user_id = result["user_id"]
        
        # Add another wallet
        mock_address.address = "0xwallet2"
        await wallet_service.add_wallet_to_user(
            db=async_db_session,
            user_id=user_id
        )
        
        wallets = await wallet_service.get_user_wallets(
            db=async_db_session,
            user_id=user_id
        )
        
        assert len(wallets) == 2


@pytest.mark.asyncio
async def test_deactivate_wallet(async_db_session, wallet_service):
    """Test deactivating a non-primary wallet."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xwallet1"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        user_id = result["user_id"]
        
        # Add a secondary wallet
        mock_address.address = "0xwallet2"
        result2 = await wallet_service.add_wallet_to_user(
            db=async_db_session,
            user_id=user_id
        )
        
        # Deactivate the secondary wallet
        success = await wallet_service.deactivate_wallet(
            db=async_db_session,
            wallet_id=result2["wallet_id"],
            user_id=user_id
        )
        
        assert success is True


@pytest.mark.asyncio
async def test_cannot_deactivate_primary_wallet(async_db_session, wallet_service):
    """Test that primary wallet cannot be deactivated."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xwallet1"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        
        with pytest.raises(ValueError, match="Cannot deactivate primary wallet"):
            await wallet_service.deactivate_wallet(
                db=async_db_session,
                wallet_id=result["wallet_id"],
                user_id=result["user_id"]
            )


@pytest.mark.asyncio
async def test_set_primary_wallet(async_db_session, wallet_service):
    """Test setting a wallet as primary."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xwallet1"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        result = await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        user_id = result["user_id"]
        
        # Add a secondary wallet
        mock_address.address = "0xwallet2"
        result2 = await wallet_service.add_wallet_to_user(
            db=async_db_session,
            user_id=user_id
        )
        
        # Set the secondary wallet as primary
        success = await wallet_service.set_primary_wallet(
            db=async_db_session,
            wallet_id=result2["wallet_id"],
            user_id=user_id
        )
        
        assert success is True


@pytest.mark.asyncio
async def test_get_wallet_by_address(async_db_session, wallet_service):
    """Test getting a wallet by its address."""
    with patch('app.services.wallet_service.create_new_address') as mock_create:
        mock_keypair = MagicMock()
        mock_keypair.private_key.to_b64.return_value = "mock_private_key_b64"
        mock_address = MagicMock()
        mock_address.address = "0xunique_address_123"
        mock_create.return_value = ("mnemonic words", mock_keypair, mock_address)
        
        await wallet_service.create_user_with_wallet(
            db=async_db_session,
            username="testuser",
            pin="1234"
        )
        
        wallet = await wallet_service.get_wallet_by_address(
            db=async_db_session,
            address="0xunique_address_123"
        )
        
        assert wallet is not None
        assert wallet.address == "0xunique_address_123"


@pytest.mark.asyncio
async def test_get_wallet_by_nonexistent_address(async_db_session, wallet_service):
    """Test getting a wallet by non-existent address returns None."""
    wallet = await wallet_service.get_wallet_by_address(
        db=async_db_session,
        address="0xnonexistent"
    )
    
    assert wallet is None

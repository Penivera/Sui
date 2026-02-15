"""Tests for offramp service."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.services.offramp_service import OfframpService


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
def offramp_service():
    """Create an offramp service instance."""
    return OfframpService()


@pytest.fixture
async def user_with_wallet(async_db_session):
    """Create a test user with a wallet."""
    user = User(username="testuser", pin="hashed_pin")
    async_db_session.add(user)
    await async_db_session.commit()
    
    wallet = Wallet(
        user_id=user.id,
        address="0xtest_wallet_address",
        wallet_name="Test Wallet",
        is_primary=True,
        is_active=True
    )
    async_db_session.add(wallet)
    await async_db_session.commit()
    
    return user, wallet


@pytest.mark.asyncio
async def test_initiate_offramp(async_db_session, offramp_service, user_with_wallet):
    """Test initiating an offramp transaction."""
    user, wallet = user_with_wallet
    
    with patch('app.services.offramp_service.wallet_service') as mock_wallet_service:
        mock_wallet_service.get_wallet_balance = AsyncMock(return_value={
            "balance": "10000000000",  # 10 SUI in MIST
            "currency": "SUI"
        })
        
        result = await offramp_service.initiate_offramp(
            db=async_db_session,
            wallet_id=wallet.id,
            amount="1",
            bank_account="1234567890"
        )
        
        assert "transaction_id" in result
        assert result["status"] == "pending"
        assert result["amount"] == "1"
        assert "estimated_fiat" in result


@pytest.mark.asyncio
async def test_initiate_offramp_insufficient_balance(async_db_session, offramp_service, user_with_wallet):
    """Test initiating offramp with insufficient balance fails."""
    user, wallet = user_with_wallet
    
    with patch('app.services.offramp_service.wallet_service') as mock_wallet_service:
        mock_wallet_service.get_wallet_balance = AsyncMock(return_value={
            "balance": "100000",  # Very small balance
            "currency": "SUI"
        })
        
        with pytest.raises(ValueError, match="Insufficient balance"):
            await offramp_service.initiate_offramp(
                db=async_db_session,
                wallet_id=wallet.id,
                amount="100",  # Requesting more than available
                bank_account="1234567890"
            )


@pytest.mark.asyncio
async def test_initiate_offramp_wallet_not_found(async_db_session, offramp_service):
    """Test initiating offramp with non-existent wallet fails."""
    with pytest.raises(ValueError, match="Wallet not found"):
        await offramp_service.initiate_offramp(
            db=async_db_session,
            wallet_id=9999,
            amount="1"
        )


@pytest.mark.asyncio
async def test_process_offramp(async_db_session, offramp_service, user_with_wallet):
    """Test processing a pending offramp transaction."""
    user, wallet = user_with_wallet
    
    # Create a pending transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.OFFRAMP,
        status=TransactionStatus.PENDING,
        amount="1",
        currency="SUI"
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    
    result = await offramp_service.process_offramp(
        db=async_db_session,
        transaction_id=transaction.id
    )
    
    assert result["status"] == "processing"
    assert result["transaction_id"] == transaction.id


@pytest.mark.asyncio
async def test_process_offramp_already_processed(async_db_session, offramp_service, user_with_wallet):
    """Test processing an already processed transaction fails."""
    user, wallet = user_with_wallet
    
    # Create a processing transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.OFFRAMP,
        status=TransactionStatus.PROCESSING,
        amount="1",
        currency="SUI"
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    
    with pytest.raises(ValueError, match="cannot be processed"):
        await offramp_service.process_offramp(
            db=async_db_session,
            transaction_id=transaction.id
        )


@pytest.mark.asyncio
async def test_complete_offramp(async_db_session, offramp_service, user_with_wallet):
    """Test completing an offramp transaction."""
    user, wallet = user_with_wallet
    
    # Create a processing transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.OFFRAMP,
        status=TransactionStatus.PROCESSING,
        amount="1",
        currency="SUI"
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    
    result = await offramp_service.complete_offramp(
        db=async_db_session,
        transaction_id=transaction.id,
        transaction_hash="0xtx_hash_123"
    )
    
    assert result["status"] == "completed"
    assert result["transaction_hash"] == "0xtx_hash_123"


@pytest.mark.asyncio
async def test_cancel_offramp(async_db_session, offramp_service, user_with_wallet):
    """Test cancelling a pending offramp transaction."""
    user, wallet = user_with_wallet
    
    # Create a pending transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.OFFRAMP,
        status=TransactionStatus.PENDING,
        amount="1",
        currency="SUI"
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    
    result = await offramp_service.cancel_offramp(
        db=async_db_session,
        transaction_id=transaction.id,
        reason="Changed my mind"
    )
    
    assert result["status"] == "cancelled"
    assert "Changed my mind" in result["message"]


@pytest.mark.asyncio
async def test_cancel_offramp_not_pending(async_db_session, offramp_service, user_with_wallet):
    """Test cancelling a non-pending transaction fails."""
    user, wallet = user_with_wallet
    
    # Create a completed transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.OFFRAMP,
        status=TransactionStatus.COMPLETED,
        amount="1",
        currency="SUI"
    )
    async_db_session.add(transaction)
    await async_db_session.commit()
    
    with pytest.raises(ValueError, match="Cannot cancel transaction"):
        await offramp_service.cancel_offramp(
            db=async_db_session,
            transaction_id=transaction.id
        )


@pytest.mark.asyncio
async def test_get_offramp_history(async_db_session, offramp_service, user_with_wallet):
    """Test getting offramp transaction history."""
    user, wallet = user_with_wallet
    
    # Create multiple transactions
    for i in range(5):
        transaction = Transaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.OFFRAMP,
            status=TransactionStatus.COMPLETED,
            amount=str(i + 1),
            currency="SUI"
        )
        async_db_session.add(transaction)
    await async_db_session.commit()
    
    result = await offramp_service.get_offramp_history(
        db=async_db_session,
        wallet_id=wallet.id,
        page=1,
        per_page=3
    )
    
    assert len(result["transactions"]) == 3
    assert result["total_count"] == 5
    assert result["page"] == 1
    assert result["per_page"] == 3


@pytest.mark.asyncio
async def test_get_offramp_history_empty(async_db_session, offramp_service, user_with_wallet):
    """Test getting offramp history when no transactions exist."""
    user, wallet = user_with_wallet
    
    result = await offramp_service.get_offramp_history(
        db=async_db_session,
        wallet_id=wallet.id
    )
    
    assert len(result["transactions"]) == 0
    assert result["total_count"] == 0

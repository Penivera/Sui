"""Tests for bill service."""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.services.bill_service import BillService


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
def bill_service():
    """Create a bill service instance."""
    return BillService()


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


def test_get_data_plans(bill_service):
    """Test getting available data plans."""
    plans = bill_service.get_data_plans()
    
    assert "MOBILE_NETWORK" in plans
    assert "MTN" in plans["MOBILE_NETWORK"]
    assert "Glo" in plans["MOBILE_NETWORK"]


def test_get_data_plans_mtn_products(bill_service):
    """Test MTN data plan products exist."""
    plans = bill_service.get_data_plans()
    
    mtn_products = plans["MOBILE_NETWORK"]["MTN"][0]["PRODUCT"]
    assert len(mtn_products) >= 3
    
    # Check product structure
    for product in mtn_products:
        assert "PRODUCT_CODE" in product
        assert "PRODUCT_NAME" in product
        assert "PRODUCT_AMOUNT" in product


def test_get_data_plans_glo_products(bill_service):
    """Test Glo data plan products exist."""
    plans = bill_service.get_data_plans()
    
    glo_products = plans["MOBILE_NETWORK"]["Glo"][0]["PRODUCT"]
    assert len(glo_products) >= 2


@pytest.mark.asyncio
async def test_purchase_data(async_db_session, bill_service, user_with_wallet):
    """Test purchasing a data bundle."""
    user, wallet = user_with_wallet
    
    result = await bill_service.purchase_data(
        db=async_db_session,
        wallet_id=wallet.id,
        phone_number="08012345678",
        network="MTN",
        product_code="2"  # 500 MB plan
    )
    
    assert "transaction_id" in result
    assert result["status"] == "pending"
    assert result["product"] == "500 MB - 30 days (SME)"
    assert result["phone_number"] == "08012345678"


@pytest.mark.asyncio
async def test_purchase_data_invalid_product(async_db_session, bill_service, user_with_wallet):
    """Test purchasing with invalid product code fails."""
    user, wallet = user_with_wallet
    
    with pytest.raises(ValueError, match="Product not found"):
        await bill_service.purchase_data(
            db=async_db_session,
            wallet_id=wallet.id,
            phone_number="08012345678",
            network="MTN",
            product_code="999"  # Non-existent product
        )


@pytest.mark.asyncio
async def test_purchase_data_invalid_network(async_db_session, bill_service, user_with_wallet):
    """Test purchasing with invalid network fails."""
    user, wallet = user_with_wallet
    
    with pytest.raises(ValueError, match="Product not found"):
        await bill_service.purchase_data(
            db=async_db_session,
            wallet_id=wallet.id,
            phone_number="08012345678",
            network="InvalidNetwork",
            product_code="2"
        )


@pytest.mark.asyncio
async def test_purchase_data_wallet_not_found(async_db_session, bill_service):
    """Test purchasing with non-existent wallet fails."""
    with pytest.raises(ValueError, match="Wallet not found"):
        await bill_service.purchase_data(
            db=async_db_session,
            wallet_id=9999,
            phone_number="08012345678",
            network="MTN",
            product_code="2"
        )


@pytest.mark.asyncio
async def test_get_bill_history(async_db_session, bill_service, user_with_wallet):
    """Test getting bill payment history."""
    user, wallet = user_with_wallet
    
    # Create multiple bill transactions
    for i in range(5):
        transaction = Transaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.BILL_PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=str(100 * (i + 1)),
            currency="NGN",
            recipient_address="08012345678"
        )
        async_db_session.add(transaction)
    await async_db_session.commit()
    
    result = await bill_service.get_bill_history(
        db=async_db_session,
        wallet_id=wallet.id,
        page=1,
        per_page=3
    )
    
    assert len(result["transactions"]) == 3
    assert result["total_count"] == 5


@pytest.mark.asyncio
async def test_get_bill_history_includes_airtime(async_db_session, bill_service, user_with_wallet):
    """Test that bill history includes airtime transactions."""
    user, wallet = user_with_wallet
    
    # Create airtime transaction
    airtime_tx = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.AIRTIME,
        status=TransactionStatus.COMPLETED,
        amount="500",
        currency="NGN",
        recipient_address="08012345678"
    )
    async_db_session.add(airtime_tx)
    
    # Create bill payment transaction
    bill_tx = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.BILL_PAYMENT,
        status=TransactionStatus.COMPLETED,
        amount="1000",
        currency="NGN",
        recipient_address="08012345678"
    )
    async_db_session.add(bill_tx)
    await async_db_session.commit()
    
    result = await bill_service.get_bill_history(
        db=async_db_session,
        wallet_id=wallet.id
    )
    
    assert result["total_count"] == 2
    
    # Verify both transaction types are included
    types = [tx["type"] for tx in result["transactions"]]
    assert "airtime" in types
    assert "bill_payment" in types


@pytest.mark.asyncio
async def test_get_bill_history_empty(async_db_session, bill_service, user_with_wallet):
    """Test getting bill history when no transactions exist."""
    user, wallet = user_with_wallet
    
    result = await bill_service.get_bill_history(
        db=async_db_session,
        wallet_id=wallet.id
    )
    
    assert len(result["transactions"]) == 0
    assert result["total_count"] == 0


@pytest.mark.asyncio
async def test_save_callback_data(bill_service, tmp_path):
    """Test saving callback data."""
    bill_service.base_dir = str(tmp_path)
    
    test_data = {"status": "success", "reference": "ABC123"}
    result = await bill_service.save_callback_data(test_data)
    
    assert result["message"] == "Data saved successfully"


@pytest.mark.asyncio
async def test_get_payment_result_no_data(bill_service, tmp_path):
    """Test getting payment result when no data exists."""
    bill_service.base_dir = str(tmp_path)
    
    result = await bill_service.get_payment_result()
    
    assert result["message"] == "No payment data available"


@pytest.mark.asyncio
async def test_get_payment_result_with_data(bill_service, tmp_path):
    """Test getting payment result after saving data."""
    bill_service.base_dir = str(tmp_path)
    
    # Save some data first
    test_data = {"status": "success", "reference": "ABC123"}
    await bill_service.save_callback_data(test_data)
    
    # Now retrieve it
    result = await bill_service.get_payment_result()
    
    assert result["status"] == "success"
    assert result["reference"] == "ABC123"

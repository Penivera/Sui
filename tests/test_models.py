"""Tests for models."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction, TransactionType, TransactionStatus


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


def test_user_model(db_session):
    """Test User model creation."""
    user = User(
        username="testuser",
        pin="hashed_pin_123"
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.is_active is True


def test_wallet_model(db_session):
    """Test Wallet model creation."""
    user = User(username="testuser", pin="hashed_pin")
    db_session.add(user)
    db_session.commit()
    
    wallet = Wallet(
        user_id=user.id,
        address="0x123456789",
        wallet_name="Test Wallet",
        is_primary=True
    )
    db_session.add(wallet)
    db_session.commit()
    
    assert wallet.id is not None
    assert wallet.address == "0x123456789"
    assert wallet.is_primary is True
    assert wallet.user_id == user.id


def test_transaction_model(db_session):
    """Test Transaction model creation."""
    user = User(username="testuser", pin="hashed_pin")
    db_session.add(user)
    db_session.commit()
    
    wallet = Wallet(
        user_id=user.id,
        address="0x123456789",
        wallet_name="Test Wallet"
    )
    db_session.add(wallet)
    db_session.commit()
    
    transaction = Transaction(
        wallet_id=wallet.id,
        transaction_type=TransactionType.DEPOSIT,
        status=TransactionStatus.PENDING,
        amount="100.5",
        currency="SUI"
    )
    db_session.add(transaction)
    db_session.commit()
    
    assert transaction.id is not None
    assert transaction.transaction_type == TransactionType.DEPOSIT
    assert transaction.status == TransactionStatus.PENDING


def test_user_wallet_relationship(db_session):
    """Test User-Wallet relationship."""
    user = User(username="testuser", pin="hashed_pin")
    db_session.add(user)
    db_session.commit()
    
    wallet1 = Wallet(user_id=user.id, address="0x111", wallet_name="Wallet 1")
    wallet2 = Wallet(user_id=user.id, address="0x222", wallet_name="Wallet 2")
    db_session.add(wallet1)
    db_session.add(wallet2)
    db_session.commit()
    
    # Refresh user to load wallets relationship
    db_session.refresh(user)
    
    assert len(user.wallets) == 2

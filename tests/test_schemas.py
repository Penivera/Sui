"""Tests for Pydantic schemas."""
import pytest
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.wallet import WalletCreate, WalletResponse, WalletBalance
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionTypeEnum


def test_user_create_schema():
    """Test UserCreate schema."""
    user = UserCreate(username="testuser", pin="1234")
    assert user.username == "testuser"
    assert user.pin == "1234"


def test_user_create_with_optional_fields():
    """Test UserCreate schema with optional fields."""
    user = UserCreate(
        username="testuser", 
        pin="1234",
        email="test@example.com",
        phone_number="08012345678"
    )
    assert user.email == "test@example.com"
    assert user.phone_number == "08012345678"


def test_user_login_schema():
    """Test UserLogin schema."""
    login = UserLogin(username="testuser", pin="1234")
    assert login.username == "testuser"
    assert login.pin == "1234"


def test_wallet_create_schema():
    """Test WalletCreate schema."""
    wallet = WalletCreate(wallet_name="My Wallet", is_primary=True)
    assert wallet.wallet_name == "My Wallet"
    assert wallet.is_primary is True


def test_wallet_balance_schema():
    """Test WalletBalance schema."""
    balance = WalletBalance(
        address="0x123...",
        balance="1000000000",
        currency="SUI"
    )
    assert balance.address == "0x123..."
    assert balance.balance == "1000000000"
    assert balance.currency == "SUI"


def test_transaction_create_schema():
    """Test TransactionCreate schema."""
    tx = TransactionCreate(
        wallet_id=1,
        transaction_type=TransactionTypeEnum.DEPOSIT,
        amount="100"
    )
    assert tx.wallet_id == 1
    assert tx.transaction_type == TransactionTypeEnum.DEPOSIT
    assert tx.amount == "100"

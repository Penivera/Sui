"""Tests for core modules."""
import pytest
from app.core.security import hash_password, verify_password, hash_pin
from app.core.config import settings


def test_hash_password():
    """Test password hashing."""
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password():
    """Test password verification."""
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_hash_pin():
    """Test PIN hashing."""
    pin = "1234"
    hashed = hash_pin(pin)
    
    assert hashed != pin
    assert verify_password(pin, hashed) is True


def test_settings_defaults():
    """Test settings have appropriate defaults."""
    assert settings.APP_NAME == "Sheda Solutions Backend"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.SUI_RPC_URL is not None

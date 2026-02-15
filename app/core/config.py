"""Application configuration and settings."""
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "Sheda Solutions Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DB_URL", "sqlite+aiosqlite:///./database.db")
    
    # Sui RPC configuration
    SUI_RPC_URL: str = os.getenv("SUI_RPC_URL", "https://fullnode.mainnet.sui.io:443")
    
    # API Keys
    API_KEY: Optional[str] = os.getenv("API_KEY")
    OFFRAMP_API_KEY: Optional[str] = os.getenv("OFFRAMP_API_KEY")
    PAYMENT_PROVIDER_API_KEY: Optional[str] = os.getenv("PAYMENT_PROVIDER_API_KEY")
    
    # Bill payment URLs
    BILL_URL: str = os.getenv("BILL_URL", "https://www.nellobytesystems.com/APICancelV1.asp")
    CALLBACK_URL: str = os.getenv("CALLBACK_URL", "https://cypher-85fk.onrender.com/callback")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

"""Main FastAPI application with proper structure and routing."""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import wallet, auth, offramp, bills


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Sheda Solutions - Sui Off-Ramp & Bills Payment Solution

A robust backend for cryptocurrency wallet management and off-ramp functionalities.

### Features

- **Wallet Management**: Create and manage SUI wallets
- **Off-Ramp**: Convert SUI to fiat currency
- **Bill Payments**: Pay for utilities, airtime, and data
- **Transaction Tracking**: Complete history of all transactions

### Authentication

Users authenticate using their username and PIN.
    """,
    docs_url="/",
    redoc_url="/docs",
    lifespan=lifespan
)

# Include routers
app.include_router(wallet.router)
app.include_router(auth.router)
app.include_router(offramp.router)
app.include_router(bills.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}

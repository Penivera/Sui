# Sui
Sui Off-Ramp & Bills Payment Solution

## Overview

This project is a Sui-based off-ramp and bill payment solution that allows users to seamlessly convert their Sui assets into fiat and pay for utilities. It automates off-ramping through integrations with liquidity providers while ensuring a smooth user experience for bill payments.

## Features

- **Wallet Management**: Create and manage multiple SUI wallets per user
- **Automated Off-Ramp**: Converts Sui assets to fiat with programmatic access to liquidity sources
- **Bill Payments**: Pay for utilities like electricity, internet, and mobile top-ups using Sui
- **Transaction Tracking**: Complete history of all transactions with status updates
- **Fast Settlements**: Ensures efficient and real-time transactions
- **Secure & Reliable**: Built with strong security measures to protect user funds and data

## Project Structure

```
Sui/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py           # Authentication routes
│   │       ├── wallet.py         # Wallet management routes
│   │       ├── offramp.py        # Off-ramp routes
│   │       └── bills.py          # Bill payment routes
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings
│   │   ├── database.py           # Database configuration
│   │   └── security.py           # Security utilities
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── wallet.py             # Wallet model
│   │   └── transaction.py        # Transaction model
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py               # User schemas
│   │   ├── wallet.py             # Wallet schemas
│   │   └── transaction.py        # Transaction schemas
│   └── services/                 # Business logic
│       ├── __init__.py
│       ├── wallet_service.py     # Wallet operations
│       ├── offramp_service.py    # Off-ramp operations
│       └── bill_service.py       # Bill payment operations
├── off_ramp/                     # Sui Move smart contracts
│   ├── Move.toml
│   ├── sources/
│   │   └── off_ramp.move         # Off-ramp contract
│   └── tests/
│       └── off_ramp_tests.move   # Contract tests
├── main.py                       # Legacy entry point (deprecated)
├── models.py                     # Legacy models (deprecated)
├── db.py                         # Legacy database (deprecated)
├── requirements.txt              # Python dependencies
└── README.md
```

## Architecture

The solution consists of:

1. **Sui Smart Contracts** – Handles transactions and ensures on-chain security.

2. **Backend API (FastAPI)** – Manages user requests, integrates with liquidity providers, and processes bill payments.

3. **Frontend Mobile app (Kotlin)** – Provides an intuitive interface for users to initiate off-ramp requests and pay bills.

4. **Payment & Liquidity Providers** – External services that facilitate fiat conversion and bill processing.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/sui-offramp-billpay.git
cd sui-offramp-billpay
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

Create a `.env` file with the following variables:
```env
DEBUG=False
DB_URL=postgresql://user:password@localhost/dbname
SUI_RPC_URL=https://fullnode.mainnet.sui.io:443
API_KEY=your_api_key
OFFRAMP_API_KEY=your_offramp_key
PAYMENT_PROVIDER_API_KEY=your_payment_key
SECRET_KEY=your-secret-key
```

5. Run the Backend:

```bash
# Using the new structured app
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or using the legacy main.py (deprecated)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/
- ReDoc: http://localhost:8000/docs

## Usage

### 1. Wallet Management

Create a new user with wallet:
```bash
POST /wallet/create
{
    "username": "john",
    "pin": "1234"
}
```

Get wallet balance:
```bash
GET /wallet/balance/{address}
```

### 2. Off-Ramping

Initiate an off-ramp:
```bash
POST /offramp/initiate
{
    "wallet_id": 1,
    "amount": "100",
    "bank_account": "1234567890"
}
```

### 3. Bill Payments

Buy airtime:
```bash
POST /bills/airtime?phone_number=08012345678&amount=500&network=MTN
```

Get data plans:
```bash
GET /bills/data-plans
```

## Future Enhancements

- Support for additional fiat currencies
- Integration with more liquidity sources
- Expanding bill payment options
- Mobile money integration
- Multi-signature wallet support

## Contributing

Feel free to submit issues or open pull requests for improvements.

## License

MIT License.

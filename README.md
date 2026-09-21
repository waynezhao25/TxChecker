This is a FastAPI project that analyzes the security of a crypto transaction.
Using only a Ethereum transaction hash as a input, TxChecker provides a human-readable explanation and analyzes the security
with 3 rules (unlimited approval, flagged spender, and failed transaction).
Features an in-memory cache that speeds up repeated lookups.

## Setup

Run these commands from the project folder to create a virtual environment and install required libraries.

```
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file in the project root with your Ethereum mainnet RPC endpoint (I used Alchemy):

```dotenv
RPC_URL=https://YOUR_RPC_ENDPOINT
EXPECTED_CHAIN_ID=1
RPC_TIMEOUT_SECONDS=10
```

## Run the API

```
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The **GET /analyze/{tx_hash}** response includes transaction details, decoded input, and any matching findings.

## Run from the terminal

```
.\venv\Scripts\python.exe -m app.rpc
```

Enter a transaction hash when prompted.

## Run tests

```
.\venv\Scripts\python.exe -m pytest tests/test_rpc.py -v
.\venv\Scripts\python.exe -m pytest tests/test_decoder.py -v
```

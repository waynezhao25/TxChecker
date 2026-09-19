import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "")

if not RPC_URL:
    raise ValueError("RPC_URL is required")

try:
    EXPECTED_CHAIN_ID = int(os.getenv("EXPECTED_CHAIN_ID", "1"))
    RPC_TIMEOUT_SECONDS = int(os.getenv("RPC_TIMEOUT_SECONDS", "10"))
    
except ValueError as exc:
    raise ValueError(
        "EXPECTED_CHAIN_ID and RPC_TIMEOUT_SECONDS must be integers"
    ) from exc

if EXPECTED_CHAIN_ID <= 0:
    raise ValueError("EXPECTED_CHAIN_ID must be positive")

if RPC_TIMEOUT_SECONDS <= 0:
    raise ValueError("RPC_TIMEOUT_SECONDS must be positive")
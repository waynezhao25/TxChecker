from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from web3.exceptions import TransactionNotFound
from app.rpc import check_connection, get_transaction_data

from app.config import EXPECTED_CHAIN_ID
from app.store import get_cached_analysis, save_analysis

from app.decoder import decode_tx
from app.rules.unlimited_approval import check_unlimited_approval
from app.rules.flagged_spender import check_flagged_spender
from app.rules.failed_transaction import check_failed_tx
from app.rules.watchlist import FLAGGED_SPENDERS

from pydantic import BaseModel
from app.models import TransactionData, RuleFinding
from app.decoder import DecodedInput


class AnalysisResponse(BaseModel):
    transaction: TransactionData
    decoded_input: DecodedInput
    findings: list[RuleFinding]

app = FastAPI(title = "TxChecker")

# Lets browser pages on other sites (like the Vercel frontend) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message" : "TxChecker API is running"}

@app.get("/analyze/{tx_hash}", response_model = AnalysisResponse)
def analyze(tx_hash: str):
    tx_hash = tx_hash.strip() 
    # checks Dynamodb for cached analysis first, if not found, makes Alchemy call.
    cached = get_cached_analysis(EXPECTED_CHAIN_ID, tx_hash)
    if cached is not None:
        print(f"cache hit: {tx_hash}")

        # turns dict from DynamoDB back into Pydantic object.
        transaction = TransactionData.model_validate(cached)
    
    else:
        print(f"cache miss: {tx_hash}")
        chain_id = check_connection()

        try:
            transaction = get_transaction_data(tx_hash, chain_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transaction hash")
        except TransactionNotFound:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Only mined transactions are saved to the cache.
        if transaction.block_number is not None:
            save_analysis(chain_id, tx_hash, transaction.model_dump(mode="json"))

    decoded = decode_tx(transaction)

    findings = []
    for finding in (
        check_unlimited_approval(transaction, decoded),
        check_flagged_spender(transaction, decoded, FLAGGED_SPENDERS),
        check_failed_tx(transaction),
    ):
        if finding is not None:
            findings.append(finding.model_dump(mode="json"))

    return {
        "transaction": transaction.model_dump(mode="json"),
        "decoded_input": decoded.model_dump(mode="json"),
        "findings": findings,
    }

from mangum import Mangum

handler = Mangum(app)

from fastapi import FastAPI, HTTPException
from web3.exceptions import TransactionNotFound
from app.rpc import check_connection, get_transaction_data

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

@app.get("/")
def home():
    return {"message" : "TxChecker API is running"}

@app.get("/analyze/{tx_hash}", response_model = AnalysisResponse)
def analyze(tx_hash: str):
    chain_id = check_connection()

    try:
        transaction = get_transaction_data(tx_hash, chain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction hash")
    except TransactionNotFound:
        raise HTTPException(status_code=404, detail="Transaction not found")

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
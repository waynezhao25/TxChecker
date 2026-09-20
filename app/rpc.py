from web3 import Web3
from app.config import EXPECTED_CHAIN_ID, RPC_TIMEOUT_SECONDS, RPC_URL
import re
from web3.exceptions import TransactionNotFound
from app.models import TransactionData
from app.decoder import decode_tx
import json
from app.rules.unlimited_approval import check_unlimited_approval
from app.rules.flagged_spender import check_flagged_spender
from app.rules.watchlist import FLAGGED_SPENDERS

w3 = Web3(Web3.HTTPProvider(
    RPC_URL, 
    request_kwargs={ "timeout": RPC_TIMEOUT_SECONDS },
    ))

def check_connection() -> int:
    chain_id = w3.eth.chain_id

    if chain_id != EXPECTED_CHAIN_ID:
        raise RuntimeError (f"Wrong network, expected {EXPECTED_CHAIN_ID}, "
                            f"received {chain_id}")

    return chain_id

def fetch_tx(tx_hash: str):
    tx_hash = tx_hash.strip()

    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", tx_hash):
        raise ValueError("Transaction does not start with 0x, with 64 hexadecimals following it.")

    return w3.eth.get_transaction(tx_hash)

def fetch_receipt(tx_hash: str):
    return w3.eth.get_transaction_receipt(tx_hash)

def tx_data_builder(tx, receipt, chain_id: int,) -> TransactionData:
    status = "unknown"

    if receipt is not None:
        if receipt["status"] == 1:
            status = "success"
        elif receipt["status"] == 0:
            status = "reverted"

    return TransactionData(
        tx_hash = Web3.to_hex(tx["hash"]),
        chain_id = chain_id,
        from_address = tx["from"],
        to_address = tx["to"],
        val_wei = tx["value"],
        block_hash = Web3.to_hex(tx["blockHash"]) if tx["blockHash"] is not None else None,
        block_number = tx["blockNumber"],
        gas_used = receipt["gasUsed"] if receipt is not None else None,
        status = status,
        
        input_data = Web3.to_hex(tx["input"]),
    )

if __name__ == "__main__":
    chain_id = check_connection()
    print(f"Connected, Chain ID: {chain_id}")

    tx_hash = input("Enter a transaction hash: ").strip()

    try:
        tx = fetch_tx(tx_hash)
    except ValueError:
        print(f"Invalid input")
    except TransactionNotFound:
        print(f"Transaction was not found")


    else:
        try:
            receipt = fetch_receipt(tx_hash)
        except TransactionNotFound:
            receipt = None
        transaction = tx_data_builder(tx, receipt, chain_id)
        decoded = decode_tx(transaction)
        findings = []
        for finding in (
            check_unlimited_approval(transaction, decoded),
            check_flagged_spender(transaction, decoded, FLAGGED_SPENDERS),
        ):
            if finding is not None:
                findings.append(finding.model_dump(mode="json"))

        print(json.dumps({
            "transaction": transaction.model_dump(mode="json"),
            "decoded_input": decoded.model_dump(mode="json"),
            "findings": findings,
        }, indent=2))

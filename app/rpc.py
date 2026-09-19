from web3 import Web3
from app.config import EXPECTED_CHAIN_ID, RPC_TIMEOUT_SECONDS, RPC_URL
import re
from web3.exceptions import TransactionNotFound
from app.models import TransactionData

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
        # turns model into readable JSON for FastAPI endpoint
        print(transaction.model_dump_json(indent=2))


        print("From:", tx["from"])
        print("To:", tx["to"])
        print("Value in wei:", tx["value"])
        print("Value in ETH:", Web3.from_wei(tx["value"], "ether"))
        print("Block:", tx["blockNumber"])
        print("Input data:", Web3.to_hex(tx["input"]))

        try:
            receipt = fetch_receipt(tx_hash)
        except TransactionNotFound:
            print("Receipt is unavailable")
        else:
            status = receipt["status"]

            if status == 1:
                print("Status: Success")
            elif status == 0:
                print("Status: Reverted")
            else:
                print("Status: Unknown")

        print("Amount of Gas used:", receipt["gasUsed"])
        print("Block number:", receipt["blockNumber"])
        print("Event logs:", receipt["logs"])

        if receipt["contractAddress"] is not None:
            print("Contract created:", receipt["contractAddress"])
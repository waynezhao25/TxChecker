from web3 import Web3
from app.config import EXPECTED_CHAIN_ID, RPC_TIMEOUT_SECONDS, RPC_URL
import re
from web3.exceptions import TransactionNotFound

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
        print("From:", tx["from"])
        print("To:", tx["to"])
        print("Value in wei:", tx["value"])
        print("Value in ETH:", Web3.from_wei(tx["value"], "ether"))
        print("Block:", tx["blockNumber"])
        print("Input data:", Web3.to_hex(tx["input"]))


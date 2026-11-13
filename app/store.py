import json
import os
import time
from typing import Any, Optional

import boto3

TABLE_NAME = os.getenv("TABLE_NAME", "")
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT") or None
_table = None

def _get_table():
    global _table
    if not TABLE_NAME:
        return None
    if _table is None:
        dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT)
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def _tx_key(chain_id: int, tx_hash: str) -> str:
    return f"TX#{chain_id}#{tx_hash.lower()}"


def get_cached_analysis(chain_id: int, tx_hash: str) -> Optional[dict[str, Any]]:
    table = _get_table()
    if table is None:
        return None

    response = table.get_item(Key={"pk": _tx_key(chain_id, tx_hash)})
    item = response.get("Item")
    if item is None:
        return None

    return json.loads(item["result"])


def save_analysis(chain_id: int, tx_hash: str, result: dict[str, Any]) -> None:
    table = _get_table()
    if table is None:
        return

    table.put_item(
        Item={
            "pk": _tx_key(chain_id, tx_hash),
            "result": json.dumps(result),
            "created_at": int(time.time()),
        }
    )

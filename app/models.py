from typing import Literal
from pydantic import BaseModel, Field

# pydantic is used to set data type constraints
class TransactionData(BaseModel):
    tx_hash: str
    chain_id: int = Field(gt=0)
    from_address: str
    to_address: str | None
    val_wei: int = Field(gt=0)
    block_hash: str | None = None
    block_number: int | None = None
    gas_used: int | None = Field(default=None, ge = 0)
    status: Literal["success", "reverted", "unknown"]

    input_data: str
    function_name: str | None = None



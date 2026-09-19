# Offline decoding of the three supported ERC-20 function signatures.

"""
Method ID (selector): first 4 bytes of input data, for example 0x095ea7b3 always means "approve" is called

Payload: everything in the input data after the 4-byte method id. Where the actual function arguments are, ABI-encoded.

ABI (Application Binary Interface): a formatter in a sense for encoding function calls. 
Defines rules like "every argument has a 32-byte slot." Caller and contract must agree on this layout for a function call 
to be understood

Padding: filler zero-bytes surrounding actual data to fit ABI's fixed 32-byte slots. Padding must be zeross

Function Signature: human readable description of a function name and argument types
e.g. "approve(address,uint256)." Method ID is derived from hashing this signature and taking the first 4 bytes

CODEC: Actually does the encode/decoding from the web3 library, knows how to translate ABI-encoded bytes into python values

Checksum Address: address string with specific letters capitalize

"""

import re
from typing import TYPE_CHECKING, Literal

from eth_abi.exceptions import DecodingError
from pydantic import BaseModel, Field
from web3 import Web3

if TYPE_CHECKING:
    from app.models import TransactionData


class DecodedInput(BaseModel):
    status: Literal["decoded", "empty", "unsupported", "contract_creation"]
    input_data: str
    method_id: str | None = None
    function_name: str | None = None
    function_signature: str | None = None
    arguments: dict[str, str | int] = Field(default_factory=dict)
    message: str


# Selector -> function name, ABI types, argument names.
_FUNCTIONS = {
    "0xa9059cbb": ("transfer", ("address", "uint256"), ("to", "value")),
    "0x095ea7b3": ("approve", ("address", "uint256"), ("spender", "value")),
    "0x23b872dd": ("transferFrom", ("address", "address", "uint256"), ("from", "to", "value"),
    ),
} 
_CODEC = Web3().codec  # No provider and no network requests.

def decode_input(input_data: str | bytes, *, is_contract_creation: bool = False) -> DecodedInput:
    """
    Decode valid calldata, accepting hex strings or bytes/HexBytes.

    Unknown selectors, payloads with wrong lengths, and invalid ABI encoding are unsupported, not malicious. 
    Known calls must have exactly the supported ABI length; extra bytes are reported as unsupported
    because contracts can accept trailing data. Caller type mistakes raise TypeError.
    """

    # allows only bytes or string
    if isinstance(input_data, bytes):
        raw = "0x" + input_data.hex()
    elif isinstance(input_data, str):
        raw = input_data
    else:
        raise TypeError("input_data must be a 0x-prefixed string or bytes")

    # string followed by 0x
    if not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", raw):
        return DecodedInput(
            status="unsupported", input_data=raw,
            message="Expected 0x followed by an even number of hexadecimal digits.",
        )

    raw = raw.lower()
    # tx with no to_address is a contract creation
    if is_contract_creation:
        return DecodedInput(
            status="contract_creation", input_data=raw,
            message="Deployment input is not decoded as a function call.",
        )
    # empty input data
    if raw == "0x":
        return DecodedInput(
            status="empty", input_data=raw,
            message="No calldata; this does not establish the recipient's account type.",
        )
    if len(raw) < 10:
        return DecodedInput(
            status="unsupported", input_data=raw,
            message="Fewer than four bytes: no full function selector (possible fallback input).",
        )

    # checks if first 4 bytes match one of the 3 known functions (transfer, approve, transferFrom)
    selector = raw[:10]
    definition = _FUNCTIONS.get(selector)
    if definition is None:
        return DecodedInput(
            status="unsupported", input_data=raw, method_id=selector,
            message="Function selector is not supported.",
        )

    name, types, names = definition
    payload = bytes.fromhex(raw[10:])
    expected_length = 32 * len(types)
    if len(payload) != expected_length:
        return DecodedInput(
            status="unsupported",
            input_data=raw, method_id=selector,
            message=f"Supported layout requires {expected_length} argument bytes; received {len(payload)}.",
        )

    try:
        # strict = True makes sure all padding bytes are 0s
        values = _CODEC.decode(types, payload, strict=True)
    except (DecodingError, ValueError):
        return DecodedInput(
            status="unsupported", input_data=raw, method_id=selector,
            message="Arguments do not satisfy the supported ABI encoding.",
        )

    arguments = {
        key: Web3.to_checksum_address(value) if abi_type == "address" else value
        for key, abi_type, value in zip(names, types, values)
    }
    return DecodedInput(
        status="decoded", input_data=raw, method_id=selector,
        function_name=name,
        function_signature=f"{name}({','.join(types)})",
        arguments=arguments,
        message=(
            "Matches a supported ERC-20 ABI layout; contract standard and execution "
            "effects are unverified. The value is a raw uint256, not a decimal-adjusted "
            "token amount. ERC-721 shares approve and transferFrom signatures."
        ),
    )


def decode_transaction(transaction: "TransactionData") -> DecodedInput:
    """Decode a normalized transaction without modifying it or fetching data."""
    return decode_input(
        transaction.input_data,
        is_contract_creation=transaction.to_address is None,
    )

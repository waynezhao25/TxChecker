import json
from types import SimpleNamespace

import pytest
from hexbytes import HexBytes

from app.decoder import decode_input, decode_transaction


ADDRESS_A = "0x" + "11" * 20
ADDRESS_B = "0x" + "22" * 20
WORD_A = "00" * 12 + "11" * 20
WORD_B = "00" * 12 + "22" * 20


def uint_word(value):
    return f"{value:064x}"


@pytest.mark.parametrize("value", [0, 1, 2**256 - 1])
@pytest.mark.parametrize(
    "selector,name,words,expected",
    [
        ("a9059cbb", "transfer", WORD_A, {"to": ADDRESS_A}),
        ("095ea7b3", "approve", WORD_A, {"spender": ADDRESS_A}),
        ("23b872dd", "transferFrom", WORD_A + WORD_B, {"from": ADDRESS_A, "to": ADDRESS_B}),
    ],
)
def test_supported_calls_preserve_full_uint256(selector, name, words, expected, value):
    result = decode_input("0x" + selector + words + uint_word(value))
    assert result.status == "decoded"
    assert result.function_name == name
    assert result.method_id == "0x" + selector
    assert result.arguments == {**expected, "value": value}
    assert json.loads(result.model_dump_json())["arguments"]["value"] == value
    assert "unverified" in result.message


@pytest.mark.parametrize("raw", ["0x", b"", HexBytes("0x")])
def test_empty_is_not_assumed_to_be_eth_transfer(raw):
    result = decode_input(raw)
    assert result.status == "empty"
    assert result.function_name is None


@pytest.mark.parametrize("raw", ["", "abcd", "0x0", "0xgg", "0x00 00", " 0x00"])
def test_bad_hex(raw):
    assert decode_input(raw).status == "malformed"


@pytest.mark.parametrize("raw", ["0x01", "0x010203", "0xdeadbeef"])
def test_unknown_and_short_input(raw):
    result = decode_input(raw)
    assert result.status == "unsupported"
    assert result.arguments == {}
    assert result.function_name is None


def test_truncated_known_call():
    assert decode_input("0xa9059cbb" + WORD_A).status == "malformed"


def test_trailing_bytes_not_silently_ignored():
    result = decode_input("0xa9059cbb" + WORD_A + uint_word(1) + "00")
    assert result.status == "unsupported"
    assert result.arguments == {}


def test_invalid_address_padding():
    invalid_word = "01" + WORD_A[2:]
    result = decode_input("0x095ea7b3" + invalid_word + uint_word(1))
    assert result.status == "malformed"


def test_bytes_hexbytes_and_uppercase_digits():
    raw = "0xa9059cbb" + WORD_A + uint_word(1234)
    expected = decode_input(raw)
    assert decode_input(bytes.fromhex(raw[2:])) == expected
    assert decode_input(HexBytes(raw)) == expected
    assert decode_input("0x" + raw[2:].upper()) == expected


def test_contract_creation_does_not_misidentify_selector():
    raw = "0x095ea7b3" + WORD_A + uint_word(1)
    tx = SimpleNamespace(input_data=raw, to_address=None)
    result = decode_transaction(tx)
    assert result.status == "contract_creation"
    assert result.function_name is None


def test_transaction_wrapper_does_not_mutate_input():
    tx = SimpleNamespace(
        input_data="0x095ea7b3" + WORD_A + uint_word(1),
        to_address=ADDRESS_B,
        function_name=None,
    )
    assert decode_transaction(tx).function_name == "approve"
    assert tx.function_name is None


def test_invalid_type_is_programming_error():
    with pytest.raises(TypeError):
        decode_input(None)


def test_signature_and_checksum_address():
    raw_address = "52908400098527886e0f7030069857d2e4169ee7"
    result = decode_input("0xa9059cbb" + "00" * 12 + raw_address + uint_word(1))
    assert result.function_signature == "transfer(address,uint256)"
    assert result.arguments["to"] == "0x52908400098527886E0F7030069857D2E4169EE7"

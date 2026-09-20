"""
Looks at a decoded transaction and decide if the approve() call grants unlimited spending permission
Creates a warning if it does, nothing if it doesnt
"""

from app.decoder import DecodedInput
from app.models import RuleFinding, TransactionData

# Unlimited ERC-20 Token approval number
MAX_UINT256 = 2**256 - 1

"""
Parameters:
    transaction: raw transaction facts (hash, addresses, status)
    decoded: result of decoder (function name, arguments)
Returns: a RuleFinding (report/warning) or None
"""
def check_unlimited_approval(transaction: TransactionData, decoded: DecodedInput) -> RuleFinding | None:
    # Only inspect successfully decoded approve calls.
    if decoded.status != "decoded" or decoded.function_name != "approve":
        return None

    amount = decoded.arguments.get("value")
    # if not max_uint256 then there is no risk
    if amount != MAX_UINT256:
        return None

    # must have some sort of risk if passed previous cases
    spender = decoded.arguments.get("spender")
    severity = "warning"
    message = "Potential unlimited token approval requested. Permission is not confirmed."

    # failed on-chain, less urgent, never took effect
    if transaction.status == "reverted":
        severity = "info"
        message = "Potential unlimited approval attempted, but the transaction reverted."

    # RuleFinding is returned if checks match
    return RuleFinding(
        rule_id="unlimited_approval",
        severity=severity,
        message=message + " Token standard is unverified; ERC-721 shares this signature.",
        evidence={
            "spender": spender,
            "amount": amount,
            "execution_status": transaction.status,
        },
    )

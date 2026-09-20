"""Flag approve calls to spenders on a user curated watchlist."""

from app.decoder import DecodedInput
from app.models import RuleFinding, TransactionData


"""
1. Checks if decoding succeeded and function is "approve"
2. Extracts the spender argument (address you're giving permission to spend your tokens)
3. Searches the watchlist for that spender on the same chain
4. Returns a finding (spender, amount, reason, tx status) if there is a match
"""
def check_flagged_spender(transaction: TransactionData, decoded: DecodedInput, watchlist: dict[tuple[int, str], str],
) -> RuleFinding | None:
    """Watchlist keys are (chain ID, address); values explain why it is listed."""
    if decoded.status != "decoded" or decoded.function_name != "approve":
        return None

    # gets spender address, if it isnt a string then returns None, preventing crashes
    spender = decoded.arguments.get("spender")
    if not isinstance(spender, str):
        return None

    # Dictionary -> {chain_id, address : reason}
    # iterates thru every entry checking if this entry chain matches our tx chain and if entry address matches spender
    # if match is never found then nothing to report.
    for (chain_id, address), reason in watchlist.items():
        if chain_id == transaction.chain_id and address.lower() == spender.lower():
            break
    else:
        return None

    # only the case if there is a watchlist match, same warnings as unlimited_approval.py
    severity = "warning"
    message = "Approval request targets a spender on the configured watchlist."

    if transaction.status == "reverted":
        severity = "info"
        message = "Approval to a watchlisted spender was attempted, but reverted."
    elif decoded.arguments.get("value") == 0:
        severity = "info"
        message = "Zero-value approval to a watchlisted spender; this may revoke an ERC-20 allowance."

    return RuleFinding(
        rule_id="flagged_spender",
        severity=severity,
        message=message + " Listing is user-configured; token standard and current permission are unverified.",
        evidence={
            "chain_id": transaction.chain_id,
            "spender": spender,
            "reason": reason,
            "amount": decoded.arguments.get("value"),
            "execution_status": transaction.status,
        },
    )

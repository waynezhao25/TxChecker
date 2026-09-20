from app.models import TransactionData, RuleFinding, Severity

"""
Report when execution is reverted
"""


def check_failed_tx(transaction:TransactionData) -> RuleFinding | None:
    if transaction.status != "reverted":
        return None

    return RuleFinding(
        rule_id = "failed_transaction", 
        severity = Severity.INFO, 
        message = "Transaction execution reverted. Gas was charged. Does not indicate malicious activity.", 
        evidence = {
            "execution_status": transaction.status,
            "gas_used": transaction.gas_used
            } 
    )

"""User-maintained spender watchlist for malicious addresses. Empty until you add your own entries."""

# Format: (chain_id, "0x...spender address..."): "Your reason for flagging it"
# Addresses are compared case-insensitively. No addresses are flagged by default.
FLAGGED_SPENDERS: dict[tuple[int, str], str] = {}

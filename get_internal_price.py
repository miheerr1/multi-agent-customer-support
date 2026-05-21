"""
Deterministic Python tool function for internal price retrieval.

Used by the Pricing Manager agent in the parallel pricing intelligence system
to look up authoritative internal prices for any valid SKU.

Why this exists as a tool function instead of an embedded price table:
1. The tool call itself becomes an auditable event in the execution trace.
2. The function is deterministic (no LLM hallucination risk on prices).
3. Mirrors production architecture (real systems pull from a database, not a prompt).
"""

# Internal price table. In production this would be a database call.
INTERNAL_PRICES = {
    "WH-1000XM5": 350.00,
    "WH-1000XM4": 280.00,
    "WF-1000XM5": 300.00,
    "MDR-XB55": 60.00,
}


def get_internal_price(sku: str) -> dict:
    """
    Return the internal price for a given SKU.

    Args:
        sku: Product SKU identifier (e.g., "WH-1000XM5")

    Returns:
        dict with keys:
            - sku: the requested SKU
            - internal_price: the authoritative price, or None if unknown
            - status: "found" or "unknown_sku"
    """
    if sku in INTERNAL_PRICES:
        return {
            "sku": sku,
            "internal_price": INTERNAL_PRICES[sku],
            "status": "found",
        }

    return {
        "sku": sku,
        "internal_price": None,
        "status": "unknown_sku",
    }


if __name__ == "__main__":
    # Quick smoke test
    print(get_internal_price("WH-1000XM5"))
    print(get_internal_price("UNKNOWN-SKU"))

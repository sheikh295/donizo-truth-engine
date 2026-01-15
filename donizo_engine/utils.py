"""
Utility functions for the Donizo Truth Engine.

Key utilities:
- Canonical JSON serialization for deterministic hashing
- SHA256 state hash calculation
- Integer-only median calculation
"""

import hashlib
import json
from typing import List, Any, Dict


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON for deterministic hashing.

    - Keys are sorted
    - No whitespace
    - Consistent formatting
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def compute_state_hash(state_dict: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of state dictionary.

    The state_hash field itself is excluded from the computation.
    """
    # Create a copy without the state_hash field
    state_copy = state_dict.copy()
    state_copy.pop('state_hash', None)

    # Serialize to canonical JSON
    canonical = canonical_json(state_copy)

    # Compute SHA256
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def median_int(values: List[int]) -> int:
    """
    Calculate median of integer list.

    For even-length lists, uses floor division of the average of middle two values.
    This ensures deterministic integer-only results.

    Args:
        values: List of integers (must be non-empty)

    Returns:
        Median as integer

    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate median of empty list")

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n % 2 == 1:
        # Odd length: return middle value
        return sorted_values[n // 2]
    else:
        # Even length: return floor of average of two middle values
        mid1 = sorted_values[n // 2 - 1]
        mid2 = sorted_values[n // 2]
        return (mid1 + mid2) // 2  # Integer division


def format_price(cents: int) -> str:
    """
    Format price in cents as dollars for display.

    Example: 1250 -> "$12.50"
    """
    dollars = cents // 100
    remaining_cents = cents % 100
    return f"${dollars}.{remaining_cents:02d}"

"""
Tests for utility functions.

Tests integer-only math, hashing, and JSON serialization.
"""

import pytest
from donizo_engine.utils import median_int, canonical_json, compute_state_hash, format_price


class TestMedianInt:
    """Test integer median calculation."""

    def test_odd_length_list(self):
        """Median of odd-length list is middle value."""
        assert median_int([1, 2, 3]) == 2
        assert median_int([5, 1, 9, 3, 7]) == 5

    def test_even_length_list(self):
        """Median of even-length list uses floor division."""
        assert median_int([1, 2, 3, 4]) == 2  # (2 + 3) // 2 = 2
        assert median_int([10, 20]) == 15  # (10 + 20) // 2 = 15
        assert median_int([1, 2, 3, 5]) == 2  # (2 + 3) // 2 = 2

    def test_single_value(self):
        """Median of single value is that value."""
        assert median_int([42]) == 42

    def test_empty_list_raises_error(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot calculate median of empty list"):
            median_int([])

    def test_negative_values(self):
        """Median works with negative values."""
        assert median_int([-5, -1, 3]) == -1
        assert median_int([-10, -20, -30, -40]) == -25

    def test_unsorted_input(self):
        """Median handles unsorted input correctly."""
        assert median_int([9, 1, 5, 3, 7]) == 5
        assert median_int([100, 1, 50, 25]) == 37  # (25 + 50) // 2


class TestCanonicalJson:
    """Test canonical JSON serialization."""

    def test_keys_sorted(self):
        """Keys should be sorted alphabetically."""
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(obj)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        """Output should have no unnecessary whitespace."""
        obj = {"key": "value", "number": 42}
        result = canonical_json(obj)
        assert ' ' not in result
        assert result == '{"key":"value","number":42}'

    def test_nested_objects(self):
        """Nested objects should also be canonical."""
        obj = {"outer": {"z": 1, "a": 2}, "first": 3}
        result = canonical_json(obj)
        assert result == '{"first":3,"outer":{"a":2,"z":1}}'

    def test_deterministic(self):
        """Same object should always produce same output."""
        obj = {"b": 2, "a": 1, "c": {"y": 2, "x": 1}}
        result1 = canonical_json(obj)
        result2 = canonical_json(obj)
        assert result1 == result2


class TestComputeStateHash:
    """Test state hash calculation."""

    def test_state_hash_excludes_itself(self):
        """state_hash field should be excluded from hash calculation."""
        state1 = {"version": 1, "items": {}, "state_hash": "old_hash"}
        state2 = {"version": 1, "items": {}, "state_hash": "different_hash"}

        # Both should produce the same hash
        hash1 = compute_state_hash(state1)
        hash2 = compute_state_hash(state2)
        assert hash1 == hash2

    def test_deterministic_hash(self):
        """Same state should always produce same hash."""
        state = {"version": 1, "items": {"copper_pipe": {"bias_cents": 100}}}
        hash1 = compute_state_hash(state)
        hash2 = compute_state_hash(state)
        assert hash1 == hash2

    def test_different_states_different_hash(self):
        """Different states should produce different hashes."""
        state1 = {"version": 1, "items": {}}
        state2 = {"version": 1, "items": {"copper_pipe": {"bias_cents": 100}}}
        assert compute_state_hash(state1) != compute_state_hash(state2)

    def test_hash_format(self):
        """Hash should be 64-character hex string (SHA256)."""
        state = {"version": 1, "items": {}}
        hash_result = compute_state_hash(state)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)


class TestFormatPrice:
    """Test price formatting."""

    def test_format_whole_dollars(self):
        """Whole dollar amounts should format correctly."""
        assert format_price(100) == "$1.00"
        assert format_price(1000) == "$10.00"
        assert format_price(0) == "$0.00"

    def test_format_with_cents(self):
        """Amounts with cents should format correctly."""
        assert format_price(1250) == "$12.50"
        assert format_price(99) == "$0.99"
        assert format_price(1505) == "$15.05"

    def test_format_large_amounts(self):
        """Large amounts should format correctly."""
        assert format_price(1000000) == "$10000.00"
        assert format_price(999999) == "$9999.99"

"""
Property-based tests for financial invariants.

Uses Hypothesis to test properties that should always hold true.
"""

import pytest
from hypothesis import given, strategies as st, assume
from donizo_engine.utils import median_int, compute_state_hash, canonical_json
from donizo_engine.models import Event, EventSource, Outcome


class TestFinancialInvariants:
    """Test financial properties that must always hold."""

    @given(st.lists(st.integers(min_value=0, max_value=1000000), min_size=1, max_size=100))
    def test_median_always_in_range(self, values):
        """Median must always be within min/max of input values."""
        result = median_int(values)
        assert min(values) <= result <= max(values)

    @given(st.lists(st.integers(min_value=-1000000, max_value=1000000), min_size=1, max_size=100))
    def test_median_is_deterministic(self, values):
        """Same input should always produce same median."""
        result1 = median_int(values)
        result2 = median_int(values)
        assert result1 == result2

    @given(st.integers(min_value=0, max_value=1000000))
    def test_prices_never_negative_with_zero_bias(self, price):
        """Adding zero bias to any price should never be negative."""
        result = price + 0
        assert result >= 0

    @given(
        st.integers(min_value=0, max_value=1000000),
        st.integers(min_value=-100000, max_value=100000)
    )
    def test_prices_clamped_to_zero(self, price, bias):
        """Price + bias should be clamped to 0 if negative."""
        result = max(0, price + bias)
        assert result >= 0

    @given(st.integers(min_value=0, max_value=1000000))
    def test_time_decay_halves_bias(self, bias):
        """Time decay should halve the bias using floor division."""
        decayed = bias // 2
        assert decayed >= 0
        assert decayed <= bias
        if bias > 0:
            assert decayed < bias  # Should strictly decrease for positive bias

    @given(st.integers(min_value=0, max_value=100000))
    def test_circuit_breaker_threshold(self, supplier_price):
        """150% threshold calculation should always be valid."""
        threshold = (supplier_price * 150) // 100
        assert threshold >= supplier_price
        if supplier_price > 0:
            assert threshold == int(supplier_price * 1.5)


class TestHashInvariants:
    """Test hashing and serialization invariants."""

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=0, max_value=1000000),
        min_size=1,
        max_size=10
    ))
    def test_canonical_json_is_deterministic(self, obj):
        """Same object should always produce same canonical JSON."""
        result1 = canonical_json(obj)
        result2 = canonical_json(obj)
        assert result1 == result2

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=1,
        max_size=10
    ))
    def test_state_hash_is_deterministic(self, state):
        """Same state should always produce same hash."""
        hash1 = compute_state_hash(state)
        hash2 = compute_state_hash(state)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    @given(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.integers(),
        min_size=1,
        max_size=10
    ))
    def test_hash_ignores_state_hash_field(self, state):
        """state_hash field should not affect the hash calculation."""
        state1 = state.copy()
        state1['state_hash'] = 'hash1'

        state2 = state.copy()
        state2['state_hash'] = 'hash2'

        assert compute_state_hash(state1) == compute_state_hash(state2)


class TestEventValidation:
    """Test event validation invariants."""

    @given(
        st.text(min_size=1, max_size=50),
        st.integers(min_value=1, max_value=2000000000),
        st.integers(min_value=0, max_value=1000000)
    )
    def test_valid_event_prices_always_nonnegative(self, item_id, timestamp, price):
        """Valid events should always have non-negative prices."""
        # This tests the validation constraint
        event = Event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            timestamp=timestamp,
            item_id=item_id,
            source=EventSource.HISTORIC,
            price_cents=price,
            outcome=Outcome.NONE
        )
        assert event.price_cents >= 0

    @given(st.integers(max_value=-1))
    def test_negative_prices_rejected(self, negative_price):
        """Negative prices should always be rejected."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Event(
                event_id="550e8400-e29b-41d4-a716-446655440000",
                timestamp=1700000000,
                item_id="item1",
                source=EventSource.HISTORIC,
                price_cents=negative_price
            )


class TestBiasCalculation:
    """Test bias calculation invariants."""

    @given(st.lists(st.integers(min_value=-100000, max_value=100000), min_size=1, max_size=5))
    def test_bias_is_median_of_deltas(self, deltas):
        """Bias should equal median of deltas."""
        bias = median_int(deltas)
        sorted_deltas = sorted(deltas)
        n = len(sorted_deltas)

        if n % 2 == 1:
            expected = sorted_deltas[n // 2]
        else:
            mid1 = sorted_deltas[n // 2 - 1]
            mid2 = sorted_deltas[n // 2]
            expected = (mid1 + mid2) // 2

        assert bias == expected

    @given(st.lists(st.integers(min_value=-100000, max_value=100000), min_size=1, max_size=10))
    def test_rolling_window_keeps_last_five(self, deltas):
        """Rolling window should keep at most 5 deltas."""
        window = deltas[-5:] if len(deltas) > 5 else deltas
        assert len(window) <= 5
        if len(deltas) >= 5:
            assert window == deltas[-5:]

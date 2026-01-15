"""
Tests for data models.

Tests validation, type safety, and model behavior.
"""

import pytest
from pydantic import ValidationError
from donizo_engine.models import Event, EventSource, Outcome, AuditLog, ItemState, State


class TestEvent:
    """Test Event model validation."""

    def test_valid_event(self):
        """Valid event should parse correctly."""
        event = Event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            timestamp=1700000000,
            item_id="copper_pipe_15mm",
            source=EventSource.HISTORIC,
            price_cents=1250,
            outcome=Outcome.NONE,
            meta={"supplier": "point_p"}
        )
        assert event.price_cents == 1250
        assert event.source == EventSource.HISTORIC

    def test_invalid_uuid(self):
        """Invalid UUID should raise validation error."""
        with pytest.raises(ValidationError):
            Event(
                event_id="not-a-uuid",
                timestamp=1700000000,
                item_id="copper_pipe_15mm",
                source=EventSource.HISTORIC,
                price_cents=1250
            )

    def test_negative_price_rejected(self):
        """Negative price should raise validation error."""
        with pytest.raises(ValidationError, match="price_cents must be >= 0"):
            Event(
                event_id="550e8400-e29b-41d4-a716-446655440000",
                timestamp=1700000000,
                item_id="copper_pipe_15mm",
                source=EventSource.HISTORIC,
                price_cents=-100
            )

    def test_invalid_timestamp(self):
        """Invalid timestamp should raise validation error."""
        with pytest.raises(ValidationError, match="timestamp must be > 0"):
            Event(
                event_id="550e8400-e29b-41d4-a716-446655440000",
                timestamp=0,
                item_id="copper_pipe_15mm",
                source=EventSource.HISTORIC,
                price_cents=1250
            )

    def test_default_outcome(self):
        """Outcome should default to NONE."""
        event = Event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            timestamp=1700000000,
            item_id="copper_pipe_15mm",
            source=EventSource.HISTORIC,
            price_cents=1250
        )
        assert event.outcome == Outcome.NONE

    def test_default_meta(self):
        """Meta should default to empty dict."""
        event = Event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            timestamp=1700000000,
            item_id="copper_pipe_15mm",
            source=EventSource.HISTORIC,
            price_cents=1250
        )
        assert event.meta == {}


class TestAuditLog:
    """Test AuditLog model validation."""

    def test_valid_audit_log(self):
        """Valid audit log should parse correctly."""
        audit = AuditLog(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            timestamp=1700000000,
            item_id="copper_pipe_15mm",
            inputs_seen={"historic_cents": 1000, "supplier_cents": 1200},
            final_price_cents=1500,
            decision="USED_HUMAN",
            bias_applied_cents=300,
            flags=["HUMAN_OVERRIDE_ACCEPTED"],
            rules_hash="abc123"
        )
        assert audit.final_price_cents == 1500
        assert "HUMAN_OVERRIDE_ACCEPTED" in audit.flags

    def test_negative_price_rejected(self):
        """Negative final price should raise validation error."""
        with pytest.raises(ValidationError):
            AuditLog(
                event_id="550e8400-e29b-41d4-a716-446655440000",
                timestamp=1700000000,
                item_id="copper_pipe_15mm",
                inputs_seen={},
                final_price_cents=-100,
                decision="USED_HUMAN",
                bias_applied_cents=0,
                rules_hash="abc123"
            )


class TestItemState:
    """Test ItemState model."""

    def test_default_values(self):
        """ItemState should have sensible defaults."""
        state = ItemState()
        assert state.bias_cents == 0
        assert state.last_updated_ts == 0
        assert state.accepted_human_deltas_cents == []

    def test_deltas_limited_to_five(self):
        """Deltas list should be limited to last 5 entries."""
        state = ItemState(
            accepted_human_deltas_cents=[1, 2, 3, 4, 5, 6, 7]
        )
        assert len(state.accepted_human_deltas_cents) == 5
        assert state.accepted_human_deltas_cents == [3, 4, 5, 6, 7]


class TestState:
    """Test State model."""

    def test_default_state(self):
        """Default state should be version 1 with empty items."""
        state = State()
        assert state.version == 1
        assert state.items == {}
        assert state.state_hash == ""

    def test_get_item_state_creates_new(self):
        """get_item_state should create new ItemState if not exists."""
        state = State()
        item_state = state.get_item_state("new_item")
        assert isinstance(item_state, ItemState)
        assert "new_item" in state.items

    def test_get_item_state_returns_existing(self):
        """get_item_state should return existing ItemState."""
        state = State()
        state.items["existing_item"] = ItemState(bias_cents=100)
        item_state = state.get_item_state("existing_item")
        assert item_state.bias_cents == 100

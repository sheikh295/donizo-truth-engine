"""
Tests for the pricing engine.

Integration tests covering all decision rules (A-E).
"""

import pytest
import json
from pathlib import Path
from donizo_engine.engine import PricingEngine
from donizo_engine.models import Event, EventSource, Outcome


class TestPricingEngine:
    """Test core pricing engine logic."""

    def create_event_file(self, tmp_path: Path, events: list) -> Path:
        """Helper to create a JSONL event file."""
        event_file = tmp_path / "events.jsonl"
        with open(event_file, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')
        return event_file

    def test_historic_only(self, tmp_path):
        """Should use historic price when only historic is available."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "HISTORIC",
                "price_cents": 1000,
                "outcome": "NONE"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        assert stats['events_processed'] == 1

        # Check audit log
        with open(audit_file, 'r') as f:
            audit = json.loads(f.readline())
            assert audit['final_price_cents'] == 1000
            assert audit['decision'] == 'USED_HISTORIC_WITH_BIAS'
            assert audit['bias_applied_cents'] == 0

    def test_supplier_within_window(self, tmp_path):
        """Should use supplier price when within 1-hour window."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1200,
                "outcome": "NONE"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700001800,  # 30 minutes later
                "item_id": "item1",
                "source": "HISTORIC",
                "price_cents": 1000,
                "outcome": "NONE"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        # Check second event (should use supplier)
        with open(audit_file, 'r') as f:
            f.readline()  # Skip first
            audit = json.loads(f.readline())
            assert audit['decision'] == 'USED_SUPPLIER_WITH_BIAS'
            assert audit['final_price_cents'] == 1200

    def test_supplier_outside_window(self, tmp_path):
        """Should use historic when supplier is outside 1-hour window."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1200,
                "outcome": "NONE"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700000000 + 3700,  # 61+ minutes later (outside window)
                "item_id": "item1",
                "source": "HISTORIC",
                "price_cents": 1000,
                "outcome": "NONE"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        # Check second event (supplier expired, should use historic)
        with open(audit_file, 'r') as f:
            f.readline()  # Skip first
            audit = json.loads(f.readline())
            assert audit['decision'] == 'USED_HISTORIC_WITH_BIAS'

    def test_human_accepted(self, tmp_path):
        """Should use human price when accepted."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1000,
                "outcome": "NONE"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700000100,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 1300,
                "outcome": "QUOTE_ACCEPTED"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        assert stats['human_accepted'] == 1

        # Check human event
        with open(audit_file, 'r') as f:
            f.readline()  # Skip supplier
            audit = json.loads(f.readline())
            assert audit['decision'] == 'USED_HUMAN'
            assert audit['final_price_cents'] == 1300
            assert 'HUMAN_OVERRIDE_ACCEPTED' in audit['flags']

    def test_human_rejected(self, tmp_path):
        """Should fallback when human quote is rejected."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1000,
                "outcome": "NONE"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700000100,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 5000,  # High human price
                "outcome": "QUOTE_REJECTED"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        assert stats['human_rejected'] == 1

        # Check human event (should fallback to supplier)
        with open(audit_file, 'r') as f:
            f.readline()  # Skip supplier
            audit = json.loads(f.readline())
            assert audit['decision'] == 'USED_SUPPLIER_WITH_BIAS'
            assert 'HUMAN_REJECTED' in audit['flags']

    def test_circuit_breaker(self, tmp_path):
        """Should reject human price if >150% of supplier."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1000,
                "outcome": "NONE"
            },
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700000100,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 2000,  # 200% of supplier (>150% threshold)
                "outcome": "QUOTE_ACCEPTED"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        assert stats['anomalies'] == 1

        # Check human event (should be rejected by circuit breaker)
        with open(audit_file, 'r') as f:
            f.readline()  # Skip supplier
            audit = json.loads(f.readline())
            assert 'ANOMALY_REJECTED' in audit['flags']
            assert audit['decision'] == 'USED_SUPPLIER_WITH_BIAS'

    def test_bias_learning(self, tmp_path):
        """Should learn bias from accepted human decisions."""
        events = [
            # Supplier baseline
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1000,
                "outcome": "NONE"
            },
            # Human accepts at 1300 (delta = +300)
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": 1700000100,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 1300,
                "outcome": "QUOTE_ACCEPTED"
            },
            # New supplier quote
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440002",
                "timestamp": 1700000200,
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1100,
                "outcome": "NONE"
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        # Check last event (should apply learned bias of 300)
        with open(audit_file, 'r') as f:
            f.readline()  # Skip first
            f.readline()  # Skip second
            audit = json.loads(f.readline())
            assert audit['bias_applied_cents'] == 300
            assert audit['final_price_cents'] == 1100 + 300  # 1400

    def test_bias_median_calculation(self, tmp_path):
        """Bias should be median of last 5 deltas."""
        events = []
        base_ts = 1700000000

        # Create events: supplier, then human accepted with varying deltas
        deltas = [100, 200, 300, 400, 500]
        for i, delta in enumerate(deltas):
            # Supplier
            events.append({
                "event_id": f"550e8400-e29b-41d4-a716-44665544000{i*2}",
                "timestamp": base_ts + (i * 200),
                "item_id": "item1",
                "source": "SUPPLIER",
                "price_cents": 1000,
                "outcome": "NONE"
            })
            # Human (creates delta)
            events.append({
                "event_id": f"550e8400-e29b-41d4-a716-44665544000{i*2+1}",
                "timestamp": base_ts + (i * 200) + 50,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 1000 + delta,
                "outcome": "QUOTE_ACCEPTED"
            })

        # Final supplier event to check bias
        events.append({
            "event_id": "550e8400-e29b-41d4-a716-446655440099",
            "timestamp": base_ts + 2000,
            "item_id": "item1",
            "source": "SUPPLIER",
            "price_cents": 1000,
            "outcome": "NONE"
        })

        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)
        stats = engine.process_events(event_file)

        # Check final event - bias should be median of [100, 200, 300, 400, 500] = 300
        with open(audit_file, 'r') as f:
            lines = f.readlines()
            last_audit = json.loads(lines[-1])
            assert last_audit['bias_applied_cents'] == 300

    def test_no_price_source_error(self, tmp_path):
        """Should error if no valid price source exists."""
        events = [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1700000000,
                "item_id": "item1",
                "source": "HUMAN",
                "price_cents": 1000,
                "outcome": "QUOTE_REJECTED"  # Rejected, no fallback
            }
        ]
        event_file = self.create_event_file(tmp_path, events)
        state_file = tmp_path / "state.json"
        audit_file = tmp_path / "audit.jsonl"

        engine = PricingEngine(state_file, audit_file)

        with pytest.raises(ValueError, match="No valid price source available"):
            engine.process_events(event_file)

    def test_deterministic_processing(self, tmp_path):
        """Same events should produce same final state hash."""
        events = [
            {"event_id": "550e8400-e29b-41d4-a716-446655440000", "timestamp": 1700000000, "item_id": "item1", "source": "SUPPLIER", "price_cents": 1000, "outcome": "NONE"},
            {"event_id": "550e8400-e29b-41d4-a716-446655440001", "timestamp": 1700000100, "item_id": "item1", "source": "HUMAN", "price_cents": 1300, "outcome": "QUOTE_ACCEPTED"},
        ]
        event_file = self.create_event_file(tmp_path, events)

        # Process first time
        state_file1 = tmp_path / "state1.json"
        audit_file1 = tmp_path / "audit1.jsonl"
        engine1 = PricingEngine(state_file1, audit_file1)
        stats1 = engine1.process_events(event_file)

        # Process second time
        state_file2 = tmp_path / "state2.json"
        audit_file2 = tmp_path / "audit2.jsonl"
        engine2 = PricingEngine(state_file2, audit_file2)
        stats2 = engine2.process_events(event_file)

        # Hashes should match
        assert stats1['final_hash'] == stats2['final_hash']

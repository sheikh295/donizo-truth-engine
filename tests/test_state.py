"""
Tests for state management.

Tests state persistence, bias updates, and time decay.
"""

import pytest
import json
from pathlib import Path
from donizo_engine.state import StateManager
from donizo_engine.models import State, ItemState


class TestStateManager:
    """Test StateManager functionality."""

    def test_load_fresh_state(self, tmp_path):
        """Loading non-existent state should return fresh state."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)
        state = manager.load()

        assert state.version == 1
        assert state.items == {}

    def test_save_and_load(self, tmp_path):
        """Saved state should be loadable with correct hash."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Modify state
        manager.state.items["test_item"] = ItemState(
            bias_cents=100,
            last_updated_ts=1700000000,
            accepted_human_deltas_cents=[50, 100, 150]
        )

        # Save
        manager.save()
        assert state_file.exists()

        # Load in new manager
        manager2 = StateManager(state_file)
        loaded_state = manager2.load()

        assert loaded_state.items["test_item"].bias_cents == 100
        assert loaded_state.items["test_item"].accepted_human_deltas_cents == [50, 100, 150]

    def test_state_hash_validation(self, tmp_path):
        """Loading state with invalid hash should raise error."""
        state_file = tmp_path / "state.json"

        # Create valid state
        manager = StateManager(state_file)
        manager.state.items["test"] = ItemState(bias_cents=100)
        manager.save()

        # Corrupt the hash
        with open(state_file, 'r') as f:
            data = json.load(f)
        data['state_hash'] = "corrupted_hash"
        with open(state_file, 'w') as f:
            json.dump(data, f)

        # Try to load
        manager2 = StateManager(state_file)
        with pytest.raises(ValueError, match="State hash mismatch"):
            manager2.load()

    def test_update_item_bias(self, tmp_path):
        """Updating bias should maintain rolling window and calculate median."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Add first delta
        manager.update_item_bias("item1", 100, 1700000000)
        assert manager.state.items["item1"].bias_cents == 100
        assert manager.state.items["item1"].accepted_human_deltas_cents == [100]

        # Add more deltas
        manager.update_item_bias("item1", 200, 1700000100)
        manager.update_item_bias("item1", 150, 1700000200)

        # Bias should be median of [100, 200, 150] = 150
        assert manager.state.items["item1"].bias_cents == 150
        assert len(manager.state.items["item1"].accepted_human_deltas_cents) == 3

    def test_update_item_bias_rolling_window(self, tmp_path):
        """Bias update should keep only last 5 deltas."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Add 7 deltas
        for i in range(7):
            manager.update_item_bias("item1", (i + 1) * 100, 1700000000 + i)

        # Should keep only last 5: [300, 400, 500, 600, 700]
        deltas = manager.state.items["item1"].accepted_human_deltas_cents
        assert len(deltas) == 5
        assert deltas == [300, 400, 500, 600, 700]

        # Bias should be median of last 5 = 500
        assert manager.state.items["item1"].bias_cents == 500

    def test_time_decay_no_decay(self, tmp_path):
        """Bias should not decay if within 7 days."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Set bias
        manager.state.items["item1"] = ItemState(
            bias_cents=1000,
            last_updated_ts=1700000000
        )

        # Check 6 days later (should not decay)
        current_ts = 1700000000 + (6 * 24 * 60 * 60)
        bias = manager.apply_time_decay("item1", current_ts)
        assert bias == 1000

    def test_time_decay_applies(self, tmp_path):
        """Bias should halve if more than 7 days old."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Set bias
        manager.state.items["item1"] = ItemState(
            bias_cents=1000,
            last_updated_ts=1700000000
        )

        # Check 8 days later (should decay)
        current_ts = 1700000000 + (8 * 24 * 60 * 60)
        bias = manager.apply_time_decay("item1", current_ts)
        assert bias == 500  # 1000 // 2

    def test_time_decay_odd_bias(self, tmp_path):
        """Odd bias should use floor division."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # Set odd bias
        manager.state.items["item1"] = ItemState(
            bias_cents=999,
            last_updated_ts=1700000000
        )

        # Check after 7+ days
        current_ts = 1700000000 + (10 * 24 * 60 * 60)
        bias = manager.apply_time_decay("item1", current_ts)
        assert bias == 499  # 999 // 2

    def test_time_decay_no_previous_update(self, tmp_path):
        """Items never updated should return current bias."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        # New item (last_updated_ts = 0)
        manager.state.items["item1"] = ItemState(bias_cents=100)

        bias = manager.apply_time_decay("item1", 1700000000)
        assert bias == 100

    def test_atomic_save(self, tmp_path):
        """Save should be atomic (temp file then rename)."""
        state_file = tmp_path / "state.json"
        manager = StateManager(state_file)

        manager.state.items["test"] = ItemState(bias_cents=100)
        manager.save()

        # Temp file should not exist after successful save
        temp_file = state_file.with_suffix('.tmp')
        assert not temp_file.exists()
        assert state_file.exists()

"""
State management for the Donizo Truth Engine.

Handles:
- Loading and saving state to JSON
- State hash calculation
- Atomic state updates
"""

import json
from pathlib import Path
from typing import Optional

from .models import State, ItemState
from .utils import compute_state_hash, canonical_json


class StateManager:
    """Manages persistent state for the pricing engine."""

    def __init__(self, state_file: Path):
        """
        Initialize state manager.

        Args:
            state_file: Path to the state JSON file
        """
        self.state_file = state_file
        self.state: State = State()

    def load(self) -> State:
        """
        Load state from file.

        If file doesn't exist, returns a fresh state.
        Validates state hash on load.

        Returns:
            Loaded state

        Raises:
            ValueError: If state file is corrupted or hash is invalid
        """
        if not self.state_file.exists():
            # Fresh state
            self.state = State()
            return self.state

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            # Validate hash
            expected_hash = data.get('state_hash', '')
            computed_hash = compute_state_hash(data)

            if expected_hash != computed_hash:
                raise ValueError(
                    f"State hash mismatch! "
                    f"Expected: {expected_hash}, Computed: {computed_hash}"
                )

            # Parse into State model
            self.state = State.model_validate(data)
            return self.state

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in state file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load state: {e}")

    def save(self) -> None:
        """
        Save state to file with updated hash.

        Atomically writes to a temporary file then renames.
        """
        # Convert to dict
        state_dict = self.state.model_dump()

        # Compute and set hash
        state_hash = compute_state_hash(state_dict)
        state_dict['state_hash'] = state_hash
        self.state.state_hash = state_hash

        # Atomic write: write to temp file then rename
        temp_file = self.state_file.with_suffix('.tmp')

        try:
            with open(temp_file, 'w') as f:
                json.dump(state_dict, f, indent=2, sort_keys=True)

            # Atomic rename
            temp_file.replace(self.state_file)

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise ValueError(f"Failed to save state: {e}")

    def get_current_hash(self) -> str:
        """Get the current state hash."""
        state_dict = self.state.model_dump()
        return compute_state_hash(state_dict)

    def update_item_bias(
        self,
        item_id: str,
        new_delta: int,
        timestamp: int
    ) -> None:
        """
        Update bias for an item by adding a new delta.

        Maintains rolling window of last 5 deltas.
        Recalculates bias as median of deltas.

        Args:
            item_id: Item identifier
            new_delta: New delta to add (human_price - supplier_price)
            timestamp: Current timestamp
        """
        from .utils import median_int

        item_state = self.state.get_item_state(item_id)

        # Add new delta (keep last 5)
        item_state.accepted_human_deltas_cents.append(new_delta)
        if len(item_state.accepted_human_deltas_cents) > 5:
            item_state.accepted_human_deltas_cents = (
                item_state.accepted_human_deltas_cents[-5:]
            )

        # Recalculate bias as median
        if item_state.accepted_human_deltas_cents:
            item_state.bias_cents = median_int(
                item_state.accepted_human_deltas_cents
            )

        # Update timestamp
        item_state.last_updated_ts = timestamp

    def apply_time_decay(self, item_id: str, current_timestamp: int) -> int:
        """
        Apply time decay to bias if needed.

        Rule D: If more than 7 days since last update, halve the bias.

        Args:
            item_id: Item identifier
            current_timestamp: Current timestamp

        Returns:
            Bias after decay (in cents)
        """
        item_state = self.state.get_item_state(item_id)

        if item_state.last_updated_ts == 0:
            return item_state.bias_cents

        # 7 days in seconds
        SEVEN_DAYS = 7 * 24 * 60 * 60

        time_diff = current_timestamp - item_state.last_updated_ts

        if time_diff > SEVEN_DAYS:
            # Apply decay: floor(bias / 2)
            decayed_bias = item_state.bias_cents // 2
            return decayed_bias

        return item_state.bias_cents

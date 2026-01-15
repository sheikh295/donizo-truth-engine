"""
Core pricing engine for the Donizo Truth Engine.

Implements "The Judge" - the decision-making logic that processes events
and determines final prices based on multiple signals.

Rules implemented:
- Rule A: Candidate selection (supplier time window)
- Rule B: Decision tree (human/supplier/historic priority)
- Rule C: Learning (bias calculation from human feedback)
- Rule D: Time decay (bias degradation)
- Rule E: Circuit breaker (anomaly detection)
"""

import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from .models import Event, AuditLog, EventSource, Outcome
from .state import StateManager


class PricingEngine:
    """
    Main pricing engine that processes events and determines prices.

    This engine is deterministic: same events + same initial state = same final state.
    """

    # Time window for supplier price eligibility (1 hour in seconds)
    SUPPLIER_WINDOW_SECONDS = 60 * 60

    # Circuit breaker threshold (150%)
    CIRCUIT_BREAKER_THRESHOLD_PERCENT = 150

    def __init__(self, state_file: Path, audit_file: Path):
        """
        Initialize pricing engine.

        Args:
            state_file: Path to state JSON file
            audit_file: Path to audit log JSONL file (output)
        """
        self.state_manager = StateManager(state_file)
        self.audit_file = audit_file

        # Load existing state or start fresh
        self.state_manager.load()

        # Tracking for supplier prices (for bias calculation)
        # Maps (item_id, timestamp) -> price_cents
        self.recent_supplier_prices: Dict[Tuple[str, int], int] = {}

        # Latest prices seen for each item (for decision making)
        self.latest_prices: Dict[str, Dict[str, Optional[int]]] = {}

        # Track timestamp of latest supplier price for each item
        self.latest_supplier_timestamp: Dict[str, int] = {}

    def process_events(self, events_file: Path) -> Dict[str, any]:
        """
        Process all events from a JSONL file.

        Args:
            events_file: Path to events.jsonl

        Returns:
            Statistics about processing (events_processed, final_hash, etc.)
        """
        events_processed = 0
        human_accepted = 0
        human_rejected = 0
        anomalies = 0

        # Open audit log for writing
        with open(self.audit_file, 'w') as audit_f:
            # Read and process events
            with open(events_file, 'r') as events_f:
                for line_num, line in enumerate(events_f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Parse event
                        event_data = json.loads(line)
                        event = Event.model_validate(event_data)

                        # Process event
                        audit_log = self._process_event(event)

                        # Track statistics
                        if 'HUMAN_OVERRIDE_ACCEPTED' in audit_log.flags:
                            human_accepted += 1
                        if 'HUMAN_REJECTED' in audit_log.flags:
                            human_rejected += 1
                        if 'ANOMALY_REJECTED' in audit_log.flags:
                            anomalies += 1

                        # Write audit log
                        audit_f.write(audit_log.model_dump_json() + '\n')

                        events_processed += 1

                    except Exception as e:
                        raise ValueError(
                            f"Error processing event on line {line_num}: {e}\n"
                            f"Event data: {line}"
                        )

        # Save final state
        self.state_manager.save()

        return {
            'events_processed': events_processed,
            'human_accepted': human_accepted,
            'human_rejected': human_rejected,
            'anomalies': anomalies,
            'final_hash': self.state_manager.get_current_hash(),
        }

    def _process_event(self, event: Event) -> AuditLog:
        """
        Process a single event and return audit log.

        This is the core decision-making logic.

        Args:
            event: Input event

        Returns:
            Audit log entry
        """
        # Initialize tracking for this item if needed
        if event.item_id not in self.latest_prices:
            self.latest_prices[event.item_id] = {
                'historic_cents': None,
                'supplier_cents': None,
                'human_cents': None,
            }

        # Update price tracking based on event source
        if event.source == EventSource.HISTORIC:
            self.latest_prices[event.item_id]['historic_cents'] = event.price_cents
        elif event.source == EventSource.SUPPLIER:
            self.latest_prices[event.item_id]['supplier_cents'] = event.price_cents
            # Store for bias calculation
            self.recent_supplier_prices[(event.item_id, event.timestamp)] = event.price_cents
            # Track timestamp for eligibility checking
            self.latest_supplier_timestamp[event.item_id] = event.timestamp
        elif event.source == EventSource.HUMAN:
            self.latest_prices[event.item_id]['human_cents'] = event.price_cents

        # Get current prices
        prices = self.latest_prices[event.item_id].copy()

        # Rule A: Check supplier eligibility (1 hour window)
        supplier_price = self._get_eligible_supplier_price(event)

        # Get bias (with time decay applied)
        bias = self.state_manager.apply_time_decay(event.item_id, event.timestamp)

        # Rule B + E: Make decision
        decision_result = self._make_decision(
            event=event,
            supplier_price=supplier_price,
            historic_price=prices['historic_cents'],
            human_price=prices['human_cents'],
            bias=bias
        )

        final_price = decision_result['final_price']
        decision = decision_result['decision']
        flags = decision_result['flags']
        bias_applied = decision_result['bias_applied']

        # Rule C: Learn from accepted human decisions
        if (event.source == EventSource.HUMAN and
                event.outcome == Outcome.QUOTE_ACCEPTED and
                'ANOMALY_REJECTED' not in flags and
                supplier_price is not None):
            # Calculate delta and update bias
            delta = event.price_cents - supplier_price
            self.state_manager.update_item_bias(
                item_id=event.item_id,
                new_delta=delta,
                timestamp=event.timestamp
            )

        # Create audit log
        audit_log = AuditLog(
            event_id=event.event_id,
            timestamp=event.timestamp,
            item_id=event.item_id,
            inputs_seen=prices,
            final_price_cents=final_price,
            decision=decision,
            bias_applied_cents=bias_applied,
            flags=flags,
            rules_hash=self.state_manager.get_current_hash()
        )

        return audit_log

    def _get_eligible_supplier_price(self, event: Event) -> Optional[int]:
        """
        Rule A: Get eligible supplier price within time window.

        Supplier price is only eligible if timestamp is within 1 hour.

        Args:
            event: Current event

        Returns:
            Supplier price in cents if eligible, None otherwise
        """
        latest_supplier = self.latest_prices[event.item_id].get('supplier_cents')

        if latest_supplier is None:
            return None

        # Get the timestamp of the latest supplier price for this item
        supplier_ts = self.latest_supplier_timestamp.get(event.item_id)

        if supplier_ts is None:
            return None

        # Check if within 1 hour window
        time_diff = abs(event.timestamp - supplier_ts)
        if time_diff <= self.SUPPLIER_WINDOW_SECONDS:
            return latest_supplier

        return None

    def _make_decision(
        self,
        event: Event,
        supplier_price: Optional[int],
        historic_price: Optional[int],
        human_price: Optional[int],
        bias: int
    ) -> Dict[str, any]:
        """
        Rule B + E: Make pricing decision based on available signals.

        Decision tree:
        1. Human + Accepted (with circuit breaker check)
        2. Human + Rejected -> fallback
        3. Non-human event -> Supplier + Bias or Historic + Bias

        Args:
            event: Current event
            supplier_price: Eligible supplier price (or None)
            historic_price: Latest historic price (or None)
            human_price: Human price if applicable (or None)
            bias: Current bias for this item

        Returns:
            Dict with final_price, decision, flags, bias_applied
        """
        flags: List[str] = []
        bias_applied = 0

        # Case 1: Human event with quote accepted
        if (event.source == EventSource.HUMAN and
                event.outcome == Outcome.QUOTE_ACCEPTED and
                human_price is not None):

            # Rule E: Circuit breaker check
            if supplier_price is not None:
                threshold = (supplier_price * self.CIRCUIT_BREAKER_THRESHOLD_PERCENT) // 100

                if human_price > threshold:
                    # Anomaly detected - reject and fallback
                    flags.append('ANOMALY_REJECTED')
                    # Fallback to supplier/historic logic
                    return self._fallback_decision(
                        supplier_price, historic_price, bias, flags
                    )

            # Human price accepted
            flags.append('HUMAN_OVERRIDE_ACCEPTED')
            return {
                'final_price': human_price,
                'decision': 'USED_HUMAN',
                'flags': flags,
                'bias_applied': 0,  # No bias when using human price directly
            }

        # Case 2: Human event with quote rejected
        if (event.source == EventSource.HUMAN and
                event.outcome == Outcome.QUOTE_REJECTED):
            flags.append('HUMAN_REJECTED')
            # Fallback to supplier/historic
            return self._fallback_decision(
                supplier_price, historic_price, bias, flags
            )

        # Case 3: Non-human event (or human with NONE outcome)
        return self._fallback_decision(
            supplier_price, historic_price, bias, flags
        )

    def _fallback_decision(
        self,
        supplier_price: Optional[int],
        historic_price: Optional[int],
        bias: int,
        flags: List[str]
    ) -> Dict[str, any]:
        """
        Fallback pricing logic: Supplier + Bias or Historic + Bias.

        Priority:
        1. Supplier price + bias (if supplier exists)
        2. Historic price + bias (if historic exists)
        3. Error (no valid price source)

        Args:
            supplier_price: Supplier price (or None)
            historic_price: Historic price (or None)
            bias: Bias to apply
            flags: Existing flags list

        Returns:
            Dict with final_price, decision, flags, bias_applied
        """
        if supplier_price is not None:
            # Use supplier + bias
            final_price = supplier_price + bias
            # Ensure non-negative
            final_price = max(0, final_price)

            return {
                'final_price': final_price,
                'decision': 'USED_SUPPLIER_WITH_BIAS',
                'flags': flags,
                'bias_applied': bias,
            }

        if historic_price is not None:
            # Use historic + bias
            final_price = historic_price + bias
            # Ensure non-negative
            final_price = max(0, final_price)

            return {
                'final_price': final_price,
                'decision': 'USED_HISTORIC_WITH_BIAS',
                'flags': flags,
                'bias_applied': bias,
            }

        # No valid price source
        raise ValueError(
            f"No valid price source available (supplier={supplier_price}, "
            f"historic={historic_price})"
        )

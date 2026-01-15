#!/usr/bin/env python3
"""
Generate synthetic test data for the Donizo Truth Engine.

Creates realistic event streams that demonstrate:
- Price conflicts between sources
- Learning curve (bias evolution)
- Time decay scenarios
- Circuit breaker triggers
- Human acceptance/rejection patterns
"""

import json
import uuid
import random
from typing import List, Dict

# Set seed for reproducibility
random.seed(42)


class EventGenerator:
    """Generate synthetic pricing events."""

    def __init__(self, start_timestamp: int = 1700000000):
        self.current_timestamp = start_timestamp
        self.events: List[Dict] = []

        # Items to track
        self.items = [
            "copper_pipe_15mm",
            "copper_pipe_22mm",
            "pvc_pipe_110mm",
            "insulation_100mm",
            "cable_2_5mm",
            "cement_bag_25kg",
            "sand_bulk_ton",
            "plasterboard_12mm",
        ]

        # Base prices (in cents)
        self.base_prices = {
            "copper_pipe_15mm": 1200,
            "copper_pipe_22mm": 1800,
            "pvc_pipe_110mm": 950,
            "insulation_100mm": 2500,
            "cable_2_5mm": 850,
            "cement_bag_25kg": 675,
            "sand_bulk_ton": 4500,
            "plasterboard_12mm": 1100,
        }

        # Suppliers
        self.suppliers = ["point_p", "travis_perkins", "jewson", "buildbase", "screwfix"]

    def advance_time(self, seconds: int):
        """Advance current timestamp."""
        self.current_timestamp += seconds

    def create_event(
        self,
        item_id: str,
        source: str,
        price_cents: int,
        outcome: str = "NONE",
        supplier: str = None
    ) -> Dict:
        """Create a single event."""
        meta = {}
        if supplier:
            meta["supplier"] = supplier

        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": self.current_timestamp,
            "item_id": item_id,
            "source": source,
            "price_cents": price_cents,
            "outcome": outcome,
            "meta": meta
        }
        self.events.append(event)
        return event

    def scenario_1_basic_learning(self):
        """
        Scenario 1: Basic learning from human decisions.

        Shows bias evolving as humans consistently price above supplier quotes.
        """
        print("Generating Scenario 1: Basic Learning...")
        item = "copper_pipe_15mm"
        base_price = self.base_prices[item]

        # Initial historic price
        self.create_event(item, "HISTORIC", base_price)
        self.advance_time(3600)

        # Series of supplier quotes with human overrides
        for i in range(5):
            # Supplier quote
            supplier_price = base_price + random.randint(-50, 50)
            self.create_event(item, "SUPPLIER", supplier_price, supplier="point_p")
            self.advance_time(300)

            # Human accepts at +200 to +400 above supplier
            human_markup = random.randint(200, 400)
            self.create_event(
                item, "HUMAN",
                supplier_price + human_markup,
                outcome="QUOTE_ACCEPTED"
            )
            self.advance_time(3600)

        # Now supplier quote should get bias applied
        for i in range(3):
            supplier_price = base_price + random.randint(-30, 30)
            self.create_event(item, "SUPPLIER", supplier_price, supplier="point_p")
            self.advance_time(7200)

    def scenario_2_circuit_breaker(self):
        """
        Scenario 2: Circuit breaker triggers.

        Shows anomalous human prices being rejected.
        """
        print("Generating Scenario 2: Circuit Breaker...")
        item = "pvc_pipe_110mm"
        base_price = self.base_prices[item]

        # Supplier baseline
        self.create_event(item, "SUPPLIER", base_price, supplier="jewson")
        self.advance_time(300)

        # Reasonable human acceptance
        self.create_event(item, "HUMAN", base_price + 100, outcome="QUOTE_ACCEPTED")
        self.advance_time(3600)

        # Another supplier quote
        self.create_event(item, "SUPPLIER", base_price + 50, supplier="jewson")
        self.advance_time(300)

        # Anomalous human price (200% of supplier - triggers circuit breaker)
        self.create_event(item, "HUMAN", (base_price + 50) * 2, outcome="QUOTE_ACCEPTED")
        self.advance_time(3600)

        # Another supplier quote
        self.create_event(item, "SUPPLIER", base_price + 25, supplier="jewson")
        self.advance_time(300)

        # Edge case: exactly at 150% threshold (should pass)
        threshold_price = ((base_price + 25) * 150) // 100
        self.create_event(item, "HUMAN", threshold_price, outcome="QUOTE_ACCEPTED")
        self.advance_time(3600)

    def scenario_3_time_decay(self):
        """
        Scenario 3: Time decay of bias.

        Shows bias degrading after 7+ days of inactivity.
        """
        print("Generating Scenario 3: Time Decay...")
        item = "insulation_100mm"
        base_price = self.base_prices[item]

        # Build up bias
        for i in range(3):
            self.create_event(item, "SUPPLIER", base_price, supplier="buildbase")
            self.advance_time(300)
            self.create_event(item, "HUMAN", base_price + 500, outcome="QUOTE_ACCEPTED")
            self.advance_time(3600)

        # Wait 8 days (time decay should trigger)
        self.advance_time(8 * 24 * 60 * 60)

        # New supplier quote (bias should be halved)
        self.create_event(item, "SUPPLIER", base_price + 100, supplier="buildbase")
        self.advance_time(3600)

        # Another long gap
        self.advance_time(10 * 24 * 60 * 60)

        # Another quote (bias halved again)
        self.create_event(item, "SUPPLIER", base_price + 50, supplier="buildbase")
        self.advance_time(3600)

    def scenario_4_human_rejection(self):
        """
        Scenario 4: Human quote rejection.

        Shows system falling back when humans reject quotes.
        """
        print("Generating Scenario 4: Human Rejection...")
        item = "cable_2_5mm"
        base_price = self.base_prices[item]

        # Historic baseline
        self.create_event(item, "HISTORIC", base_price)
        self.advance_time(3600)

        # Supplier quote
        self.create_event(item, "SUPPLIER", base_price + 100, supplier="screwfix")
        self.advance_time(300)

        # Human rejects high price
        self.create_event(item, "HUMAN", base_price + 500, outcome="QUOTE_REJECTED")
        self.advance_time(3600)

        # New supplier quote
        self.create_event(item, "SUPPLIER", base_price + 50, supplier="screwfix")
        self.advance_time(300)

        # Human accepts reasonable price
        self.create_event(item, "HUMAN", base_price + 150, outcome="QUOTE_ACCEPTED")
        self.advance_time(3600)

    def scenario_5_supplier_time_window(self):
        """
        Scenario 5: Supplier price eligibility window.

        Shows supplier prices expiring after 1 hour.
        """
        print("Generating Scenario 5: Supplier Time Window...")
        item = "cement_bag_25kg"
        base_price = self.base_prices[item]

        # Historic baseline
        self.create_event(item, "HISTORIC", base_price)
        self.advance_time(3600)

        # Supplier quote
        self.create_event(item, "SUPPLIER", base_price + 50, supplier="travis_perkins")
        self.advance_time(1800)  # 30 minutes - within window

        # Another event (should use supplier)
        self.create_event(item, "HISTORIC", base_price - 100)
        self.advance_time(3600)  # Now 90 minutes from supplier - outside window

        # Another event (should use historic, supplier expired)
        self.create_event(item, "HISTORIC", base_price + 25)
        self.advance_time(3600)

    def scenario_6_conflicting_sources(self):
        """
        Scenario 6: Conflicting price signals.

        Shows different sources giving different prices.
        """
        print("Generating Scenario 6: Conflicting Sources...")
        item = "sand_bulk_ton"
        base_price = self.base_prices[item]

        # Historic says one thing
        self.create_event(item, "HISTORIC", base_price)
        self.advance_time(3600)

        # Supplier says another (lower)
        self.create_event(item, "SUPPLIER", base_price - 500, supplier="jewson")
        self.advance_time(300)

        # Human validates supplier is right
        self.create_event(item, "HUMAN", base_price - 450, outcome="QUOTE_ACCEPTED")
        self.advance_time(7200)

        # New historic (still outdated)
        self.create_event(item, "HISTORIC", base_price)
        self.advance_time(300)

        # Supplier with learned bias
        self.create_event(item, "SUPPLIER", base_price - 480, supplier="jewson")
        self.advance_time(3600)

    def scenario_7_multiple_items(self):
        """
        Scenario 7: Multiple items being priced concurrently.

        Shows system handling multiple items independently.
        """
        print("Generating Scenario 7: Multiple Items...")

        for _ in range(540):
            # Pick random item
            item = random.choice(self.items)
            base_price = self.base_prices[item]

            # Random event type
            event_type = random.choices(
                ["HISTORIC", "SUPPLIER", "HUMAN"],
                weights=[0.3, 0.5, 0.2]
            )[0]

            if event_type == "HISTORIC":
                price = base_price + random.randint(-100, 100)
                self.create_event(item, "HISTORIC", price)

            elif event_type == "SUPPLIER":
                price = base_price + random.randint(-200, 200)
                supplier = random.choice(self.suppliers)
                self.create_event(item, "SUPPLIER", price, supplier=supplier)

            else:  # HUMAN
                price = base_price + random.randint(-100, 600)
                outcome = random.choices(
                    ["QUOTE_ACCEPTED", "QUOTE_REJECTED"],
                    weights=[0.7, 0.3]
                )[0]
                self.create_event(item, "HUMAN", price, outcome=outcome)

            # Variable time advance
            self.advance_time(random.randint(300, 7200))

    def scenario_8_realistic_workflow(self):
        """
        Scenario 8: Realistic daily workflow.

        Simulates a realistic day of pricing activity.
        """
        print("Generating Scenario 8: Realistic Workflow...")

        # Morning: historic prices loaded
        for item in self.items:
            base_price = self.base_prices[item]
            self.create_event(item, "HISTORIC", base_price)
            self.advance_time(60)

        self.advance_time(3600)

        # Throughout day: supplier quotes come in
        for _ in range(300):
            item = random.choice(self.items)
            base_price = self.base_prices[item]
            supplier = random.choice(self.suppliers)
            price = base_price + random.randint(-100, 150)
            self.create_event(item, "SUPPLIER", price, supplier=supplier)
            self.advance_time(random.randint(600, 1800))

        # Humans review and make decisions
        for _ in range(120):
            item = random.choice(self.items)
            base_price = self.base_prices[item]
            price = base_price + random.randint(100, 400)
            outcome = random.choices(
                ["QUOTE_ACCEPTED", "QUOTE_REJECTED"],
                weights=[0.75, 0.25]
            )[0]
            self.create_event(item, "HUMAN", price, outcome=outcome)
            self.advance_time(random.randint(1800, 3600))

    def generate_all(self, output_file: str = "events.jsonl"):
        """Generate all scenarios and write to file."""
        print("Generating synthetic test data...")

        self.scenario_1_basic_learning()
        self.advance_time(86400)  # 1 day gap

        self.scenario_2_circuit_breaker()
        self.advance_time(86400)

        self.scenario_3_time_decay()
        self.advance_time(86400)

        self.scenario_4_human_rejection()
        self.advance_time(86400)

        self.scenario_5_supplier_time_window()
        self.advance_time(86400)

        self.scenario_6_conflicting_sources()
        self.advance_time(86400)

        self.scenario_7_multiple_items()
        self.advance_time(86400)

        self.scenario_8_realistic_workflow()

        # Write to file
        print(f"Writing {len(self.events)} events to {output_file}...")
        with open(output_file, 'w') as f:
            for event in self.events:
                f.write(json.dumps(event) + '\n')

        print(f"Done! Generated {len(self.events)} events")
        print(f"Time span: {(self.current_timestamp - 1700000000) / 86400:.1f} days")

        # Print statistics
        sources = {}
        outcomes = {}
        for event in self.events:
            sources[event['source']] = sources.get(event['source'], 0) + 1
            outcomes[event['outcome']] = outcomes.get(event['outcome'], 0) + 1

        print("\nEvent breakdown:")
        print(f"  Sources: {sources}")
        print(f"  Outcomes: {outcomes}")
        print(f"  Unique items: {len(set(e['item_id'] for e in self.events))}")


if __name__ == "__main__":
    generator = EventGenerator()
    generator.generate_all()

#!/usr/bin/env python3
"""
Interactive menu for Donizo Truth Engine.

Provides a user-friendly CLI interface for all operations.
"""

import os
import sys
import subprocess
from pathlib import Path


class DonizoMenu:
    """Interactive menu system for Donizo Truth Engine."""

    def __init__(self):
        self.running = True
        self.data_dir = Path("/data")
        self.events_file = self.data_dir / "events.jsonl"
        self.state_file = self.data_dir / "rules_state.json"
        self.audit_file = self.data_dir / "audit_log.jsonl"

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def print_header(self):
        """Print the application header."""
        print("=" * 60)
        print("     DONIZO TRUTH ENGINE - Interactive Menu")
        print("     Version 0.1.0")
        print("=" * 60)
        print()

    def print_menu(self):
        """Print the main menu options."""
        print("\n📋 MAIN MENU:")
        print("-" * 60)
        print("  [1] 🧪 Run All Tests")
        print("  [2] 📊 Generate Test Data (1000+ events)")
        print("  [3] ▶️  Run Engine (Process Events)")
        print("  [4] 🔄 Replay Mode (Verify Determinism)")
        print("  [5] 📁 View Generated Files")
        print("  [6] 📈 Show Statistics")
        print("  [7] 🧹 Clean Generated Files")
        print("  [8] ℹ️  Help & Documentation")
        print("  [9] 🐚 Open Shell (Advanced)")
        print("  [0] 🚪 Exit")
        print("-" * 60)

    def run_tests(self):
        """Run the test suite."""
        self.clear_screen()
        self.print_header()
        print("🧪 Running Test Suite...\n")
        print("=" * 60)

        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd="/app"
            )
            print("\n" + "=" * 60)
            if result.returncode == 0:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed. Review output above.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")

        input("\nPress Enter to continue...")

    def generate_data(self):
        """Generate synthetic test data."""
        self.clear_screen()
        self.print_header()
        print("📊 Generating Synthetic Test Data...\n")
        print("=" * 60)

        try:
            # Change to data directory
            os.chdir(self.data_dir)

            result = subprocess.run(
                ["python3", "/app/generate_test_data.py"],
                cwd=str(self.data_dir)
            )

            print("\n" + "=" * 60)
            if result.returncode == 0:
                print("✅ Test data generated successfully!")
                if self.events_file.exists():
                    line_count = sum(1 for _ in open(self.events_file))
                    print(f"📄 Created: {self.events_file}")
                    print(f"📊 Events: {line_count}")
            else:
                print("❌ Data generation failed.")
        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter to continue...")

    def run_engine(self):
        """Run the pricing engine."""
        self.clear_screen()
        self.print_header()
        print("▶️  Running Pricing Engine...\n")

        # Check if events file exists
        if not self.events_file.exists():
            print("⚠️  No events.jsonl found!")
            print("   Would you like to generate test data first? (y/n): ", end="")
            if input().lower() == 'y':
                self.generate_data()
                return
            else:
                input("\nPress Enter to continue...")
                return

        print("=" * 60)
        print(f"📥 Input:  {self.events_file}")
        print(f"💾 State:  {self.state_file}")
        print(f"📝 Audit:  {self.audit_file}")
        print("=" * 60)
        print()

        try:
            result = subprocess.run([
                "donizo_engine", "run",
                "--events", str(self.events_file),
                "--state", str(self.state_file),
                "--audit", str(self.audit_file)
            ])

            print("\n" + "=" * 60)
            if result.returncode == 0:
                print("✅ Engine completed successfully!")

                # Show quick stats
                if self.audit_file.exists():
                    line_count = sum(1 for _ in open(self.audit_file))
                    print(f"📊 Processed {line_count} events")

                    # Get final hash
                    with open(self.audit_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            import json
                            last_entry = json.loads(lines[-1])
                            print(f"🔐 Final Hash: {last_entry['rules_hash'][:16]}...")
            else:
                print("❌ Engine failed. Review errors above.")
        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter to continue...")

    def replay_mode(self):
        """Run replay mode with verification."""
        self.clear_screen()
        self.print_header()
        print("🔄 Replay Mode - Determinism Verification\n")

        if not self.events_file.exists():
            print("⚠️  No events.jsonl found! Generate data first.")
            input("\nPress Enter to continue...")
            return

        if not self.state_file.exists():
            print("⚠️  No state file found! Run engine first.")
            input("\nPress Enter to continue...")
            return

        print("=" * 60)
        print("Step 1: Extracting expected hash from original run...")

        try:
            # Extract hash from audit log
            import json
            with open(self.audit_file, 'r') as f:
                lines = f.readlines()
                last_entry = json.loads(lines[-1])
                expected_hash = last_entry['rules_hash']

            # Save expected hash
            hash_file = self.data_dir / "expected_hash.txt"
            with open(hash_file, 'w') as f:
                f.write(expected_hash)

            print(f"✅ Expected hash: {expected_hash[:32]}...")
            print("\nStep 2: Running replay...")
            print("=" * 60)
            print()

            # Run replay
            replay_state = self.data_dir / "rules_state_replay.json"
            replay_audit = self.data_dir / "audit_log_replay.jsonl"

            result = subprocess.run([
                "donizo_engine", "replay",
                "--events", str(self.events_file),
                "--state", str(replay_state),
                "--audit", str(replay_audit),
                "--verify", str(hash_file)
            ])

            print("\n" + "=" * 60)
            if result.returncode == 0:
                print("✅ DETERMINISM VERIFIED!")
                print("   Replay produced identical results.")
            else:
                print("❌ Determinism check failed!")
                print("   This should not happen - please investigate.")

        except Exception as e:
            print(f"❌ Error: {e}")

        input("\nPress Enter to continue...")

    def view_files(self):
        """View generated files."""
        self.clear_screen()
        self.print_header()
        print("📁 Generated Files:\n")
        print("=" * 60)

        files = [
            ("events.jsonl", "Input event stream"),
            ("rules_state.json", "Learned pricing rules"),
            ("audit_log.jsonl", "Decision audit trail"),
            ("expected_hash.txt", "Hash for verification"),
        ]

        for filename, description in files:
            filepath = self.data_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                if filename.endswith('.jsonl'):
                    line_count = sum(1 for _ in open(filepath))
                    print(f"✅ {filename:20s} - {description:30s} ({line_count} lines, {size:,} bytes)")
                else:
                    print(f"✅ {filename:20s} - {description:30s} ({size:,} bytes)")
            else:
                print(f"❌ {filename:20s} - Not found")

        print("\n" + "=" * 60)
        print("\nOptions:")
        print("  [1] View events.jsonl (first 10 lines)")
        print("  [2] View audit_log.jsonl (last 10 lines)")
        print("  [3] View rules_state.json")
        print("  [0] Back to main menu")
        print()

        choice = input("Select option: ").strip()

        if choice == "1" and self.events_file.exists():
            print("\n--- First 10 Events ---")
            subprocess.run(["head", "-10", str(self.events_file)])
            input("\nPress Enter to continue...")
        elif choice == "2" and self.audit_file.exists():
            print("\n--- Last 10 Audit Entries ---")
            subprocess.run(["tail", "-10", str(self.audit_file)])
            input("\nPress Enter to continue...")
        elif choice == "3" and self.state_file.exists():
            print("\n--- State File ---")
            subprocess.run(["cat", str(self.state_file)])
            input("\nPress Enter to continue...")

    def show_statistics(self):
        """Show statistics about processed data."""
        self.clear_screen()
        self.print_header()
        print("📈 Statistics & Analysis\n")
        print("=" * 60)

        if not self.audit_file.exists():
            print("⚠️  No audit log found. Run the engine first.")
            input("\nPress Enter to continue...")
            return

        try:
            import json
            from collections import Counter

            decisions = []
            flags_list = []
            items = set()

            with open(self.audit_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    decisions.append(entry['decision'])
                    flags_list.extend(entry['flags'])
                    items.add(entry['item_id'])

            print(f"Total Events Processed: {len(decisions)}")
            print(f"Unique Items: {len(items)}")
            print()

            print("Decision Breakdown:")
            decision_counts = Counter(decisions)
            for decision, count in decision_counts.most_common():
                pct = (count / len(decisions)) * 100
                print(f"  {decision:30s}: {count:4d} ({pct:5.1f}%)")

            print()
            print("Flags Summary:")
            if flags_list:
                flag_counts = Counter(flags_list)
                for flag, count in flag_counts.most_common():
                    print(f"  {flag:30s}: {count:4d}")
            else:
                print("  No flags recorded")

            print()
            print("Top 5 Items by Activity:")
            item_counts = Counter()
            with open(self.audit_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    item_counts[entry['item_id']] += 1

            for item, count in item_counts.most_common(5):
                print(f"  {item:30s}: {count:4d} events")

        except Exception as e:
            print(f"❌ Error analyzing data: {e}")

        print("\n" + "=" * 60)
        input("\nPress Enter to continue...")

    def clean_files(self):
        """Clean generated files."""
        self.clear_screen()
        self.print_header()
        print("🧹 Clean Generated Files\n")
        print("=" * 60)
        print("⚠️  WARNING: This will delete all generated files!")
        print()
        print("Files that will be deleted:")

        files_to_delete = [
            "events.jsonl",
            "rules_state.json",
            "audit_log.jsonl",
            "rules_state_replay.json",
            "audit_log_replay.jsonl",
            "expected_hash.txt"
        ]

        existing_files = []
        for filename in files_to_delete:
            filepath = self.data_dir / filename
            if filepath.exists():
                existing_files.append(filepath)
                print(f"  ❌ {filename}")

        if not existing_files:
            print("  (No files to delete)")
            input("\nPress Enter to continue...")
            return

        print()
        confirm = input("Are you sure? (yes/no): ").strip().lower()

        if confirm == "yes":
            for filepath in existing_files:
                filepath.unlink()
                print(f"✅ Deleted: {filepath.name}")
            print("\n✅ Cleanup complete!")
        else:
            print("\n❌ Cleanup cancelled.")

        input("\nPress Enter to continue...")

    def show_help(self):
        """Show help and documentation."""
        self.clear_screen()
        self.print_header()
        print("ℹ️  Help & Documentation\n")
        print("=" * 60)
        print("""
WORKFLOW:
---------
1. Generate Test Data (Option 2)
   - Creates events.jsonl with 1000+ synthetic events

2. Run Engine (Option 3)
   - Processes events and creates audit log
   - Learns pricing biases from human decisions

3. Replay Mode (Option 4)
   - Verifies determinism by replaying events
   - Confirms identical results via hash matching

4. View Statistics (Option 6)
   - Analyze decisions and patterns

RULES IMPLEMENTED:
------------------
- Rule A: Supplier eligibility (1-hour window)
- Rule B: Decision tree (Human → Supplier → Historic)
- Rule C: Bias learning (median of last 5 deltas)
- Rule D: Time decay (halve after 7 days)
- Rule E: Circuit breaker (reject >150% of supplier)

FILES:
------
- events.jsonl: Input event stream
- rules_state.json: Learned pricing rules (persistent)
- audit_log.jsonl: Complete decision trail

GUARANTEES:
-----------
✓ Deterministic: Same inputs = same outputs
✓ Integer-only math: No floating-point errors
✓ Fully auditable: Every decision is logged
✓ Replayable: Cryptographic verification

For detailed documentation, see README.md
        """)
        print("=" * 60)
        input("\nPress Enter to continue...")

    def open_shell(self):
        """Open a bash shell for advanced users."""
        self.clear_screen()
        self.print_header()
        print("🐚 Opening Shell (Advanced Mode)\n")
        print("=" * 60)
        print("You are now in a bash shell.")
        print("Type 'exit' to return to the menu.")
        print("=" * 60)
        print()

        subprocess.run(["/bin/bash"])

    def run(self):
        """Main menu loop."""
        while self.running:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self.run_tests()
            elif choice == "2":
                self.generate_data()
            elif choice == "3":
                self.run_engine()
            elif choice == "4":
                self.replay_mode()
            elif choice == "5":
                self.view_files()
            elif choice == "6":
                self.show_statistics()
            elif choice == "7":
                self.clean_files()
            elif choice == "8":
                self.show_help()
            elif choice == "9":
                self.open_shell()
            elif choice == "0":
                self.clear_screen()
                print("\n" + "=" * 60)
                print("  Thank you for using Donizo Truth Engine!")
                print("=" * 60 + "\n")
                self.running = False
            else:
                print("\n❌ Invalid option. Please try again.")
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    menu = DonizoMenu()
    menu.run()

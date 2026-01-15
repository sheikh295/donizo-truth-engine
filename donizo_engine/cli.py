"""
CLI interface for the Donizo Truth Engine.

Provides two commands:
- run: Process events and generate audit log
- replay: Verify determinism by replaying events
"""

import click
from pathlib import Path
import sys


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Donizo Truth Engine - Deterministic Financial Pricing System"""
    pass


@main.command()
@click.option(
    '--events',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to events.jsonl file'
)
@click.option(
    '--state',
    type=click.Path(path_type=Path),
    required=True,
    help='Path to rules_state.json file'
)
@click.option(
    '--audit',
    type=click.Path(path_type=Path),
    required=True,
    help='Path to audit_log.jsonl file (output)'
)
def run(events: Path, state: Path, audit: Path):
    """
    Process event stream and generate audit log.

    This mode reads events, applies pricing rules, learns from human decisions,
    and outputs a complete audit trail.
    """
    from .engine import PricingEngine

    click.echo(f"Donizo Truth Engine v0.1.0")
    click.echo(f"Processing: {events}")
    click.echo(f"State file: {state}")
    click.echo(f"Audit log: {audit}")
    click.echo()

    try:
        engine = PricingEngine(state_file=state, audit_file=audit)
        stats = engine.process_events(events)

        click.echo()
        click.echo("Processing complete!")
        click.echo(f"Events processed: {stats['events_processed']}")
        click.echo(f"Human accepted: {stats['human_accepted']}")
        click.echo(f"Human rejected: {stats['human_rejected']}")
        click.echo(f"Anomalies detected: {stats['anomalies']}")
        click.echo(f"Final state hash: {stats['final_hash']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    '--events',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to events.jsonl file'
)
@click.option(
    '--state',
    type=click.Path(path_type=Path),
    required=True,
    help='Path to rules_state.json file'
)
@click.option(
    '--audit',
    type=click.Path(path_type=Path),
    required=True,
    help='Path to audit_log.jsonl file (output)'
)
@click.option(
    '--verify',
    type=click.Path(exists=True, path_type=Path),
    required=False,
    help='Path to expected_hash.txt file (optional)'
)
def replay(events: Path, state: Path, audit: Path, verify: Path):
    """
    Replay event stream and verify determinism.

    This mode processes events exactly like 'run' mode, but compares the
    final state hash against an expected value to ensure determinism.
    """
    from .engine import PricingEngine

    click.echo(f"Donizo Truth Engine v0.1.0 - REPLAY MODE")
    click.echo(f"Processing: {events}")
    click.echo(f"State file: {state}")
    click.echo(f"Audit log: {audit}")
    click.echo()

    try:
        # Load expected hash if provided
        expected_hash = None
        if verify:
            with open(verify, 'r') as f:
                expected_hash = f.read().strip()
            click.echo(f"Expected hash: {expected_hash}")
            click.echo()

        # Process events
        engine = PricingEngine(state_file=state, audit_file=audit)
        stats = engine.process_events(events)

        click.echo()
        click.echo("Replay complete!")
        click.echo(f"Events processed: {stats['events_processed']}")
        click.echo(f"Final state hash: {stats['final_hash']}")
        click.echo()

        # Verify hash if provided
        if expected_hash:
            if stats['final_hash'] == expected_hash:
                click.secho("✓ Hash verification PASSED - Determinism confirmed!", fg='green', bold=True)
                sys.exit(0)
            else:
                click.secho("✗ Hash verification FAILED - Non-deterministic behavior detected!", fg='red', bold=True)
                click.echo(f"Expected: {expected_hash}")
                click.echo(f"Got:      {stats['final_hash']}")
                sys.exit(1)
        else:
            click.echo("No expected hash provided - skipping verification")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

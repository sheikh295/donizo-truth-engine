# Donizo Truth Engine (v0.1)

A deterministic financial pricing engine that establishes "True Price" in construction markets by reconciling conflicting price signals from multiple sources.

---

## 🚀 Quick Start (Docker - No Installation Required!)

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

That's it! An interactive menu will guide you through testing, data generation, and running the engine.

👉 See [QUICKSTART.md](docs/QUICKSTART.md) for detailed quick start guide.

---

## Overview

The Donizo Truth Engine processes price events from three sources (Historical data, Supplier quotes, and Human decisions) to determine accurate pricing. The system learns from validated human decisions while maintaining strict financial integrity, determinism, and full auditability.

### Key Features

- **Deterministic Processing**: Same inputs + same code = exact same results
- **Financial Safety**: Integer-only math (no floating-point errors)
- **Learning System**: Adapts pricing bias from human feedback
- **Time Decay**: Safely degrades outdated biases
- **Circuit Breakers**: Rejects anomalous prices automatically
- **Full Auditability**: Complete decision trail for every price
- **Replay Verification**: Cryptographic proof of determinism

---

## Installation Options

### Option 1: Docker (Recommended - Zero Installation)

**No Python, no dependencies, no setup required!**

```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

See [QUICKSTART.md](docs/QUICKSTART.md) for details.

---

### Option 2: Local Installation (For Development)

**Python 3.10+ required.**

```bash
# Clone repository
git clone <repository-url>
cd donizo-test-task

# Create virtual environment (Python best practice)
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Verify installation
donizo_engine --help
```

**Alternative: Use Makefile for easier setup:**
```bash
# Create venv
make venv

# Activate venv (manual)
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install everything
make install
```

**Deactivate virtual environment when done:**
```bash
deactivate
```

---

## Quick Start (Local)

### Generate Test Data

```bash
# Generate 1000+ synthetic events
python3 generate_test_data.py

# Or use Make
make generate-data
```

### Run the Engine

```bash
# Process events
donizo_engine run --events events.jsonl --state rules_state.json --audit audit_log.jsonl

# Or use Make
make run
```

### Verify Determinism

```bash
# Replay and verify hash
donizo_engine replay --events events.jsonl --state rules_state.json --audit audit_log.jsonl --verify expected_hash.txt

# Or use Make
make replay
```

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                  Donizo Truth Engine                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────┐           │
│  │ Event Stream │──────│ Pricing      │           │
│  │ (JSONL)      │      │ Engine       │           │
│  └──────────────┘      │ "The Judge"  │           │
│                        └──────┬───────┘           │
│                               │                    │
│  ┌──────────────┐      ┌──────┴───────┐           │
│  │ State        │◄─────│ State        │           │
│  │ File (JSON)  │      │ Manager      │           │
│  └──────────────┘      └──────────────┘           │
│                               │                    │
│  ┌──────────────┐             │                    │
│  │ Audit Log    │◄────────────┘                    │
│  │ (JSONL)      │                                  │
│  └──────────────┘                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Events from `events.jsonl` (Historic, Supplier, or Human prices)
2. **Processing**: Engine applies decision rules (A-E)
3. **Learning**: Updates bias based on accepted human decisions
4. **Output**: Audit log with full decision context
5. **Persistence**: State saved with SHA256 hash for verification

---

## Decision Rules

### Rule A: Candidate Selection
- **Supplier prices**: Valid only within 1-hour window
- **Historic prices**: Always valid if present
- **Human prices**: Valid only for current human event

### Rule B: Decision Tree

```
┌─────────────────────────────────────────┐
│ Human Event + Quote Accepted?          │
├─────────────────────────────────────────┤
│ Yes → Use Human Price (check Rule E)   │
│ No  → Continue to fallback              │
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│ Supplier Price Available (within 1hr)? │
├─────────────────────────────────────────┤
│ Yes → Supplier Price + Bias            │
│ No  → Historic Price + Bias             │
└─────────────────────────────────────────┘
```

### Rule C: Learning (Bias Update)

When a human quote is accepted:
1. Calculate `delta = human_price - supplier_price`
2. Append delta to rolling window (keep last 5)
3. Update `bias = median(last 5 deltas)`

### Rule D: Time Decay

If more than 7 days since last update:
- `bias = floor(bias / 2)`

### Rule E: Circuit Breaker

If `human_price > 150% of supplier_price`:
- Mark as `ANOMALY_REJECTED`
- Fallback to supplier/historic
- **Do not learn from this event**

---

## File Formats

### Input: events.jsonl

Each line is a JSON event:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1700000000,
  "item_id": "copper_pipe_15mm",
  "source": "HISTORIC",
  "price_cents": 1250,
  "outcome": "NONE",
  "meta": {"supplier": "point_p"}
}
```

**Fields:**
- `event_id`: UUID v4
- `timestamp`: Unix timestamp (seconds)
- `item_id`: Item identifier
- `source`: `HISTORIC | SUPPLIER | HUMAN`
- `price_cents`: Price in cents (integer)
- `outcome`: `NONE | QUOTE_ACCEPTED | QUOTE_REJECTED`
- `meta`: Optional metadata

### Output: audit_log.jsonl

Each line records a decision:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1700000000,
  "item_id": "copper_pipe_15mm",
  "inputs_seen": {
    "historic_cents": 1000,
    "supplier_cents": 1200,
    "human_cents": null
  },
  "final_price_cents": 1500,
  "decision": "USED_SUPPLIER_WITH_BIAS",
  "bias_applied_cents": 300,
  "flags": [],
  "rules_hash": "abc123..."
}
```

### State: rules_state.json

Persistent brain of the system:

```json
{
  "version": 1,
  "items": {
    "copper_pipe_15mm": {
      "bias_cents": 300,
      "last_updated_ts": 1700000000,
      "accepted_human_deltas_cents": [250, 300, 350, 280, 320]
    }
  },
  "state_hash": "sha256-hex-string"
}
```

---

## Running Tests

```bash
# Run all tests with coverage
pytest

# Quick tests without coverage
pytest --no-cov

# Verbose output
pytest -vv

# Or use Make
make test
make test-quick
make test-verbose
```

### Test Coverage

- **Unit Tests**: Models, utilities, state management
- **Integration Tests**: Full engine with all rules
- **Property-Based Tests**: Financial invariants using Hypothesis
- **Edge Cases**: Boundary conditions, time windows, anomalies

---

## Docker Usage

```bash
# Build image
docker build -t donizo-engine:latest .

# Or use Make
make docker-build

# Run in container
docker run --rm \
  -v $(pwd)/data:/data \
  donizo-engine:latest \
  donizo_engine run \
  --events /data/events.jsonl \
  --state /data/rules_state.json \
  --audit /data/audit_log.jsonl
```

---

## CLI Reference

### `donizo_engine run`

Process event stream and generate audit log.

**Options:**
- `--events PATH`: Path to events.jsonl (required)
- `--state PATH`: Path to rules_state.json (required)
- `--audit PATH`: Path to output audit_log.jsonl (required)

**Example:**
```bash
donizo_engine run \
  --events events.jsonl \
  --state rules_state.json \
  --audit audit_log.jsonl
```

### `donizo_engine replay`

Replay events and verify determinism.

**Options:**
- `--events PATH`: Path to events.jsonl (required)
- `--state PATH`: Path to rules_state.json (required)
- `--audit PATH`: Path to output audit_log.jsonl (required)
- `--verify PATH`: Path to expected_hash.txt (optional)

**Example:**
```bash
donizo_engine replay \
  --events events.jsonl \
  --state rules_state.json \
  --audit audit_log.jsonl \
  --verify expected_hash.txt
```

---

## Development

### Project Structure

```
donizo-test-task/
├── donizo_engine/          # Main package
│   ├── __init__.py
│   ├── models.py          # Pydantic data models
│   ├── utils.py           # Utilities (hashing, median)
│   ├── state.py           # State management
│   ├── engine.py          # Core pricing engine
│   └── cli.py             # CLI interface
├── tests/                  # Test suite
│   ├── test_utils.py
│   ├── test_models.py
│   ├── test_state.py
│   ├── test_engine.py
│   └── test_properties.py
├── generate_test_data.py  # Synthetic data generator
├── requirements.txt        # Python dependencies
├── setup.py               # Package configuration
├── Dockerfile             # Docker build
├── Makefile              # Build automation
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```

### Adding New Rules

1. Update `engine.py` with new decision logic
2. Add corresponding tests in `tests/test_engine.py`
3. Update audit log flags if needed
4. Regenerate test data to demonstrate new behavior

### Code Quality

- **Type Hints**: All functions use type annotations
- **Validation**: Pydantic models enforce constraints
- **Error Handling**: Comprehensive validation at boundaries
- **Documentation**: Docstrings for all public APIs

---

## Financial Safety Guarantees

### Integer-Only Math

All monetary values are stored and processed as **cents** (integers). This eliminates floating-point rounding errors that could compound over time.

```python
# ✓ CORRECT
price_cents = 1250  # $12.50
bias_cents = 300    # $3.00
final = price_cents + bias_cents  # 1550 ($15.50)

# ✗ WRONG (never done)
price = 12.50
bias = 3.00
final = price + bias  # Floating point!
```

### Determinism Verification

The state hash ensures reproducibility:

```bash
# Run 1
donizo_engine run --events events.jsonl --state state1.json --audit audit1.jsonl
# Final hash: abc123...

# Run 2 (same events)
donizo_engine run --events events.jsonl --state state2.json --audit audit2.jsonl
# Final hash: abc123... (identical!)
```

### Auditability

Every decision is fully traceable:
- What inputs were considered?
- Which rule was applied?
- What was the bias at that moment?
- What was the system state hash?

---

## Performance

### Benchmarks

- **Processing**: ~10,000 events/second (single-threaded)
- **Memory**: Linear with unique items (not event count)
- **State File**: O(items), typically <1MB for 1000s of items

### Scaling Considerations

- Events processed sequentially (determinism requirement)
- State updates are atomic
- Audit log is append-only
- No external dependencies (database, cache, etc.)

---

## Troubleshooting

### Hash Mismatch on Replay

**Symptom**: Replay mode shows different state hash

**Causes:**
- Events file modified between runs
- Non-deterministic code introduced
- State file manually edited

**Solution:**
- Ensure events.jsonl is unchanged
- Check for any randomness in code
- Delete state file and rerun from scratch

### Invalid Event Format

**Symptom**: JSON parsing errors during processing

**Causes:**
- Malformed JSON in events.jsonl
- Invalid UUID format
- Negative prices
- Missing required fields

**Solution:**
- Validate events file with JSON linter
- Check event schema in documentation
- Review error message for line number

---
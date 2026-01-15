# Donizo Truth Engine (V0.1)
**Technical Test – Founding Engineer**  
**Duration:** 1 Week  
**Language:** Python (implementation choice)

---

## 1. Context & Goal

We are building the **“Bloomberg for Construction”** — a system that establishes the **True Price** of work in a chaotic market.

The goal of this pilot is to prove the ability to build a **deterministic financial core** that:
- Converges toward truth from conflicting signals (Suppliers vs. History vs. Humans)
- Evolves safely over time
- Maintains strict auditability and replay guarantees

---

## 2. Non‑Negotiables

- **Language:** Rust or Python  
- **Money:** Integers only (cents). **No floating‑point math**
- **Determinism:** Same inputs + same code → **exact same state hash**
- **Persistence:** State must persist between runs (system learns)
- **Production Quality:** No shortcuts on validation or error handling

---

## 3. Data Model

### A. Input – Event Stream (`events.jsonl`)

Each line is a JSON object:

```json
{
  "event_id": "uuid-v4-string",
  "timestamp": 1700000000,
  "item_id": "copper_pipe_15mm",
  "source": "HISTORIC",
  "price_cents": 1250,
  "outcome": "NONE",
  "meta": { "supplier": "point_p" }
}
```

**Notes**
- `source`: `HISTORIC | SUPPLIER | HUMAN`
- `outcome`: Only meaningful when source is `HUMAN`
  - `NONE | QUOTE_ACCEPTED | QUOTE_REJECTED`

---

### B. Output – Audit Log (`audit_log.jsonl`)

One record per processed event:

```json
{
  "event_id": "uuid-from-input",
  "timestamp": 1700000000,
  "item_id": "copper_pipe_15mm",
  "inputs_seen": {
    "historic_cents": 1000,
    "supplier_cents": 1200,
    "human_cents": 1500
  },
  "final_price_cents": 1500,
  "decision": "USED_HUMAN",
  "bias_applied_cents": 300,
  "flags": ["HUMAN_OVERRIDE_ACCEPTED"],
  "rules_hash": "sha256-of-current-state-file"
}
```

Purpose: **Full explainability and replay proof**.

---

### C. State – The Brain (`rules_state.json`)

```json
{
  "version": 1,
  "items": {
    "copper_pipe_15mm": {
      "bias_cents": 300,
      "last_updated_ts": 1700000000,
      "accepted_human_deltas_cents": [300, 250, 400, 200, 350]
    }
  },
  "state_hash": "sha256-of-this-json-content-excluding-hash-field"
}
```

**Key Rules**
- `accepted_human_deltas_cents`: Rolling window of last 5 accepted deltas
- `state_hash`: SHA256 hash of canonical JSON (excluding itself)

---

## 4. Core Algorithm – “The Judge”

### Rule A – Candidate Selection

- **Supplier:** Eligible if timestamp is within **1 hour**
- **Historic:** Always eligible if present
- **Human:** Eligible only when current event source is `HUMAN`

---

### Rule B – Decision Tree

1. **Human + Accepted**
   - Final Price = Human Price
   - Update Bias (Rule C)

2. **Human + Rejected**
   - Ignore Human Price
   - Fallback to Supplier/Historic logic
   - Flag: `HUMAN_REJECTED`

3. **Non‑Human Event**
   - Supplier + Bias (if eligible)
   - Else Historic + Bias
   - Else fallback/error

---

### Rule C – Learning (Bias Update)

Triggered only when:
- Human quote is accepted
- Valid supplier price exists

Steps:
1. `Delta = Human - Supplier`
2. Append delta (keep last 5)
3. `Bias = Median(last 5 deltas)`

---

### Rule D – Time Decay

Before applying bias:
- If `current_time - last_updated_ts > 7 days`
- Then: `bias = floor(bias / 2)`

---

### Rule E – Circuit Breaker

If:
- `Human Price > 150% of Supplier Price`

Then:
- Mark `ANOMALY_REJECTED`
- Treat as rejected
- **Do not learn from this event**

---

## 5. CLI Interface

### Run Mode

```bash
./donizo_engine run   --events events.jsonl   --state rules_state.json   --audit audit_log.jsonl
```

### Replay Verification Mode

```bash
./donizo_engine replay   --events events.jsonl   --state rules_state.json   --audit audit_log.jsonl   --verify expected_hash.txt
```

Replay must produce **exact same final state hash**.

---

## 6. Deliverables

1. Private GitHub repository
2. Dockerfile or Makefile
3. Synthetic `events.jsonl` (≥1000 events) demonstrating:
   - Conflicts
   - Learning curve
   - Time decay
   - Circuit breaker

---

## 7. Evaluation Rubric

- Determinism (Pass/Fail)
- Financial Safety (Integers only)
- Architecture clarity
- Property‑based tests (e.g. price ≥ 0)

---

## Mental Model

This engine behaves like a **deterministic pricing brain**:
- Humans establish truth
- Suppliers anchor reality
- History provides fallback
- Bias learns slowly and decays safely
- Every decision is auditable and replayable

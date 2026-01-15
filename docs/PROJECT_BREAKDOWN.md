# Donizo Truth Engine - Project Breakdown & Proposal

## Executive Summary

This project involves building a deterministic financial pricing engine that establishes "True Price" in construction markets by reconciling conflicting price signals from multiple sources (historical data, supplier quotes, and human decisions). The system learns from validated decisions while maintaining strict financial integrity and full auditability.

**Timeline:** 1 Week
**Core Technology:** Python
**Complexity Level:** High (Financial Systems + Machine Learning + Event Sourcing)

---

## What We're Building

A **production-grade pricing brain** that:
- Processes price signals from 3 sources (Historic, Supplier, Human)
- Learns pricing biases from accepted human decisions
- Maintains deterministic, auditable financial calculations
- Decays learned biases safely over time
- Prevents anomalous prices through circuit breakers

---

## Core Components

### 1. Event Processing Engine
**Purpose:** Ingests and validates event streams from JSONL files

**Key Requirements:**
- Parse JSON events with strict validation
- Handle 3 event types: HISTORIC, SUPPLIER, HUMAN
- Process events sequentially in timestamp order
- Validate UUID, timestamp, and pricing data integrity

**Complexity:** Medium

---

### 2. Decision Engine ("The Judge")
**Purpose:** Determines final price using rule-based logic

**Key Logic:**
- **Supplier Eligibility:** Only prices within 1 hour window
- **Human Decisions:** Process QUOTE_ACCEPTED vs QUOTE_REJECTED outcomes
- **Fallback Chain:** Human → Supplier+Bias → Historic+Bias
- **Circuit Breaker:** Reject prices >150% of supplier baseline

**Complexity:** High (critical business logic)

---

### 3. Learning System (Bias Calculation)
**Purpose:** Learns market patterns from validated human decisions

**Algorithm:**
- Calculate delta between accepted human price and supplier price
- Maintain rolling window of last 5 deltas per item
- Apply median of deltas as bias to future prices
- Implement time decay (7-day threshold, halve bias)

**Complexity:** Medium-High

---

### 4. State Management System
**Purpose:** Persistent storage of learned biases and system state

**Requirements:**
- JSON-based state file (`rules_state.json`)
- Per-item bias tracking with timestamps
- SHA256 state hashing for determinism verification
- Atomic read/write operations

**Complexity:** Medium

---

### 5. Audit Trail System
**Purpose:** Full explainability and replay capability

**Output:**
- Record every decision with all input signals
- Document which rule was applied
- Track bias values at decision time
- Link to state hash for verification

**Complexity:** Medium

---

### 6. Replay & Verification System
**Purpose:** Cryptographic proof of determinism

**Features:**
- Replay mode that reprocesses all events
- State hash comparison against expected values
- Guarantee: Same inputs + same code = same hash

**Complexity:** High (critical for trust)

---

## Technical Requirements (Non-Negotiables)

### Financial Safety
- **Integer-only math** (all prices in cents)
- No floating-point operations
- Prevents rounding errors and financial inconsistencies

### Determinism
- Same event stream must produce identical results
- State hash verification
- Reproducible across environments

### Production Quality
- Comprehensive input validation
- Error handling for malformed data
- Property-based tests (e.g., prices always ≥ 0)
- No shortcuts on edge cases

---

## Deliverables

### 1. Core Application
- CLI tool with `run` and `replay` commands
- Event processor with validation
- Decision engine with all 5 rules implemented
- State persistence system
- Audit log generation

### 2. Test Data
- Synthetic `events.jsonl` with 1000+ events
- Demonstrates all scenarios:
  - Conflicting price signals
  - Learning curve over time
  - Time decay of biases
  - Circuit breaker triggers
  - Human accept/reject outcomes

### 3. Infrastructure
- Dockerfile OR Makefile for reproducible builds
- Clear setup instructions
- Dependency management

### 4. Testing Suite
- Unit tests for each component
- Property-based tests for financial invariants
- Integration tests for full event processing
- Replay verification tests

### 5. Documentation
- README with setup instructions
- Architecture overview
- Algorithm explanations
- Example usage

---

## Work Breakdown Structure

### Phase 1: Foundation (Days 1)
- [ ] Project setup and structure
- [ ] Data models (Event, AuditLog, State)
- [ ] JSON parsing and validation
- [ ] Integer-only money handling utilities
- [ ] Basic CLI interface

### Phase 2: Core Logic (Days 1)
- [ ] Candidate selection (Rule A)
- [ ] Decision tree implementation (Rule B)
- [ ] Bias learning algorithm (Rule C)
- [ ] Time decay logic (Rule D)
- [ ] Circuit breaker (Rule E)

### Phase 3: State & Audit (Day 2)
- [ ] State persistence system
- [ ] SHA256 hashing for determinism
- [ ] Audit log generation
- [ ] Replay mode implementation

### Phase 4: Testing & Data (Day 2)
- [ ] Comprehensive test suite
- [ ] Synthetic event generation (1000+ events)
- [ ] Replay verification
- [ ] Property-based tests

### Phase 5: Polish & Delivery (Day 2)
- [ ] Dockerfile/Makefile
- [ ] Documentation
- [ ] Final testing
- [ ] Code review and cleanup

---

## Key Technical Challenges

### 1. Deterministic State Hashing
**Challenge:** JSON key ordering can vary across languages
**Solution:** Canonical JSON serialization before hashing

### 2. Time Window Logic
**Challenge:** Supplier price eligibility (1-hour window)
**Solution:** Careful timestamp comparison with timezone handling

### 3. Median Calculation on Integers
**Challenge:** Median of even-length arrays may need rounding
**Solution:** Floor division or consistent rounding strategy

### 4. Concurrent State Updates
**Challenge:** Multiple events for same item
**Solution:** Sequential processing with atomic state writes

### 5. Replay Verification
**Challenge:** Ensuring bit-identical results
**Solution:** No timestamps in output, fixed seed for any randomness

---

## Quality Assurance Strategy

### Property-Based Tests
- All prices must be ≥ 0
- Bias must be within reasonable bounds
- State hash must be reproducible
- Audit log must have 1:1 mapping with events

### Edge Cases to Test
- Empty event stream
- Events with missing fields
- Extreme price values
- Events exactly at 1-hour boundary
- State file corruption scenarios
- Events out of order

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Floating-point math accidentally used | High | Code review + type hints + tests |
| Non-deterministic behavior | High | Replay tests on every commit |
| State corruption | Medium | Validation on load + backup strategy |
| Performance with large event files | Low | Stream processing + benchmarking |
| Complex debugging of pricing decisions | Medium | Rich audit logs with all context |

---

## Success Criteria

1. **Determinism Test:** Replay produces identical state hash
2. **Financial Integrity:** No floating-point math anywhere
3. **Learning Demonstration:** Synthetic data shows bias evolution
4. **Edge Case Coverage:** All circuit breaker and decay scenarios tested
5. **Production Readiness:** Comprehensive validation and error handling

---

## Next Steps

To proceed with this project, I recommend:

1. **Confirm Approach:** Review this breakdown and adjust priorities
2. **Setup Repository:** Initialize Git repo with proper structure
3. **Begin Implementation:** Start with Phase 1 (Foundation)
4. **Daily Check-ins:** Review progress and adjust course
5. **Final Review:** Code review before submission

---

## Questions for Clarification

1. **Python Version:** Any preference (3.10+, 3.11+, 3.12+)?
2. **Dependencies:** Are external libraries allowed (e.g., pytest, click)?
3. **Time Zones:** Should timestamps be UTC or timezone-aware?
4. **State File:** How to handle missing/corrupted state on first run?
5. **Event Ordering:** Can we assume events are pre-sorted by timestamp?

---

**Prepared By:** [Your Name]
**Date:** January 14, 2026
**Estimated Delivery:** 7 days from approval

---
id: ADR-005
type: adr
title: Storage of the per-stat below-threshold clock
description: Whether the per-stat below-threshold clock the neglect progression runs on is reconstructed from the decay curve at each evaluation or introduced as a new persisted pet-state field.
traces_from: [FR-008]
traces_to: {}
status: draft
confidence: low
created_at: '2026-08-24'
decision_status: proposed
considered_options:
- Reconstructed from the decay curve at each evaluation
- Introduced as a new persisted pet-state field
---

# ADR-005: Storage of the per-stat below-threshold clock

## Context and Problem Statement

The undecided question is unchanged and remains genuinely undecided: FR-008 needs a per-stat below-threshold clock running unbroken across an application close, the glossary's Pet state entry — the single maintained enumeration of what is persisted — carries no such field, and whether that clock is reconstructed from the decay curve at each evaluation or introduced as a new persisted field is tracked under an open question. The health-progression component and its contract both state the deferral in their own confidence notes rather than papering over it, and the progression operation deliberately exposes no way to read that clock precisely because its existence is undecided. The coverage that does exist is real: health status has exactly one writer, which carries the deadline rule in its operation summary and consumes the wall clock directly so the rule is named at its own point of consumption, and the running-cadence half now obtains its tick from inside the adapter layer. None of that settles the storage decision, which the requirement's own significance calls structural and not settled by any requirement.

## Decision Drivers

- FR-008

## Considered Options

### Reconstructed from the decay curve at each evaluation

- Pros: Adds no field to the maintained enumeration of what is persisted, so the persisted field set, the round-trip measure and the field set integrity validation must account for all stay as they are; and no backward-clock observation becomes a mutation of persisted state.
- Cons: Makes the neglect clock a function of the decay curve, so any re-tuning of the balance parameters silently rewrites how long a pet has already been neglected — a balance change that quietly moves a health-status transition. It also leaves the deadline rule with little to act on, since an origin derived from the current stat value cannot read as being in the future.

### Introduced as a new persisted pet-state field

- Pros: The clock is an explicit recorded origin rather than a derived quantity, so it is independent of the decay curve and survives a re-tuning of the balance parameters unchanged.
- Cons: Adds a field to the single maintained enumeration of what is persisted, widening the component's field set, the round-trip measure and the field set validation must account for; and because the deadline rule re-bases the origin, every backward-clock observation becomes a mutation of persisted pet state, which is a new class of write on a path the business rules require to be inspected exhaustively.

## Decision Outcome

Pending. No option has been chosen. The question is owned by engineering and is tracked as open question Q-11, the design-side refinement of the still-open cadence question Q-10 that governs it; the decomposition is correct under either answer, which is why the decision could be deferred rather than forced. The claim most worth re-examining when it is taken is the progression contract's assertion that the deadline rule survives either answer.

### Consequences

- None — the decision is pending.

---
id: IF-006
type: interface
title: Pet Lifecycle State
description: The contract through which components learn the pet's current lifecycle state and are told when it transitions, including the terminal state after which no care action may take effect.
traces_from:
- FR-007
- FR-008
- NFR-003
- NFR-007
- BR-001
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: 2026-07-30
scope: project
parent_scope: null
provider: CMP-004
operations:
- name: current_lifecycle_state
  summary: Return the pet's current lifecycle state, including whether it has reached the terminal dead state.
- name: subscribe_to_transitions
  summary: Register to be notified when the lifecycle state transitions, receiving the prior state, the new state, and the instant of the transition.
interaction: synchronous
error_modes:
- Lifecycle state queried before the session has been seeded — no state exists to report, and the caller must not assume a healthy default.
- Transition notification missed — a subscriber that misses one must re-query the current state rather than inferring it from the transitions it did see, because the terminal state is irreversible and cannot be reconstructed from a partial sequence.
- Transition observed out of order relative to the Stat changes that caused it — the two notification streams are not interleaved, so a consumer must not derive one from the other.
---

# IF-006 — Pet Lifecycle State

The contract through which components learn the pet's current lifecycle state and are
told when it transitions, including the terminal state after which no care action may
take effect.

## Operations
- **current_lifecycle_state** — Return the pet's current lifecycle state, including
  whether it has reached the terminal dead state.
- **subscribe_to_transitions** — Register to be notified when the lifecycle state
  transitions, receiving the prior state, the new state, and the instant of the
  transition.

## Interaction
Synchronous, and this is the closest call in the set — the three consumers want
opposite things from one contract. CMP-003 must know the lifecycle state *before* it
mutates a Stat, because the Q-2 resolution makes death permanent and no restorative
arithmetic may run after it; that is a blocking read on the write path and it decides
the enum value here. CMP-005 and CMP-006 want the opposite: a push, so that a
transition reaches the mood mapping and the window without polling under NFR-002.
Both are on the contract, and the interaction is recorded as synchronous because the
correctness-critical use is the blocking one — a missed push shows a stale mood for a
moment, a missed gate revives a dead pet. What would tip it to asynchronous is moving
the death gate into CMP-003 itself as cached state, at the cost of two components
holding the same terminal flag and a window in which they disagree.

## Error Modes
- Lifecycle state queried before the session has been seeded — no state exists to
  report, and the caller must not assume a healthy default.
- Transition notification missed — a subscriber that misses one must re-query the
  current state rather than inferring it from the transitions it did see, because the
  terminal state is irreversible and cannot be reconstructed from a partial sequence.
- Transition observed out of order relative to the Stat changes that caused it — the
  two notification streams are not interleaved, so a consumer must not derive one from
  the other.

## Rationale
Satisfies the identically declared lifecycle-observation capability of CMP-003,
CMP-005 and CMP-006: the state manager gating mutations (BR-001, Q-2), the mood
evaluator because a sick or dead pet's Mood is not a function of Stats alone (FR-007),
and the window because the terminal state has to be visible and its controls
unavailable (FR-008, NFR-003). Q-1 leaves the sickness and death threshold durations
open, but those are parameters inside CMP-004, not fields on this contract — the
reason this is medium rather than low.

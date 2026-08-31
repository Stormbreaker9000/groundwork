---
id: IF-005
type: interface
title: Sleep Entry
description: The contract through which the sleep care action puts an Awake pet into the Sleeping state and stamps the sleep-entry timestamp the wake deadline is later measured from.
traces_from: [FR-006, FR-001, NFR-007]
traces_to:
  adr: [ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-006
operations:
- name: enter_sleep
  summary: Transition an Awake pet to the Sleeping state and record its sleep-entry timestamp from the current wall-clock reading; a pet already Sleeping is returned unchanged, its existing timestamp preserved.
  interaction: synchronous
error_modes:
- Host clock reading unavailable — no sleep-entry timestamp can be recorded, so the transition is refused rather than made with an absent origin that FR-011 would then have nothing to measure from.
- 'The pet is already Sleeping — not a failure: the request is idempotent and the existing sleep-entry timestamp is preserved, because re-stamping it on every repeat would extend the sleep duration indefinitely.'
- The diagnostic record for the transition cannot be written — the transition still stands; NFR-007's record is a consequence of the transition, not a precondition for it.
---

# IF-005 — Sleep Entry

The contract through which the sleep care action puts an Awake pet into the Sleeping state and
stamps the sleep-entry timestamp the wake deadline is later measured from.

## Operations
- **enter_sleep** — Transition an Awake pet to the Sleeping state and record its sleep-entry
  timestamp from the current wall-clock reading; a pet already Sleeping is returned unchanged,
  its existing timestamp preserved.

## Interaction
Synchronous. The care action installs the returned pet state as the live one and cannot
proceed without it.

One operation, and deliberately separate from IF-006's wake resolution even though the same
component provides both: the care interaction handler enters sleep and never resolves a wake,
and the evaluator resolves wakes and never enters sleep. Requirements A-8 fixes that asymmetry — the pet
leaves Sleeping on elapsed duration, not by an owner action — so the two consumer sets are
disjoint by requirement, not by accident.

## Error Modes
- Host clock reading unavailable — no sleep-entry timestamp can be recorded, so the transition
  is refused rather than made with an absent origin.
- The pet is already Sleeping — not a failure: idempotent, and the existing timestamp is
  preserved, because re-stamping on every repeat would extend the sleep duration indefinitely.
- The diagnostic record for the transition cannot be written — the transition still stands.

## Rationale
Satisfies CMP-008's declared need to put the pet into the Sleeping state, which FR-006 requires
and FR-006's fit criterion requires to be idempotent. Confidence is medium: FR-006 sits in the
inherited review queue on Q-8 (still_open — whether the Sleeping state is rendered to the
owner), but Q-8 bears on the presentation surface rather than on this transition, since the
Awake/Sleeping field is already part of pet state and needs no new contract to be displayed.

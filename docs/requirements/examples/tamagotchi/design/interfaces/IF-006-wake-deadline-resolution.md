---
id: IF-006
type: interface
title: Wake Deadline Resolution
description: The contract through which a pet-state evaluation tests a Sleeping pet's wake deadline under FR-011's re-basing rule, which differs from the clamp the same evaluation applies to decay.
traces_from: [FR-011, FR-006, NFR-007]
traces_to:
  adr: []
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
- name: resolve_wake
  summary: Test a Sleeping pet's elapsed interval since its sleep-entry timestamp against the sleep duration and return the pet Awake where the duration has been reached; where that interval computes as non-positive, re-base the sleep-entry timestamp to the current reading and leave the pet Sleeping.
  interaction: synchronous
error_modes:
- Host clock reading unavailable — the deadline cannot be tested, and the pet is left Sleeping with its timestamp untouched, deferring the wake to the next evaluation rather than waking on an unknown reading.
- A Sleeping pet carries no sleep-entry timestamp — the deadline has no origin, so the timestamp is re-based to the current reading, bounding the wake at one sleep duration instead of leaving the pet Sleeping without bound.
- The balance parameter set has not been loaded — the sleep duration is unknown and no wake can be resolved; the pet is left Sleeping.
- 'The interval computes as non-positive because the owner moved the clock backward — not a failure: the origin is re-based, which is what bounds the deadline where FR-002''s clamp alone would defer it indefinitely (A-6).'
---

# IF-006 — Wake Deadline Resolution

The contract through which a pet-state evaluation tests a Sleeping pet's wake deadline under
FR-011's re-basing rule, which differs from the clamp the same evaluation applies to decay.

## Operations
- **resolve_wake** — Test a Sleeping pet's elapsed interval since its sleep-entry timestamp
  against the sleep duration and return the pet Awake where the duration has been reached;
  where that interval computes as non-positive, re-base the sleep-entry timestamp to the
  current reading and leave the pet Sleeping.

## Interaction
Synchronous. FR-011's AC-3 requires the wake test at launch before the pet is displayed, so
the evaluation blocks on it.

This contract is one of the two places A-6's deadline rule lives — the other is IF-004's
neglect clock. IF-018 hands out a signed interval and applies neither rule; IF-003 clamps it
as a quantity; this operation and IF-004's re-base the origin as a deadline. The discriminator
has to be named wherever the interval is consumed, and these are the namings.

## Error Modes
- Host clock reading unavailable — the deadline cannot be tested and the pet is left Sleeping
  with its timestamp untouched.
- A Sleeping pet carries no sleep-entry timestamp — the origin is re-based to the current
  reading, bounding the wake at one sleep duration rather than leaving the pet Sleeping
  without bound.
- The balance parameter set has not been loaded — the sleep duration is unknown and no wake is
  resolved.
- The interval computes as non-positive because the clock moved backward — not a failure: the
  origin is re-based, which is exactly what FR-011's backward-clock trials measure.

## Rationale
Satisfies CMP-009's declared need to resolve a sleeping pet's wake deadline. Separate from
IF-005 because the consumer sets are disjoint: the care handler enters sleep and never resolves
a wake, and per A-8 no owner action wakes the pet. Confidence is medium — FR-011 is in the
inherited review queue and its own confidence is low, but the residual uncertainty is the sleep
duration's value (Q-1) and the evaluation cadence (Q-10), neither of which changes this
operation's shape.

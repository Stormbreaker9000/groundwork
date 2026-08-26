---
id: IF-003
type: interface
title: Decay Computation
description: The independently invocable computation that maps a starting pet state and a signed elapsed interval to the decayed pet state, in one bounded step.
traces_from: [FR-002, NFR-001, NFR-008, NFR-009]
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-004
operations:
- name: decay
  summary: Return the pet state produced by applying the configured decay curve to a supplied starting pet state over a supplied signed elapsed interval, in one bounded step rather than by walking the interval; an interval at or below zero is treated as zero elapsed time, so no stat value increases.
  interaction: synchronous
error_modes:
- The balance parameter set has not been loaded for this session — the decay curve is undefined and no decayed state can be produced; the computation does not load it, because doing so would put a file read inside the loop NFR-008 requires to be file-free.
- The supplied starting pet state carries a stat outside its configured bounds — rejected rather than extrapolated from, because the result would be unbounded in the same direction.
- The supplied elapsed interval exceeds the representable range — rejected rather than silently truncated, so an absurd interval cannot masquerade as a plausible one.
---

# IF-003 — Decay Computation

The independently invocable computation that maps a starting pet state and a signed elapsed
interval to the decayed pet state, in one bounded step.

## Operations
- **decay** — Return the pet state produced by applying the configured decay curve to a
  supplied starting pet state over a supplied signed elapsed interval, in one bounded step
  rather than by walking the interval; an interval at or below zero is treated as zero
  elapsed time, so no stat value increases.

## Interaction
Synchronous. FR-002 forbids the pet being displayed before decay has been applied, so the
launch path cannot proceed without the result.

One operation, deliberately. A-17 and NFR-008 require this computation to be reachable as a
single unit callable 1,000 times in a loop against an in-memory starting state, with no save
file read and no application launch. Every parameter it needs arrives as an argument or from
IF-001, and IF-001 is now a pure memory read whose source-loading half lives in IF-026 — so
the whole transitive read set of this operation touches no file. It reads no clock either.
That is what makes NFR-001's non-positive-interval matrix drivable directly against it, and
it is why FR-002's clamp lives here rather than in the caller: the clamp is part of what the
matrix tests.

## Error Modes
- The balance parameter set has not been loaded for this session — the curve is undefined and
  no decayed state is produced; this operation does not load it.
- The supplied starting pet state carries a stat outside its configured bounds — rejected
  rather than extrapolated from.
- The supplied elapsed interval exceeds the representable range — rejected rather than
  silently truncated.

## Rationale
Satisfies CMP-009's declared need to compute a decayed pet state, which FR-002 forces onto
the launch path ahead of first render and NFR-008 forbids living inside that sequence.

---
id: IF-018
type: interface
title: Host Clock Access
description: The platform-adapter contract that supplies the host's current wall-clock reading and the signed interval since a recorded timestamp, applying neither non-positive-interval rule itself.
traces_from: [FR-002, FR-006, FR-008, FR-011, NFR-001, NFR-006, NFR-007]
traces_to:
  adr: [ADR-001, ADR-002, ADR-003, ADR-005]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-017
operations:
- name: now
  summary: Return the host's current wall-clock reading.
  interaction: synchronous
- name: signed_interval_since
  summary: Return the interval between a supplied recorded timestamp and the current reading, signed — negative where the clock now reads behind that timestamp — applying neither of A-6's non-positive-interval rules, so that each consumer applies the one its own requirement names.
  interaction: synchronous
error_modes:
- The host clock is unavailable or uninitialised — no reading is returned, and every elapsed-interval computation in the product is blocked rather than proceeding from a substituted reading.
- 'The clock now reads behind the recorded timestamp — returned as a non-positive signed interval and never corrected here: a consumer driving a quantity clamps it to zero (FR-002, decay) and a consumer driving a deadline additionally re-bases its origin (FR-011''s wake, FR-008''s neglect clock).'
- The host smooths backward clock movement into slow-forward time, so no non-positive interval is ever observed — A-7 is unmet, both of A-6's rules are silently defeated, and the condition is not detectable through this contract.
- A recorded timestamp arrives that the host clock cannot represent — rejected rather than returning an interval derived from a truncated value.
---

# IF-018 — Host Clock Access

The platform-adapter contract that supplies the host's current wall-clock reading and the signed
interval since a recorded timestamp, applying neither non-positive-interval rule itself.

## Operations
- **now** — Return the host's current wall-clock reading.
- **signed_interval_since** — Return the interval between a supplied recorded timestamp and the
  current reading, signed — negative where the clock now reads behind that timestamp — applying
  neither of A-6's non-positive-interval rules, so that each consumer applies the one its own
  requirement names.

## Interaction
Both synchronous. A clock reading has no meaning delivered later than it was asked for.

The deliberate omission is the design content here. A-6 carries two incompatible rules over the
same reading: FR-002 clamps a non-positive interval to zero because it drives a quantity, and
FR-011 additionally re-bases its origin because it drives a deadline. A contract that exposed one
"elapsed since" would have to pick one and would silently give the other consumer the wrong
answer, so this contract hands back the sign and applies neither.

Every consumer of the signed interval now names its rule at the point of consumption. IF-003
clamps. IF-006 re-bases the sleep-entry origin. IF-004 re-bases the per-stat below-threshold
origin — the third consumer, added this round, and previously the one that read the interval
through its caller and named no rule at all. IF-012 and IF-015 use `now` for timestamping and
read no interval. The correctness of all of it rests on A-7 — that the host exposes backward
movement observably rather than smoothing it away — which this contract cannot itself verify.

## Error Modes
- The host clock is unavailable or uninitialised — no reading returned; every elapsed-interval
  computation is blocked rather than proceeding from a substituted reading.
- The clock reads behind the recorded timestamp — returned as a non-positive signed interval and
  never corrected here.
- The host smooths backward movement, so no non-positive interval is ever observed — A-7 unmet,
  both rules defeated, and undetectable through this contract.
- A recorded timestamp the host clock cannot represent — rejected rather than truncated.

## Rationale
Satisfies the identical capability declared by CMP-005 (FR-008's per-stat below-threshold clock),
CMP-006 (sleep-entry stamping and the wake deadline), CMP-009 (every evaluation), CMP-012 (the
last-saved timestamp on every commit) and CMP-015 (every diagnostic record's timestamp).
Distinct from IF-024, which is the raw OS reading the adapter itself consumes: this contract adds
the signed-interval derivation and is the only clock the rest of the codebase sees, which is what
keeps the platform-specific reading inside the adapter layer NFR-006 names.

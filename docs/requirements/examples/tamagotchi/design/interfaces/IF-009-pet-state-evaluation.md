---
id: IF-009
type: interface
title: Pet-State Evaluation
description: The contract through which the pet's state is re-derived from the current wall-clock reading — decay applied, health status advanced, wake deadline tested, mood re-selected — and installed.
traces_from: [FR-002, FR-007, FR-008, FR-009, FR-011, NFR-001, NFR-007, NFR-009]
traces_to:
  adr: [ADR-001, ADR-005]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-009
operations:
- name: evaluate
  summary: 'Perform one pet-state evaluation: read the current wall-clock reading, apply elapsed decay from the last-saved timestamp, advance health status for sustained neglect, resolve any wake deadline, re-select the mood expression, raise any warranted care reminders, and install the re-derived pet state as the live one.'
  interaction: synchronous
error_modes:
- Host clock reading unavailable — no evaluation is performed and the live pet state is left as it stands, rather than derived from a substituted reading.
- A stage of the derivation fails — decay, health advancement or wake resolution — and the evaluation is abandoned without installing a partially derived pet state, so the pet never advances through half a derivation.
- The re-derived pet state cannot be installed or its commit fails — the evaluation is reported as not applied, because a display refreshed from an uncommitted derivation would show a pet the next launch cannot reproduce.
- 'The elapsed interval since the last-saved timestamp computes as non-positive — not a failure: decay contributes exactly zero and both deadline consumers re-base their origins, so no stat increases (FR-002) and no deadline is deferred without bound (FR-011, FR-008).'
- The evaluation completes but the redraw it asks for fails — the evaluation still stands, because the state has already been installed and committed; the owner sees a stale view until the next redraw succeeds.
---

# IF-009 — Pet-State Evaluation

The contract through which the pet's state is re-derived from the current wall-clock reading —
decay applied, health status advanced, wake deadline tested, mood re-selected — and installed
as the live pet state.

## Operations
- **evaluate** — Perform one pet-state evaluation: read the current wall-clock reading, apply
  elapsed decay from the last-saved timestamp, advance health status for sustained neglect,
  resolve any wake deadline, re-select the mood expression, raise any warranted care reminders,
  and install the re-derived pet state as the live one.

## Interaction
Synchronous. The launch sequence must not display the pet until the evaluation has completed
(FR-002, FR-011 AC-3), and NFR-009 measures a window that closes at first render — a window
that only exists if the evaluation completes before it.

One operation, and the same one for both consumers. A launch evaluation and a cadence
evaluation are the same derivation over a different elapsed interval; splitting them would put
two subtly different derivations in the codebase, which is precisely what FR-008's continuity
across an application close forbids. What differs between the two callers is what happens
*after*: the launch path goes on to first display (IF-017), the cadence does not, and the
evaluation itself asks for a redraw (IF-030) either way.

## Error Modes
- Host clock reading unavailable — no evaluation is performed and the live state is left as it
  stands.
- A stage of the derivation fails — the evaluation is abandoned without installing a partially
  derived pet state.
- The re-derived state cannot be installed or its commit fails — reported as not applied.
- The elapsed interval computes as non-positive — not a failure: decay contributes zero and
  both deadline consumers re-base their origins.
- The redraw the evaluation asks for fails — the evaluation still stands; the state is already
  installed and committed, and the owner sees a stale view until the next redraw succeeds.

## Rationale
Satisfies the identical capability declared by CMP-010 (the running cadence) and CMP-011 (the
launch path). This is the one place the two non-positive-interval rules of A-6 meet: the
evaluation passes the signed interval to IF-003, which clamps it, and to IF-006 and IF-004,
which re-base against it, and applies neither rule itself.

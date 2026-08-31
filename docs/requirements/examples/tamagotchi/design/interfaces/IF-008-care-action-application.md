---
id: IF-008
type: interface
title: Care Action Application
description: The contract through which the owner's selection of one of the four care-loop interactions is applied to the current pet.
traces_from: [FR-003, FR-004, FR-005, FR-006, FR-001, FR-007, NFR-003]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-008
operations:
- name: feed
  summary: Raise the pet's hunger stat by the configured feed increment, capped at the stat's maximum, and install the result as the live pet state.
  interaction: synchronous
- name: play
  summary: Raise the pet's happiness stat by the configured play increment, capped at the stat's maximum, and install the result as the live pet state.
  interaction: synchronous
- name: clean
  summary: Raise the pet's hygiene stat by the configured clean increment, capped at the stat's maximum, and install the result as the live pet state.
  interaction: synchronous
- name: put_to_sleep
  summary: Put the pet into the Sleeping state and install the result as the live pet state; already-Sleeping pets are left unchanged.
  interaction: synchronous
error_modes:
- The targeted stat is already at its maximum — the action completes with the stat unchanged, which FR-003, FR-004 and FR-005 each require explicitly; the caller must not announce a change that did not occur (NFR-003).
- The live pet state cannot be replaced, or its durable commit fails — the care action is reported as not applied, because a view showing a fed pet whose state never reached disk is the failure NFR-004's measure is written to catch.
- The balance parameter set has not been loaded — the interaction's increment is unknown and no care action can be applied.
- The sleep action is selected for an already-Sleeping pet — accepted and idempotent, leaving both the Awake/Sleeping field and the sleep-entry timestamp unchanged (FR-006).
---

# IF-008 — Care Action Application

The contract through which the owner's selection of one of the four care-loop interactions is
applied to the current pet.

## Operations
- **feed** — Raise the hunger stat by the configured feed increment, capped at maximum, and
  install the result as the live pet state.
- **play** — Raise the happiness stat by the configured play increment, capped at maximum, and
  install the result.
- **clean** — Raise the hygiene stat by the configured clean increment, capped at maximum, and
  install the result.
- **put_to_sleep** — Put the pet into the Sleeping state and install the result;
  already-Sleeping pets are left unchanged.

## Interaction
All four synchronous. NFR-003 requires the state change a care action causes to be announced
as text through the platform accessibility API, and an announcement can only follow a result
the caller has been given. The announcement itself happens through IF-027, from the surface
that called this contract.

Four operations, not one action-typed operation. The care loop is a fixed set of exactly four
(requirements A-8 forbids a fifth), each named by its own requirement with its own configured increment, and
NFR-003's scripted screen-reader walkthrough exercises them one by one. Naming them separately
is what lets FR-003, FR-004, FR-005 and FR-006 trace to distinct operations rather than to one
switch statement.

## Error Modes
- The targeted stat is already at maximum — the action completes with the stat unchanged, which
  each of FR-003/4/5 requires explicitly; the caller must not announce a change that did not
  occur.
- The live pet state cannot be replaced, or its commit fails — the action is reported as not
  applied.
- The balance parameter set has not been loaded — the increment is unknown and no action can be
  applied.
- Sleep selected for an already-Sleeping pet — accepted and idempotent.

## Rationale
Satisfies CMP-016's declared need to apply an owner-selected care-loop action, keeping the four
interactions as domain behaviour rather than as logic inside the presentation surface.

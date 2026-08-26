---
id: CMP-010
type: component
title: Evaluation Scheduler
description: The recurring driver that causes a pet-state evaluation to happen on the running application's own cadence, with a bounded period.
traces_from: [FR-007, FR-008, FR-011, NFR-002, NFR-006]
traces_to:
  adr: [ADR-001, ADR-003, ADR-004, ADR-005, ADR-006]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Drives recurring pet-state evaluation while the application is running.
boundary: internal
depends_on: [IF-009, IF-031]
---

# CMP-010 — Evaluation Scheduler

The recurring driver that causes a pet-state evaluation to happen on the running
application's own cadence, with a bounded period.

## Responsibility
Drives recurring pet-state evaluation while the application is running.

## Rationale
FR-011 makes the pet's state advance with no owner input at all, which forces a
recurring driver to exist as its own unit rather than as a side effect of rendering —
a pet asleep behind a static window must still wake. NFR-002 is the counter-force: it
budgets "whatever background timer machinery the chosen implementation uses" at idle,
so the period is a first-class architectural parameter rather than an implementation
detail, and isolating it in one component is what lets it be tuned against the budget
without touching the derivation.

The recurring timer itself is not held here. NFR-006 enumerates "wall-clock and timer
access" in one clause as platform-touching seams that belong to the platform-adapter
layer, so this component consumes timer access from that layer the way every other
component consumes platform behaviour. That is also what gives it a structural way to
observe a timer facility that cannot be established, and to report it rather than
leaving the caller assuming a live pet.

Confidence is low: Q-10 — how often the running application re-evaluates pet state and
what bounds that interval — is still_open, and NFR-002, the constraint that would bound
it from the other side, is not evaluable until Q-5 records a reference machine.

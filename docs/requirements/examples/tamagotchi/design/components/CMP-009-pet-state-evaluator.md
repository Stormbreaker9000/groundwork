---
id: CMP-009
type: component
title: Pet State Evaluator
description: The single occasion on which the system reads the current wall clock and re-derives the pet's state from it — applying elapsed decay, advancing health status and testing the wake deadline.
traces_from: [FR-002, FR-007, FR-008, FR-011, NFR-001, NFR-007, NFR-009]
traces_to:
  adr: [ADR-001, ADR-005]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Performs a pet-state evaluation, re-deriving the current pet state from the wall clock.
boundary: internal
depends_on: [IF-002, IF-003, IF-004, IF-006, IF-007, IF-015, IF-016, IF-018, IF-030]
---

# CMP-009 — Pet State Evaluator

The single occasion on which the system reads the current wall clock and re-derives
the pet's state from it — applying elapsed decay, advancing health status and testing
the wake deadline.

## Responsibility
Performs a pet-state evaluation, re-deriving the current pet state from the wall clock.

## Rationale
Pet-state evaluation is a named concept in the glossary, and FR-007's mood update,
FR-008's neglect progression and FR-011's wake all presuppose one (A-23). Giving it a
component means the launch path and the running cadence drive the same derivation
rather than two divergent ones, which is what makes FR-011's "including trials where
the duration elapses entirely while the application is closed" the same code path as
the in-session case.

This component composes; it does not compute. Decay, progression and the wake deadline
each live in their own unit, which is what NFR-008's direct-invocation constraint and
BR-001's single-writer rule require. It emits NFR-007's one record per decay
computation, and it derives that record's delta field itself, by differencing the
pre-state it supplied to CMP-004 against the decayed state CMP-004 handed back —
CMP-004 returns a state, not deltas, and holding both ends is what lets this component
produce the field NFR-007's replay check is defined over. Doing the differencing here
also keeps the decay computation free of the log, so NFR-008's thousand-repetition
measure times the computation alone.

Confidence is medium: the shape is settled, but what an evaluation must do about
FR-008's below-threshold clock depends on the still_open Q-10 decision recorded against
CMP-005.

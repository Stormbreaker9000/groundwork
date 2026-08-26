---
id: CMP-001
type: component
title: Pet State Model
description: The canonical in-memory representation of a pet state — every pet stat value, the health status, the Awake/Sleeping state field, the sleep-entry timestamp and the last-saved timestamp — together with the invariants those values must satisfy.
traces_from: [FR-001, FR-003, FR-004, FR-005, FR-010, NFR-001]
traces_to:
  adr: [ADR-001, ADR-003]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Owns the pet state representation and its invariants, including construction of a default pet.
boundary: internal
depends_on: [IF-001]
---

# CMP-001 — Pet State Model

The canonical in-memory representation of a pet state — every pet stat value, the
health status, the Awake/Sleeping state field, the sleep-entry timestamp and the
last-saved timestamp — together with the invariants those values must satisfy.

## Responsibility
Owns the pet state representation and its invariants, including construction of a
default pet.

## Rationale
The glossary's Pet state entry is the single maintained enumeration of what the
application persists (A-22), and FR-001 requires every one of those fields to
round-trip unchanged; giving that enumeration one owner is what makes the round-trip
testable as a property of a type rather than of a serialiser. The same owner holds
the stat bounds that make FR-003, FR-004 and FR-005's "up to the stat's maximum
value" true at every write, not only at the care action. FR-010's default pet is a
particular instance of this model, so its construction belongs here rather than on
the recovery path.

Confidence is medium rather than high because FR-008's per-stat below-threshold clock
may require a new persisted field (see CMP-005); that decision, tied to Q-10, changes
this component's field set and A-22's enumeration with it.

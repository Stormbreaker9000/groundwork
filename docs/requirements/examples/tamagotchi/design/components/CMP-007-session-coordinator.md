---
id: CMP-007
type: component
title: Session Coordinator
description: The composition root that runs the application's launch and shutdown sequence, wiring the restored state, the elapsed interval, and the live simulation together in the correct order.
traces_from:
- FR-001
- FR-002
- FR-010
- NFR-001
- NFR-004
- NFR-007
- CON-001
- BR-002
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
responsibility: Owns the order in which the pet is restored at launch, caught up to the present, and committed at shutdown.
boundary: internal
depends_on:
- IF-001
- IF-002
- IF-003
- IF-004
- IF-009
---

# CMP-007 — Session Coordinator

The composition root that runs the application's launch and shutdown sequence,
wiring the restored state, the elapsed interval, and the live simulation together
in the correct order.

## Responsibility
Owns the order in which the pet is restored at launch, caught up to the present,
and committed at shutdown.

## Rationale
FR-002's "when the application starts" is an ordering requirement, and orderings
need an owner. Load, then measure the elapsed interval, then evaluate Decay, then
seed the live state, then show the window — get that sequence wrong and the pet is
either shown stale or saved before it is caught up. FR-010 rides on the same path:
a missing or unreadable save must divert to a default pet without terminating, and
the divert belongs where the sequence lives. NFR-001's demand that the clock be an
injected dependency is honoured here by making the interval an argument passed
through the sequence rather than an ambient call inside the Decay computation, and
CON-001 places this component on the native side of the process boundary with the
rest of the simulation.

Confidence is **medium**: no requirement names a coordinator, so the seam is
inferred from the launch-time ordering FR-002 and FR-010 jointly imply. It is sound,
but the boundary between what this component sequences and what CMP-003 does for
itself rests on inference rather than on stated requirement text.

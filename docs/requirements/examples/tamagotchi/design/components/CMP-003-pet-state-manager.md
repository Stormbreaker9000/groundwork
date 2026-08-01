---
id: CMP-003
type: component
title: Pet State Manager
description: The in-memory custodian of the pet's live Stat values during a session, and the only path through which those values change.
traces_from:
- FR-002
- FR-003
- FR-004
- FR-005
- FR-006
- FR-001
- NFR-002
- NFR-007
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Owns the pet's current Stat values as the single in-session authority over them.
boundary: internal
depends_on:
- IF-001
- IF-002
- IF-003
- IF-004
- IF-006
---

# CMP-003 — Pet State Manager

The in-memory custodian of the pet's live Stat values during a session, and the
only path through which those values change.

## Responsibility
Owns the pet's current Stat values as the single in-session authority over them.

## Rationale
FR-003 through FR-006 are four different arithmetic rules over the same four Stats —
feed raises hunger-satisfaction by an increment, play raises happiness, clean resets
cleanliness to maximum, sleep restores energy over a duration — and every one of
them has the same invariants: never below zero, never above maximum, never applied
to a dead pet. Giving each action its own component would scatter those invariants
across four places, so they collapse into one custodian instead. The same custodian
is where in-session Decay lands (FR-002's model applied to live values) and where
FR-001's save trigger fires, because a Stat change is the event both requirements
key off. NFR-002's idle budget is why this component is timer- and event-driven and
holds only the small live Stat set rather than an in-process store.

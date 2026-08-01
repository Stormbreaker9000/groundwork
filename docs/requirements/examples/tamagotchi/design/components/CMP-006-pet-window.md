---
id: CMP-006
type: component
title: Pet Window
description: The system-webview surface the owner sees — the pet's rendered Mood, its Stat readouts, and the controls through which the owner acts on it.
traces_from:
- FR-003
- FR-004
- FR-005
- FR-006
- FR-007
- NFR-002
- NFR-003
- NFR-006
- CON-001
- CON-003
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
responsibility: Presents the pet to the owner and turns the owner's input into care actions.
boundary: internal
depends_on:
- IF-005
- IF-006
- IF-007
- IF-008
- IF-010
---

# CMP-006 — Pet Window

The system-webview surface the owner sees — the pet's rendered Mood, its Stat
readouts, and the controls through which the owner acts on it.

## Responsibility
Presents the pet to the owner and turns the owner's input into care actions.

## Rationale
CON-001 makes this a process boundary rather than a layering preference: excluding
runtimes that bundle a browser engine fixes the topology as a native core plus an
OS-supplied webview, so the simulation sits on one side of the seam and everything
the owner sees sits on the other. NFR-002's <=1% idle CPU budget then constrains
what this side may do — no continuous animation or polling loop, and a quiescent or
absent window when unfocused. NFR-003 is satisfied here in its rendering half:
every control keyboard-reachable and named, every Mood distinguishable without
colour, using the named value CMP-005 supplies. NFR-006 and CON-003 are why this is
one shared surface rather than a native view per platform.

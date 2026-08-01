---
id: CMP-008
type: component
title: Care Reminder Scheduler
description: The watcher that decides when the owner should be reminded to care for the pet, and the holder of whether the owner wants reminders at all.
traces_from:
- FR-009
- NFR-002
- NFR-006
- CON-003
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
responsibility: Decides when a care reminder is due for the owner.
boundary: internal
depends_on:
- IF-005
- IF-011
- IF-012
---

# CMP-008 — Care Reminder Scheduler

The watcher that decides when the owner should be reminded to care for the pet, and
the holder of whether the owner wants reminders at all.

## Responsibility
Decides when a care reminder is due for the owner.

## Rationale
FR-009 is the only requirement that crosses the process boundary outward, and it is
the sole reason an external element appears in this architecture at all. Keeping
the *decision* (a care Stat crossed its warning threshold, reminders are enabled,
the owner has not just been told) separate from the *delivery* is what lets the one
platform-specific egress path stay isolated: on the platforms staged after v1 per
CON-003 and NFR-006, delivery can be absent without this component or anything
below it changing. NFR-002 keeps the watch event-driven rather than polled.

Confidence is **medium**: FR-009 is a `could`-priority requirement and its warning
thresholds are configuration the requirement set does not fix, so the component is
sound but its triggering detail rests on inference.

---
id: IF-005
type: interface
title: Pet Stat Observation
description: The contract through which components read the pet's current Stat values and are told when those values change, without any of them being able to set one.
traces_from:
- FR-007
- FR-008
- FR-009
- NFR-002
- NFR-003
- BR-001
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
provider: CMP-003
operations:
- name: current_stats
  summary: Return the pet's Stat values as a single consistent snapshot taken at one instant, rather than value by value.
- name: subscribe_to_stat_changes
  summary: Register to be notified whenever a Stat value changes, receiving the new snapshot and the instant of the change.
interaction: asynchronous
error_modes:
- Notification observed after a further change — a subscriber may act on a snapshot that is already stale, so the most recent notification is authoritative and an older one must never be re-applied.
- Subscriber slow or unresponsive — notifications are coalesced or dropped rather than queued without bound, and the subscriber must be able to recover by taking a fresh snapshot.
- Stats read before the session has been seeded — no snapshot exists yet, and the caller must handle that window rather than reading zeroed values as if they were real.
- Stale subscription outliving its subscriber — a registration whose owner is gone must be discarded rather than delivered to, or the idle process keeps doing work NFR-002 has no budget for.
---

# IF-005 — Pet Stat Observation

The contract through which components read the pet's current Stat values and are
told when those values change, without any of them being able to set one.

## Operations
- **current_stats** — Return the pet's Stat values as a single consistent snapshot
  taken at one instant, rather than value by value.
- **subscribe_to_stat_changes** — Register to be notified whenever a Stat value
  changes, receiving the new snapshot and the instant of the change.

## Interaction
Asynchronous. Four components declared this capability as "track ... as they change",
and NFR-002's <= 1% idle CPU budget forbids each of them polling for it: FR-007's
one-second expression update and FR-009's one-minute reminder latency both have to be
met by being told, not by asking. The snapshot read exists for recovery and for the
first read after seeding, not as the normal path. What makes this medium rather than
high: the push mechanism is inferred from the budget, not declared. The consumers on
the webview side of the Tauri process boundary (CMP-006) receive these notifications
over an IPC hop that the in-process consumers do not, which is a latency asymmetry
FR-007's one-second bound has to absorb.

## Error Modes
- Notification observed after a further change — a subscriber may act on a snapshot
  that is already stale, so the most recent notification is authoritative and an
  older one must never be re-applied.
- Subscriber slow or unresponsive — notifications are coalesced or dropped rather
  than queued without bound, and the subscriber must be able to recover by taking a
  fresh snapshot.
- Stats read before the session has been seeded — no snapshot exists yet, and the
  caller must handle that window rather than reading zeroed values as if they were
  real.
- Stale subscription outliving its subscriber — a registration whose owner is gone
  must be discarded rather than delivered to, or the idle process keeps doing work
  NFR-002 has no budget for.

## Rationale
Satisfies the identically declared stat-observation capability of CMP-004, CMP-005,
CMP-006 and CMP-008 — the lifecycle manager watching for sustained depletion
(FR-008, BR-001), the mood evaluator deriving an expression (FR-007), the window
showing the values, and the reminder scheduler watching for a warning-threshold
crossing (FR-009). Four consumers, one provider, one contract. Read-only by
construction: mutation goes through IF-008 so that CMP-003 stays the single authority
over its own values.

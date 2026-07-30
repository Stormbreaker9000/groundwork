---
id: IF-009
type: interface
title: Session State Seeding
description: The contract through which the launch sequence installs the restored and caught-up pet state — or a fresh default pet — as the live in-session values, once, before anything observes them.
traces_from:
- FR-001
- FR-002
- FR-010
- NFR-001
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
provider: CMP-003
operations:
- name: seed_from_snapshot
  summary: Install a restored, decay-adjusted set of Stat values as the live in-session state, before any consumer observes or mutates it.
- name: seed_defaults
  summary: Install a fresh default pet as the live in-session state, for the case where no valid saved state exists.
interaction: synchronous
error_modes:
- Seeding attempted a second time in one session — live values would be replaced underneath existing observers, so the second attempt must be refused rather than silently applied.
- Supplied snapshot fails validation — Stat values outside the valid range must be rejected rather than installed, because every later computation is anchored to them.
- The session is observed before it is seeded — reads and subscriptions must have defined behaviour in that window rather than racing it, which is the same unseeded window IF-005 and IF-006 report.
---

# IF-009 — Session State Seeding

The contract through which the launch sequence installs the restored and caught-up pet
state — or a fresh default pet — as the live in-session values, once, before anything
observes them.

## Operations
- **seed_from_snapshot** — Install a restored, decay-adjusted set of Stat values as the
  live in-session state, before any consumer observes or mutates it.
- **seed_defaults** — Install a fresh default pet as the live in-session state, for the
  case where no valid saved state exists.

## Interaction
Synchronous. CMP-007 owns the order in which the pet is restored, caught up, and shown,
and the window must not be presented until seeding has returned; an asynchronous seed
would reintroduce exactly the unseeded-observation race the operation exists to close.

## Error Modes
- Seeding attempted a second time in one session — live values would be replaced
  underneath existing observers, so the second attempt must be refused rather than
  silently applied.
- Supplied snapshot fails validation — Stat values outside the valid range must be
  rejected rather than installed, because every later computation is anchored to them.
- The session is observed before it is seeded — reads and subscriptions must have
  defined behaviour in that window rather than racing it, which is the same unseeded
  window IF-005 and IF-006 report.

## Rationale
Satisfies CMP-007's declared need to seed the in-session pet state from a restored
snapshot. It is separate from IF-008 because it is a different contract with a different
consumer and different rules: a care action nudges one Stat within its bounds, seeding
installs a whole state wholesale and may do so only once. FR-010's default-pet path is
an operation here rather than a special case of the snapshot path, so that "no valid
save existed" stays a visible outcome all the way through the launch sequence.

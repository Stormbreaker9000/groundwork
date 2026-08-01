---
id: IF-011
type: interface
title: Reminder Preference Persistence
description: The contract through which the care-reminder preference is stored durably and read back, separately from the pet state record.
traces_from:
- FR-009
- FR-010
- NFR-004
- CON-002
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
provider: CMP-001
operations:
- name: read_reminder_preference
  summary: Return the stored care-reminder preference, or report that none has been stored so the documented default applies.
- name: write_reminder_preference
  summary: Store the care-reminder preference durably so that it survives a restart.
interaction: synchronous
error_modes:
- No preference stored — a first launch, which the caller must resolve to the documented default rather than treating an absent record as 'off' by accident.
- Storage unwritable — the app-data directory is missing, full, or permission-denied, so the preference change did not persist and will revert on the next launch.
- Timeout with unknown commit state — the write may or may not have landed, so the caller must re-read before reporting success to the owner.
---

# IF-011 — Reminder Preference Persistence

The contract through which the care-reminder preference is stored durably and read back,
separately from the pet state record.

## Operations
- **read_reminder_preference** — Return the stored care-reminder preference, or report
  that none has been stored so the documented default applies.
- **write_reminder_preference** — Store the care-reminder preference durably so that it
  survives a restart.

## Interaction
Synchronous. CMP-008 reads the preference on the launch path before it can decide whether
to watch for threshold crossings at all, and the write is small, rare, and owner-initiated,
so there is nothing to gain from deferring it.

## Error Modes
- No preference stored — a first launch, which the caller must resolve to the documented
  default rather than treating an absent record as "off" by accident.
- Storage unwritable — the app-data directory is missing, full, or permission-denied, so
  the preference change did not persist and will revert on the next launch.
- Timeout with unknown commit state — the write may or may not have landed, so the caller
  must re-read before reporting success to the owner.

## Rationale
Satisfies CMP-008's declared need to remember whether the owner wants care reminders. It
is a second contract on the same provider as IF-003, not a widening of it, because the two
have different lifetimes and different failure consequences: FR-010 lets a corrupt pet
state be quarantined and replaced with a default pet, and the owner's reminder setting must
not be destroyed by that recovery. Medium confidence — that the preference lives in the same
store as the pet state but as a separate record is an inference, and FR-009 is a *could*.

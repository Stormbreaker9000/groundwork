---
id: IF-010
type: interface
title: Care Reminder Preference Control
description: The contract through which the owner-facing control turns care reminders on or off, without holding the preference itself.
traces_from:
- FR-009
- NFR-003
- NFR-006
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
provider: CMP-008
operations:
- name: reminders_enabled
  summary: Report whether the owner currently wants care reminders, so the control can show the true state rather than an assumed one.
- name: set_reminders_enabled
  summary: Turn care reminders on or off on the owner's behalf, taking effect for subsequent warning-threshold crossings.
interaction: synchronous
error_modes:
- The preference could not be persisted — the change applies to this session only, and the owner must be told rather than discovering it reverted after a restart.
- Reminders enabled where no notification delivery exists — the preference is accepted but no reminder can be shown on this platform, and the control must be able to surface that rather than silently promising reminders that never arrive.
---

# IF-010 — Care Reminder Preference Control

The contract through which the owner-facing control turns care reminders on or off,
without holding the preference itself.

## Operations
- **reminders_enabled** — Report whether the owner currently wants care reminders, so
  the control can show the true state rather than an assumed one.
- **set_reminders_enabled** — Turn care reminders on or off on the owner's behalf,
  taking effect for subsequent warning-threshold crossings.

## Interaction
Synchronous. NFR-003 requires the control to be keyboard-operable and named, which means
it has to reflect a confirmed state after the owner toggles it; an accepted-then-settled
toggle would let the control and the actual preference disagree, which for an on/off
switch is the failure the owner notices first.

## Error Modes
- The preference could not be persisted — the change applies to this session only, and
  the owner must be told rather than discovering it reverted after a restart.
- Reminders enabled where no notification delivery exists — the preference is accepted
  but no reminder can be shown on this platform, and the control must be able to surface
  that rather than silently promising reminders that never arrive.

## Rationale
Satisfies CMP-006's declared need to turn care reminders on or off. The provider is
CMP-008 rather than the store: CMP-008 is the component whose behaviour the switch
changes, and routing the toggle through it means the scheduler learns about the change
directly instead of having to watch a preference record for edits. CMP-008 in turn keeps
the value durable through IF-011, which is the capability it declared for exactly that.
Medium confidence because FR-009 is a *could*-priority requirement at medium confidence,
so the existence of an owner-facing control is firmer than its shape.

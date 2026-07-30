---
id: IF-012
type: interface
title: Desktop Notification Delivery
description: The contract through which a care reminder is presented to the owner outside the application window — the system's only outward crossing of the process boundary.
traces_from:
- FR-009
- NFR-005
- NFR-006
- CON-002
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
provider: CMP-010
operations:
- name: show_reminder
  summary: Present a short care-reminder message to the owner outside the application window.
- name: delivery_available
  summary: Report whether this platform can deliver a notification at all, including whether the owner has granted permission, so the caller can decide before it tries.
interaction: asynchronous
error_modes:
- No notification service on this platform — a target staged after v1 may have none, and no core feature may depend on delivery, since CON-002 keeps the rest of the system fully local and FR-009 is optional.
- Permission denied by the operating system or the owner — delivery is refused until the owner grants it, and the application cannot grant it on their behalf.
- Delivered but never seen — the OS may coalesce, suppress under do-not-disturb, or expire the notification, so delivery is not acknowledgement and the reminder must never be treated as read.
- Throttled by the operating system — repeated reminders may be suppressed, so the caller must not assume every raised reminder arrives, and must not compensate by raising more.
---

# IF-012 — Desktop Notification Delivery

The contract through which a care reminder is presented to the owner outside the
application window — the system's only outward crossing of the process boundary.

## Operations
- **show_reminder** — Present a short care-reminder message to the owner outside the
  application window.
- **delivery_available** — Report whether this platform can deliver a notification at
  all, including whether the owner has granted permission, so the caller can decide
  before it tries.

## Interaction
Asynchronous. Nothing in the system waits on a reminder: the owner may not be at the
machine, the OS may hold or coalesce it, and no pet state depends on the outcome.
Blocking the scheduler on an OS call would also put a foreign latency inside the process
that NFR-002's idle budget has to cover.

## Error Modes
- No notification service on this platform — a target staged after v1 may have none, and
  no core feature may depend on delivery, since CON-002 keeps the rest of the system
  fully local and FR-009 is optional.
- Permission denied by the operating system or the owner — delivery is refused until the
  owner grants it, and the application cannot grant it on their behalf.
- Delivered but never seen — the OS may coalesce, suppress under do-not-disturb, or
  expire the notification, so delivery is not acknowledgement and the reminder must never
  be treated as read.
- Throttled by the operating system — repeated reminders may be suppressed, so the caller
  must not assume every raised reminder arrives, and must not compensate by raising more.

## Rationale
Satisfies CMP-008's declared need to display a notification outside the application
window. The provider is the external OS notification service (CMP-010), modelled as a
component so that the one outward dependency in the architecture still points inside the
graph. FR-009 is the sole requirement that crosses the boundary outward, and NFR-006 plus
the Q-3 resolution are why `delivery_available` is on the contract: Windows ships first,
and macOS and Linux must be addable by changing an adapter rather than the core.

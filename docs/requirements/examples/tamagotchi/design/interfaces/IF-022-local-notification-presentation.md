---
id: IF-022
type: interface
title: Local Notification Presentation
description: The platform-adapter contract through which a care reminder is presented to the owner on the host desktop, reaching no network.
traces_from: [FR-009, CON-002, CON-003, NFR-005, NFR-006]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-017
operations:
- name: present_notification
  summary: Present a local notification to the owner on the host desktop, contacting no remote service and opening no outbound connection.
  interaction: asynchronous
error_modes:
- The host notification service is unavailable, or notification permission has been denied by the owner or the OS — the notification is not presented and the caller is told, with no retry that could surface as a burst later.
- The notification is accepted by the host but suppressed by its do-not-disturb or focus mode — never shown to the owner, and indistinguishable from delivery to the application.
- The host rate-limits notifications — further notifications are dropped for a period rather than queued.
- The platform's notification API requires an application identity the build has not registered — every notification is rejected on that platform while succeeding on the others, which NFR-006's cross-platform acceptance run is what catches.
---

# IF-022 — Local Notification Presentation

The platform-adapter contract through which a care reminder is presented to the owner on the host
desktop, reaching no network.

## Operations
- **present_notification** — Present a local notification to the owner on the host desktop,
  contacting no remote service and opening no outbound connection.

## Interaction
Asynchronous. The reminder service hands the notification over and does not wait: host notification
delivery is outside the application's control, and FR-009's reminders are advisory.

One operation. The contract's whole content is the delivery plus the boundary it must not cross —
CON-002 forbids any core function depending on a remote service, and NFR-005 checks it at the
network interface, so "no outbound connection" is part of the contract rather than an
implementation note.

## Error Modes
- The host notification service is unavailable or permission has been denied — not presented, and
  the caller is told, with no retry that could surface as a burst later.
- Accepted by the host but suppressed by do-not-disturb or focus mode — never shown, and
  indistinguishable from delivery.
- The host rate-limits notifications — further notifications dropped for a period, not queued.
- The platform's notification API requires an unregistered application identity — rejected on that
  platform while succeeding on the others.

## Rationale
Satisfies CMP-014's declared need to present a local notification without network access. Requirements A-19
establishes that delivery through the host's local notification service counts as fully offline;
this contract is the seam that keeps it that way, and it is the only path out of the process for
FR-009. The permission failure named here is the same one IF-028 must be able to report to the
owner, since an enabled preference that can never deliver is otherwise silent.

---
id: IF-023
type: interface
title: OS Notification Posting
description: The external contract the platform adapter posts notifications to — the host operating system's own native notification service.
traces_from: [FR-009, CON-003, NFR-006]
traces_to:
  adr: [ADR-002]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-018
operations:
- name: post
  summary: Post a notification to the host operating system's native notification service for display to the owner on the desktop.
  interaction: asynchronous
error_modes:
- The service is not running, or the platform's notification facility is absent in this session — an unregistered application identity on Windows, no notification daemon on Linux — and the post is rejected.
- The owner has revoked notification permission for the application at the OS level — posts are rejected until permission is granted again, and the application cannot grant it for itself.
- The post is accepted and then silently withheld by the host's do-not-disturb or focus mode — acceptance is not evidence of display.
- The service rate-limits or coalesces repeated notifications from the same application — later posts are dropped without notice.
---

# IF-023 — OS Notification Posting

The external contract the platform adapter posts notifications to — the host operating system's
own native notification service.

## Operations
- **post** — Post a notification to the host operating system's native notification service for
  display to the owner on the desktop.

## Interaction
Asynchronous. The service displays the notification on its own schedule and the application has no
result to wait for; acceptance of a post is not evidence of display, and this contract cannot make
it one.

## Error Modes
- The service is not running, or the platform's notification facility is absent in this session —
  the post is rejected.
- The owner has revoked notification permission at the OS level — posts are rejected until it is
  granted again, and the application cannot grant it for itself.
- Accepted and then silently withheld by do-not-disturb or focus mode.
- Rate-limited or coalesced by the service — later posts dropped without notice.

## Rationale
Satisfies CMP-017's declared need to post to the host notification service. This is one of the
edges leaving the process, and modelling the service as an external component keeps that edge
inside the graph rather than pointing outside it. A-21 assumes each target platform provides a
usable native notification API — an assumption this contract's first failure mode is where it would
show up if it did not hold.

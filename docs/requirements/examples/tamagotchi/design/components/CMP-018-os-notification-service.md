---
id: CMP-018
type: component
title: OS Notification Service
description: The host operating system's native local notification service, through which care reminders reach the owner.
traces_from: [FR-009, NFR-005, CON-002]
traces_to:
  adr: [ADR-002]
  diagrams: [DIA-001, DIA-002]
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Presents notifications the application posts to the owner on the host desktop.
boundary: external
depends_on: []
---

# CMP-018 — OS Notification Service

The host operating system's native local notification service, through which care
reminders reach the owner.

## Responsibility
Presents notifications the application posts to the owner on the host desktop.

## Rationale
FR-009 is the only requirement that crosses the process boundary out of the
application, and requirements A-19 records that reminders delivered through the host's local
notification service count as fully offline and do not violate CON-002 — there is no
push service and no network hop. Requirements A-21 assumes each target platform provides a usable
native notification API. Modelling the service as a component keeps the dependency
graph total and makes the one outbound edge in the system visible rather than implicit.

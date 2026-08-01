---
id: CMP-010
type: component
title: OS Notification Service
description: The operating system's own notification facility, which raises messages to the owner outside any application window.
traces_from:
- FR-009
- NFR-006
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
responsibility: Presents a message to the owner on behalf of an application that is not in focus.
boundary: external
depends_on: []
---

# CMP-010 — OS Notification Service

The operating system's own notification facility, which raises messages to the
owner outside any application window.

## Responsibility
Presents a message to the owner on behalf of an application that is not in focus.

## Rationale
This is the only integration point the system has. FR-009's optional local care
reminders are the sole path that leaves the process, and CON-002 rules out every
other one, so this is the entire external surface of the architecture. It is
modelled as a component with `boundary: external` so the dependency edge that
reaches it has somewhere to land and the graph stays total. Its behaviour differs
per platform, which under NFR-006 and CON-003 is exactly why it sits behind a
contract: the v1 Windows implementation and the macOS and Linux ones staged after
it are substitutions here, not changes to anything above.

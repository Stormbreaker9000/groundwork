---
id: CMP-009
type: component
title: Diagnostic Log
description: The append-only, on-device, user-readable record of what the simulation computed and when.
traces_from:
- NFR-005
- NFR-007
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
responsibility: Owns the application's local diagnostic record.
boundary: internal
depends_on:
- IF-001
---

# CMP-009 — Diagnostic Log

The append-only, on-device, user-readable record of what the simulation computed
and when.

## Responsibility
Owns the application's local diagnostic record.

## Rationale
NFR-007 requires a durable record of every Decay computation and every lifecycle
transition, with a 24-hour session having zero missing transition entries. That is
a sink that would not otherwise exist, and it is what turns those computations into
observable events rather than silent mutations. NFR-005 and CON-002 fix its shape
completely: with zero outbound connections permitted and no telemetry or crash
reporting anywhere in the design space, this local file is the only diagnostic
channel the product has, so it must be readable by the owner without a tool.

Confidence is **medium**: NFR-007 is a `should`, and the retention and rotation
behaviour of the log is not stated anywhere in the requirement set.

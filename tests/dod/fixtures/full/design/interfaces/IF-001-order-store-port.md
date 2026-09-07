---
id: IF-001
type: interface
title: Order store port
description: The persistence contract the Order Service depends on.
traces_from: [FR-001]
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-09-07'
provider: CMP-001
operations:
- name: save
  summary: Persist an order's current state, superseding any prior stored state for the same order.
  interaction: synchronous
error_modes:
- Write conflict on concurrent cancellation
---

# IF-001 — Order store port

## Operations
Described above.

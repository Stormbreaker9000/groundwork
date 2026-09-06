---
id: CMP-002
type: component
title: order-store
description: Persists orders.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
responsibility: Persists the order aggregate.
boundary: internal
depends_on: []
---

# order-store

Provides both interfaces and consumes none, which keeps the set acyclic.

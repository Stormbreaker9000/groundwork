---
id: CMP-001
type: component
title: order-service
description: Owns the order aggregate.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
responsibility: Owns the order aggregate and every transition of its state.
boundary: internal
depends_on: []
---

# order-service

The near-miss for `god-component`: "and every transition" is a noun phrase, not
a second action verb, so this must stay clean.

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
responsibility: Owns the order aggregate.
boundary: internal
depends_on:
  - IF-001
---

# order-service

Consumes IF-001 and nothing else, leaving IF-002 orphaned.

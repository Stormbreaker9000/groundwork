---
id: IF-001
type: interface
title: order-lookup
description: Reads an order by id.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: get_order
    summary: Return the order with the given id.
    interaction: synchronous
error_modes:
  - The requested order id does not exist.
---

# order-lookup

Consumed by CMP-001 — the near-miss that must stay clean.

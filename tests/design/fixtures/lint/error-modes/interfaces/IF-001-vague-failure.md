---
id: IF-001
type: interface
title: order-lookup
description: Reads an order by id.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: get_order
    summary: Return the order with the given id.
    interaction: synchronous
error_modes:
  - Errors are handled gracefully.
  - The requested order id does not exist.
---

# order-lookup

One hand-waved mode and one real one: the rule must flag exactly the first.
CMP-001 consumes this, so the set has no orphan and no cycle either — the
handwaved mode is the only finding it should produce.

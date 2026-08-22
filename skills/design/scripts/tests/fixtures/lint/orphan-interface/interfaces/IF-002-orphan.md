---
id: IF-002
type: interface
title: order-archive
description: Archives an order.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: archive_order
    summary: Move the order to cold storage.
    interaction: synchronous
error_modes:
  - The order is already archived.
---

# order-archive

No component lists IF-002 in depends_on — this is the orphan.

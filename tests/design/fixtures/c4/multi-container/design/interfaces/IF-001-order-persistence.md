---
id: IF-001
type: interface
title: Order Persistence
description: Durable storage and retrieval of orders.
provider: CMP-002
operations:
  - name: commit
    interaction: synchronous
    summary: Write an order durably.
  - name: load
    interaction: synchronous
    summary: Read an order by id.
error_modes:
  - Storage is unavailable; the caller receives a retryable failure.
traces_from: [FR-002]
traces_to: {}
status: draft
confidence: high
created_at: 2026-08-22
---

# Order Persistence

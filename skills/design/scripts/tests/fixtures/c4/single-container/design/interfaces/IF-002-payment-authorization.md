---
id: IF-002
type: interface
title: Payment Authorization
description: Authorization and capture of card payments.
provider: CMP-003
operations:
  - name: authorize
    interaction: synchronous
    description: Authorize a card payment for an order.
error_modes:
  - The card is declined; the caller receives a non-retryable failure.
traces_from: [FR-001]
traces_to: {}
status: draft
confidence: high
created_at: 2026-08-22
---

# Payment Authorization

---
id: IF-001
type: interface
title: payment-api
description: The contract order-service uses to charge a customer through the payment provider.
traces_from:
  - FR-001
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: reviewed
confidence: high
created_at: 2026-07-18
provider: CMP-002
operations:
  - name: authorize
    summary: Reserve funds on a card without capturing them.
  - name: capture
    summary: Capture previously authorized funds.
interaction: synchronous
error_modes:
  - card declined
  - provider timeout
  - idempotency key reused with a different amount
---

# payment-api

Provided by the external `stripe-gateway` (`CMP-002`), consumed by
`order-service` (`CMP-001`). This is the single edge between them: the
dependency is expressed as `CMP-001.depends_on -> IF-001.provider -> CMP-002`.

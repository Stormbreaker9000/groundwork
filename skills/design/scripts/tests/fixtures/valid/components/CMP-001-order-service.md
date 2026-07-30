---
id: CMP-001
type: component
title: order-service
description: Owns the lifecycle of a customer order from placement to fulfilment.
traces_from:
  - FR-001
traces_to:
  adr:
    - ADR-001
  diagrams:
    - c4-container
  code: []
  tests: []
status: reviewed
confidence: high
created_at: 2026-07-18
responsibility: Accept, validate, and persist orders, and coordinate payment via the payment contract.
boundary: internal
depends_on:
  - IF-001
---

# order-service

The internal component that owns orders. It consumes the payment API (`IF-001`)
to charge the customer; it never talks to the payment provider directly.

---
id: NFR-001
type: non_functional
tier: solution
title: Order API latency
description: >
  The Order API shall respond to order submissions within a bounded latency
  budget under normal load.
rationale: >
  Slow order submission directly reduces checkout conversion; performance is a
  contractual SLO with the storefront team.
fit_criterion: >
  End-to-end latency <= 200 ms at p95 over a rolling 5-minute window with error
  rate <= 0.1%.
priority: should
confidence: medium
verification_method: analysis
status: reviewed
created_at: 2026-06-26
traces_from: []
traces_to:
  design:
    - ADR-0021-order-state-machine
---

# NFR-001 — Order API latency

## Quality Attribute Scenario
- **Source:** Authenticated customer (external)
- **Stimulus:** Submits an order via `POST /orders`
- **Environment:** Normal operations, load <= 80% capacity
- **Artifact:** Order API service + Order DB
- **Response:** Order persisted, 201 returned, `orders.created` event published
- **Response measure:** End-to-end latency <= 200 ms at p95 over a rolling
  5-minute window; error rate <= 0.1%

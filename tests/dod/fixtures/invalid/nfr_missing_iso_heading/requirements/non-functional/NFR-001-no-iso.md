---
id: NFR-001
type: non_functional
tier: solution
title: Order API latency
description: The Order API shall respond within a bounded latency budget under normal load.
rationale: Slow submission reduces checkout conversion.
fit_criterion: p95 <= 200 ms over a rolling 5-minute window.
priority: should
confidence: medium
verification_method: test
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# NFR-001 — Order API latency

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated customer
- **Stimulus:** Submits an order via `POST /orders`
- **Environment:** Normal operations, load <= 80% capacity
- **Artifact:** Order API service
- **Response:** Order persisted and 201 returned
- **Response measure:** End-to-end latency <= 200 ms at p95 over a rolling
  5-minute window; error rate <= 0.1%

---
id: FR-001
type: functional
tier: solution
title: Cancel a pending order
description: When a customer requests cancellation of a pending order, the system shall cancel it and confirm within 5 seconds.
rationale: Customers abandon checkout when a mistaken order cannot be undone.
fit_criterion: 100% of cancellation requests against pending orders succeed within 5 seconds.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# FR-001 — Cancel a pending order

## Acceptance Criteria
Given a pending order, when the customer cancels, then the order is cancelled.

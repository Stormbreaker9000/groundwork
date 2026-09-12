---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: >
  When an authenticated customer issues a cancellation request for an order in
  status Pending, the system shall transition the order to status Cancelled
  within 60 seconds.
rationale: >
  Customers expect to cancel before fulfillment to avoid charges; cancellation
  requests are currently 18% of all support tickets.
fit_criterion: >
  100% of cancellation requests on Pending orders succeed in tests; 0% on
  Fulfilling orders.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: approved
created_at: 2026-06-26
traces_from:
  - BR-001
traces_to:
  tests:
    - TC-ORDER-CANCEL-001
  code:
    - src/order/cancel_handler.py
scope: story
parent_scope: null
---

# FR-001 — Cancel pending order

## Description
When an authenticated customer issues a cancellation request for an order in
status Pending, the system shall transition the order to status Cancelled
within 60 seconds.

## Rationale
Customers expect to cancel before fulfillment to avoid charges.

## Acceptance Criteria
### AC-1 — Successful cancellation
```gherkin
Given an authenticated customer with a Pending order O
When the customer issues DELETE /orders/{O.id}
Then the order status becomes Cancelled
 And the orders.cancelled event is published
```

## Fit Criterion
100% of cancellation requests on Pending orders succeed in tests; 0% on Fulfilling orders.

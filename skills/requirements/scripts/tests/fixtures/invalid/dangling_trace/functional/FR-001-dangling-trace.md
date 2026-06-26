---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: When the customer cancels a Pending order, the system shall cancel it.
rationale: Customers expect to cancel before fulfillment to avoid charges.
fit_criterion: 100% of Pending-order cancellations succeed.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-06-26
traces_from:
  - BR-999
traces_to: {}
---

# FR-001 — Dangling trace (INVALID)

`traces_from` references `BR-999`, which is not defined anywhere in the set.

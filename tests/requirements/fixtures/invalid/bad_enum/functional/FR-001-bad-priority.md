---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: When the customer cancels a Pending order, the system shall cancel it.
rationale: Customers expect to cancel before fulfillment to avoid charges.
fit_criterion: 100% of Pending-order cancellations succeed.
priority: critical
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-06-26
traces_from: []
traces_to: {}
---

# FR-001 — Bad enum (INVALID)

`priority: critical` is not a member of the MoSCoW enum
(must|should|could|wont).

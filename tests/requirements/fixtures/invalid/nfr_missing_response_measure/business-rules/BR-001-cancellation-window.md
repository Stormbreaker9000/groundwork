---
id: BR-001
type: business_rule
tier: business
title: Orders may be cancelled only before fulfillment
description: >
  An order may be cancelled by the customer only while it remains in the
  Pending state and has not entered Fulfilling.
rationale: >
  Once fulfillment begins, inventory and shipping costs are committed; allowing
  cancellation after that point creates unrecoverable cost.
fit_criterion: >
  No order in Fulfilling or later state is ever cancellable by a customer in
  audited transaction logs.
priority: must
confidence: high
verification_method: inspection
status: approved
created_at: 2026-06-26
traces_from: []
traces_to: {}
---

# BR-001 — Orders may be cancelled only before fulfillment

## Description
This policy exists independent of the system; the functional requirements
describe what the system does to enforce it.

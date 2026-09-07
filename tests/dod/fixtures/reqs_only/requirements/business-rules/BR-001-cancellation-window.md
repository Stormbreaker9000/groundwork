---
id: BR-001
type: business_rule
tier: business
title: Cancellation window closes at fulfilment
description: An order shall not be cancellable once fulfilment has begun.
rationale: Stock is committed at fulfilment and cannot be released.
fit_criterion: 0 cancellations succeed against an order in fulfilment.
priority: must
confidence: high
verification_method: test
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# BR-001 — Cancellation window closes at fulfilment

## Description
Fulfilment is the cut-off.

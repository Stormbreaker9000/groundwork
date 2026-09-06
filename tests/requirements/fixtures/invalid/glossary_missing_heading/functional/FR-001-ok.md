---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: When the customer cancels a pending order, the system shall release the reserved stock.
rationale: Reserved stock on abandoned orders blocks sales to other customers.
fit_criterion: Reserved stock returns to the available pool within 5 seconds of cancellation.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: "2026-07-13"
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Cancel pending order

## Acceptance Criteria

### AC-1 — Reserved stock is released
```gherkin
Given a pending order holding reserved stock
When the customer cancels the order
Then the reserved stock returns to the available pool
```

---
id: FR-003
type: functional
tier: solution
title: Feed the pet
description: When the owner selects the feed action, the system shall increase the pet's hunger-satisfaction stat by the configured feed increment up to its maximum value.
rationale: Feeding is the primary care interaction that reverses hunger decay; it is the most frequent reason a user returns, so it must produce an immediate, legible reward.
fit_criterion: Each feed action raises the hunger-satisfaction stat by exactly the configured increment, never exceeding the maximum, verified for boundary cases at 0, mid-range, and near-maximum starting values.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-003 — Feed the pet

## Description
When the owner selects the feed action, the system shall increase the pet's
hunger-satisfaction stat by the configured feed increment up to its maximum value.

## Rationale
Feeding is the primary care interaction that reverses hunger decay; it is the most
frequent reason a user returns, so it must produce an immediate, legible reward.

## Acceptance Criteria
### AC-1 — Feeding raises hunger satisfaction
```gherkin
Given a pet with hunger-satisfaction below its maximum
When the owner selects the feed action
Then the hunger-satisfaction stat increases by the configured feed increment
```

### AC-2 — Feeding never overflows the maximum
```gherkin
Given a pet with hunger-satisfaction near its maximum
When the owner selects the feed action
Then the hunger-satisfaction stat is capped at its maximum value
```

## Fit Criterion
Each feed action raises the hunger-satisfaction stat by exactly the configured
increment, never exceeding the maximum, verified for boundary cases at 0,
mid-range, and near-maximum starting values.

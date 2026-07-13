---
id: FR-004
type: functional
tier: solution
title: Play with the pet
description: When the owner selects the play action, the system shall increase the pet's happiness stat by the configured play increment up to its maximum value.
rationale: Play is the interaction that builds emotional attachment rather than mere survival; rewarding play with a happiness gain is what turns a utility into a companion.
fit_criterion: Each play action raises the happiness stat by exactly the configured increment, never exceeding the maximum, verified for boundary cases at 0, mid-range, and near-maximum starting values.
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

# FR-004 — Play with the pet

## Description
When the owner selects the play action, the system shall increase the pet's
happiness stat by the configured play increment up to its maximum value.

## Rationale
Play is the interaction that builds emotional attachment rather than mere survival;
rewarding play with a happiness gain is what turns a utility into a companion.

## Acceptance Criteria
### AC-1 — Playing raises happiness
```gherkin
Given a pet with happiness below its maximum
When the owner selects the play action
Then the happiness stat increases by the configured play increment
```

### AC-2 — Playing never overflows the maximum
```gherkin
Given a pet with happiness near its maximum
When the owner selects the play action
Then the happiness stat is capped at its maximum value
```

## Fit Criterion
Each play action raises the happiness stat by exactly the configured increment,
never exceeding the maximum, verified for boundary cases at 0, mid-range, and
near-maximum starting values.

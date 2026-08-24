---
id: FR-004
type: functional
tier: solution
title: Play with the pet
description: When the owner selects the play action, the system shall increase the pet's happiness stat by the play interaction's defined increment, up to the stat's maximum value.
rationale: Play is one of the four care interactions the owner performs to counteract stat decay; without it the owner has no way to raise happiness, and low happiness would be irrecoverable, undermining both the care loop and the mood display it feeds.
fit_criterion: The happiness stat increases by the configured play increment (or is unchanged if already at maximum) in 100% of play action invocations in acceptance tests.
priority: must
confidence: medium
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-08-24
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
happiness stat by the play interaction's defined increment, up to the stat's
maximum value.

## Rationale
Play is one of the four care interactions the owner performs to counteract stat
decay; without it the owner has no way to raise happiness, and low happiness would
be irrecoverable, undermining both the care loop and the mood display it feeds.

## Acceptance Criteria
### AC-1 — Playing increases happiness below maximum
```gherkin
Given the pet's happiness stat is below its maximum value
When the owner selects the play action
Then the happiness stat increases by the play interaction's defined increment, not exceeding the maximum value
```

### AC-2 — Playing at maximum happiness has no further effect
```gherkin
Given the pet's happiness stat is already at its maximum value
When the owner selects the play action
Then the happiness stat remains at its maximum value with no error
```

## Fit Criterion
The happiness stat increases by the configured play increment (or is unchanged if
already at maximum) in 100% of play action invocations in acceptance tests.

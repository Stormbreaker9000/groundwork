---
id: FR-005
type: functional
tier: solution
title: Clean the pet
description: When the owner selects the clean action, the system shall increase the pet's hygiene stat by the clean interaction's defined increment, up to the stat's maximum value.
rationale: Clean is one of the four care interactions the owner performs to counteract stat decay; without it sustained hygiene neglect cannot be remedied, and unresolved hygiene decay is one of the inputs to the sickness progression this pet must be protected from.
fit_criterion: The hygiene stat increases by the configured clean increment (or is unchanged if already at maximum) in 100% of clean action invocations in acceptance tests.
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

# FR-005 — Clean the pet

## Description
When the owner selects the clean action, the system shall increase the pet's
hygiene stat by the clean interaction's defined increment, up to the stat's maximum
value.

## Rationale
Clean is one of the four care interactions the owner performs to counteract stat
decay; without it sustained hygiene neglect cannot be remedied, and unresolved
hygiene decay is one of the inputs to the sickness progression this pet must be
protected from.

## Acceptance Criteria
### AC-1 — Cleaning increases hygiene below maximum
```gherkin
Given the pet's hygiene stat is below its maximum value
When the owner selects the clean action
Then the hygiene stat increases by the clean interaction's defined increment, not exceeding the maximum value
```

### AC-2 — Cleaning at maximum hygiene has no further effect
```gherkin
Given the pet's hygiene stat is already at its maximum value
When the owner selects the clean action
Then the hygiene stat remains at its maximum value with no error
```

## Fit Criterion
The hygiene stat increases by the configured clean increment (or is unchanged if
already at maximum) in 100% of clean action invocations in acceptance tests.

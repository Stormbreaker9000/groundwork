---
id: FR-003
type: functional
tier: solution
title: Feed the pet
description: When the owner selects the feed action, the system shall increase the pet's hunger stat by the feed interaction's defined increment, up to the stat's maximum value.
rationale: Feed is one of the four care interactions the owner performs to counteract stat decay; without it the owner has no way to address hunger decay, breaking the core care loop the attachment habit depends on.
fit_criterion: The hunger stat increases by the configured feed increment (or is unchanged if already at maximum) in 100% of feed action invocations in acceptance tests.
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

# FR-003 — Feed the pet

## Description
When the owner selects the feed action, the system shall increase the pet's hunger
stat by the feed interaction's defined increment, up to the stat's maximum value.

## Rationale
Feed is one of the four care interactions the owner performs to counteract stat
decay; without it the owner has no way to address hunger decay, breaking the core
care loop the attachment habit depends on.

## Acceptance Criteria
### AC-1 — Feeding increases hunger below maximum
```gherkin
Given the pet's hunger stat is below its maximum value
When the owner selects the feed action
Then the hunger stat increases by the feed interaction's defined increment, not exceeding the maximum value
```

### AC-2 — Feeding at maximum hunger has no further effect
```gherkin
Given the pet's hunger stat is already at its maximum value
When the owner selects the feed action
Then the hunger stat remains at its maximum value with no error
```

## Fit Criterion
The hunger stat increases by the configured feed increment (or is unchanged if
already at maximum) in 100% of feed action invocations in acceptance tests.

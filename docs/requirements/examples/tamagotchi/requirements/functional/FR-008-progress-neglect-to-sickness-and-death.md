---
id: FR-008
type: functional
tier: solution
title: Progress neglect to sickness and death
description: While the pet's care stats remain fully depleted beyond the configured sustained-neglect threshold, the system shall transition the pet from sick to the dead state.
rationale: Consequence is what gives care meaning; a pet that cannot come to harm creates no stakes and no habit, so sustained neglect must lead to a terminal outcome — but only after a grace period so a single missed day is forgiving.
fit_criterion: The pet transitions to sick only after care stats remain at zero for the sickness threshold, and to dead only after remaining sick for the death threshold; no transition to dead occurs before the combined threshold elapses, verified across boundary timings.
priority: must
confidence: low
verification_method: test
ears_pattern: state
status: draft
created_at: 2026-07-10
traces_from: [BR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-008 — Progress neglect to sickness and death

## Description
While the pet's care stats remain fully depleted beyond the configured
sustained-neglect threshold, the system shall transition the pet from sick to the
dead state.

## Rationale
Consequence is what gives care meaning; a pet that cannot come to harm creates no
stakes and no habit, so sustained neglect must lead to a terminal outcome — but
only after a grace period so a single missed day is forgiving.

## Acceptance Criteria
### AC-1 — Sustained neglect leads to death
```gherkin
Given a pet whose care stats have been fully depleted past the sickness threshold
When neglect continues past the death threshold without any care interaction
Then the pet transitions to the dead state
```

### AC-2 — A single lapse does not kill the pet
```gherkin
Given a sick pet within the death grace period
When the owner performs a care interaction before the death threshold elapses
Then the pet recovers from the sick state and does not die
```

## Fit Criterion
The pet transitions to sick only after care stats remain at zero for the sickness
threshold, and to dead only after remaining sick for the death threshold; no
transition to dead occurs before the combined threshold elapses, verified across
boundary timings.

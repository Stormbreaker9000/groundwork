---
id: FR-007
type: functional
tier: stakeholder
title: Display mood expression tracking stat thresholds
description: While the pet's lowest stat value falls within a given mood-threshold band, the system shall display the mood expression mapped to that band.
rationale: Owners need an at-a-glance wellbeing indicator so they can judge whether care is needed without inspecting individual numeric stats; this directly supports the daily check-in habit by making neglect visible immediately rather than requiring the owner to interpret raw numbers. The lowest stat is the reduction rule because the indicator exists to surface the need most at risk of being missed — an average would let one critically low stat be masked by healthy ones, which is the exact failure the display is there to prevent.
fit_criterion: The displayed mood expression matches the expression mapped to the band containing the pet's lowest stat value in 100% of sampled states, across a test matrix that spans every defined band and includes states in which the individual stats fall in different bands. Band boundaries are taken from the Q-1 balance values and are not fixed by this requirement.
priority: must
confidence: medium
verification_method: test
ears_pattern: state
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

# FR-007 — Display mood expression tracking stat thresholds

## Description
While the pet's lowest stat value falls within a given mood-threshold band, the
system shall display the mood expression mapped to that band.

## Rationale
Owners need an at-a-glance wellbeing indicator so they can judge whether care is
needed without inspecting individual numeric stats; this directly supports the daily
check-in habit by making neglect visible immediately rather than requiring the owner
to interpret raw numbers. The lowest stat is the reduction rule because the indicator
exists to surface the need most at risk of being missed — an average would let one
critically low stat be masked by healthy ones, which is the exact failure the display
is there to prevent.

## Acceptance Criteria
### AC-1 — Mood expression matches the band of the lowest stat
```gherkin
Given the pet's lowest stat value falls within the "content" mood-threshold band
When the mood expression is displayed
Then the expression shown is the one mapped to the "content" band
```

### AC-2 — Stats in different bands resolve to the lowest stat's band
```gherkin
Given the pet's hunger stat falls within the "content" mood-threshold band
And the pet's hygiene stat falls within a lower mood-threshold band
When the mood expression is displayed
Then the expression shown is the one mapped to the lower band containing the hygiene stat
```

### AC-3 — Mood expression updates when the lowest stat crosses a band boundary
```gherkin
Given the pet's lowest stat value is within the "content" mood-threshold band
When decay or neglect moves that stat into a lower mood-threshold band
Then the displayed mood expression updates to the expression mapped to the new band
```

## Fit Criterion
The displayed mood expression matches the expression mapped to the band containing
the pet's lowest stat value in 100% of sampled states, across a test matrix that
spans every defined band and includes states in which the individual stats fall in
different bands. Band boundaries are taken from the Q-1 balance values and are not
fixed by this requirement.

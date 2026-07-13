---
id: FR-002
type: functional
tier: solution
title: Apply offline-elapsed decay on launch
description: When the application starts, the system shall reduce each affected pet stat by the amount accrued over the real elapsed wall-clock time since the last recorded save.
rationale: The pet is an ambient companion that must reflect the passage of real time even while closed; if stats only decayed while the app was open, users could avoid consequences by never opening it, defeating the periodic check-in habit the product exists to create.
fit_criterion: For an elapsed offline interval of duration T since the last save, each stat equals its saved value minus the reference decay function evaluated at T, within +/- 1 stat unit, for T values from 1 minute to 30 days.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-07-10
traces_from: [BR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-002 — Apply offline-elapsed decay on launch

## Description
When the application starts, the system shall reduce each affected pet stat by the
amount accrued over the real elapsed wall-clock time since the last recorded save.

## Rationale
The pet is an ambient companion that must reflect the passage of real time even
while closed; if stats only decayed while the app was open, users could avoid
consequences by never opening it, defeating the periodic check-in habit the
product exists to create.

## Acceptance Criteria
### AC-1 — Decay reflects time the app was closed
```gherkin
Given a pet saved with full hunger 24 hours ago
When the application starts and reads the current wall-clock time
Then hunger is reduced by the decay accrued over the full 24-hour elapsed interval
```

### AC-2 — No elapsed time yields no decay
```gherkin
Given a pet saved less than one decay tick ago
When the application starts
Then no stat is reduced beyond the decay for the elapsed sub-tick interval
```

## Fit Criterion
For an elapsed offline interval of duration T since the last save, each stat equals
its saved value minus the reference decay function evaluated at T, within +/- 1
stat unit, for T values from 1 minute to 30 days.

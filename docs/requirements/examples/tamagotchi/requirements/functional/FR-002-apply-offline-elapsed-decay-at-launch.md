---
id: FR-002
type: functional
tier: solution
title: Apply offline-elapsed decay at launch
description: When the application launches, the system shall compute stat decay from the real wall-clock time elapsed since the last committed save, treating any elapsed interval at or below zero as zero elapsed time so that no stat value increases as a result of decay computation, and apply the resulting decay to the pet's stats before the pet is displayed.
rationale: The product's premise is that the pet ages in real time whether or not the app is running; without decay computed from actual elapsed time at launch, time away would have no consequence and the periodic check-in habit the product exists to create would have nothing to enforce it. The clamp at zero is required because the elapsed interval is derived from a device clock the owner can move backward (manual change, DST, NTP correction), and a negative interval driven through the decay function would raise stats — silently rewarding clock tampering and corrupting the neglect progression.
fit_criterion: For elapsed intervals from 1 minute to 30 days, the decay applied at launch is within +/-1 stat unit of the reference decay model, verified across a test matrix of representative intervals; for elapsed intervals at or below zero, including a system clock set behind the last committed save's timestamp, the computed decay is exactly zero and 0% of trials show any stat value higher after launch than at the last committed save.
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

# FR-002 — Apply offline-elapsed decay at launch

## Description
When the application launches, the system shall compute stat decay from the real
wall-clock time elapsed since the last committed save, treating any elapsed interval
at or below zero as zero elapsed time so that no stat value increases as a result of
decay computation, and apply the resulting decay to the pet's stats before the pet is
displayed.

## Rationale
The product's premise is that the pet ages in real time whether or not the app is
running; without decay computed from actual elapsed time at launch, time away would
have no consequence and the periodic check-in habit the product exists to create
would have nothing to enforce it. The clamp at zero is required because the elapsed
interval is derived from a device clock the owner can move backward (manual change,
DST, NTP correction), and a negative interval driven through the decay function would
raise stats — silently rewarding clock tampering and corrupting the neglect
progression.

## Acceptance Criteria
### AC-1 — Decay applied for a short offline interval
```gherkin
Given the last committed save's timestamp is 3 hours before the current launch time
When the application launches
Then each stat is reduced by the decay amount the reference decay model produces for a 3-hour interval, within +/-1 stat unit
```

### AC-2 — Decay applied for a long offline interval
```gherkin
Given the last committed save's timestamp is 30 days before the current launch time
When the application launches
Then decay is computed and applied without error or numeric overflow, matching the reference decay model's 30-day decay output within +/-1 stat unit
```

### AC-3 — Backward clock yields no decay and no stat increase
```gherkin
Given the system clock now reads earlier than the last committed save's timestamp
When the application launches
Then no decay is applied and no stat value increases
```

## Fit Criterion
For elapsed intervals from 1 minute to 30 days, the decay applied at launch is within
+/-1 stat unit of the reference decay model, verified across a test matrix of
representative intervals; for elapsed intervals at or below zero, including a system
clock set behind the last committed save's timestamp, the computed decay is exactly
zero and 0% of trials show any stat value higher after launch than at the last
committed save.

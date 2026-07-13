---
id: FR-006
type: functional
tier: solution
title: Put the pet to sleep
description: When the owner initiates the sleep action, the system shall restore the pet's energy stat toward its maximum over the configured sleep duration.
rationale: Energy is the stat that regenerates through rest rather than a consumable; a sleep interaction gives the pet a daily rhythm that reinforces periodic check-ins.
fit_criterion: A completed sleep interaction of the configured duration raises the energy stat to its maximum; an interrupted sleep raises energy proportionally to the fraction of the duration elapsed, within +/- 1 stat unit.
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

# FR-006 — Put the pet to sleep

## Description
When the owner initiates the sleep action, the system shall restore the pet's
energy stat toward its maximum over the configured sleep duration.

## Rationale
Energy is the stat that regenerates through rest rather than a consumable; a sleep
interaction gives the pet a daily rhythm that reinforces periodic check-ins.

## Acceptance Criteria
### AC-1 — Completed sleep restores energy
```gherkin
Given a pet with depleted energy
When the owner initiates the sleep action and the sleep duration completes
Then the energy stat reaches its maximum value
```

### AC-2 — Interrupted sleep restores partial energy
```gherkin
Given a pet sleeping with depleted energy
When the sleep is interrupted after part of the duration has elapsed
Then the energy stat rises in proportion to the elapsed fraction of the duration
```

## Fit Criterion
A completed sleep interaction of the configured duration raises the energy stat to
its maximum; an interrupted sleep raises energy proportionally to the fraction of
the duration elapsed, within +/- 1 stat unit.

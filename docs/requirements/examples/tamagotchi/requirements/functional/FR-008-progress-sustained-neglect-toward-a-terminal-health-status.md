---
id: FR-008
type: functional
tier: solution
title: Progress sustained neglect toward a terminal health status
description: While at least one of the pet's stats remains below its neglect threshold continuously for the defined sustained-neglect duration, the system shall advance the pet's health status one step along the Healthy -> Sick -> terminal end-of-life progression.
rationale: Sustained neglect must have escalating, visible consequences for the daily-return habit loop to carry real stakes, and a single ignored need is enough to constitute neglect — requiring every stat to be starved simultaneously would let an owner neglect one need indefinitely with no consequence. This requirement intentionally stops at the terminal end-of-life status and does not assert what happens once it is reached, because that disposition depends on open question Q-2 (whether the terminal state is permanent or a configurable soft reset), which is owned by a separate business rule.
fit_criterion: Health status transitions Healthy -> Sick when at least one stat has remained below its neglect threshold continuously for the defined sustained-neglect duration, and Sick -> the terminal end-of-life status when at least one stat remains below its neglect threshold for the further defined duration, matching the reference progression model in 100% of scripted neglect-duration test cases; 0% of cases advance health status when no stat has been below its threshold for the full duration, including cases where a stat drops below and recovers within the window. Behavior after the terminal status is reached is explicitly out of scope for this requirement pending Q-2 and is not exercised by these cases.
priority: must
confidence: low
verification_method: test
ears_pattern: state
status: draft
created_at: 2026-08-24
traces_from: [BR-001, BR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-008 — Progress sustained neglect toward a terminal health status

## Description
While at least one of the pet's stats remains below its neglect threshold
continuously for the defined sustained-neglect duration, the system shall advance the
pet's health status one step along the Healthy -> Sick -> terminal end-of-life
progression.

## Rationale
Sustained neglect must have escalating, visible consequences for the daily-return
habit loop to carry real stakes, and a single ignored need is enough to constitute
neglect — requiring every stat to be starved simultaneously would let an owner
neglect one need indefinitely with no consequence. This requirement intentionally
stops at the terminal end-of-life status and does not assert what happens once it is
reached, because that disposition depends on open question Q-2 (whether the terminal
state is permanent or a configurable soft reset), which is owned by a separate
business rule.

## Acceptance Criteria
### AC-1 — Sustained neglect of a single stat advances Healthy to Sick
```gherkin
Given the pet's health status is Healthy
And the pet's hygiene stat has remained below its neglect threshold continuously for the defined sustained-neglect duration
And every other stat has remained above its neglect threshold throughout
When the neglect-progression check runs
Then the pet's health status becomes Sick
```

### AC-2 — Continued neglect advances Sick to the terminal end-of-life status
```gherkin
Given the pet's health status is Sick
And at least one stat has remained below its neglect threshold continuously for the further defined duration
When the neglect-progression check runs
Then the pet's health status becomes the terminal end-of-life status
```

### AC-3 — Recovery within the window does not advance health status
```gherkin
Given the pet's health status is Healthy
And a stat dropped below its neglect threshold and was restored above it before the defined sustained-neglect duration elapsed
When the neglect-progression check runs
Then the pet's health status remains Healthy
```

## Fit Criterion
Health status transitions Healthy -> Sick when at least one stat has remained below
its neglect threshold continuously for the defined sustained-neglect duration, and
Sick -> the terminal end-of-life status when at least one stat remains below its
neglect threshold for the further defined duration, matching the reference
progression model in 100% of scripted neglect-duration test cases; 0% of cases
advance health status when no stat has been below its threshold for the full
duration, including cases where a stat drops below and recovers within the window.
Behavior after the terminal status is reached is explicitly out of scope for this
requirement pending Q-2 and is not exercised by these cases.

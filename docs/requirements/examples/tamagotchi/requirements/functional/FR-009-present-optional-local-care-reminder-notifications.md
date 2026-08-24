---
id: FR-009
type: functional
tier: solution
title: Present optional local care-reminder notifications
description: Where care-reminder notifications are enabled by the owner, the system shall present a local, non-network notification when a pet stat crosses its neglect threshold.
rationale: An always-on background pet with real-time decay risks the owner missing the check-in window entirely; an opt-in local reminder supports the daily-return habit for owners who want it, without imposing a mandatory interruption or any network dependency on owners who don't.
fit_criterion: When notifications are enabled and any stat crosses its defined neglect threshold, a local OS-level notification is presented in 100% of test trials; zero notifications are presented, and zero network requests are made, when the feature is disabled.
priority: should
confidence: medium
verification_method: test
ears_pattern: optional
status: draft
created_at: 2026-08-24
traces_from: [CON-002, CON-003]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-009 — Present optional local care-reminder notifications

## Description
Where care-reminder notifications are enabled by the owner, the system shall
present a local, non-network notification when a pet stat crosses its neglect
threshold.

## Rationale
An always-on background pet with real-time decay risks the owner missing the
check-in window entirely; an opt-in local reminder supports the daily-return habit
for owners who want it, without imposing a mandatory interruption or any network
dependency on owners who don't.

## Acceptance Criteria
### AC-1 — Notification presented when enabled and a threshold is crossed
```gherkin
Given the owner has enabled care-reminder notifications
When a pet stat crosses its defined neglect threshold
Then a local notification is presented to the owner via the operating system's native notification mechanism
And no network request is made in the course of presenting it
```

### AC-2 — No notification when the feature is disabled
```gherkin
Given the owner has not enabled care-reminder notifications
When a pet stat crosses its defined neglect threshold
Then no notification is presented
```

## Fit Criterion
When notifications are enabled and any stat crosses its defined neglect threshold,
a local OS-level notification is presented in 100% of test trials; zero
notifications are presented, and zero network requests are made, when the feature
is disabled.

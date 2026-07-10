---
id: FR-009
type: functional
tier: solution
title: Optional local care reminders
description: Where local reminders are enabled, the system shall display a local reminder notification when a care stat falls below its warning threshold.
rationale: A gentle nudge when the pet needs attention reinforces the daily-return habit; making it opt-in respects users who find notifications intrusive and keeps the ambient companion from becoming a nag.
fit_criterion: With reminders enabled, a notification is raised within 1 minute of any care stat crossing below its warning threshold; with reminders disabled, 0 notifications are raised under the same conditions.
priority: could
confidence: medium
verification_method: test
ears_pattern: optional
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

# FR-009 — Optional local care reminders

## Description
Where local reminders are enabled, the system shall display a local reminder
notification when a care stat falls below its warning threshold.

## Rationale
A gentle nudge when the pet needs attention reinforces the daily-return habit;
making it opt-in respects users who find notifications intrusive and keeps the
ambient companion from becoming a nag.

## Acceptance Criteria
### AC-1 — Reminder fires when enabled
```gherkin
Given reminders are enabled
When a care stat falls below its warning threshold
Then a local reminder notification is displayed within 1 minute
```

### AC-2 — No reminder when disabled
```gherkin
Given reminders are disabled
When a care stat falls below its warning threshold
Then no reminder notification is displayed
```

## Fit Criterion
With reminders enabled, a notification is raised within 1 minute of any care stat
crossing below its warning threshold; with reminders disabled, 0 notifications are
raised under the same conditions.

---
id: FR-001
type: functional
tier: solution
title: Persist pet state to local storage
description: When a pet stat changes or the application is closing, the system shall write the pet's current state and a last-saved timestamp to local storage.
rationale: The pet must feel continuous across sessions; without durable local state the pet would reset on every launch, breaking the attachment and daily-return loop that is the core success criterion.
fit_criterion: After any stat change followed by an application restart, 100% of restarts restore the exact stat values and last-saved timestamp that were current at the moment of the change, verified across 50 restart cycles.
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

# FR-001 — Persist pet state to local storage

## Description
When a pet stat changes or the application is closing, the system shall write the
pet's current state and a last-saved timestamp to local storage.

## Rationale
The pet must feel continuous across sessions; without durable local state the pet
would reset on every launch, breaking the attachment and daily-return loop that is
the core success criterion.

## Acceptance Criteria
### AC-1 — State survives a normal restart
```gherkin
Given a pet whose hunger stat has just changed to a new value
When the application is closed normally and reopened
Then the restored pet shows the same hunger value and last-saved timestamp
```

### AC-2 — Every stat change is captured
```gherkin
Given a running application
When any care stat changes value
Then a write to local storage records the new state before the next stat change
```

## Fit Criterion
After any stat change followed by an application restart, 100% of restarts restore
the exact stat values and last-saved timestamp that were current at the moment of
the change, verified across 50 restart cycles.

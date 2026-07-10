---
id: FR-010
type: functional
tier: solution
title: Recover from corrupted or missing save file
description: If the saved state file is missing or fails integrity validation on load, then the system shall start a new pet from default values without terminating.
rationale: A single unreadable save must never crash the always-on app or silently lose the user's data with no trace; degrading to a fresh pet while preserving the bad file keeps the app usable and the failure diagnosable.
fit_criterion: For an absent save file and for a deliberately corrupted save file, the application launches to a valid default pet in 100% of trials, exits 0, and retains the unreadable file under a quarantine name for diagnostics.
priority: must
confidence: high
verification_method: test
ears_pattern: unwanted
status: draft
created_at: 2026-07-10
traces_from: [FR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-010 — Recover from corrupted or missing save file

## Description
If the saved state file is missing or fails integrity validation on load, then the
system shall start a new pet from default values without terminating.

## Rationale
A single unreadable save must never crash the always-on app or silently lose the
user's data with no trace; degrading to a fresh pet while preserving the bad file
keeps the app usable and the failure diagnosable.

## Acceptance Criteria
### AC-1 — Missing save file yields a default pet
```gherkin
Given no saved state file exists on disk
When the application starts
Then the application creates a new pet from default values and does not crash
```

### AC-2 — Corrupted save file is quarantined, not loaded
```gherkin
Given a saved state file whose integrity check fails
When the application starts
Then the application starts a new default pet
And the unreadable file is retained under a quarantine name for diagnostics
```

## Fit Criterion
For an absent save file and for a deliberately corrupted save file, the application
launches to a valid default pet in 100% of trials, exits 0, and retains the
unreadable file under a quarantine name for diagnostics.

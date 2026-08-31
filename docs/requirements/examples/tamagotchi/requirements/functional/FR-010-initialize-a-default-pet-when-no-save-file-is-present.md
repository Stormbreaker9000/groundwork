---
id: FR-010
type: functional
tier: solution
title: Initialize a default pet when no save file is present
description: If no save file is present at application launch, then the system shall initialize a new default pet.
rationale: A first-ever launch and a launch after the save file has been lost to a crash, forced termination, or storage clearance are indistinguishable to the application, and both must produce a usable pet rather than a failure to start; without this the app has no defined entry state and cannot launch at all on a clean install.
fit_criterion: Across 100 missing-save fault-injection trials, the application launches with a valid default pet in 100% of trials, 0% result in a crash or unhandled error, and 0% create a quarantine artifact.
priority: must
confidence: high
verification_method: test
ears_pattern: unwanted
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

# FR-010 — Initialize a default pet when no save file is present

## Description
If no save file is present at application launch, then the system shall initialize a
new default pet.

## Rationale
A first-ever launch and a launch after the save file has been lost to a crash, forced
termination, or storage clearance are indistinguishable to the application, and both
must produce a usable pet rather than a failure to start; without this the app has no
defined entry state and cannot launch at all on a clean install.

## Acceptance Criteria
### AC-1 — No save file present
```gherkin
Given no save file exists at the expected storage location
When the application launches
Then a new default pet is initialized and displayed
And the application starts normally without crashing
```

### AC-2 — No quarantine artifact is produced when there is no file
```gherkin
Given no save file exists at the expected storage location
When the application launches
Then no file is written to the quarantine location
```

## Fit Criterion
Across 100 missing-save fault-injection trials, the application launches with a valid
default pet in 100% of trials, 0% result in a crash or unhandled error, and 0% create
a quarantine artifact.

---
id: FR-012
type: functional
tier: solution
title: Quarantine a save file that fails integrity validation
description: If a save file is present but fails integrity validation at application launch, then the system shall move that file to the quarantine location unmodified before initializing a new default pet.
rationale: Local storage can be corrupted by crashes, forced termination, or power loss, and crashing on a bad save would break the app entirely; silently deleting or overwriting the corrupt file destroys the only evidence available to diagnose the corruption, so the artifact must be preserved intact while the owner is still given a working app.
fit_criterion: Across 100 corrupted-save fault-injection trials, 100% of the original files are found byte-identical at the quarantine location afterward, 0% are deleted or overwritten in place, 100% of trials launch with a valid default pet, and 0% result in a crash or unhandled error.
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

# FR-012 — Quarantine a save file that fails integrity validation

## Description
If a save file is present but fails integrity validation at application launch, then
the system shall move that file to the quarantine location unmodified before
initializing a new default pet.

## Rationale
Local storage can be corrupted by crashes, forced termination, or power loss, and
crashing on a bad save would break the app entirely; silently deleting or overwriting
the corrupt file destroys the only evidence available to diagnose the corruption, so
the artifact must be preserved intact while the owner is still given a working app.

## Acceptance Criteria
### AC-1 — Corrupt save file is quarantined and a default pet is initialized
```gherkin
Given a save file exists at the expected storage location but fails integrity validation
When the application launches
Then the file is moved to the quarantine location byte-identical to its pre-launch content
And a new default pet is initialized and displayed
And the application starts normally without crashing
```

### AC-2 — Corrupt save file is never destroyed in place
```gherkin
Given a save file exists at the expected storage location but fails integrity validation
When the application launches
Then no file remains at the original storage location containing the corrupt content
And the corrupt content has not been deleted, truncated, or overwritten by the new default pet state
```

## Fit Criterion
Across 100 corrupted-save fault-injection trials, 100% of the original files are found
byte-identical at the quarantine location afterward, 0% are deleted or overwritten in
place, 100% of trials launch with a valid default pet, and 0% result in a crash or
unhandled error.

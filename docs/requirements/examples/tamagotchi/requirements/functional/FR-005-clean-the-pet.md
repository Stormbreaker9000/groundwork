---
id: FR-005
type: functional
tier: solution
title: Clean the pet
description: When the owner selects the clean action, the system shall reset the pet's cleanliness stat to its maximum value.
rationale: Cleaning is a distinct care need whose neglect contributes to sickness; giving it a dedicated restorative action keeps the care loop varied and legible.
fit_criterion: Each clean action sets the cleanliness stat to exactly its maximum value regardless of the prior value, verified from starting values of 0, mid-range, and near-maximum.
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

# FR-005 — Clean the pet

## Description
When the owner selects the clean action, the system shall reset the pet's
cleanliness stat to its maximum value.

## Rationale
Cleaning is a distinct care need whose neglect contributes to sickness; giving it a
dedicated restorative action keeps the care loop varied and legible.

## Acceptance Criteria
### AC-1 — Cleaning restores cleanliness fully
```gherkin
Given a pet with cleanliness below its maximum
When the owner selects the clean action
Then the cleanliness stat is set to its maximum value
```

## Fit Criterion
Each clean action sets the cleanliness stat to exactly its maximum value regardless
of the prior value, verified from starting values of 0, mid-range, and
near-maximum.

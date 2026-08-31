---
id: FR-006
type: functional
tier: solution
title: Put the pet to sleep
description: While the pet is not already in the Sleeping state, when the owner selects the sleep action, the system shall transition the pet to the Sleeping state.
rationale: Sleep is the fourth of the four defined care interactions, and a discrete Sleeping state gives the sleep action a persisted, loggable effect (FR-001, NFR-007) and a defined exit (FR-011). Sleep deliberately does not alter stat decay, and no requirement in this set renders the Sleeping state to the owner — FR-007 maps the mood display to the lowest stat value alone, and NFR-003 requires only mood and health status to be perceivable. Whether the Sleeping state should be owner-visible is open question Q-8 (owner product); until Q-8 closes, the value of this requirement rests on persistence and traceability rather than on anything the owner can see.
fit_criterion: The pet's state field equals Sleeping immediately after the sleep action is selected while the pet was previously Awake, in 100% of interaction tests; the state field remains Sleeping and unchanged if the action is selected again while already Sleeping.
priority: must
confidence: low
verification_method: test
ears_pattern: complex
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

# FR-006 — Put the pet to sleep

## Description
While the pet is not already in the Sleeping state, when the owner selects the
sleep action, the system shall transition the pet to the Sleeping state.

## Rationale
Sleep is the fourth of the four defined care interactions, and a discrete Sleeping
state gives the sleep action a persisted, loggable effect (FR-001, NFR-007) and a
defined exit (FR-011). Sleep deliberately does not alter stat decay, and no
requirement in this set renders the Sleeping state to the owner — FR-007 maps the
mood display to the lowest stat value alone, and NFR-003 requires only mood and
health status to be perceivable. Whether the Sleeping state should be owner-visible
is open question Q-8 (owner product); until Q-8 closes, the value of this
requirement rests on persistence and traceability rather than on anything the owner
can see.

## Acceptance Criteria
### AC-1 — Selecting sleep while awake transitions the pet
```gherkin
Given the pet is in the Awake state
When the owner selects the sleep action
Then the pet's state becomes Sleeping
```

### AC-2 — Selecting sleep while already sleeping is idempotent
```gherkin
Given the pet is already in the Sleeping state
When the owner selects the sleep action again
Then the pet's state remains Sleeping with no error
```

## Fit Criterion
The pet's state field equals Sleeping immediately after the sleep action is
selected while the pet was previously Awake, in 100% of interaction tests; the
state field remains Sleeping and unchanged if the action is selected again while
already Sleeping.

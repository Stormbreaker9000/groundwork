---
id: FR-007
type: functional
tier: solution
title: Display pet mood expression
description: While the application window is visible, the system shall display a pet mood expression matching the current stat thresholds.
rationale: The visible mood is how the pet communicates need without words; a legible expression is what prompts the user to act and creates the emotional feedback loop behind attachment.
fit_criterion: For each defined mood band, the displayed expression matches the band mapped to the current stats within 1 second of a threshold crossing, verified for every band boundary.
priority: must
confidence: medium
verification_method: test
ears_pattern: state
status: draft
created_at: 2026-07-10
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-007 — Display pet mood expression

## Description
While the application window is visible, the system shall display a pet mood
expression matching the current stat thresholds.

## Rationale
The visible mood is how the pet communicates need without words; a legible
expression is what prompts the user to act and creates the emotional feedback loop
behind attachment.

## Acceptance Criteria
### AC-1 — Mood tracks stat thresholds
```gherkin
Given a pet whose stats fall within the "content" mood band
When the window is visible
Then the pet displays the content mood expression
```

### AC-2 — Mood updates when a threshold is crossed
```gherkin
Given a visible pet displaying the content mood
When a stat decays below the threshold into the "unhappy" band
Then the displayed expression changes to the unhappy mood within 1 second
```

## Fit Criterion
For each defined mood band, the displayed expression matches the band mapped to the
current stats within 1 second of a threshold crossing, verified for every band
boundary.

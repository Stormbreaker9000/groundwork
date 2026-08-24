---
id: NFR-003
type: non_functional
tier: solution
title: Keyboard-only and screen-reader operability of the full care loop
description: Every interactive control and the pet's mood and health state shall be fully operable and perceivable by keyboard-only and screen-reader users, without reliance on color or on pointer input.
rationale: Keyboard-only and assistive-technology users are named in scope as secondary users, and a habit-forming daily interaction is exactly the kind of software that is unusable-in-practice if any one care action is mouse-only or if mood is conveyed by color alone. A colorblind-safe palette plus shape and text redundancy is the agreed v1 approach; a user-tunable palette is explicitly out of scope.
fit_criterion: 100% of interactive controls are reachable and operable by keyboard with a visible focus indicator; 100% of mood and health states expose a non-color textual equivalent through the platform accessibility API; text contrast >= 4.5:1 and non-text indicator contrast >= 3:1; zero critical or serious automated accessibility violations; a scripted screen-reader walkthrough of feed, play, clean and sleep completes with no unlabeled control.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-003, FR-004, FR-005, FR-006, FR-007, CON-003]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-003 — Keyboard-only and screen-reader operability of the full care loop

## ISO 25010 Characteristic
Interaction Capability → Operability, Inclusivity, Self-descriptiveness, User
assistance

## Quality Attribute Scenario
- **Source of stimulus:** A keyboard-only owner, or an owner using a screen
  reader.
- **Stimulus:** The owner navigates to and performs each of the four care
  actions — feed, play, clean, put to sleep — and reads the pet's current mood
  and health state.
- **Environment:** Normal operation, on each supported desktop platform using
  that platform's native accessibility stack and screen reader.
- **Artifact:** The application user interface — all interactive controls, focus
  order and focus indication, the mood expression, and any status or
  notification surface.
- **Response:** Each control is reached in a logical focus order, is operable
  from the keyboard, and announces a meaningful name and role; the mood and
  health state is announced as text and is distinguishable on screen by shape or
  label, not by hue alone; state changes caused by a care action are announced
  without the owner having to hunt for them.
- **Response measure:** 100% of interactive controls keyboard-reachable and
  operable with a visible focus indicator; 100% of mood and health states carry
  a non-color-dependent textual equivalent exposed to the accessibility API;
  contrast >= 4.5:1 for text and >= 3:1 for non-text state indicators; zero
  critical or serious violations from an automated accessibility scan; a
  scripted screen-reader walkthrough of all four care actions completes with 0
  unlabeled or unreachable controls.

## Rationale
Assistive-technology users are in scope as first-class owners. Because the
product's value is a repeated daily interaction, a single mouse-only control or a
color-only mood cue does not merely inconvenience these users — it removes them
from the habit loop entirely. Color-independence also covers colorblind owners
without needing the user-tunable palette that v1 excludes.

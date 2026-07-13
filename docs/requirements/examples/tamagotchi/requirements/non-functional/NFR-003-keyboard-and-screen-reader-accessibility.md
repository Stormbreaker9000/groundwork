---
id: NFR-003
type: non_functional
tier: solution
title: Keyboard and screen-reader accessibility
description: Every interactive control and mood indicator shall expose a text label and a non-color cue reachable by keyboard and by an assistive screen reader.
rationale: Keyboard and screen-reader users are explicitly in scope, and mood is conveyed visually; without text labels and non-color cues those users cannot perceive the pet's state or operate its care actions, excluding them from the entire experience.
fit_criterion: 100% of interactive controls are reachable and operable via keyboard alone; every control and mood state exposes an accessible name to the platform screen reader; every mood is distinguishable without color, verified against WCAG 2.1 AA success criteria 1.4.1, 2.1.1, and 4.1.2.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: [FR-007]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-003 — Keyboard and screen-reader accessibility

## ISO 25010 Characteristic
Interaction Capability → Accessibility

## Quality Attribute Scenario
- **Source of stimulus:** A keyboard-only user or a screen-reader user.
- **Stimulus:** The user navigates the pet's controls and reads the pet's current mood.
- **Environment:** Normal operation with an active platform screen reader and no pointing device.
- **Artifact:** The interactive controls, mood indicator, and their accessibility metadata.
- **Response:** Each control is focusable and operable from the keyboard, announces an accessible name, and each mood is signalled by shape or text in addition to color.
- **Response measure:** 100% of controls operable by keyboard alone; every control and mood exposes an accessible name; every mood is distinguishable without color; verified against WCAG 2.1 AA criteria 1.4.1, 2.1.1, and 4.1.2.

## Rationale
Keyboard and screen-reader users are explicitly in scope, and mood is conveyed
visually; without text labels and non-color cues those users cannot perceive the
pet's state or operate its care actions, excluding them from the entire experience.

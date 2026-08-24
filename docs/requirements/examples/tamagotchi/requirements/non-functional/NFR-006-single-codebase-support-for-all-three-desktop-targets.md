---
id: NFR-006
type: non_functional
tier: solution
title: Single-codebase support for all three desktop targets
description: The application shall be built from one shared codebase that runs with identical behavior on Windows, macOS and Linux, with all platform-specific code confined to a named platform-adapter layer.
rationale: All three desktop platforms are named targets and no design decision may foreclose any of them, so the portability boundary has to be structural rather than aspirational — platform conditionals scattered through the simulation logic are what makes a third platform unaffordable later. The acceptance suite is scoped to the whole functional set rather than a fixed range because the two most platform-divergent behaviours in the product are the wall-clock interval derived across an application close and the byte-identical file move into quarantine; a cross-platform suite that omits those is not testing the portability boundary it claims to. This target deliberately does not fix which platforms ship in v1, which remains an open product question.
fit_criterion: The full functional acceptance suite — every functional requirement in this set, including the wall-clock interval derivation across an application close and the byte-identical quarantine file move — passes unmodified on Windows, macOS and Linux; the count of platform conditionals outside the designated platform-adapter layer is 0; the count of recorded design decisions that foreclose any of the three targets is 0.
priority: must
confidence: medium
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-001, FR-002, FR-009, FR-011, FR-012, CON-003]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-006 — Single-codebase support for all three desktop targets

## ISO 25010 Characteristic
Flexibility → Adaptability and Installability

## Quality Attribute Scenario
- **Source of stimulus:** The owner installing and running the application on
  their platform of choice; and the developer adding support for a target not
  yet shipped.
- **Stimulus:** The same source tree is built, packaged and run on Windows, on
  macOS, and on Linux.
- **Environment:** Current supported OS versions of each of the three targets;
  the v1 ship order is deliberately not fixed by this requirement.
- **Artifact:** The whole codebase, and in particular the platform-touching
  seams — local data directory paths; the quarantine location and the
  byte-identical file move into it (FR-012), whose move semantics, path
  conventions and file-locking behaviour all differ per platform; wall-clock and
  timer access, including the elapsed-interval derivation across an application
  close that FR-011 and FR-002 depend on; native notifications; accessibility
  integration; and rendering.
- **Response:** The full care loop, persistence, offline decay, wake,
  save-file quarantine and mood display behave identically on each target; every
  platform difference is resolved inside a single named platform-adapter layer,
  so adding or enabling a target touches only that layer.
- **Response measure:** The acceptance suite for every functional requirement in
  this set passes unmodified on all three platforms in CI — the quarantine move
  and the across-close interval derivation included, not excepted; 0 platform
  conditionals outside the platform-adapter layer; 0 recorded design decisions
  that foreclose any of the three targets.

## Rationale
The constraint is that no decision may foreclose a target, not that all three
ship at once. Confining platform differences to one adapter layer is what makes
that constraint checkable and keeps a later target cheap, while leaving the v1
ship order (Q-3) genuinely open rather than settled by accident of
implementation.

The suite is bound to the whole functional set because the two behaviours a
fixed range most easily drops are the two that diverge most: deriving a
wall-clock interval across an application close exercises clock and timer access
per platform, and moving a file byte-identically into quarantine exercises move
semantics, path conventions and locking. Both are named in the Artifact list
above, so omitting them from the suite would leave the seams this requirement
identifies untested.

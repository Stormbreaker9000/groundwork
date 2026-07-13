---
id: NFR-006
type: non_functional
tier: solution
title: Cross-platform desktop support
description: The application shall run on current Windows, macOS, and Linux desktop environments from a single codebase without platform-specific feature loss.
rationale: The audience spans all three desktop platforms and the product targets ubiquity as an ambient companion; a build that only works on one OS forfeits a large share of potential daily users and the habit-formation network effect.
fit_criterion: The full acceptance-test suite passes on a supported version of each of Windows, macOS, and Linux; every functional requirement is available on all three, with 0 platform-exclusive features in the shipped scope.
priority: should
confidence: medium
verification_method: test
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

# NFR-006 — Cross-platform desktop support

## ISO 25010 Characteristic
Flexibility (Portability) → Installability and Adaptability

## Quality Attribute Scenario
- **Source of stimulus:** A desktop owner on any of the three supported operating systems.
- **Stimulus:** The user installs and runs the application on their platform.
- **Environment:** A clean supported install of Windows, macOS, or Linux.
- **Artifact:** The application package and its platform-abstraction layer.
- **Response:** The application installs, launches, and exposes the full feature set on each platform from one codebase.
- **Response measure:** The acceptance-test suite passes on a supported version of each OS; every functional requirement is available on all three; 0 platform-exclusive features ship.

## Rationale
The audience spans all three desktop platforms and the product targets ubiquity as
an ambient companion; a build that only works on one OS forfeits a large share of
potential daily users and the habit-formation network effect. Which platforms ship
in v1 (all three vs Windows-first) is still open (Q-3).

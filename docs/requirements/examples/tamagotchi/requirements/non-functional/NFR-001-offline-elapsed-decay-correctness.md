---
id: NFR-001
type: non_functional
tier: solution
title: Offline-elapsed decay correctness
description: The pet-state engine shall compute post-offline stat values that match the reference decay model within a bounded error for elapsed intervals up to 30 days.
rationale: Attachment depends on the pet's state feeling fair and predictable; if offline decay is miscomputed the pet may appear to have died or barely changed after a realistic absence, breaking trust in the simulation and the daily-return loop.
fit_criterion: For 1000 sampled elapsed intervals between 1 minute and 30 days, the computed value of every stat is within +/- 1 stat unit of the reference decay function output; 0 samples produce a value outside the valid stat range.
priority: must
confidence: medium
verification_method: test
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

# NFR-001 — Offline-elapsed decay correctness

## ISO 25010 Characteristic
Functional Suitability → Functional Correctness

## Quality Attribute Scenario
- **Source of stimulus:** The system clock (elapsed wall-clock time while the app was closed).
- **Stimulus:** The application is launched after an arbitrary offline interval since the last save.
- **Environment:** Normal operation, cold start, across the full supported range of elapsed intervals.
- **Artifact:** The pet-state decay computation.
- **Response:** Each stat is recomputed from the saved value and the elapsed interval using the reference decay model.
- **Response measure:** For 1000 sampled intervals between 1 minute and 30 days, every stat is within +/- 1 stat unit of the reference decay function output, and 0 samples fall outside the valid stat range.

## Rationale
Attachment depends on the pet's state feeling fair and predictable; if offline
decay is miscomputed the pet may appear to have died or barely changed after a
realistic absence, breaking trust in the simulation and the daily-return loop.

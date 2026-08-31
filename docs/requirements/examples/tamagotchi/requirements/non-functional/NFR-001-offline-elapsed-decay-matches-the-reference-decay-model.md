---
id: NFR-001
type: non_functional
tier: solution
title: Offline-elapsed decay matches the reference decay model
description: On launch after any offline interval, each pet stat shall be decayed to within ±1 stat unit of the value the reference decay model produces for that same elapsed interval.
rationale: Offline decay is the mechanism the entire daily-return loop rests on — if the pet's condition on relaunch does not match what elapsed real time implies, the owner's mental model of "my neglect had consequences" breaks and the attachment loop fails. Expressing correctness against a reference model rather than hardcoded rates keeps the target verifiable while the decay-curve balance values (Q-1) remain open.
fit_criterion: For at least 20 log-spaced offline intervals from 1 minute to 30 days, every stat after launch is within ±1 stat unit of the reference decay model's output for the same interval and starting state; 0 out-of-range results. For at least 5 non-positive elapsed intervals — exactly zero, and negative intervals produced by a backward wall-clock change — every stat after launch equals its last-committed value exactly (0 delta), with 0 stats increased and 0 stats decayed.
priority: must
confidence: medium
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-001 — Offline-elapsed decay matches the reference decay model

## ISO 25010 Characteristic
Functional Suitability → Functional correctness

## Quality Attribute Scenario
- **Source of stimulus:** The passage of real wall-clock time while the
  application is not running, surfaced when the owner relaunches.
- **Stimulus:** The application launches after an elapsed interval T since the
  last committed save, where T may be positive or, if the wall clock has moved
  backward, zero or negative.
- **Environment:** Normal operation; the positive matrix spans T from 1 minute to
  30 days, and the clock-regression matrix covers T at exactly zero and T
  negative (manual clock change, DST shift, NTP correction); a valid save file is
  present; elapsed time is derived from wall-clock timestamps.
- **Artifact:** The offline decay computation and the pet state model.
- **Response:** Decay is computed for every stat from the last-save timestamp to
  the current time and applied before the pet is first rendered, so the owner
  sees the post-decay state and never the stale pre-decay state. Where T is at or
  below zero, the interval is treated as zero elapsed time per FR-002, so no stat
  moves in either direction.
- **Response measure:** For at least 20 log-spaced intervals across 1 minute to
  30 days, each resulting stat is within ±1 stat unit of the reference decay
  model's value for the same interval and starting state; 0 out-of-range
  results. For at least 5 non-positive intervals (T = 0 and T < 0), each stat
  after launch equals its last-committed value exactly — 0 stats increased and 0
  stats decayed.

## Rationale
Offline decay is the mechanism the daily-return loop rests on. If relaunch state
does not match what elapsed time implies, the owner's sense that neglect has
consequences collapses and the habit the product exists to create does not form.
Testing against a reference model as an oracle keeps this target verifiable while
the decay curve and balance values remain an open product question (Q-1). The
non-positive-interval clause gives FR-002's clock-regression rule a measurable
oracle, so a backward clock cannot silently gift the owner a healthier pet.

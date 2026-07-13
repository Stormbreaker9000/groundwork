---
id: BR-002
type: business_rule
tier: business
title: Decay accrues only for real forward elapsed time
description: Pet-stat decay accrues only for real, forward-moving elapsed wall-clock time since the last save and is capped at the configured maximum offline interval.
rationale: Decay must be fair and not exploitable; crediting backward clock changes as negative decay would let users rewind their clock to revive a pet, and uncapped decay over very long absences would guarantee death regardless of intent, so both edges are bounded by policy.
fit_criterion: For a non-negative elapsed interval, decay equals the reference function of that interval capped at the maximum; for a detected backward clock change since the last save, decay applied is 0 and no stat is increased.
priority: must
confidence: medium
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: [FR-002]
scope: project
parent_scope: null
---

# BR-002 — Decay accrues only for real forward elapsed time

## Statement
Pet-stat decay accrues only for real, forward-moving elapsed wall-clock time since
the last save and is capped at the configured maximum offline interval.

## Implemented by
FR-002 (Apply offline-elapsed decay on launch) enforces this policy in the system.

## Rationale
Decay must be fair and not exploitable; crediting backward clock changes as negative
decay would let users rewind their clock to revive a pet, and uncapped decay over
very long absences would guarantee death regardless of intent, so both edges are
bounded by policy.

## Fit Criterion
For a non-negative elapsed interval, decay equals the reference function of that
interval capped at the maximum; for a detected backward clock change since the last
save, decay applied is 0 and no stat is increased.

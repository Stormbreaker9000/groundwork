---
id: BR-001
type: business_rule
tier: business
title: Death only after sustained neglect
description: A pet reaches the dead state only after its care stats remain fully depleted beyond a defined sustained-neglect threshold, and upon death the pet is reset to a new pet according to the death-handling policy.
rationale: The care metaphor requires real stakes, but a pet that dies from a single missed day would feel punishing and drive users away; the policy fixes both the grace period before death and what death means, in one place, so the balance can be tuned without touching enforcement logic.
fit_criterion: Death occurs if and only if care stats have been continuously depleted past the sustained-neglect threshold with no intervening care action; any care action before the threshold resets the neglect timer.
priority: must
confidence: low
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: [FR-008]
scope: project
parent_scope: null
---

# BR-001 — Death only after sustained neglect

## Statement
A pet reaches the dead state only after its care stats remain fully depleted beyond
a defined sustained-neglect threshold, and upon death the pet is reset to a new pet
according to the death-handling policy.

## Implemented by
FR-008 (Progress neglect to sickness and death) enforces this policy in the system.

## Rationale
The care metaphor requires real stakes, but a pet that dies from a single missed day
would feel punishing and drive users away; the policy fixes both the grace period
before death and what death means, in one place, so the balance can be tuned without
touching enforcement logic. Whether death is permanent or a configurable soft reset
is still open (Q-2), which is why this rule is held at low confidence.

## Fit Criterion
Death occurs if and only if care stats have been continuously depleted past the
sustained-neglect threshold with no intervening care action; any care action before
the threshold resets the neglect timer.

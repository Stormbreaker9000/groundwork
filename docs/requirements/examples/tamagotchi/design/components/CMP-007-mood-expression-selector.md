---
id: CMP-007
type: component
title: Mood Expression Selector
description: The rule that maps a pet's current stat values to a mood expression, by locating the mood-threshold band containing the pet's lowest stat value.
traces_from: [FR-007, NFR-003, NFR-007]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Selects the pet's mood expression from the band containing its lowest stat value.
boundary: internal
depends_on: [IF-001, IF-016]
---

# CMP-007 — Mood Expression Selector

The rule that maps a pet's current stat values to a mood expression, by locating the
mood-threshold band containing the pet's lowest stat value.

## Responsibility
Selects the pet's mood expression from the band containing its lowest stat value.

## Rationale
FR-007's reduction rule is the minimum, not the mean — an average would let one
critically low stat hide behind healthy ones — and that rule is domain logic, not
rendering. Keeping selection separate from CMP-016 is also what NFR-003 needs: the
presentation surface consumes a semantic mood it can expose as text through the
platform accessibility API, rather than deriving one from what it drew. The band
boundaries themselves are configuration, so re-tuning them under Q-1 does not touch
this component.

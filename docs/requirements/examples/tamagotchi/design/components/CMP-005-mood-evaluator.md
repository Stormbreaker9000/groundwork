---
id: CMP-005
type: component
title: Mood Evaluator
description: The rule that maps the pet's current Stats and lifecycle state onto a single named Mood value.
traces_from:
- FR-007
- NFR-003
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Derives the pet's current Mood as a named semantic value.
boundary: internal
depends_on:
- IF-005
- IF-006
---

# CMP-005 — Mood Evaluator

The rule that maps the pet's current Stats and lifecycle state onto a single named
Mood value.

## Responsibility
Derives the pet's current Mood as a named semantic value.

## Rationale
NFR-003 is what forces this seam. Requiring every Mood to be perceivable without
colour and announceable by an assistive screen reader means Mood must exist as a
named value in the model, derived by a rule, *before* anything is drawn — the
accessible name and the sprite then become two renderings of one value rather than
two independent mappings from Stats that could disagree. FR-007's one-second
threshold-crossing budget is met by deriving on change rather than on a repaint
tick, which also keeps the idle path quiet for NFR-002.

Confidence is **medium**: the seam follows directly from NFR-003, but the band
boundaries themselves are configuration the requirement set describes only as
"defined", and FR-007 arrived from the requirements stage at medium confidence.

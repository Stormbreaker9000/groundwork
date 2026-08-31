---
id: CMP-008
type: component
title: Care Interaction Handler
description: The application of an owner-selected care-loop action — feed, play, clean or sleep — to the current pet, producing the resulting pet state.
traces_from: [FR-001, FR-003, FR-004, FR-005, FR-006]
traces_to:
  adr: []
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Applies an owner-selected care-loop action to the current pet.
boundary: internal
depends_on: [IF-001, IF-002, IF-005, IF-007]
---

# CMP-008 — Care Interaction Handler

The application of an owner-selected care-loop action — feed, play, clean or sleep —
to the current pet, producing the resulting pet state.

## Responsibility
Applies an owner-selected care-loop action to the current pet.

## Rationale
The care loop is the fixed set of four interactions the glossary names, and requirements A-8 rules
out a fifth, so one component can own the whole set without an open-ended surface.
Three of the four are the same shape — raise the corresponding stat by its configured
increment, capped at the stat maximum by CMP-001's invariant — and the fourth delegates
to CMP-006 rather than touching the Awake/Sleeping field itself.

This component returns the resulting pet state to its caller rather than driving the
display, which keeps the owner-facing surface a caller of the care loop and not also
its callee.

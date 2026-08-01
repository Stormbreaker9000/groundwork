---
id: CMP-002
type: component
title: Decay Engine
description: A stateless evaluator of the reference decay model that turns a saved stat set and an elapsed interval into the stat set that should hold now.
traces_from:
- FR-002
- NFR-001
- BR-002
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Computes the Decay accrued by a pet's Stats over a given elapsed interval.
boundary: internal
depends_on: []
---

# CMP-002 — Decay Engine

A stateless evaluator of the reference decay model that turns a saved stat set and
an elapsed interval into the stat set that should hold now.

## Responsibility
Computes the Decay accrued by a pet's Stats over a given elapsed interval.

## Rationale
FR-002 is the requirement that makes this a resumable simulation rather than a game
loop: time advances while the process does not exist, so Decay cannot be maintained
by an in-session tick. That forces it to be a pure function of (saved state,
elapsed interval), separate from the store that supplies the saved value and from
the clock that supplies the interval. NFR-001 is why the separation has to be a
real seam rather than a helper: a +/- 1 unit tolerance across intervals from one
minute to thirty days is only testable if the computation is deterministic and
reachable without a real clock, which is also why this component takes the interval
as an argument and never reads the time itself. BR-002 lives here as the two guards
on that function — a negative interval yields zero Decay, and a positive one is
capped at the configured maximum offline interval.

Confidence is **low** because of open question **Q-1**: the decay curve and its
rate tuning are unresolved, and this component *is* that curve. Its seam and its
signature are settled; the model it evaluates is not. Answering Q-1 does not move
this component, but nothing here can be verified against NFR-001's tolerance until
it is answered.

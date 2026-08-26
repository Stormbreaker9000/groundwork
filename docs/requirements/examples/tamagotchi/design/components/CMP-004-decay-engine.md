---
id: CMP-004
type: component
title: Decay Engine
description: The pure computation that maps a starting pet state and an elapsed interval to the decayed pet state, in one bounded step and without reading a clock.
traces_from: [FR-002, NFR-001, NFR-008, NFR-009]
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
responsibility: Computes the decayed pet state for a given starting pet state and elapsed interval.
boundary: internal
depends_on: [IF-001]
---

# CMP-004 — Decay Engine

The pure computation that maps a starting pet state and an elapsed interval to the
decayed pet state, in one bounded step and without reading a clock.

## Responsibility
Computes the decayed pet state for a given starting pet state and elapsed interval.

## Rationale
NFR-008 carries an explicit testability constraint on the design (A-17): the decay
computation must be invocable directly, a thousand times in a loop, with an in-memory
starting state and no save file read and no application launch. That forbids decay
being a stage inside the launch routine and makes it its own unit that the launch path
calls. NFR-008's response also forbids walking the interval tick by tick, so the
mapping is closed-form over the interval.

The elapsed interval arrives as a parameter, never from an ambient clock read: FR-002's
clamp of a non-positive interval to zero elapsed time, and NFR-001's requirement to
drive the computation through a negative-interval matrix, are both only executable if
the interval is supplied. This component applies FR-002's clamp rule; it does not apply
FR-011's re-basing rule, which belongs to a deadline rather than to a quantity (A-6).

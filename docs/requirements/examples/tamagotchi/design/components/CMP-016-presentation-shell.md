---
id: CMP-016
type: component
title: Presentation Shell
description: The owner-facing surface — the rendered pet with its mood expression, health status and stats, and the controls through which the care loop is exercised.
traces_from: [FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, NFR-002, NFR-003, NFR-006, CON-001, CON-003]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: [DIA-004]
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Owns the owner's view of the pet and the controls the care loop is exercised through.
boundary: internal
depends_on: [IF-002, IF-008, IF-027, IF-028]
---

# CMP-016 — Presentation Shell

The owner-facing surface — the rendered pet with its mood expression, health status and
stats, and the controls through which the care loop is exercised.

## Responsibility
Owns the owner's view of the pet and the controls the care loop is exercised through.

## Rationale
NFR-003 requires mood and health status to be perceivable as text through each
platform's native accessibility API, without reliance on colour or pointer input, which
makes this surface a consumer of semantic state rather than a producer of pixels that
something else must interpret. CON-001 bounds the shell everything is built inside — a
single shared surface is what keeps one codebase viable for a team with no platform
specialists, and the runtime choice itself is a decision record rather than a behaviour
of this component.

Two of the six seams NFR-006 enumerates — rendering, and accessibility integration —
touch this component, and neither is held here. NFR-006 does not merely prefer them
inside the platform-adapter layer, it counts conditionals outside that layer against a
target of zero, and NFR-003's measure runs through three distinct native accessibility
stacks. So this component owns what the owner sees and what the pet's state means in
words, and reaches CMP-017 for both the surface it is painted onto and the native API
the words are announced through. That division is also what keeps the seam honest under
Q-3's staged rollout: the semantic content is written once, and only the adapter changes
when macOS and Linux follow Windows.

This component is also the only element an owner acts on, which is why FR-009's
enablement preference is read and changed from here even though CMP-014 owns it. A
preference with no owner-reachable writer is a feature permanently at its default.

Confidence is low: Q-8 — whether the Sleeping state is rendered to the owner — is
still_open, and it is a question about precisely this component's surface. No
requirement in the set renders Sleeping today.

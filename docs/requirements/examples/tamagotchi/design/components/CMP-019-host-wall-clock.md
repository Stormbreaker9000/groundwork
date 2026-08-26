---
id: CMP-019
type: component
title: Host Wall Clock
description: The operating system's wall clock, the source of every timestamp and elapsed interval the pet simulation reads, and an owner-movable one.
traces_from: [FR-002, FR-011, NFR-001]
traces_to:
  adr: []
  diagrams: [DIA-001, DIA-002]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Supplies the host's current wall-clock time to the application.
boundary: external
depends_on: []
---

# CMP-019 — Host Wall Clock

The operating system's wall clock, the source of every timestamp and elapsed interval
the pet simulation reads, and an owner-movable one.

## Responsibility
Supplies the host's current wall-clock time to the application.

## Rationale
The whole product rests on elapsed real time measured across application closes, and
the design context names the platform wall clock as an integration point alongside the
notification service. Modelling it as a component gives the design's most delicate
assumption a place to live: A-7 requires the host to expose backward movement
observably, as a non-positive interval, rather than silently smoothing it into a
slow-forward clock — an OS that smooths defeats both of A-6's rules at once, FR-002's
clamp and FR-011's re-basing.

Confidence is medium for exactly that reason: A-7 is an inherited assumption about this
external system's behaviour that no requirement in the set verifies.

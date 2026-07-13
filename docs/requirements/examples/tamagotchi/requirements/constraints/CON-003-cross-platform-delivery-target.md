---
id: CON-003
type: constraint
tier: business
title: Cross-platform delivery target
description: The delivered product shall target Windows, macOS, and Linux desktop environments, with no design decision that forecloses shipping on any of the three.
rationale: Cross-platform reach is a stated business boundary for the companion; committing to it up front prevents platform-locking architecture choices, even though which platforms ship first in v1 is not yet decided.
fit_criterion: No component in the architecture depends on a single-OS-only technology without a documented cross-platform equivalent; a build can be produced for each of the three targets from the same source tree.
priority: should
confidence: low
verification_method: inspection
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: [NFR-006]
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-003 — Cross-platform delivery target

## Statement
The delivered product shall target Windows, macOS, and Linux desktop environments,
with no design decision that forecloses shipping on any of the three.

## Category
business

## Bounds / Implemented by
Bounds cross-platform desktop support (NFR-006) by fixing the set of platforms the
architecture must keep reachable. The v1 subset (all three vs Windows-first) is
open (Q-3).

## Rationale
Cross-platform reach is a stated business boundary for the companion; committing to
it up front prevents platform-locking architecture choices, even though which
platforms ship first in v1 is not yet decided.

## Fit Criterion
No component in the architecture depends on a single-OS-only technology without a
documented cross-platform equivalent; a build can be produced for each of the three
targets from the same source tree.

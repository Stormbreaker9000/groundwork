---
id: CON-003
type: constraint
tier: business
title: No design decision may foreclose Windows, macOS or Linux
description: The product shall target Windows, macOS and Linux desktop environments. No design, dependency or platform-API decision may foreclose shipping on any of the three, irrespective of which platforms are selected to ship first.
rationale: "All three desktop environments are named targets, and the cost of un-picking a platform-exclusive dependency after it has spread through the codebase is far higher than avoiding it up front. The boundary is therefore on the design space rather than on the release plan: which platforms ship in v1 (all three, or Windows-first) is open question Q-3 (owner: product) and is deliberately not asserted here. Q-3's answer changes the ship order but not this boundary, which holds either way — hence medium rather than low confidence."
fit_criterion: The application builds and its full care loop passes acceptance on Windows, macOS and Linux from a single source tree. Design review of the core path finds 0 platform-exclusive APIs, dependencies or file-path assumptions that lack a documented working equivalent on the other two targets.
priority: must
confidence: medium
verification_method: inspection
status: draft
created_at: 2026-08-24
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-003 — No design decision may foreclose Windows, macOS or Linux

## Statement
The product shall target Windows, macOS and Linux desktop environments.
No design, dependency or platform-API decision may foreclose shipping on
any of the three, irrespective of which platforms are selected to ship
first. This constraint does not assert a v1 ship order.

## Category
environmental

## Bounds / Implemented by
Bounds NFR-006 (single-codebase support for all three desktop targets),
FR-009 (care-reminder notifications, whose delivery mechanism differs
per platform and must not be built on one platform's service alone),
and NFR-003 (keyboard and screen-reader operability, which must be
reachable through each platform's own assistive-technology stack rather
than a single vendor's).

## Rationale
All three desktop environments are named targets, and un-picking a
platform-exclusive dependency after it has spread through the codebase
costs far more than avoiding it up front. The boundary is on the design
space, not the release plan: which platforms ship in v1 (all three, or
Windows-first) is open question Q-3, owned by product, and is not
asserted here. Q-3's answer changes the ship order but not this
boundary, which holds either way.

## Fit Criterion
The application builds and its full care loop passes acceptance on
Windows, macOS and Linux from a single source tree. Design review of the
core path finds 0 platform-exclusive APIs, dependencies or file-path
assumptions that lack a documented working equivalent on the other two
targets.

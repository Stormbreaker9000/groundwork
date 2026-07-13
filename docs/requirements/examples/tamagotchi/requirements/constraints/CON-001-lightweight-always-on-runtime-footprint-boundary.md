---
id: CON-001
type: constraint
tier: solution
title: Lightweight always-on runtime footprint boundary
description: The delivered product shall use an application runtime whose idle resident-memory and CPU overhead fit within the idle-footprint budget on the reference machine, excluding runtimes that cannot meet it.
rationale: A heavy runtime such as a full Chromium/Electron shell carries a baseline memory and CPU cost that alone can exceed the idle budget for an always-on background app; this constraint removes such runtimes from the design space rather than treating footprint as something to be tuned after the fact.
fit_criterion: The chosen runtime's measured baseline idle overhead on the reference machine is within the NFR-002 budget with headroom for the app's own state; any candidate runtime whose baseline alone exceeds the budget is rejected during technology selection.
priority: must
confidence: low
verification_method: analysis
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: [NFR-002]
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-001 — Lightweight always-on runtime footprint boundary

## Statement
The delivered product shall use an application runtime whose idle resident-memory
and CPU overhead fit within the idle-footprint budget on the reference machine,
excluding runtimes that cannot meet it.

## Category
technical

## Bounds / Implemented by
Bounds the design space of the idle-footprint target (NFR-002) by constraining the
runtime/framework choice (Q-4). A heavy runtime whose idle baseline alone exceeds
the budget is disallowed.

## Rationale
A heavy runtime such as a full Chromium/Electron shell carries a baseline memory
and CPU cost that alone can exceed the idle budget for an always-on background app;
this constraint removes such runtimes from the design space rather than treating
footprint as something to be tuned after the fact.

## Fit Criterion
The chosen runtime's measured baseline idle overhead on the reference machine is
within the NFR-002 budget with headroom for the app's own state; any candidate
runtime whose baseline alone exceeds the budget is rejected during technology
selection.

---
id: CON-002
type: constraint
tier: solution
title: Fully offline local-only operation
description: The application shall operate fully offline, making no outbound network connection for any core pet-simulation functionality.
rationale: The product is defined as a private, offline, local-only companion; requiring the network for core function would break its promise, create a privacy surface, and make the pet unusable when disconnected.
fit_criterion: With networking disabled at the OS level, 100% of core features (persistence, decay, all interactions, mood, lifecycle) function normally; a traffic capture during full-feature exercise shows 0 outbound connections required for core function.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: [NFR-005, FR-001]
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-002 — Fully offline local-only operation

## Statement
The application shall operate fully offline, making no outbound network connection
for any core pet-simulation functionality.

## Category
technical

## Bounds / Implemented by
Bounds local-only data handling (NFR-005) and local state persistence (FR-001) by
forbidding any server or cloud dependency in the core loop.

## Rationale
The product is defined as a private, offline, local-only companion; requiring the
network for core function would break its promise, create a privacy surface, and
make the pet unusable when disconnected.

## Fit Criterion
With networking disabled at the OS level, 100% of core features (persistence,
decay, all interactions, mood, lifecycle) function normally; a traffic capture
during full-feature exercise shows 0 outbound connections required for core
function.

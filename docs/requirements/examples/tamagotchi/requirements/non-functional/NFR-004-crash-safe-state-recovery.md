---
id: NFR-004
type: non_functional
tier: solution
title: Crash-safe state recovery
description: Following a forced termination or power loss, the application shall recover the last committed pet state without corruption on the next launch.
rationale: An always-on app will inevitably be force-quit or lose power mid-write; if that corrupts the single save file the user loses their pet, which is the most attachment-destroying failure the product can have, so writes must be atomic and recoverable.
fit_criterion: Across 200 fault-injection trials that kill the process at randomized points during a state write, 100% of subsequent launches load either the last fully committed state or a valid default, and 0 trials load a partially written or corrupt state.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: [FR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-004 — Crash-safe state recovery

## ISO 25010 Characteristic
Reliability → Recoverability

## Quality Attribute Scenario
- **Source of stimulus:** A forced-quit, OS kill, or power loss.
- **Stimulus:** The process is terminated at an arbitrary point, possibly mid-write to the save file.
- **Environment:** Normal operation with a state write in progress.
- **Artifact:** The state-persistence layer and the on-disk save file.
- **Response:** On the next launch the application loads the last fully committed state, or falls back to a valid default, never a partially written file.
- **Response measure:** Across 200 fault-injection trials killing the process at randomized write points, 100% of launches load a fully committed state or valid default and 0 load a corrupt state.

## Rationale
An always-on app will inevitably be force-quit or lose power mid-write; if that
corrupts the single save file the user loses their pet, which is the most
attachment-destroying failure the product can have, so writes must be atomic and
recoverable.

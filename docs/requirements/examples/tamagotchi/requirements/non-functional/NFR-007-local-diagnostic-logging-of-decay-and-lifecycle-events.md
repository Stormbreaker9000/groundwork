---
id: NFR-007
type: non_functional
tier: solution
title: Local diagnostic logging of decay and lifecycle events
description: The application shall write a structured local log record for every decay computation and every pet lifecycle transition, sufficient to independently recompute the resulting state from the record alone.
rationale: Decay happens while the app is closed and is therefore invisible; without a record of what was computed and why, neither the owner nor a developer can tell a balance-tuning problem from a real defect when the pet's condition looks wrong on relaunch. It is also the evidence source that makes NFR-001's correctness target diagnosable rather than merely pass or fail.
fit_criterion: 100% of decay computations and lifecycle transitions produce exactly one structured record containing timestamp, event type, elapsed interval, pre-state, post-state and computed deltas; replaying >= 100 recorded decay events through the reference model reproduces the logged post-state with 0 mismatches; the log is size-bounded by rotation and never leaves the machine.
priority: should
confidence: high
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-002, FR-008, FR-010]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-007 — Local diagnostic logging of decay and lifecycle events

## ISO 25010 Characteristic
Extension: Observability (supporting Maintainability → Analysability)

## Quality Attribute Scenario
- **Source of stimulus:** The application itself, on behalf of an owner or
  developer investigating a pet state that looks wrong.
- **Stimulus:** A decay computation runs, or a lifecycle transition occurs —
  launch, save, load, save-file quarantine, mood change, onset of sickness,
  terminal transition, sleep and wake.
- **Environment:** Normal operation at the default log level, with no network
  available.
- **Artifact:** The local diagnostic log on disk.
- **Response:** Exactly one structured record is appended per event, carrying
  the timestamp, event type, elapsed interval where applicable, the pre-event
  and post-event stat values, and the computed deltas — written locally and
  never transmitted.
- **Response measure:** 100% of decay computations and lifecycle transitions
  produce exactly one such record; replaying >= 100 recorded decay events
  through the reference model reproduces each logged post-state with 0
  mismatches; total log size stays under a fixed rotation cap indefinitely; 0
  outbound transmissions of log content.

## Rationale
Offline decay is the one behavior the owner never watches happen, so when the
pet's condition on relaunch surprises them there is otherwise no evidence to
reason from. A record that permits independent recomputation turns "the decay
feels wrong" into a decidable question, and keeps the balance-tuning work (Q-1)
grounded in observed data rather than impression.

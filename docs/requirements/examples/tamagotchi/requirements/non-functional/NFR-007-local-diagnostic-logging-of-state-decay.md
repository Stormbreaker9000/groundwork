---
id: NFR-007
type: non_functional
tier: solution
title: Local diagnostic logging of state decay
description: The application shall record structured local log entries for every state-decay computation and pet lifecycle transition.
rationale: Decay is computed from wall-clock deltas that are hard to reproduce after the fact; a local log of each computation and transition is what lets a developer or a bug-reporting user diagnose "why did my pet die overnight" without any telemetry leaving the device.
fit_criterion: For every launch-time decay computation and every lifecycle transition (born, sick, recovered, dead, reset), a log entry is written locally capturing the timestamp, elapsed interval, and before/after stat values; a 24-hour session produces a parseable log with 0 missing transition entries.
priority: should
confidence: medium
verification_method: inspection
status: draft
created_at: 2026-07-10
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-007 — Local diagnostic logging of state decay

## ISO 25010 Characteristic
Observability (extension) → Logging

## Quality Attribute Scenario
- **Source of stimulus:** A developer or a bug-reporting user investigating unexpected pet state.
- **Stimulus:** A decay computation runs at launch, or the pet changes lifecycle state.
- **Environment:** Normal operation, with logs written to a local application data directory.
- **Artifact:** The decay engine, the lifecycle state machine, and the local log writer.
- **Response:** A structured entry is appended locally capturing the event, elapsed interval, and before/after stat values.
- **Response measure:** Every decay computation and every lifecycle transition produces a parseable local log entry; a 24-hour session has 0 missing transition entries.

## Rationale
Decay is computed from wall-clock deltas that are hard to reproduce after the fact;
a local log of each computation and transition is what lets a developer or a
bug-reporting user diagnose "why did my pet die overnight" without any telemetry
leaving the device.

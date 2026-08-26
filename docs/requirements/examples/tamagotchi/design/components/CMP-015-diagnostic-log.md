---
id: CMP-015
type: component
title: Diagnostic Log
description: The local, user-readable structured log of every decay computation and pet lifecycle transition, held under a fixed rotation cap.
traces_from: [NFR-005, NFR-007, CON-002]
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
responsibility: Writes the structured local record for each decay computation and lifecycle transition.
boundary: internal
depends_on: [IF-018, IF-021]
---

# CMP-015 — Diagnostic Log

The local, user-readable structured log of every decay computation and pet lifecycle
transition, held under a fixed rotation cap.

## Responsibility
Writes the structured local record for each decay computation and lifecycle transition.

## Rationale
NFR-007 requires exactly one structured record per decay computation and per lifecycle
transition, carrying pre-state, post-state and deltas, and replayable through the
reference decay model. "Exactly one" is a structural claim: the emit points must be
singular and owned, which rules out incidental logging scattered through callers. This
component owns the record shape and the rotation cap; each emit point is the single
component that owns the transition it announces — CMP-005 for sickness and terminal,
CMP-006 for sleep and wake, CMP-007 for mood, CMP-012 for save, load and quarantine,
CMP-011 for launch, and CMP-009 for the decay computation it applies.

Owning the cap means enforcing it, not only knowing it. NFR-007's "indefinitely" is
the operative word: a log that only appends grows without limit, and a log that stops
appending at the cap silently loses every record after it, which fails the same clause
from the other side. So this component tracks the log's size and rolls the file over
when the cap is reached, discarding the oldest rolled copy — the decision is its own,
the file operations are the adapter's. The cap's numeric value is not stated by any
requirement in the digest and must be set before the behaviour is testable.

NFR-005 and CON-002 bind the log as tightly as they bind the save file: local-only,
user-readable, and never transmitted.

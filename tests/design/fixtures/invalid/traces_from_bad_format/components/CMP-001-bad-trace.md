---
id: CMP-001
type: component
title: bad-trace
description: A component whose traces_from entry is not a requirement-shaped id.
traces_from:
  - NOPE-1
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-18
responsibility: Traces from an id that does not match any requirement prefix.
boundary: internal
depends_on: []
---

# bad-trace

`traces_from: [NOPE-1]` — `NOPE-` is not a requirement prefix
(FR/NFR/CON/BR/UC). Format is checked here; existence is STO-102's job.

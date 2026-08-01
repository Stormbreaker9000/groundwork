---
id: CMP-011
type: component
title: System Clock
description: The operating system's wall-clock time source, reporting the current instant to the application.
traces_from:
- FR-001
- FR-002
- NFR-001
- NFR-007
- BR-002
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Reports the current wall-clock instant.
boundary: external
depends_on: []
---

# CMP-011 — System Clock

The operating system's wall-clock time source, reporting the current instant to the
application.

## Responsibility
Reports the current wall-clock instant.

## Rationale
NFR-001 forces this into the architecture as an element rather than leaving it as
an ambient call. A +/- 1 stat-unit tolerance across intervals spanning five orders
of magnitude is only testable if the Decay computation can be driven without real
elapsed time, which means the clock has to be a dependency something injects — and
a dependency needs a provider. Modelling it as an external component gives the
substitution point a name: production reads the OS clock, the NFR-001 test suite
reads a controlled one, and neither case changes a line of the simulation. BR-002's
backward-clock rule exists precisely because this source is outside the system's
control and can move backwards, and FR-001's last-saved timestamp and NFR-007's log
timestamps both originate here.

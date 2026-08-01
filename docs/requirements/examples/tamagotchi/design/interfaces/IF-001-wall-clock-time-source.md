---
id: IF-001
type: interface
title: Wall-Clock Time Source
description: The contract through which any component that needs to know "now" obtains the current wall-clock instant, and through which an elapsed interval between two instants is derived and validated.
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
provider: CMP-011
operations:
- name: now
  summary: Report the current wall-clock instant as an absolute timestamp.
- name: elapsed_since
  summary: Report the interval between a supplied earlier instant and the present, signalling explicitly when that interval is negative rather than returning it.
interaction: synchronous
error_modes:
- Clock unavailable — the platform time source cannot be read, so no instant can be reported and the caller must not substitute a guess.
- Backward clock movement — the reported instant precedes a previously observed one, so any interval derived from it is invalid and BR-002 requires zero Decay rather than a stat increase.
- Coarse or drifting resolution — the reported instant may differ from true wall-clock time by more than the caller's tolerance, which NFR-001's +/- 1 stat unit budget must absorb.
---

# IF-001 — Wall-Clock Time Source

The contract through which any component that needs to know "now" obtains the
current wall-clock instant, and through which an elapsed interval between two
instants is derived and validated.

## Operations
- **now** — Report the current wall-clock instant as an absolute timestamp.
- **elapsed_since** — Report the interval between a supplied earlier instant and
  the present, signalling explicitly when that interval is negative rather than
  returning it.

## Interaction
Synchronous. Every consumer blocks on the answer: CMP-001 cannot write a record
without the last-saved timestamp, CMP-007 cannot compute the offline-elapsed
interval without it, and CMP-009 cannot stamp a log entry without it. There is no
version of "now" that arrives later and is still "now".

## Error Modes
- Clock unavailable — the platform time source cannot be read, so no instant can
  be reported and the caller must not substitute a guess.
- Backward clock movement — the reported instant precedes a previously observed
  one, so any interval derived from it is invalid and BR-002 requires zero Decay
  rather than a stat increase.
- Coarse or drifting resolution — the reported instant may differ from true
  wall-clock time by more than the caller's tolerance, which NFR-001's +/- 1 stat
  unit budget must absorb.

## Rationale
Satisfies the identically declared clock capability of CMP-001, CMP-003, CMP-004,
CMP-007 and CMP-009 — five consumers, one contract, because they all want the same
thing from the same provider. NFR-001 is the reason it is an interface at all: a
+/- 1 unit tolerance over intervals from one minute to thirty days is only testable
if the clock is injected rather than called ambiently. Making `elapsed_since` refuse
a negative interval rather than return one puts BR-002's backward-clock rule on the
contract boundary instead of in five separate callers.

---
id: IF-024
type: interface
title: Host Wall-Clock Reading
description: The external contract through which the platform adapter reads the operating system's current wall-clock time.
traces_from: [FR-002, FR-011, NFR-001, NFR-006]
traces_to:
  adr: [ADR-002]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-019
operations:
- name: read_time
  summary: Return the operating system's current wall-clock time.
  interaction: synchronous
error_modes:
- The host clock is uninitialised or unavailable — no reading can be returned, and no elapsed interval anywhere in the product can be derived.
- The owner or the OS moves the clock backward between two readings — a reading earlier than a previously recorded timestamp is returned, which A-7 requires the host to expose observably rather than smooth into slow-forward time.
- The host smooths a backward correction rather than exposing it — readings remain monotonic, no non-positive interval is ever observable, and both of A-6's rules are defeated with no failure visible to the application.
- A time-sync correction moves the clock forward — an elapsed interval larger than the real absence is observed and decay is applied for the whole of it, bounded only by each stat's own scale (A-24 sets no cap on decay over long absences).
---

# IF-024 — Host Wall-Clock Reading

The external contract through which the platform adapter reads the operating system's current
wall-clock time.

## Operations
- **read_time** — Return the operating system's current wall-clock time.

## Interaction
Synchronous. A clock reading delivered later than it was requested is a different reading.

Distinct from IF-018 and deliberately not merged with it. This is the raw host reading, consumed
only by the platform adapter; IF-018 is what the rest of the codebase sees, and it adds the
signed-interval derivation the adapter builds on top. Collapsing the two would put a platform call
in front of every internal consumer, which is precisely the seam NFR-006 counts violations of.

## Error Modes
- The host clock is uninitialised or unavailable — no reading, and no elapsed interval anywhere in
  the product can be derived.
- The clock is moved backward between two readings — a reading earlier than a recorded timestamp is
  returned, which A-7 requires the host to expose observably.
- The host smooths a backward correction instead — readings stay monotonic, no non-positive
  interval is ever observable, and both of A-6's rules are defeated with no visible failure.
- A time-sync correction moves the clock forward — a larger-than-real elapsed interval is observed
  and decay applies for all of it, bounded only by each stat's scale (A-24).

## Rationale
Satisfies CMP-017's declared need to read the operating system's wall-clock time. It is one of the
edges leaving the process, modelled as an external component so the dependency stays inside the
graph. Every elapsed-interval computation in the product originates here, which is why A-7's
observability assumption is stated as a failure mode of this contract rather than left implicit.

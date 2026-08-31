---
id: IF-013
type: interface
title: Pet State Commit
description: The contract through which the current pet state is committed to the save file as the system's single system of record, atomically and dated with a last-saved timestamp.
traces_from: [FR-001, NFR-004, NFR-005, NFR-007, BR-002]
traces_to:
  adr: [ADR-001, ADR-003, ADR-004]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-012
operations:
- name: commit
  summary: Write the supplied pet state to the save file as one committed state, dated with a last-saved timestamp taken from the host clock, atomically replacing the single retained generation.
  interaction: synchronous
error_modes:
- The atomic replace fails — the previously committed state remains intact and unmodified, and the caller is told the change is not durable; an interrupted write never replaces the committed file, which is what makes single-generation retention sufficient (Q-9, resolved).
- The local data directory is unavailable or not writable — nothing is committed, and the pet's accumulated state exists only in memory for the rest of the session.
- Host clock reading unavailable — no last-saved timestamp can be written, and a committed state without one leaves FR-002 with no origin to measure the offline-elapsed interval from, so the commit is refused rather than dated with a guess.
- The supplied pet state cannot be encoded in full — the commit is refused rather than a partial record written, because every persisted field must round-trip unchanged (FR-001).
- The supplied state would discard or overwrite the accumulated state of a pet at the terminal end-of-life status — refused while BR-002's prohibition stands.
---

# IF-013 — Pet State Commit

The contract through which the current pet state is committed to the save file as the system's
single system of record, atomically and dated with a last-saved timestamp.

## Operations
- **commit** — Write the supplied pet state to the save file as one committed state, dated with
  a last-saved timestamp taken from the host clock, atomically replacing the single retained
  generation.

## Interaction
Synchronous. FR-001 fires on every stat change, and NFR-004's discriminating clause requires the
committed state to be the one restored — the caller has to know whether the write landed.

**Separate from IF-012, deliberately.** CMP-012 provides both, but the consumer sets are disjoint:
the Pet Session (CMP-003) commits and never retrieves, and the lifecycle sequencer (CMP-011)
retrieves and never commits. Folding them into one store contract would make the launch path
depend on a commit operation it never calls, and the session depend on a retrieval that carries
FR-012's quarantine branch — a failure path it has no business handling. The two are also
lifecycle-disjoint in time: retrieval happens once, before the pet exists; commit happens
repeatedly, for the rest of the session. Segregation is the honest verdict here, not a preference.

Note that the close-path commit does not reach this contract directly either: IF-029 is asked of
the session (CMP-003), which is what routes it back through here, so BR-002's inspection of every
state-writing path still converges on one custodian.

## Error Modes
- The atomic replace fails — the previously committed state remains intact, and the caller is
  told the change is not durable.
- The local data directory is unavailable or not writable — nothing is committed.
- Host clock reading unavailable — the commit is refused rather than dated with a guess, because
  a committed state with no last-saved timestamp leaves FR-002 no origin.
- The pet state cannot be encoded in full — refused rather than partially written.
- The write would discard a terminal pet's accumulated state — refused (BR-002).

## Rationale
Satisfies CMP-003's declared need to commit the current pet state. Atomicity is a property of
this contract rather than of its caller because no caller-side ordering can supply it (NFR-004),
and one generation is retained rather than two (Q-9, resolved).

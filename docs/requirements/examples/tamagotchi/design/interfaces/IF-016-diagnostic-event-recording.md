---
id: IF-016
type: interface
title: Diagnostic Event Recording
description: The contract through which every decay computation and every pet lifecycle transition emits its one structured local record.
traces_from: [NFR-007, NFR-005]
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-015
operations:
- name: record_lifecycle_transition
  summary: Record exactly one structured local record for a pet lifecycle transition — launch, close, save, load, save-file quarantine, mood change, onset of sickness, terminal transition, sleep or wake — carrying its timestamp, event type, pre-state and post-state.
  interaction: asynchronous
- name: record_decay_computation
  summary: Record exactly one structured local record for a decay computation, carrying its timestamp, the elapsed interval, pre-state, post-state and computed deltas, sufficient to recompute the resulting state from the record alone.
  interaction: asynchronous
error_modes:
- The rotation cap is reached — the log is rolled over and the oldest retained copy discarded before the record is written, so records continue past the cap rather than being lost from it onward; NFR-007 requires both the cap and a record per transition, and rolling is what keeps the two compatible.
- The roll-over itself fails and the live log is already at the cap — only then is the record dropped, and the caller is still neither blocked nor failed; a lost diagnostic record must never abort the transition it describes.
- The log file cannot be written for any other reason — permission, device full, directory unresolvable — the record is dropped, again without blocking or failing the caller.
- The supplied pre-state or post-state is incomplete — the record is written and marked unreplayable rather than written silently short, because NFR-007's replay check would otherwise report a mismatch with no indication of why.
- The same transition is submitted more than once — recorded once, since NFR-007 requires exactly one record per transition and a duplicate would break the replay count as surely as a missing one.
---

# IF-016 — Diagnostic Event Recording

The contract through which every decay computation and every pet lifecycle transition emits its
one structured local record.

## Operations
- **record_lifecycle_transition** — Record exactly one structured local record for a pet
  lifecycle transition — launch, close, save, load, save-file quarantine, mood change, onset of
  sickness, terminal transition, sleep or wake — carrying its timestamp, event type, pre-state
  and post-state.
- **record_decay_computation** — Record exactly one structured local record for a decay
  computation, carrying its timestamp, the elapsed interval, pre-state, post-state and computed
  deltas, sufficient to recompute the resulting state from the record alone.

## Interaction
Both asynchronous. No caller may have its transition delayed or failed by a log write; the record
is a consequence of the transition, never a precondition. The cost is that a caller cannot know
its record landed, which is why record dropped is stated as a failure mode of this contract
rather than of its consumers.

Two operations rather than one, because the two record shapes differ in required content: a decay
record must carry the elapsed interval and the computed deltas, which are what NFR-007's replay
check drives through the reference decay model, and no lifecycle transition has either. One
operation with everything optional would make "sufficient to independently recompute the resulting
state" unenforceable at the contract.

## Error Modes
The cap-reached path is the one that changed, and it is worth being explicit about why. NFR-007
asks for two things that pull against each other: exactly one record per transition, and total
log size under a fixed cap indefinitely. With only an append primitive underneath, the cap could
be honoured only by dropping every record from the moment it was reached — permanent silent
record loss, and a log that stops describing the pet precisely when it has been running longest.
With IF-021's `file_size` and `roll_over`, the cap is honoured by rolling instead, and a record
is dropped only when the roll itself fails.

- The rotation cap is reached — the log is rolled over and the oldest retained copy discarded
  before the record is written; records continue past the cap.
- The roll-over itself fails at the cap — only then is the record dropped, and the caller is
  still neither blocked nor failed.
- The log file cannot be written for any other reason — the record is dropped, without blocking
  or failing the caller.
- The supplied pre-state or post-state is incomplete — the record is written marked unreplayable
  rather than silently short.
- The same transition is submitted twice — recorded once; a duplicate breaks NFR-007's
  exactly-one count as surely as a missing record.

## Rationale
Satisfies the identical capability declared by CMP-005 (sickness onset, terminal transition),
CMP-006 (sleep, wake), CMP-007 (mood change), CMP-009 (decay computations), CMP-011 (launch and
close) and CMP-012 (save, load, quarantine). One contract for all six, because "exactly one
structured record" is a claim about a single owned emit point — scattering the recording across
callers is precisely what NFR-007's phrasing rules out.

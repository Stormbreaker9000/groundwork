---
id: IF-003
type: interface
title: Durable Pet State Persistence
description: The contract through which the pet's state and its last-saved timestamp are committed to and restored from durable local storage, as the only path by which anything reaches the state file.
traces_from:
- FR-001
- FR-002
- FR-010
- NFR-004
- CON-002
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
provider: CMP-001
operations:
- name: load
  summary: Return the last committed pet state together with its last-saved timestamp, or report that no valid state exists, having first retained any unreadable file under a Quarantine name.
- name: commit
  summary: Write a complete pet state and its last-saved timestamp such that a reader afterwards sees either the whole previous state or the whole new one, never a partial write.
interaction: synchronous
error_modes:
- No committed state found — a first launch or a removed file, so the caller must start a new pet from default values and must not treat this as a failure (FR-010).
- Integrity validation failed — the stored state is unreadable or malformed; it is retained under a Quarantine name and reported as a distinct outcome, not thrown.
- Storage unwritable — the app-data directory is missing, full, or permission-denied, so the commit did not happen and the previously committed state still stands.
- Timeout with unknown commit state — the process may be terminated mid-commit; the caller cannot know whether the write landed, and only the atomic replace guarantees the next load sees one whole state rather than a half-written one.
---

# IF-003 — Durable Pet State Persistence

The contract through which the pet's state and its last-saved timestamp are
committed to and restored from durable local storage, as the only path by which
anything reaches the state file.

## Operations
- **load** — Return the last committed pet state together with its last-saved
  timestamp, or report that no valid state exists, having first retained any
  unreadable file under a Quarantine name.
- **commit** — Write a complete pet state and its last-saved timestamp such that a
  reader afterwards sees either the whole previous state or the whole new one,
  never a partial write.

## Interaction
Synchronous. CMP-007 cannot sequence the launch until `load` has returned an outcome
— restored state, absent, or quarantined — because which of the three it is decides
what happens next. On the write side the call is closer: FR-001 fires a commit on
every stat change, and an accepted-then-settled write would take disk latency off
that path. It is kept synchronous because NFR-004 measures 200 fault-injection
trials in which every launch must load a fully committed state or a valid default,
and a queued write in flight at kill time is precisely the window that measurement
is closing. The cost is disk latency inside each stat change; what would tip it is a
measured breach of NFR-002's idle budget attributable to commit frequency, which
would be answered by coalescing commits, not by making them asynchronous.

## Error Modes
- No committed state found — a first launch or a removed file, so the caller must
  start a new pet from default values and must not treat this as a failure (FR-010).
- Integrity validation failed — the stored state is unreadable or malformed; it is
  retained under a Quarantine name and reported as a distinct outcome, not thrown.
- Storage unwritable — the app-data directory is missing, full, or permission-denied,
  so the commit did not happen and the previously committed state still stands.
- Timeout with unknown commit state — the process may be terminated mid-commit; the
  caller cannot know whether the write landed, and only the atomic replace guarantees
  the next load sees one whole state rather than a half-written one.

## Rationale
Satisfies CMP-003's and CMP-007's identically declared need to preserve the pet's
state across restarts — the manager because that is where stats change (FR-001), the
coordinator because it sequences the launch restore and the shutdown commit. One
contract, two consumers. NFR-004 is the reason the commit protocol lives behind this
interface rather than in either caller: the number of code paths that can leave a
half-written file on disk has to be exactly zero, and that is only true if nobody
else can write the file.

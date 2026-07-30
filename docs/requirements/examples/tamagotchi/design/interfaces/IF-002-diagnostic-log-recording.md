---
id: IF-002
type: interface
title: Diagnostic Log Recording
description: The contract through which components record a structured diagnostic entry in the application's local, on-device log without owning where or how it is written.
traces_from:
- FR-010
- NFR-002
- NFR-005
- NFR-007
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
provider: CMP-009
operations:
- name: record
  summary: Append one structured diagnostic entry — its event kind and the fields that event carries — to the local diagnostic record, stamped with a single ordering clock.
- name: flush
  summary: Make every previously accepted entry durable, so a shutdown or a lifecycle transition is not lost to buffering.
interaction: asynchronous
error_modes:
- Log sink unwritable — the log directory is missing, full, or permission-denied, so entries are discarded; the caller's own work must still complete, because diagnostics may never gate pet simulation.
- Entry accepted but not yet durable — a crash between acceptance and flush loses the most recent entries, which is the cost of not blocking the caller.
- Retention bound reached — the oldest entries are discarded to keep the on-disk log within a bounded size, so a diagnostic window is finite.
---

# IF-002 — Diagnostic Log Recording

The contract through which components record a structured diagnostic entry in the
application's local, on-device log without owning where or how it is written.

## Operations
- **record** — Append one structured diagnostic entry — its event kind and the
  fields that event carries — to the local diagnostic record, stamped with a single
  ordering clock.
- **flush** — Make every previously accepted entry durable, so a shutdown or a
  lifecycle transition is not lost to buffering.

## Interaction
Asynchronous, and this is a genuinely close call worth naming. NFR-002's <= 1% idle
CPU budget argues against putting a synchronous disk write on the decay path, which
fires on a timer for the whole life of the process. NFR-007 pulls the other way: a
24-hour session must have zero missing transition entries, and an accepted-but-buffered
entry is exactly the one a crash loses. The resolution is asynchronous accept plus an
explicit `flush` that CMP-007 calls on the shutdown path and CMP-004 calls after a
lifecycle transition. What would tip it to synchronous is evidence that transition
entries are being lost in fault-injection testing; the cost of that would be a disk
write inside every stat mutation.

## Error Modes
- Log sink unwritable — the log directory is missing, full, or permission-denied,
  so entries are discarded; the caller's own work must still complete, because
  diagnostics may never gate pet simulation.
- Entry accepted but not yet durable — a crash between acceptance and flush loses
  the most recent entries, which is the cost of not blocking the caller.
- Retention bound reached — the oldest entries are discarded to keep the on-disk
  log within a bounded size, so a diagnostic window is finite.

## Rationale
Satisfies the identically declared logging capability of CMP-001, CMP-003, CMP-004
and CMP-007. NFR-007 requires a parseable entry for every decay computation and every
lifecycle transition; NFR-005 makes this local log the only diagnostic channel that
exists, since there is no remote counterpart to fall back on. FR-010's quarantine
event is recorded here too — quarantining a file nobody is told about is not
diagnostics.

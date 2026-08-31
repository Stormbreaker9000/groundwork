---
id: CMP-003
type: component
title: Pet Session
description: The holder of the application's single live pet state for the duration of a session, the only path through which any component reads or replaces it, and the point from which it is committed to durable storage on both of FR-001's persist triggers.
traces_from: [FR-001, BR-002]
traces_to:
  adr: [ADR-001, ADR-003, ADR-004]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Holds the application's live pet state as its sole custodian, mediating every read of it, every replacement of it and every commit of it to durable storage.
boundary: internal
depends_on: [IF-013]
---

# CMP-003 — Pet Session

The holder of the application's single live pet state for the duration of a session,
the only path through which any component reads or replaces it, and the point from
which it is committed to durable storage on both of FR-001's persist triggers.

## Responsibility
Holds the application's live pet state as its sole custodian, mediating every read of
it, every replacement of it and every commit of it to durable storage.

## Rationale
FR-001's ASR reading is that the only path able to destroy accumulated state must sit
behind one contract, because BR-002 is verified by inspecting every path that writes,
clears or replaces persisted pet state — a finite inspection only if those paths
converge. The durable half of that convergence is CMP-012; this is the in-memory half.

Both of FR-001's persist triggers leave through this component. The "when a pet stat
value changes" trigger is observed here because every replacement passes through here.
The "owner closes the application" trigger is asked for here too, as the session's
final act, rather than the closing caller reading the live state out and committing it
itself — a second commit path opened at close would reopen the inspection BR-002's
convergence argument depends on being finite, which is the whole reason this component
is stated as the sole custodian rather than merely as a reader and replacer.

A replacement that leaves every pet state field equal does not re-commit. The write
cadence that results from combining FR-001's trigger with a running evaluation cadence
(Q-10) is in tension with NFR-002's idle budget and is left to the decision stage.

---
id: CMP-011
type: component
title: Application Lifecycle Sequencer
description: The ordered path across both of the application's session boundaries — at launch, retrieve the committed pet state or fall back to a default pet, evaluate before anything is drawn, show the pet and start the running cadence; at close, stop that cadence and commit what the session holds.
traces_from: [FR-001, FR-002, FR-010, FR-011, FR-012, NFR-004, NFR-007, NFR-009, BR-001]
traces_to:
  adr: [ADR-001, ADR-003]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Orders the application's session boundaries, from launch through to close.
boundary: internal
depends_on: [IF-002, IF-009, IF-010, IF-011, IF-012, IF-016, IF-017, IF-026, IF-029]
---

# CMP-011 — Application Lifecycle Sequencer

The ordered path across both of the application's session boundaries — at launch,
retrieve the committed pet state or fall back to a default pet, evaluate before anything
is drawn, show the pet and start the running cadence; at close, stop that cadence and
commit what the session holds.

## Responsibility
Orders the application's session boundaries, from launch through to close.

## Rationale
FR-002 places a computation whose input is elapsed real time ahead of first render,
which separates launch into ordered stages, and NFR-009 defines its measurement window
structurally — between the completion of the committed-save read and the first render.
That window is only expressible if those two events are distinct, observable boundaries
rather than one opaque startup, which is what this component provides.

NFR-004's discriminating clause rules out a failed read falling through to the default
pet without first establishing that no committed state survives, so the retrieval
outcome distinguishes "no file present" (FR-010) from "present but not a committed
state" (FR-012) and this sequence branches on it rather than on an error. BR-001 is
satisfied structurally: neither branch here can advance health status, because the only
writer of it is CMP-005, which this sequence does not call except through an evaluation
that starts from a Healthy default pet.

Close is the other half of the same responsibility, and it is here because launch is.
FR-001 names two persist triggers and the second of them — the owner closing the
application — is an occasion rather than a state change, so no component that watches
state changes can serve it; it needs an element that knows the session is ending. The
close path is the launch path in reverse: stop the recurring cadence this sequence
started, so that no evaluation is still re-deriving a state as the process exits, then
ask the session to commit what it holds. FR-001's AC-3 — the Sleeping state and its
sleep-entry timestamp surviving a close — is satisfied at that commit, because the
session's live pet state carries both fields and the commit writes pet state in full.

Owning both boundaries is also what makes the lifecycle symmetric rather than a start
with no stop. It does not make this two components: the responsibility is the ordering
of the session's boundaries, and there is exactly one ordering, read forwards at launch
and backwards at close.

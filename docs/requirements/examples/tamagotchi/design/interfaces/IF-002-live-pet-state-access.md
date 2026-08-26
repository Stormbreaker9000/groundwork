---
id: IF-002
type: interface
title: Live Pet State Access
description: The contract through which the session's live pet state is read and replaced, and the single point at which a replacement triggers a durable commit.
traces_from: [FR-001, FR-003, FR-004, FR-005, NFR-004, BR-002]
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
provider: CMP-003
operations:
- name: current
  summary: Return the application's live pet state.
  interaction: synchronous
- name: replace
  summary: Install a supplied pet state as the live one; this replacement is the trigger FR-001's persist-on-stat-change obligation hangs off.
  interaction: synchronous
error_modes:
- Replacement rejected because the supplied pet state violates a pet-state invariant — a stat outside its bounds, or a Sleeping pet with no sleep-entry timestamp — leaving the live state unchanged.
- The durable commit the replacement triggers fails — the caller is told the change is not durable rather than the failure being swallowed, since a silently in-memory-only stat change survives only until the process ends.
- A replacement that would discard or overwrite the accumulated state of a pet at the terminal end-of-life status — refused outright while BR-002's prohibition stands.
---

# IF-002 — Live Pet State Access

The contract through which the session's live pet state is read and replaced, and the single
point at which a replacement triggers a durable commit.

## Operations
- **current** — Return the application's live pet state.
- **replace** — Install a supplied pet state as the live one; this replacement is the trigger
  FR-001's persist-on-stat-change obligation hangs off.

## Interaction
Both synchronous. `current` obviously so. `replace` is the closer call: it carries a durable
commit behind it, so the caller blocks on a file write. Accepting the replacement and
committing behind the caller's back would take the store's latency off the care-action path
and off every evaluation, at the cost that a care action could report success for a change
that never reaches disk — and NFR-004's discriminating clause exists precisely to catch a
launch that fails to restore a change the owner believes they made. Kept synchronous;
if the write latency later shows up against the responsiveness of the care loop, the
alternative is deferred commit plus an explicit not-yet-durable state on the contract, not
a silent one.

Separate from IF-029, the session-end commit, even though the same component provides both:
IF-029's only consumer is the lifecycle sequencer, which never replaces a state on the close
path, and the four consumers here never close the session. See IF-029.

## Error Modes
- Replacement rejected because the supplied pet state violates a pet-state invariant — a stat
  outside its bounds, or a Sleeping pet with no sleep-entry timestamp — leaving the live
  state unchanged.
- The durable commit the replacement triggers fails — the caller is told the change is not
  durable rather than the failure being swallowed.
- A replacement that would discard or overwrite the accumulated state of a pet at the terminal
  end-of-life status — refused outright while BR-002's prohibition stands.

## Rationale
Satisfies the live-state capability declared by CMP-008 (care actions), CMP-009 (evaluation),
CMP-011 (launch) and CMP-016 (the owner's view). Routing every replacement through one
contract is what makes BR-002's "inspect every code path that writes, clears or replaces
persisted pet state" a finite inspection, and what stops a caller changing a stat without
persisting it (FR-001).

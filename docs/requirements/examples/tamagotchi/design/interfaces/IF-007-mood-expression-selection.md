---
id: IF-007
type: interface
title: Mood Expression Selection
description: The contract that maps a pet's current stat values to the mood expression displayed for it, by the band containing its lowest stat, and reports whether that expression has changed from the one the pet's prior stat values selected.
traces_from: [FR-007, NFR-003, NFR-007]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-007
operations:
- name: select
  summary: Return the mood expression mapped to the mood-threshold band containing the pet's lowest stat value, together with the expression the supplied prior stat values select and whether the two differ, so that NFR-007's one-record-per-mood-change obligation has both the fact of a change and the pre-state it must carry.
  interaction: synchronous
error_modes:
- Mood-threshold bands unavailable or incomplete — no band can be matched and no expression is selected.
- The configured bands leave a gap that the lowest stat value falls into — reported rather than resolved to the nearest band, because a silent nearest-band fallback displays a mood FR-007 does not define and no test would catch it.
- The pet carries no stat values at all — there is no minimum to reduce over and no expression can be selected.
- No prior stat values are supplied — the current expression is still selected, but the result is marked as having no comparable predecessor, so the first selection of a session records no mood change rather than recording a change from nothing and inflating NFR-007's per-transition record count.
- The prior stat values supplied are not the ones the pet actually held before this change — the change is judged against the wrong predecessor, and a mood change is recorded that did not happen or a real one is missed; this contract cannot detect it, which is why the caller that caused the change is the one that supplies them.
---

# IF-007 — Mood Expression Selection

The contract that maps a pet's current stat values to the mood expression displayed for it, by
the band containing its lowest stat, and reports whether that expression has changed from the
one the pet's prior stat values selected.

## Operations
- **select** — Return the mood expression mapped to the mood-threshold band containing the
  pet's lowest stat value, together with the expression the supplied prior stat values select
  and whether the two differ.

## Interaction
Synchronous. Both consumers install the selected expression as part of the pet state they hand
on, so neither can proceed without it.

One operation, which now takes the prior stat values as well as the current ones. That
addition is not decoration: NFR-007 enumerates a mood change as a lifecycle transition
requiring exactly one structured record carrying pre-state and post-state, and CMP-007 is the
only place the mood changes, so it is the component that must emit that record. The previous
shape gave `select` only the current values, which left it able to compute an expression but
unable to tell whether that expression was a change, or to name what it changed from. The
contract could not serve the capability its own provider was assigned. Prior values are the
same shape IF-015's `raise_for_stat_change` already takes, for the same reason — both
consumers hold the pre-change and post-change pet states at the moment they call.

The alternative was to let this component remember the last expression it selected. That was
rejected: it would make a pure mapping stateful, make the record depend on call ordering
rather than on the pet, and give a wrong answer the first time it is called after a launch
restores a pet whose mood it never selected.

## Error Modes
- Mood-threshold bands unavailable or incomplete — no band can be matched.
- The configured bands leave a gap the lowest stat value falls into — reported rather than
  resolved to the nearest band, because a silent fallback displays a mood FR-007 does not
  define.
- The pet carries no stat values — there is no minimum to reduce over.
- No prior stat values supplied — an expression is selected but marked as having no comparable
  predecessor, so the session's first selection records no mood change.
- The prior values are not the ones the pet actually held — a change is recorded that did not
  happen, or a real one is missed; undetectable here, which is why the caller that caused the
  change supplies them.

## Rationale
Satisfies the identical capability declared by CMP-008 (a care action can move the lowest stat
across a band boundary) and CMP-009 (so can decay, which FR-007's AC-3 names). One contract for
both, because both consume the same single capability.

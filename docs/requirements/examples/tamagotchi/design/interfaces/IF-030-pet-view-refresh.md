---
id: IF-030
type: interface
title: Pet View Refresh
description: The contract through which a pet-state evaluation asks the owner's view to be redrawn after the pet has advanced with no owner input, carrying the pet as it stood before that advance so that an unchanged mood expression and health status is not announced again.
traces_from: [FR-007, FR-008, FR-011, NFR-002, NFR-003]
traces_to:
  adr: [ADR-002, ADR-003, ADR-004, ADR-006]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-016
operations:
- name: refresh
  summary: Redraw the owner's view from the live pet state and, where the pet's mood expression or health status differs from the one the supplied pre-advance pet state carried, announce the new values — without blocking the evaluation that asked for it.
  interaction: asynchronous
error_modes:
- The live pet state cannot be read at the moment of a redraw — the previous view is held rather than a blank or half-populated one drawn, since a momentarily empty pet reads to the owner as a lost pet.
- The redraw fails outright — the evaluation that asked for it still stands, because the state was installed and committed before the refresh was requested; the owner sees a stale view until the next evaluation redraws successfully.
- A refresh arrives while a previous one is still drawing — coalesced to the latest live pet state rather than queued, so the owner never watches a backlog of stale frames replay.
- Refreshes arrive faster than the display can present them — coalesced for the same reason, and this is the bound that keeps a short evaluation cadence from spending NFR-002's idle CPU budget on redraws nobody sees.
- The pet advanced but its mood expression and health status did not change — the view still redraws and the announcement is suppressed, because a screen-reader user hearing the same mood and health status repeated at cadence frequency is an NFR-003 failure rather than a harmless redundancy.
- No pre-advance pet state is supplied — the announcement fires rather than being suppressed, since a refresh with no comparable predecessor may well be carrying something the owner has not heard, and a repeated announcement is the better of the two failures.
- The pre-advance pet state supplied is not the one the pet actually held before the advance — a real change is suppressed as unchanged, or an unchanged status is announced again; this contract cannot detect it, which is why the evaluation that caused the advance is the one that supplies it.
---

# IF-030 — Pet View Refresh

The contract through which a pet-state evaluation asks the owner's view to be redrawn after the
pet has advanced with no owner input, carrying the pet as it stood before that advance so that an
unchanged mood expression and health status is not announced again.

## Operations
- **refresh** — Redraw the owner's view from the live pet state and, where the pet's mood
  expression or health status differs from the one the supplied pre-advance pet state carried,
  announce the new values — without blocking the evaluation that asked for it.

## Interaction
Asynchronous. The evaluation has already installed and committed the state before it asks for a
redraw, so it has nothing to learn from the result and no reason to wait. A redraw that fails must
not fail the evaluation — the pet really did advance, and reverting or retrying the derivation
because a frame did not paint would be worse than a stale view for one cadence period.

**This is the other half of the old IF-017, and the split was overdue.** Last round both this and
the launch-time first display were forced into one contract, because CMP-009 and CMP-011 had
declared the identical capability string and the exactly-once rule left no way to separate them
from the interface layer. That was flagged then as a carving too coarse to segregate; the
component set has since split the capability, and the two halves separate along all three axes at
once. Disjoint consumers: the evaluator refreshes, the lifecycle sequencer displays first.
Opposed interaction: this one must not block, and first render must be blocking to close NFR-009's
measurement window. Opposed failure semantics: a failed first render fails the launch, a failed
refresh does not fail the evaluation. Bundling them made the second and third of those
unstateable, because the contract could carry only one answer per question.

The drawing and announcing themselves go through IF-027, inside the platform-adapter layer. This
contract decides that a redraw is warranted and from what; it does not touch a platform.

**Why `refresh` takes the pre-advance pet state.** Without it the announcement fires on every
tick, and most ticks change nothing a screen-reader user has not already heard — an unchanged
mood and health status repeated at cadence frequency, which is precisely what NFR-003's scripted
walkthrough is run to catch. The comparison was never unavailable: CMP-009 holds the pre-state
and the post-state at the moment it calls, and already hands that same pair to IF-007's `select`
and IF-015's `raise_for_stat_change`. This contract takes it in the same shape, for the same
reason, and the previous round simply had not asked for it. Only the announcement is conditioned
on the comparison — the visual redraw runs either way, because it is coalesced and cheap and the
frame should track the live pet state whether or not the difference is one worth speaking.

## Error Modes
- The live pet state cannot be read at redraw time — the previous view is held rather than a blank
  one drawn.
- The redraw fails outright — the evaluation still stands; the owner sees a stale view until the
  next one succeeds.
- Overlapping refreshes — coalesced to the latest live state rather than queued.
- Refreshes faster than the display can present them — coalesced, which is what keeps a short
  cadence from spending NFR-002's idle budget on frames nobody sees.
- The pet advanced but its mood and health status did not change — the view still redraws and
  the announcement is suppressed, since repeating it at cadence frequency is an NFR-003 failure
  rather than a harmless redundancy.
- No pre-advance pet state supplied — the announcement fires rather than being suppressed; a
  repeated announcement is the better of the two failures.
- The pre-advance pet state is not the one the pet actually held — a real change is suppressed,
  or an unchanged one announced; undetectable here, which is why the evaluation that caused the
  advance supplies it.

## Rationale
Satisfies CMP-009's declared need to refresh the owner's view after the pet has advanced without
owner input, which FR-008's neglect progression and FR-011's wake both cause with no interaction
at all. Confidence is medium: Q-8 (still_open) asks whether the Sleeping state is rendered, and a
wake is precisely one of the advances this contract exists to show — so what a refresh is obliged
to draw and announce after FR-011 fires depends on Q-8's answer even though the operation does not.

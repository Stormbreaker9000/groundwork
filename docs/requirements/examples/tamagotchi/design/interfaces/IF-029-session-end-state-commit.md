---
id: IF-029
type: interface
title: Session-End State Commit
description: The contract through which the lifecycle sequencer asks the session holding the live pet state to commit it as the session's final act, discharging FR-001's close trigger.
traces_from: [FR-001, NFR-004, NFR-007, BR-002]
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
- name: commit_before_close
  summary: Commit the session's live pet state durably as the last act of the session, returning once it is durable or once the commit has definitively failed, so the close path never exits on the assumption that a write landed.
  interaction: synchronous
error_modes:
- The commit fails — the session ends with the owner's most recent care unsaved beyond the last stat-change commit, and the caller is told rather than exiting on the assumption it landed.
- The evaluation cadence has not been stopped first — an in-flight evaluation can install a re-derived state after this commit has read the live one, so the close would persist a state the owner never saw and the next launch would re-derive decay from a timestamp that was stale when written; the ordering is the caller's obligation and IF-010's stop is what discharges it.
- Called more than once on the same close path — idempotent; the second commit writes the same state and must not be counted as a second FR-001 trigger for NFR-007's per-transition record count.
- The host terminates the process before the commit returns — nothing this contract can do; the most recent stat-change commit remains the committed state, which is what makes FR-001's per-change trigger the primary durability guarantee and this one the tidy close rather than the only one.
- The live pet state is at the terminal end-of-life status — committed unchanged like any other; BR-002 forbids discarding or overwriting its accumulated state, not persisting it.
---

# IF-029 — Session-End State Commit

The contract through which the lifecycle sequencer asks the session holding the live pet state to
commit it as the session's final act, discharging FR-001's close trigger.

## Operations
- **commit_before_close** — Commit the session's live pet state durably as the last act of the
  session, returning once it is durable or once the commit has definitively failed.

## Interaction
Synchronous, and there is no close call here. The process is about to exit; an asynchronous commit
would have no one left to complete for. The whole value of the operation is that the caller can
wait for it before exiting, and can be told when it did not happen.

**Its own contract, not an operation on IF-002.** The pet session provides both, but IF-002's
consumers — the care handler, the evaluator, the launch path, the presentation shell — are four
components that read and replace live state during a session, and none of them closes it. This
contract's single consumer closes the session and does not replace state on that path. A strict
subset of consumers, so the Interface Segregation test splits rather than merges: folding this in
would give all four of those components a close-the-session operation, and one of them is the
recurring evaluator whose evaluations must be stopped *before* this runs, not able to trigger it.

**Why FR-001's close trigger routes through the session rather than the store.** The lifecycle
sequencer could have called IF-013 directly. Routing it here keeps BR-002's obligation — inspect
every code path that writes, clears or replaces persisted pet state — converging on one custodian:
the session owns the live state and mediates every commit of it, whether the trigger was a stat
change or the owner closing the application.

**The close path is ordered: stop, then commit, then exit.** That ordering is not stated by any
requirement, and it is the second failure mode below, because the reverse is silently wrong rather
than loudly broken.

## Error Modes
- The commit fails — the session ends with the most recent care unsaved beyond the last
  stat-change commit, and the caller is told.
- The cadence was not stopped first — an in-flight evaluation can install a state after this
  commit read the live one; IF-010's stop is what discharges the ordering.
- Called more than once on the same close path — idempotent, and not a second FR-001 trigger for
  NFR-007's record count.
- The host terminates the process before the commit returns — the most recent stat-change commit
  remains the committed state.
- The pet is at the terminal end-of-life status — committed unchanged; BR-002 forbids discarding
  its state, not persisting it.

## Rationale
Satisfies CMP-011's declared need to commit the live pet state before the session ends. FR-001
names two persist triggers — a stat value changing, and the owner closing the application — and
until this round only the first had an owning element. This is the second, and it is why the
lifecycle sequencer now owns close symmetrically with launch.

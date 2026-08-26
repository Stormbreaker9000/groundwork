---
id: IF-010
type: interface
title: Recurring Evaluation Cadence
description: The contract through which the lifecycle sequencer starts the running application's own cadence of pet-state evaluations once a pet has been established, and stops it again before the session ends.
traces_from: [FR-001, FR-007, FR-008, FR-011, NFR-002]
traces_to:
  adr: [ADR-001, ADR-003, ADR-004, ADR-005, ADR-006]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-010
operations:
- name: start
  summary: Begin driving pet-state evaluations on the running application's own cadence and return once the cadence is established — not once an evaluation has occurred, so first render never waits on an evaluation coming due.
  interaction: synchronous
- name: stop
  summary: Stop driving evaluations and return once the cadence is quiescent and no evaluation is still in flight, so the close path's final commit cannot race an evaluation that would re-derive a state nothing will commit.
  interaction: synchronous
error_modes:
- The platform timer contract refuses to establish a recurring tick (IF-031) — the cadence is not started and the refusal is passed on to the caller rather than swallowed here; the pet then advances only at launch, so wake and neglect progression are invisible for the whole session.
- An evaluation raises an error on one tick — the cadence continues rather than terminating, because a single failed evaluation must not silently stop the pet advancing for the rest of the session.
- Evaluations overrun their own period — ticks are coalesced rather than queued, so a slow evaluation cannot accumulate a backlog that spends the idle CPU budget NFR-002 caps at 1% of one core.
- 'The platform delivers no tick for a long stretch — the machine slept, or background work was throttled — and the missed ticks are not back-filled on resumption: one evaluation then derives from the whole elapsed interval, which is the same path FR-002''s offline decay already takes. This contract originates none of that; it decides only not to queue what the platform never delivered.'
- Started more than once — idempotent; a second cadence over the same pet would double both the evaluation rate and the idle cost.
- Stop is asked for while an evaluation is mid-derivation — stop waits for that evaluation to finish rather than abandoning it partway, since an abandoned evaluation could leave a half-derived pet state installed for the close path to commit.
- Stop cannot confirm quiescence within a bounded wait — either an evaluation is still in flight here, or IF-031's cancel has not confirmed that no further tick will be delivered — reported to the caller, which must then decide whether to commit and exit anyway; FR-001's per-stat-change commits mean the last one already landed, so exiting loses at most the current evaluation's advance.
- Stopped without ever having been started, or stopped twice — idempotent, and not an error; the close path must be able to run after a launch that failed to establish a cadence.
---

# IF-010 — Recurring Evaluation Cadence

The contract through which the lifecycle sequencer starts the running application's own cadence
of pet-state evaluations once a pet has been established, and stops it again before the session
ends.

## Operations
- **start** — Begin driving evaluations on the application's own cadence and return once the
  cadence is established, not once an evaluation has occurred.
- **stop** — Stop driving evaluations and return once the cadence is quiescent and no
  evaluation is still in flight.

## Interaction
Both synchronous, and `start` was wrong before. The concern the previous asynchronous
declaration was reaching for is real — first render must not wait on an evaluation coming due —
but that concern is about what `start` waits *for*, not about whether it returns a result.
Establishing a cadence is fast and local; the evaluations it goes on to drive are what happen
later. A synchronous `start` that returns on establishment meets the launch-latency concern
exactly as well, and it is the only shape consistent with the first error mode below, which
requires the caller to be told when the platform timer contract (IF-031) refuses to establish
a tick. An asynchronous `start` has nobody to tell.

`stop` is synchronous for a stronger reason: its whole purpose is ordering. The close path is
stop, then commit (IF-029), then exit. If `stop` returned before the cadence was quiescent, an
in-flight evaluation could install a re-derived state after the final commit had read the live
one — FR-001's close trigger would then persist a state the owner never saw, and the next
launch would re-derive decay from a timestamp that was already stale when it was written.

**What this contract holds, and what it now delegates.** The recurring tick itself is not held
here. NFR-006 names timer access in the same clause as wall-clock access, so the tick is
obtained from the platform-adapter layer through IF-031, and what stays on this side is the
cadence: its period, its coalescing rule, and when it starts and stops. That is what finally
gives the first error mode below a structural source — this contract can report an
unestablishable timer facility because its provider asks a contract that can refuse, which was
not true of it before. Quiescence gains the same shape: it has two halves now, IF-031's
`cancel` confirming that no further tick will be delivered and this contract waiting out any
evaluation already in flight, and `stop` returns only once both hold.

## Error Modes
- The platform timer contract refuses to establish a tick (IF-031) — the cadence does not
  start, the refusal is passed on, and the pet advances only at launch.
- An evaluation fails on one tick — the cadence continues rather than terminating.
- Evaluations overrun their period — ticks are coalesced, not queued, so no backlog can spend
  the idle budget NFR-002 caps.
- The platform delivers no tick for a long stretch (sleep, throttling) — missed ticks are not
  back-filled; one evaluation then derives from the whole elapsed interval, the same path
  FR-002's offline decay takes.
- Started more than once — idempotent; a second cadence doubles both the rate and the idle cost.
- Stop asked for mid-derivation — stop waits rather than abandoning the evaluation partway.
- Stop cannot confirm quiescence within a bounded wait — from either half, an evaluation still
  in flight or an unconfirmed cancel — reported, and the caller decides whether to commit and
  exit anyway.
- Stopped without having been started, or stopped twice — idempotent, and not an error.

## Rationale
Satisfies CMP-011's declared need to drive recurring evaluation. `stop` exists because CMP-011
now owns the application-close path symmetrically with launch, which is what closes FR-001's
second named trigger — the owner closing the application. The platform tick this cadence runs
on is consumed from IF-031 rather than held by the provider, which is what keeps the sixth of
NFR-006's enumerated seams inside the adapter layer with the other five.

**Confidence is low**: Q-10 (still_open) asks exactly how often the running application
re-evaluates pet state and what bounds that interval, and NFR-002 constrains it from the other
side. Whether `start` carries a period at all, and whether that period is fixed, adaptive or
event-driven, follows from Q-10's answer. `stop`'s shape does not depend on it.

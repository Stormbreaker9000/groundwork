---
id: IF-031
type: interface
title: Platform Recurring Timer
description: The platform-adapter contract through which a caller that owns a cadence obtains a recurring tick at a period it supplies, and stops that tick again, without holding a platform timer of its own.
traces_from: [FR-008, FR-011, NFR-002, NFR-006]
traces_to:
  adr: [ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-017
operations:
- name: start_recurring
  summary: Begin delivering a recurring tick at the requested period to the supplied handler, and return once the host's timer facility is established — or report that it cannot be established, so that no caller is left waiting on a tick that will never arrive.
  interaction: synchronous
- name: cancel
  summary: Stop delivering ticks and return once no further tick will be delivered and no tick delivery is still in flight, so that a caller ordering work after the last tick can rely on quiescence rather than on a delay.
  interaction: synchronous
error_modes:
- The host offers no usable timer facility, or one cannot be established in this session — reported at start_recurring rather than by silence, because silence is indistinguishable from a period that has not yet elapsed and would leave the caller believing it holds a live cadence.
- The requested period is non-positive, or finer than the host's timer resolution — rejected rather than silently coerced to the fastest tick the host can deliver, which would spend NFR-002's idle CPU budget at a rate the caller never asked for.
- Ticks arrive later than the requested period, or not at all, while the machine sleeps or the host throttles background work — the missed ticks are not back-filled on resumption and the delivered period is approximate rather than exact, so a caller must never read elapsed time from a tick count and must take it from the wall clock (IF-018) instead.
- The supplied handler raises on a tick — subsequent ticks are still delivered rather than the timer cancelling itself, because a platform primitive that stopped silently would leave the caller holding a cadence that no longer exists.
- cancel is asked for while a tick is being delivered — it returns only once that delivery has returned and never abandons it partway, since ordering work after the last tick is the caller's whole reason for cancelling.
- cancel cannot confirm within a bounded wait that no further tick will be delivered — reported to the caller rather than returned as success, because a false confirmation of quiescence is the one failure this operation exists to prevent.
- start_recurring is called while a tick is already running, or cancel is called twice or without a start — idempotent in both directions, so that a caller's close path can run after a launch that never established a tick.
---

# IF-031 — Platform Recurring Timer

The platform-adapter contract through which a caller that owns a cadence obtains a recurring tick
at a period it supplies, and stops that tick again, without holding a platform timer of its own.

## Operations
- **start_recurring** — Begin delivering a recurring tick at the requested period to the supplied
  handler, and return once the host's timer facility is established, or report that it cannot be.
- **cancel** — Stop delivering ticks and return once no further tick will be delivered and no
  tick delivery is still in flight.

## Interaction
Both synchronous, and for the same reason in both directions: each returns a fact the caller
cannot proceed without. `start_recurring` returns whether a timer facility exists at all — the
condition IF-010 must report and, until this contract existed, had no structural way to observe.
`cancel` returns quiescence, which is an ordering guarantee rather than a value: the close path is
stop the cadence, commit the live pet state (IF-029), exit, and a cancel that returned before the
last tick had been delivered would let an evaluation install a re-derived state after the final
commit had already read the live one.

Neither operation blocks for long. The ticks themselves are the asynchronous part of this seam,
but they are deliveries the provider makes to the handler, not calls the consumer makes here, so
the contract's two operations are both blocking and the arrangement is not mixed-mode.

Two operations and no more. A period query, a running-or-not query, or a one-shot timer would each
be a facility no declared capability asks for; stoppability is what the capability names, and
`cancel` is what supplies it.

## Error Modes
- No usable timer facility, or one that cannot be established — reported at start rather than by
  silence, which is indistinguishable from a period that has not yet elapsed.
- A non-positive period, or one finer than the host can resolve — rejected rather than coerced to
  the fastest tick available, which would spend NFR-002's idle budget at a rate nobody asked for.
- Late, dropped, or drifting ticks across a sleep or a throttling window — not back-filled, and
  the period is approximate; elapsed time must come from the wall clock, never from a tick count.
- The handler raises on a tick — later ticks are still delivered; a primitive that stopped
  silently would leave the caller holding a cadence that no longer exists.
- cancel asked for mid-delivery — it waits for that delivery rather than abandoning it partway.
- cancel cannot confirm quiescence within a bounded wait — reported rather than returned as
  success, since a false confirmation is the one failure this operation exists to prevent.
- Started twice, or cancelled twice or without a start — idempotent in both directions.

## Rationale
Satisfies CMP-010's declared need for a recurring tick driven from the host's timer facility.
NFR-006 enumerates "wall-clock and timer access" in a single clause as platform-touching seams
that belong inside the platform-adapter layer, and this is the timer half of it; the wall-clock
half is IF-018. The two are deliberately separate contracts even though one layer provides both
and one component consumes both, because they are different questions: IF-018 answers what time
it is when asked, and this one drives the application unasked, which is the machinery NFR-002
budgets by name at idle. Their consumer sets differ too — five components read the clock and one
is driven by a tick — so folding them together would hand every clock reader a timer it never
starts.

Before this contract, IF-010 declared an unavailable timer facility as its first error mode while
its provider held no platform seam through which such a thing could be observed. That was F-14.
The cadence — period, coalescing, when it starts and stops — stays with CMP-010; only the tick
crosses into the adapter.

**Confidence is low**: Q-10 (still_open) asks how often the running application re-evaluates pet
state and what bounds that interval, and NFR-002 constrains the same parameter from the other
side. A fixed period is what CMP-010's capability names and what `start_recurring` therefore
takes; if Q-10 resolves instead to an adaptive or event-driven cadence, the period argument — and
possibly whether a recurring-tick primitive is the right seam at all — changes with it. The
stop half does not depend on the answer.

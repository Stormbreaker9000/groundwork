---
id: IF-004
type: interface
title: Health Progression Advance
description: The contract through which the pet's health status is advanced along the Healthy to Sick to terminal progression under sustained unremedied neglect, and the only writer of that status.
traces_from: [FR-008, NFR-007, BR-001, BR-002]
traces_to:
  adr: [ADR-001, ADR-005]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-005
operations:
- name: advance
  summary: Return the pet's health status advanced one step where at least one pet stat has remained below its neglect threshold continuously for the applicable sustained-neglect duration, measured from that stat's below-threshold-since origin against the current wall-clock reading, and unchanged otherwise; where the interval since an origin computes as non-positive, that origin is re-based to the current reading and no advancement is derived from it.
  interaction: synchronous
error_modes:
- 'The interval since a below-threshold-since origin computes as non-positive because the host clock now reads behind it — not a failure: this contract applies A-6''s deadline rule and re-bases the origin to the current reading, which bounds the progression at one further duration instead of either advancing on a negative interval or deferring the transition indefinitely, as the clamp rule alone would.'
- Host clock reading unavailable — no interval can be measured against any origin, so the health status is returned unchanged rather than advanced or retired on an unknown reading.
- The per-stat below-threshold-since origin cannot be established for the supplied pet — the health status is left unchanged rather than advanced on incomplete evidence, because BR-001 forbids a terminal transition arising from an application fault.
- The balance parameter set has not been loaded — neglect thresholds and sustained-neglect durations are unknown, so no advancement is computed and the status is returned unchanged.
- A pet already at the terminal end-of-life status is supplied — returned unchanged; there is no further step, and no disposition exists to apply (BR-002).
- A pet whose stat recovered above its threshold and fell below it again within one duration is supplied — the origin restarts for that stat rather than accumulating across the recovery, which FR-008's fit criterion tests explicitly.
---

# IF-004 — Health Progression Advance

The contract through which the pet's health status is advanced along the Healthy to Sick to
terminal progression under sustained unremedied neglect, and the only writer of that status.

## Operations
- **advance** — Return the pet's health status advanced one step where at least one pet stat
  has remained below its neglect threshold continuously for the applicable sustained-neglect
  duration, measured from that stat's below-threshold-since origin against the current
  wall-clock reading, and unchanged otherwise; where the interval since an origin computes as
  non-positive, that origin is re-based to the current reading and no advancement is derived
  from it.

## Interaction
Synchronous. An evaluation installs one re-derived pet state, and the health status is part of
it; the caller cannot install a state whose status it has not yet been told.

One operation. The contract exposes no way to read the per-stat below-threshold clock, because
whether that clock exists as a persisted field or is reconstructed at each evaluation is
undecided — see below.

**Which of A-6's two rules this contract applies.** IF-018 hands out a signed interval and
applies neither rule, delegating the choice to each consumer; this is the third consumer, and
the rule it applies is the **deadline rule**, the same one IF-006 applies to the wake test and
not the clamp IF-003 applies to decay. A below-threshold-since origin is a deadline, not a
quantity: nothing is accumulated proportionally to the interval, a single boundary is either
reached or not. Clamping alone would give the wrong answer under a backward clock in a way
FR-008's continuity-across-close behaviour would show — the interval since the origin would
read as zero at every subsequent evaluation while the clock stayed behind, and the sustained
neglect the owner really accumulated would never mature into a transition. Re-basing bounds
the deferral at one further duration and can never advance the status on a negative interval,
which is what BR-001's "0 terminal transitions arise from an application fault" needs from
this operation. The cost is stated honestly: an owner who moves the clock backward repeatedly
can hold off the progression indefinitely, one duration at a time. That is the same exposure
FR-011's wake test accepts, and it is preferred here over the alternative, where the same
owner retires the progression permanently with one adjustment.

## Error Modes
- The interval since an origin computes as non-positive — not a failure: the origin is
  re-based under A-6's deadline rule, bounding the deferral at one further duration.
- Host clock reading unavailable — no interval can be measured and the status is returned
  unchanged rather than advanced or retired on an unknown reading.
- The per-stat below-threshold-since origin cannot be established — the status is left
  unchanged rather than advanced on incomplete evidence (BR-001).
- The balance parameter set has not been loaded — thresholds and durations are unknown, so no
  advancement is computed.
- A pet already at the terminal end-of-life status is supplied — returned unchanged; there is
  no further step and no disposition to apply (BR-002).
- A stat that recovered and fell below its threshold again within one duration — the origin
  restarts for that stat rather than accumulating across the recovery.

## Rationale
Satisfies CMP-009's declared need to advance health status. BR-001's "0 terminal transitions
arise from an application fault" is what makes this a contract with exactly one provider and
no presence on the recovery paths: FR-010 and FR-012 reach a default pet without ever calling
it.

**Confidence is low.** FR-008 requires a per-stat below-threshold clock continuous across an
application close, and the glossary's Pet state entry — the single maintained enumeration of
what is persisted (A-22) — carries no such field. Reconstructing that clock from the decay
curve at each evaluation and persisting it as a new field are both open; the choice is tracked
under Q-10 (still_open) by A-24 and is deferred by this stage. The operation's shape and the
deadline-rule choice above survive either answer, but what `advance` can be given, and whether
A-22's enumeration must grow, does not.

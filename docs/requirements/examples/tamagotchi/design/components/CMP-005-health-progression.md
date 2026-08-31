---
id: CMP-005
type: component
title: Health Progression
description: The single writer of the pet's health status, advancing it one step along the Healthy to Sick to terminal end-of-life progression under sustained per-stat neglect.
traces_from: [FR-008, NFR-007, BR-001, BR-002]
traces_to:
  adr: [ADR-001, ADR-005]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Advances the pet's health status under sustained unremedied neglect.
boundary: internal
depends_on: [IF-001, IF-016, IF-018]
---

# CMP-005 — Health Progression

The single writer of the pet's health status, advancing it one step along the
Healthy to Sick to terminal end-of-life progression under sustained per-stat neglect.

## Responsibility
Advances the pet's health status under sustained unremedied neglect.

## Rationale
BR-001's "0 terminal transitions arise from an application fault" is an allocation
rule before it is a behaviour: health-status advancement must have exactly one writer,
and that writer must not sit on the recovery path FR-010 and FR-012 define. Making
this a component distinct from the launch and recovery sequence is what makes that
claim inspectable. BR-002 is honoured by omission — no disposition of a terminal pet
is implemented anywhere, so the terminal status is a state this progression can reach
and nothing downstream consumes.

Requirements assumption A-6 puts two rules over a non-positive elapsed interval, and this design names the
discriminator wherever the interval is consumed rather than hiding it in the clock. This
component is the third consumer, and it applies the DEADLINE rule: the interval since a
stat's below-threshold-since origin is tested, and wherever that interval computes as
non-positive the origin is re-based to the current wall-clock reading. That is FR-011's
rule, not FR-002's clamp.

The clock is a deadline because FR-008 measures unbroken continuity from an origin
rather than accumulating elapsed time. A stat raised back above its threshold stops that
stat's clock outright and no accumulated total survives it, so there is no quantity here
to clamp — there is an origin and a duration, which is the shape of a deadline. Clamping
alone would leave the origin ahead of the clock after a backward jump and defer the
Healthy -> Sick transition for as long as the jump lasted, which is deferral without
bound: precisely the failure requirements A-6 introduces the second rule to prevent. Re-basing bounds
it, so that after a backward clock change the pet advances no later than one
sustained-neglect duration after the first pet-state evaluation following the change —
the same shape FR-011's own backward-clock criterion takes. Neither rule can produce an
advance that sustained neglect did not earn, so BR-001 is safe under both; boundedness
is what decides it.

Confidence is low. FR-008 requires a per-stat below-threshold clock that runs unbroken
across an application close, while the Pet state enumeration carries no such field.
Reconstructing that clock from the decay curve at each evaluation, or introducing a new
persisted field (which would update requirements A-22's enumeration and CMP-001's field set), is an
open structural decision tracked under Q-10, which is still_open.

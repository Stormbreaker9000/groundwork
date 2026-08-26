---
id: IF-011
type: interface
title: Default Pet Construction
description: The contract that produces a default pet — the state both recovery paths initialize when no committed state is available.
traces_from: [FR-010, FR-012, NFR-004, BR-001]
traces_to:
  adr: [ADR-001, ADR-002, ADR-003, ADR-004]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-001
operations:
- name: default_pet
  summary: 'Return a default pet: health status Healthy, in the Awake state, every pet stat at its configuration-defined starting value, no sleep-entry timestamp, and no accumulated care or lifecycle history.'
  interaction: synchronous
error_modes:
- The balance parameter set has not been loaded — no starting values exist and no default pet can be constructed; the launch must not proceed with a partially initialized pet.
- A configured starting value falls outside its stat's bounds — rejected rather than clamped, because a clamped starting value would make every subsequent decay comparison against the reference model wrong from the first launch.
---

# IF-011 — Default Pet Construction

The contract that produces a default pet — the state both recovery paths initialize when no
committed state is available.

## Operations
- **default_pet** — Return a default pet: health status Healthy, in the Awake state, every pet
  stat at its configuration-defined starting value, no sleep-entry timestamp, and no accumulated
  care or lifecycle history.

## Interaction
Synchronous. The launch branch that calls it cannot continue without the pet it returns.

Exactly one operation, because the capability is exactly one thing. The glossary fixes what a
default pet is; there is no variant to parameterise and no second way to ask for it.

## Error Modes
- The balance parameter set has not been loaded — no starting values exist and no default pet
  can be constructed.
- A configured starting value falls outside its stat's bounds — rejected rather than clamped.

## Rationale
Satisfies CMP-011's declared need to produce a default pet, which FR-010 requires when no save
file is present and FR-012 requires after a failing file has been quarantined. Healthy is not a
default chosen for convenience: BR-001 requires 0 terminal transitions to arise from an
application fault, and this contract's inability to return anything but Healthy is what makes
the recovery paths structurally incapable of producing a terminal pet. The launch sequence
orders IF-026's load before this call, which is why an unloaded parameter set is a failure mode
here rather than a load trigger.

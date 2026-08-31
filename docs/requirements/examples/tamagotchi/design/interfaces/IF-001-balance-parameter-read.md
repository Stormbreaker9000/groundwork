---
id: IF-001
type: interface
title: Balance Parameter Read
description: The contract through which every component that needs a balance or tuning parameter — stat bounds and starting values, the decay curve, neglect thresholds and durations, mood bands, care increments and the sleep duration — reads it from memory, rather than holding it and rather than touching the configuration source it was loaded from.
traces_from: [FR-003, FR-004, FR-005, FR-007, FR-008, FR-010, FR-011, NFR-001, NFR-008]
traces_to:
  adr: [ADR-001, ADR-005]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-002
operations:
- name: stat_bounds_and_starting_values
  summary: Return each pet stat's minimum, maximum, and the starting value a default pet is built from.
  interaction: synchronous
- name: decay_parameters
  summary: Return the decay-curve parameters the reference decay model is defined over.
  interaction: synchronous
- name: neglect_thresholds
  summary: Return each pet stat's own neglect threshold.
  interaction: synchronous
- name: sustained_neglect_durations
  summary: Return both sustained-neglect durations — Healthy to Sick, and the neglect period from Sick to the terminal end-of-life status.
  interaction: synchronous
- name: mood_band_boundaries
  summary: Return the mood-threshold bands and the mood expression each band maps to.
  interaction: synchronous
- name: care_increments
  summary: Return the increment each care-loop action adds to its corresponding stat.
  interaction: synchronous
- name: sleep_duration
  summary: Return the sleep duration measured from a pet's sleep-entry timestamp.
  interaction: synchronous
error_modes:
- A read arrives before the parameter set has been loaded into memory for this session — reported as its own outcome rather than triggering a load, because a read that can load is a read that can touch a file, and NFR-008 requires the decay computation's transitive reads to stay file-free.
- A requested parameter is absent from the loaded set — the caller receives no value rather than a silent default, because a silently defaulted decay rate or neglect threshold passes every functional test while producing the wrong pet.
- A parameter is present but out of range — a starting value outside the stat bounds, a non-positive duration, a band that maps to no mood expression — rejected rather than clamped into plausibility.
---

# IF-001 — Balance Parameter Read

The contract through which every component that needs a balance or tuning parameter —
stat bounds and starting values, the decay curve, neglect thresholds and durations,
mood bands, care increments and the sleep duration — reads it from memory, rather than
holding it and rather than touching the configuration source it was loaded from.

## Operations
- **stat_bounds_and_starting_values** — Return each pet stat's minimum, maximum, and the
  starting value a default pet is built from.
- **decay_parameters** — Return the decay-curve parameters the reference decay model is
  defined over.
- **neglect_thresholds** — Return each pet stat's own neglect threshold.
- **sustained_neglect_durations** — Return both sustained-neglect durations — Healthy to
  Sick, and the neglect period from Sick to the terminal end-of-life status.
- **mood_band_boundaries** — Return the mood-threshold bands and the mood expression each
  band maps to.
- **care_increments** — Return the increment each care-loop action adds to its stat.
- **sleep_duration** — Return the sleep duration measured from a sleep-entry timestamp.

## Interaction
Synchronous throughout, and every operation is a memory read. Every reader needs its
parameter before it can produce anything at all — a decay curve with no rates and a mood
selector with no bands each compute nothing.

Seven operations rather than one blob accessor. All seven consumers declared the same
capability, so this is necessarily one contract; grouping the parameters by the requirement
that needs them is the only segregation available inside it. No consumer reads more than two
groups: the pet state model reads bounds, the decay engine the curve, health progression
thresholds and durations, the reminder service thresholds alone, mood the bands, care the
increments, sleep the duration.

**This contract does not read a file, and cannot.** The parameter set reaches memory exactly
once, through IF-026, ordered by the launch sequence before any reader runs. That separation
is not tidiness: NFR-008 and requirements A-17 require the decay computation to be invocable 1,000 times
in a loop against an in-memory starting state with no save file read and no application
launch, and the decay engine reads `decay_parameters` on every one of those repetitions. If
a parameter read could fall back to loading its source, those 1,000 repetitions would each
be a potential file access and the constraint would be unmeetable. Hence the first error
mode below reports the unloaded case rather than repairing it.

## Error Modes
- A read arrives before the parameter set has been loaded for this session — reported as its
  own outcome rather than triggering a load, because a read that can load is a read that can
  touch a file.
- A requested parameter is absent from the loaded set — the caller receives no value rather
  than a silent default, because a silently defaulted decay rate or neglect threshold passes
  every functional test while producing the wrong pet.
- A parameter is present but out of range — a starting value outside the stat bounds, a
  non-positive duration, a band mapping to no mood expression — rejected rather than clamped.

## Rationale
Satisfies the identical capability declared by CMP-001, CMP-004, CMP-005, CMP-006, CMP-007,
CMP-008 and CMP-014. Every numeric value behind these operations is unfixed pending Q-1
(still_open), which is exactly why the indirection exists — but the operation set follows
from the requirements that name the parameters (requirements A-2 bounds, NFR-001's curve, FR-008's
thresholds and durations, FR-007's bands, FR-003/4/5's increments, FR-011's sleep duration)
and not from Q-1's answer. Confidence is medium because the grouping is inferred, not
because the values are open. Source-level failures — a missing or unparseable configuration
file — belong to IF-026 and are deliberately absent here.

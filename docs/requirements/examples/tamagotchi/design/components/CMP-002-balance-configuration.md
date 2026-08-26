---
id: CMP-002
type: component
title: Balance Configuration
description: The supplier of every tunable value the pet simulation reads — decay rates, neglect thresholds, both sustained-neglect durations, the sleep duration, mood-threshold band boundaries, care increments, and stat bounds and starting values.
traces_from: [FR-003, FR-004, FR-005, FR-007, FR-008, FR-010, FR-011, NFR-001, NFR-008]
traces_to:
  adr: []
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: low
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Supplies the pet's balance and tuning parameters to the components that read them.
boundary: internal
depends_on: [IF-019]
---

# CMP-002 — Balance Configuration

The supplier of every tunable value the pet simulation reads — decay rates, neglect
thresholds, both sustained-neglect durations, the sleep duration, mood-threshold band
boundaries, care increments, and stat bounds and starting values.

## Responsibility
Supplies the pet's balance and tuning parameters to the components that read them.

## Rationale
Every numeric value in the requirement set is deferred to Q-1, and the requirements
themselves are written around that — "the feed interaction's defined increment", "the
configuration-defined starting value", "band boundaries come from Q-1 and are not
fixed by this requirement". Naming one supplier keeps those values out of the logic
components entirely, so the balance loop Q-1 describes can run without touching the
decay, progression, mood or care code.

The parameter set is read from a local configuration file exactly once, when the
launch sequence asks for it, and is then held in memory for the rest of the session.
That ordering is what keeps two different failure kinds apart: a missing, unreadable or
unparseable source is a launch-time failure with a caller positioned to abandon the
launch, while a parameter read after the load cannot fail on source grounds at all. It
is also what keeps NFR-008's measure executable — the decay computation reads its curve
parameters from memory, so invoking it a thousand times in a loop reads no file and
starts no application, which is exactly what A-17 requires of it.

Confidence is low: Q-1 is still_open, so every value this component carries is
unfixed. Only its shape — a read-only parameter set with one owner, filled once at
launch — is settled.

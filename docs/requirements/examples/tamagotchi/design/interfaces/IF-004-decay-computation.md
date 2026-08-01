---
id: IF-004
type: interface
title: Decay Computation
description: The contract through which a set of Stat values is advanced over an elapsed interval according to the reference Decay model, as a deterministic computation with no clock and no state of its own.
traces_from:
- FR-002
- NFR-001
- NFR-007
- BR-002
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-30
scope: project
parent_scope: null
provider: CMP-002
operations:
- name: apply_decay
  summary: Given a set of Stat values and a non-negative elapsed interval, return the Stat values after the reference Decay model has been applied, clamped to the valid Stat range.
- name: maximum_offline_interval
  summary: Report the configured cap beyond which additional elapsed time accrues no further Decay, so a caller can tell a capped result from an uncapped one.
interaction: synchronous
error_modes:
- Negative elapsed interval — a backward clock change was observed, so BR-002 requires zero Decay and the caller must be told the interval was rejected rather than silently receiving unchanged stats.
- Elapsed interval beyond the configured maximum — Decay is capped, and the caller is told the cap applied so that the difference is visible to NFR-007's log rather than silent.
- Input Stat values outside the valid range — the supplied state is one the model cannot evaluate, and it must be refused rather than clamped into plausibility.
---

# IF-004 — Decay Computation

The contract through which a set of Stat values is advanced over an elapsed interval
according to the reference Decay model, as a deterministic computation with no clock
and no state of its own.

## Operations
- **apply_decay** — Given a set of Stat values and a non-negative elapsed interval,
  return the Stat values after the reference Decay model has been applied, clamped
  to the valid Stat range.
- **maximum_offline_interval** — Report the configured cap beyond which additional
  elapsed time accrues no further Decay, so a caller can tell a capped result from
  an uncapped one.

## Interaction
Synchronous. This is a pure computation with no I/O: CMP-007 cannot seed the session
until the caught-up stats exist, and CMP-003 cannot apply its in-session tick until
the new values are known. There is nothing here to await.

## Error Modes
- Negative elapsed interval — a backward clock change was observed, so BR-002 requires
  zero Decay and the caller must be told the interval was rejected rather than
  silently receiving unchanged stats.
- Elapsed interval beyond the configured maximum — Decay is capped, and the caller is
  told the cap applied so that the difference is visible to NFR-007's log rather than
  silent.
- Input Stat values outside the valid range — the supplied state is one the model
  cannot evaluate, and it must be refused rather than clamped into plausibility.

## Rationale
Satisfies CMP-003's and CMP-007's identically declared need to compute accrued decay:
the coordinator applies it once at launch over the offline interval (FR-002), the
manager applies it repeatedly in-session on a low-frequency timer under NFR-002's
budget. Same computation, same provider, one contract. Keeping the model free of both
a clock and stored state is what makes NFR-001's 1000 sampled intervals testable
without waiting thirty days.

Confidence is **low** because of **Q-1**, which is still open: the exact decay curve,
rates, thresholds and increments are undecided. That does not threaten the existence
of this contract — FR-002 and NFR-001 fix it as a function of (Stats, elapsed
interval). What Q-1 leaves open is whether the tuning parameters are supplied per call
or owned inside CMP-002, and whether the model needs any history beyond the interval.
If Q-1 resolves to a curve that depends on more than elapsed time — a neglect streak,
or a per-Stat schedule that varies with lifecycle state — this contract grows an input
and both consumers change with it.

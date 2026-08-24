---
id: NFR-008
type: non_functional
tier: solution
title: Offline-decay computation cost does not scale with the length of the absence
description: The offline-decay computation shall not scale materially with the length of the elapsed interval it is given, so that a 30-day absence does not cost proportionally more time to process than a short one.
rationale: FR-002 requires up to 30 days of offline decay to be computed and applied before the pet is displayed, which puts an interval-proportional computation directly on the owner-visible launch path. A tick-by-tick implementation is the specific failure mode, and it is invisible in development where intervals are minutes and only appears for the owner who actually went away for a month. The property is measured on the decay computation invoked in isolation rather than through a launch, because the ratio needs many repetitions inside one session and a launch cannot be repeated that way; NFR-009 bounds the same computation in place on the launch path. This is the half of the launch-cost concern that is machine-independent and therefore verifiable today, while NFR-009's absolute wall-clock bound stays blocked on the unfixed reference machine (Q-5). Splitting them means a verdict on the algorithm's shape is available now rather than waiting on a product decision.
fit_criterion: On any single machine, in one measurement session, over at least 20 runs per arm, the p95 computation time for a 30-day elapsed interval is <= 5x the p95 for a 1-hour elapsed interval over the same starting state. One run is the total time of a batch of >= 1,000 repetitions of the decay computation divided by the repetition count; the computation is invoked directly with the starting pet state supplied in memory, with no save file read and no application launch at any point in the measurement. The batch size is increased until the short-arm batch total exceeds 10 ms, so that neither arm is measured at the platform timer-resolution noise floor. No reference-machine specification is required.
priority: must
confidence: medium
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-008 — Offline-decay computation cost does not scale with the length of the absence

## ISO 25010 Characteristic
Performance Efficiency → Time behavior

## Quality Attribute Scenario
- **Source of stimulus:** A performance test harness, standing in for the owner
  who relaunches the application after being away for a long period.
- **Stimulus:** The decay computation is invoked directly with a starting pet
  state and an elapsed interval, at the two interval lengths the comparison
  uses — 1 hour, and the 30-day worst case that FR-002 permits and NFR-001's
  test matrix already exercises — and each invocation is repeated within one
  measurement session.
- **Environment:** Any single development or CI machine, with both arms measured
  in the same session on the same hardware so the comparison is internal; no
  save file is read and no application launch occurs — the starting pet state is
  supplied directly to the computation; no reference-machine specification
  required, and therefore no dependency on Q-5.
- **Artifact:** The offline-decay computation as an independently invocable
  unit — the function that maps a starting pet state and an elapsed interval to
  a decayed pet state — exercised directly rather than through a launch, so that
  it can be repeated within one measurement session. The same computation on the
  launch path is what NFR-009 bounds in absolute terms.
- **Response:** The decay for the whole elapsed interval is computed and applied
  in one bounded step rather than by walking the interval tick by tick, so the
  cost of the computation is substantially independent of how long the owner was
  away.
- **Response measure:** Over at least 20 runs per arm, p95 computation time for
  a 30-day elapsed interval is <= 5x the p95 for a 1-hour elapsed interval, both
  measured on the same machine in the same session over the same starting state.
  One run is the total time of a batch of >= 1,000 repetitions divided by the
  repetition count, with the batch size raised until the short-arm batch total
  exceeds 10 ms, so neither arm is taken near the platform timer resolution.

## Rationale
Launch is the only moment the owner meets the product, and FR-002 places an
interval-proportional computation squarely in front of it. Thirty days of decay
is exactly the case a tick-loop implementation gets wrong: a naive loop over a
30-day interval does roughly 720 times the work of a 1-hour one, which a 5x
ceiling rejects outright, while a closed-form computation is essentially flat and
passes with wide margin.

The measurement deliberately takes the decay computation on its own rather than
in place on the launch path. The ratio is only meaningful well above the timer
floor, which needs a batch of repetitions inside one session; a launch, which
ends at first render, cannot be repeated that way, and 1,000 relaunches would
put process start into both arms and swamp the quantity under test. Measuring
the unit directly is what makes the batching rule executable. The cost on the
launch path itself is not left unbounded — NFR-009 carries it.

The short arm is 1 hour rather than 1 minute because a 1-minute interval is
likely sub-millisecond, and a ratio taken there would be measuring timer jitter
rather than algorithmic cost. The batching rule closes the same gap from the
other direction by guaranteeing the timed quantity sits well above the
resolution floor on any platform, so the measure is meaningful without naming
hardware. The 20-run floor per arm is the same sample basis NFR-009 uses, so
that a p95 is taken over a stated sample rather than interpolated from a
handful of points.

This requirement deliberately carries no absolute wall-clock figure. The absolute
bound is NFR-009, which inherits NFR-002's dependency on the unfixed reference
machine; a single verdict spanning both would be unavailable until Q-5 closes,
even though the property that actually distinguishes a correct implementation
from a broken one is testable today.

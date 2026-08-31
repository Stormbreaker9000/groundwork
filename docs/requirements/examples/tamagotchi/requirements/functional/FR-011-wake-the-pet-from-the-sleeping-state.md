---
id: FR-011
type: functional
tier: solution
title: Wake the pet from the Sleeping state
description: While the pet is in the Sleeping state, when the elapsed wall-clock time since its sleep-entry timestamp — computed under the non-positive-interval rule FR-002 applies, and measured from a sleep-entry timestamp that the system re-bases to the current time whenever that elapsed interval computes as non-positive — reaches the defined sleep duration, the system shall transition the pet to the Awake state.
rationale: "Without a normative exit, Sleeping is a state the pet can enter and never leave — the sleep action would be usable exactly once per pet, contradicting its role as one of the four repeatable care interactions, and the wake transition that pet-lifecycle logging records would never be produced by anything. A time-based exit keeps the owner-facing interaction set at the four defined actions and resolves consistently whether or not the application was running while the pet slept. The elapsed interval is computed under FR-002's non-positive-interval rule because this arithmetic spans an application close — precisely the window in which an owner changes the clock, DST lands, or NTP corrects. That rule alone is not sufficient here. Clamping a negative interval to zero is the correct answer for decay, where a stat that does not move is safe, and the wrong answer for a deadline, where a deadline that never arrives is the exact hazard: a backward jump larger than the sleep already served leaves the elapsed interval clamped at zero, so the wake is deferred by the size of the jump — unbounded in that size, and never arriving at all if the clock is left where the owner put it. Re-basing the sleep-entry timestamp whenever the elapsed interval computes as non-positive re-anchors the deadline to the clock the owner actually left in place, so the wake arrives within one sleep duration of the first evaluation following any backward change, and no forward correction is required for the pet to wake. Where the change lands while the application is closed the re-base happens at the next launch, so the pet serves a further full sleep duration from that launch — bounded, and never stranded, but later than a running application delivers."
fit_criterion: "Across scripted trials sampling the boundary at +/-1 second, the pet's state field equals Sleeping at every sample before the defined sleep duration has elapsed and equals Awake at the first sample at or after it, in 100% of trials; this holds in 100% of trials where the duration elapses entirely while the application is closed, and 0% of trials leave the pet in the Sleeping state once the duration has elapsed. Across backward-clock trials injected at points spanning the sleep interval, with backward jumps of 1 hour, 1 day and 30 days and no forward correction applied, 100% of trials wake the pet no later than one sleep duration after the first pet-state evaluation that follows the backward clock change — the next scheduled check where the application is running, or the next launch where it was closed. The sleep duration is the Q-1 balance value, not a value fixed by this requirement."
priority: must
confidence: low
verification_method: test
ears_pattern: complex
status: draft
created_at: 2026-08-24
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-011 — Wake the pet from the Sleeping state

## Description
While the pet is in the Sleeping state, when the elapsed wall-clock time since its
sleep-entry timestamp — computed under the non-positive-interval rule FR-002 applies,
and measured from a sleep-entry timestamp that the system re-bases to the current time
whenever that elapsed interval computes as non-positive — reaches the defined sleep
duration, the system shall transition the pet to the Awake state.

## Rationale
Without a normative exit, Sleeping is a state the pet can enter and never leave — the
sleep action would be usable exactly once per pet, contradicting its role as one of the
four repeatable care interactions, and the wake transition that pet-lifecycle logging
records would never be produced by anything. A time-based exit keeps the owner-facing
interaction set at the four defined actions and resolves consistently whether or not the
application was running while the pet slept.

The elapsed interval is computed under FR-002's non-positive-interval rule because this
arithmetic spans an application close — precisely the window in which an owner changes
the clock, DST lands, or NTP corrects. That rule alone is not sufficient here. Clamping a
negative interval to zero is the correct answer for decay, where a stat that does not move
is safe, and the wrong answer for a deadline, where a deadline that never arrives is the
exact hazard: a backward jump larger than the sleep already served leaves the elapsed
interval clamped at zero, so the wake is deferred by the size of the jump — unbounded in
that size, and never arriving at all if the clock is left where the owner put it.
Re-basing the sleep-entry timestamp whenever the elapsed interval computes as non-positive
re-anchors the deadline to the clock the owner actually left in place, so the wake arrives
within one sleep duration of the first evaluation following any backward change, and no
forward correction is required for the pet to wake. Where the change lands while the
application is closed the re-base happens at the next launch, so the pet serves a further
full sleep duration from that launch — bounded, and never stranded, but later than a
running application delivers.

## Acceptance Criteria
### AC-1 — Pet wakes when the sleep duration elapses
```gherkin
Given the pet is in the Sleeping state and entered it exactly the defined sleep duration ago
When the pet-state check runs
Then the pet's state becomes Awake
```

### AC-2 — Pet remains asleep before the duration elapses
```gherkin
Given the pet is in the Sleeping state and entered it less than the defined sleep duration ago
When the pet-state check runs
Then the pet's state remains Sleeping
```

### AC-3 — Sleep completed while the application was closed
```gherkin
Given the pet was in the Sleeping state when the application was last closed
And the elapsed wall-clock time since it entered that state now exceeds the defined sleep duration
When the application launches
Then the pet is in the Awake state before it is displayed
```

### AC-4 — Backward clock re-bases the wake deadline rather than deferring it
```gherkin
Given the pet is in the Sleeping state
When the system clock moves backward by more than the sleep already served
And no forward correction is applied to the clock afterward
Then at the next pet-state evaluation the pet's sleep-entry timestamp is re-based to that evaluation's current time
And the pet wakes no later than one sleep duration after that evaluation
```

## Fit Criterion
Across scripted trials sampling the boundary at +/-1 second, the pet's state field equals
Sleeping at every sample before the defined sleep duration has elapsed and equals Awake at
the first sample at or after it, in 100% of trials; this holds in 100% of trials where the
duration elapses entirely while the application is closed, and 0% of trials leave the pet
in the Sleeping state once the duration has elapsed. Across backward-clock trials injected
at points spanning the sleep interval, with backward jumps of 1 hour, 1 day and 30 days and
no forward correction applied, 100% of trials wake the pet no later than one sleep duration
after the first pet-state evaluation that follows the backward clock change — the next
scheduled check where the application is running, or the next launch where it was closed.
The sleep duration is the Q-1 balance value, not a value fixed by this requirement.

<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/requirements/functional/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Functional requirements

The 12 functional requirements from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## FR-001 — Persist pet state on stat change and app close [#fr-001]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | stakeholder |
| Priority | must |
| Status | draft |
| Confidence | high |
| EARS pattern | event |
| Verification | test |
| Traces from | [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

### Description
When a pet stat value changes or the owner closes the application, the system shall
persist the current pet state to local storage.

### Rationale
Without persistence the pet's progress and current condition would be lost between
sessions, defeating the premise that the pet is a persistent companion the owner returns
to — the core mechanic the daily-return habit loop depends on. Persistence covers the pet
state in full and not only its stat values: FR-006's Sleeping state and FR-011's wake
deadline both survive an application close only because the Awake/Sleeping field and the
sleep-entry timestamp are persisted with everything else.

### Acceptance Criteria
#### AC-1 — State is written when a stat changes
```gherkin
Given the owner performs a feed action that changes the pet's hunger stat
When the stat change is applied
Then the updated pet state, including the new stat value and a save timestamp, is written to local storage immediately
```

#### AC-2 — State is written on application close
```gherkin
Given the pet's current state has not yet been saved since the last stat change
When the owner closes the application
Then the final pet state is written to local storage before the process exits
```

#### AC-3 — Sleep state and its entry timestamp survive a close
```gherkin
Given the pet is in the Sleeping state with a recorded sleep-entry timestamp
And a positive interval of less than the defined sleep duration will have elapsed when the application is reopened
When the owner closes the application and reopens it
Then the pet is in the Sleeping state
And its sleep-entry timestamp equals the value recorded before the close
```

### Fit Criterion
Every field of the pet state held at close round-trips unchanged: across 50 restart cycles,
100% of persisted fields are present in the restored state and equal to their pre-close
values, with 0 fields absent and 0 fields differing. The fields under test include, and are
not limited to, every pet stat value, the health status, the Awake/Sleeping state field, the
sleep-entry timestamp wherever the pet is Sleeping, and the last-saved timestamp.

## FR-002 — Apply offline-elapsed decay at launch [#fr-002]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| EARS pattern | event |
| Verification | test |

### Description
When the application launches, the system shall compute stat decay from the real
wall-clock time elapsed since the last committed save, treating any elapsed interval
at or below zero as zero elapsed time so that no stat value increases as a result of
decay computation, and apply the resulting decay to the pet's stats before the pet is
displayed.

### Rationale
The product's premise is that the pet ages in real time whether or not the app is
running; without decay computed from actual elapsed time at launch, time away would
have no consequence and the periodic check-in habit the product exists to create
would have nothing to enforce it. The clamp at zero is required because the elapsed
interval is derived from a device clock the owner can move backward (manual change,
DST, NTP correction), and a negative interval driven through the decay function would
raise stats — silently rewarding clock tampering and corrupting the neglect
progression.

### Acceptance Criteria
#### AC-1 — Decay applied for a short offline interval
```gherkin
Given the last committed save's timestamp is 3 hours before the current launch time
When the application launches
Then each stat is reduced by the decay amount the reference decay model produces for a 3-hour interval, within +/-1 stat unit
```

#### AC-2 — Decay applied for a long offline interval
```gherkin
Given the last committed save's timestamp is 30 days before the current launch time
When the application launches
Then decay is computed and applied without error or numeric overflow, matching the reference decay model's 30-day decay output within +/-1 stat unit
```

#### AC-3 — Backward clock yields no decay and no stat increase
```gherkin
Given the system clock now reads earlier than the last committed save's timestamp
When the application launches
Then no decay is applied and no stat value increases
```

### Fit Criterion
For elapsed intervals from 1 minute to 30 days, the decay applied at launch is within
+/-1 stat unit of the reference decay model, verified across a test matrix of
representative intervals; for elapsed intervals at or below zero, including a system
clock set behind the last committed save's timestamp, the computed decay is exactly
zero and 0% of trials show any stat value higher after launch than at the last
committed save.

## FR-003 — Feed the pet [#fr-003]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| EARS pattern | event |
| Verification | test |

### Description
When the owner selects the feed action, the system shall increase the pet's hunger
stat by the feed interaction's defined increment, up to the stat's maximum value.

### Rationale
Feed is one of the four care interactions the owner performs to counteract stat
decay; without it the owner has no way to address hunger decay, breaking the core
care loop the attachment habit depends on.

### Acceptance Criteria
#### AC-1 — Feeding increases hunger below maximum
```gherkin
Given the pet's hunger stat is below its maximum value
When the owner selects the feed action
Then the hunger stat increases by the feed interaction's defined increment, not exceeding the maximum value
```

#### AC-2 — Feeding at maximum hunger has no further effect
```gherkin
Given the pet's hunger stat is already at its maximum value
When the owner selects the feed action
Then the hunger stat remains at its maximum value with no error
```

### Fit Criterion
The hunger stat increases by the configured feed increment (or is unchanged if
already at maximum) in 100% of feed action invocations in acceptance tests.

## FR-004 — Play with the pet [#fr-004]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| EARS pattern | event |
| Verification | test |

### Description
When the owner selects the play action, the system shall increase the pet's
happiness stat by the play interaction's defined increment, up to the stat's
maximum value.

### Rationale
Play is one of the four care interactions the owner performs to counteract stat
decay; without it the owner has no way to raise happiness, and low happiness would
be irrecoverable, undermining both the care loop and the mood display it feeds.

### Acceptance Criteria
#### AC-1 — Playing increases happiness below maximum
```gherkin
Given the pet's happiness stat is below its maximum value
When the owner selects the play action
Then the happiness stat increases by the play interaction's defined increment, not exceeding the maximum value
```

#### AC-2 — Playing at maximum happiness has no further effect
```gherkin
Given the pet's happiness stat is already at its maximum value
When the owner selects the play action
Then the happiness stat remains at its maximum value with no error
```

### Fit Criterion
The happiness stat increases by the configured play increment (or is unchanged if
already at maximum) in 100% of play action invocations in acceptance tests.

## FR-005 — Clean the pet [#fr-005]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| EARS pattern | event |
| Verification | test |

### Description
When the owner selects the clean action, the system shall increase the pet's
hygiene stat by the clean interaction's defined increment, up to the stat's maximum
value.

### Rationale
Clean is one of the four care interactions the owner performs to counteract stat
decay; without it sustained hygiene neglect cannot be remedied, and unresolved
hygiene decay is one of the inputs to the sickness progression this pet must be
protected from.

### Acceptance Criteria
#### AC-1 — Cleaning increases hygiene below maximum
```gherkin
Given the pet's hygiene stat is below its maximum value
When the owner selects the clean action
Then the hygiene stat increases by the clean interaction's defined increment, not exceeding the maximum value
```

#### AC-2 — Cleaning at maximum hygiene has no further effect
```gherkin
Given the pet's hygiene stat is already at its maximum value
When the owner selects the clean action
Then the hygiene stat remains at its maximum value with no error
```

### Fit Criterion
The hygiene stat increases by the configured clean increment (or is unchanged if
already at maximum) in 100% of clean action invocations in acceptance tests.

## FR-006 — Put the pet to sleep [#fr-006]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| EARS pattern | complex |
| Verification | test |

### Description
While the pet is not already in the Sleeping state, when the owner selects the
sleep action, the system shall transition the pet to the Sleeping state.

### Rationale
Sleep is the fourth of the four defined care interactions, and a discrete Sleeping
state gives the sleep action a persisted, loggable effect (FR-001, NFR-007) and a
defined exit (FR-011). Sleep deliberately does not alter stat decay, and no
requirement in this set renders the Sleeping state to the owner — FR-007 maps the
mood display to the lowest stat value alone, and NFR-003 requires only mood and
health status to be perceivable. Whether the Sleeping state should be owner-visible
is open question Q-8 (owner product); until Q-8 closes, the value of this
requirement rests on persistence and traceability rather than on anything the owner
can see.

### Acceptance Criteria
#### AC-1 — Selecting sleep while awake transitions the pet
```gherkin
Given the pet is in the Awake state
When the owner selects the sleep action
Then the pet's state becomes Sleeping
```

#### AC-2 — Selecting sleep while already sleeping is idempotent
```gherkin
Given the pet is already in the Sleeping state
When the owner selects the sleep action again
Then the pet's state remains Sleeping with no error
```

### Fit Criterion
The pet's state field equals Sleeping immediately after the sleep action is
selected while the pet was previously Awake, in 100% of interaction tests; the
state field remains Sleeping and unchanged if the action is selected again while
already Sleeping.

## FR-007 — Display mood expression tracking stat thresholds [#fr-007]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | stakeholder |
| Priority | must |
| Status | draft |
| Confidence | medium |
| EARS pattern | state |
| Verification | test |

### Description
While the pet's lowest stat value falls within a given mood-threshold band, the
system shall display the mood expression mapped to that band.

### Rationale
Owners need an at-a-glance wellbeing indicator so they can judge whether care is
needed without inspecting individual numeric stats; this directly supports the daily
check-in habit by making neglect visible immediately rather than requiring the owner
to interpret raw numbers. The lowest stat is the reduction rule because the indicator
exists to surface the need most at risk of being missed — an average would let one
critically low stat be masked by healthy ones, which is the exact failure the display
is there to prevent.

### Acceptance Criteria
#### AC-1 — Mood expression matches the band of the lowest stat
```gherkin
Given the pet's lowest stat value falls within the "content" mood-threshold band
When the mood expression is displayed
Then the expression shown is the one mapped to the "content" band
```

#### AC-2 — Stats in different bands resolve to the lowest stat's band
```gherkin
Given the pet's hunger stat falls within the "content" mood-threshold band
And the pet's hygiene stat falls within a lower mood-threshold band
When the mood expression is displayed
Then the expression shown is the one mapped to the lower band containing the hygiene stat
```

#### AC-3 — Mood expression updates when the lowest stat crosses a band boundary
```gherkin
Given the pet's lowest stat value is within the "content" mood-threshold band
When decay or neglect moves that stat into a lower mood-threshold band
Then the displayed mood expression updates to the expression mapped to the new band
```

### Fit Criterion
The displayed mood expression matches the expression mapped to the band containing
the pet's lowest stat value in 100% of sampled states, across a test matrix that
spans every defined band and includes states in which the individual stats fall in
different bands. Band boundaries are taken from the Q-1 balance values and are not
fixed by this requirement.

## FR-008 — Progress sustained neglect toward a terminal health status [#fr-008]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| EARS pattern | state |
| Verification | test |
| Traces from | [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

### Description
While at least one of the pet's stats remains below its neglect threshold
continuously for the defined sustained-neglect duration, the system shall advance the
pet's health status one step along the Healthy -> Sick -> terminal end-of-life
progression.

### Rationale
Sustained neglect must have escalating, visible consequences for the daily-return
habit loop to carry real stakes, and a single ignored need is enough to constitute
neglect — requiring every stat to be starved simultaneously would let an owner
neglect one need indefinitely with no consequence. This requirement intentionally
stops at the terminal end-of-life status and does not assert what happens once it is
reached, because that disposition depends on open question Q-2 (whether the terminal
state is permanent or a configurable soft reset), which is owned by a separate
business rule.

### Acceptance Criteria
#### AC-1 — Sustained neglect of a single stat advances Healthy to Sick
```gherkin
Given the pet's health status is Healthy
And the pet's hygiene stat has remained below its neglect threshold continuously for the defined sustained-neglect duration
And every other stat has remained above its neglect threshold throughout
When the neglect-progression check runs
Then the pet's health status becomes Sick
```

#### AC-2 — Continued neglect advances Sick to the terminal end-of-life status
```gherkin
Given the pet's health status is Sick
And at least one stat has remained below its neglect threshold continuously for the further defined duration
When the neglect-progression check runs
Then the pet's health status becomes the terminal end-of-life status
```

#### AC-3 — Recovery within the window does not advance health status
```gherkin
Given the pet's health status is Healthy
And a stat dropped below its neglect threshold and was restored above it before the defined sustained-neglect duration elapsed
When the neglect-progression check runs
Then the pet's health status remains Healthy
```

### Fit Criterion
Health status transitions Healthy -> Sick when at least one stat has remained below
its neglect threshold continuously for the defined sustained-neglect duration, and
Sick -> the terminal end-of-life status when at least one stat remains below its
neglect threshold for the further defined duration, matching the reference
progression model in 100% of scripted neglect-duration test cases; 0% of cases
advance health status when no stat has been below its threshold for the full
duration, including cases where a stat drops below and recovers within the window.
Behavior after the terminal status is reached is explicitly out of scope for this
requirement pending Q-2 and is not exercised by these cases.

## FR-009 — Present optional local care-reminder notifications [#fr-009]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | medium |
| EARS pattern | optional |
| Verification | test |
| Traces from | [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |

### Description
Where care-reminder notifications are enabled by the owner, the system shall
present a local, non-network notification when a pet stat crosses its neglect
threshold.

### Rationale
An always-on background pet with real-time decay risks the owner missing the
check-in window entirely; an opt-in local reminder supports the daily-return habit
for owners who want it, without imposing a mandatory interruption or any network
dependency on owners who don't.

### Acceptance Criteria
#### AC-1 — Notification presented when enabled and a threshold is crossed
```gherkin
Given the owner has enabled care-reminder notifications
When a pet stat crosses its defined neglect threshold
Then a local notification is presented to the owner via the operating system's native notification mechanism
And no network request is made in the course of presenting it
```

#### AC-2 — No notification when the feature is disabled
```gherkin
Given the owner has not enabled care-reminder notifications
When a pet stat crosses its defined neglect threshold
Then no notification is presented
```

### Fit Criterion
When notifications are enabled and any stat crosses its defined neglect threshold,
a local OS-level notification is presented in 100% of test trials; zero
notifications are presented, and zero network requests are made, when the feature
is disabled.

## FR-010 — Initialize a default pet when no save file is present [#fr-010]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| EARS pattern | unwanted |
| Verification | test |

### Description
If no save file is present at application launch, then the system shall initialize a
new default pet.

### Rationale
A first-ever launch and a launch after the save file has been lost to a crash, forced
termination, or storage clearance are indistinguishable to the application, and both
must produce a usable pet rather than a failure to start; without this the app has no
defined entry state and cannot launch at all on a clean install.

### Acceptance Criteria
#### AC-1 — No save file present
```gherkin
Given no save file exists at the expected storage location
When the application launches
Then a new default pet is initialized and displayed
And the application starts normally without crashing
```

#### AC-2 — No quarantine artifact is produced when there is no file
```gherkin
Given no save file exists at the expected storage location
When the application launches
Then no file is written to the quarantine location
```

### Fit Criterion
Across 100 missing-save fault-injection trials, the application launches with a valid
default pet in 100% of trials, 0% result in a crash or unhandled error, and 0% create
a quarantine artifact.

## FR-011 — Wake the pet from the Sleeping state [#fr-011]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| EARS pattern | complex |
| Verification | test |

### Description
While the pet is in the Sleeping state, when the elapsed wall-clock time since its
sleep-entry timestamp — computed under the non-positive-interval rule FR-002 applies,
and measured from a sleep-entry timestamp that the system re-bases to the current time
whenever that elapsed interval computes as non-positive — reaches the defined sleep
duration, the system shall transition the pet to the Awake state.

### Rationale
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

### Acceptance Criteria
#### AC-1 — Pet wakes when the sleep duration elapses
```gherkin
Given the pet is in the Sleeping state and entered it exactly the defined sleep duration ago
When the pet-state check runs
Then the pet's state becomes Awake
```

#### AC-2 — Pet remains asleep before the duration elapses
```gherkin
Given the pet is in the Sleeping state and entered it less than the defined sleep duration ago
When the pet-state check runs
Then the pet's state remains Sleeping
```

#### AC-3 — Sleep completed while the application was closed
```gherkin
Given the pet was in the Sleeping state when the application was last closed
And the elapsed wall-clock time since it entered that state now exceeds the defined sleep duration
When the application launches
Then the pet is in the Awake state before it is displayed
```

#### AC-4 — Backward clock re-bases the wake deadline rather than deferring it
```gherkin
Given the pet is in the Sleeping state
When the system clock moves backward by more than the sleep already served
And no forward correction is applied to the clock afterward
Then at the next pet-state evaluation the pet's sleep-entry timestamp is re-based to that evaluation's current time
And the pet wakes no later than one sleep duration after that evaluation
```

### Fit Criterion
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

## FR-012 — Quarantine a save file that fails integrity validation [#fr-012]

| Field | Value |
| --- | --- |
| Type | functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| EARS pattern | unwanted |
| Verification | test |

### Description
If a save file is present but fails integrity validation at application launch, then
the system shall move that file to the quarantine location unmodified before
initializing a new default pet.

### Rationale
Local storage can be corrupted by crashes, forced termination, or power loss, and
crashing on a bad save would break the app entirely; silently deleting or overwriting
the corrupt file destroys the only evidence available to diagnose the corruption, so
the artifact must be preserved intact while the owner is still given a working app.

### Acceptance Criteria
#### AC-1 — Corrupt save file is quarantined and a default pet is initialized
```gherkin
Given a save file exists at the expected storage location but fails integrity validation
When the application launches
Then the file is moved to the quarantine location byte-identical to its pre-launch content
And a new default pet is initialized and displayed
And the application starts normally without crashing
```

#### AC-2 — Corrupt save file is never destroyed in place
```gherkin
Given a save file exists at the expected storage location but fails integrity validation
When the application launches
Then no file remains at the original storage location containing the corrupt content
And the corrupt content has not been deleted, truncated, or overwritten by the new default pet state
```

### Fit Criterion
Across 100 corrupted-save fault-injection trials, 100% of the original files are found
byte-identical at the quarantine location afterward, 0% are deleted or overwritten in
place, 100% of trials launch with a valid default pet, and 0% result in a crash or
unhandled error.

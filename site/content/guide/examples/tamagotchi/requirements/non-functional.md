<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/requirements/non-functional/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Non-functional requirements

The 9 non-functional requirements from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## NFR-001 — Offline-elapsed decay matches the reference decay model [#nfr-001]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| Verification | test |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002) |

### ISO 25010 Characteristic
Functional Suitability → Functional correctness

### Quality Attribute Scenario
- **Source of stimulus:** The passage of real wall-clock time while the
  application is not running, surfaced when the owner relaunches.
- **Stimulus:** The application launches after an elapsed interval T since the
  last committed save, where T may be positive or, if the wall clock has moved
  backward, zero or negative.
- **Environment:** Normal operation; the positive matrix spans T from 1 minute to
  30 days, and the clock-regression matrix covers T at exactly zero and T
  negative (manual clock change, DST shift, NTP correction); a valid save file is
  present; elapsed time is derived from wall-clock timestamps.
- **Artifact:** The offline decay computation and the pet state model.
- **Response:** Decay is computed for every stat from the last-save timestamp to
  the current time and applied before the pet is first rendered, so the owner
  sees the post-decay state and never the stale pre-decay state. Where T is at or
  below zero, the interval is treated as zero elapsed time per FR-002, so no stat
  moves in either direction.
- **Response measure:** For at least 20 log-spaced intervals across 1 minute to
  30 days, each resulting stat is within ±1 stat unit of the reference decay
  model's value for the same interval and starting state; 0 out-of-range
  results. For at least 5 non-positive intervals (T = 0 and T < 0), each stat
  after launch equals its last-committed value exactly — 0 stats increased and 0
  stats decayed.

### Rationale
Offline decay is the mechanism the daily-return loop rests on. If relaunch state
does not match what elapsed time implies, the owner's sense that neglect has
consequences collapses and the habit the product exists to create does not form.
Testing against a reference model as an oracle keeps this target verifiable while
the decay curve and balance values remain an open product question (Q-1). The
non-positive-interval clause gives FR-002's clock-regression rule a measurable
oracle, so a backward clock cannot silently gift the owner a healthier pet.

## NFR-002 — Idle CPU and memory footprint of the always-on process [#nfr-002]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | test |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-001](/guide/examples/tamagotchi/requirements/constraints/#con-001) |

### ISO 25010 Characteristic
Performance Efficiency → Resource utilization (with Capacity implications for
the always-on process)

### Quality Attribute Scenario
- **Source of stimulus:** The owner, who leaves the application running
  unattended between check-ins.
- **Stimulus:** The application sits in an idle steady state — pet alive, window
  open, no owner input, no care action in progress.
- **Environment:** The project's designated reference machine under normal
  desktop use. That machine is a single named baseline whose hardware and OS
  specification has not yet been recorded (Q-5); this requirement depends on it
  normatively rather than assuming one. A continuous 10-minute observation
  window; measurements taken from OS process accounting and summed across every
  process the application owns.
- **Artifact:** The complete delivered runtime — the application process, any
  child or helper processes, and whatever rendering or background timer
  machinery the chosen implementation uses.
- **Response:** The application continues to keep time, render the pet, and
  remain ready for a care action, without accumulating CPU or memory.
- **Response measure:** On the designated reference machine, mean CPU <= 1% of
  one core and peak resident memory <= 150 MB across the 10-minute window; no
  monotonic growth — final RSS within 5% of the RSS sampled at the 1-minute
  mark. A run on any machine other than the recorded baseline is not evidence
  either way.

### Rationale
This is an application designed to be left open indefinitely, so its idle cost
determines whether the owner tolerates it running at all. A budget expressed in
measured CPU and RSS is testable against any candidate implementation, which is
what lets the runtime decision (Q-4) stay open without leaving the quality target
unspecified — so Q-4 is explicitly *not* what limits confidence here. What limits
it is that "1% of one core" and "150 MB" are not comparable figures without a
named baseline to measure them on, and no requirement, constraint or glossary
entry yet fixes one. That gap is tracked as Q-5, and this requirement becomes
verifiable the moment Q-5 is answered — the figures themselves need no revisiting.
CON-001 inherits the same dependency.

## NFR-003 — Keyboard-only and screen-reader operability of the full care loop [#nfr-003]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |
| Traces from | [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |

### ISO 25010 Characteristic
Interaction Capability → Operability, Inclusivity, Self-descriptiveness, User
assistance

### Quality Attribute Scenario
- **Source of stimulus:** A keyboard-only owner, or an owner using a screen
  reader.
- **Stimulus:** The owner navigates to and performs each of the four care
  actions — feed, play, clean, put to sleep — and reads the pet's current mood
  and health state.
- **Environment:** Normal operation, on each supported desktop platform using
  that platform's native accessibility stack and screen reader.
- **Artifact:** The application user interface — all interactive controls, focus
  order and focus indication, the mood expression, and any status or
  notification surface.
- **Response:** Each control is reached in a logical focus order, is operable
  from the keyboard, and announces a meaningful name and role; the mood and
  health state is announced as text and is distinguishable on screen by shape or
  label, not by hue alone; state changes caused by a care action are announced
  without the owner having to hunt for them.
- **Response measure:** 100% of interactive controls keyboard-reachable and
  operable with a visible focus indicator; 100% of mood and health states carry
  a non-color-dependent textual equivalent exposed to the accessibility API;
  contrast >= 4.5:1 for text and >= 3:1 for non-text state indicators; zero
  critical or serious violations from an automated accessibility scan; a
  scripted screen-reader walkthrough of all four care actions completes with 0
  unlabeled or unreachable controls.

### Rationale
Assistive-technology users are in scope as first-class owners. Because the
product's value is a repeated daily interaction, a single mouse-only control or a
color-only mood cue does not merely inconvenience these users — it removes them
from the habit loop entirely. Color-independence also covers colorblind owners
without needing the user-tunable palette that v1 excludes.

## NFR-004 — Crash-safe atomic persistence and recovery [#nfr-004]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012) |

### ISO 25010 Characteristic
Reliability → Fault tolerance and Recoverability

### Quality Attribute Scenario
- **Source of stimulus:** An external fault — forced process termination, OS
  crash, or power loss.
- **Stimulus:** The process is killed at an arbitrary point in its lifetime,
  including part-way through writing the save file.
- **Environment:** Normal operation with fault injection, covering saves
  triggered both by a stat change and by application close; local disk, no
  network involved.
- **Artifact:** The state persistence layer and the save file on local disk.
- **Response:** The next launch loads the last committed state. A partially
  written file is never presented as valid, because an interrupted write never
  reaches committed status and never replaces the file that is already
  committed. Where no committed state survives, the launch proceeds by the
  FR-owned recovery paths — FR-012 where a save file is present but fails
  integrity validation (including its quarantine), FR-010 where no save file is
  present — and this requirement asserts no behaviour of its own beyond
  reaching a valid state.
- **Response measure:** 200 fault-injection trials yield 100% launches into a
  valid pet state, 0 corrupt loads, 0 unhandled exceptions. In 100% of those
  trials where a committed state existed before the kill, that committed state
  is the state restored; recovery to a default pet occurs in 0% of such trials.
  50 clean restart cycles restore the exact prior state 100% of the time.

### Rationale
State written on every stat change means writes are frequent and a kill during a
write is routine rather than exotic. Because the persisted pet is the owner's
accumulated investment, corruption is not a degraded experience but a total loss
of the thing the product exists to build, so the recovery target is stated as an
absolute rather than a rate.

The discriminating half of the measure exists because "launches into a valid pet
state" is satisfied by a brand-new default pet, and a default pet is precisely
the outcome this requirement exists to prevent — it is the same loss BR-002
forbids applying silently. Requiring that a pre-existing committed state be the
one restored is achievable with single-generation retention and needs no new
scope: atomic commit means the in-progress write never touches the file that is
already committed, so the pre-kill committed state survives the kill intact and
the FR-012 path is never reached. Only where no committed state survives at all
does recovery apply.

What the owner is or is not told during recovery is a product decision this
quality target has no basis to assert, so it is left entirely to the FRs that own
recovery.

## NFR-005 — Local-only handling of pet and owner data [#nfr-005]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002) |

### ISO 25010 Characteristic
Security → Confidentiality (with Resistance implications: no network attack
surface is exposed at all)

### Quality Attribute Scenario
- **Source of stimulus:** An observer of the machine's network traffic — the
  privacy-conscious owner auditing the app, or a reviewer verifying the claim.
- **Stimulus:** The owner exercises every functional requirement in this set —
  the four care actions, wake, save and load, offline decay, mood display,
  sickness and terminal progression, local reminders, default-pet
  initialization, and save-file quarantine — with no opt-in granted.
- **Environment:** Normal operation on a machine with all traffic captured at
  the OS network interface, including a run with the network interface disabled
  entirely.
- **Artifact:** The whole application process, its dependencies, its local data
  directory, and the quarantine location.
- **Response:** All function completes using local storage and local
  notifications only; no outbound connection is attempted; the app behaves
  identically with networking disabled.
- **Response measure:** 0 outbound TCP, UDP or DNS attempts attributable to the
  application across a >= 30 minute capture that exercises every functional
  requirement in this set; 100% of those requirements pass with the network
  interface disabled; pet and owner data written only inside the application's
  local data directory and its quarantine location; any future opt-in telemetry
  path is off by default and inert until explicitly enabled by the owner.

### Rationale
Offline-only operation is both a stated constraint and the basis of the privacy
promise made to the owner. Stating it as a measurable network-capture assertion
turns it into a regression test rather than a policy statement, and the
network-disabled run proves no core function has quietly acquired a dependency
on connectivity. The scope is bound to "every functional requirement in this
set" rather than a fixed range so that a later-added FR cannot fall outside the
capture session by omission — which is exactly how FR-011 and FR-012 escaped the
previous wording.

## NFR-006 — Single-codebase support for all three desktop targets [#nfr-006]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| Verification | test |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |

### ISO 25010 Characteristic
Flexibility → Adaptability and Installability

### Quality Attribute Scenario
- **Source of stimulus:** The owner installing and running the application on
  their platform of choice; and the developer adding support for a target not
  yet shipped.
- **Stimulus:** The same source tree is built, packaged and run on Windows, on
  macOS, and on Linux.
- **Environment:** Current supported OS versions of each of the three targets;
  the v1 ship order is deliberately not fixed by this requirement.
- **Artifact:** The whole codebase, and in particular the platform-touching
  seams — local data directory paths; the quarantine location and the
  byte-identical file move into it (FR-012), whose move semantics, path
  conventions and file-locking behaviour all differ per platform; wall-clock and
  timer access, including the elapsed-interval derivation across an application
  close that FR-011 and FR-002 depend on; native notifications; accessibility
  integration; and rendering.
- **Response:** The full care loop, persistence, offline decay, wake,
  save-file quarantine and mood display behave identically on each target; every
  platform difference is resolved inside a single named platform-adapter layer,
  so adding or enabling a target touches only that layer.
- **Response measure:** The acceptance suite for every functional requirement in
  this set passes unmodified on all three platforms in CI — the quarantine move
  and the across-close interval derivation included, not excepted; 0 platform
  conditionals outside the platform-adapter layer; 0 recorded design decisions
  that foreclose any of the three targets.

### Rationale
The constraint is that no decision may foreclose a target, not that all three
ship at once. Confining platform differences to one adapter layer is what makes
that constraint checkable and keeps a later target cheap, while leaving the v1
ship order (Q-3) genuinely open rather than settled by accident of
implementation.

The suite is bound to the whole functional set because the two behaviours a
fixed range most easily drops are the two that diverge most: deriving a
wall-clock interval across an application close exercises clock and timer access
per platform, and moving a file byte-identically into quarantine exercises move
semantics, path conventions and locking. Both are named in the Artifact list
above, so omitting them from the suite would leave the seams this requirement
identifies untested.

## NFR-007 — Local diagnostic logging of decay and lifecycle events [#nfr-007]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | high |
| Verification | test |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010) |

### ISO 25010 Characteristic
Extension: Observability (supporting Maintainability → Analysability)

### Quality Attribute Scenario
- **Source of stimulus:** The application itself, on behalf of an owner or
  developer investigating a pet state that looks wrong.
- **Stimulus:** A decay computation runs, or a lifecycle transition occurs —
  launch, save, load, save-file quarantine, mood change, onset of sickness,
  terminal transition, sleep and wake.
- **Environment:** Normal operation at the default log level, with no network
  available.
- **Artifact:** The local diagnostic log on disk.
- **Response:** Exactly one structured record is appended per event, carrying
  the timestamp, event type, elapsed interval where applicable, the pre-event
  and post-event stat values, and the computed deltas — written locally and
  never transmitted.
- **Response measure:** 100% of decay computations and lifecycle transitions
  produce exactly one such record; replaying >= 100 recorded decay events
  through the reference model reproduces each logged post-state with 0
  mismatches; total log size stays under a fixed rotation cap indefinitely; 0
  outbound transmissions of log content.

### Rationale
Offline decay is the one behavior the owner never watches happen, so when the
pet's condition on relaunch surprises them there is otherwise no evidence to
reason from. A record that permits independent recomputation turns "the decay
feels wrong" into a decidable question, and keeps the balance-tuning work (Q-1)
grounded in observed data rather than impression.

## NFR-008 — Offline-decay computation cost does not scale with the length of the absence [#nfr-008]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| Verification | test |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002) |

### ISO 25010 Characteristic
Performance Efficiency → Time behavior

### Quality Attribute Scenario
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

### Rationale
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

## NFR-009 — Offline-decay computation time on the launch path [#nfr-009]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | low |
| Verification | test |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002) |

### ISO 25010 Characteristic
Performance Efficiency → Time behavior

### Quality Attribute Scenario
- **Source of stimulus:** The owner, relaunching the application after being
  away.
- **Stimulus:** Launch occurs after a 30-day offline interval — the worst case
  that NFR-001's test matrix already exercises — requiring the full elapsed
  decay to be computed and applied before the pet can be shown.
- **Environment:** Cold start on the project's designated reference machine
  (specification pending Q-5) under normal desktop use, with a valid committed
  save file present and no other application load contrived.
- **Artifact:** The offline-decay computation on the launch path, between the
  completion of the committed-save read and the first render of the pet.
- **Response:** The owner sees the post-decay pet without a perceptible stall;
  the decay stage consumes a minor share of the launch rather than dominating
  it.
- **Response measure:** For a 30-day elapsed interval, the computation completes
  in <= 250 ms at p95 and <= 500 ms at maximum across 20 cold-start runs on the
  designated reference machine. The measure is not evaluable until Q-5 records
  that machine's specification; a measurement taken against an unrecorded
  baseline is unassessed, not passing.

### Rationale
Elsewhere the set treats every interaction as instantaneous, but that is an
assertion rather than a measurement, and this one path contradicts it: FR-002
places an interval-proportional computation directly in front of the only moment
the owner meets the product. Bounding the stage at 250 ms keeps the decay work a
minor share of a launch budget rather than its dominant term.

The figure inherits NFR-002's and CON-001's dependency on the unfixed reference
machine (Q-5), which is why confidence is low — until Q-5 is answered, "250 ms"
names a duration with no hardware to hold it against, and the fit criterion says
so rather than pretending otherwise. The verification method is fully defined and
the single missing parameter is tracked, so the requirement is verifiable in the
INCOSE sense even though it cannot be executed today.

Priority is `should` rather than `must` because the property that separates a
correct implementation from a broken one is the scaling behaviour in NFR-008,
which is a `must` and is testable now. This absolute bound is the refinement on
top of it: worth holding, but not a gate that can be enforced before a product
decision lands.

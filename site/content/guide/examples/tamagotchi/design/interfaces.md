<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/design/interfaces/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Interfaces

The 31 interfaces from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## IF-001 — Balance Parameter Read [#if-001]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-002 |
| Traces from | [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-008](/guide/examples/tamagotchi/requirements/non-functional/#nfr-008) |

The contract through which every component that needs a balance or tuning parameter —
stat bounds and starting values, the decay curve, neglect thresholds and durations,
mood bands, care increments and the sleep duration — reads it from memory, rather than
holding it and rather than touching the configuration source it was loaded from.

### Operations
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

### Interaction
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

### Error Modes
- A read arrives before the parameter set has been loaded for this session — reported as its
  own outcome rather than triggering a load, because a read that can load is a read that can
  touch a file.
- A requested parameter is absent from the loaded set — the caller receives no value rather
  than a silent default, because a silently defaulted decay rate or neglect threshold passes
  every functional test while producing the wrong pet.
- A parameter is present but out of range — a starting value outside the stat bounds, a
  non-positive duration, a band mapping to no mood expression — rejected rather than clamped.

### Rationale
Satisfies the identical capability declared by CMP-001, CMP-004, CMP-005, CMP-006, CMP-007,
CMP-008 and CMP-014. Every numeric value behind these operations is unfixed pending Q-1
(still_open), which is exactly why the indirection exists — but the operation set follows
from the requirements that name the parameters (requirements A-2 bounds, NFR-001's curve, FR-008's
thresholds and durations, FR-007's bands, FR-003/4/5's increments, FR-011's sleep duration)
and not from Q-1's answer. Confidence is medium because the grouping is inferred, not
because the values are open. Source-level failures — a missing or unparseable configuration
file — belong to IF-026 and are deliberately absent here.

## IF-002 — Live Pet State Access [#if-002]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-003 |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

The contract through which the session's live pet state is read and replaced, and the single
point at which a replacement triggers a durable commit.

### Operations
- **current** — Return the application's live pet state.
- **replace** — Install a supplied pet state as the live one; this replacement is the trigger
  FR-001's persist-on-stat-change obligation hangs off.

### Interaction
Both synchronous. `current` obviously so. `replace` is the closer call: it carries a durable
commit behind it, so the caller blocks on a file write. Accepting the replacement and
committing behind the caller's back would take the store's latency off the care-action path
and off every evaluation, at the cost that a care action could report success for a change
that never reaches disk — and NFR-004's discriminating clause exists precisely to catch a
launch that fails to restore a change the owner believes they made. Kept synchronous;
if the write latency later shows up against the responsiveness of the care loop, the
alternative is deferred commit plus an explicit not-yet-durable state on the contract, not
a silent one.

Separate from IF-029, the session-end commit, even though the same component provides both:
IF-029's only consumer is the lifecycle sequencer, which never replaces a state on the close
path, and the four consumers here never close the session. See IF-029.

### Error Modes
- Replacement rejected because the supplied pet state violates a pet-state invariant — a stat
  outside its bounds, or a Sleeping pet with no sleep-entry timestamp — leaving the live
  state unchanged.
- The durable commit the replacement triggers fails — the caller is told the change is not
  durable rather than the failure being swallowed.
- A replacement that would discard or overwrite the accumulated state of a pet at the terminal
  end-of-life status — refused outright while BR-002's prohibition stands.

### Rationale
Satisfies the live-state capability declared by CMP-008 (care actions), CMP-009 (evaluation),
CMP-011 (launch) and CMP-016 (the owner's view). Routing every replacement through one
contract is what makes BR-002's "inspect every code path that writes, clears or replaces
persisted pet state" a finite inspection, and what stops a caller changing a stat without
persisting it (FR-001).

## IF-003 — Decay Computation [#if-003]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-004 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-008](/guide/examples/tamagotchi/requirements/non-functional/#nfr-008), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |

The independently invocable computation that maps a starting pet state and a signed elapsed
interval to the decayed pet state, in one bounded step.

### Operations
- **decay** — Return the pet state produced by applying the configured decay curve to a
  supplied starting pet state over a supplied signed elapsed interval, in one bounded step
  rather than by walking the interval; an interval at or below zero is treated as zero
  elapsed time, so no stat value increases.

### Interaction
Synchronous. FR-002 forbids the pet being displayed before decay has been applied, so the
launch path cannot proceed without the result.

One operation, deliberately. Requirements A-17 and NFR-008 require this computation to be reachable as a
single unit callable 1,000 times in a loop against an in-memory starting state, with no save
file read and no application launch. Every parameter it needs arrives as an argument or from
IF-001, and IF-001 is now a pure memory read whose source-loading half lives in IF-026 — so
the whole transitive read set of this operation touches no file. It reads no clock either.
That is what makes NFR-001's non-positive-interval matrix drivable directly against it, and
it is why FR-002's clamp lives here rather than in the caller: the clamp is part of what the
matrix tests.

### Error Modes
- The balance parameter set has not been loaded for this session — the curve is undefined and
  no decayed state is produced; this operation does not load it.
- The supplied starting pet state carries a stat outside its configured bounds — rejected
  rather than extrapolated from.
- The supplied elapsed interval exceeds the representable range — rejected rather than
  silently truncated.

### Rationale
Satisfies CMP-009's declared need to compute a decayed pet state, which FR-002 forces onto
the launch path ahead of first render and NFR-008 forbids living inside that sequence.

## IF-004 — Health Progression Advance [#if-004]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | low |
| Provider | CMP-005 |
| Traces from | [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

The contract through which the pet's health status is advanced along the Healthy to Sick to
terminal progression under sustained unremedied neglect, and the only writer of that status.

### Operations
- **advance** — Return the pet's health status advanced one step where at least one pet stat
  has remained below its neglect threshold continuously for the applicable sustained-neglect
  duration, measured from that stat's below-threshold-since origin against the current
  wall-clock reading, and unchanged otherwise; where the interval since an origin computes as
  non-positive, that origin is re-based to the current reading and no advancement is derived
  from it.

### Interaction
Synchronous. An evaluation installs one re-derived pet state, and the health status is part of
it; the caller cannot install a state whose status it has not yet been told.

One operation. The contract exposes no way to read the per-stat below-threshold clock, because
whether that clock exists as a persisted field or is reconstructed at each evaluation is
undecided — see below.

**Which of requirements A-6's two rules this contract applies.** IF-018 hands out a signed interval and
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

### Error Modes
- The interval since an origin computes as non-positive — not a failure: the origin is
  re-based under requirements A-6's deadline rule, bounding the deferral at one further duration.
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

### Rationale
Satisfies CMP-009's declared need to advance health status. BR-001's "0 terminal transitions
arise from an application fault" is what makes this a contract with exactly one provider and
no presence on the recovery paths: FR-010 and FR-012 reach a default pet without ever calling
it.

**Confidence is low.** FR-008 requires a per-stat below-threshold clock continuous across an
application close, and the glossary's Pet state entry — the single maintained enumeration of
what is persisted (requirements A-22) — carries no such field. Reconstructing that clock from the decay
curve at each evaluation and persisting it as a new field are both open; the choice is tracked
under Q-10 (still_open) by requirements A-24 and is deferred by this stage. The operation's shape and the
deadline-rule choice above survive either answer, but what `advance` can be given, and whether
requirements A-22's enumeration must grow, does not.

## IF-005 — Sleep Entry [#if-005]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-006 |
| Traces from | [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |

The contract through which the sleep care action puts an Awake pet into the Sleeping state and
stamps the sleep-entry timestamp the wake deadline is later measured from.

### Operations
- **enter_sleep** — Transition an Awake pet to the Sleeping state and record its sleep-entry
  timestamp from the current wall-clock reading; a pet already Sleeping is returned unchanged,
  its existing timestamp preserved.

### Interaction
Synchronous. The care action installs the returned pet state as the live one and cannot
proceed without it.

One operation, and deliberately separate from IF-006's wake resolution even though the same
component provides both: the care interaction handler enters sleep and never resolves a wake,
and the evaluator resolves wakes and never enters sleep. Requirements A-8 fixes that asymmetry — the pet
leaves Sleeping on elapsed duration, not by an owner action — so the two consumer sets are
disjoint by requirement, not by accident.

### Error Modes
- Host clock reading unavailable — no sleep-entry timestamp can be recorded, so the transition
  is refused rather than made with an absent origin.
- The pet is already Sleeping — not a failure: idempotent, and the existing timestamp is
  preserved, because re-stamping on every repeat would extend the sleep duration indefinitely.
- The diagnostic record for the transition cannot be written — the transition still stands.

### Rationale
Satisfies CMP-008's declared need to put the pet into the Sleeping state, which FR-006 requires
and FR-006's fit criterion requires to be idempotent. Confidence is medium: FR-006 sits in the
inherited review queue on Q-8 (still_open — whether the Sleeping state is rendered to the
owner), but Q-8 bears on the presentation surface rather than on this transition, since the
Awake/Sleeping field is already part of pet state and needs no new contract to be displayed.

## IF-006 — Wake Deadline Resolution [#if-006]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-006 |
| Traces from | [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |

The contract through which a pet-state evaluation tests a Sleeping pet's wake deadline under
FR-011's re-basing rule, which differs from the clamp the same evaluation applies to decay.

### Operations
- **resolve_wake** — Test a Sleeping pet's elapsed interval since its sleep-entry timestamp
  against the sleep duration and return the pet Awake where the duration has been reached;
  where that interval computes as non-positive, re-base the sleep-entry timestamp to the
  current reading and leave the pet Sleeping.

### Interaction
Synchronous. FR-011's AC-3 requires the wake test at launch before the pet is displayed, so
the evaluation blocks on it.

This contract is one of the two places requirements A-6's deadline rule lives — the other is IF-004's
neglect clock. IF-018 hands out a signed interval and applies neither rule; IF-003 clamps it
as a quantity; this operation and IF-004's re-base the origin as a deadline. The discriminator
has to be named wherever the interval is consumed, and these are the namings.

### Error Modes
- Host clock reading unavailable — the deadline cannot be tested and the pet is left Sleeping
  with its timestamp untouched.
- A Sleeping pet carries no sleep-entry timestamp — the origin is re-based to the current
  reading, bounding the wake at one sleep duration rather than leaving the pet Sleeping
  without bound.
- The balance parameter set has not been loaded — the sleep duration is unknown and no wake is
  resolved.
- The interval computes as non-positive because the clock moved backward — not a failure: the
  origin is re-based, which is exactly what FR-011's backward-clock trials measure.

### Rationale
Satisfies CMP-009's declared need to resolve a sleeping pet's wake deadline. Separate from
IF-005 because the consumer sets are disjoint: the care handler enters sleep and never resolves
a wake, and per requirements A-8 no owner action wakes the pet. Confidence is medium — FR-011 is in the
inherited review queue and its own confidence is low, but the residual uncertainty is the sleep
duration's value (Q-1) and the evaluation cadence (Q-10), neither of which changes this
operation's shape.

## IF-007 — Mood Expression Selection [#if-007]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-007 |
| Traces from | [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |

The contract that maps a pet's current stat values to the mood expression displayed for it, by
the band containing its lowest stat, and reports whether that expression has changed from the
one the pet's prior stat values selected.

### Operations
- **select** — Return the mood expression mapped to the mood-threshold band containing the
  pet's lowest stat value, together with the expression the supplied prior stat values select
  and whether the two differ.

### Interaction
Synchronous. Both consumers install the selected expression as part of the pet state they hand
on, so neither can proceed without it.

One operation, which now takes the prior stat values as well as the current ones. That
addition is not decoration: NFR-007 enumerates a mood change as a lifecycle transition
requiring exactly one structured record carrying pre-state and post-state, and CMP-007 is the
only place the mood changes, so it is the component that must emit that record. The previous
shape gave `select` only the current values, which left it able to compute an expression but
unable to tell whether that expression was a change, or to name what it changed from. The
contract could not serve the capability its own provider was assigned. Prior values are the
same shape IF-015's `raise_for_stat_change` already takes, for the same reason — both
consumers hold the pre-change and post-change pet states at the moment they call.

The alternative was to let this component remember the last expression it selected. That was
rejected: it would make a pure mapping stateful, make the record depend on call ordering
rather than on the pet, and give a wrong answer the first time it is called after a launch
restores a pet whose mood it never selected.

### Error Modes
- Mood-threshold bands unavailable or incomplete — no band can be matched.
- The configured bands leave a gap the lowest stat value falls into — reported rather than
  resolved to the nearest band, because a silent fallback displays a mood FR-007 does not
  define.
- The pet carries no stat values — there is no minimum to reduce over.
- No prior stat values supplied — an expression is selected but marked as having no comparable
  predecessor, so the session's first selection records no mood change.
- The prior values are not the ones the pet actually held — a change is recorded that did not
  happen, or a real one is missed; undetectable here, which is why the caller that caused the
  change supplies them.

### Rationale
Satisfies the identical capability declared by CMP-008 (a care action can move the lowest stat
across a band boundary) and CMP-009 (so can decay, which FR-007's AC-3 names). One contract for
both, because both consume the same single capability.

## IF-008 — Care Action Application [#if-008]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-008 |
| Traces from | [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003) |

The contract through which the owner's selection of one of the four care-loop interactions is
applied to the current pet.

### Operations
- **feed** — Raise the hunger stat by the configured feed increment, capped at maximum, and
  install the result as the live pet state.
- **play** — Raise the happiness stat by the configured play increment, capped at maximum, and
  install the result.
- **clean** — Raise the hygiene stat by the configured clean increment, capped at maximum, and
  install the result.
- **put_to_sleep** — Put the pet into the Sleeping state and install the result;
  already-Sleeping pets are left unchanged.

### Interaction
All four synchronous. NFR-003 requires the state change a care action causes to be announced
as text through the platform accessibility API, and an announcement can only follow a result
the caller has been given. The announcement itself happens through IF-027, from the surface
that called this contract.

Four operations, not one action-typed operation. The care loop is a fixed set of exactly four
(requirements A-8 forbids a fifth), each named by its own requirement with its own configured increment, and
NFR-003's scripted screen-reader walkthrough exercises them one by one. Naming them separately
is what lets FR-003, FR-004, FR-005 and FR-006 trace to distinct operations rather than to one
switch statement.

### Error Modes
- The targeted stat is already at maximum — the action completes with the stat unchanged, which
  each of FR-003/4/5 requires explicitly; the caller must not announce a change that did not
  occur.
- The live pet state cannot be replaced, or its commit fails — the action is reported as not
  applied.
- The balance parameter set has not been loaded — the increment is unknown and no action can be
  applied.
- Sleep selected for an already-Sleeping pet — accepted and idempotent.

### Rationale
Satisfies CMP-016's declared need to apply an owner-selected care-loop action, keeping the four
interactions as domain behaviour rather than as logic inside the presentation surface.

## IF-009 — Pet-State Evaluation [#if-009]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-009 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |

The contract through which the pet's state is re-derived from the current wall-clock reading —
decay applied, health status advanced, wake deadline tested, mood re-selected — and installed
as the live pet state.

### Operations
- **evaluate** — Perform one pet-state evaluation: read the current wall-clock reading, apply
  elapsed decay from the last-saved timestamp, advance health status for sustained neglect,
  resolve any wake deadline, re-select the mood expression, raise any warranted care reminders,
  and install the re-derived pet state as the live one.

### Interaction
Synchronous. The launch sequence must not display the pet until the evaluation has completed
(FR-002, FR-011 AC-3), and NFR-009 measures a window that closes at first render — a window
that only exists if the evaluation completes before it.

One operation, and the same one for both consumers. A launch evaluation and a cadence
evaluation are the same derivation over a different elapsed interval; splitting them would put
two subtly different derivations in the codebase, which is precisely what FR-008's continuity
across an application close forbids. What differs between the two callers is what happens
*after*: the launch path goes on to first display (IF-017), the cadence does not, and the
evaluation itself asks for a redraw (IF-030) either way.

### Error Modes
- Host clock reading unavailable — no evaluation is performed and the live state is left as it
  stands.
- A stage of the derivation fails — the evaluation is abandoned without installing a partially
  derived pet state.
- The re-derived state cannot be installed or its commit fails — reported as not applied.
- The elapsed interval computes as non-positive — not a failure: decay contributes zero and
  both deadline consumers re-base their origins.
- The redraw the evaluation asks for fails — the evaluation still stands; the state is already
  installed and committed, and the owner sees a stale view until the next redraw succeeds.

### Rationale
Satisfies the identical capability declared by CMP-010 (the running cadence) and CMP-011 (the
launch path). This is the one place the two non-positive-interval rules of requirements A-6 meet: the
evaluation passes the signed interval to IF-003, which clamps it, and to IF-006 and IF-004,
which re-base against it, and applies neither rule itself.

## IF-010 — Recurring Evaluation Cadence [#if-010]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | low |
| Provider | CMP-010 |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002) |

The contract through which the lifecycle sequencer starts the running application's own cadence
of pet-state evaluations once a pet has been established, and stops it again before the session
ends.

### Operations
- **start** — Begin driving evaluations on the application's own cadence and return once the
  cadence is established, not once an evaluation has occurred.
- **stop** — Stop driving evaluations and return once the cadence is quiescent and no
  evaluation is still in flight.

### Interaction
Both synchronous, and `start` was wrong before. The concern the previous asynchronous
declaration was reaching for is real — first render must not wait on an evaluation coming due —
but that concern is about what `start` waits *for*, not about whether it returns a result.
Establishing a cadence is fast and local; the evaluations it goes on to drive are what happen
later. A synchronous `start` that returns on establishment meets the launch-latency concern
exactly as well, and it is the only shape consistent with the first error mode below, which
requires the caller to be told when the platform timer contract (IF-031) refuses to establish
a tick. An asynchronous `start` has nobody to tell.

`stop` is synchronous for a stronger reason: its whole purpose is ordering. The close path is
stop, then commit (IF-029), then exit. If `stop` returned before the cadence was quiescent, an
in-flight evaluation could install a re-derived state after the final commit had read the live
one — FR-001's close trigger would then persist a state the owner never saw, and the next
launch would re-derive decay from a timestamp that was already stale when it was written.

**What this contract holds, and what it now delegates.** The recurring tick itself is not held
here. NFR-006 names timer access in the same clause as wall-clock access, so the tick is
obtained from the platform-adapter layer through IF-031, and what stays on this side is the
cadence: its period, its coalescing rule, and when it starts and stops. That is what finally
gives the first error mode below a structural source — this contract can report an
unestablishable timer facility because its provider asks a contract that can refuse, which was
not true of it before. Quiescence gains the same shape: it has two halves now, IF-031's
`cancel` confirming that no further tick will be delivered and this contract waiting out any
evaluation already in flight, and `stop` returns only once both hold.

### Error Modes
- The platform timer contract refuses to establish a tick (IF-031) — the cadence does not
  start, the refusal is passed on, and the pet advances only at launch.
- An evaluation fails on one tick — the cadence continues rather than terminating.
- Evaluations overrun their period — ticks are coalesced, not queued, so no backlog can spend
  the idle budget NFR-002 caps.
- The platform delivers no tick for a long stretch (sleep, throttling) — missed ticks are not
  back-filled; one evaluation then derives from the whole elapsed interval, the same path
  FR-002's offline decay takes.
- Started more than once — idempotent; a second cadence doubles both the rate and the idle cost.
- Stop asked for mid-derivation — stop waits rather than abandoning the evaluation partway.
- Stop cannot confirm quiescence within a bounded wait — from either half, an evaluation still
  in flight or an unconfirmed cancel — reported, and the caller decides whether to commit and
  exit anyway.
- Stopped without having been started, or stopped twice — idempotent, and not an error.

### Rationale
Satisfies CMP-011's declared need to drive recurring evaluation. `stop` exists because CMP-011
now owns the application-close path symmetrically with launch, which is what closes FR-001's
second named trigger — the owner closing the application. The platform tick this cadence runs
on is consumed from IF-031 rather than held by the provider, which is what keeps the sixth of
NFR-006's enumerated seams inside the adapter layer with the other five.

**Confidence is low**: Q-10 (still_open) asks exactly how often the running application
re-evaluates pet state and what bounds that interval, and NFR-002 constrains it from the other
side. Whether `start` carries a period at all, and whether that period is fixed, adaptive or
event-driven, follows from Q-10's answer. `stop`'s shape does not depend on it.

## IF-011 — Default Pet Construction [#if-011]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-001 |
| Traces from | [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001) |

The contract that produces a default pet — the state both recovery paths initialize when no
committed state is available.

### Operations
- **default_pet** — Return a default pet: health status Healthy, in the Awake state, every pet
  stat at its configuration-defined starting value, no sleep-entry timestamp, and no accumulated
  care or lifecycle history.

### Interaction
Synchronous. The launch branch that calls it cannot continue without the pet it returns.

Exactly one operation, because the capability is exactly one thing. The glossary fixes what a
default pet is; there is no variant to parameterise and no second way to ask for it.

### Error Modes
- The balance parameter set has not been loaded — no starting values exist and no default pet
  can be constructed.
- A configured starting value falls outside its stat's bounds — rejected rather than clamped.

### Rationale
Satisfies CMP-011's declared need to produce a default pet, which FR-010 requires when no save
file is present and FR-012 requires after a failing file has been quarantined. Healthy is not a
default chosen for convenience: BR-001 requires 0 terminal transitions to arise from an
application fault, and this contract's inability to return anything but Healthy is what makes
the recovery paths structurally incapable of producing a terminal pet. The launch sequence
orders IF-026's load before this call, which is why an unloaded parameter set is a failure mode
here rather than a load trigger.

## IF-012 — Committed Save Retrieval [#if-012]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-012 |
| Traces from | [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |

The contract through which the launch path asks for the committed pet state and is told which
of the two recovery cases applies where none is returned.

### Operations
- **retrieve** — Return the committed pet state held in the save file, or report which recovery
  case applies: no save file present, or a file present that failed integrity validation and has
  already been moved byte-identically to the quarantine location.

### Interaction
Synchronous. NFR-009 measures from the completion of the committed-save read to first render, so
that completion has to be an observable boundary the launch sequence waits on.

One operation with a three-way outcome, rather than a `read` plus a separate `exists`. NFR-004's
discriminating clause rules out any design in which a failed read falls through to the default-pet
path without first establishing that no committed state survives — a two-call shape leaves a
window between the check and the read where exactly that can happen.

### Error Modes
- No save file present — its own outcome, with no quarantine artifact created (FR-010 AC-2).
- The file fails integrity validation — its own outcome, reported only once the file has been
  moved byte-identically to quarantine, so the default pet's commit cannot overwrite the evidence.
- The quarantine move fails — retrieval reports failure rather than a recovery case.
- The file is present but unreachable — reported as an unreadable-state failure, never as absence.

### Rationale
Satisfies CMP-011's declared need to retrieve the committed pet state. FR-010 and FR-012 own
different halves of the recovery space and this operation's outcome is what tells them apart —
which is why the two cases are distinct outcomes rather than one no-state answer.

Separate from IF-013 (commit) even though CMP-012 provides both: see IF-013's Interaction note.

## IF-013 — Pet State Commit [#if-013]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-012 |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

The contract through which the current pet state is committed to the save file as the system's
single system of record, atomically and dated with a last-saved timestamp.

### Operations
- **commit** — Write the supplied pet state to the save file as one committed state, dated with
  a last-saved timestamp taken from the host clock, atomically replacing the single retained
  generation.

### Interaction
Synchronous. FR-001 fires on every stat change, and NFR-004's discriminating clause requires the
committed state to be the one restored — the caller has to know whether the write landed.

**Separate from IF-012, deliberately.** CMP-012 provides both, but the consumer sets are disjoint:
the Pet Session (CMP-003) commits and never retrieves, and the lifecycle sequencer (CMP-011)
retrieves and never commits. Folding them into one store contract would make the launch path
depend on a commit operation it never calls, and the session depend on a retrieval that carries
FR-012's quarantine branch — a failure path it has no business handling. The two are also
lifecycle-disjoint in time: retrieval happens once, before the pet exists; commit happens
repeatedly, for the rest of the session. Segregation is the honest verdict here, not a preference.

Note that the close-path commit does not reach this contract directly either: IF-029 is asked of
the session (CMP-003), which is what routes it back through here, so BR-002's inspection of every
state-writing path still converges on one custodian.

### Error Modes
- The atomic replace fails — the previously committed state remains intact, and the caller is
  told the change is not durable.
- The local data directory is unavailable or not writable — nothing is committed.
- Host clock reading unavailable — the commit is refused rather than dated with a guess, because
  a committed state with no last-saved timestamp leaves FR-002 no origin.
- The pet state cannot be encoded in full — refused rather than partially written.
- The write would discard a terminal pet's accumulated state — refused (BR-002).

### Rationale
Satisfies CMP-003's declared need to commit the current pet state. Atomicity is a property of
this contract rather than of its caller because no caller-side ordering can supply it (NFR-004),
and one generation is retained rather than two (Q-9, resolved).

## IF-014 — Save Integrity Validation [#if-014]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-013 |
| Traces from | [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004) |

The contract that establishes whether a save file's contents are a committed state, separately
from any unit that hands back a decoded pet state.

### Operations
- **validate** — Establish whether the supplied save-file contents are a committed state —
  complete and internally consistent as written — without putting them into service as a pet
  state.

### Interaction
Synchronous. The store's retrieval branches on the answer.

One operation, and the separation from decoding is the point: FR-012 splits the load path in two,
and integrity validation cannot be folded into the same unit that hands back a usable pet state,
or the failing branch would already have consumed the contents it must preserve untouched.

### Error Modes
- Contents truncated, unparseable, or failing the consistency check — reported as not a committed
  state; the ordinary result FR-012 keys on, not an exception.
- An unrecognised format version — treated as failing validation, so the file is quarantined and
  preserved rather than trusted or discarded.
- Validation cannot be completed at all — reported as inconclusive, never as a pass.

### Rationale
Satisfies CMP-012's declared need to establish whether a save file's contents are a committed
state. Confidence is medium: the glossary makes the mechanism implementation-defined and
dependent on the storage format, and while Q-4 is resolved (Tauri/Rust, a JSON file written by
atomic rename), the concrete check — structural decode alone, or a recorded checksum — is not
fixed by any requirement, and which one is chosen changes what inconclusive can mean.

## IF-015 — Care Reminder Raising [#if-015]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-014 |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005) |

The contract through which a pet-state evaluation reports the stat movement it caused, so that
any neglect-threshold crossing can be turned into a local care reminder.

### Operations
- **raise_for_stat_change** — Present a local care reminder for each pet stat that crossed its
  neglect threshold between the supplied pre-change and post-change stat values, where the owner
  has enabled reminders.

### Interaction
Asynchronous, and the choice is close enough to record. The evaluation hands over the crossing
and continues; it does not block on the host notification service, whose latency is outside the
application's control and would otherwise land inside NFR-009's launch window. The cost is that
the evaluation cannot report a reminder failure to anyone — a dropped reminder is invisible to
the path that caused it. Making it synchronous would surface that, at the price of coupling
every launch's timing to the OS notification service. FR-009 is a *should* and reminders are
advisory, which is what tips it: a missed reminder must never delay or fail a pet-state
evaluation.

**Separate from IF-028, the preference contract, deliberately.** CMP-014 provides both, and the
consumer sets are disjoint: the evaluator raises reminders and never touches the setting, and
the owner-facing surface reads and changes the setting and never raises a reminder. They also
differ in interaction — this one is fire-and-forget, and a preference change must be confirmed
durable before the owner is shown a new toggle position. Folding them together would give the
evaluator a setter it has no business holding, which is close to how FR-009's enabled arm came
to be unreachable in the first place.

### Error Modes
- Reminders disabled by the owner — nothing presented, no notification service contacted at all.
- The notification service is unavailable or permission denied — the reminder is dropped rather
  than retried or queued, since a queued backlog arrives as a burst at the next launch.
- The reminder preference cannot be read — treated as disabled here, so an unreadable preference
  can never cause an unwanted notification; the surface learns the difference through IF-028.
- Neglect thresholds unavailable — no crossing detected, no reminder raised.
- The same crossing reported twice by consecutive evaluations — reminded once.

### Rationale
Satisfies CMP-009's declared need to raise warranted care reminders; decay applied during an
evaluation is the only thing that lowers a stat across its threshold. Confidence is medium:
FR-009 is a *should* whose de-duplication window — how long a stat may sit below its threshold
before it is worth reminding again — is fixed by no requirement, and the last error mode above
states the obligation without being able to state its period.

## IF-016 — Diagnostic Event Recording [#if-016]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-015 |
| Traces from | [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005) |

The contract through which every decay computation and every pet lifecycle transition emits its
one structured local record.

### Operations
- **record_lifecycle_transition** — Record exactly one structured local record for a pet
  lifecycle transition — launch, close, save, load, save-file quarantine, mood change, onset of
  sickness, terminal transition, sleep or wake — carrying its timestamp, event type, pre-state
  and post-state.
- **record_decay_computation** — Record exactly one structured local record for a decay
  computation, carrying its timestamp, the elapsed interval, pre-state, post-state and computed
  deltas, sufficient to recompute the resulting state from the record alone.

### Interaction
Both asynchronous. No caller may have its transition delayed or failed by a log write; the record
is a consequence of the transition, never a precondition. The cost is that a caller cannot know
its record landed, which is why record dropped is stated as a failure mode of this contract
rather than of its consumers.

Two operations rather than one, because the two record shapes differ in required content: a decay
record must carry the elapsed interval and the computed deltas, which are what NFR-007's replay
check drives through the reference decay model, and no lifecycle transition has either. One
operation with everything optional would make "sufficient to independently recompute the resulting
state" unenforceable at the contract.

### Error Modes
The cap-reached path is the one that changed, and it is worth being explicit about why. NFR-007
asks for two things that pull against each other: exactly one record per transition, and total
log size under a fixed cap indefinitely. With only an append primitive underneath, the cap could
be honoured only by dropping every record from the moment it was reached — permanent silent
record loss, and a log that stops describing the pet precisely when it has been running longest.
With IF-021's `file_size` and `roll_over`, the cap is honoured by rolling instead, and a record
is dropped only when the roll itself fails.

- The rotation cap is reached — the log is rolled over and the oldest retained copy discarded
  before the record is written; records continue past the cap.
- The roll-over itself fails at the cap — only then is the record dropped, and the caller is
  still neither blocked nor failed.
- The log file cannot be written for any other reason — the record is dropped, without blocking
  or failing the caller.
- The supplied pre-state or post-state is incomplete — the record is written marked unreplayable
  rather than silently short.
- The same transition is submitted twice — recorded once; a duplicate breaks NFR-007's
  exactly-one count as surely as a missing record.

### Rationale
Satisfies the identical capability declared by CMP-005 (sickness onset, terminal transition),
CMP-006 (sleep, wake), CMP-007 (mood change), CMP-009 (decay computations), CMP-011 (launch and
close) and CMP-012 (save, load, quarantine). One contract for all six, because "exactly one
structured record" is a claim about a single owned emit point — scattering the recording across
callers is precisely what NFR-007's phrasing rules out.

## IF-017 — First Pet Display [#if-017]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-016 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |

The contract through which the pet is displayed for the first time in a session, completing at
the first render that closes NFR-009's measurement window.

### Operations
- **present_initial** — Display the pet for the first time in this session from the live pet
  state, returning when the first render has completed.

### Interaction
Synchronous, and that is the whole reason this contract exists apart from IF-030. NFR-009
defines its measurement window as ending at first render, which is only expressible if first
render is an event the launch sequence causes and can observe completing. It happens once per
session; its ordering after decay is FR-002's requirement rather than a preference; and a first
render that fails fails the launch.

**This contract used to carry the recurring redraw as well, and should not have.** The previous
round bundled `present_initial` and `refresh` because CMP-009 and CMP-011 had declared the same
capability string, and the exactly-once rule left no way to split them from the interface layer.
That was recorded as a finding rather than resolved, and the component set has since split the
capability in two. The halves are now what they always were: disjoint consumers, opposed
interaction modes, and opposed failure semantics — a failed first render must fail the launch,
while a failed redraw must not fail the evaluation that asked for it. IF-030 carries the other
half.

Drawing and announcing are not done here. This contract decides *that* the pet is displayed and
when; the platform work of painting a surface and exposing status text to a native accessibility
stack goes through IF-027, inside the adapter layer NFR-006 names.

### Error Modes
- No rendering surface available — reported, because NFR-009's window has no closing boundary.
- The live pet state cannot be read at first display — nothing is drawn and the launch fails,
  rather than an empty pet being shown.
- A mood expression or health status has no textual equivalent to announce — a failure under
  NFR-003, not a degradation.
- Called more than once in a session — refused; the recurring redraw is IF-030's job.
- The pet is displayed before decay has been applied — undetectable here, and named because
  FR-002 makes the ordering the launch sequence's obligation.

### Rationale
Satisfies CMP-011's declared need to display the pet for the first time in this session.
Confidence is medium: Q-8 (still_open) asks whether the Sleeping state is rendered to the owner.
The operation survives either answer — the Awake/Sleeping field is already part of pet state —
but what the first render is obliged to show and announce does not.

## IF-018 — Host Clock Access [#if-018]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |

The platform-adapter contract that supplies the host's current wall-clock reading and the signed
interval since a recorded timestamp, applying neither non-positive-interval rule itself.

### Operations
- **now** — Return the host's current wall-clock reading.
- **signed_interval_since** — Return the interval between a supplied recorded timestamp and the
  current reading, signed — negative where the clock now reads behind that timestamp — applying
  neither of requirements A-6's non-positive-interval rules, so that each consumer applies the one its own
  requirement names.

### Interaction
Both synchronous. A clock reading has no meaning delivered later than it was asked for.

The deliberate omission is the design content here. Requirements A-6 carries two incompatible rules over the
same reading: FR-002 clamps a non-positive interval to zero because it drives a quantity, and
FR-011 additionally re-bases its origin because it drives a deadline. A contract that exposed one
"elapsed since" would have to pick one and would silently give the other consumer the wrong
answer, so this contract hands back the sign and applies neither.

Every consumer of the signed interval now names its rule at the point of consumption. IF-003
clamps. IF-006 re-bases the sleep-entry origin. IF-004 re-bases the per-stat below-threshold
origin — the third consumer, added this round, and previously the one that read the interval
through its caller and named no rule at all. IF-012 and IF-015 use `now` for timestamping and
read no interval. The correctness of all of it rests on requirements A-7 — that the host exposes backward
movement observably rather than smoothing it away — which this contract cannot itself verify.

### Error Modes
- The host clock is unavailable or uninitialised — no reading returned; every elapsed-interval
  computation is blocked rather than proceeding from a substituted reading.
- The clock reads behind the recorded timestamp — returned as a non-positive signed interval and
  never corrected here.
- The host smooths backward movement, so no non-positive interval is ever observed — requirements A-7 unmet,
  both rules defeated, and undetectable through this contract.
- A recorded timestamp the host clock cannot represent — rejected rather than truncated.

### Rationale
Satisfies the identical capability declared by CMP-005 (FR-008's per-stat below-threshold clock),
CMP-006 (sleep-entry stamping and the wake deadline), CMP-009 (every evaluation), CMP-012 (the
last-saved timestamp on every commit) and CMP-015 (every diagnostic record's timestamp).
Distinct from IF-024, which is the raw OS reading the adapter itself consumes: this contract adds
the signed-interval derivation and is the only clock the rest of the codebase sees, which is what
keeps the platform-specific reading inside the adapter layer NFR-006 names.

## IF-019 — Local Data Directory File Read [#if-019]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract for reading the bytes of a file inside the application's local data
directory, whose concrete path is platform-specific.

### Operations
- **read_file** — Return the bytes of a named file within the application's local data directory,
  or report that no such file is present.

### Interaction
Synchronous. Every caller branches immediately on what came back — a present save file, an absent
one, an unreadable one — and none of them has anything to do until it knows.

**This contract carried the atomic replace last round, and no longer does.** The two capabilities
were merged then because their consumer sets were identical: the pet state store read and replaced
the save file, and the reminder service read and replaced the preference file. The balance
configuration (CMP-002) has since become a third reader, and it never writes — its source is
loaded once at launch and is not the application's to modify. The consumer sets are now a strict
subset rather than a match, so the merge no longer holds: keeping them together would give the
balance configuration a dependency on an atomic-replace operation it has no business being able
to call. The replace lives in IF-025.

The split has a second benefit worth stating, since it is what makes it more than bookkeeping:
the failure modes separate cleanly. Everything here is about not being able to see a file;
everything in IF-025 is about a write not landing. Bundled, the list read as a mixture in which
neither caller could tell which half applied to it.

### Error Modes
- The local data directory cannot be resolved or created — no file can be read at all.
- The named file is not present — its own outcome, not a read error, so FR-010's and FR-012's
  cases stay distinguishable and a first launch without a preference file is ordinary.
- The file is present but unreadable — a read failure, never absence, since absence licenses the
  caller to write over it.
- A torn read while another writer is mid-replace — impossible for files this application writes,
  because IF-025 replaces atomically; possible for a balance configuration edited outside the
  application, where it surfaces as unparseable content.

### Rationale
Satisfies the read capability declared by CMP-002 (the balance configuration source), CMP-012
(the save file) and CMP-014 (the reminder preference). The directory path lives here because it
is one of the platform-divergent seams NFR-006 names.

## IF-020 — Save File Quarantine Move [#if-020]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract that moves a save file byte-identically from the local data
directory to the quarantine location, preserving it as evidence.

### Operations
- **move_to_quarantine** — Move a named file from the local data directory to the quarantine
  location byte-identically, modifying no byte of its contents and leaving no copy at the
  original path.

### Interaction
Synchronous. FR-012 requires the move to have completed before the default pet is initialized, so
the caller must block on it — an asynchronous move races the default pet's first commit for the
same path.

Separate from IF-019 and IF-025 even though the same adapter provides all three, because the
consumer sets are proper subsets rather than matches: only the pet state store quarantines
anything. Quarantine's failure modes are also unlike any ordinary file failure — a failed
quarantine must stop a launch, where a failed preference write must not.

Distinct from IF-021's `roll_over`, which is the other move-a-file-aside operation in the set:
that one discards its oldest copy by design, and this one must never discard anything.

### Error Modes
- The quarantine location cannot be resolved or created — the file cannot be preserved, so the
  caller must not initialize a default pet.
- A file already exists at the destination — a distinct destination is required rather than a
  silent replace over previously preserved evidence.
- The move degrades to copy-then-delete across a filesystem boundary — the copy is verified
  byte-identical before the original is removed, or the operation fails with the original intact.
- Permission denied on the original — left unmodified, and quarantine reported as failed.

### Rationale
Satisfies CMP-012's declared need to move a failing save file to quarantine. FR-012's fit
criterion counts byte-identical files at the quarantine location and zero files deleted or
overwritten in place, and NFR-006 names this move as one of the two most platform-divergent
operations in the product — which is why it sits in the adapter layer and why NFR-006's acceptance
suite runs it unmodified on all three targets rather than excepting it.

## IF-021 — Diagnostic Log File Append and Rotation [#if-021]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract for appending records to the diagnostic log file, measuring its
current size, and rolling it over so the log component can hold total occupancy under the fixed
rotation cap NFR-007 requires.

### Operations
- **append_file** — Append the supplied bytes to a named file within the local data directory,
  creating it if absent, and report the number of bytes actually written.
- **file_size** — Return the current size in bytes of a named file, or report that no such file
  is present.
- **roll_over** — Move a named file aside to a rolled copy, discard the oldest rolled copy beyond
  the number the caller asks to retain, and leave the original path free.

### Interaction
All three synchronous, which is worth distinguishing from IF-016. Recording an event is
asynchronous to its *caller* — no transition waits on a log write — but the log component itself
must learn whether its bytes landed and how many, because it owns the cap and cannot account for
a file whose size it does not know. The asynchrony is absorbed at IF-016, not pushed down here.
`roll_over` in particular must be synchronous: the next append goes to the path it just freed.

**The rotation half is new, and it closes a real gap rather than adding polish.** Last round this
contract carried `append_file` alone, because append was the whole of the log component's
declared file surface. That left NFR-007's "total log size stays under a fixed rotation cap
indefinitely" with no implementer, and left IF-016's cap-reached path with nowhere to go but
permanent silent record loss — a log that stops describing the pet exactly when the pet has the
longest history to describe. The component set now declares the measuring and rolling capability,
so the operations land here.

The split between measuring and rolling is deliberate. The log component owns the cap and the
decision that it has been reached; the adapter owns the platform-specific file operations. Giving
the adapter a single `append_and_roll_if_over(cap)` would move that policy decision across the
layer boundary and put a balance-like tuning value inside the platform layer, where NFR-006's
conditional-count would then have to follow it.

Separate from IF-019 and IF-025: the diagnostic log is the only consumer of all three operations
here, it never needs an atomic replace, and the save-file and preference consumers never append,
measure or roll. Disjoint consumer sets, so a separate contract.

### Error Modes
- The directory cannot be resolved, or the file cannot be opened for append — no record written.
- Device full or permission denied — the append fails, and a returned call is not evidence the
  record landed.
- A partial append leaves a truncated final record — the byte count written is reported.
- Concurrent appends interleave mid-record — records must be submitted whole.
- The roll moves the live file aside but the discard of the oldest copy fails — occupancy exceeds
  the cap until the next successful roll, and the caller is told.
- The roll cannot move the live file at all — the log stays at its size, and the caller decides
  whether to append past the cap or drop; IF-016 drops.
- The measured size is stale by the time the roll is asked for — the cap is enforced approximately
  and can be exceeded transiently, which is what "under a cap indefinitely" allows and "under a
  cap at every instant" would not.

### Rationale
Satisfies both of CMP-015's file capabilities: appending to the log, and measuring and rolling it
over. One contract for the two because their consumer set is the same single component and the
three operations are used in one sequence — measure, roll if over, append. Confidence is raised to
high this round: the operations now follow directly from NFR-007's two clauses rather than leaving
one of them unimplementable. What NFR-007 does not fix is the cap's value or the number of rolled
copies retained, and both are caller-supplied here rather than assumed.

## IF-022 — Local Notification Presentation [#if-022]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract through which a care reminder is presented to the owner on the host
desktop, reaching no network.

### Operations
- **present_notification** — Present a local notification to the owner on the host desktop,
  contacting no remote service and opening no outbound connection.

### Interaction
Asynchronous. The reminder service hands the notification over and does not wait: host notification
delivery is outside the application's control, and FR-009's reminders are advisory.

One operation. The contract's whole content is the delivery plus the boundary it must not cross —
CON-002 forbids any core function depending on a remote service, and NFR-005 checks it at the
network interface, so "no outbound connection" is part of the contract rather than an
implementation note.

### Error Modes
- The host notification service is unavailable or permission has been denied — not presented, and
  the caller is told, with no retry that could surface as a burst later.
- Accepted by the host but suppressed by do-not-disturb or focus mode — never shown, and
  indistinguishable from delivery.
- The host rate-limits notifications — further notifications dropped for a period, not queued.
- The platform's notification API requires an unregistered application identity — rejected on that
  platform while succeeding on the others.

### Rationale
Satisfies CMP-014's declared need to present a local notification without network access. Requirements A-19
establishes that delivery through the host's local notification service counts as fully offline;
this contract is the seam that keeps it that way, and it is the only path out of the process for
FR-009. The permission failure named here is the same one IF-028 must be able to report to the
owner, since an enabled preference that can never deliver is otherwise silent.

## IF-023 — OS Notification Posting [#if-023]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-018 |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The external contract the platform adapter posts notifications to — the host operating system's
own native notification service.

### Operations
- **post** — Post a notification to the host operating system's native notification service for
  display to the owner on the desktop.

### Interaction
Asynchronous. The service displays the notification on its own schedule and the application has no
result to wait for; acceptance of a post is not evidence of display, and this contract cannot make
it one.

### Error Modes
- The service is not running, or the platform's notification facility is absent in this session —
  the post is rejected.
- The owner has revoked notification permission at the OS level — posts are rejected until it is
  granted again, and the application cannot grant it for itself.
- Accepted and then silently withheld by do-not-disturb or focus mode.
- Rate-limited or coalesced by the service — later posts dropped without notice.

### Rationale
Satisfies CMP-017's declared need to post to the host notification service. This is one of the
edges leaving the process, and modelling the service as an external component keeps that edge
inside the graph rather than pointing outside it. Requirements A-21 assumes each target platform provides a
usable native notification API — an assumption this contract's first failure mode is where it would
show up if it did not hold.

## IF-024 — Host Wall-Clock Reading [#if-024]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-019 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The external contract through which the platform adapter reads the operating system's current
wall-clock time.

### Operations
- **read_time** — Return the operating system's current wall-clock time.

### Interaction
Synchronous. A clock reading delivered later than it was requested is a different reading.

Distinct from IF-018 and deliberately not merged with it. This is the raw host reading, consumed
only by the platform adapter; IF-018 is what the rest of the codebase sees, and it adds the
signed-interval derivation the adapter builds on top. Collapsing the two would put a platform call
in front of every internal consumer, which is precisely the seam NFR-006 counts violations of.

### Error Modes
- The host clock is uninitialised or unavailable — no reading, and no elapsed interval anywhere in
  the product can be derived.
- The clock is moved backward between two readings — a reading earlier than a recorded timestamp is
  returned, which requirements A-7 requires the host to expose observably.
- The host smooths a backward correction instead — readings stay monotonic, no non-positive
  interval is ever observable, and both of requirements A-6's rules are defeated with no visible failure.
- A time-sync correction moves the clock forward — a larger-than-real elapsed interval is observed
  and decay applies for all of it, bounded only by each stat's scale (requirements A-24).

### Rationale
Satisfies CMP-017's declared need to read the operating system's wall-clock time. It is one of the
edges leaving the process, modelled as an external component so the dependency stays inside the
graph. Every elapsed-interval computation in the product originates here, which is why requirements A-7's
observability assumption is stated as a failure mode of this contract rather than left implicit.

## IF-025 — Local Data Directory Atomic File Replace [#if-025]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-017 |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract for replacing a file inside the application's local data directory
as one atomic operation, so an interrupted write never leaves a partially written file where the
previous one stood.

### Operations
- **replace_file_atomically** — Replace a named file with the supplied bytes as one atomic
  operation — written to a temporary file and renamed into place.

### Interaction
Synchronous. Atomicity is only useful to a caller that learns whether the replace took effect;
NFR-004 turns on exactly that distinction, and FR-009's preference toggle turns on a weaker version
of it — an owner must not be shown a saved setting that never reached disk.

**Split out of IF-019 this round.** The two were one contract while their consumer sets matched.
The balance configuration now reads from the local data directory and never writes to it, so the
read's consumers are a strict superset of the replace's, and a merged contract would hand CMP-002
an atomic-replace operation it must never call. This is the Interface Segregation test applied to
a subset rather than to a disjoint pair, and it is the same test that keeps IF-020 and IF-021
separate from both.

### Error Modes
- The temporary file is written but the rename fails — the previously committed file remains byte
  for byte, and the caller is told the replacement did not take effect.
- The local data directory cannot be resolved or created — nothing can be written.
- Permission denied or device full — nothing replaced, existing file untouched.
- The rename is not atomic on this platform or filesystem — the guarantee NFR-004 rests on is
  absent and FR-012's quarantine becomes the primary defence; not detectable from inside here.
- The process is terminated between the temporary write and the rename — the previous file stands
  and a temporary file is left behind, which the next replace must overwrite rather than treat as
  an obstruction.

### Rationale
Satisfies the atomic-replace capability declared by CMP-012 (the save file) and CMP-014 (the
reminder preference). Atomicity lives in this primitive because no caller-side ordering can supply
it (NFR-004), and the write-then-rename mechanism is one of the platform-divergent seams NFR-006
names — which is why the fourth failure mode is stated as a property of the platform rather than
of the code.

## IF-026 — Balance Configuration Load [#if-026]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-002 |
| Traces from | [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-008](/guide/examples/tamagotchi/requirements/non-functional/#nfr-008), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |

The contract through which the launch sequence causes the balance and tuning parameter set to be
read from its configuration source exactly once, so that every parameter read for the rest of the
session is served from memory.

### Operations
- **load** — Read the balance and tuning parameter set from its configuration source and hold it
  in memory for the remainder of the session, returning once the whole set is available or once
  the load has definitively failed.

### Interaction
Synchronous, and ordered. Nothing else in the launch sequence can run before it: the default pet
is built from configured starting values, the decay applied before first display needs the curve,
and the wake test needs the sleep duration. The lifecycle sequencer is the only component
positioned to order this read before its dependants and to abandon the launch if it fails, which
is why it is the only consumer.

**Why this exists as a contract separate from IF-001.** Last round there was only IF-001, and it
carried both the reads and the source-level failures — a missing or unparseable configuration
file — which its provider could not structurally have had, since nothing gave that provider a way
to reach a file. The fix is not to delete the failures, which are real, but to give them a place:
the load happens once, here, and the reads that follow are memory reads, there.

The separation earns its keep against NFR-008 and requirements A-17. Those require the decay computation to be
invocable 1,000 times against an in-memory starting state with no save file read and no
application launch. The decay computation reads `decay_parameters` on each repetition, so if a
parameter read could fall back to loading its source, the constraint would be unmeetable — every
repetition would be a potential file access. Load-once makes the whole transitive read set of
IF-003 file-free, and the fourth failure mode below is what keeps it that way: there is no
reload, so there is no second path to a file.

One operation, and the whole parameter set at once. A per-group load would let a launch proceed
with half a configuration and would multiply the ordering obligations the sequencer has to get
right.

### Error Modes
- The source is missing or unreadable — no set is held and the launch is abandoned.
- The source is present but unparseable — the same outcome, reported distinctly from absence, so a
  corrupt or hand-edited configuration is not mistaken for a first run.
- The source parses but carries no parameter set — treated as unparseable, not as a valid empty
  configuration.
- Load is asked for twice in one session — refused, because a mid-session parameter change would
  move a decay rate underneath a computation in flight.
- The source is edited while the application runs — not observed; Q-1's tuning loop needs a
  relaunch to take effect.

### Rationale
Satisfies CMP-011's declared need to load the balance and tuning parameters into memory.
Confidence is medium: no requirement states that the balance parameters live in a file separate
from the save file, or names their format — that shape is inferred from Q-1's tuning loop being
live and ongoing, and from the requirement set's consistent refusal to fix the values. What is not
inferred is the once-per-session ordering, which NFR-008 forces.

## IF-027 — Platform Presentation Surface [#if-027]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-017 |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |

The platform-adapter contract through which the owner's view is painted onto the host's rendering
surface and the pet's mood expression and health status are exposed as text to the platform's
native accessibility API.

### Operations
- **draw_view** — Paint the supplied owner-facing view onto the host's rendering surface and
  return once the frame has been presented.
- **announce_status_text** — Expose the supplied textual equivalents of the pet's mood expression
  and health status to the platform's native accessibility API.

### Interaction
Both synchronous. `draw_view` must be, because both of its callers' contracts depend on knowing
the frame landed: IF-017's first render is the closing boundary of NFR-009's measurement window,
and IF-030's redraw coalescing needs to know when a draw is still in flight. `announce_status_text`
is synchronous too, but not because the call is purely local — that premise was wrong. On some
targets the announcement goes to an accessibility bridge inside this process; on others it crosses
to a service in its own right, AT-SPI on a CON-003 Linux target being a D-Bus service, which is why
this contract's own third and sixth error modes have that stack absent, not running, or
un-integrated. Synchronous is the right answer under either premise, and the remote one argues for
it the more strongly: it is exactly when there is a party on the other end that can be missing that
the caller must learn the announcement did not land. Making it asynchronous would make NFR-003's
failure — a status that never became perceivable — unreportable to the only component that could
act on it.

**Why the two seams are one contract.** They are both provided by the platform adapter and both
consumed by exactly one component, the presentation shell, and the consumer uses both every time
it uses either: NFR-003 requires the textual equivalent to accompany the visual state, so there is
no render in this product that is drawn but not announced, and no announcement that does not
accompany a render. Splitting them would hand the shell two contracts it always holds together,
which is the shape the Interface Segregation rule exists to avoid rather than to produce. The
operations stay two, because their failure modes are entirely different and NFR-003 and NFR-006
trace to them separately.

**Why these seams sit in the adapter at all.** NFR-006 names rendering and accessibility
integration among the platform-touching behaviours that must live inside the platform-adapter
layer, and counts conditionals outside it against a target of zero. The previous round had the
presentation shell reaching both directly, which put two of the six named seams outside the layer
that exists to contain them; NFR-003's measure compounds it, because it runs through each
platform's own native stack, so "announce as text" is three different integrations behind one
contract. This is the seam that keeps that divergence in one place. CON-003 stages the platforms —
Windows first, macOS and Linux after v1 — so in practice this contract has one implementation at
v1 and its cross-platform value is realised later; that is a reason to fix the seam now, not to
defer it.

### Error Modes
- No rendering surface available — nothing painted, and a caller measuring first render has no
  boundary to close.
- The frame is presented but the surface is occluded, minimised, or on a disconnected display —
  the owner sees nothing while the application correctly believes it rendered.
- The platform's native accessibility stack is absent or not running — the status text is not
  exposed, which NFR-003 counts as a failure rather than a degradation.
- Empty status text, or a mood or health status with no textual equivalent — rejected rather than
  announced blank.
- The host coalesces or interrupts consecutive announcements — a rapid sequence reaches the owner
  as only its last.
- A platform whose accessibility stack this build has not integrated — the view paints, the text
  reaches nobody, and only NFR-006's cross-platform run shows it.

### Rationale
Satisfies both platform capabilities declared by CMP-016: drawing the owner's view, and announcing
mood and health status as text through the native accessibility API. Confidence is medium: Q-8
(still_open) asks whether the Sleeping state is rendered to the owner, and its answer changes what
a view carries and what the announcement must include. The operations survive either answer; their
content does not.

## IF-028 — Care Reminder Preference [#if-028]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-014 |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005) |

The contract through which the owner-facing surface reads the owner's care-reminder setting and
changes it — the "enabled by the owner" precondition FR-009 hangs its whole behaviour on.

### Operations
- **read_preference** — Return whether the owner has enabled care reminders, or report that no
  preference has ever been set.
- **set_preference** — Record the owner's choice and return once it is durable.

### Interaction
Both synchronous. `read_preference` because the surface cannot draw a control whose position it
does not know. `set_preference` because durability is the point: FR-009's condition outlives the
session that set it, and an owner who toggles reminders on and finds them off at the next launch
has been lied to by the control. The cost is that the owner's toggle blocks on a file write; it is
a single small file and a deliberate owner action, which is the opposite of the recurring hot path
where that cost would matter.

**Its own contract, not an operation on IF-015.** Both are provided by the reminder service, so
merging was the question. The consumer sets are disjoint — IF-015's consumer is the pet-state
evaluator, which raises reminders and has no business changing the owner's settings, and this
one's is the presentation shell, which never raises a reminder. They differ in interaction as
well: raising is fire-and-forget, and a preference change must be confirmed durable. Merging would
have put a setter in the evaluator's dependency surface, which is uncomfortably close to how
FR-009's enabled arm became unreachable in the first place.

**What this fixes.** FR-009 reads "Where care-reminder notifications are enabled by the owner",
and until this round nothing in the design could enable them. IF-015 read the effect of the
preference, IF-015's own failure mode treated an unreadable preference as disabled, and no
operation anywhere set it — so the never-writable default was permanently off and FR-009's enabled
arm was unreachable by construction. The feature validated as a design and could not have shipped
working.

Note the deliberate asymmetry in the second failure mode: an unreadable preference is *disabled*
to the raising path and *unreadable* to the surface. Treating it as disabled is the safe default
where the consequence is an unwanted notification; it is the wrong default where the consequence
is showing the owner a setting they never chose.

### Error Modes
- No preference has ever been set — its own outcome, treated as disabled, because FR-009's
  reminders are opt-in.
- The preference cannot be read — reported as unreadable to the surface, disabled to the raising
  path.
- The change cannot be made durable — reported as not saved, and the control must not move.
- Enabled while the host denies notification permission — set, undeliverable, and the owner must
  be able to be told.
- Changed mid-evaluation — the reminder that evaluation raises may reflect either setting; FR-009
  is a should and this is accepted rather than serialized.

### Rationale
Satisfies CMP-016's declared need to read and change the owner's care-reminder preference. The
preference belongs to the feature it gates rather than to the surface that displays it, which is
why the provider is the reminder service and not the shell. Confidence is medium: FR-009 is a
*should* and states nothing about where the control lives, how the owner reaches it, or whether
the preference survives a save-file quarantine — the last of which is why it is assumed to live in
its own file rather than inside the pet state.

## IF-029 — Session-End State Commit [#if-029]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | high |
| Provider | CMP-003 |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |

The contract through which the lifecycle sequencer asks the session holding the live pet state to
commit it as the session's final act, discharging FR-001's close trigger.

### Operations
- **commit_before_close** — Commit the session's live pet state durably as the last act of the
  session, returning once it is durable or once the commit has definitively failed.

### Interaction
Synchronous, and there is no close call here. The process is about to exit; an asynchronous commit
would have no one left to complete for. The whole value of the operation is that the caller can
wait for it before exiting, and can be told when it did not happen.

**Its own contract, not an operation on IF-002.** The pet session provides both, but IF-002's
consumers — the care handler, the evaluator, the launch path, the presentation shell — are four
components that read and replace live state during a session, and none of them closes it. This
contract's single consumer closes the session and does not replace state on that path. A strict
subset of consumers, so the Interface Segregation test splits rather than merges: folding this in
would give all four of those components a close-the-session operation, and one of them is the
recurring evaluator whose evaluations must be stopped *before* this runs, not able to trigger it.

**Why FR-001's close trigger routes through the session rather than the store.** The lifecycle
sequencer could have called IF-013 directly. Routing it here keeps BR-002's obligation — inspect
every code path that writes, clears or replaces persisted pet state — converging on one custodian:
the session owns the live state and mediates every commit of it, whether the trigger was a stat
change or the owner closing the application.

**The close path is ordered: stop, then commit, then exit.** That ordering is not stated by any
requirement, and it is the second failure mode below, because the reverse is silently wrong rather
than loudly broken.

### Error Modes
- The commit fails — the session ends with the most recent care unsaved beyond the last
  stat-change commit, and the caller is told.
- The cadence was not stopped first — an in-flight evaluation can install a state after this
  commit read the live one; IF-010's stop is what discharges the ordering.
- Called more than once on the same close path — idempotent, and not a second FR-001 trigger for
  NFR-007's record count.
- The host terminates the process before the commit returns — the most recent stat-change commit
  remains the committed state.
- The pet is at the terminal end-of-life status — committed unchanged; BR-002 forbids discarding
  its state, not persisting it.

### Rationale
Satisfies CMP-011's declared need to commit the live pet state before the session ends. FR-001
names two persist triggers — a stat value changing, and the owner closing the application — and
until this round only the first had an owning element. This is the second, and it is why the
lifecycle sequencer now owns close symmetrically with launch.

## IF-030 — Pet View Refresh [#if-030]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | medium |
| Provider | CMP-016 |
| Traces from | [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003) |

The contract through which a pet-state evaluation asks the owner's view to be redrawn after the
pet has advanced with no owner input, carrying the pet as it stood before that advance so that an
unchanged mood expression and health status is not announced again.

### Operations
- **refresh** — Redraw the owner's view from the live pet state and, where the pet's mood
  expression or health status differs from the one the supplied pre-advance pet state carried,
  announce the new values — without blocking the evaluation that asked for it.

### Interaction
Asynchronous. The evaluation has already installed and committed the state before it asks for a
redraw, so it has nothing to learn from the result and no reason to wait. A redraw that fails must
not fail the evaluation — the pet really did advance, and reverting or retrying the derivation
because a frame did not paint would be worse than a stale view for one cadence period.

**This is the other half of the old IF-017, and the split was overdue.** Last round both this and
the launch-time first display were forced into one contract, because CMP-009 and CMP-011 had
declared the identical capability string and the exactly-once rule left no way to separate them
from the interface layer. That was flagged then as a carving too coarse to segregate; the
component set has since split the capability, and the two halves separate along all three axes at
once. Disjoint consumers: the evaluator refreshes, the lifecycle sequencer displays first.
Opposed interaction: this one must not block, and first render must be blocking to close NFR-009's
measurement window. Opposed failure semantics: a failed first render fails the launch, a failed
refresh does not fail the evaluation. Bundling them made the second and third of those
unstateable, because the contract could carry only one answer per question.

The drawing and announcing themselves go through IF-027, inside the platform-adapter layer. This
contract decides that a redraw is warranted and from what; it does not touch a platform.

**Why `refresh` takes the pre-advance pet state.** Without it the announcement fires on every
tick, and most ticks change nothing a screen-reader user has not already heard — an unchanged
mood and health status repeated at cadence frequency, which is precisely what NFR-003's scripted
walkthrough is run to catch. The comparison was never unavailable: CMP-009 holds the pre-state
and the post-state at the moment it calls, and already hands that same pair to IF-007's `select`
and IF-015's `raise_for_stat_change`. This contract takes it in the same shape, for the same
reason, and the previous round simply had not asked for it. Only the announcement is conditioned
on the comparison — the visual redraw runs either way, because it is coalesced and cheap and the
frame should track the live pet state whether or not the difference is one worth speaking.

### Error Modes
- The live pet state cannot be read at redraw time — the previous view is held rather than a blank
  one drawn.
- The redraw fails outright — the evaluation still stands; the owner sees a stale view until the
  next one succeeds.
- Overlapping refreshes — coalesced to the latest live state rather than queued.
- Refreshes faster than the display can present them — coalesced, which is what keeps a short
  cadence from spending NFR-002's idle budget on frames nobody sees.
- The pet advanced but its mood and health status did not change — the view still redraws and
  the announcement is suppressed, since repeating it at cadence frequency is an NFR-003 failure
  rather than a harmless redundancy.
- No pre-advance pet state supplied — the announcement fires rather than being suppressed; a
  repeated announcement is the better of the two failures.
- The pre-advance pet state is not the one the pet actually held — a real change is suppressed,
  or an unchanged one announced; undetectable here, which is why the evaluation that caused the
  advance supplies it.

### Rationale
Satisfies CMP-009's declared need to refresh the owner's view after the pet has advanced without
owner input, which FR-008's neglect progression and FR-011's wake both cause with no interaction
at all. Confidence is medium: Q-8 (still_open) asks whether the Sleeping state is rendered, and a
wake is precisely one of the advances this contract exists to show — so what a refresh is obliged
to draw and announce after FR-011 fires depends on Q-8's answer even though the operation does not.

## IF-031 — Platform Recurring Timer [#if-031]

| Field | Value |
| --- | --- |
| Type | interface |
| Status | draft |
| Confidence | low |
| Provider | CMP-017 |
| Traces from | [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |

The platform-adapter contract through which a caller that owns a cadence obtains a recurring tick
at a period it supplies, and stops that tick again, without holding a platform timer of its own.

### Operations
- **start_recurring** — Begin delivering a recurring tick at the requested period to the supplied
  handler, and return once the host's timer facility is established, or report that it cannot be.
- **cancel** — Stop delivering ticks and return once no further tick will be delivered and no
  tick delivery is still in flight.

### Interaction
Both synchronous, and for the same reason in both directions: each returns a fact the caller
cannot proceed without. `start_recurring` returns whether a timer facility exists at all — the
condition IF-010 must report and, until this contract existed, had no structural way to observe.
`cancel` returns quiescence, which is an ordering guarantee rather than a value: the close path is
stop the cadence, commit the live pet state (IF-029), exit, and a cancel that returned before the
last tick had been delivered would let an evaluation install a re-derived state after the final
commit had already read the live one.

Neither operation blocks for long. The ticks themselves are the asynchronous part of this seam,
but they are deliveries the provider makes to the handler, not calls the consumer makes here, so
the contract's two operations are both blocking and the arrangement is not mixed-mode.

Two operations and no more. A period query, a running-or-not query, or a one-shot timer would each
be a facility no declared capability asks for; stoppability is what the capability names, and
`cancel` is what supplies it.

### Error Modes
- No usable timer facility, or one that cannot be established — reported at start rather than by
  silence, which is indistinguishable from a period that has not yet elapsed.
- A non-positive period, or one finer than the host can resolve — rejected rather than coerced to
  the fastest tick available, which would spend NFR-002's idle budget at a rate nobody asked for.
- Late, dropped, or drifting ticks across a sleep or a throttling window — not back-filled, and
  the period is approximate; elapsed time must come from the wall clock, never from a tick count.
- The handler raises on a tick — later ticks are still delivered; a primitive that stopped
  silently would leave the caller holding a cadence that no longer exists.
- cancel asked for mid-delivery — it waits for that delivery rather than abandoning it partway.
- cancel cannot confirm quiescence within a bounded wait — reported rather than returned as
  success, since a false confirmation is the one failure this operation exists to prevent.
- Started twice, or cancelled twice or without a start — idempotent in both directions.

### Rationale
Satisfies CMP-010's declared need for a recurring tick driven from the host's timer facility.
NFR-006 enumerates "wall-clock and timer access" in a single clause as platform-touching seams
that belong inside the platform-adapter layer, and this is the timer half of it; the wall-clock
half is IF-018. The two are deliberately separate contracts even though one layer provides both
and one component consumes both, because they are different questions: IF-018 answers what time
it is when asked, and this one drives the application unasked, which is the machinery NFR-002
budgets by name at idle. Their consumer sets differ too — five components read the clock and one
is driven by a tick — so folding them together would hand every clock reader a timer it never
starts.

Before this contract, IF-010 declared an unavailable timer facility as its first error mode while
its provider held no platform seam through which such a thing could be observed. That was F-14.
The cadence — period, coalescing, when it starts and stops — stays with CMP-010; only the tick
crosses into the adapter.

**Confidence is low**: Q-10 (still_open) asks how often the running application re-evaluates pet
state and what bounds that interval, and NFR-002 constrains the same parameter from the other
side. A fixed period is what CMP-010's capability names and what `start_recurring` therefore
takes; if Q-10 resolves instead to an adaptive or event-driven cadence, the period argument — and
possibly whether a recurring-tick primitive is the right seam at all — changes with it. The
stop half does not depend on the answer.

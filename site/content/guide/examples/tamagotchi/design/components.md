<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/design/components/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Components

The 19 components from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## CMP-001 — Pet State Model [#cmp-001]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Owns the pet state representation and its invariants, including construction of a default pet. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001) |

The canonical in-memory representation of a pet state — every pet stat value, the
health status, the Awake/Sleeping state field, the sleep-entry timestamp and the
last-saved timestamp — together with the invariants those values must satisfy.

### Responsibility
Owns the pet state representation and its invariants, including construction of a
default pet.

### Rationale
The glossary's Pet state entry is the single maintained enumeration of what the
application persists (requirements A-22), and FR-001 requires every one of those fields to
round-trip unchanged; giving that enumeration one owner is what makes the round-trip
testable as a property of a type rather than of a serialiser. The same owner holds
the stat bounds that make FR-003, FR-004 and FR-005's "up to the stat's maximum
value" true at every write, not only at the care action. FR-010's default pet is a
particular instance of this model, so its construction belongs here rather than on
the recovery path.

Confidence is medium rather than high because FR-008's per-stat below-threshold clock
may require a new persisted field (see CMP-005); that decision, tied to Q-10, changes
this component's field set and requirements A-22's enumeration with it.

## CMP-002 — Balance Configuration [#cmp-002]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | low |
| Boundary | internal |
| Responsibility | Supplies the pet's balance and tuning parameters to the components that read them. |
| Traces from | [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-008](/guide/examples/tamagotchi/requirements/non-functional/#nfr-008) |
| Depends on | [IF-019](/guide/examples/tamagotchi/design/interfaces/#if-019) |

The supplier of every tunable value the pet simulation reads — decay rates, neglect
thresholds, both sustained-neglect durations, the sleep duration, mood-threshold band
boundaries, care increments, and stat bounds and starting values.

### Responsibility
Supplies the pet's balance and tuning parameters to the components that read them.

### Rationale
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
starts no application, which is exactly what requirements A-17 requires of it.

Confidence is low: Q-1 is still_open, so every value this component carries is
unfixed. Only its shape — a read-only parameter set with one owner, filled once at
launch — is settled.

## CMP-003 — Pet Session [#cmp-003]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Holds the application's live pet state as its sole custodian, mediating every read of it, every replacement of it and every commit of it to durable storage. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |
| Depends on | [IF-013](/guide/examples/tamagotchi/design/interfaces/#if-013) |

The holder of the application's single live pet state for the duration of a session,
the only path through which any component reads or replaces it, and the point from
which it is committed to durable storage on both of FR-001's persist triggers.

### Responsibility
Holds the application's live pet state as its sole custodian, mediating every read of
it, every replacement of it and every commit of it to durable storage.

### Rationale
FR-001's ASR reading is that the only path able to destroy accumulated state must sit
behind one contract, because BR-002 is verified by inspecting every path that writes,
clears or replaces persisted pet state — a finite inspection only if those paths
converge. The durable half of that convergence is CMP-012; this is the in-memory half.

Both of FR-001's persist triggers leave through this component. The "when a pet stat
value changes" trigger is observed here because every replacement passes through here.
The "owner closes the application" trigger is asked for here too, as the session's
final act, rather than the closing caller reading the live state out and committing it
itself — a second commit path opened at close would reopen the inspection BR-002's
convergence argument depends on being finite, which is the whole reason this component
is stated as the sole custodian rather than merely as a reader and replacer.

A replacement that leaves every pet state field equal does not re-commit. The write
cadence that results from combining FR-001's trigger with a running evaluation cadence
(Q-10) is in tension with NFR-002's idle budget and is left to the decision stage.

## CMP-004 — Decay Engine [#cmp-004]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Computes the decayed pet state for a given starting pet state and elapsed interval. |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-008](/guide/examples/tamagotchi/requirements/non-functional/#nfr-008), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001) |

The pure computation that maps a starting pet state and an elapsed interval to the
decayed pet state, in one bounded step and without reading a clock.

### Responsibility
Computes the decayed pet state for a given starting pet state and elapsed interval.

### Rationale
NFR-008 carries an explicit testability constraint on the design (requirements A-17): the decay
computation must be invocable directly, a thousand times in a loop, with an in-memory
starting state and no save file read and no application launch. That forbids decay
being a stage inside the launch routine and makes it its own unit that the launch path
calls. NFR-008's response also forbids walking the interval tick by tick, so the
mapping is closed-form over the interval.

The elapsed interval arrives as a parameter, never from an ambient clock read: FR-002's
clamp of a non-positive interval to zero elapsed time, and NFR-001's requirement to
drive the computation through a negative-interval matrix, are both only executable if
the interval is supplied. This component applies FR-002's clamp rule; it does not apply
FR-011's re-basing rule, which belongs to a deadline rather than to a quantity (requirements A-6).

## CMP-005 — Health Progression [#cmp-005]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | low |
| Boundary | internal |
| Responsibility | Advances the pet's health status under sustained unremedied neglect. |
| Traces from | [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016), [IF-018](/guide/examples/tamagotchi/design/interfaces/#if-018) |

The single writer of the pet's health status, advancing it one step along the
Healthy to Sick to terminal end-of-life progression under sustained per-stat neglect.

### Responsibility
Advances the pet's health status under sustained unremedied neglect.

### Rationale
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

## CMP-006 — Sleep Cycle [#cmp-006]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Owns the pet's Awake/Sleeping transitions and the sleep-entry timestamp they turn on. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016), [IF-018](/guide/examples/tamagotchi/design/interfaces/#if-018) |

The owner of the Awake/Sleeping state field and the sleep-entry timestamp, including
entry into the Sleeping state and the elapsed-duration wake deadline with its
re-basing rule.

### Responsibility
Owns the pet's Awake/Sleeping transitions and the sleep-entry timestamp they turn on.

### Rationale
FR-011 introduces a second, incompatible non-positive-interval rule alongside FR-002's
(requirements A-6): a deadline re-bases its origin where a quantity merely clamps. Two rules over
the same clock reading mean the clock contract cannot expose a single "elapsed since"
and be done — the discriminator has to live somewhere the design names, and this is
that place for the deadline half. The clock contract this component consumes therefore
returns a signed interval and applies neither rule.

Entry is idempotent per FR-006's fit criterion, and requirements A-8 fixes that there is no
owner-initiated wake: the pet leaves Sleeping only on elapsed sleep duration, tested at
launch before display and on the running cadence. Sleep does not alter stat decay, so
nothing here touches CMP-004.

## CMP-007 — Mood Expression Selector [#cmp-007]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Selects the pet's mood expression from the band containing its lowest stat value. |
| Traces from | [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016) |

The rule that maps a pet's current stat values to a mood expression, by locating the
mood-threshold band containing the pet's lowest stat value.

### Responsibility
Selects the pet's mood expression from the band containing its lowest stat value.

### Rationale
FR-007's reduction rule is the minimum, not the mean — an average would let one
critically low stat hide behind healthy ones — and that rule is domain logic, not
rendering. Keeping selection separate from CMP-016 is also what NFR-003 needs: the
presentation surface consumes a semantic mood it can expose as text through the
platform accessibility API, rather than deriving one from what it drew. The band
boundaries themselves are configuration, so re-tuning them under Q-1 does not touch
this component.

## CMP-008 — Care Interaction Handler [#cmp-008]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Applies an owner-selected care-loop action to the current pet. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001), [IF-002](/guide/examples/tamagotchi/design/interfaces/#if-002), [IF-005](/guide/examples/tamagotchi/design/interfaces/#if-005), [IF-007](/guide/examples/tamagotchi/design/interfaces/#if-007) |

The application of an owner-selected care-loop action — feed, play, clean or sleep —
to the current pet, producing the resulting pet state.

### Responsibility
Applies an owner-selected care-loop action to the current pet.

### Rationale
The care loop is the fixed set of four interactions the glossary names, and requirements A-8 rules
out a fifth, so one component can own the whole set without an open-ended surface.
Three of the four are the same shape — raise the corresponding stat by its configured
increment, capped at the stat maximum by CMP-001's invariant — and the fourth delegates
to CMP-006 rather than touching the Awake/Sleeping field itself.

This component returns the resulting pet state to its caller rather than driving the
display, which keeps the owner-facing surface a caller of the care loop and not also
its callee.

## CMP-009 — Pet State Evaluator [#cmp-009]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Performs a pet-state evaluation, re-deriving the current pet state from the wall clock. |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009) |
| Depends on | [IF-002](/guide/examples/tamagotchi/design/interfaces/#if-002), [IF-003](/guide/examples/tamagotchi/design/interfaces/#if-003), [IF-004](/guide/examples/tamagotchi/design/interfaces/#if-004), [IF-006](/guide/examples/tamagotchi/design/interfaces/#if-006), [IF-007](/guide/examples/tamagotchi/design/interfaces/#if-007), [IF-015](/guide/examples/tamagotchi/design/interfaces/#if-015), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016), [IF-018](/guide/examples/tamagotchi/design/interfaces/#if-018), [IF-030](/guide/examples/tamagotchi/design/interfaces/#if-030) |

The single occasion on which the system reads the current wall clock and re-derives
the pet's state from it — applying elapsed decay, advancing health status and testing
the wake deadline.

### Responsibility
Performs a pet-state evaluation, re-deriving the current pet state from the wall clock.

### Rationale
Pet-state evaluation is a named concept in the glossary, and FR-007's mood update,
FR-008's neglect progression and FR-011's wake all presuppose one (requirements A-23). Giving it a
component means the launch path and the running cadence drive the same derivation
rather than two divergent ones, which is what makes FR-011's "including trials where
the duration elapses entirely while the application is closed" the same code path as
the in-session case.

This component composes; it does not compute. Decay, progression and the wake deadline
each live in their own unit, which is what NFR-008's direct-invocation constraint and
BR-001's single-writer rule require. It emits NFR-007's one record per decay
computation, and it derives that record's delta field itself, by differencing the
pre-state it supplied to CMP-004 against the decayed state CMP-004 handed back —
CMP-004 returns a state, not deltas, and holding both ends is what lets this component
produce the field NFR-007's replay check is defined over. Doing the differencing here
also keeps the decay computation free of the log, so NFR-008's thousand-repetition
measure times the computation alone.

Confidence is medium: the shape is settled, but what an evaluation must do about
FR-008's below-threshold clock depends on the still_open Q-10 decision recorded against
CMP-005.

## CMP-010 — Evaluation Scheduler [#cmp-010]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | low |
| Boundary | internal |
| Responsibility | Drives recurring pet-state evaluation while the application is running. |
| Traces from | [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006) |
| Depends on | [IF-009](/guide/examples/tamagotchi/design/interfaces/#if-009), [IF-031](/guide/examples/tamagotchi/design/interfaces/#if-031) |

The recurring driver that causes a pet-state evaluation to happen on the running
application's own cadence, with a bounded period.

### Responsibility
Drives recurring pet-state evaluation while the application is running.

### Rationale
FR-011 makes the pet's state advance with no owner input at all, which forces a
recurring driver to exist as its own unit rather than as a side effect of rendering —
a pet asleep behind a static window must still wake. NFR-002 is the counter-force: it
budgets "whatever background timer machinery the chosen implementation uses" at idle,
so the period is a first-class architectural parameter rather than an implementation
detail, and isolating it in one component is what lets it be tuned against the budget
without touching the derivation.

The recurring timer itself is not held here. NFR-006 enumerates "wall-clock and timer
access" in one clause as platform-touching seams that belong to the platform-adapter
layer, so this component consumes timer access from that layer the way every other
component consumes platform behaviour. That is also what gives it a structural way to
observe a timer facility that cannot be established, and to report it rather than
leaving the caller assuming a live pet.

Confidence is low: Q-10 — how often the running application re-evaluates pet state and
what bounds that interval — is still_open, and NFR-002, the constraint that would bound
it from the other side, is not evaluable until Q-5 records a reference machine.

## CMP-011 — Application Lifecycle Sequencer [#cmp-011]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Orders the application's session boundaries, from launch through to close. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-010](/guide/examples/tamagotchi/requirements/functional/#fr-010), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [NFR-009](/guide/examples/tamagotchi/requirements/non-functional/#nfr-009), [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001) |
| Depends on | [IF-002](/guide/examples/tamagotchi/design/interfaces/#if-002), [IF-009](/guide/examples/tamagotchi/design/interfaces/#if-009), [IF-010](/guide/examples/tamagotchi/design/interfaces/#if-010), [IF-011](/guide/examples/tamagotchi/design/interfaces/#if-011), [IF-012](/guide/examples/tamagotchi/design/interfaces/#if-012), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016), [IF-017](/guide/examples/tamagotchi/design/interfaces/#if-017), [IF-026](/guide/examples/tamagotchi/design/interfaces/#if-026), [IF-029](/guide/examples/tamagotchi/design/interfaces/#if-029) |

The ordered path across both of the application's session boundaries — at launch,
retrieve the committed pet state or fall back to a default pet, evaluate before anything
is drawn, show the pet and start the running cadence; at close, stop that cadence and
commit what the session holds.

### Responsibility
Orders the application's session boundaries, from launch through to close.

### Rationale
FR-002 places a computation whose input is elapsed real time ahead of first render,
which separates launch into ordered stages, and NFR-009 defines its measurement window
structurally — between the completion of the committed-save read and the first render.
That window is only expressible if those two events are distinct, observable boundaries
rather than one opaque startup, which is what this component provides.

NFR-004's discriminating clause rules out a failed read falling through to the default
pet without first establishing that no committed state survives, so the retrieval
outcome distinguishes "no file present" (FR-010) from "present but not a committed
state" (FR-012) and this sequence branches on it rather than on an error. BR-001 is
satisfied structurally: neither branch here can advance health status, because the only
writer of it is CMP-005, which this sequence does not call except through an evaluation
that starts from a Healthy default pet.

Close is the other half of the same responsibility, and it is here because launch is.
FR-001 names two persist triggers and the second of them — the owner closing the
application — is an occasion rather than a state change, so no component that watches
state changes can serve it; it needs an element that knows the session is ending. The
close path is the launch path in reverse: stop the recurring cadence this sequence
started, so that no evaluation is still re-deriving a state as the process exits, then
ask the session to commit what it holds. FR-001's AC-3 — the Sleeping state and its
sleep-entry timestamp surviving a close — is satisfied at that commit, because the
session's live pet state carries both fields and the commit writes pet state in full.

Owning both boundaries is also what makes the lifecycle symmetric rather than a start
with no stop. It does not make this two components: the responsibility is the ordering
of the session's boundaries, and there is exactly one ordering, read forwards at launch
and backwards at close.

## CMP-012 — Pet State Store [#cmp-012]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Owns custody of the pet state save file as the system's single system of record. |
| Traces from | [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002) |
| Depends on | [IF-014](/guide/examples/tamagotchi/design/interfaces/#if-014), [IF-016](/guide/examples/tamagotchi/design/interfaces/#if-016), [IF-018](/guide/examples/tamagotchi/design/interfaces/#if-018), [IF-019](/guide/examples/tamagotchi/design/interfaces/#if-019), [IF-020](/guide/examples/tamagotchi/design/interfaces/#if-020), [IF-025](/guide/examples/tamagotchi/design/interfaces/#if-025) |

The custodian of the save file as the system's single system of record — committing a
pet state atomically, and handing back the committed pet state or reporting that none
is available.

### Responsibility
Owns custody of the pet state save file as the system's single system of record.

### Rationale
FR-001 writes on every stat change rather than on a timer, which makes a mid-write kill
an ordinary event and forces commit atomicity into the store rather than leaving it to
the caller. BR-002 is verified by inspecting every code path that writes, clears or
replaces persisted pet state — affordable only because every such path converges here.
One committed generation is retained (Q-9, resolved), because atomic write-then-rename
already prevents an interrupted write from replacing a committed file.

This component orders the failed-read path but implements neither half of it:
validation belongs to CMP-013 and the byte-identical move to CMP-017, per FR-012's
requirement that neither be folded into the unit that hands back a decoded pet state.
The quarantine move completes before any new write, so a default pet cannot overwrite
the evidence. CON-002 and NFR-005 bind this component absolutely — the local file is
the only permissible system of record, and it holds no network client of any kind.

## CMP-013 — Save Integrity Validator [#cmp-013]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Establishes whether a save file's contents are a committed state. |
| Traces from | [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004) |

The check applied to a save file's contents at read, establishing whether the file is
complete and internally consistent enough to be treated as a committed state.

### Responsibility
Establishes whether a save file's contents are a committed state.

### Rationale
FR-012 splits the load path in two — a read that succeeds and a read that fails
validation and must preserve its evidence byte-identically before anything else writes
— so integrity validation cannot live in the same unit that hands back a decoded pet
state. Separating it also gives NFR-004's 200-trial fault injection a unit to drive
directly with truncated and corrupted content, rather than only through a launch.

Committed status is established at write time; this check is how a reader confirms it,
not what creates it. Confidence is medium because the glossary leaves the mechanism
implementation-defined — a checksum over the file, or a strict decode against CMP-001's
field set — and this stage defers that choice to the decision record.

## CMP-014 — Care Reminder Service [#cmp-014]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | internal |
| Responsibility | Owns the optional care-reminder feature, from the owner's enablement of it through to the reminder it raises. |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |
| Depends on | [IF-001](/guide/examples/tamagotchi/design/interfaces/#if-001), [IF-019](/guide/examples/tamagotchi/design/interfaces/#if-019), [IF-022](/guide/examples/tamagotchi/design/interfaces/#if-022), [IF-025](/guide/examples/tamagotchi/design/interfaces/#if-025) |

The optional care-reminder feature in full — the owner's enablement preference, the rule
that decides when a pet stat's crossing of its neglect threshold warrants a reminder,
and the request that presents it.

### Responsibility
Owns the optional care-reminder feature, from the owner's enablement of it through to
the reminder it raises.

### Rationale
FR-009 is the only requirement that crosses the process boundary out of the
application, and it is the one place a "local" delivery mechanism could quietly acquire
a network dependency, which CON-002 forbids outright and NFR-005 measures at the
network interface. Isolating the feature — its enablement, its trigger rule and its
request for delivery — makes the "zero notifications and zero network requests when the
feature is disabled" half of its fit criterion a property of one component.

The threshold comparison lives here rather than in the evaluator so that FR-009's
trigger and CMP-005's neglect clock read the same configured thresholds without either
owning the other's rule.

FR-009's condition is not "reminders are on" but "enabled by the owner", which means the
preference needs a writer the owner can reach, not only a reader the trigger consults. It
is owned here — alongside the trigger it gates — and read and changed through this
component by the owner-facing surface, which is the only element an owner acts on. Without
that edge the preference would be permanently at its default and FR-009's enabled arm
would be unreachable by any owner action, which the fit criterion tests both halves of.
The default itself is off: an absent or unreadable preference file is treated as disabled,
so the feature can never surprise an owner who has not asked for it.

Confidence is medium: FR-009 is a should-priority requirement, and no requirement in the
digest states where the owner's reminder preference is persisted, so this component's
ownership of that setting remains an assumption even though its writer is now named.

## CMP-015 — Diagnostic Log [#cmp-015]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Writes the structured local record for each decay computation and lifecycle transition. |
| Traces from | [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002) |
| Depends on | [IF-018](/guide/examples/tamagotchi/design/interfaces/#if-018), [IF-021](/guide/examples/tamagotchi/design/interfaces/#if-021) |

The local, user-readable structured log of every decay computation and pet lifecycle
transition, held under a fixed rotation cap.

### Responsibility
Writes the structured local record for each decay computation and lifecycle transition.

### Rationale
NFR-007 requires exactly one structured record per decay computation and per lifecycle
transition, carrying pre-state, post-state and deltas, and replayable through the
reference decay model. "Exactly one" is a structural claim: the emit points must be
singular and owned, which rules out incidental logging scattered through callers. This
component owns the record shape and the rotation cap; each emit point is the single
component that owns the transition it announces — CMP-005 for sickness and terminal,
CMP-006 for sleep and wake, CMP-007 for mood, CMP-012 for save, load and quarantine,
CMP-011 for launch, and CMP-009 for the decay computation it applies.

Owning the cap means enforcing it, not only knowing it. NFR-007's "indefinitely" is
the operative word: a log that only appends grows without limit, and a log that stops
appending at the cap silently loses every record after it, which fails the same clause
from the other side. So this component tracks the log's size and rolls the file over
when the cap is reached, discarding the oldest rolled copy — the decision is its own,
the file operations are the adapter's. The cap's numeric value is not stated by any
requirement in the digest and must be set before the behaviour is testable.

NFR-005 and CON-002 bind the log as tightly as they bind the save file: local-only,
user-readable, and never transmitted.

## CMP-016 — Presentation Shell [#cmp-016]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | low |
| Boundary | internal |
| Responsibility | Owns the owner's view of the pet and the controls the care loop is exercised through. |
| Traces from | [FR-003](/guide/examples/tamagotchi/requirements/functional/#fr-003), [FR-004](/guide/examples/tamagotchi/requirements/functional/#fr-004), [FR-005](/guide/examples/tamagotchi/requirements/functional/#fr-005), [FR-006](/guide/examples/tamagotchi/requirements/functional/#fr-006), [FR-007](/guide/examples/tamagotchi/requirements/functional/#fr-007), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [CON-001](/guide/examples/tamagotchi/requirements/constraints/#con-001), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |
| Depends on | [IF-002](/guide/examples/tamagotchi/design/interfaces/#if-002), [IF-008](/guide/examples/tamagotchi/design/interfaces/#if-008), [IF-027](/guide/examples/tamagotchi/design/interfaces/#if-027), [IF-028](/guide/examples/tamagotchi/design/interfaces/#if-028) |

The owner-facing surface — the rendered pet with its mood expression, health status and
stats, and the controls through which the care loop is exercised.

### Responsibility
Owns the owner's view of the pet and the controls the care loop is exercised through.

### Rationale
NFR-003 requires mood and health status to be perceivable as text through each
platform's native accessibility API, without reliance on colour or pointer input, which
makes this surface a consumer of semantic state rather than a producer of pixels that
something else must interpret. CON-001 bounds the shell everything is built inside — a
single shared surface is what keeps one codebase viable for a team with no platform
specialists, and the runtime choice itself is a decision record rather than a behaviour
of this component.

Two of the six seams NFR-006 enumerates — rendering, and accessibility integration —
touch this component, and neither is held here. NFR-006 does not merely prefer them
inside the platform-adapter layer, it counts conditionals outside that layer against a
target of zero, and NFR-003's measure runs through three distinct native accessibility
stacks. So this component owns what the owner sees and what the pet's state means in
words, and reaches CMP-017 for both the surface it is painted onto and the native API
the words are announced through. That division is also what keeps the seam honest under
Q-3's staged rollout: the semantic content is written once, and only the adapter changes
when macOS and Linux follow Windows.

This component is also the only element an owner acts on, which is why FR-009's
enablement preference is read and changed from here even though CMP-014 owns it. A
preference with no owner-reachable writer is a feature permanently at its default.

Confidence is low: Q-8 — whether the Sleeping state is rendered to the owner — is
still_open, and it is a question about precisely this component's surface. No
requirement in the set renders Sleeping today.

## CMP-017 — Platform Adapter [#cmp-017]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | internal |
| Responsibility | Confines every platform-specific behaviour to one layer so the rest of the codebase stays platform-agnostic. |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [NFR-007](/guide/examples/tamagotchi/requirements/non-functional/#nfr-007), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002), [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003) |
| Depends on | [IF-023](/guide/examples/tamagotchi/design/interfaces/#if-023), [IF-024](/guide/examples/tamagotchi/design/interfaces/#if-024) |

The single named layer holding every platform-specific behaviour the application needs
— local data directory paths, file reads, atomic writes, log measurement and roll-over,
the byte-identical quarantine move, wall-clock and interval access, recurring-timer
access, native notification delivery, the host rendering surface, and native
accessibility exposure.

### Responsibility
Confines every platform-specific behaviour to one layer so the rest of the codebase
stays platform-agnostic.

### Rationale
NFR-006 is the most directly structural requirement in the set: it names a layer and
then counts violations of it — zero platform conditionals outside it — and enumerates
the seams it must hold, including the byte-identical quarantine move and the
across-close wall-clock interval derivation. CON-003 makes that boundary binding now,
while only Windows is being built, because a platform-exclusive API adopted anywhere
outside this layer forecloses a named target. NFR-005 and CON-002 add the other half:
this is the only component permitted to touch anything outside the process, and what it
touches is enumerable and contains no network client.

NFR-006's enumeration is taken in full rather than in part. Rendering and accessibility
integration are the two seams most easily left outside a layer like this one, because the
runtime appears to supply them and it is tempting to read "the runtime does it" as
"nobody has to own it". NFR-006 does not allow that reading — it counts platform
conditionals outside this layer against a target of zero — and NFR-003's measure runs
through three distinct native accessibility stacks (UI Automation, NSAccessibility,
AT-SPI). So both live here: this layer owns the host surface the owner-facing view is
drawn onto, and the exposure of the pet's mood expression and health status as text to
whichever native accessibility API the platform provides. CMP-016 supplies the semantic
content; this layer decides what each platform does with it. Requirements A-21 assumes each target
provides a usable native accessibility API, and NFR-003 is cited here for that reason.

Recurring-timer access is the third seam of the same kind, and it is named in the same
clause of NFR-006 as the clock: "wall-clock and timer access". The two are not one seam.
Reading the clock answers what time it is; a recurring timer drives the application
without being asked, and it is the machinery NFR-002 budgets by name at idle. So this
layer offers both, through separate contracts, and CMP-010 keeps what is genuinely its
own — the evaluation cadence's period, its coalescing rule, and when it starts and stops
— while consuming timer access from here rather than reaching for a platform timer
directly. Without that seam, CMP-010 could not observe an unavailable timer facility at
all, and NFR-006's zero-conditionals count would be violated by the one component whose
whole purpose is to be driven by the platform.

None of those three seams — the rendering surface, accessibility exposure and timer
access — is declared as an outward need on an external component, and the asymmetry with
the clock and the notification service is deliberate. It is not, however, a claim about
where the code runs. The design context names exactly two integration points, the OS
notification service and the platform wall clock, and this decomposition does not add to
that list; the file primitives this layer already offers are held on the same footing.
All three are real platform facilities that can be absent or not running in a given
session — NFR-003's measure runs through three distinct native accessibility stacks, and
AT-SPI on a CON-003 target is a service in its own right — and the contracts this layer
offers say so in their error modes. What keeps them out of the external component set is
the integration-point list this stage inherited, not a belief that there is no party on
the other end of the call.

The clock contract it offers returns a signed interval and applies none of the
non-positive-interval rules: FR-002's clamp belongs to CMP-004, FR-011's re-basing to
CMP-006 and FR-008's re-basing to CMP-005, and a clock that pre-corrected any of them
would defeat all three (requirements A-6, A-7).

## CMP-018 — OS Notification Service [#cmp-018]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | high |
| Boundary | external |
| Responsibility | Presents notifications the application posts to the owner on the host desktop. |
| Traces from | [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [NFR-005](/guide/examples/tamagotchi/requirements/non-functional/#nfr-005), [CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002) |

The host operating system's native local notification service, through which care
reminders reach the owner.

### Responsibility
Presents notifications the application posts to the owner on the host desktop.

### Rationale
FR-009 is the only requirement that crosses the process boundary out of the
application, and requirements A-19 records that reminders delivered through the host's local
notification service count as fully offline and do not violate CON-002 — there is no
push service and no network hop. Requirements A-21 assumes each target platform provides a usable
native notification API. Modelling the service as a component keeps the dependency
graph total and makes the one outbound edge in the system visible rather than implicit.

## CMP-019 — Host Wall Clock [#cmp-019]

| Field | Value |
| --- | --- |
| Type | component |
| Status | draft |
| Confidence | medium |
| Boundary | external |
| Responsibility | Supplies the host's current wall-clock time to the application. |
| Traces from | [FR-002](/guide/examples/tamagotchi/requirements/functional/#fr-002), [FR-011](/guide/examples/tamagotchi/requirements/functional/#fr-011), [NFR-001](/guide/examples/tamagotchi/requirements/non-functional/#nfr-001) |

The operating system's wall clock, the source of every timestamp and elapsed interval
the pet simulation reads, and an owner-movable one.

### Responsibility
Supplies the host's current wall-clock time to the application.

### Rationale
The whole product rests on elapsed real time measured across application closes, and
the design context names the platform wall clock as an integration point alongside the
notification service. Modelling it as a component gives the design's most delicate
assumption a place to live: requirements A-7 requires the host to expose backward movement
observably, as a non-positive interval, rather than silently smoothing it into a
slow-forward clock — an OS that smooths defeats both of requirements A-6's rules at once, FR-002's
clamp and FR-011's re-basing.

Confidence is medium for exactly that reason: requirements A-7 is an inherited assumption about this
external system's behaviour that no requirement in the set verifies.

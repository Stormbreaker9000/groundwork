<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/requirements/constraints/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Constraints

The 3 constraints from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## CON-001 — Runtime baseline overhead must leave headroom in the idle-footprint budget [#con-001]

| Field | Value |
| --- | --- |
| Type | constraint |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | analysis |

### Statement
The runtime or application shell the product is built on shall consume no more
than 40% of the idle-footprint budget while running an empty do-nothing
application — no more than 0.4% of one core and no more than 60 MB RSS against
the NFR-002 budget of 1% of one core and 150 MB RSS. The remaining 0.6% of a
core and 90 MB RSS is reserved as headroom for the pet application itself.

Any runtime or application shell whose baseline overhead alone — measured with
no pet logic running — exceeds that allowance is excluded from the design
space. A full Chromium/Electron-class shell is the stated example of an
excluded runtime. This constraint names no chosen runtime; the selection is
open question Q-4.

The screen depends normatively on the reference-machine specification recorded
by open question Q-5. Until Q-5 is answered, no candidate may be recorded as
having passed or failed this screen; a candidate measured against an
unrecorded baseline is unassessed, not admitted.

### Category
technical

### Bounds / Implemented by
Bounds NFR-002 (idle CPU and memory footprint of the always-on process).
NFR-002 states the measurable quality target on a scale; CON-001 is the
boundary on the design space that target implies — it removes runtime options
outright at selection time rather than being tuned toward afterwards.

### Rationale
The pet is an always-on background companion the owner is expected to leave
running all day. A runtime that consumes a meaningful share of the machine at
idle makes the daily-return habit feel like a cost, and owners will quit the
app between check-ins — breaking the attachment loop the product exists to
create. A shell whose empty baseline already exceeds the budget cannot be
brought under it by optimising pet code, so the boundary must be applied at
runtime-selection time.

The headroom allowance exists because that same argument holds for a shell
sitting just under the budget: the delivered application has to fit inside the
same 150 MB, so a screen with no allowance would admit a 149 MB shell that
makes NFR-002 unachievable before a line of pet code is written. The allowance
is set at two fifths because the delivered application adds to the empty shell
everything the pet actually is — sprite and mood-animation assets held in
memory, the decay scheduler, the persistence layer and its save buffer — and
because a shell's own footprint grows once it renders a real window rather than
nothing. 90 MB and 0.6% of a core is the smallest remainder that work can be
expected to fit in without measurement to argue from; the split is an
engineering judgement recorded as an assumption, not a stated figure, and is
one of the reasons this constraint is held at low confidence.

Which runtime is selected is open question Q-4 (owner: engineering); this
constraint deliberately asserts no positive choice.

### Fit Criterion
For any candidate runtime, an empty do-nothing application built on it and left
idle for 10 minutes on the reference machine consumes no more than 40% of the
NFR-002 idle budget: <=0.4% of one core and <=60 MB RSS. A candidate whose
empty-shell baseline exceeds either figure is excluded from selection and is
recorded as rejected in the runtime decision record.

The screen is executable only against a fixed reference-machine specification.
Until open question Q-5 records that specification, no candidate may be
recorded as having passed or failed this screen, and any candidate measured
against an unrecorded baseline counts as unassessed rather than admitted.

## CON-002 — Core pet simulation must operate fully offline [#con-002]

| Field | Value |
| --- | --- |
| Type | constraint |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | inspection |

### Statement
The application shall operate fully offline. No core pet-simulation
function — launch, offline-elapsed decay, the four care interactions,
mood expression, health progression, persistence, recovery, or care
reminders — may depend on an outbound network connection or a remote
service. Care reminders in particular are local notifications only.

### Category
technical

### Bounds / Implemented by
Bounds FR-001 (persist pet state — the store must be local, ruling out
cloud sync as the system of record), FR-009 (care-reminder
notifications — local delivery only, no push service), and NFR-005
(local-only handling of pet and owner data).

### Rationale
The pet, its history and its care record are personal local data
belonging to a single desktop owner, and the product promises the pet
is theirs and always there. A remote dependency would make the pet
unavailable exactly when the owner is offline — breaking the
daily-return habit through no fault of the owner — and would move
personal care data off the machine. This is an absolute boundary rather
than a reliability target: the core loop either works with the network
unplugged or it does not.

### Fit Criterion
With every network interface on the test machine disabled, 100% of core
pet-simulation function completes normally — launch, offline-elapsed
decay application, all four care interactions, mood display, health
progression, save, and recovery from a missing or corrupted save file.
Inspection of the core-path dependency graph finds 0 network client
libraries and 0 outbound socket or HTTP calls.

## CON-003 — No design decision may foreclose Windows, macOS or Linux [#con-003]

| Field | Value |
| --- | --- |
| Type | constraint |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | medium |
| Verification | inspection |

### Statement
The product shall target Windows, macOS and Linux desktop environments.
No design, dependency or platform-API decision may foreclose shipping on
any of the three, irrespective of which platforms are selected to ship
first. This constraint does not assert a v1 ship order.

### Category
environmental

### Bounds / Implemented by
Bounds NFR-006 (single-codebase support for all three desktop targets),
FR-009 (care-reminder notifications, whose delivery mechanism differs
per platform and must not be built on one platform's service alone),
and NFR-003 (keyboard and screen-reader operability, which must be
reachable through each platform's own assistive-technology stack rather
than a single vendor's).

### Rationale
All three desktop environments are named targets, and un-picking a
platform-exclusive dependency after it has spread through the codebase
costs far more than avoiding it up front. The boundary is on the design
space, not the release plan: which platforms ship in v1 (all three, or
Windows-first) is open question Q-3, owned by product, and is not
asserted here. Q-3's answer changes the ship order but not this
boundary, which holds either way.

### Fit Criterion
The application builds and its full care loop passes acceptance on
Windows, macOS and Linux from a single source tree. Design review of the
core path finds 0 platform-exclusive APIs, dependencies or file-path
assumptions that lack a documented working equivalent on the other two
targets.

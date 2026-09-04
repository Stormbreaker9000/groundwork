<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/requirements/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Project artifacts

The stage-level files that sit alongside the atomic artifacts: the vocabulary they are written in, what was assumed, and what is still open.
## Glossary [#glossary]

### Terms
- **Baseline overhead**: The idle footprint of a candidate runtime or application shell running an empty do-nothing application, before any pet logic is added. The figure CON-001 uses to exclude runtimes, because it is a floor that pet-code optimisation cannot lower. *Also: empty-shell baseline.*
- **Care loop**: The four owner interactions that maintain the pet — feed, play, clean, and put to sleep — taken together as the interaction the accessibility and cross-platform targets are measured against.
- **Committed state**: A persisted pet state whose write completed in full, leaving the file complete and internally consistent as written. Committed status is established at write time; integrity validation at read is how a reader confirms it, not what creates it. A state whose write was interrupted is never committed, regardless of what bytes reached disk. *Also: committed save, last committed save.*
- **Core pet-simulation function**: The set of behaviours the pet cannot exist without — launch, offline-elapsed decay, the four care interactions, mood expression, health progression, persistence and recovery. The scope CON-002's offline boundary binds; explicitly opt-in extras such as telemetry fall outside it. *Also: core loop.*
- **Decay**: The reduction of a pet's stat values over elapsed real time, applied whether or not the application was running. *Also: stat decay.*
- **Default pet**: The pet state the application initializes when no committed state is available — a pet at health status Healthy, in the Awake state, with every pet stat at its configuration-defined starting value, no sleep-entry timestamp, and no accumulated care or lifecycle history. It is the state FR-010 and FR-012 produce, and the outcome NFR-004's measure is written to exclude wherever a committed state survived.
- **Disposition**: What the system does with a pet's accumulated state once that pet has reached the terminal end-of-life status — retain it permanently, archive it, or clear it and start a fresh pet. The undecided subject of Q-2.
- **Health status**: The pet's position on the neglect progression, distinct from its stat values — Healthy, Sick, or the terminal end-of-life status. Stat values vary gradually as they decay and are restored by care actions; health status is a discrete label that advances only under sustained neglect and is never restored by a single care action. *Also: Healthy, Sick.*
- **Idle footprint**: The CPU and resident-memory consumption of the application while in the idle steady state. *Also: idle budget.*
- **Idle steady state**: The application running with the pet alive and the window open, receiving no owner input and with no care action in progress; the operating mode NFR-002's footprint budget is measured in.
- **Integrity validation**: The check applied to a save file when it is read, to establish that it is complete and internally consistent before its contents are treated as a committed state. A file that cannot be read, is truncated, or fails the check does not pass validation. The mechanism is implementation-defined and depends on the storage format (Q-4).
- **Last-saved timestamp**: The wall-clock timestamp written into a pet state at the moment of its save, dating that write. It is the origin FR-002 measures the offline-elapsed interval from and the field that identifies which committed state a launch restored. *Also: last-save timestamp, last committed save's timestamp.*
- **Local data directory**: The single per-platform directory the application owns for its own persisted files; the save file's expected storage location sits within it, and the quarantine location is a separate location alongside it. The concrete path is platform-specific and is resolved in the platform-adapter layer. *Also: application data directory.*
- **Mood expression**: The pet's displayed emotional state, selected by FR-007 from the mood-threshold band containing the pet's lowest stat value. Distinct from health status — mood expression tracks current stat values and moves freely in both directions with care and decay, whereas health status advances only under sustained neglect.
- **Mood-threshold band**: One of a set of stat-value ranges that determines which mood expression is displayed for the pet at a given moment.
- **Neglect period**: The span of unbroken time a pet must remain in the sick state with at least one pet stat left below its neglect threshold, unremedied, before it reaches the terminal end-of-life status. It is the Sick-to-terminal instance of the sustained-neglect duration. Its numeric value is unfixed pending decay-curve tuning (Q-1). *Also: further defined duration.*
- **Neglect threshold**: The stat value at or below which a single pet stat counts as neglected, evaluated independently per stat. Crossing it is FR-009's notification trigger and starts the clock on a sustained-neglect duration; being raised back above it stops that clock for that stat alone. Each stat has its own threshold value, unfixed pending Q-1.
- **Pet stat**: One of exactly three integer-valued care values on a single shared scale — hunger, happiness, and hygiene — each of which decays with elapsed wall-clock time, is raised by its corresponding care action, and has its own neglect threshold. *Also: stat, stats.*
- **Pet state**: The complete set of values the application persists for a single pet and restores at launch — every pet stat value, the health status, the Awake/Sleeping state field, and the sleep-entry timestamp where the pet is Sleeping, together with the last-saved timestamp that dates the write. It is what FR-001 persists in full, what a committed state contains, and what a default pet is one particular instance of. *Also: pet's state, the current pet state.*
- **Pet-state evaluation**: An occasion on which the system reads the current wall clock and re-derives the pet's state from it — applying elapsed decay, advancing health status, and testing the wake deadline. It occurs at launch and, while the application is running, on the implementation's own cadence; no requirement in this set fixes that cadence (Q-10). *Also: pet-state check, neglect-progression check.*
- **Platform-adapter layer**: The single named module that holds every platform-specific behaviour (data directory paths, clock access, native notifications, accessibility integration), so the rest of the codebase stays platform-agnostic.
- **Quarantine**: Moving an unreadable or corrupt save file aside — preserved, not deleted — so a fresh default pet can start without the bad file being retried or silently overwritten. The quarantine location is the separate local storage location the file is moved to. *Also: quarantine location.*
- **Reference decay model**: An executable specification of the intended decay curve, kept independent of the production implementation and used as the correctness oracle for FR-002 and NFR-001 while the balance values remain open.
- **Reference machine**: The single agreed baseline hardware and OS specification against which idle CPU and memory footprint are measured. Not the owner's machine — a fixed measurement target so footprint figures are comparable between builds and between candidate runtimes. The specification itself is not yet recorded (Q-5). *Also: reference spec.*
- **Reference progression model**: The authoritative specification of health-status transitions under sustained neglect — which threshold breaches count, how long each must persist, and the resulting Healthy/Sick/terminal sequence. It is the test oracle for FR-008 and is distinct from the reference decay model, which specifies stat-value curves over elapsed time and says nothing about health status. *Also: progression model.*
- **Sleep duration**: The span of elapsed wall-clock time, measured from the pet's sleep-entry timestamp, after which the pet returns to the Awake state. It is FR-011's entire wake trigger. Its numeric value is unfixed pending Q-1. The interval is computed under the non-positive-interval rule FR-002 applies, and FR-011 additionally re-bases the sleep-entry timestamp to the current time at any evaluation where that interval computes as non-positive, so the deadline is re-anchored rather than deferred.
- **Sleep-entry timestamp**: The wall-clock timestamp recorded when a pet enters the Sleeping state, persisted as part of pet state and used as the origin from which the sleep duration is measured. FR-011 re-bases it to the current time at any evaluation where the interval since it computes as non-positive. It is absent while the pet is Awake. *Also: sleep-entry time.*
- **Sleeping state**: A discrete pet state entered by the sleep care action and exited when the defined sleep duration has elapsed, distinct from Awake — the pet's default state, which it occupies at all times other than while sleeping. The Sleeping state does not alter stat decay. *Also: Awake, Awake state.*
- **Soft reset**: One candidate disposition for a terminal pet — the owner is given a fresh default pet rather than the terminal state being permanent. Named in Q-2 as a possibility under consideration, not as a chosen behaviour.
- **Stat unit**: One increment on the pet's stat scale — the unit in which NFR-001's +/-1 decay tolerance is expressed. Applies uniformly to every stat in the pet's stat set, whose membership and names are fixed by the Pet stat entry.
- **Sustained-neglect duration**: The span of unbroken time at least one pet stat must remain below its neglect threshold before health status advances one step. Two instances exist — Healthy to Sick, and Sick to the terminal end-of-life status (the latter is the Neglect period). Both values are unfixed pending Q-1.
- **Terminal end-of-life status**: The final health status a pet reaches after sustained unremedied neglect, at the end of the Healthy to Sick to terminal progression. Named neutrally because what follows it — permanence or a soft reset — is an open product question (Q-2) that no requirement in this set answers. *Also: terminal status, death.*

## Assumptions [#assumptions]

### Assumptions
- A-1: A single local desktop owner per installation. No multi-user, account, server, or operator role applies anywhere in the set.
- A-2: The pet has exactly three care stats — hunger, happiness and hygiene — each integer-valued on a single shared scale, bounded to a defined min/max, and raised by its corresponding care action by a fixed configuration-defined increment capped at the maximum. The source context named four interactions and "stat thresholds" generically but never named the stats or their mapping to actions.
- A-3: Quarantining an unreadable save file means moving or renaming it to a separate local location, not deleting it, so it stays available for diagnosis and cannot collide with the newly written default-pet save.
- A-4: A colorblind-safe palette plus shape and text redundancy is sufficient for v1; a user-tunable palette is out of scope, so no requirement demands one.
- A-5: The reference decay model and all balance values are placeholders pending Q-1, and are referenced as an oracle rather than hardcoded in any requirement.
- A-6: A non-positive elapsed interval between two wall-clock readings is handled by one of two rules depending on what the interval feeds. Where it drives a quantity it is clamped to zero elapsed time (FR-002, for decay). Where it drives a deadline the origin timestamp is additionally re-based to the current time (FR-011, for the wake deadline), because clamping alone defers a deadline without bound rather than bounding it.
- A-7: The platform exposes a wall clock whose backward movement is observable to the application as a non-positive interval, rather than silently smoothing it into a slow-forward clock. Both rules in A-6 trigger on observing that non-positive interval, so an OS that smooths defeats both.
- A-8: The pet leaves the Sleeping state on elapsed sleep duration rather than by an owner-initiated wake action. The source context fixes the interaction set at four actions and says nothing about how sleep ends; a fifth owner action would exceed that set.
- A-9: The mood display reduces the three stats to a single band by taking the lowest stat value. The source context states no reduction rule; FR-007 fixes it normatively because a mean would let one critically low stat hide behind healthy ones.
- A-10: Neglect progression is driven by at least one stat below its own threshold, not by all stats simultaneously. Inferred from the per-stat threshold semantics in FR-009 and carried consistently into FR-008 and BR-001.
- A-11: The source context's 200 fault-injection trials are apportioned as 100 missing-save and 100 corrupted-save trials — a partition, not a duplication, so neither FR-010 nor FR-012 over-claims the original budget.
- A-12: Energy is not a pet stat. No requirement reads or writes it; it was vestigial vocabulary and has been removed rather than justified by inventing energy-consumption and energy-restoration rules.
- A-13: CON-001's 40% headroom allowance is an engineering judgement, not a stated or measured figure. It exists because a screen with no allowance would admit a shell consuming almost the whole budget while empty, making NFR-002 unachievable before any pet code is written. To be re-derived against real measurement once Q-4 and Q-5 close.
- A-14: NFR-009's 250 ms p95 budget assumes a whole launch should land inside roughly one second to read as uninterrupted, and that decay should be a minor share of that. The apportionment is reasoned, not elicited; if a total launch budget is ever stated, the figure should be re-derived from it.
- A-15: NFR-004's discriminating measure assumes single-generation retention is sufficient, because atomic commit means an interrupted write never replaces the already-committed file. Residual gap — a file validly committed and damaged afterwards by media- or filesystem-level corruption has no prior generation and resolves to quarantine plus a default pet. Tracked as Q-9.
- A-16: NFR-008's 5x scaling ratio is calibrated against a tick-loop failure mode, which at 30-day-versus-1-hour arms would show roughly 720x. The 5x ceiling is a deliberately generous band that rejects that shape without over-constraining a closed-form implementation carrying fixed per-call overhead.
- A-17: The offline-decay computation is reachable as an independently invocable unit — a function from starting pet state and elapsed interval to decayed pet state — separately from the launch sequence that calls it. NFR-008's measure is only executable if it can be called and repeated without starting the application. A testability constraint on the design, cheap to honour, but an assumption rather than a given.
- A-18: NFR-008's measure is assumed to run under a harness-level wall-clock timeout. A tick-loop implementation makes the measurement slow rather than failing, so a timeout converts that runtime blowup into a prompt failure signal. A harness-construction concern, not a change to the requirement.
- A-19: Care reminders delivered through the host operating system's local notification service count as fully offline and do not violate CON-002, even where that OS service can deliver over a network for other applications.
- A-20: Telemetry the owner has explicitly opted into falls outside core pet-simulation function and is therefore not a CON-002 violation. The offline boundary binds the core loop, not an opt-in extra.
- A-21: Each target platform provides a usable native notification API and a native accessibility API, so no target needs a bespoke assistive-technology implementation.
- A-22: The Pet state glossary entry is the single maintained enumeration of what the application persists. FR-001's completeness property ("0 fields absent") is decidable only against it, which makes the glossary normative rather than explanatory — a requirement introducing a new persisted field updates that entry rather than every fit criterion that would otherwise enumerate.
- A-23: A pet-state evaluation occurs while the application is running, on the implementation's own cadence. FR-007's mood update, FR-008's neglect progression and FR-011's wake all presuppose one, and no requirement asserts or bounds it. Tracked as Q-10.
- A-24: The old set's cap on decay at "the configured maximum offline interval" is not carried forward into this set. Its stated rationale — "uncapped decay over very long absences would guarantee death regardless of intent" — does not transfer to this set's neglect model. Decay magnitude is already scale-bounded independent of any cap (A-2's min/max bound on every pet stat, reinforced by FR-002 AC-2's requirement that even a 30-day interval decay without error or overflow), and health-status progression toward the terminal status is driven by sustained below-threshold duration per stat (FR-008), not by accumulated decay magnitude — so a magnitude cap would not change whether or when an absence reaches the terminal status. A long, closed-app absence in which a stat crosses its neglect threshold and stays unremedied for the defined duration is exactly the "sustained, unremedied neglect" BR-001 already treats as legitimate causation, as distinct from the "elapsed time alone" cause BR-001 rules out; capping decay would not prevent that outcome, and reinstating a cap purely to blunt it would work against BR-001's own rationale for why the terminal status must carry real stakes. Residual concern about unbounded computation cost over very long intervals is covered separately by NFR-008's scaling bound and the closed-form assumption (A-16, A-18), not by a decay cap. Whether offline elapsed time is reconstructed retrospectively against the neglect-duration clock, versus accruing only while the app is running, is a detail of the pet-state-evaluation mechanism already tracked at Q-10, not a separate gap.

### Dependencies
- D-1: A reference decay model must exist as an executable oracle independent of the production implementation — stat curves over elapsed time, the oracle for FR-002 and NFR-001.
- D-2: A reference progression model must exist as a separate executable oracle — health-status transitions under sustained neglect, the oracle for FR-008. Distinct from D-1, which says nothing about health status.
- D-3: Platform-native accessibility stacks and screen readers (UI Automation/NVDA on Windows, NSAccessibility/VoiceOver on macOS, AT-SPI/Orca on Linux) are required to verify NFR-003 on each target.
- D-4: An OS-level network capture facility is required to verify NFR-005's zero-outbound-connection assertion.
- D-5: A fault-injection harness able to kill the process at randomized points, including mid-write, is required for NFR-004, FR-010 and FR-012.
- D-6: CI runners for all three desktop operating systems are required for NFR-006's "passes unmodified on all three" measure.
- D-7: OS per-process CPU and RSS accounting is required to verify NFR-002.
- D-8: An automated accessibility scanner appropriate to the eventual UI technology is required for NFR-003's zero-critical-violations measure; the choice depends on the still-open runtime decision (Q-4).
- D-9: A recorded reference-machine specification (Q-5) is a hard precondition for verifying NFR-002's and NFR-009's absolute figures, and CON-001's exclusion screen inherits it. NFR-008 deliberately does not depend on Q-5 and is the only time-behaviour target executable before it closes.
- D-10: CON-001 makes Q-4 (runtime selection) unresolvable until Q-5 (reference machine) is answered, since no candidate may be recorded as passing or failing the exclusion screen before then. A scheduling dependency between two engineering-owned questions, surfaced rather than resolved.
- D-11: Q-1 supplies every balance value the set defers — the feed/play/clean increments, the mood-threshold band boundaries, each stat's own neglect threshold, both sustained-neglect durations (Healthy-to-Sick and Sick-to-terminal), and the sleep duration. Every fit criterion referencing a "defined" value is unconstructible until Q-1 lands.
- D-12: Neither BR-001 nor BR-002 can leave low confidence until product resolves Q-2. BR-002 is scoped explicitly to the interim and should be revisited — replaced or retired — the moment Q-2 lands.
- D-13: Q-3 fixes the v1 test-matrix and acceptance scope. CON-003's design boundary holds regardless of the answer.
- D-14: Q-4 fixes the concrete local-storage mechanism and file format underlying FR-001, FR-012 and the Integrity validation definition.
- D-15: Q-7 is the tracking artifact for the Maintainability deferral. Until it is answered the set carries no explicit modularity or modifiability target beyond NFR-006's platform-seam measure and NFR-007's analysability support.
- D-16: CON-002 and CON-003 together depend on each target platform exposing a local notification service and an assistive-technology API that function with no network connection. Believed true of all three; not verified, Linux desktop environments especially.

### Open Questions
- Q-1: What is the exact decay-curve and balance tuning — rates, thresholds, increments, both sustained-neglect durations, and the sleep duration? (owner: product/design)
- Q-2: Is the terminal end-of-life status permanent, or a configurable soft reset? No requirement in this set answers it; FR-008, BR-001 and BR-002 all deliberately decline to. A candidate constraint on the answer, recorded but not asserted: whether a disposition must be surfaced to the owner. (owner: product)
- Q-3: Which platforms ship in v1 — all three, or Windows-first? (owner: product)
- Q-4: Which framework/runtime is chosen given the footprint constraint (Electron vs Tauri vs native)? Note D-10 — this cannot be closed before Q-5. (owner: engineering)
- Q-5: What is the reference-machine specification against which the idle-footprint budget and launch-latency figures are measured? Surfaced by the critique; NFR-002, NFR-009 and CON-001 all name it normatively and none can be executed until it is recorded. (owner: engineering)
- Q-6: What are the release, auto-update and rollback strategies for desktop distribution? Recorded as a deferral rather than an inapplicability, and the tracking artifact for the Deployability gap. (owner: engineering)
- Q-7: Should v1 carry explicit maintainability targets (modularity / modifiability), given that Q-1's decay-balance tuning is a live, ongoing loop? (owner: engineering)
- Q-8: Should the Sleeping state be rendered to the owner? Sleep is currently owner-imperceptible across the whole set — FR-006 is authored honestly on that basis and held at low confidence. (owner: product)
- Q-9: Should committed saves be retained for two generations, to survive post-commit media corruption? See A-15 — the residual gap NFR-004 does not claim to cover. (owner: engineering)
- Q-10: How often does the running application re-evaluate pet state, and what bounds that interval? Nothing in the set establishes that a pet-state evaluation occurs while the application is running — FR-007, FR-008 and FR-011 all presuppose one; none asserts one exists or bounds its cadence. FR-011's backward-clock bound is therefore relative to an event of unbounded arrival, so "bounded, and never stranded" is only as strong as a cadence no requirement fixes. Not raised as a defect against FR-011: the gap sits identically under FR-011 AC-1/AC-2 and FR-008, so amending FR-011 would repair one of three sites. NFR-002's idle-CPU budget constrains the cadence from the other side. (owner: engineering)

### Recommendations recorded, not authored
- R-1: Two-generation retention of committed saves (tracked as Q-9). NFR-004's measure is satisfiable by atomic commit alone and does not cover a file committed validly then damaged by media-level corruption. Not a hole in BR-002 — BR-002 forbids the system discarding state, and a failing disk is not the system acting. Stands on cost/benefit; needs a functional home plus an FR-012 fallback clause.
- R-2: Owner visibility of a terminal-pet disposition. Deliberately removed from BR-002's normative statement because requiring it would pre-commit Q-2 — it would rule out a silent soft reset, which Q-2 may legitimately choose. Recorded as a candidate constraint on Q-2's answer.
- R-3: A set-wide wall-clock interval rule. Would need to carry BOTH rules in A-6 plus a discriminator (clamp where the interval feeds a quantity whose non-advance is safe; re-base the origin where it feeds a deadline whose non-arrival is the hazard). A clamp-only set-wide rule would have propagated FR-011's defect to every future deadline. Not proposed as an artifact — it needs a home nothing in the current set provides.
- R-4: FR-001 fit-criterion wording. "Equal to their pre-close values" is measured at restore, before launch-time decay (FR-002) and wake re-evaluation (FR-011) are applied — the only reading under which FR-001 and FR-002 have ever been consistent. The critic judged this not a defect and explicitly directed that no revise round be spawned for it. If FR-001 is ever reopened, fold in "as restored, before launch-time decay and wake evaluation are applied".

## Definition of done [#definition-of-done]

> **M1 STUB** — generated by the `dod-generator` agent from the requirements in
> `.sdlc/requirements/`. This is a foundational checklist; **M3 (STO-104)**
> expands it into the full Definition of Done generator. Edit the source
> requirement files (not this file) and regenerate to keep gates in sync.

- **Project / feature:** Tamagotchi Virtual Pet
- **Generated:** 2026-08-25
- **Derived from:** 12 functional + 9 non-functional requirements
- **Scope:** project (`scope` / `parent_scope` reserved for future agile slicing — STO-104)

A work item is **Done** only when **every** gate below is satisfied. Gates are
derived mechanically from the requirement set: do not hand-edit; update the
source requirement and regenerate.

### 1. Functional Acceptance Gates
*Derived from each functional requirement's EARS description, Gherkin acceptance
criteria, and `fit_criterion`. One gate per FR; the linked file holds the
authoritative, executable acceptance criteria.*

- [ ] **FR-001 — Persist pet state on stat change and app close** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-001-persist-pet-state-on-stat-change-and-app-close.md` pass.
  Fit criterion: Every field of the pet state held at close round-trips unchanged: across 50 restart cycles, 100% of persisted fields are present in the restored state and equal to their pre-close values, with 0 fields absent and 0 fields differing. The fields under test include, and are not limited to, every pet stat value, the health status, the Awake/Sleeping state field, the sleep-entry timestamp wherever the pet is Sleeping, and the last-saved timestamp.
  Verification: test.

- [ ] **FR-002 — Apply offline-elapsed decay at launch** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-002-apply-offline-elapsed-decay-at-launch.md` pass.
  Fit criterion: For elapsed intervals from 1 minute to 30 days, the decay applied at launch is within +/-1 stat unit of the reference decay model, verified across a test matrix of representative intervals; for elapsed intervals at or below zero, including a system clock set behind the last committed save's timestamp, the computed decay is exactly zero and 0% of trials show any stat value higher after launch than at the last committed save.
  Verification: test.

- [ ] **FR-003 — Feed the pet** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-003-feed-the-pet.md` pass.
  Fit criterion: The hunger stat increases by the configured feed increment (or is unchanged if already at maximum) in 100% of feed action invocations in acceptance tests.
  Verification: test.

- [ ] **FR-004 — Play with the pet** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-004-play-with-the-pet.md` pass.
  Fit criterion: The happiness stat increases by the configured play increment (or is unchanged if already at maximum) in 100% of play action invocations in acceptance tests.
  Verification: test.

- [ ] **FR-005 — Clean the pet** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-005-clean-the-pet.md` pass.
  Fit criterion: The hygiene stat increases by the configured clean increment (or is unchanged if already at maximum) in 100% of clean action invocations in acceptance tests.
  Verification: test.

- [ ] **FR-006 — Put the pet to sleep** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-006-put-the-pet-to-sleep.md` pass.
  Fit criterion: The pet's state field equals Sleeping immediately after the sleep action is selected while the pet was previously Awake, in 100% of interaction tests; the state field remains Sleeping and unchanged if the action is selected again while already Sleeping.
  Verification: test.

- [ ] **FR-007 — Display mood expression tracking stat thresholds** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-007-display-mood-expression-tracking-stat-thresholds.md` pass.
  Fit criterion: The displayed mood expression matches the expression mapped to the band containing the pet's lowest stat value in 100% of sampled states, across a test matrix that spans every defined band and includes states in which the individual stats fall in different bands. Band boundaries are taken from the Q-1 balance values and are not fixed by this requirement.
  Verification: test.

- [ ] **FR-008 — Progress sustained neglect toward a terminal health status** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-008-progress-sustained-neglect-toward-a-terminal-health-status.md` pass.
  Fit criterion: Health status transitions Healthy -> Sick when at least one stat has remained below its neglect threshold continuously for the defined sustained-neglect duration, and Sick -> the terminal end-of-life status when at least one stat remains below its neglect threshold for the further defined duration, matching the reference progression model in 100% of scripted neglect-duration test cases; 0% of cases advance health status when no stat has been below its threshold for the full duration, including cases where a stat drops below and recovers within the window. Behavior after the terminal status is reached is explicitly out of scope for this requirement pending Q-2 and is not exercised by these cases.
  Verification: test.

- [ ] **FR-009 — Present optional local care-reminder notifications** (should): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-009-present-optional-local-care-reminder-notifications.md` pass.
  Fit criterion: When notifications are enabled and any stat crosses its defined neglect threshold, a local OS-level notification is presented in 100% of test trials; zero notifications are presented, and zero network requests are made, when the feature is disabled.
  Verification: test.

- [ ] **FR-010 — Initialize a default pet when no save file is present** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-010-initialize-a-default-pet-when-no-save-file-is-present.md` pass.
  Fit criterion: Across 100 missing-save fault-injection trials, the application launches with a valid default pet in 100% of trials, 0% result in a crash or unhandled error, and 0% create a quarantine artifact.
  Verification: test.

- [ ] **FR-011 — Wake the pet from the Sleeping state** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-011-wake-the-pet-from-the-sleeping-state.md` pass.
  Fit criterion: Across scripted trials sampling the boundary at +/-1 second, the pet's state field equals Sleeping at every sample before the defined sleep duration has elapsed and equals Awake at the first sample at or after it, in 100% of trials; this holds in 100% of trials where the duration elapses entirely while the application is closed, and 0% of trials leave the pet in the Sleeping state once the duration has elapsed. Across backward-clock trials injected at points spanning the sleep interval, with backward jumps of 1 hour, 1 day and 30 days and no forward correction applied, 100% of trials wake the pet no later than one sleep duration after the first pet-state evaluation that follows the backward clock change. The sleep duration is the Q-1 balance value, not a value fixed by this requirement.
  Verification: test.

- [ ] **FR-012 — Quarantine a save file that fails integrity validation** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-012-quarantine-a-save-file-that-fails-integrity-validation.md` pass.
  Fit criterion: Across 100 corrupted-save fault-injection trials, 100% of the original files are found byte-identical at the quarantine location afterward, 0% are deleted or overwritten in place, 100% of trials launch with a valid default pet, and 0% result in a crash or unhandled error.
  Verification: test.

### 2. NFR Fitness Gates
*Derived from each non-functional requirement's six-part quality attribute
scenario (QAS). The **response measure** is the pass/fail oracle; the
`verification_method` is how it is confirmed.*

- [ ] **NFR-001 — Offline-elapsed decay matches the reference decay model** (must): meets response measure —
  For at least 20 log-spaced intervals across 1 minute to 30 days, each resulting stat is within ±1 stat unit of the reference decay model's value for the same interval and starting state; 0 out-of-range results. For at least 5 non-positive intervals (T = 0 and T < 0), each stat after launch equals its last-committed value exactly — 0 stats increased and 0 stats decayed.
  — for the QAS *The application launches after an elapsed interval T since the last committed save, where T may be positive or, if the wall clock has moved backward, zero or negative* on *The offline decay computation and the pet state model* under *Normal operation; the positive matrix spans T from 1 minute to 30 days, and the clock-regression matrix covers T at exactly zero and T negative (manual clock change, DST shift, NTP correction); a valid save file is present; elapsed time is derived from wall-clock timestamps*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-001-offline-elapsed-decay-matches-the-reference-decay-model.md`.

- [ ] **NFR-002 — Idle CPU and memory footprint of the always-on process** (must): meets response measure —
  On the designated reference machine, mean CPU <= 1% of one core and peak resident memory <= 150 MB across the 10-minute window; no monotonic growth — final RSS within 5% of the RSS sampled at the 1-minute mark. A run on any machine other than the recorded baseline is not evidence either way.
  — for the QAS *The application sits in an idle steady state — pet alive, window open, no owner input, no care action in progress* on *The complete delivered runtime — the application process, any child or helper processes, and whatever rendering or background timer machinery the chosen implementation uses* under *The project's designated reference machine under normal desktop use (specification pending Q-5); a continuous 10-minute observation window; measurements taken from OS process accounting and summed across every process the application owns*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-002-idle-cpu-and-memory-footprint-of-the-always-on-process.md`.

- [ ] **NFR-003 — Keyboard-only and screen-reader operability of the full care loop** (must): meets response measure —
  100% of interactive controls keyboard-reachable and operable with a visible focus indicator; 100% of mood and health states carry a non-color-dependent textual equivalent exposed to the accessibility API; contrast >= 4.5:1 for text and >= 3:1 for non-text state indicators; zero critical or serious violations from an automated accessibility scan; a scripted screen-reader walkthrough of all four care actions completes with 0 unlabeled or unreachable controls.
  — for the QAS *The owner navigates to and performs each of the four care actions — feed, play, clean, put to sleep — and reads the pet's current mood and health state* on *The application user interface — all interactive controls, focus order and focus indication, the mood expression, and any status or notification surface* under *Normal operation, on each supported desktop platform using that platform's native accessibility stack and screen reader*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-003-keyboard-only-and-screen-reader-operability-of-the-full-care-loop.md`.

- [ ] **NFR-004 — Crash-safe atomic persistence and recovery** (must): meets response measure —
  200 fault-injection trials yield 100% launches into a valid pet state, 0 corrupt loads, 0 unhandled exceptions. In 100% of those trials where a committed state existed before the kill, that committed state is the state restored; recovery to a default pet occurs in 0% of such trials. 50 clean restart cycles restore the exact prior state 100% of the time.
  — for the QAS *The process is killed at an arbitrary point in its lifetime, including part-way through writing the save file* on *The state persistence layer and the save file on local disk* under *Normal operation with fault injection, covering saves triggered both by a stat change and by application close; local disk, no network involved*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-004-crash-safe-atomic-persistence-and-recovery.md`.

- [ ] **NFR-005 — Local-only handling of pet and owner data** (must): meets response measure —
  0 outbound TCP, UDP or DNS attempts attributable to the application across a >= 30 minute capture that exercises every functional requirement in this set; 100% of those requirements pass with the network interface disabled; pet and owner data written only inside the application's local data directory and its quarantine location; any future opt-in telemetry path is off by default and inert until explicitly enabled by the owner.
  — for the QAS *The owner exercises every functional requirement in this set — the four care actions, wake, save and load, offline decay, mood display, sickness and terminal progression, local reminders, default-pet initialization, and save-file quarantine — with no opt-in granted* on *The whole application process, its dependencies, its local data directory, and the quarantine location* under *Normal operation on a machine with all traffic captured at the OS network interface, including a run with the network interface disabled entirely*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-005-local-only-handling-of-pet-and-owner-data.md`.

- [ ] **NFR-006 — Single-codebase support for all three desktop targets** (must): meets response measure —
  The acceptance suite for every functional requirement in this set passes unmodified on all three platforms in CI — the quarantine move and the across-close interval derivation included, not excepted; 0 platform conditionals outside the platform-adapter layer; 0 recorded design decisions that foreclose any of the three targets.
  — for the QAS *The same source tree is built, packaged and run on Windows, on macOS, and on Linux* on *The whole codebase, and in particular the platform-touching seams — local data directory paths; the quarantine location and the byte-identical file move into it (FR-012); wall-clock and timer access, including the elapsed-interval derivation across an application close; native notifications; accessibility integration; and rendering* under *Current supported OS versions of each of the three targets; the v1 ship order is deliberately not fixed by this requirement*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-006-single-codebase-support-for-all-three-desktop-targets.md`.

- [ ] **NFR-007 — Local diagnostic logging of decay and lifecycle events** (should): meets response measure —
  100% of decay computations and lifecycle transitions produce exactly one such record; replaying >= 100 recorded decay events through the reference model reproduces each logged post-state with 0 mismatches; total log size stays under a fixed rotation cap indefinitely; 0 outbound transmissions of log content.
  — for the QAS *A decay computation runs, or a lifecycle transition occurs — launch, save, load, save-file quarantine, mood change, onset of sickness, terminal transition, sleep and wake* on *The local diagnostic log on disk* under *Normal operation at the default log level, with no network available*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-007-local-diagnostic-logging-of-decay-and-lifecycle-events.md`.

- [ ] **NFR-008 — Offline-decay computation cost does not scale with the length of the absence** (must): meets response measure —
  Over at least 20 runs per arm, p95 computation time for a 30-day elapsed interval is <= 5x the p95 for a 1-hour elapsed interval, both measured on the same machine in the same session over the same starting state. One run is the total time of a batch of >= 1,000 repetitions divided by the repetition count, with the batch size raised until the short-arm batch total exceeds 10 ms, so neither arm is taken near the platform timer resolution.
  — for the QAS *The decay computation is invoked directly with a starting pet state and an elapsed interval, at the two interval lengths the comparison uses — 1 hour, and the 30-day worst case — and each invocation is repeated within one measurement session* on *The offline-decay computation as an independently invocable unit — the function that maps a starting pet state and an elapsed interval to a decayed pet state* under *Any single development or CI machine, with both arms measured in the same session on the same hardware so the comparison is internal; no save file is read and no application launch occurs; no reference-machine specification required*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-008-offline-decay-computation-cost-does-not-scale-with-the-length-of-the-absence.md`.

- [ ] **NFR-009 — Offline-decay computation time on the launch path** (should): meets response measure —
  For a 30-day elapsed interval, the computation completes in <= 250 ms at p95 and <= 500 ms at maximum across 20 cold-start runs on the designated reference machine. The measure is not evaluable until Q-5 records that machine's specification; a measurement taken against an unrecorded baseline is unassessed, not passing.
  — for the QAS *Launch occurs after a 30-day offline interval, requiring the full elapsed decay to be computed and applied before the pet can be shown* on *The offline-decay computation on the launch path, between the completion of the committed-save read and the first render of the pet* under *Cold start on the project's designated reference machine (specification pending Q-5) under normal desktop use, with a valid committed save file present and no other application load contrived*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-009-offline-decay-computation-time-on-the-launch-path.md`.

### 3. Test Coverage Expectations
- [ ] Every `must` / `should` FR above has at least one automated test mapped to
  its acceptance criteria (Gherkin → executable test), recorded in the FR's
  `traces_to.tests`.
- [ ] Every NFR with `verification_method: test` has an automated fitness check
  asserting its QAS response measure: NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, NFR-007, NFR-008, NFR-009.
- [ ] NFRs with `verification_method` of `inspection` / `analysis` /
  `demonstration` have a recorded, signed-off evidence artifact: none.
- [ ] No FR/NFR marked `must` remains without a corresponding test or evidence
  link (no dangling `traces_to`). **Flagged as currently unmet:** every requirement
  in this set has an empty `traces_to.tests`, including all `must`-priority
  requirements — FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008,
  FR-010, FR-011, FR-012, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006,
  NFR-008, CON-001, CON-002, CON-003, BR-001, BR-002.

### 4. Documentation Requirements
- [ ] Public-facing behavior described by `must` FRs is documented (user/API
  docs as applicable): FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007,
  FR-008, FR-010, FR-011, FR-012.
- [ ] Operational NFRs (security, reliability, observability, deployability) have
  runbook / config notes: NFR-004 (reliability), NFR-005 (security), NFR-006
  (deployability), NFR-007 (observability).
- [ ] `.sdlc/requirements/` is current: every implemented requirement has
  `status: implemented` (or `verified`) and populated `traces_to.code`.
- [ ] Architecture-significant decisions are captured as ADRs referenced from the
  relevant requirements' `traces_to.design`.

### 5. Deployment / Operational Readiness
- [ ] Security NFR gates pass before release: NFR-005.
- [ ] Reliability / availability NFR targets are met or have an accepted waiver:
  NFR-004.
- [ ] Observability is in place (logs / metrics / traces) for the response
  measures asserted above.
- [ ] Applicable constraints (`CON-*`) and business rules (`BR-*`) are honored in
  the deployed configuration: CON-001, CON-002, CON-003, BR-001, BR-002.
- [ ] Rollback / cutover path exists for any transition-tier requirement.

---
*This file is generated. Do not edit by hand — change the requirement files in
`.sdlc/requirements/` and re-run the `dod-generator` agent. M3 (STO-104) will
replace this stub with scope-aware, CI-enforceable gates.*

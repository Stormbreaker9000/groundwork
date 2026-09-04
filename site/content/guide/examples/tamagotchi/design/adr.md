<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/design/adr/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Architecture decision records

The 7 architecture decision records from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## ADR-001 — Permanent terminal end-of-life status [#adr-001]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | high |
| Traces from | [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002), [BR-001](/guide/examples/tamagotchi/requirements/business-rules/#br-001), [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008) |

### Context and Problem Statement

The terminal end-of-life status is named neutrally in the glossary precisely because what follows it was undecided, and BR-002 froze the question: until it was settled, no terminal pet's accumulated state could be discarded and no disposition could be implemented at all, because whichever answer was taken had to become a single project-wide policy applied consistently. BR-001 constrains the same boundary from the other side by requiring that the terminal status arise only from sustained unremedied neglect and never from an application fault, and FR-008 owns the transition that reaches it. The decision had to be taken before the health-progression path could be decomposed, because a disposition — had one been selected — would have needed an owner, a trigger and a write path of its own.

### Decision Drivers

- BR-002
- BR-001
- FR-008

### Considered Options

#### Permanent terminal status with no disposition

- Pros: Gives BR-002 the single project-wide policy it requires the answer to take, and keeps the emotional weight that makes the daily-return habit carry stakes. The design needs no disposition component at all: the terminal status becomes a health status the progression can reach and nothing downstream consumes, which is why BR-002's prohibition survives as a structural property rather than as a rule someone must remember to keep.
- Cons: An owner who loses a pet after one bad week has no in-product recovery, which is the abandonment risk the alternative existed to mitigate.

#### Configurable soft reset to a fresh default pet

- Pros: Mitigates abandonment by giving the owner a way back after a terminal outcome, and was the option BR-002 was written to keep reachable.
- Cons: Requires a disposition to exist as an implemented behaviour with its own owner and write path, and a configurable one introduces a second lifecycle path alongside the terminal one, which is what BR-002's single-project-wide-policy clause was written to prevent from proliferating.

### Decision Outcome

The terminal end-of-life status is permanent. There is one terminal lifecycle path, no reset setting, and no disposition that discards a terminal pet's accumulated state. The terminal status is therefore a health status the progression can reach and nothing downstream is permitted to consume, which is what turns BR-002's prohibition into a structural property of the decomposition rather than a discipline every future writer of persisted state must remember.

#### Consequences

- Good:
  - BR-002 gets the single project-wide policy its fit criterion requires the answer to take, and the count of terminal-pet disposition implementations stays at zero by construction.
  - No disposition component is needed anywhere in the decomposition, so no path exists that could discard or overwrite a terminal pet's accumulated state.
  - The emotional weight that makes the daily-return habit carry stakes is retained.
- Bad:
  - Forecloses the configurable soft reset the question held open, and accepts the abandonment risk that option existed to mitigate — an owner who loses a pet after one bad week has no in-product recovery.
  - BR-002 was written to keep both answers reachable; taking the permanent answer spends that optionality.

## ADR-002 — Windows-first platform staging for v1 [#adr-002]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | high |
| Traces from | [CON-003](/guide/examples/tamagotchi/requirements/constraints/#con-003), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [FR-009](/guide/examples/tamagotchi/requirements/functional/#fr-009), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012) |

### Context and Problem Statement

CON-003 requires that no design, dependency or platform-API decision foreclose any of the three desktop targets, and it says explicitly that it asserts no ship order — so the ship order was left as a separate decision to take. It is a real decision because the v1 acceptance surface differs enormously between the two answers: NFR-003's measure runs a scripted screen-reader walkthrough through each platform's own native accessibility stack, FR-009's delivery path rests on each platform's native notification API, and FR-012's byte-identical quarantine move has different file-move semantics on each target. NFR-006's zero-conditionals-outside-the-adapter-layer count is the measure that most depends on the answer, because it is only checkable against a second platform.

### Decision Drivers

- CON-003
- NFR-006
- NFR-003
- FR-009
- FR-012

### Considered Options

#### Windows ships first for v1, with macOS and Linux staged after it

- Pros: Concentrates the v1 acceptance surface on one platform's accessibility stack and one set of path and file-move semantics, which is what a team with no dedicated platform specialists can actually verify.
- Cons: The cross-platform boundary still binds in full while only one target is being built, so the platform-adapter seam earns nothing measurable at v1 and a seam drawn wrong stays undetected until the staged targets arrive.

#### All three desktop targets ship at v1

- Pros: The zero-conditionals measure and the cross-platform acceptance run are checkable from the start, so an adapter seam drawn in the wrong place is found while it is still cheap to move.
- Cons: Triples the v1 acceptance surface — three native accessibility stacks, three notification APIs and three sets of file-move semantics — against a team constraint of no dedicated platform specialists.

### Decision Outcome

Windows ships first for v1; macOS and Linux are staged after it. The staging changes the ship order only: CON-003's boundary is unaffected by it, so the platform-adapter seam is still drawn now, in full, while only one target is being built.

#### Consequences

- Good:
  - Concentrates the v1 acceptance surface on one platform's accessibility stack and one set of path and file-move semantics, which is what a team with no platform specialists can actually verify.
- Bad:
  - CON-003's boundary still binds in full while only one target is being built, so the platform-adapter seam earns nothing measurable at v1.
  - NFR-006's zero-conditionals-outside-the-layer measure has no second platform to be checked against until after v1, so a seam drawn wrong stays undetected until then.

## ADR-003 — Tauri as the desktop runtime and shell [#adr-003]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | medium |
| Traces from | [CON-001](/guide/examples/tamagotchi/requirements/constraints/#con-001), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002), [NFR-006](/guide/examples/tamagotchi/requirements/non-functional/#nfr-006), [NFR-003](/guide/examples/tamagotchi/requirements/non-functional/#nfr-003), [FR-001](/guide/examples/tamagotchi/requirements/functional/#fr-001), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012) |

### Context and Problem Statement

CON-001 excludes whole runtime families from the design space at selection time rather than tuning a figure afterwards: any candidate whose empty-shell baseline alone exceeds 40% of the idle-footprint budget is excluded, with a full Chromium/Electron-class shell named as the stated excluded example. That makes the runtime a boundary on the shell everything else is built inside — it is settled before any component exists and cannot be revisited by optimising component code. NFR-006 constrains the same choice from the other side by requiring one shared codebase across three targets, and NFR-003 requires native accessibility integration on each. The choice also fixes the storage mechanism that FR-001's persistence and FR-012's integrity validation are defined over, and it sets the floor under NFR-002's idle budget.

### Decision Drivers

- CON-001
- NFR-002
- NFR-006
- NFR-003
- FR-001
- FR-012

### Considered Options

#### Tauri — a Rust core with an OS-supplied system webview

- Pros: The exclusion screen is passable on published baselines because the webview is supplied by the OS rather than bundled, and a single shared codebase stays viable for a team with no platform specialists. It also fixes the storage mechanism the rest of the design needed — a JSON save file written by atomic write-then-rename — which is what lets integrity validation and the atomic-replace contract be specified at all.
- Cons: Rendering and native accessibility both land on a shared webview, which is why both had to be pulled explicitly back inside the platform-adapter layer rather than being allowed to ride the runtime.

#### An Electron-class shell bundling a full Chromium runtime

- Pros: The most familiar shell for a single shared codebase across three desktop targets, with the widest ecosystem and the least platform-specific work.
- Cons: Rejected on its empty-shell baseline: a bundled full Chromium runtime is the stated excluded example of a candidate whose baseline alone consumes more than the allowance the exclusion screen permits.

#### A native view per platform

- Pros: The lowest achievable baseline overhead, and the most direct route to each platform's own native accessibility stack.
- Cons: Rejected on the team constraint: it abandons the single shared codebase outright and needs a dedicated specialist per platform, which the team does not have.

### Decision Outcome

Tauri — a Rust core with an OS-supplied system webview — is selected, rejecting an Electron-class shell on its empty-shell baseline against the exclusion screen, and native-per-platform on the team constraint. The selection is being built on, but it is provisional against measurement rather than settled by it: the exclusion screen cannot be executed until a reference machine is recorded, so the rejection rests on published baselines rather than on this project's own. The unexecuted screen and the missing runtime decision record are the subject of ADR-007 and are deliberately not merged into this record, which documents a decision that was taken.

#### Consequences

- Good:
  - The empty-shell exclusion screen is passable on published baselines, and the Electron-class candidate is excluded on the figure the constraint names.
  - A single shared codebase across all three desktop targets stays viable for a team with no platform specialists, which is the constraint that ruled out native-per-platform.
  - Fixes the storage mechanism the persistence path needed — a JSON save file written by atomic write-then-rename — which is what lets integrity validation and the atomic-replace contract be specified at all.
- Bad:
  - The selection rests on published baselines rather than on this project's own measurement, because no reference machine has been recorded — so the exclusion is asserted rather than executed, and the runtime decision record the constraint requires does not yet exist.
  - Every downstream footprint argument inherits that provisionality, including the evaluation cadence period and the per-tick cost of the timer seam.
  - Puts rendering and native accessibility on a shared webview, which is why both had to be pulled explicitly back inside the platform-adapter layer rather than being allowed to ride the runtime.

## ADR-004 — Single committed generation of the save file [#adr-004]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | high |
| Traces from | [NFR-004](/guide/examples/tamagotchi/requirements/non-functional/#nfr-004), [FR-012](/guide/examples/tamagotchi/requirements/functional/#fr-012), [BR-002](/guide/examples/tamagotchi/requirements/business-rules/#br-002), [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002) |

### Context and Problem Statement

NFR-004's discriminating clause requires that where a committed state existed before a kill, that committed state is the one restored, and that recovery to a default pet occurs in 0% of such trials. The question is what supplies that guarantee: an atomic write primitive alone, or an atomic write plus a retained previous generation to fall back to. Retention interacts with FR-012, because the fallback path for a file that fails integrity validation is quarantine plus a default pet, and with BR-002, whose preservation clause is about not losing accumulated state. It also interacts with NFR-002, because a rotation is more idle I/O and disk than a single write per commit.

### Decision Drivers

- NFR-004
- FR-012
- BR-002
- NFR-002

### Considered Options

#### One committed generation retained

- Pros: A simpler store contract and one write per commit rather than a rotation, and less idle I/O and disk against the footprint budget. Atomic write-then-rename already prevents an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure actually exercises.
- Cons: Post-commit media corruption has no second generation to fall back to and resolves to quarantine plus a default pet — total loss of accumulated state.

#### Two committed generations retained, the previous kept as a fallback

- Pros: Survives post-commit media corruption of the live file, which is the one failure class atomicity does not cover, and was the residual gap the requirements stage recommended against accepting.
- Cons: A rotation rather than one write per commit, on a write path whose frequency is a function of the evaluation cadence, so it spends idle I/O and disk against the footprint budget; and it widens the store contract and the set of paths that write or replace persisted pet state.

### Decision Outcome

One committed generation of the save file is retained, not two. The argument rests on atomic write-then-rename already preventing an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure is written to exercise — leaving only post-commit media corruption uncovered.

#### Consequences

- Good:
  - A simpler store contract, one write per commit rather than a rotation, and less idle I/O and disk against the footprint budget.
  - Atomic write-then-rename already prevents an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure actually exercises.
- Bad:
  - Post-commit media corruption has no second generation to fall back to; it resolves to quarantine plus a default pet, which is total loss of accumulated state, and BR-002's preservation clause is then satisfied only in the weak sense that the corrupt bytes are preserved at the quarantine location.
  - The atomicity the whole argument rests on is a property of the platform and is not detectable from inside the atomic-replace contract, which concedes this as an error mode of its own.
  - The requirements stage recorded this as a residual gap and recommended against it; taking the one-generation answer accepts that gap for v1.

## ADR-005 — Storage of the per-stat below-threshold clock [#adr-005]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | low |
| Traces from | [FR-008](/guide/examples/tamagotchi/requirements/functional/#fr-008) |

### Context and Problem Statement

The undecided question is unchanged and remains genuinely undecided: FR-008 needs a per-stat below-threshold clock running unbroken across an application close, the glossary's Pet state entry — the single maintained enumeration of what is persisted — carries no such field, and whether that clock is reconstructed from the decay curve at each evaluation or introduced as a new persisted field is tracked under an open question. The health-progression component and its contract both state the deferral in their own confidence notes rather than papering over it, and the progression operation deliberately exposes no way to read that clock precisely because its existence is undecided. The coverage that does exist is real: health status has exactly one writer, which carries the deadline rule in its operation summary and consumes the wall clock directly so the rule is named at its own point of consumption, and the running-cadence half now obtains its tick from inside the adapter layer. None of that settles the storage decision, which the requirement's own significance calls structural and not settled by any requirement.

### Decision Drivers

- FR-008

### Considered Options

#### Reconstructed from the decay curve at each evaluation

- Pros: Adds no field to the maintained enumeration of what is persisted, so the persisted field set, the round-trip measure and the field set integrity validation must account for all stay as they are; and no backward-clock observation becomes a mutation of persisted state.
- Cons: Makes the neglect clock a function of the decay curve, so any re-tuning of the balance parameters silently rewrites how long a pet has already been neglected — a balance change that quietly moves a health-status transition. It also leaves the deadline rule with little to act on, since an origin derived from the current stat value cannot read as being in the future.

#### Introduced as a new persisted pet-state field

- Pros: The clock is an explicit recorded origin rather than a derived quantity, so it is independent of the decay curve and survives a re-tuning of the balance parameters unchanged.
- Cons: Adds a field to the single maintained enumeration of what is persisted, widening the component's field set, the round-trip measure and the field set validation must account for; and because the deadline rule re-bases the origin, every backward-clock observation becomes a mutation of persisted pet state, which is a new class of write on a path the business rules require to be inspected exhaustively.

### Decision Outcome

Pending. No option has been chosen. The question is owned by engineering and is tracked as open question Q-11, the design-side refinement of the still-open cadence question Q-10 that governs it; the decomposition is correct under either answer, which is why the decision could be deferred rather than forced. The claim most worth re-examining when it is taken is the progression contract's assertion that the deadline rule survives either answer.

#### Consequences

- None — the decision is pending.

## ADR-006 — Pet-state evaluation cadence period [#adr-006]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | low |
| Traces from | [NFR-002](/guide/examples/tamagotchi/requirements/non-functional/#nfr-002) |

### Context and Problem Statement

The undecided question is the evaluation cadence period — still open — measured against a budget that is itself not evaluable until a reference machine is recorded, also still open. NFR-002's own measure concedes it: not evaluable until the reference machine is recorded. The scheduler component and its contract are at low confidence for exactly this reason and both say so. The partial coverage is worth naming and it improved this round without moving the verdict: the period is isolated in one component so it can be tuned against the budget without touching what an evaluation does; the scheduler's overrun mode coalesces ticks rather than queueing them, so a slow evaluation cannot accumulate a backlog that spends the budget; the refresh contract coalesces redraws for the same reason and no longer re-announces on every tick regardless of change; and the background timer machinery the measure budgets by name now has a contract of its own that defends the budget at its own boundary, rejecting a non-positive or sub-resolution period rather than coercing it to the fastest tick the host can deliver. What remains undecided is the parameter itself, and it cannot be decided inside the artifact set.

### Decision Drivers

- NFR-002

### Considered Options

- None — no alternatives are recorded yet.

### Decision Outcome

Pending. No value has been chosen and no discrete options have been recorded, because what is undecided is a parameter rather than a choice among named alternatives. The question is owned by engineering and is tracked as open question Q-12, the design-side refinement of the still-open cadence question Q-10, now that the period is a named parameter on the platform recurring-timer contract rather than an unstated implementation detail. It is the sharpest parameter in the design: shorten it and the wake, the neglect progression and the mood update all become prompt while the idle budget is spent on the exact machinery the requirement names; lengthen it and the budget is safe while every time-driven behaviour becomes stale. The flip cannot be measured today, only argued, because the budget that would bound it from the other side is not evaluable until a reference machine is recorded.

#### Consequences

- None — the decision is pending.

## ADR-007 — Runtime baseline-overhead exclusion screen and its decision record [#adr-007]

| Field | Value |
| --- | --- |
| Type | adr |
| Status | draft |
| Confidence | low |
| Traces from | [CON-001](/guide/examples/tamagotchi/requirements/constraints/#con-001) |

### Context and Problem Statement

The undecided question is the reference machine. CON-001's exclusion screen is a measurement on a reference machine that has not been recorded, and the design context says so outright: the screen has not actually been executed, and the selection is provisional against measurement rather than settled by it. Nothing in the artifact set can address this and nothing should try — the constraint is settled before any component exists, it is a boundary on the shell everything else is built inside, and CON-001 additionally requires a runtime decision record naming the rejected candidates, which is an ADR rather than a component. It is deferred with no partial coverage to name: two components cite the constraint in their traces_from, but a citation is not coverage. The corresponding runtime selection is recorded as ADR-003, with its provisionality stated as a consequence there.

### Decision Drivers

- CON-001

### Considered Options

- None — no alternatives are recorded yet.

### Decision Outcome

Pending. No option has been chosen, and none can be recorded here yet, because what is outstanding is the execution of a measurement rather than a choice among candidates. The question is owned by engineering and is tracked as open question Q-13; it cannot be closed until the still-open reference-machine question Q-5 records a specification to measure against. Until then the runtime selection in ADR-003 rests on published baselines rather than on this project's own measurement, and the constraint's own rule is that a candidate measured against an unrecorded baseline counts as unassessed rather than admitted. This record is the runtime decision record the constraint mandates; it cannot record a pass or a fail against the exclusion screen until the reference machine lands.

#### Consequences

- None — the decision is pending.

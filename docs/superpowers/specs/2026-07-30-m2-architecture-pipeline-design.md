# M2 Architecture Generation Pipeline — Design

**Issue:** STO-99
**Date:** 2026-07-30
**Status:** approved

The M2 analogue of STO-96. Defines the architecture stage: a `design` skill that
interviews for what requirements cannot carry, and a multi-agent pipeline that turns a
validated requirement set into atomic component and interface specs under `.sdlc/design/`.

STO-197 defined the contract these agents emit against. This ticket builds the agents.
STO-100 (ADRs) and STO-101 (C4 diagrams) plug into dispatch slots declared here.

---

## Part A — Settled decisions

Seven decisions were taken during brainstorming. Each closes off an alternative that will
look attractive again later, so each is recorded with its reasoning.

### A.1 This ticket is the pipeline plus the `CMP`/`IF` specialists — not ADRs, not C4

The STO-99 ticket lists "ADR generation, C4 model output" among its specialists. STO-100
and STO-101 own those artifacts and are separate issues in this milestone.

This spec resolves the contradiction in favour of the other tickets, the same way STO-197
resolved its own Deliverables-versus-Boundaries conflict: **one owner per artifact.**

STO-99 ships `SKILL.md`, the orchestrator, the component and interface specialists, the
critic, and the formatter — and declares the `adr-generator` and `c4-generator` dispatch
slots with their hand-off shapes stubbed. STO-100 and STO-101 each add an agent and a
dispatch line rather than renegotiating the pipeline.

**Consequence, accepted:** the stage ships without ADRs or diagrams. It still produces a
validator-green, end-to-end useful artifact set — components, interfaces, `assumptions.md`,
`drivers.md`.

### A.2 The stage runs its own interview

The requirement set **cannot** carry the technology context architecture needs. That is by
construction, not by omission: `lint_requirements_content.py` treats implementation bias as
a defect and the critic flags it. Nothing in `.sdlc/requirements/` says "Tauri" or
"Postgres", and nothing should.

So the design stage either asks or invents. The project's own history settles which: the
first tamagotchi build took an unexamined Electron recommendation and paid to rip it out
later. That is the failure mode at the requirements layer, and an architecture stage that
picks a runtime silently reproduces it one layer up.

The interview covers six areas requirements cannot hold — runtime and stack, persistence,
deployment target, integration points, operational constraints, team constraints — and
produces a `design_context` that serialises 1:1 into the orchestrator, exactly as
`clarification_context` does in M1.

**Consequence, accepted:** the stage is conversational, not a one-shot batch job. It cannot
be run unattended. That is the same trade M1 made deliberately.

### A.3 The authoring cycle is broken by capabilities, then back-fill

The STO-197 schema creates a circular authoring dependency that M1 never had. A component
declares `depends_on: [IF-…]`; an interface declares `provider: CMP-…`. Neither specialist
can finish before the other starts. M1's specialists only ever traced *backwards* to
already-allocated IDs, so this is genuinely new.

The break:

1. The **component specialist** decomposes and declares each component's `required_capabilities`
   in prose — no `IF-` IDs. `depends_on` is left empty.
2. The **interface specialist** receives the component set, turns every capability into an
   `IF-` with a `provider`, and reports `consumed_by` and `satisfies_capabilities`.
3. The **orchestrator** back-fills `depends_on` mechanically and drops the transient fields.

Architecture judgment stays entirely in the specialists. The orchestrator wires and never
decides. The edge is authored exactly once — by the interface specialist — and stored in
the schema's canonical slot.

The rejected alternative was giving the orchestrator the whole graph. It wires most cleanly
and extends M1's "single ID authority" to "single graph authority" — but deciding the
decomposition *is* the architecture work, and M1's orchestrator is explicitly the agent that
does no domain work. Extending its remit that far would make the specialists typists.

A single combined architecture specialist was also rejected: it abandons the
specialist-per-concern thesis that M1 validated, and one agent holding both concerns
under-specifies the interfaces, which are the easy half to skimp.

A review of this spec caught a hole the break above does not close on its own: nothing
stops a component specialist from declaring a capability nothing in the component set can
provide. The interface specialist would then have no `provider` to name, and the only
re-dispatch target in Stage 7 for a zero-match capability is the interface specialist
itself — which would go looking for the same missing provider and report the same gap
forever. That is decided here rather than by adding an escalation contract: the component
specialist is the only agent that both declares capabilities and owns the component set,
so it is the only one that can guarantee every capability it declares has a provider in its
own output — usually by emitting the `boundary: external` component the capability implies,
the same move the `context.integration_points` sweep already makes for named external
systems. **Consequence, accepted:** if the component specialist still violates this — a
prompt failure, not a structural one — the interface specialist cannot invent a provider or
a re-dispatch path; it reports the contract violation plainly, and it surfaces at the human
sign-off gate rather than looping.

### A.4 The back-fill carries a completeness check, and it is load-bearing

Every `required_capability` must appear in exactly one interface's `satisfies_capabilities`.
Zero matches means the interface specialist dropped a dependency; two means a duplicated
contract. Either re-dispatches.

This check is not optional bookkeeping. Without it a dropped edge is **invisible** — the
artifacts still validate, because `depends_on: []` is legal frontmatter. The output would be
structurally perfect and quietly wrong.

That is the same failure class the STO-197 spec flagged for `unevaluatedProperties`: shipped
code was correct, but nothing would have noticed if it were not. Here the check is what
notices.

### A.5 The critic is anchored in ISO/IEC/IEEE 42010 and ATAM

M1's critic holds up because it is anchored: INCOSE/ISO 29148 per requirement, ISO 25010 for
coverage, plus a deterministic lint and the validator as a hard gate. M2 needs the analogue,
not a hand-written checklist that cannot answer "why these checks and not others".

- **42010** is the direct architecture analogue of 29148 — it governs what an architecture
  description must contain.
- **ATAM** is the established method for asking whether an architecture satisfies its
  quality-attribute scenarios, which is exactly the shape M1's NFRs are already written in.
  The six-part QAS the NFR specialist emits is an ATAM input with no conversion.

The critic runs two phases: per-artifact quality (42010) and ASR coverage with tradeoffs and
sensitivity points named (ATAM-lite). It does **not** run `validate_design.py` — an
end-to-end run of the pipeline surfaced why that cannot work here even though M1's critic runs
its analogous validator directly. Two reasons, not one:

- The critic runs **before** the formatter, by the pipeline's own design — nothing is written
  to `.sdlc/design/` until the critic returns `gate: pass`. Pointing the validator at a
  directory that does not exist yet exits 2 unconditionally, failing the gate on every run
  regardless of how sound the architecture is.
- `drivers.md`'s gated headings — Architecturally Significant Requirements, Tradeoffs,
  Sensitivity Points — **are** the critic's own Phase 2 output. It cannot validate a file built
  from findings it is still in the middle of producing; the dependency is circular by
  construction.

The structural gate belongs where the files actually exist: at `design-formatter`, which
writes them and immediately re-runs `validate_design.py` against the real on-disk output,
reporting the result as `formatter_result.validator_rerun`. That run is the pipeline's one
structural gate; a non-zero exit is a hard failure that re-opens the critique loop rather than
a second, earlier check duplicating it.

**Scope discipline:** the critic does not resolve `traces_from` (STO-102) and does not detect
cycles, orphan interfaces, or vague prose (STO-208). Those tiers exist; this one does not
duplicate them.

### A.6 Architectural drivers are persisted to `drivers.md`

The ASR analysis, the tradeoffs, and the sensitivity points are precisely the class of
reasoning this project already decided to externalise rather than let the model bake
silently into artifact prose — the argument that justified `assumptions.md` (research Gap 5).
Leaving them in the conversation loses them at the moment they become checkable.

`.sdlc/design/drivers.md` is gated on three headings: `## Architecturally Significant
Requirements`, `## Tradeoffs`, `## Sensitivity Points`. Content is never gated.

The inherited open questions the interview resolves land under `## Tradeoffs` (see A.7 and D.7).
They are the clearest instance of the reasoning this decision exists to preserve: the runtime,
the platform scope and the death policy are the most consequential calls the stage makes, and
without this they would live only in the interview transcript.

Folding these into `assumptions.md` was rejected: it conflates *what this design assumes*
with *what drove this design*, and it would have required extending the existing three-heading
gate anyway — so it saves no validator work and costs clarity.

**Consequence, accepted:** this touches `validate_design.py`, shipped one commit ago. The
cost is one skip-list entry, one gate calling the already-generalised `_check_project_artifact`,
and a fixture pair. STO-209 is already slated to touch both validators; this is not the only
such change coming.

### A.7 M1's uncertainty is inherited and routed, not blocked on

M1 emits a `review_queue` of low-confidence requirements in `index.yaml` and `Q-` open
questions in `assumptions.md`. The tamagotchi run ended with Q-4 open: *which framework given
the footprint constraint — Electron, Tauri, or native?*

That is not a defect in the requirements. It is an architecture decision that landed in the
right place. So:

- Phase 1 reads both, and the interview **opens** with the inherited open questions.
- Resolved ones become design decisions (and, once STO-100 ships, ADRs).
- Resolved ones are also **written down**: each becomes a tradeoff entry under `## Tradeoffs`
  in `.sdlc/design/drivers.md` — the resolution as the decision, the interview's reasoning as
  its gains and costs, and the requirements that rested on the question as `affected`. Without
  that they vanish with the conversation, which is exactly what A.6 exists to prevent.
- Unresolved ones propagate: any `CMP`/`IF` resting on one is marked `confidence: low`, and
  the question is re-emitted into `.sdlc/design/assumptions.md` with its original `Q-` ID.

Blocking the stage until the review queue empties was rejected as backwards: it would demand
that architecture decisions be made before the stage that makes them.

**Entry gate, stated precisely:** Phase 1 requires `validate_requirements.py` to exit 0. That
is a *structural* check. It does **not** require an empty review queue — a set with five
low-confidence items and four open questions passes and carries them forward.

---

## Part B — Pipeline shape

```
design_context  (from the interview)
        │
        ▼
[ design-orchestrator ]   read requirement set → identify ASRs
                          → allocate CMP/IF blocks → generation_brief
        │
        ├──► [ component-specialist ]  → draft_components  (+ required_capabilities)
        │              │
        │              ▼  (orchestrator forwards the component set)
        └──► [ interface-specialist ]  → draft_interfaces  (+ consumed_by)
        │
        ▼  orchestrator BACK-FILLS depends_on, drops transient fields
[ design-critic ]   42010 per-artifact + ATAM-lite ASR coverage
                    (judgment only) → critique_report
        │
        ▼  on pass: orchestrator synthesises assumptions + drivers
[ design-formatter ]   CMP/IF files + assumptions.md + drivers.md + index.yaml
                    + validate_design.py hard gate (the structural gate)
        │
        ▼
   [adr-generator]  ← STO-100 slot        [c4-generator]  ← STO-101 slot
```

Dispatch order is fixed and **serial**: component specialist before interface specialist,
because the latter needs the component set to assign `provider` and resolve capabilities.
This is the M2 analogue of M1's constraint specialist running last so it can trace to
concrete IDs.

Five agent files under `agents/`, following M1's flat-directory convention:
`design-orchestrator`, `component-specialist`, `interface-specialist`, `design-critic`,
`design-formatter`.

The two unfilled slots are declared in `design-orchestrator` as named post-formatter stages
with their trigger condition and expected return stated, and marked as owned by STO-100 and
STO-101. Declaring them costs a paragraph and means those tickets add an agent plus a
dispatch line instead of reopening the pipeline's shape.

Collapsing the formatter into the orchestrator was rejected: M1's orchestrator never writes
to disk — it plans, allocates, and routes — and breaking that invariant in the second stage
that copies it would also hand the STO-100/101 slots back to an agent with two jobs.

---

## Part C — Skill phases

`skills/design/SKILL.md`, mirroring the M1 skill with the interview retargeted.

| Phase | What happens |
| --- | --- |
| **1. Locate and read the input** | Find `.sdlc/requirements/`. Run `validate_requirements.py` as an entry gate. Read the requirement files, `index.yaml`'s `review_queue`, and `assumptions.md`'s open questions. Scan an existing codebase if present. |
| **2. Hypothesise** | Propose a candidate decomposition and a stack hypothesis in a single message — the same one-question shape as M1 Phase 3. |
| **3. Architecture interview** | Six coverage areas: runtime/stack, persistence, deployment target, integration points, operational constraints, team constraints. Opens with the inherited open questions (A.7). Numbered options preferred, as in M1. |
| **4. `design_context` synthesis** | Render the context block and confirm. Hard stop until the user confirms. |
| **5. Generate** | Run the pipeline, render an in-conversation summary foregrounding the low-confidence triage list, **sign-off gate**, write files, `validate_design.py` hard gate, commit. |

No files are written before sign-off. That M1 invariant is preserved exactly.

---

## Part D — Hand-off contracts

The orchestrator owns these shapes, as in M1.

### D.1 `design_context` — interview → orchestrator

```yaml
design_context:
  requirements_root: ".sdlc/requirements"
  system_purpose: string             # restated from the requirement set, not re-elicited
  runtime_and_stack: string
  persistence: string
  deployment_target: string
  integration_points: string         # external systems → boundary: external components
  operational_constraints: string
  team_constraints: string
  out_of_scope: string               # or "None identified"
  inherited_open_questions:
    - id: Q-4                        # ID preserved from requirements/assumptions.md
      statement: string
      disposition: resolved | still_open
      resolution: string             # present only when resolved
  inherited_review_queue: [ NFR-002, CON-001 ]
```

Preserving the `Q-` IDs is deliberate: a question resolved here traces back to the
requirement that raised it, and one still open keeps its identity when re-emitted into the
design `assumptions.md`.

### D.2 `generation_brief` — orchestrator → specialist

```yaml
generation_brief:
  context: { ...full design_context... }
  requirements_digest:               # the FULL requirement set, not just the ASRs.
                                     # The orchestrator reads the files once; specialists never re-read.
                                     # asr_analysis marks the significant subset within it — the
                                     # component specialist still needs every FR to decompose against.
    - id: NFR-002
      type: non_functional
      title: string
      description: string
      measure: string                # fit_criterion (FR), response measure (NFR), or a CON/BR's
                                      # own fit_criterion where it states one — omitted when the
                                      # requirement genuinely has no measure
      priority: must | should | could | wont
      confidence: high | medium | low
  terms:                              # inherited verbatim from requirements/glossary.md — the design
                                     # stage does not author vocabulary, only consumes it (STO-197 A.2)
    - term: string
      definition: string
      aliases: [ string ]
  asr_analysis: [ ...see D.3... ]
  target_category: component | interface
  id_block: { prefix: CMP | IF, start: 1 }
  created_at: "YYYY-MM-DD"
  component_set: [ ... ]             # INTERFACE BRIEF ONLY: components + their capabilities
```

The orchestrator is the single ID authority, as in M1. IDs are stable, never reused after
deletion (`status: obsolete` instead), and the categorical prefix must match `type` —
`CMP-`→`component`, `IF-`→`interface` — which the validator enforces.

`terms` closes a gap the schema left open: the orchestrator is the only agent that reads
`requirements/glossary.md` (A.2), and the specialists never re-read the requirement files, so
without this field the vocabulary inheritance STO-197 decided on would be silently broken —
two specialists free to coin different words for the same concept. Neither specialist gains a
`terms` *output*; the design stage consumes the glossary, it does not grow one of its own.

`measure` is likewise extended beyond FR/NFR: `requirements_digest` carries the full
requirement set, which includes `CON-` and `BR-` entries. For those, `measure` is their own
`fit_criterion` where one is stated, and the field is omitted where the requirement genuinely
has none.

### D.3 `asr_analysis` — the orchestrator's routing judgment

```yaml
asr_analysis:
  - requirement_id: NFR-002
    driver_type: quality_attribute | constraint | business_rule | high_impact_function
    significance: string             # why this one shapes structure
```

This is what the ATAM-lite critic checks coverage against and what lands in `drivers.md`.

### D.4 `draft_components` / `draft_interfaces` — specialist → orchestrator

Both carry the full STO-197 frontmatter contract plus a rendered body, mirroring M1's
`draft_requirements`. Fields marked **TRANSIENT** never reach a file.

```yaml
draft_components:
  - id: CMP-001
    type: component
    title: string
    description: string
    responsibility: string
    boundary: internal | external
    traces_from: [ FR-001, NFR-002 ]
    traces_to: { adr: [], diagrams: [], code: [], tests: [] }
    depends_on: []                   # left empty — the orchestrator fills it
    required_capabilities:           # ← TRANSIENT
      - capability: "take card payments"
        rationale: string
    status: draft
    confidence: high | medium | low
    created_at: "YYYY-MM-DD"
    body_markdown: |
      # ...rendered body...

draft_interfaces:
  - id: IF-001
    type: interface
    title: string
    description: string
    provider: CMP-002
    operations: [ { name, summary } ]
    interaction: synchronous | asynchronous
    error_modes: [ ... ]
    consumed_by: [ CMP-001 ]         # ← TRANSIENT, drives the back-fill
    satisfies_capabilities:          # ← TRANSIENT, proves nothing was dropped
      - { component: CMP-001, capability: "take card payments" }
    traces_from: [ ... ]
    traces_to: { adr: [], diagrams: [], code: [], tests: [] }
    status: draft
    confidence: high | medium | low
    created_at: "YYYY-MM-DD"
    body_markdown: |
      # ...rendered body...
```

### D.5 The back-fill algorithm

The orchestrator executes exactly this, and applies no judgment:

1. For each interface, for each `CMP` in `consumed_by`: append the `IF` ID to that
   component's `depends_on`. Deduplicate, sort.
2. **Completeness check (A.4).** Every `required_capability` must appear in exactly one
   interface's `satisfies_capabilities`. Zero matches → re-dispatch to the interface
   specialist with the gap attached. Two or more → re-dispatch as a duplicated contract.
3. Derive `capability_map` from the matches step 2 just made — one entry per
   `required_capability`: `{ component, capability, satisfied_by }`. This is free: step 2
   already walked every capability to completeness-check it, so this retains that mapping
   rather than discarding it. Then drop `required_capabilities`, `consumed_by`, and
   `satisfies_capabilities`. What remains is schema-shaped; `capability_map` never reaches
   a file either — it is forwarded to the critic as a sidecar (D.6) and goes no further.

### D.6 `critique_report` — critic → orchestrator

```yaml
critique_report:
  gate: pass | fail
  validator:
    command: "python3 skills/design/scripts/validate_design.py .sdlc/design"
    exit_code: 0
    summary: string
  per_artifact:
    - { id: CMP-001, verdict: pass | revise, findings: [ ...42010 notes... ] }
  asr_coverage:
    - requirement_id: NFR-002
      addressed_by: [ CMP-001, IF-001 ]
      verdict: addressed | deferred_to_decision | unaddressed
  tradeoffs:
    - { decision: string, gains: string, costs: string, affected: [ NFR-002, CON-001 ] }
  sensitivity_points:
    - { point: string, affected_requirements: [ NFR-002 ], note: string }
```

`unaddressed` fails the gate. `deferred_to_decision` passes but forces a `Q-` open question —
the honest disposition until STO-100 exists to write the ADR, and it means the deferral is
recorded rather than lost.

`validator` keeps its three fields, but its meaning changed from the original draft of this
spec (A.5): the critic does not run `validate_design.py` (nothing is on disk yet, and
`drivers.md`'s gated headings are the critic's own output), so it leaves `validator`
null/unset on the report it returns. The orchestrator fills it in afterward, once
`design-formatter` re-runs the validator against the files it actually wrote and reports the
result as `formatter_result.validator_rerun` (D.8) — that value is what `critique_report.validator`
records. Consumers of this contract see the same three fields either way; only who produced
the value, and when, changed.

Alongside the artifact set, the orchestrator also forwards the `capability_map` sidecar
derived in D.5 step 3:

```yaml
capability_map:
  - component: CMP-001
    capability: "take card payments"
    satisfied_by: IF-001
```

By Stage 8 the transient capability fields are already stripped, so without this sidecar the
critic could only judge an interface's `operations` against the interface's own
`description` — a comparison whose two sides were both written by the interface specialist.
`capability_map` lets it check `operations` against the capability a *different* agent, the
component specialist, declared, so agreement between them is real evidence rather than one
agent agreeing with itself. This is the same move M1's orchestrator makes forwarding `terms`
to `requirements-critic` (`requirements-orchestrator.md` Stage 6) for its glossary-coverage
check, since `glossary.md` does not exist yet at that stage — and it costs nothing here for
the same reason it costs nothing there: Stage 7 already builds this mapping to run its
completeness check, and now keeps it instead of throwing it away.

### D.7 `design_context_artifact` — orchestrator → formatter

Assembled **after** the critique gate, because the critic's tradeoffs and sensitivity points
are inputs to it rather than consumers of it. Same ordering argument STO-135 settled for the
glossary.

```yaml
design_context_artifact:
  assumptions:    [ { id: A-1, statement } ]      # architecture's own, e.g. single-writer DB
  dependencies:   [ { id: D-1, statement } ]
  open_questions: [ { id: Q-4, statement, owner } ]   # inherited IDs preserved + newly raised
  drivers:
    asrs:               [ { requirement_id, driver_type, significance } ]
    tradeoffs:          [ { decision, gains, costs, affected: [] } ]
    sensitivity_points: [ { point, affected_requirements: [], note } ]
```

`drivers.tradeoffs` is not only the critic's. Every `inherited_open_questions` entry the
interview closed with `disposition: resolved` becomes a tradeoff entry as well: `decision` is
the resolution taken, `gains` and `costs` the reasoning behind it, and `affected` the
requirement IDs that rested on the question, which the `inherited_review_queue` and the
requirements citing that `Q-` ID identify. Tradeoffs is the right heading — a resolved runtime
or scope question is a decision taken, with something gained and something paid — and the three
`drivers.md` headings are fixed by the validator, so it is also the only heading available.
A resolved question correspondingly does *not* reappear under `open_questions`; only
`still_open` ones carry forward there.

Empty sections render as `None identified`, as in M1. An honest empty section beats invented
entries.

### D.8 `formatter_result` — formatter → orchestrator

```yaml
formatter_result:
  files_written: [ ".sdlc/design/components/CMP-001-...md", ... ]
  index: ".sdlc/design/index.yaml"
  review_queue_count: 0
  context_artifact: ".sdlc/design/assumptions.md"
  drivers: ".sdlc/design/drivers.md"
  validator_rerun: { exit_code: 0 }
```

Mirrors M1's shape with `drivers` added. The orchestrator reports it to the skill, which owns
sign-off and commit. The orchestrator never commits.

---

## Part E — Output layout and the validator change

```
.sdlc/design/
├── components/     CMP-001-<kebab-title>.md
├── interfaces/     IF-001-<kebab-title>.md
├── adr/            ← STO-100, not written by this ticket
├── diagrams/       ← STO-101, not written by this ticket
├── assumptions.md  ← gated: ## Assumptions / ## Dependencies / ## Open Questions
├── drivers.md      ← gated: ## Architecturally Significant Requirements / ## Tradeoffs / ## Sensitivity Points
└── index.yaml      ← review_queue of every confidence: low artifact
```

`drivers.md` is new, so `validate_design.py` needs three edits. `_check_project_artifact` was
already generalised into `lib/artifact_core.py` by STO-197, which is what makes this cheap:

- `SKIP_FILENAMES` gains `"drivers.md"`. Without this, discovery would try to parse it as a
  `CMP-`/`IF-` artifact and fail — the same reason `assumptions.md` and `index.yaml` are
  already skipped.
- A `check_drivers_artifact` gate calling the shared helper with the three headings.
- `DRIVERS_ARTIFACT` exported alongside the existing constants, so STO-208's linter can
  import it the way `lint_requirements_content.py` imports `GLOSSARY_ARTIFACT`.

Headings are gated; content never is.

---

## Part F — Error handling and gates

In order of evaluation:

| Condition | Behaviour |
| --- | --- |
| No `.sdlc/requirements/` | Stop. Direct the user to the requirements workflow. |
| `validate_requirements.py` exits non-zero | Stop. Structurally invalid requirements cannot be designed against. |
| Capability with no possible provider | Prevented at the source: the component specialist must emit a provider (often `boundary: external`) for every capability it declares, so this state cannot arise from a correct decomposition. A violation is a contract breach, not a re-dispatchable gap — the interface specialist reports it plainly and it surfaces at the human sign-off gate rather than looping. |
| Unsatisfied or duplicated capability | Orchestrator re-dispatches to the interface specialist with the gap attached. Never silently accepted. |
| Any ASR `unaddressed` | Critic gate fails. Re-dispatch to the owning specialist. |
| ASR `deferred_to_decision` | Gate passes; a `Q-` open question is forced into `assumptions.md`. |
| Critic `gate: fail` or any `revise` | Re-dispatch only the affected artifacts, re-run the critic. Never advance to the formatter. |
| `validate_design.py` exits non-zero (run by `design-formatter`'s post-write re-run — the pipeline's structural gate, not the critic) | Hard block before commit. Re-open the critique loop with the validator's findings attached; re-dispatch, re-run the critic and the formatter until clean. |

---

## Part G — Testing

**Validator.** The only new executable code, and so the only place with unit tests. Two new
invalid fixture directories — `missing_drivers` and `drivers_missing_heading` — plus
`drivers.md` added to the valid fixture, which the exit-0 test requires once the gate is
live.

The existing suite's interaction with this change was checked rather than assumed:

- The invalid-case table asserts `exit != 0` and a substring needle. Those directories will
  now also fail for a missing `drivers.md`, but each needle still appears, so every case
  stays green untouched.
- The skip-coverage test enumerates skipped filenames that must not appear in the report.
  It gains one assertion for `drivers.md`. **This is the one existing test that changes**,
  and it is an addition, not a rewrite.

Every other design and requirements test stays green and unmodified. If one needs rewriting,
the change was wrong — the same standard Part E.4 of the STO-197 spec set.

**Agents.** Prompt files, no unit tests, matching M1. Their verification is the end-to-end run.

**End-to-end.** Run the stage against `docs/requirements/examples/tamagotchi/requirements/`
and commit the output as a worked example beside the M1 set. It is the only way to learn
whether the capability back-fill produces a sane graph on a real requirement set rather than
a fixture. Acceptance bar:

- components and interfaces that close the `CMP → IF → CMP` graph
- `validate_design.py` exits 0
- Q-4 resolved into an actual framework decision recorded in `drivers.md`

---

## Part H — Sequencing

Four commits, in this order:

1. **`drivers.md` gate in `validate_design.py`** plus its fixtures. The only change to code
   that already ships, so it goes alone — the same reason STO-197's extraction commit was
   isolated.
2. **The five agent files.**
3. **`skills/design/SKILL.md`**, plus the `design` workflow entry in `commands/groundwork.md`.
4. **The tamagotchi worked example**, generated by running the stage end to end.

---

## Part I — Boundaries

| Not here | Owner |
| --- | --- |
| ADR authoring (MADR 4.0) — this ticket only declares the dispatch slot | STO-100 |
| C4 Mermaid diagrams — declares the dispatch slot | STO-101 |
| Cross-artifact validation: `traces_from` resolution, FR coverage, ADR drivers → NFR IDs | STO-102 |
| Dependency cycles, orphan interfaces, vague `responsibility` prose | STO-208 |
| Directory-placement gating in either validator | STO-209 |

---

## Deliverables

- `agents/design-orchestrator.md`
- `agents/component-specialist.md`
- `agents/interface-specialist.md`
- `agents/design-critic.md`
- `agents/design-formatter.md`
- `skills/design/SKILL.md`
- `commands/groundwork.md` — the `design` workflow entry
- `skills/design/scripts/validate_design.py` — `drivers.md` skip entry, gate, and export
- `skills/design/scripts/tests/fixtures/` — `missing_drivers`, `drivers_missing_heading`, and
  `drivers.md` in the valid fixture
- `docs/requirements/examples/tamagotchi/design/` — the end-to-end worked example

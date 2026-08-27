# Desktop Tamagotchi — Example Artifact Set

A full requirements set (M1) and the architecture set generated from it (M2),
produced by the Groundwork pipelines for a "desktop tamagotchi" feature. This
is the example from the
[eyeofthestorm.dev dev log](https://eyeofthestorm.dev/posts/dev-log-building-groundwork):
the first run exposed a list of gaps, and these sets are the re-runs after
the work closed them.

Both sets were regenerated end-to-end under STO-219, against the corrected
pipeline, and neither contains a hand-edited artifact. What changed in that
regeneration and why is recorded in
**[`../REGENERATION.md`](../REGENERATION.md)** — including every finding that
survived it, and why surviving was the better answer. Read that file before
comparing this set against an older copy of it.

## Layout

- **[`requirements/`](./requirements/)** — the validatable atomic requirement
  set: one Markdown+YAML file per requirement under `functional/`,
  `non-functional/`, `constraints/`, `business-rules/`, plus the project-level
  `assumptions.md`, `glossary.md`, `definition-of-done.md`, and a machine
  `index.yaml` (which carries the low-confidence `review_queue`). 26
  requirements.
- **[`design/`](./design/)** — the architecture set generated from those
  requirements: 19 component specs under `components/`, 31 interface specs
  under `interfaces/`, 7 ADRs under `adr/` and 4 C4 views under `diagrams/`,
  plus `assumptions.md`, `drivers.md`, and an `index.yaml` that lists all four
  artifact types. That is the pipeline's complete declared output — nothing in
  this directory was added by hand.
- **[`critique-report.yaml`](./critique-report.yaml)** — the design critic's
  real return value against this set: the round-3 report that returned
  `gate: pass`. It sits **here at the example root, not inside `design/`**,
  because no agent is instructed to write it and no declared layout contains
  it — see *The one file that is not pipeline layout* below.
- **[`clarification-context.yaml`](./clarification-context.yaml)** /
  **[`design-context.yaml`](./design-context.yaml)** — the reconstructed inputs
  each stage was replayed from. Also companions, also not pipeline layout.
- **[`CONSOLIDATED.md`](./CONSOLIDATED.md)** — every requirement, the
  assumptions, and the review queue rendered into one readable document.
- **[`dev-log-followup.md`](./dev-log-followup.md)** — the follow-up dev-log
  post (portable draft) narrating the before/after.

## Validating the sets

Run each stage's tooling against its own subdirectory, not against this folder
— the consolidated doc, the two context files and the critique report are not
atomic artifacts, and no validator will accept them.

```bash
# M1 — requirements
python3 skills/requirements/scripts/validate_requirements.py \
  docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/tamagotchi/requirements

# M2 — design
python3 skills/design/scripts/validate_design.py \
  docs/requirements/examples/tamagotchi/design
python3 skills/design/scripts/lint_design_content.py \
  docs/requirements/examples/tamagotchi/design

# M1 ↔ M2 — traceability. Note the shape: the design directory is positional,
# and the requirement set is named. Passing the example root instead exits 2.
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements
```

Expected, verified against the shipped sets:

| Command | Result | Exit |
| --- | --- | --- |
| `validate_requirements.py` | `Summary: 26/26 file(s) passed, 0 failed, 0 error(s) total.` | 0 |
| `lint_requirements_content.py` | `Summary: 3 finding(s) (0 error, 3 warn, 0 info).` | 0 |
| `validate_design.py` | `Summary: 61/61 file(s) passed, 0 failed, 0 error(s) total.` | 0 |
| `lint_design_content.py` | `No content anti-patterns found.` | 0 |
| `validate_traceability.py` | `Indexed 61 design artifact(s), 26 requirement(s).` / `Summary: 0 error(s), 0 warning(s).` | 0 |

The design set's 61 files are 19 components, 31 interfaces, 7 ADRs and 4
diagrams.

The requirements content linter is **not** clean, and is not meant to be: it
reports three advisory `warn` findings and still exits 0, because the tool is
advisory. Each is named and justified in *The findings that are still here*
below, and again in `CONSOLIDATED.md`'s *Content-lint notes*. The design
content linter **is** clean — including of the `dependency-cycle` finding the
previous version of this set carried, which is a change with a cost of its own;
see the same section.

Note that the design set deliberately has no `README.md` of its own. Anything
under `design/` that is not a skipped companion is discovered as an artifact
and must parse as one, so a stray Markdown file there fails the gate. That is
why this README sits at the example root — the same reason `requirements/` has
none either.

## What the requirements set demonstrates

- Functional requirements in EARS notation with Gherkin acceptance criteria,
  across five patterns rather than one: `event` (FR-001..FR-005), `state`
  (FR-007, FR-008), `complex` (FR-006, FR-011), `optional` (FR-009) and
  `unwanted` error paths (FR-010, FR-012).
- Nine ISO 25010 quality-attribute-scenario NFRs with measurable response
  measures.
- Constraints and business rules kept distinct from NFRs.
- Externalized `assumptions.md` (Assumptions / Dependencies / Open Questions),
  plus a *Recommendations recorded, not authored* section for proposals the set
  declined to turn into requirements.
- A generated `definition-of-done.md` deriving an acceptance gate per
  functional requirement and a fitness gate per NFR.
- Per-requirement `confidence` with a low-confidence `review_queue` for human
  triage — 8 of the 26, each naming the open question it rests on. `NFR-002`,
  `NFR-009` and `CON-001` are there for the same reason: the set states CPU,
  memory and latency budgets and has no reference machine to measure them on
  (`Q-5`), so it declines to present them as executable.
- Two business rules that assert *less* than their predecessor did. `BR-001`
  now says nothing about what happens to a pet after it reaches the terminal
  status, because `Q-2` is open — and `BR-002` exists to hold that state
  undisturbed until it closes. `BR-002`'s own rationale names the previous
  draft's answer as a fabrication.

## How this set was produced

Both stages were replayed from a reconstructed context object, committed
alongside the set: `clarification-context.yaml` for M1, `design-context.yaml`
for M2. Every field in each traces to something the *previously published set
itself* asserted; nothing that only a later stage knew was allowed back into
the input. The pipelines then ran normally — specialists, critic, formatter —
and their output was copied in whole. No artifact under `requirements/` or
`design/` was hand-edited at any point.

The design stage reached `gate: pass` on its third critique round with no
override: round 1 returned `fail` with ten findings, all discharged; round 2
returned `fail` with four entirely new ones, all discharged; round 3 returned
`pass` with an empty register. The requirements stage took five specialist
rounds to reach `pass`.

### The one file that is not pipeline layout

**`critique-report.yaml` is an exhibit, not output.** No agent is instructed to
write it, and it appears in no declared layout — not in the spec's Part E, not
in `agents/design-formatter.md`'s directory layout. The `critique_report` is an
in-flight hand-off between the critic and the orchestrator; it is consumed and
then it is gone. It is serialised here so the critique can be published rather
than described second-hand. A real `.sdlc/design/` will not contain this file,
and the formatter should not start emitting one. It sits at the example root,
alongside the two context files, for exactly that reason — inside `design/` it
would look like part of the set.

Only the final passing report is published. The failing rounds are narrated in
[`../REGENERATION.md`](../REGENERATION.md); shipping a second critique report
would just be more hand-added non-pipeline content in a directory that should
have none.

**One field in it invites misreading.** `critique_report.validator` is `null`.
That is correct by contract, not an omission: the critic runs *before* anything
is on disk and before `drivers.md` exists, so it has no structural-validator
result to report. The structural gate is the formatter's own re-run of
`validate_design.py`, which the orchestrator folds back into that field in a
live run. The file's header comment says so; it is repeated here because a
reader who opens the exhibit cold will read `null` as "the validator was
skipped".

## What the design set demonstrates

The architecture stage picks up exactly where the requirements stage left off,
including its unfinished business.

- **The inherited questions get answered, and the answers are recorded as
  decisions.** Q-4 — *Electron, Tauri, or native, given the footprint
  constraint* — is the question the requirements stage could not settle, and
  the one the first tamagotchi build got wrong by never treating it as a
  decision. It is answered here (Tauri), along with Q-2 (the terminal status is
  permanent), Q-3 (Windows first) and Q-9 (one committed save generation). All
  four appear in `drivers.md` as tradeoffs with their gains and costs, **and**
  as MADR-format records in `adr/` — `ADR-001` through `ADR-004`.
- **The decisions it could not make are recorded too.** `ADR-005`, `ADR-006`
  and `ADR-007` carry `decision_status: proposed` rather than `accepted`:
  where the below-threshold clock lives, what period the evaluation cadence
  runs at, and whether
  `CON-001`'s runtime exclusion screen was ever actually executed. Each carries
  a matching open question (`Q-11`, `Q-12`, `Q-13`). Eleven further tradeoffs
  were reported as *skipped* by the ADR generator instead of being inflated
  into one-option decision records.
- **The dependency graph closes.** 19 components and 31 interfaces. Components
  declare *capabilities* in prose; interfaces satisfy each exactly once; the
  orchestrator back-fills the edge. Two components are `boundary: external` —
  the OS notification service and the host wall clock — because a dependency
  cannot point outside the graph.
- **The diagrams are part of the run.** Four C4 views under `diagrams/`,
  projected by `generate_c4.py` from the component and interface frontmatter
  during the formatter's own pass — a system context, a container view, and one
  component view per container (`pet-core`, `webview-ui`). `traces_to.diagrams`
  is back-filled on all 19 components, and `index.yaml` carries all 61
  artifacts: components, interfaces, ADRs and diagrams alike. There are two
  containers, and therefore four diagrams rather than three, because
  `generate_c4.py` reuses a container's `technology` label for every member
  component and one container would have had to mislabel either the Rust core
  or the webview.
- **The drivers are written down.** `drivers.md` carries 20 architecturally
  significant requirements with why each shapes structure, 15 tradeoffs, and 10
  sensitivity points — the reasoning that would otherwise live only in the
  conversation that produced it.
- **The critique is published, not hidden.** `critique-report.yaml` is the
  design critic's real output against this set. It returns `gate: pass`, which
  it earned rather than being granted; the ten-then-four findings it raised on
  the way are in [`../REGENERATION.md`](../REGENERATION.md).
- **Every requirement is covered, including the two that did not exist
  before.** The traceability sweep reports 0 errors and 0 warnings across all
  26 requirements. `FR-011` (wake) and `FR-012` (quarantine) are new in this M1
  set; `FR-011` now traces to seven components and `FR-012` to four.

### The findings that are still here

A worked example whose tooling found nothing would teach nothing about whether
that tooling works. These are the findings that survived the regeneration. Each
is a choice — the full reasoning for every one is in
[`../REGENERATION.md`](../REGENERATION.md).

- **Three advisory requirements-lint findings**, none of them a defect, none
  hand-patched away:
  - `NFR-001` `passive-nameless` on "each pet stat shall be decayed…". The
    actor is the offline-decay computation, named in the scenario's Artifact
    field directly below.
  - `NFR-007` `vague-qualifier` on "sufficient", which appears only in
    supporting prose; the description and fit criterion both carry a concrete
    measure.
  - `glossary.md` `glossary-unused` on "Idle steady state", which *is* used —
    inside `NFR-002`'s scenario body, a field the linter's scan does not index.

  Hand-editing any of the three would have produced a cleaner linter run and a
  set that was no longer a pipeline product. The linter is advisory and exits
  0; that is the trade it exists to allow.

- **Operation counts now cluster at one instead of two.** The previous version
  of this set had 11 of its 12 interfaces at exactly two operations — 92%,
  which was the interface specialist matching a shape inferred from the
  examples in its own instructions. That is gone: 7 of 31 are at two, 23%,
  across 49 operations, with argued outliers at 3, 4 and 7. But 21 of 31 are
  single-operation, and a one-operation contract is the cheapest thing to emit
  when unsure. Most of these capabilities genuinely are one verb, so nothing
  was changed — recorded here so a future pass checks the tiebreaker moved
  rather than vanished.

- **The `dependency-cycle` linter rule has lost its only real-world input.**
  Before STO-219 this example contained a genuine cycle —
  `CMP-003 → IF-006 → CMP-004 → IF-005 → CMP-003`, two state-holding
  components consulting each other — and `test_lint_design_content.py`
  pinned the rule's exact rendered path against it. The regenerated
  decomposition draws the live-state holder as a leaf below the state store
  rather than as a peer of a second state holder, so no cycle remains, and
  nothing forced that: no re-dispatch was made to break a cycle and no cycle
  appeared at any round. The rule is still tested,
  but now only against synthetic fixtures —
  `test_dependency_cycle_is_reported_with_its_rendered_path` asserts the same
  exact path against `fixtures/lint/cycle-one`. **Coverage of this rule is
  thinner than it was, and the loss was accepted rather than avoided:**
  breaking the cycle was the better design, and keeping a worse decomposition
  alive to preserve one test's realism would have been the wrong trade.

- **The C4 golden test covers a different shape than it used to.** The old
  golden was an incidental witness for `Rel` deduplication, because five
  internal components shared one external interface. The regenerated set routes
  every platform edge through the single platform-adapter component `NFR-006`
  requires, so each external interface now has exactly one internal consumer
  and that shape is gone from the worked example. It is not lost — both dedup
  guarantees are pinned directly by dedicated synthetic tests. What the golden
  now uniquely covers instead is the multi-container projection over a real
  set: container-to-container edges across the webview/core seam, and
  per-container `DIA-` allocation.

- **`Q-4` is recorded as resolved while the requirement set's `D-10` says it
  cannot be.** Q-4 (the runtime choice) rests on footprint figures that have no
  reference machine until `Q-5` closes. Rather than pretend the tension away,
  the resolution is explicitly provisional — and the pipeline surfaced the same
  tension on its own, as `ADR-003`'s `medium` confidence and as `ADR-007`
  existing at all. This is an inconsistency somebody noticed, not one nobody
  did.

### Interface segregation — right outcome, unexpected mechanism

The previous version of this set carried two interfaces whose consumers wanted
different halves of them — `IF-003` (durable persistence: `load` + `commit`)
and `IF-006` (lifecycle state: a blocking read + a subscription). Both were
recorded as segregation defects and left in place, because the fault sat
upstream in how coarsely the capability had been carved and the interface
specialist had no split available to it.

In the regenerated set both concerns are separated. **Only one of them was
separated by the segregation heuristics**, and the difference is worth stating
because the output does not show it:

- **Durable persistence split by segregation.** It is now `IF-012` (`retrieve`)
  and `IF-013` (`commit`), with *disjoint* consumer sets — `CMP-003` commits
  and never retrieves, `CMP-011` retrieves and never commits — disjoint in
  time, and differing in failure kind.
- **Lifecycle state was separated before segregation was ever reached.**
  Live-state access (`IF-002`) is provided by `CMP-003`, while the lifecycle
  transitions landed on **different providers** — sleep entry and wake
  resolution on `CMP-006`, health advancement on `CMP-005`. The merge rule only
  ever applies within one provider, so it could never have merged them. The
  heuristics agree with the result; they did not produce it.

The finding is about the heuristics, not the set: they only see a question when
both capabilities sit on the same provider. Where that condition genuinely held
here — inside `CMP-006` — they did split, into `IF-005 enter_sleep` and
`IF-006 resolve_wake`. A reader comparing the two sets would otherwise credit
the heuristics with a split they did not make.

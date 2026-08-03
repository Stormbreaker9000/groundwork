# Desktop Tamagotchi — Example Artifact Set

A full requirements set (M1) and the architecture set generated from it (M2), produced
by the Groundwork pipelines for a "desktop tamagotchi" feature. This is the example from
the [eyeofthestorm.dev dev log](https://eyeofthestorm.dev/posts/dev-log-building-groundwork):
the first run exposed a list of gaps, and these sets are the re-runs after the work
closed them.

## Layout

- **[`requirements/`](./requirements/)** — the validatable atomic requirement set: one
  Markdown+YAML file per requirement under `functional/`, `non-functional/`,
  `constraints/`, `business-rules/`, plus the project-level `assumptions.md`,
  `glossary.md`, and a machine `index.yaml` (which carries the low-confidence
  `review_queue`).
- **[`design/`](./design/)** — the architecture set generated from those requirements:
  11 component specs under `components/`, 12 interface specs under `interfaces/`, plus
  `assumptions.md`, `drivers.md`, and `index.yaml`. Those are the pipeline's declared
  output. Alongside them sits `critique-report.yaml`, the design critic's real return
  value against this set, **added here by hand** — see *How this set was produced* below.
- **[`CONSOLIDATED.md`](./CONSOLIDATED.md)** — every requirement, the assumptions, and the
  review queue rendered into one readable document.
- **[`dev-log-followup.md`](./dev-log-followup.md)** — the follow-up dev-log post
  (portable draft) narrating the before/after.

## Validating the sets

Run each stage's tooling against its own subdirectory, not against this folder — the
consolidated doc and the dev-log are not atomic artifacts, and neither validator will
accept them.

```bash
# M1 — requirements
python3 skills/requirements/scripts/validate_requirements.py \
  docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/tamagotchi/requirements

# M2 — design
python3 skills/design/scripts/validate_design.py \
  docs/requirements/examples/tamagotchi/design
```

Expected: requirements validator **22/22 pass**, content linter **clean**, design
validator **23/23 pass**.

Note that the design set deliberately has no `README.md` of its own. Anything under
`design/` that is not a skipped companion is discovered as an artifact and must parse as
one, so a stray Markdown file there fails the gate. That is why this README sits at the
example root — the same reason `requirements/` has none either.

## What the requirements set demonstrates

- Functional requirements in EARS notation with Gherkin acceptance criteria,
  including an `unwanted`-pattern error path (`FR-010`).
- Seven ISO 25010 quality-attribute-scenario NFRs with measurable response measures.
- Constraints and business rules kept distinct from NFRs.
- Externalized `assumptions.md` (Assumptions / Dependencies / Open Questions).
- Per-requirement `confidence` with a low-confidence `review_queue` for human triage —
  including the runtime/footprint decision (`NFR-002`, `CON-001` → open question Q-4).

## How this set was produced — two deviations from the documented pipeline

Read this before treating the `design/` folder as a reference run. It is a faithful
example of what the artifacts look like, but it is **not** reproducible by following the
agent instructions, and two things about it are deliberate exceptions rather than normal
behaviour.

**The set was written on a failing gate, by human override.** The pipeline's hardest
invariant is that nothing is written until the critic returns `gate: pass` —
`agents/design-formatter.md` ("Never write anything before the critic has returned
`gate: pass`") and `agents/design-orchestrator.md` ("Never advance to the formatter
without `gate: pass`"). This set's `critique-report.yaml` says `gate: fail`, and the
artifacts were written anyway. That was a human decision taken knowingly, for one reason:
the alternative was to keep re-dispatching until the critic went quiet, and the seven
remaining findings are *worth more than a clean gate* (see the next section — three of
them are schema limitations no wording could satisfy, and one is arguably a false
positive). A worked example whose critic found nothing would teach nothing about whether
the critic works. **An ordinary run must not do this.** A `gate: fail` reaching the
formatter is a bug in the run, not a judgment call available to the agents; only a human
looking at the specific findings can decide they are acceptable, and that is what
happened here.

**`critique-report.yaml` is a hand-added exhibit, not pipeline output.** No agent is
instructed to write it, and it appears in no declared layout — not in the spec's Part E,
not in `agents/design-formatter.md`'s directory layout. The `critique_report` is an
in-flight hand-off between the critic and the orchestrator; it is consumed and then it is
gone. It was serialised to disk here so the findings could be published rather than
described second-hand. A real `.sdlc/design/` will not contain this file, and the
formatter should not start emitting one.

## What the design set demonstrates

The architecture stage picks up exactly where the requirements stage left off, including
its unfinished business.

- **The inherited questions get answered.** Q-4 — *Electron, Tauri, or native, given the
  footprint constraint* — is the question the requirements stage could not settle, and the
  one the first tamagotchi build got wrong by never treating it as a decision. It is
  answered here (Tauri), along with Q-3 (Windows first) and Q-2 (death is permanent), and
  all three are recorded in `drivers.md` as tradeoffs with their gains, their costs, and
  the requirements that rested on them.
- **The dependency graph closes.** 11 components and 12 interfaces, 26 `CMP → IF → CMP`
  edges. Components declare *capabilities* in prose; interfaces satisfy each exactly once;
  the orchestrator back-fills the edge. Two components are `boundary: external` — the OS
  notification service and the system clock — because a dependency cannot point outside
  the graph.
- **The drivers are written down.** `drivers.md` carries 13 architecturally significant
  requirements with why each shapes structure, 10 tradeoffs, and 6 sensitivity points —
  the reasoning that would otherwise live only in the conversation that produced it.
- **The critique is published, not hidden.** `critique-report.yaml` is the design critic's
  real output against this set. It returned `gate: fail`, and the set is shipped with that
  visible rather than tidied away — which took the human override described above.

### The open critic findings, and why they are still here

Two findings were correctness faults and were fixed: `CMP-004` and `IF-008` traced from
`BR-001` while asserting the opposite of its statement text. Both now pass.

The `BR-001` finding behind that pair is worth reading in full, because it runs the other
way. `BR-001` is *internally inconsistent*: its statement asserts the pet "is reset to a
new pet", while its own rationale says whether death is permanent "is still open (Q-2),
which is why this rule is held at low confidence". The design stage resolved Q-2 as permanent and the specialists
silently followed it. The critic caught the mismatch. The resolution recorded here is that
`BR-001`'s statement text is stale and needs amending upstream — filed as **Q-5** in
`design/assumptions.md`. Architecture found a latent defect in the requirements it was
built from.

Seven findings remain open and are deliberately preserved as genuine critic output:

- **Three responsibility phrasings** (`CMP-003`, `CMP-006`, `CMP-008`) trip the
  single-responsibility rule. `CMP-006` is arguably a false positive — the rule greps the
  sentence for "and" rather than judging cohesion, and a UI surface that presents and
  accepts input is one duty by most readings.
- **Three interfaces** (`IF-002`, `IF-006`, `IF-012`) carry both a blocking and a
  non-blocking operation, but `interaction` is a single enum. The schema cannot express a
  mixed-mode contract, so no wording of these artifacts would satisfy the check.
- **One `traces_from` plausibility** flag on `CMP-001`.

They are left in place because a worked example showing a critic that found nothing would
teach nothing about whether the critic works.

### Two granularity artifacts, recorded rather than fixed

This set was generated before the capability and interface granularity heuristics
existed. Two divergences from what the pipeline now teaches are left in place, for
the same reason the critic findings above are.

- **`IF-003` should have been two interfaces.** *Durable Pet State Persistence*
  carries `load` and `commit`. `CMP-007` needs both — it restores at launch and
  commits at shutdown — but `CMP-003` needs only `commit`, since `FR-001`'s save
  trigger is all it uses the store for and its launch state arrives through
  `IF-009` instead. The consumer sets are nested, not identical, so under the
  Interface Segregation rule they do not coincide: the single contract makes
  `CMP-003` depend on a `load` it never calls. Note where the fault actually
  sits: one capability can only ever become one interface, so the interface
  specialist had no split available to it. The capability was carved too
  coarsely upstream, and the split-when-unsure tiebreaker the component
  specialist now carries is what would have prevented it. This is the
  unrecoverable direction of that asymmetry, caught in the wild.
- **Operation counts are suspiciously uniform.** Eleven of the twelve interfaces
  carry exactly two operations; only `IF-007` carries one. Twelve independent
  contracts over a clock, a log, a store, a decay calculator, a mood evaluator and
  a notifier do not converge on two operations each by coincidence. This is the
  specialist matching a shape it inferred from the examples in its own
  instructions and then carving granularity to fit — the clearest evidence in this
  set for why the heuristics were needed at all.

Regenerating this set against the corrected pipeline is tracked separately, and
waits on the other in-flight changes so the examples are re-run once rather than
after every fix.

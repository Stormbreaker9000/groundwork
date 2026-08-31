# Worked Example Regeneration — Design

**Ticket:** STO-219 — Regenerate the worked example artifact sets against
the corrected pipeline. The last M2 ticket; all five of its blockers
(STO-100, STO-101, STO-208, STO-216, STO-217) have merged.

## Problem

`docs/requirements/examples/` holds the sets the plugin teaches from: a
tamagotchi requirements set (22 requirements) with the design set
generated from it (11 components, 12 interfaces, 3 diagrams), and a GDPR
requirements set (8 requirements). Both were produced by pipeline
versions that have since been corrected, so they record what the pipeline
*did*, not what it *should* do.

What is actually stale, in the order a reader meets it:

- **The design set has no ADRs at all.** There is no `design/adr/`
  directory. STO-100 added the artifact type after this set was
  generated, so the example demonstrates a design stage that never
  records a decision.
- **The diagrams are bolted on.** `diagrams/` was produced by running
  `generate_c4.py` over a set generated before that tool existed.
  `traces_to.diagrams` is deliberately un-back-filled on the components
  and `index.yaml` lists the 23 CMP/IF artifacts and none of the 3
  diagrams — both to avoid becoming a second writer of a set nothing
  else was rewriting. A real formatter run does both.
- **The set was written on a failing gate.** `critique-report.yaml`
  says `gate: fail` and the artifacts were written anyway, by human
  override. The README spends three paragraphs on this and has to warn
  that "an ordinary run must not do this". The set is, by its own
  admission, not reproducible by following the agent instructions.
- **`critique-report.yaml` is a hand-added exhibit.** No agent writes
  it and it appears in no declared layout. It sits inside the validated
  set, where a real `.sdlc/design/` will never have one.
- **Interface granularity predates its own rules.** Eleven of the twelve
  interfaces have exactly two operations, which is the specialist
  pattern-matching the shape of the examples in its instructions rather
  than a design outcome. IF-003 and IF-006 both have divergent consumer
  sets that STO-217's Interface Segregation rule would split.
- **Both M1 sets were generated through an unreachable gate.** STO-215
  found the requirements critic's structural gate and content lint could
  not run where they were placed, so neither actually ran as written
  during generation.
- **The two M1 sets disagree about their own layout.**
  `tamagotchi/requirements/` has `index.yaml` and no
  `definition-of-done.md`; `gdpr/requirements/` has
  `definition-of-done.md` and no `index.yaml`. The ticket does not
  mention this one.

## Evidence

**Replay is mechanically supported at both stages.**
`agents/requirements-orchestrator.md:53` defines `clarification_context`
as a flat eight-field object (`problem_domain`,
`stakeholders_and_users`, `core_functionality`, `success_criteria`,
`non_functional_concerns`, `constraints`, `out_of_scope`,
`open_questions`), and `skills/requirements/SKILL.md:136` states it
serializes 1:1 from the interview's Phase 4.5 block. Every field is
recoverable from what the sets already publish. For M2, the original
run's design context survives locally at
`.superpowers/sdd/e2e/design-context.yaml` — the user-confirmed Phase 4
output that fed orchestrator Stage 1, carrying the Q-1..Q-4
dispositions verbatim.

**Six tests assert against the shipped example.** Regenerating it is a
test-suite change, not only a docs change:

| Test | Coupling |
|---|---|
| `test_generate_c4.py::test_worked_example_generates_a_valid_diagram_set` | Byte-identical golden comparison against the committed diagrams, driven by `fixtures/c4/tamagotchi-model.json` |
| `test_lint_design_content.py::test_shipped_tamagotchi_example_has_the_known_cycle` | Asserts exactly one `dependency-cycle` finding, matched on the exact rendered path |
| `test_lint_design_content.py::test_shipped_tamagotchi_example_has_no_error_findings` | Property — should survive |
| `test_lint_design_content.py::test_shipped_tamagotchi_example_survives_without_pyyaml` | Property — should survive |
| `test_validate_design.py::test_shipped_tamagotchi_example_passes_structural_gate` | Property — should survive |
| `test_validate_traceability.py::test_shipped_tamagotchi_example_is_clean` | Property, but guards a named D6 data fix — re-check after the swap |

The four property-based tests are the regression net for the swap. The
two pinned ones are expected to change, and one of them costs something
real: `dependency-cycle` has exactly one real-world input in this
repository, and it is the `CMP-003 ⇄ CMP-004` cycle in this example. If
the regenerated design breaks that cycle, the rule falls back to
synthetic fixtures alone.

## Decisions

### D1 — Replay the recorded answers; do not re-interview

The pipelines are conversational at both stages. A fresh interview would
be the most faithful re-run and the only route that re-tests the
elicitation stages, but it is long, non-deterministic, and its answers
would drift from the decisions the published set already documents. The
replay reconstructs the context objects from what is recorded and runs
the generation pipelines against them. What is being regenerated is the
*generation*, not the *elicitation*.

The reconstructed `clarification_context` for each M1 set is committed
alongside the example, so the run is auditable and repeatable rather
than resting on a transcript nobody kept.

### D2 — Full ticket scope, plus companion parity

tamagotchi requirements, tamagotchi design, and gdpr requirements. Both
M1 sets end with the same companion files, settling the `index.yaml` /
`definition-of-done.md` divergence. `definition-of-done.md` comes from
the `dod-generator` agent, which is an M1 stub that STO-104 expands in
M3; if the generated file is thin, the README says so and points at
STO-104 rather than hand-writing a better one.

### D3 — Aim for `gate: pass`; teaching value moves to narrative

The current set ships on `gate: fail` because the surviving findings
were judged worth more than a clean gate. That reasoning holds — an
example whose critic found nothing teaches nothing — but it costs the
property that matters more: the set cannot be reproduced by following
the documented process, and the pipeline's hardest invariant needs an
apology every time it is described.

So the regenerated set drives to `gate: pass`, and the findings the
critic raised on the way are documented as narrative (D8) rather than
preserved as a failing gate. The risk is a critic argued into silence,
which is a worse outcome than a documented finding. The mitigation is a
stop rule: **a finding that survives three re-dispatches is recorded and
kept, not ground down.** If that happens, D3 is reconsidered rather than
worked around.

### D4 — Scratch-generate, diff, then swap

Each stage generates into a scratch directory outside the repository.
The new set is diffed against the current one, the delta is reviewed,
and only then is it swapped in and gated. A discarded run costs nothing;
a committed-then-reverted one costs a dirty history and a window where
`main` holds a half-migrated set — a new M1 with an M2 still built from
the superseded one.

The diff is not a formality. It is the input to D8, and it is how the
ticket's actual test gets applied: that every deviation which survives
is *chosen*, not inherited.

### D5 — The replay stays faithful to what each stage knew

Q-2 (is death permanent) was resolved during the *design* stage. The
replayed M1 context therefore keeps it open, exactly as the requirements
stage saw it.

This matters for `BR-001`, whose recorded defect is subtle: its
statement asserts the pet "is reset to a new pet" while its own
rationale says the question is open. The fault is not that M1 did not
know the answer — it is that M1 asserted one anyway, contradicting
itself. Under D3 the critic must now catch that internal inconsistency
and it gets fixed before the gate clears. The lesson (architecture
surfaced a latent requirements defect) is preserved in the narrative;
the defect is not preserved in the artifact.

### D6 — Acceptance is by property, not by count

Artifact counts are expected to change — that is the point of
regenerating under STO-217's granularity heuristics — so pinning them
would assert the wrong thing. The gates are:

- Both structural validators exit 0 on all three sets.
- Content linters are clean, or every remaining finding is explained in
  the README.
- `design/adr/` exists and holds ADRs traced to the decisions
  `drivers.md` records.
- `traces_to.diagrams` is back-filled on every component a diagram
  depicts.
- `index.yaml` lists every artifact type, diagrams included.
- Operation counts vary with need rather than clustering at two.
- IF-003 and IF-006 are either split, or kept with a stated reason.
- Both M1 sets carry the same companion files.

### D7 — The regenerated example is a test-suite change

The two pinned tests in the Evidence table are updated in the same
commit as the swap they describe, never separately: a set and its
goldens that disagree is a red suite with no diagnostic value.
`fixtures/c4/tamagotchi-model.json` is regenerated in lockstep with the
diagrams it drives.

If the cycle is broken, `test_shipped_tamagotchi_example_has_the_known_cycle`
is rewritten rather than deleted — the rule still needs a test, and the
loss of its only real-world input is recorded in the README so a future
reader knows the coverage got thinner and why.

### D8 — A divergence record replaces the failing critique report

`docs/requirements/examples/tamagotchi/REGENERATION.md` records what the
corrected pipeline produced differently and why, divergence by
divergence. With the gate passing, this is the artifact that carries
"the tooling really does catch things" — a job the `gate: fail`
critique report was doing at the cost of the set's reproducibility. It
also gives the before/after that `dev-log-followup.md` already
establishes as a pattern for this example.

### D9 — `critique-report.yaml` leaves the validated set

It moves to the example root as a clearly-labelled exhibit. Inside
`design/` it is a file the formatter does not declare and a real
`.sdlc/design/` will not contain; at the root it cannot be mistaken for
pipeline layout — and the root is already where non-artifact companions
live, since the validators are run against the subdirectories, never the
folder itself.

The exhibit is the **regenerated run's final critique report**, the one
that returns `gate: pass`. The failing findings raised along the way are
narrated in `REGENERATION.md` (D8), not shipped as a second file:
publishing both was considered and rejected, because two critique
reports in a directory the formatter does not declare is more
hand-added non-pipeline content, not less. The README's "the critique is
published, not hidden" property survives the move.

### D10 — Stage order and commit granularity

1. **tamagotchi M1** — must land first; M2 consumes it and `traces_from`
   must resolve against the new IDs.
2. **tamagotchi M2** — consuming the new M1.
3. **gdpr M1** — independent, so it goes last where it cannot
   destabilise the tamagotchi chain.

One commit per stage, each with its gates green and its coupled tests
updated. The README rewrite and `REGENERATION.md` land last, once every
divergence is known.

### D11 — Deferred to the run, deliberately

Two outcomes are not pre-decided here, because deciding them before
seeing what the corrected pipeline produces would be inventing the
result:

- **The `CMP-003 ⇄ CMP-004` cycle.** The ticket allows breaking it or
  keeping it with a stated reason. What is *not* allowed is inheriting
  it silently. D7 records the coverage cost of breaking it; that cost
  informs the decision without settling it.
- **Whether IF-003 and IF-006 actually split** under the segregation
  heuristics. If the specialists do not split them, that is a finding
  about the heuristics worth recording, not a result to force by hand.

## Files changed

**Regenerated**

| Path | Change |
|---|---|
| `docs/requirements/examples/tamagotchi/requirements/` | Full re-run; gains `definition-of-done.md` |
| `docs/requirements/examples/tamagotchi/design/` | Full re-run; gains `adr/`, a complete `index.yaml`, back-filled `traces_to.diagrams` |
| `docs/requirements/examples/gdpr/requirements/` | Full re-run; gains `index.yaml` |

**New**

| Path | Responsibility |
|---|---|
| `docs/requirements/examples/tamagotchi/REGENERATION.md` | The divergence record (D8) |
| `docs/requirements/examples/tamagotchi/clarification-context.yaml` | The committed M1 replay input (D1) |
| `docs/requirements/examples/gdpr/clarification-context.yaml` | The committed M1 replay input (D1) |
| `docs/requirements/examples/tamagotchi/design-context.yaml` | The M2 replay input, rescued from gitignored scratch and committed so the design stage is replayable too (D1) |

**Modified**

| Path | Change |
|---|---|
| `docs/requirements/examples/tamagotchi/README.md` | The three-deviation section is rewritten; the gate-override and after-the-fact-diagram notes go away because they stop being true |
| `docs/requirements/examples/tamagotchi/CONSOLIDATED.md` | Rebuilt from the new requirement set. No renderer script exists — it is assembled from the set, and it hard-codes counts and validator results (`22/22 pass`, `10 functional, 7 non_functional, 3 constraint, 2 business_rule`) that all change |
| `docs/requirements/examples/tamagotchi/critique-report.yaml` | Moved here from `design/` as a labelled exhibit (D9) |
| `skills/design/scripts/tests/fixtures/c4/tamagotchi-model.json` | Regenerated in lockstep with the diagrams |
| `skills/design/scripts/tests/test_generate_c4.py` | Golden comparison updated |
| `skills/design/scripts/tests/test_lint_design_content.py` | Cycle test updated or rewritten, per D11 |

## Testing

The four property-based example tests are the regression net and must
stay green throughout, unchanged. The two pinned tests are updated with
the swap that changes them (D7). The whole suite runs from the repo root
with `python3 -m pytest -q` and must be green at the end of every stage,
not only at the end of the ticket.

Beyond the suite, each stage is gated by the tooling the READMEs
document: both structural validators exit 0, and both content linters
are clean or have every finding explained.

## Out of scope

- **Re-running the elicitation interviews.** D1. What is regenerated is
  the generation.
- **Improving the `god-component` rule's recall.** The README records
  that the rule finds 0 of 3 critic-flagged responsibilities by two
  distinct mechanisms — a vocabulary miss and a stated field-scope
  limit. Both are principled fixes and neither is this ticket.
- **Expanding `definition-of-done.md` beyond the M1 stub.** STO-104.
- **Adding a design stage to the GDPR example.** It stays a
  requirements-only set.

## Risks

**Non-determinism.** A replayed run will not reproduce the current set
token-for-token, so "diff and review" is a judgement exercise, not a
mechanical one. This is why D4 puts a human review between generation
and the swap.

**Gate churn.** Driving to `gate: pass` can turn into re-dispatching
until the critic goes quiet. D3's three-re-dispatch stop rule is the
guard, and hitting it reopens D3 rather than being worked around.

**Uneven coverage.** The GDPR set has no design stage, so it exercises
far less of the corrected pipeline than tamagotchi does. It is included
because a stale published set is a stale published set, not because it
carries equal teaching weight.

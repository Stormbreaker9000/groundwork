# Worked Example Regeneration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate the tamagotchi requirements and design sets and the
GDPR requirements set through the corrected pipeline, so the published
examples record what the pipeline *should* do rather than what a
superseded version of it did.

**Architecture:** Each stage replays a reconstructed context object
through the real generation pipeline into a scratch working directory,
is diffed against the set it replaces, and is swapped in only once the
delta has been reviewed and the gates are green. The teaching value that
a `gate: fail` critique report used to carry moves into a committed
divergence record, which lets the set become reproducible by following
the documented process.

**Tech Stack:** The Groundwork M1/M2 agent pipelines, Python 3 validators
and content linters (`validate_requirements.py`,
`lint_requirements_content.py`, `validate_design.py`,
`lint_design_content.py`, `validate_traceability.py`, `generate_c4.py`),
pytest.

**Spec:** `docs/superpowers/specs/2026-08-24-sto-219-worked-example-regeneration-design.md`

## Global Constraints

- **The pipelines write to `.sdlc/` relative to the current working
  directory, and the path is hard-coded.**
  `agents/requirements-formatter.md:37` runs
  `mkdir -p .sdlc/requirements/{...}`; `agents/design-formatter.md:45`
  runs `mkdir -p .sdlc/design/{components,interfaces}`. Neither accepts a
  target root. Scratch generation is therefore the mechanism, not a
  precaution: run the pipeline with the CWD set to a scratch directory,
  then copy `<scratch>/.sdlc/<stage>/` into the example directory. **Never
  point a pipeline at `docs/requirements/examples/`.**
- **Agent dispatch needs the user's explicit go-ahead.** Every generation
  step in Tasks 2, 3 and 4 dispatches the pipeline's specialist agents.
  Confirm before the first dispatch of each task; do not assume approval
  carries across tasks.
- **The gate stop rule (spec D3).** Drive to `gate: pass`, but a finding
  that survives **three** re-dispatches is recorded and kept, not ground
  down. Hitting the rule reopens D3 with the user rather than being
  worked around.
- **Counts are not pinned (spec D6).** Artifact counts are expected to
  change. Assert properties, never totals.
- **Both structural validators must exit 0** on every set at the end of
  every task. Content linters must be clean or have each remaining
  finding explained in the README.
- **Run the whole suite from the repo root** with `python3 -m pytest -q`.
  It is **263 tests green** at the start of this plan and must be green
  at the end of every task.
- **Commit convention:** `docs(sto-219): …` / `test(sto-219): …`, body
  wrapped at 72 columns.
- **Prose in `.md` wraps at 79 columns.** Python wraps at 88.

## Baseline (measured at plan time — the "before" side of the diff)

| Set | Validator | Content linter |
|---|---|---|
| `tamagotchi/requirements` | 22/22 pass | clean |
| `tamagotchi/design` | 26/26 pass (11 CMP, 12 IF, 3 DIA) | 1 warn — `dependency-cycle` on `CMP-003` |
| `gdpr/requirements` | 8/8 pass | 1 warn — `passive-nameless` on `NFR-001`'s description |

`tamagotchi/design/index.yaml` holds 23 artifact entries (no diagrams)
plus 3 `review_queue` entries. There is no `design/adr/` directory.

## File Structure

**New**

| File | Responsibility |
|---|---|
| `docs/requirements/examples/tamagotchi/clarification-context.yaml` | The committed M1 replay input (spec D1) |
| `docs/requirements/examples/gdpr/clarification-context.yaml` | The committed M1 replay input (spec D1) |
| `docs/requirements/examples/tamagotchi/design-context.yaml` | The committed M2 replay input, rescued from gitignored scratch |
| `docs/requirements/examples/tamagotchi/REGENERATION.md` | The divergence record (spec D8) |
| `docs/requirements/examples/tamagotchi/critique-report.yaml` | The passing critique report, moved out of the validated set (spec D9) |

**Regenerated**

| Path | Change |
|---|---|
| `docs/requirements/examples/tamagotchi/requirements/` | Full re-run; gains `definition-of-done.md` |
| `docs/requirements/examples/tamagotchi/design/` | Full re-run; gains `adr/`, a complete `index.yaml`, back-filled `traces_to.diagrams`; loses `critique-report.yaml` |
| `docs/requirements/examples/gdpr/requirements/` | Full re-run; gains `index.yaml` |

**Modified**

| File | Change |
|---|---|
| `skills/requirements/scripts/tests/test_validate_requirements.py` | Task 1 adds the shipped-example structural net |
| `skills/requirements/scripts/tests/test_lint_content.py` | Task 1 adds the shipped-example content net |
| `skills/design/scripts/tests/fixtures/c4/tamagotchi-model.json` | Regenerated in lockstep with the diagrams |
| `skills/design/scripts/tests/test_generate_c4.py` | Golden comparison updated |
| `skills/design/scripts/tests/test_lint_design_content.py` | Cycle test updated or rewritten (spec D11) |
| `docs/requirements/examples/tamagotchi/README.md` | Deviation section rewritten |
| `docs/requirements/examples/tamagotchi/CONSOLIDATED.md` | Rebuilt; hard-codes counts and validator results that all change |

---

### Task 1: Give both M1 example sets a regression net

The design side already pins its shipped example five ways. **Neither M1
set is covered at all** — nothing in `skills/requirements/scripts/tests/`
references `docs/requirements/examples/`. Tasks 2 and 4 replace those
sets wholesale, so the net has to exist first or the swap has nothing
watching it.

Both assertions pass against today's sets (measured: 22/22 and 8/8, zero
`error` findings on either), so this task is green from the start. That
is the point — it is the "before" half of a before/after.

**Files:**
- Modify: `skills/requirements/scripts/tests/test_validate_requirements.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`

**Interfaces:**
- Consumes: `vr.main([reqs_dir, "--schema", SCHEMA])` returning an exit
  code (already wrapped by the module-level `run(reqs_dir)` helper), and
  `lc.lint_dir(path)` returning findings with `.severity` and `.rule`.
- Produces: nothing later tasks import. Tasks 2 and 4 must leave both
  tests green without editing them.

- [ ] **Step 1: Add the structural net**

Append to `skills/requirements/scripts/tests/test_validate_requirements.py`:

```python
# ---------------------------------------------------------------------------
# Real-world regression: the shipped worked examples
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
EXAMPLES = os.path.join(REPO_ROOT, "docs", "requirements", "examples")


@pytest.mark.parametrize("name", ["tamagotchi", "gdpr"])
def test_shipped_example_passes_structural_gate(name, capsys):
    """The published requirement sets must satisfy the schema they ship
    alongside. The design side has pinned its example since STO-216;
    nothing has ever run THIS validator over `docs/requirements/examples/`,
    so a schema change could stale every published requirement with
    nothing turning red. STO-219 replaces both sets wholesale, which is
    exactly when that net needs to already exist."""
    code = run(os.path.join(EXAMPLES, name, "requirements"))
    assert code == 0, capsys.readouterr().out
```

- [ ] **Step 2: Add the content net**

`skills/requirements/scripts/tests/test_lint_content.py` does not import
`pytest` yet. Add `import pytest` to its imports, then append:

```python
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
EXAMPLES = os.path.join(REPO_ROOT, "docs", "requirements", "examples")


@pytest.mark.parametrize("name", ["tamagotchi", "gdpr"])
def test_shipped_example_has_no_error_findings(name):
    """Deliberately not "has no findings". The linter always exits 0 and
    the GDPR set carries one known `passive-nameless` warn, so `clean` is
    not a state this pins. This catches a future rule promoted to `error`
    silently invalidating a published set."""
    findings = lc.lint_dir(os.path.join(EXAMPLES, name, "requirements"))
    assert [f for f in findings if f.severity == "error"] == []
```

- [ ] **Step 3: Run the new tests and confirm they pass**

```bash
python3 -m pytest skills/requirements/scripts/tests -q -k shipped_example
```
Expected: 4 passed (2 sets × 2 tests).

- [ ] **Step 4: Prove the net bites**

A test that has never failed is not yet a net. Temporarily break one
requirement — e.g. delete the `id:` line from
`docs/requirements/examples/gdpr/requirements/functional/` first file —
re-run Step 3, confirm `test_shipped_example_passes_structural_gate[gdpr]`
fails, then restore the file with `git checkout` and re-run to confirm
green.

- [ ] **Step 5: Run the whole suite**

```bash
python3 -m pytest -q
```
Expected: 267 passed (263 + 4).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/tests/
git commit
```
Message: `test(sto-219): pin the shipped M1 example sets`, noting in the
body that neither M1 set had any coverage and that this is the net for
the regeneration that follows.

---

### Task 2: Regenerate the tamagotchi requirements set

Stage 1 of spec D10. Must land before Task 3 — the design stage consumes
this set and `traces_from` must resolve against whatever IDs it produces.

**Files:**
- Create: `docs/requirements/examples/tamagotchi/clarification-context.yaml`
- Regenerate: `docs/requirements/examples/tamagotchi/requirements/`
- Modify: `docs/requirements/examples/tamagotchi/CONSOLIDATED.md`

**Interfaces:**
- Consumes: the published tamagotchi set as source material for the
  context reconstruction.
- Produces: a validated requirement set whose IDs Task 3's design stage
  traces from, and `clarification-context.yaml` as the committed record
  of what was replayed.

- [ ] **Step 1: Reconstruct the clarification context**

Write `docs/requirements/examples/tamagotchi/clarification-context.yaml`
with exactly the eight fields `agents/requirements-orchestrator.md:53`
requires — `problem_domain`, `stakeholders_and_users`,
`core_functionality`, `success_criteria`, `non_functional_concerns`,
`constraints`, `out_of_scope`, `open_questions`.

Source every field from what the current set already publishes:
`requirements/assumptions.md` (A-1..A-5, D-1..D-4, Q-1..Q-4),
`requirements/glossary.md`, the requirement bodies, and
`CONSOLIDATED.md`. Do not invent content, and do not import decisions the
requirements stage did not have: **Q-1 through Q-4 all stay open** here.
Q-2's resolution belongs to Task 3 (spec D5).

- [ ] **Step 2: Have the user confirm the context**

Show the reconstructed context and get explicit confirmation before
dispatching anything. This is the replay's only human checkpoint, and a
wrong field here silently mis-generates the whole set.

- [ ] **Step 3: Generate into scratch**

```bash
export SCRATCH=$(mktemp -d)/tama-m1 && mkdir -p "$SCRATCH"
```

With the CWD set to `$SCRATCH`, run the M1 generation pipeline
(`skills/requirements/SKILL.md` Phase 5) against the confirmed context.
Instruct the formatter to emit `index.yaml` —
`agents/requirements-formatter.md:130` makes it a MAY, and spec D2
requires it for companion parity. The
`dod-generator` run at `skills/requirements/SKILL.md:249` produces
`definition-of-done.md`; keep it even if the M1 stub is thin, and note
its thinness for the README rather than hand-improving it.

- [ ] **Step 4: Gate the scratch set before it touches the repo**

```bash
python3 skills/requirements/scripts/validate_requirements.py "$SCRATCH/.sdlc/requirements"
python3 skills/requirements/scripts/lint_requirements_content.py "$SCRATCH/.sdlc/requirements"
```
Expected: validator exits 0; linter clean or every finding explainable.
If the validator fails, fix by re-dispatching the pipeline, never by
hand-editing the scratch output — a hand-patched set is not a pipeline
product and the example's whole claim is that it is one.

- [ ] **Step 5: Diff against the set being replaced**

```bash
diff -ru docs/requirements/examples/tamagotchi/requirements "$SCRATCH/.sdlc/requirements" \
  | tee "$SCRATCH/m1-divergence.diff"
```

Read it. For each divergence decide: expected under the corrected
pipeline, or a regression? Keep notes — they are Task 5's raw material.
Pay particular attention to `BR-001`: its old statement asserted the pet
"is reset to a new pet" while its own rationale called the question open.
Under spec D5 the critic must catch that internal inconsistency; confirm
the new `BR-001` either does not assert an outcome or is explicitly
conditional.

- [ ] **Step 6: Swap it in**

```bash
rm -rf docs/requirements/examples/tamagotchi/requirements
cp -r "$SCRATCH/.sdlc/requirements" docs/requirements/examples/tamagotchi/requirements
```

- [ ] **Step 7: Rebuild CONSOLIDATED.md**

There is no renderer script — it is assembled from the set. Rebuild it
from the new requirements, updating the hard-coded header numbers: the
`Validator: N/N pass` line, the `**N** atomic requirements: …` breakdown,
the low-confidence count, and the glossary-term count. Every one of them
changes.

- [ ] **Step 8: Run the gates and the suite**

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples/tamagotchi/requirements
python3 -m pytest -q
```
Expected: validator exits 0, suite green. Task 1's two tamagotchi
parametrisations are the net here — they must pass **without being
edited**. If they need editing to go green, the swap broke something.

Note: `test_validate_traceability.py::test_shipped_tamagotchi_example_is_clean`
crosses M1 and M2. It may go red here because the design set still traces
to the old requirement IDs. That is expected and is repaired by Task 3;
if it fails, record the failure and continue rather than patching the
design set now.

- [ ] **Step 9: Commit**

```bash
git add docs/requirements/examples/tamagotchi/
git commit
```
Message: `docs(sto-219): regenerate the tamagotchi requirements set`, with
the body naming the notable divergences and the `BR-001` outcome.

---

### Task 3: Regenerate the tamagotchi design set

Stage 2 of spec D10, and the largest task: it is the only one that gains
whole artifact types. Its coupled test updates land in the **same commit**
as the swap (spec D7) — a set and its goldens that disagree make a red
suite with no diagnostic value.

**Files:**
- Create: `docs/requirements/examples/tamagotchi/design-context.yaml`
- Create: `docs/requirements/examples/tamagotchi/critique-report.yaml`
- Regenerate: `docs/requirements/examples/tamagotchi/design/`
- Delete: `docs/requirements/examples/tamagotchi/design/critique-report.yaml`
- Modify: `skills/design/scripts/tests/fixtures/c4/tamagotchi-model.json`
- Modify: `skills/design/scripts/tests/test_generate_c4.py`
- Modify: `skills/design/scripts/tests/test_lint_design_content.py`

**Interfaces:**
- Consumes: the Task 2 requirement set (its IDs are what the new design
  traces from), and `.superpowers/sdd/e2e/design-context.yaml`.
- Produces: a design set including `adr/`, a complete `index.yaml`, and
  regenerated `diagrams/` whose bytes Task 3's own golden test pins.

- [ ] **Step 1: Rescue the replay input before it is lost**

`.superpowers/` is gitignored, so the original run's design context exists
only in this working copy.

```bash
cp .superpowers/sdd/e2e/design-context.yaml \
   docs/requirements/examples/tamagotchi/design-context.yaml
```

- [ ] **Step 2: Update it for the corrected pipeline**

Two edits, both required:

1. Delete the `out_of_scope` clause reading `ADRs (STO-100) and C4
   diagrams (STO-101), which do not exist yet; cross-artifact
   traceability (STO-102)`. Those exclusions are precisely what this
   ticket lifts; leaving them in instructs the pipeline to skip the
   artifact types the regeneration exists to add.
2. Re-point `requirements_root` and re-check every `inherited_open_questions`
   entry against the Task 2 set — the Q-numbering must match the
   `assumptions.md` that Task 2 just produced, not the old one.

- [ ] **Step 3: Generate into scratch**

```bash
export SCRATCH=$(mktemp -d)/tama-m2 && mkdir -p "$SCRATCH"
```

With the CWD set to `$SCRATCH`, run the M2 pipeline
(`skills/design/SKILL.md` Phase 5) against the updated context. The
formatter runs `generate_c4.py` itself and back-fills `traces_to.adr` and
`traces_to.diagrams`; do not run the generator separately.

Apply the gate stop rule: drive to `gate: pass`, and if any finding
survives three re-dispatches, stop and take it to the user.

- [ ] **Step 4: Save the passing critique report as the exhibit**

Serialise the final `critique_report` (the one returning `gate: pass`) to
`docs/requirements/examples/tamagotchi/critique-report.yaml` — the
**example root**, not inside `design/`. Then delete the old one:

```bash
git rm docs/requirements/examples/tamagotchi/design/critique-report.yaml
```

Anything under `design/` that is not a skipped companion is discovered as
an artifact and must parse as one, which is why the root is the only
correct home for it.

- [ ] **Step 5: Gate the scratch set**

```bash
python3 skills/design/scripts/validate_design.py "$SCRATCH/.sdlc/design"
python3 skills/design/scripts/lint_design_content.py "$SCRATCH/.sdlc/design"
```
Expected: validator exits 0. Confirm by inspection that `adr/` exists and
is populated, that `index.yaml` lists components, interfaces, ADRs **and**
diagrams, and that `traces_to.diagrams` is present on the components the
diagrams depict.

- [ ] **Step 6: Diff, and settle the two deferred decisions**

```bash
diff -ru docs/requirements/examples/tamagotchi/design "$SCRATCH/.sdlc/design" \
  | tee "$SCRATCH/m2-divergence.diff"
```

Spec D11 leaves two outcomes to this run. Record what actually happened:

- **The `CMP-003 ⇄ CMP-004` cycle** — broken, or kept? If kept, the reason
  goes in the README. If broken, note that `dependency-cycle` has just
  lost its only real-world input (Step 9).
- **`IF-003` and `IF-006`** — did the segregation heuristics split them?
  If not, that is a finding about the heuristics worth recording, not a
  result to force by hand.

Also check operation counts across the new interfaces: the old set had 11
of 12 with exactly two operations. Variety is the expected outcome.

- [ ] **Step 7: Swap it in**

```bash
rm -rf docs/requirements/examples/tamagotchi/design
cp -r "$SCRATCH/.sdlc/design" docs/requirements/examples/tamagotchi/design
```

- [ ] **Step 8: Regenerate the C4 test fixture and golden**

`skills/design/scripts/tests/fixtures/c4/tamagotchi-model.json` pins the
container grouping and actors that drive
`test_worked_example_generates_a_valid_diagram_set`. Update it to the
`draft_diagram_model` the c4-generator returned in Step 3, then confirm
the golden comparison passes against the newly committed diagrams:

```bash
python3 -m pytest skills/design/scripts/tests/test_generate_c4.py -q \
  -k worked_example
```
Expected: PASS. A failure here means the fixture model and the shipped
diagrams disagree — fix the fixture, never the diagrams.

- [ ] **Step 9: Update the cycle test to match reality**

The test
`test_lint_design_content.py::test_shipped_tamagotchi_example_has_the_known_cycle`
asserts exactly one `dependency-cycle` finding matched on an exact
rendered path.

- **If the cycle was kept:** update the expected path to the new one.
- **If the cycle was broken:** rewrite the test — do not delete it. The
  rule still needs coverage, so move the assertion onto a synthetic
  fixture and rename the test to say so
  (`test_dependency_cycle_is_reported_with_its_rendered_path`). Record in
  the README that the rule has lost its only real-world input and why.

- [ ] **Step 10: Run every gate and the whole suite**

```bash
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
python3 skills/design/scripts/lint_design_content.py docs/requirements/examples/tamagotchi/design
python3 skills/design/scripts/validate_traceability.py docs/requirements/examples/tamagotchi
python3 -m pytest -q
```
Expected: all validators exit 0 and the suite is green — including
`test_shipped_tamagotchi_example_is_clean`, which Task 2 may have left
red and which this task repairs.

- [ ] **Step 11: Commit**

```bash
git add -A docs/requirements/examples/tamagotchi/ skills/design/scripts/tests/
git commit
```
Message: `docs(sto-219): regenerate the tamagotchi design set`, with the
body recording the cycle decision, the IF-003/IF-006 outcome, and the
critique-report relocation.

---

### Task 4: Regenerate the GDPR requirements set

Stage 3 of spec D10 — independent of the tamagotchi chain, so it goes
last where it cannot destabilise it.

**Files:**
- Create: `docs/requirements/examples/gdpr/clarification-context.yaml`
- Regenerate: `docs/requirements/examples/gdpr/requirements/`

**Interfaces:**
- Consumes: the published GDPR set as source material.
- Produces: a validated requirement set with `index.yaml`, completing the
  companion parity spec D2 requires.

- [ ] **Step 1: Reconstruct and confirm the clarification context**

Same eight fields, same rules as Task 2 Step 1, sourced from
`gdpr/requirements/assumptions.md`, `glossary.md`,
`definition-of-done.md` and the requirement bodies. Show it to the user
and get confirmation before dispatching.

- [ ] **Step 2: Generate into scratch**

```bash
export SCRATCH=$(mktemp -d)/gdpr-m1 && mkdir -p "$SCRATCH"
```

CWD set to `$SCRATCH`, run the M1 pipeline. Instruct the formatter to
emit `index.yaml` — this set has never had one, and parity is the point.

- [ ] **Step 3: Gate the scratch set**

```bash
python3 skills/requirements/scripts/validate_requirements.py "$SCRATCH/.sdlc/requirements"
python3 skills/requirements/scripts/lint_requirements_content.py "$SCRATCH/.sdlc/requirements"
```
Expected: validator exits 0. The old set carried one `passive-nameless`
warn on `NFR-001`'s description; if it recurs, that is a finding to
explain in the README, and if it does not, that is a divergence worth
recording.

- [ ] **Step 4: Diff, swap, and confirm parity**

```bash
diff -ru docs/requirements/examples/gdpr/requirements "$SCRATCH/.sdlc/requirements"
rm -rf docs/requirements/examples/gdpr/requirements
cp -r "$SCRATCH/.sdlc/requirements" docs/requirements/examples/gdpr/requirements
diff <(ls docs/requirements/examples/gdpr/requirements) \
     <(ls docs/requirements/examples/tamagotchi/requirements)
```
Expected from the final command: no output. Both M1 sets now carry the
same companion files, which is spec D2's acceptance check.

- [ ] **Step 5: Run the gates and the suite**

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
python3 -m pytest -q
```
Expected: exit 0 and a green suite, with Task 1's two `gdpr`
parametrisations passing unedited.

- [ ] **Step 6: Commit**

```bash
git add docs/requirements/examples/gdpr/
git commit
```
Message: `docs(sto-219): regenerate the GDPR requirements set`.

---

### Task 5: Write the divergence record and rewrite the README

Lands last, once every divergence is known (spec D10). This is the task
that discharges the ticket's actual requirement — that the deviations
which remain are *chosen*, not inherited.

**Files:**
- Create: `docs/requirements/examples/tamagotchi/REGENERATION.md`
- Modify: `docs/requirements/examples/tamagotchi/README.md`

**Interfaces:**
- Consumes: the divergence notes from Task 2 Step 5, Task 3 Step 6 and
  Task 4 Step 3.
- Produces: the narrative that replaces a `gate: fail` critique report as
  the example's evidence that the tooling works.

- [ ] **Step 1: Write REGENERATION.md**

Structure it as one section per divergence, each answering: what the old
set had, what the corrected pipeline produced, and why the difference
exists. Cover at minimum the ADRs that did not previously exist, the
diagram back-fill and complete `index.yaml`, the interface granularity
and operation-count changes, the `BR-001` outcome, the cycle decision,
and the `IF-003`/`IF-006` result. Where a finding survived, say it
survived and why that was the better answer.

- [ ] **Step 2: Rewrite the README's deviation section**

Three claims stop being true and must go, not be softened:

- "The set was written on a failing gate, by human override" — with the
  whole "an ordinary run must not do this" warning that follows it.
- "`critique-report.yaml` is a hand-added exhibit" inside `design/` —
  replaced by a note that it sits at the example root and is the passing
  report.
- "The diagrams were generated after the fact", along with the paragraph
  explaining why `traces_to.diagrams` and `index.yaml` are incomplete.

Then update the **Validating the sets** section's expected results — the
`22/22`, `26/26` and per-tool expectations all change — and add a pointer
to `REGENERATION.md`. Keep the honesty the ticket asks for: every finding
still present gets named and justified.

- [ ] **Step 3: Verify every documented command still does what it says**

Run all four commands the README's Validating section lists, and confirm
the stated expected output matches byte-for-byte what they now print. A
README that documents the wrong pass count is the exact failure mode this
ticket exists to end.

- [ ] **Step 4: Run the whole suite one final time**

```bash
python3 -m pytest -q
```

- [ ] **Step 5: Commit**

```bash
git add docs/requirements/examples/tamagotchi/
git commit
```
Message: `docs(sto-219): record the regeneration divergences`.

---

## Definition of Done

- [ ] All three sets regenerated through the pipeline; no hand-edited
      artifacts.
- [ ] Both structural validators exit 0 on all three sets.
- [ ] Content linters clean, or every finding explained in the README.
- [ ] `design/adr/` exists and is populated.
- [ ] `traces_to.diagrams` back-filled; `index.yaml` lists every artifact
      type including diagrams.
- [ ] Both M1 sets carry identical companion files.
- [ ] `critique-report.yaml` is the passing report and sits at the example
      root.
- [ ] The cycle decision and the IF-003/IF-006 outcome are both stated,
      not inherited.
- [ ] Suite green; Task 1's four tests passed throughout without edits.
- [ ] README documents no claim that is no longer true.

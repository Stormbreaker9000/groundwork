# M2 Architecture Generation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the M2 architecture stage — a `design` skill that interviews for technology context, and a five-agent pipeline that turns a validated requirement set into atomic component and interface specs under `.sdlc/design/`.

**Architecture:** A `SKILL.md` runs a five-phase conversation (read requirements → hypothesise → interview → synthesise `design_context` → generate). The orchestrator reads the requirement set, identifies architecturally significant requirements, allocates `CMP`/`IF` ID blocks, and dispatches serially to a component specialist then an interface specialist. Because components declare `depends_on: [IF-…]` and interfaces declare `provider: CMP-…`, the authoring cycle is broken by having components declare *capabilities* in prose, interfaces satisfy them, and the orchestrator mechanically back-fill `depends_on`. A critic gates on ISO 42010 + ATAM-lite plus `validate_design.py`, then a formatter writes files.

**Tech Stack:** Python 3.12 (stdlib, with optional `pyyaml` + `jsonschema`), pytest, Markdown + YAML frontmatter agent/skill files. No new dependencies.

## Global Constraints

- **Read `docs/superpowers/specs/2026-07-30-m2-architecture-pipeline-design.md` before starting.** Task steps cite its section numbers (A.1–A.7, D.1–D.8) for the authoritative contract YAML. It is committed at `5bb4678`.
- Agent files live flat in `agents/` with YAML frontmatter containing exactly one key, `description:`. Match the existing style in `agents/requirements-orchestrator.md`.
- Skill files live at `skills/<name>/SKILL.md` with `name:` and `description:` frontmatter.
- No new runtime dependencies. The validator must keep degrading gracefully when `pyyaml`/`jsonschema` are absent.
- IDs: `^(CMP|IF)(-[A-Z0-9]+)*-[0-9]{3,}$`. The prefix must equal `type` — `CMP-`→`component`, `IF-`→`interface`. IDs are never reused; set `status: obsolete` instead.
- Project artifacts gate on **headings only**. Content is never gated; `None identified` is always legal.
- A single `created_at` date is passed to every specialist so all files agree.
- **No files are written before the user's sign-off.** This is the M1 invariant and it carries over unchanged.
- Every existing test must stay green. Exactly one existing test changes (`test_skip_files_and_subtrees_are_ignored` gains one assertion). If any other test needs rewriting, the change is wrong.
- Commit messages: `<type>(sto-99): <subject>`, and end with `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `skills/design/scripts/validate_design.py` | **Modify.** Add the `drivers.md` skip entry, gate, and export. |
| `skills/design/scripts/tests/test_validate_design.py` | **Modify.** Three unit tests, two parametrized cases, one added assertion. |
| `skills/design/scripts/tests/fixtures/**` | **Modify + create.** `drivers.md` in the valid set and the 8 existing invalid cases; two new invalid case dirs. |
| `agents/design-orchestrator.md` | **Create.** Owns every hand-off contract, ASR identification, ID allocation, the back-fill algorithm, and the STO-100/101 slots. |
| `agents/component-specialist.md` | **Create.** Decomposes into `CMP-` artifacts; declares `required_capabilities`. |
| `agents/interface-specialist.md` | **Create.** Turns capabilities into `IF-` artifacts with `provider`, `consumed_by`, `satisfies_capabilities`. |
| `agents/design-critic.md` | **Create.** 42010 per-artifact review, ATAM-lite ASR coverage, `validate_design.py` hard gate. |
| `agents/design-formatter.md` | **Create.** Writes `CMP`/`IF` files, `assumptions.md`, `drivers.md`, `index.yaml`. |
| `skills/design/SKILL.md` | **Create.** The five-phase conversation and the sign-off gate. |
| `commands/groundwork.md` | **Modify.** Add the `design` workflow entry. |
| `docs/requirements/examples/tamagotchi/design/` | **Create.** The end-to-end worked example. |

Task 1 is the only task with executable code and therefore the only one with unit tests. Tasks 2–6 produce prompt files; their verification is structural (frontmatter parses, contract names agree across producer and consumer) plus the end-to-end run in Task 7. This mirrors M1, where no agent has a unit test.

**Deliberate divergence from the spec's Part H.** The spec sequences four commits, with all five agent files in one. This plan splits that into four tasks (2–5) and splits Task 1 into two commits — eight total. The reason is reviewability: the orchestrator owns every contract, the two specialists only make sense reviewed as a pair, and the critic and formatter are independently rejectable. A reviewer can meaningfully approve the specialists while sending the critic back, which is the test for where a task boundary belongs. The order and content of the work are unchanged.

---

### Task 1: Gate `drivers.md` in the design validator

**Files:**
- Modify: `skills/design/scripts/validate_design.py:89` (SKIP_FILENAMES), `:100-101` (artifact constants), `:253-265` (gate functions), `:296` (wiring), `:1-60` (docstring)
- Modify: `skills/design/scripts/tests/test_validate_design.py:56-66` (INVALID_CASES), `:42-50` (skip test)
- Create: `skills/design/scripts/tests/fixtures/valid/drivers.md`
- Create: `skills/design/scripts/tests/fixtures/invalid/missing_drivers/` (components + assumptions.md, no drivers.md)
- Create: `skills/design/scripts/tests/fixtures/invalid/drivers_missing_heading/` (components + assumptions.md + a drivers.md missing one heading)
- Modify: `drivers.md` added to the 8 existing invalid fixture dirs

**Interfaces:**
- Consumes: `artifact_core._check_project_artifact(root_dir, filename, required_headings, label, hint) -> List[str]` (already generalised by STO-197).
- Produces: `validate_design.DRIVERS_ARTIFACT` (str), `validate_design.REQUIRED_DRIVERS_HEADINGS` (List[str]), `validate_design.check_drivers_artifact(design_dir: str) -> List[str]`. STO-208's linter will import `DRIVERS_ARTIFACT` the way `lint_requirements_content.py` imports `GLOSSARY_ARTIFACT`.

- [ ] **Step 1: Write the failing unit tests**

Append to `skills/design/scripts/tests/test_validate_design.py`, after the existing assumptions-artifact tests (they end around line 180):

```python
# ---------------------------------------------------------------------------
# Drivers artifact (STO-99): ASRs / Tradeoffs / Sensitivity Points
# ---------------------------------------------------------------------------
DRIVERS_OK = (
    "# Design Drivers\n\n"
    "## Architecturally Significant Requirements\n- None identified.\n\n"
    "## Tradeoffs\n- None identified.\n\n"
    "## Sensitivity Points\n- None identified.\n"
)


def test_drivers_artifact_ok(tmp_path):
    (tmp_path / "drivers.md").write_text(DRIVERS_OK, encoding="utf-8")
    assert vd.check_drivers_artifact(str(tmp_path)) == []


def test_missing_drivers_is_flagged(tmp_path):
    errors = vd.check_drivers_artifact(str(tmp_path))
    assert any("drivers artifact" in e for e in errors)


def test_drivers_missing_heading_is_flagged(tmp_path):
    truncated = DRIVERS_OK.split("## Sensitivity Points")[0]
    (tmp_path / "drivers.md").write_text(truncated, encoding="utf-8")
    errors = vd.check_drivers_artifact(str(tmp_path))
    assert any(
        "missing required heading" in e and "Sensitivity Points" in e for e in errors
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k drivers -v`
Expected: 3 FAILED with `AttributeError: module 'validate_design' has no attribute 'check_drivers_artifact'`

- [ ] **Step 3: Implement the constants and the gate**

In `skills/design/scripts/validate_design.py`, directly after the `REQUIRED_ASSUMPTIONS_HEADINGS` line (currently line 101), add:

```python
# Project-level drivers artifact (STO-99). Persists the ASR analysis, tradeoffs,
# and sensitivity points the critic produces, so the reasoning behind the
# decomposition survives the conversation that produced it (design spec A.6).
DRIVERS_ARTIFACT = "drivers.md"
REQUIRED_DRIVERS_HEADINGS = [
    "## Architecturally Significant Requirements",
    "## Tradeoffs",
    "## Sensitivity Points",
]
```

Then, immediately after the existing `check_assumptions_artifact` function (currently ending line 265), add:

```python
def check_drivers_artifact(design_dir: str) -> List[str]:
    """Architectural-drivers artifact (hard gate).

    Presence plus the three headings, gated by the shared core. As with the
    assumptions artifact, content is never gated — an honest 'None identified'
    section is legal and passes.
    """
    return core._check_project_artifact(
        design_dir,
        DRIVERS_ARTIFACT,
        REQUIRED_DRIVERS_HEADINGS,
        "drivers artifact",
        "Architecturally Significant Requirements / Tradeoffs / Sensitivity Points",
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k drivers -v`
Expected: 3 PASSED

Run: `python3 -m pytest skills/design/scripts/tests -q`
Expected: all PASSED — the gate is defined but not yet wired into `validate()`, so nothing else changes.

- [ ] **Step 5: Commit the gate function**

```bash
git add skills/design/scripts/validate_design.py skills/design/scripts/tests/test_validate_design.py
git commit -m "$(cat <<'EOF'
feat(sto-99): add the drivers.md project-artifact gate

Presence plus three headings, via the shared _check_project_artifact helper
STO-197 generalised. Not yet wired into validate() — that lands with the
fixtures in the next commit, so the valid set never goes red.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Create the valid fixture's `drivers.md`**

Create `skills/design/scripts/tests/fixtures/valid/drivers.md`. It must reference the same `CMP`/`IF` IDs the existing valid fixture uses (`CMP-001` order-service, `CMP-002` stripe-gateway, `IF-001` payment-api):

```markdown
# Design Drivers

The architecturally significant requirements behind this decomposition, the
tradeoffs taken, and the points where a small change to a decision would move a
quality attribute sharply.

## Architecturally Significant Requirements
- NFR-001 (quality_attribute) — the confidentiality budget on payment data is
  what forces the gateway behind an explicit contract (IF-001) rather than an
  in-process call.
- CON-001 (constraint) — the single-writer database boundary constrains
  CMP-001's persistence strategy.

## Tradeoffs
- Routing all card traffic through IF-001 gains an auditable boundary and a
  single place to enforce the confidentiality budget; it costs a synchronous
  hop on the checkout path, which spends part of NFR-001's latency budget.

## Sensitivity Points
- IF-001's `interaction: synchronous` choice. Switching it to asynchronous
  would relax the latency budget but breaks the read-after-write expectation
  CMP-001 relies on. Affects NFR-001.
```

- [ ] **Step 7: Create the two new invalid fixture directories**

Run from the repo root (the paths below are absolute-from-root, so no `cd` is needed and none of the later steps inherit a moved working directory):

```bash
F=skills/design/scripts/tests/fixtures
mkdir -p "$F/invalid/missing_drivers/components" "$F/invalid/drivers_missing_heading/components"
for d in missing_drivers drivers_missing_heading; do
  cp "$F/valid/components/CMP-001-order-service.md" "$F/invalid/$d/components/"
  cp "$F/valid/assumptions.md" "$F/invalid/$d/"
done
```

`CMP-001-order-service.md` declares `depends_on: [IF-001]`, which will not resolve in a components-only fixture. Strip it so each case fails for exactly its intended reason — edit both copies so the frontmatter reads:

```yaml
depends_on: []
```

Then give `drivers_missing_heading/` a `drivers.md` that omits the third heading:

```markdown
# Design Drivers

## Architecturally Significant Requirements
- None identified.

## Tradeoffs
- None identified.
```

`missing_drivers/` gets no `drivers.md` at all.

- [ ] **Step 8: Add `drivers.md` to all 9 existing invalid fixtures**

The design suite's convention is that each invalid case fails for exactly one reason (unlike M1's, where `bad_enum/` also trips the missing-companion gates). Preserve it. From the repo root:

```bash
F=skills/design/scripts/tests/fixtures
for d in assumptions_missing_heading bad_enum dangling_depends_on dangling_provider \
         duplicate_id missing_assumptions missing_required_field prefix_type_mismatch \
         traces_from_bad_format; do
  cp "$F/valid/drivers.md" "$F/invalid/$d/drivers.md"
done
```

All 9 existing directories get one, including `missing_assumptions/` — it needs `drivers.md` precisely so its only remaining failure is the missing assumptions file. Verify:

```bash
ls skills/design/scripts/tests/fixtures/invalid/*/drivers.md | wc -l
```
Expected: `10` — the 9 above plus the `drivers_missing_heading/` copy from Step 7. `missing_drivers/` correctly has none.

- [ ] **Step 9: Register the new cases and the skip assertion**

In `skills/design/scripts/tests/test_validate_design.py`, add two entries to `INVALID_CASES` (keep the dict alphabetically tidy):

```python
    "missing_drivers": "drivers artifact",
    "drivers_missing_heading": "missing required heading",
```

And add one line to `test_skip_files_and_subtrees_are_ignored`, after the `index.yaml` assertion:

```python
    assert "drivers.md" not in out
```

- [ ] **Step 10: Run tests to verify the new cases fail**

Run: `python3 -m pytest skills/design/scripts/tests -q -k "missing_drivers or drivers_missing_heading"`
Expected: 2 FAILED — the validator still exits 0 on both, because `check_drivers_artifact` is not wired into `validate()` yet.

- [ ] **Step 11: Wire the gate in**

In `skills/design/scripts/validate_design.py`, change `SKIP_FILENAMES` (line 89) from:

```python
SKIP_FILENAMES = {"assumptions.md", "index.yaml"}
```

to:

```python
SKIP_FILENAMES = {"assumptions.md", "drivers.md", "index.yaml"}
```

Then in `validate()` (line 296), after the existing assumptions call, add the drivers call:

```python
    global_errors = cross_file_checks(files)
    global_errors.extend(check_assumptions_artifact(design_dir))
    global_errors.extend(check_drivers_artifact(design_dir))
    return files, global_errors
```

Skipping the file is not optional: without the `SKIP_FILENAMES` entry, discovery would try to parse `drivers.md` as a `CMP-`/`IF-` artifact and fail — the same reason `assumptions.md` is already skipped.

- [ ] **Step 12: Update the module docstring**

In the docstring's directory sketch (line 12), add the drivers line under `assumptions.md`:

```
      assumptions.md                (gated: Assumptions/Dependencies/Open Questions)
      drivers.md                    (gated: ASRs/Tradeoffs/Sensitivity Points)
      index.yaml                    (skipped)
```

And extend the numbered list item 5 (line 32) to read:

```
  5. Gates the project-level ``assumptions.md`` and ``drivers.md`` (presence +
     required headings).
```

- [ ] **Step 13: Run the full suite**

Run: `python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q`
Expected: all PASSED, including the two new invalid cases. Confirm the count went up by 5 (3 unit tests + 2 parametrized cases) and that no pre-existing test failed.

- [ ] **Step 14: Verify the stdlib fallback path still works**

Run: `python3 -m pytest skills/design/scripts/tests -q -k fallback`
Expected: PASSED. The gate uses the shared `_check_project_artifact`, which never touched jsonschema, so the fallback path is unaffected — this step confirms rather than fixes.

- [ ] **Step 15: Commit**

```bash
git add skills/design/scripts/ && git commit -m "$(cat <<'EOF'
feat(sto-99): wire the drivers.md gate into the design validator

Adds the skip-list entry (without it, discovery parses drivers.md as an
artifact and fails), the validate() call, fixtures, and two invalid cases.

drivers.md is copied into every existing invalid fixture so each case keeps
failing for exactly one reason — the design suite's convention, which is
stricter than M1's and worth preserving.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: The design orchestrator agent

**Files:**
- Create: `agents/design-orchestrator.md`
- Reference: `agents/requirements-orchestrator.md` (the M1 analogue — match its structure and voice)

**Interfaces:**
- Consumes: `design_context` from `skills/design/SKILL.md` Phase 4 (spec D.1). Fields: `requirements_root`, `system_purpose`, `runtime_and_stack`, `persistence`, `deployment_target`, `integration_points`, `operational_constraints`, `team_constraints`, `out_of_scope`, `inherited_open_questions[]{id,statement,disposition,resolution}`, `inherited_review_queue[]`.
- Produces:
  - `generation_brief` (spec D.2) → consumed by Tasks 3's two specialists. Fields: `context`, `requirements_digest[]{id,type,title,description,measure,priority,confidence}`, `asr_analysis`, `target_category`, `id_block{prefix,start}`, `created_at`, and `component_set` (interface brief only).
  - `asr_analysis` (spec D.3): `[]{requirement_id, driver_type, significance}` where `driver_type ∈ {quality_attribute, constraint, business_rule, high_impact_function}`.
  - `design_context_artifact` (spec D.7) → consumed by Task 5's formatter.

- [ ] **Step 1: Write the agent file**

Create `agents/design-orchestrator.md`. Frontmatter is a single `description:` key, matching `agents/requirements-orchestrator.md:1-3`:

```markdown
---
description: Routes the design context object through the architecture generation pipeline. Identifies architecturally significant requirements, allocates categorical zero-padded CMP/IF IDs, dispatches to the component and interface specialists, back-fills the depends_on edge, then routes through the critic and formatter. Owns the explicit hand-off data shapes passed between every stage.
---
```

The body must contain these sections, in this order:

1. **Role statement.** You do not write design prose and do not write code. You plan, identify ASRs, allocate IDs, route typed objects, and perform the mechanical back-fill. Mirror the opening of `agents/requirements-orchestrator.md:5-16`.
2. **Pipeline overview** — reproduce the ASCII diagram from spec Part B verbatim, including the two slot markers.
3. **Stage 1 — Consume the `design_context`.** Reproduce the D.1 YAML block. State: if any field is missing or malformed, stop and report to the caller rather than guessing. Treat `out_of_scope` as a hard exclusion list.
4. **Stage 2 — Read the requirement set.** Read every file under `context.requirements_root`. Build `requirements_digest` from the **full set, not just the ASRs** — the component specialist needs every FR to decompose against. Specialists never re-read the files; the digest is their only view.
5. **Stage 3 — Identify ASRs.** Produce `asr_analysis` (D.3). An NFR carrying a quality-attribute scenario is architecturally significant by default. A CON or BR is significant when it bounds structure rather than behaviour. An FR is significant only when it is high-impact — it forces a component that would not otherwise exist, or it crosses a trust or process boundary. Record `significance` as *why this one shapes structure*, never a restatement of the requirement.
6. **Stage 4 — Allocate ID blocks.** You are the single ID authority. `CMP-001…` and `IF-001…`, three-digit zero-padded, contiguous blocks per prefix. The prefix must equal `type`. IDs are stable and never reused (`status: obsolete` instead). Pass one `created_at` to every specialist.
7. **Stage 5 — Dispatch the `generation_brief`.** Reproduce the D.2 YAML block. State the fixed serial order explicitly: **component specialist first, then interface specialist** — the latter needs `component_set` to assign `provider` and resolve capabilities. This is the M2 analogue of M1's constraint specialist running last.
8. **Stage 6 — Collect drafts.** Reproduce both D.4 YAML blocks. Mark `required_capabilities`, `consumed_by`, and `satisfies_capabilities` as TRANSIENT in the prose — they must never reach a file.
9. **Stage 7 — Back-fill.** Reproduce the three-step D.5 algorithm exactly. Add the rationale for step 2 in one sentence: a dropped edge is invisible because `depends_on: []` is legal frontmatter, so the artifacts would validate while being quietly wrong.
10. **Stage 8 — Critique gate.** Reproduce the D.6 `critique_report` block. `unaddressed` fails the gate; `deferred_to_decision` passes but forces a `Q-` open question. Re-dispatch only affected artifacts. Never advance to the formatter without `gate: pass`.
11. **Stage 9 — Synthesise the `design_context_artifact`.** Reproduce the D.7 block. State the ordering rationale: this runs *after* the gate because the critic's tradeoffs and sensitivity points are inputs to it, not consumers of it — the same argument STO-135 settled for the glossary. Inherited `Q-` IDs are preserved; newly raised questions continue the sequence. Empty sections emit `None identified`.
12. **Stage 10 — Format.** Reproduce the D.8 `formatter_result` block. Report it to the caller, which owns sign-off and commit. **You never commit.**
13. **Stages 11 and 12 — the unfilled slots.** Declare both as named post-formatter stages:

```markdown
## Stage 11 — ADR generation (SLOT — owned by STO-100)

Not implemented. When STO-100 lands, this stage runs after the formatter and
receives the written artifact set plus `design_context_artifact.drivers`, and
returns the ADR files it wrote for `traces_to.adr` back-population. Until then,
a `deferred_to_decision` ASR is recorded as a `Q-` open question in
`assumptions.md` instead of an ADR. Do not invent ADR files.

## Stage 12 — C4 diagram generation (SLOT — owned by STO-101)

Not implemented. When STO-101 lands, this stage receives the component and
interface set and returns the diagram files it wrote for `traces_to.diagrams`
back-population. Do not invent diagram files.
```

14. **Gotchas**, mirroring `agents/requirements-orchestrator.md:281-296`. At minimum: you are the only ID authority; never generate anything in `out_of_scope`; pass one `created_at` to everyone; an unsatisfied capability is a re-dispatch, never an accepted gap; any `CMP`/`IF` resting on an unresolved inherited question is `confidence: low`; the low-confidence set must agree across the artifacts, `index.yaml`'s `review_queue`, and the skill's summary — low in all three places or none.

- [ ] **Step 2: Verify the frontmatter parses**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from artifact_core import extract_frontmatter_block
b = extract_frontmatter_block(open('agents/design-orchestrator.md', encoding='utf-8').read())
assert b is not None, 'no frontmatter block found'
assert b.strip().startswith('description:'), b[:80]
print('frontmatter OK')
"
```
Expected: `frontmatter OK`

Note `extract_frontmatter_block` takes the file's **contents**, not a path — `parse_frontmatter` is the path-taking one. Getting this backwards raises `TypeError` on the regex match.

- [ ] **Step 3: Verify every contract is present**

Run:
```bash
for k in design_context generation_brief asr_analysis draft_components \
         draft_interfaces critique_report design_context_artifact formatter_result \
         required_capabilities consumed_by satisfies_capabilities; do
  grep -q "$k" agents/design-orchestrator.md && echo "ok   $k" || echo "MISS $k"
done
```
Expected: eleven `ok` lines, no `MISS`.

- [ ] **Step 4: Commit**

```bash
git add agents/design-orchestrator.md && git commit -m "$(cat <<'EOF'
feat(sto-99): add the design orchestrator agent

Owns every hand-off contract in the M2 pipeline, ASR identification, CMP/IF ID
allocation, and the mechanical depends_on back-fill that breaks the CMP <-> IF
authoring cycle. Declares the STO-100 (ADR) and STO-101 (C4) slots as named
post-formatter stages so those tickets add an agent and a dispatch line rather
than reopening the pipeline's shape.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: The component and interface specialists

These two ship together: the cycle-break (spec A.3) is the contract *between* them, and reviewing one without the other cannot tell you whether the capability hand-off closes.

**Files:**
- Create: `agents/component-specialist.md`
- Create: `agents/interface-specialist.md`
- Reference: `agents/fr-specialist.md` and `agents/nfr-specialist.md` for structure and voice

**Interfaces:**
- Consumes: `generation_brief` from Task 2 (spec D.2). The interface specialist's brief additionally carries `component_set`, each entry `{id, title, responsibility, boundary, required_capabilities}`.
- Produces:
  - Component specialist → `draft_components` (spec D.4). Every item sets `depends_on: []` and carries `required_capabilities[]{capability, rationale}`.
  - Interface specialist → `draft_interfaces` (spec D.4). Every item carries `provider` (exactly one `CMP-` ID), `operations[]{name, summary}` (minItems 1), `interaction`, `error_modes` (minItems 1), `consumed_by[]`, and `satisfies_capabilities[]{component, capability}`.
  - Both MAY return sibling `assumptions` and `dependencies` lists (plain statements), which feed the orchestrator's Stage 9 only. Neither returns `terms` — design inherits the requirements glossary and does not grow a second one (STO-197 A.2).

- [ ] **Step 1: Write `agents/component-specialist.md`**

```markdown
---
description: Component decomposition specialist. Converts the orchestrator's generation_brief into atomic component specs (CMP-), each with a single clear responsibility, an internal/external boundary, and its required capabilities declared in prose rather than interface IDs. Returns a draft_components object with depends_on left empty for the orchestrator to back-fill.
---
```

Required body sections:

1. **Role.** You decompose the system into components and author their specs. You do **not** invent `IF-` IDs and you do **not** populate `depends_on` — leave it `[]`. The orchestrator back-fills it after the interface specialist has run. Explain why in one sentence: interfaces do not exist yet, so any ID you wrote would be a guess.
2. **Input.** Reproduce the D.2 `generation_brief` block. Note that `requirements_digest` is your only view of the requirements — do not read the files yourself.
3. **How to decompose.** Drive the decomposition from `asr_analysis` first, then sweep `requirements_digest` for functionality no component yet owns. Rules, each stated as a rule:
   - One component, one responsibility. If `responsibility` needs an "and", split it.
   - Every external system named in `context.integration_points` becomes a component with `boundary: external`. The graph must be total — a dependency cannot point outside it (STO-197 A.4).
   - Prefer fewer, well-bounded components over many thin ones. Do not create a component per requirement.
   - `traces_from` lists the requirement IDs this component satisfies. May be empty for pure infrastructure, but an empty one is worth questioning.
4. **Declaring capabilities.** This is the load-bearing part. For every dependency the component has, add a `required_capabilities` entry describing *what it needs done*, in domain terms, with a `rationale`. Give worked examples of the distinction:
   - Good: `capability: "take card payments"` — names the need.
   - Bad: `capability: "call the Stripe API"` — names a mechanism, and pre-decides the interface.
   - Bad: `capability: "use CMP-002"` — names a component; the edge must go through an interface.
   State the consequence: every capability becomes exactly one interface. A capability you omit becomes a dependency the architecture does not record.
5. **Output.** Reproduce the `draft_components` block from D.4 verbatim, including the TRANSIENT marker on `required_capabilities`.
6. **Body rendering.** `body_markdown` is the file's prose below the frontmatter: an H1 title line, the description, the responsibility in full, and a short rationale tying the component to the requirements it traces from.
7. **Confidence.** `confidence: low` when the component rests on an unresolved `inherited_open_questions` item; name the `Q-` ID in the body. Otherwise `medium` or `high`.
8. **Gotchas.** Never emit `depends_on` with content. Never coin `IF-` IDs. Never exceed your `id_block`. Never generate anything in `out_of_scope`. Use the `created_at` you were given.

- [ ] **Step 2: Write `agents/interface-specialist.md`**

```markdown
---
description: Interface design specialist. Converts each component's declared capabilities into atomic interface specs (IF-) at architecture altitude — provider, operations, interaction style, and error modes — and reports which components consume each contract so the orchestrator can back-fill depends_on. Returns a draft_interfaces object.
---
```

Required body sections:

1. **Role.** You turn declared capabilities into interface contracts. You run *after* the component specialist and receive the full `component_set`.
2. **Input.** Reproduce the D.2 block, noting that your brief carries `component_set` with each component's `required_capabilities`.
3. **The core rule.** Every `required_capability` across the whole `component_set` must be satisfied by **exactly one** interface. Not zero, not two. State that the orchestrator verifies this and will re-dispatch to you on either failure (spec A.4, D.5 step 2).
   - Two components needing the same capability from the same provider share one interface; list both in `consumed_by`.
   - The same capability from different providers is two interfaces.
4. **Assigning `provider`.** Exactly one `CMP-` ID from `component_set`, the component that *implements* the contract — never the one that consumes it. For an external system, the provider is that system's `boundary: external` component.
5. **Authoring at architecture altitude.** `operations` is `{name, summary}` — no payload schemas, no versioning, no auth, no transport (STO-197 C.3). Enough for a C4 component diagram and for tracing, not OpenAPI in YAML.
6. **`error_modes` is mandatory, minimum one.** State the reasoning from the STO-197 spec: an interface that does not say how it fails is how the missing-error-paths gap returns at the architecture layer. Give examples of real modes (provider unreachable, request rejected, timeout with unknown commit state) versus non-answers ("error").
7. **`interaction`.** `synchronous` when the consumer blocks on the result; `asynchronous` otherwise. When the choice is genuinely close, say so in the body — the critic looks for sensitivity points, and this is a common one.
8. **Output.** Reproduce the `draft_interfaces` block from D.4 verbatim, with the TRANSIENT markers on `consumed_by` and `satisfies_capabilities`.
9. **Gotchas.** Never invent a capability nobody declared. Never leave `operations` or `error_modes` empty. Never name a provider outside `component_set`. Never exceed your `id_block`. Use the `created_at` you were given.

- [ ] **Step 3: Verify both files' frontmatter parses**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from artifact_core import extract_frontmatter_block
for p in ['agents/component-specialist.md', 'agents/interface-specialist.md']:
    b = extract_frontmatter_block(open(p, encoding='utf-8').read())
    assert b is not None and b.strip().startswith('description:'), p
    print('frontmatter OK', p)
"
```
Expected: two `frontmatter OK` lines.

- [ ] **Step 4: Verify the capability hand-off names agree across all three agents**

This is the check that catches a renamed field silently breaking the cycle-break:

```bash
for k in required_capabilities satisfies_capabilities consumed_by; do
  n=$(grep -l "$k" agents/design-orchestrator.md agents/component-specialist.md \
        agents/interface-specialist.md 2>/dev/null | wc -l)
  echo "$k: $n file(s)"
done
```
Expected: `required_capabilities: 3`, `satisfies_capabilities: 2`, `consumed_by: 2`.
(`required_capabilities` appears in all three — declared by the component specialist, consumed by the interface specialist, verified by the orchestrator. The other two are written by the interface specialist and read by the orchestrator.)

- [ ] **Step 5: Commit**

```bash
git add agents/component-specialist.md agents/interface-specialist.md && git commit -m "$(cat <<'EOF'
feat(sto-99): add the component and interface specialists

The pair that breaks the CMP <-> IF authoring cycle: components declare
required capabilities in prose without interface IDs, and the interface
specialist satisfies each one exactly once while reporting consumed_by for the
orchestrator's back-fill.

They ship together because the capability hand-off is the contract between
them; neither is reviewable alone.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: The design critic

**Files:**
- Create: `agents/design-critic.md`
- Reference: `agents/requirements-critic.md` (the M1 analogue — match its two-phase comprehension/critique separation)

**Interfaces:**
- Consumes: the merged, back-filled `draft_components` + `draft_interfaces` set from the orchestrator, plus `asr_analysis` (spec D.3) and the `requirements_digest`.
- Produces: `critique_report` (spec D.6). Fields: `gate`, `validator{command,exit_code,summary}`, `per_artifact[]{id,verdict,findings}`, `asr_coverage[]{requirement_id,addressed_by,verdict}`, `tradeoffs[]{decision,gains,costs,affected}`, `sensitivity_points[]{point,affected_requirements,note}`.

- [ ] **Step 1: Write the agent file**

```markdown
---
description: Architecture quality critic. Runs a three-phase review over the merged design set — an ISO/IEC/IEEE 42010 per-artifact quality gate, an ATAM-lite check that every architecturally significant requirement is addressed with its tradeoffs and sensitivity points named, and the structural validator as a hard gate. Returns a critique_report.
---
```

Required body sections:

1. **Role and the separation rule.** Comprehend the set first, critique second, and keep the two separate — the same discipline `agents/requirements-critic.md` enforces, for the same reason: interleaving them produces over-correction.
2. **Phase 1 — per-artifact quality (ISO/IEC/IEEE 42010).** Per artifact, verdict `pass` or `revise` with findings. Check at minimum:
   - `responsibility` states one purpose. An "and" joining two duties is a `revise`.
   - `description` is a claim about what the element *is*, not a restatement of its title.
   - Interfaces: `operations` cover the capabilities the contract exists to serve; `error_modes` name real failures rather than the word "error"; `interaction` matches how the body describes the consumer waiting.
   - `traces_from` is plausible — the element genuinely serves the requirements it claims.
   - `boundary: external` components are things the project does not build.
3. **Phase 2 — ASR coverage (ATAM-lite).** For every entry in `asr_analysis`, emit an `asr_coverage` row:
   - `addressed` — a named component, interface, or set of them demonstrably serves it. List the IDs.
   - `deferred_to_decision` — it turns on a decision not yet made. Legal, but it forces a `Q-` open question downstream.
   - `unaddressed` — nothing in the set serves it. **This fails the gate.**
   Then name the **tradeoffs** (a decision that helps one quality attribute at another's cost) and the **sensitivity points** (a decision where a small change moves a quality attribute sharply). State that a set with no tradeoffs at all is itself suspicious and worth a finding — every real architecture trades something.
4. **Phase 3 — the structural hard gate.** Run:
   ```bash
   python3 skills/design/scripts/validate_design.py .sdlc/design
   ```
   Record `command`, `exit_code`, and a one-line summary. **A non-zero exit forces `gate: fail`** regardless of Phases 1 and 2.
5. **Gate arithmetic**, stated unambiguously: `gate: pass` requires a zero validator exit, no `revise` verdicts, and no `unaddressed` ASRs. Anything else is `gate: fail`.
6. **Output.** Reproduce the D.6 `critique_report` block verbatim.
7. **Scope boundaries.** State what you do **not** check, and who owns it:
   - `traces_from` *resolution* against `.sdlc/requirements/` — STO-102.
   - Every FR being addressed by some component — STO-102.
   - Dependency cycles, orphan interfaces, vague `responsibility` prose — STO-208's content linter.
   Flagging these is duplicated work that will disagree with the owning tool.

- [ ] **Step 2: Verify the frontmatter parses and the validator command is exact**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from artifact_core import extract_frontmatter_block
b = extract_frontmatter_block(open('agents/design-critic.md', encoding='utf-8').read())
assert b is not None and b.strip().startswith('description:')
print('frontmatter OK')
"
grep -c "skills/design/scripts/validate_design.py" agents/design-critic.md
```
Expected: `frontmatter OK`, then a count of at least 1. The path must match the one in the orchestrator's D.6 block exactly — a stale path here means the hard gate silently never runs.

- [ ] **Step 3: Commit**

```bash
git add agents/design-critic.md && git commit -m "$(cat <<'EOF'
feat(sto-99): add the design critic

Three phases: ISO/IEC/IEEE 42010 per-artifact quality, ATAM-lite ASR coverage
with tradeoffs and sensitivity points named, and validate_design.py as the hard
gate. 42010 and ATAM are the direct architecture analogues of M1's 29148 and
25010, and the NFR quality-attribute scenarios M1 emits are ATAM inputs already.

Explicitly scoped off STO-102's tracing and STO-208's lint tier.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: The design formatter

**Files:**
- Create: `agents/design-formatter.md`
- Reference: `agents/requirements-formatter.md` (the M1 analogue — match its file-writing discipline)

**Interfaces:**
- Consumes: the critic-approved artifact set plus `design_context_artifact` (spec D.7) from the orchestrator.
- Produces: `formatter_result` (spec D.8). Fields: `files_written[]`, `index`, `review_queue_count`, `context_artifact`, `drivers`, `validator_rerun{exit_code}`.
- Depends on Task 1: the headings it writes into `drivers.md` must match `validate_design.REQUIRED_DRIVERS_HEADINGS` exactly, or the gate fails.

- [ ] **Step 1: Write the agent file**

```markdown
---
description: Design artifact formatter. Takes the critic-approved design set and writes one atomic Markdown+YAML file per component and interface into the correct .sdlc/design subdirectory, named <ID>-<kebab-title>.md, plus the project-level assumptions.md, drivers.md, and index.yaml. Returns a formatter_result.
---
```

Required body sections:

1. **Role.** You write files and nothing else. You do not author prose, revise artifacts, or commit. Run only after the critic returns `gate: pass`.
2. **Directory layout.** Reproduce the spec's Part E tree. Create directories as needed:
   ```bash
   mkdir -p .sdlc/design/{components,interfaces}
   ```
   Do **not** create `adr/` or `diagrams/` — STO-100 and STO-101 own those, and an empty directory misrepresents what this stage produced.
3. **File naming.** `<ID>-<kebab-title>.md`. Kebab-case the `title` field: lowercase, non-alphanumerics to hyphens, collapse runs, strip leading and trailing hyphens. `CMP-001` with title "Order Service" → `components/CMP-001-order-service.md`. Components go in `components/`, interfaces in `interfaces/`.
4. **File body.** YAML frontmatter delimited by `---`, then `body_markdown` verbatim. Emit frontmatter keys in the schema's declaration order so regenerated files diff cleanly. Never write `required_capabilities`, `consumed_by`, or `satisfies_capabilities` — they are transient and the schema's `unevaluatedProperties: false` will reject them.
5. **`assumptions.md`.** Exactly these three H2 headings, in this order:
   ```markdown
   ## Assumptions
   ## Dependencies
   ## Open Questions
   ```
   Render `A-#`, `D-#`, `Q-#` items as bullets, preserving inherited `Q-` IDs. An empty section gets a single `- None identified.` bullet.
6. **`drivers.md`.** Exactly these three H2 headings, in this order:
   ```markdown
   ## Architecturally Significant Requirements
   ## Tradeoffs
   ## Sensitivity Points
   ```
   Populated from `design_context_artifact.drivers`. State plainly: **these heading strings are gated by `validate_design.py` and must match character for character.** Empty sections get `- None identified.`
7. **`index.yaml`.** Machine index of every artifact, plus a `review_queue` listing every `confidence: low` artifact with a one-line reason. Mirror the M1 index shape in `agents/requirements-formatter.md`.
8. **Validator re-run.** After writing, run:
   ```bash
   python3 skills/design/scripts/validate_design.py .sdlc/design
   ```
   Record the exit code in `formatter_result.validator_rerun`. A non-zero exit is reported back, not worked around.
9. **Output.** Reproduce the D.8 `formatter_result` block verbatim.
10. **Gotchas.** Never write before `gate: pass`. Never commit — the skill owns that. Never invent an artifact the critic did not approve. The `review_queue` must agree with the artifacts' own `confidence` fields and with the skill's summary — low in all three places or none.

- [ ] **Step 2: Verify the gated headings match the validator exactly**

This is the check that catches a one-word drift between the writer and the gate:

```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/design/scripts')
import validate_design as vd
text = open('agents/design-formatter.md', encoding='utf-8').read()
missing = [h for h in vd.REQUIRED_DRIVERS_HEADINGS + vd.REQUIRED_ASSUMPTIONS_HEADINGS
           if h not in text]
assert not missing, f'formatter does not name these gated headings verbatim: {missing}'
print('all 6 gated headings present verbatim')
"
```
Expected: `all 6 gated headings present verbatim`

- [ ] **Step 3: Commit**

```bash
git add agents/design-formatter.md && git commit -m "$(cat <<'EOF'
feat(sto-99): add the design formatter

Writes the atomic CMP/IF files plus assumptions.md, drivers.md, and index.yaml,
then re-runs the structural validator and reports its exit code.

Drops the transient capability fields before writing — the schema's
unevaluatedProperties:false would reject them, and they are generation
scaffolding, not part of the contract.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: The design skill and its command entry

**Files:**
- Create: `skills/design/SKILL.md`
- Modify: `commands/groundwork.md:20-28` (add the `design` workflow entry after `requirements`)
- Reference: `skills/requirements/SKILL.md` (the M1 analogue — match its phase structure and gate discipline)

**Interfaces:**
- Consumes: `.sdlc/requirements/` produced by the M1 skill — the requirement files, `index.yaml`'s `review_queue`, and `assumptions.md`'s open questions.
- Produces: `design_context` (spec D.1) for Task 2's orchestrator, and owns the sign-off gate and the commit.

- [ ] **Step 1: Write `skills/design/SKILL.md`**

Frontmatter matches `skills/requirements/SKILL.md:1-4` in shape:

```markdown
---
name: design
description: Use when a validated requirement set exists and the user is ready to turn it into an architecture — guides an architecture interview and a multi-agent pipeline that produces atomic component and interface specs before any code is written.
---
```

Required sections:

1. **When this applies / does not.** Applies after the requirements workflow has produced `.sdlc/requirements/`. Does not apply to questions, bug reports, or requests to explain existing code. State plainly: **do not write any application code at any point during this skill.** It produces design artifacts only.
2. **Phase 1 — Locate and read the input.**
   - Find `.sdlc/requirements/`. If absent, stop and direct the user to the requirements workflow.
   - Run the entry gate:
     ```bash
     python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements
     ```
     A non-zero exit stops the stage — designing against a structurally invalid set is meaningless.
   - State explicitly that this is a **structural** gate only: **a non-empty `review_queue` does not block.** Those items are carried into Phase 3 by design (spec A.7).
   - Read the requirement files, `index.yaml`'s `review_queue`, and `assumptions.md`'s open questions.
   - Scan an existing codebase if one is present, using the same bounded 3–5 file scan as `skills/requirements/SKILL.md:37`.
3. **Phase 2 — Hypothesise.** One message, one question. Propose a candidate decomposition (4–6 named components in plain terms) and a stack hypothesis, then ask whether it matches. Mirror the shape of M1's Phase 3, including a worked example.
4. **Phase 3 — Architecture interview.** Six coverage areas — runtime and stack, persistence, deployment target, integration points, operational constraints, team constraints. Rules:
   - **Open with the inherited open questions.** Many are architecture decisions by nature. Show the worked example: a requirements-stage `Q-4` asking "which framework given the footprint constraint — Electron, Tauri, or native?" is this stage's call, and it goes first, not last.
   - One question per message. Prefer 2–4 numbered options over open-ended; carry over the rationale from `skills/requirements/SKILL.md:103`.
   - Infer from the codebase where obvious. Only ask what you cannot determine.
5. **Phase 4 — `design_context` synthesis.** Render the block for confirmation:
   ```
   **Design context:**

   **System purpose:** ...
   **Runtime & stack:** ...
   **Persistence:** ...
   **Deployment target:** ...
   **Integration points:** ...
   **Operational constraints:** ...
   **Team constraints:** ...
   **Out of scope:** ...
   **Inherited questions:** [each Q-# with resolved / still open]
   **Inherited review queue:** [requirement IDs, or "None"]
   ```
   Ask whether it captures the context. **Do not proceed until the user confirms.**
6. **Phase 5 — Generate.** Document the fixed agent order — orchestrator → component-specialist → interface-specialist → design-critic → design-formatter — and state that the formatter runs only on `gate: pass`. Then:
   - **Step 1:** run the pipeline.
   - **Step 2:** render the in-conversation summary before writing anything: overview, the component list with one-line responsibilities, the interface list with provider and interaction, the drivers (ASRs, tradeoffs, sensitivity points), assumptions and open questions, and a **⚠️ Triage before sign-off** block listing every `confidence: low` artifact with its reason. Mirror `skills/requirements/SKILL.md:171-197`.
   - **Step 3:** the sign-off gate. **No files are written until the user confirms.** Corrections re-dispatch to the owning specialist via the orchestrator, then re-summarise.
   - **Step 4:** on confirmation, run the formatter, then the hard gate:
     ```bash
     python3 skills/design/scripts/validate_design.py .sdlc/design
     ```
     It MUST exit 0. Note the `pyyaml`/`jsonschema` requirement and point at `skills/requirements/scripts/README.md`.
   - **Step 5:** commit:
     ```bash
     git add .sdlc/design/
     git commit -m "docs: add design artifact set for <feature-name>"
     ```
7. **What this stage does not produce.** ADRs (STO-100), C4 diagrams (STO-101), cross-artifact traceability (STO-102). Say so plainly so a user does not read the empty `adr/` slot as a bug.

- [ ] **Step 2: Add the workflow entry to `commands/groundwork.md`**

Insert after the `requirements` section's `---` separator and before the closing italic line:

```markdown
### design

**Trigger:** A validated requirement set exists under `.sdlc/requirements/` and you're ready to turn it into an architecture ("design this", "let's do the architecture", "turn the requirements into components").

**Purpose:** Runs an architecture interview covering what requirements deliberately cannot carry — runtime and stack, persistence, deployment target, integration points, operational and team constraints — opening with any open questions the requirements stage left for architecture to decide. Then runs a multi-agent pipeline (orchestrator → component/interface specialists → critic → formatter) that emits **atomic Markdown+YAML design files** with categorical IDs (CMP/IF) under `.sdlc/design/`, plus `assumptions.md` and `drivers.md`. Components declare a single responsibility; interfaces declare provider, operations, interaction style, and error modes. A critic gates on ISO/IEC/IEEE 42010 and ATAM before anything is written, and a structural validator gates after. No files are written until you sign off.

**Why it matters:** The architecture stage is where technology decisions get made silently if nobody forces them into the open. This one asks, records the drivers and tradeoffs behind the decomposition, and hands the next stage a traceable component graph instead of a diagram.

---
```

- [ ] **Step 3: Verify the skill frontmatter and the phase count**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from artifact_core import extract_frontmatter_block
b = extract_frontmatter_block(open('skills/design/SKILL.md', encoding='utf-8').read())
assert b is not None, 'no frontmatter'
assert 'name: design' in b, b
assert 'description:' in b, b
print('skill frontmatter OK')
"
grep -c "^## Phase" skills/design/SKILL.md
grep -q "^### design" commands/groundwork.md && echo "command entry OK"
```
Expected: `skill frontmatter OK`, then `5`, then `command entry OK`.

- [ ] **Step 4: Verify both hard-gate commands appear verbatim**

```bash
grep -q "validate_requirements.py .sdlc/requirements" skills/design/SKILL.md && echo "entry gate OK"
grep -q "validate_design.py .sdlc/design" skills/design/SKILL.md && echo "exit gate OK"
```
Expected: both `OK` lines.

- [ ] **Step 5: Commit**

```bash
git add skills/design/SKILL.md commands/groundwork.md && git commit -m "$(cat <<'EOF'
feat(sto-99): add the design skill and its workflow entry

Five phases mirroring M1, with the interview retargeted at what the requirement
set cannot carry by construction — the content linter treats implementation bias
as a defect, so the stack is nowhere in .sdlc/requirements/ and the stage either
asks or invents.

Phase 1's entry gate is structural only: a non-empty review_queue is carried
into the interview rather than blocking, because those questions are often
exactly what this stage exists to decide.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: End-to-end run against the tamagotchi requirement set

This is the only test the agent files get. Fixtures cannot tell you whether the capability back-fill produces a sane graph on a real requirement set.

**Files:**
- Create: `docs/requirements/examples/tamagotchi/design/` — the generated artifact set
- Input (read-only): `docs/requirements/examples/tamagotchi/requirements/`

**Interfaces:**
- Consumes: everything built in Tasks 1–6.
- Produces: a committed worked example beside the M1 set, and a validated answer to whether the pipeline works.

- [ ] **Step 1: Confirm the input set is valid**

Run: `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements`
Expected: exit 0. If it fails, stop — the entry gate is doing its job and the example set needs fixing first.

- [ ] **Step 2: Note the inherited uncertainty before starting**

Run:
```bash
grep -A 20 "review_queue" docs/requirements/examples/tamagotchi/requirements/index.yaml
grep -A 20 "## Open Questions" docs/requirements/examples/tamagotchi/requirements/assumptions.md
```
Expected: the review queue lists `NFR-002` and `CON-001` among others, and `Q-4` asks which framework to use given the footprint constraint. **`Q-4` is the acceptance criterion for the whole ticket** — the stage must open the interview with it and land on a real answer.

- [ ] **Step 3: Run the design skill end to end**

Invoke the `design` skill against the example set. Answer the interview as the tamagotchi's owner would — a single-user offline desktop pet, local file persistence, cross-platform desktop delivery — and resolve `Q-4` explicitly when asked.

Write the output to the example directory rather than a real `.sdlc/`:

```bash
mkdir -p docs/requirements/examples/tamagotchi/design
```

- [ ] **Step 4: Run the hard gate**

Run: `python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design`
Expected: exit 0. Iterate until clean — this is a gate, not a report.

- [ ] **Step 5: Verify the graph actually closes**

```bash
python3 -c "
import sys, os, glob; sys.path.insert(0, 'lib')
from artifact_core import parse_frontmatter
root = 'docs/requirements/examples/tamagotchi/design'
comps, ifaces = {}, {}
for p in glob.glob(os.path.join(root, 'components', '*.md')):
    d, _ = parse_frontmatter(p); comps[d['id']] = d
for p in glob.glob(os.path.join(root, 'interfaces', '*.md')):
    d, _ = parse_frontmatter(p); ifaces[d['id']] = d
assert comps, 'no components were generated'
assert ifaces, 'no interfaces were generated'
edges = [(c, i) for c, d in comps.items() for i in d.get('depends_on') or []]
assert edges, 'no CMP -> IF edges: the back-fill produced nothing'
for c, i in edges:
    assert i in ifaces, f'{c} depends on unknown {i}'
    assert ifaces[i]['provider'] in comps, f'{i} provider not a known component'
print(f'{len(comps)} components, {len(ifaces)} interfaces, {len(edges)} edges')
print('CMP -> IF -> CMP graph closes')
"
```
Expected: non-zero counts and `CMP -> IF -> CMP graph closes`. **An edge count of zero means the back-fill silently dropped every dependency** — that is the A.4 failure mode, and it would otherwise pass the validator.

- [ ] **Step 6: Verify Q-4 was actually resolved**

```bash
grep -i -e electron -e tauri -e native \
  docs/requirements/examples/tamagotchi/design/drivers.md \
  docs/requirements/examples/tamagotchi/design/assumptions.md
```
Expected: a concrete framework decision recorded in `drivers.md`. If it appears only in `assumptions.md` as a still-open `Q-4`, the interview did not do its job — go back to Phase 3.

- [ ] **Step 7: Write the example README**

Create `docs/requirements/examples/tamagotchi/design/README.md` describing what generated the set, on what date, from which requirement set, and which stage-M2 pieces are deliberately absent (ADRs, C4 diagrams). Match the tone of `docs/requirements/examples/tamagotchi/README.md`.

- [ ] **Step 8: Run every test one final time**

Run: `python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q`
Expected: all PASSED. Confirm no test was modified beyond the single added assertion in `test_skip_files_and_subtrees_are_ignored`:

```bash
git diff main --stat -- skills/design/scripts/tests/test_validate_design.py
```

- [ ] **Step 9: Commit**

```bash
git add docs/requirements/examples/tamagotchi/design/ && git commit -m "$(cat <<'EOF'
docs(sto-99): tamagotchi design set as the M2 worked example

The end-to-end run of the architecture stage against the M1 example
requirements — the only verification the agent files get, since fixtures cannot
show whether the capability back-fill produces a sane graph on real input.

Q-4 (Electron vs Tauri vs native), left open by the requirements stage, is
resolved here and recorded in drivers.md with its tradeoff — which is the
handoff the milestone was built to make work.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Verification Checklist

Before opening the PR:

- [ ] `python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q` — all green
- [ ] Test count rose by exactly 5; only `test_skip_files_and_subtrees_are_ignored` was modified, by one added line
- [ ] `python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design` — exit 0
- [ ] The graph check in Task 7 Step 5 reports a non-zero edge count
- [ ] `drivers.md` names a concrete framework decision for Q-4
- [ ] Five agent files exist in `agents/` with parseable single-key frontmatter
- [ ] `skills/design/SKILL.md` has five `## Phase` sections and both hard-gate commands verbatim
- [ ] `commands/groundwork.md` lists the `design` workflow
- [ ] No `adr/` or `diagrams/` directory was created in the example output
- [ ] No application code was written anywhere outside `skills/`, `agents/`, `lib/`, `commands/`, and `docs/`

# QA Stage Shape Adjustments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close STO-307's three findings — give `enforcement: none` a register in
the QA stage, rename the specialist whose remit outgrew its name, and add a
second axis so a check that is never executed can say so.

**Architecture:** Six tasks, ordered so the mechanical rename lands first and
every later edit is written against final filenames and final contract keys.
Task 2 is the only Python; Tasks 1 and 3–5 are agent-instruction and template
changes whose tests are the structural validator, the reference export's
drift check, and a stale-reference sweep. Nothing here regenerates
`docs/requirements/examples/`.

**Tech Stack:** Python 3 stdlib only (`jsonschema` and `pyyaml` are optional at
runtime and present in CI), pytest, JSON Schema draft 2020-12, Markdown agent
instructions with YAML frontmatter.

**Spec:** `docs/superpowers/specs/2026-09-15-sto-307-qa-stage-shape-design.md`

## Global Constraints

- **Python is stdlib-only, everywhere, including the site scripts.** No new
  dependency may be introduced by any task.
- **`site/content/_generated/` is committed and CI fails on drift.** Any task
  that edits an agent's frontmatter `description:`, a JSON Schema, a
  `SKILL.md` coverage list, or an orchestrator's stage headings or hand-off
  YAML must run `python3 site/scripts/export_reference.py` and commit the
  regenerated files *in the same commit*. The gate is
  `python3 site/scripts/export_reference.py --check`
  (`.github/workflows/ci.yml:32`).
- **`python3 -m pytest -q` runs everything from the repository root**, and must
  pass at the end of every task.
- **`plugin/` is the published surface.** Nothing is added there that users
  should not download; fixtures live under `tests/`.
- **Do not regenerate `docs/requirements/examples/`.** Spec D9: no QA example
  set is committed yet, which is what makes the schema change cheap. STO-309
  owns that regeneration.
- **Do not edit `docs/superpowers/specs/2026-09-06-sto-103-qa-strategy-design.md`
  or `docs/superpowers/plans/2026-09-06-sto-103-qa-strategy.md`.** Their five
  references to the old agent name are historical records of what STO-103
  built (spec D3).
- **Commit message convention:** `<type>(sto-307): <subject>`, and every commit
  message ends with the trailer
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Rename the specialist and its contract keys

Spec D3 and D4. Purely mechanical: no rule changes meaning here, so anything
that looks like a judgment call belongs to a later task.

**Files:**
- Rename: `plugin/agents/functional-test-specialist.md` →
  `plugin/agents/behavioural-test-specialist.md`
- Modify: `plugin/agents/behavioural-test-specialist.md` (frontmatter
  `description:`, body H1, and its own 5 contract-key references at old lines
  12, 16, 22, 73, 88)
- Modify: `plugin/agents/qa-orchestrator.md` (4 name references at lines 30,
  46, 351, 365; 8 contract-key sites at lines 270, 277, 342, 346, 351, 354,
  355, 630)
- Modify: `plugin/agents/qa-critic.md` (3 name references at lines 94, 100, 167)
- Modify: `plugin/agents/quality-attribute-test-specialist.md` (2 name
  references at lines 68, 204)
- Modify: `plugin/agents/qa-formatter.md` (1 name reference at line 176)
- Modify: `plugin/skills/qa/SKILL.md` (1 name reference at line 270)
- Modify: `site/content/architecture/index.mdx` (1 name reference at line 119)
- Regenerate: `site/content/_generated/agents.json`
- Test: `site/scripts/tests/test_export_reference.py` (asserted unchanged, not
  edited)

**Interfaces:**
- Produces: the agent file `behavioural-test-specialist.md`, dispatched under
  that name; the `generation_brief` keys `id_block.behavioural` and
  `assigned.behavioural`, which Tasks 3, 4 and 5 all reference.
- Consumes: nothing from earlier tasks.

- [ ] **Step 1: Rename the file with git so history follows**

```bash
git mv plugin/agents/functional-test-specialist.md \
       plugin/agents/behavioural-test-specialist.md
```

- [ ] **Step 2: Update the frontmatter description and the body H1**

`export_agents()` (`site/scripts/export_reference.py:216`) takes the agent's
name from its filename and its title from the body H1, so all three must agree
or the generated roster reads wrong.

Replace line 2 (the whole `description:` line) with:

```
description: Behavioural test-strategy specialist. Converts the assigned functional requirements, constraints and business rules from the orchestrator's generation_brief, plus the design set's component boundaries, into atomic test-strategy items that say how each requirement is exercised, by what means, and at what level. Returns a draft_test_strategies object.
```

Replace the H1 on line 5:

```markdown
# Behavioural Test Specialist
```

And the opening sentence directly below it, which still says "functional
requirements" alone:

```markdown
You author test-strategy items derived from functional requirements,
constraints and business rules — the behavioural and compliance claims, as
against the quality-attribute scenarios `quality-attribute-test-specialist`
handles.
```

- [ ] **Step 3: Rename the contract keys**

`id_block.functional` → `id_block.behavioural` and `assigned.functional` →
`assigned.behavioural`, everywhere. `quality_attribute` is untouched in both.

```bash
sed -i 's/id_block\.functional/id_block.behavioural/g; s/assigned\.functional/assigned.behavioural/g' \
  plugin/agents/qa-orchestrator.md plugin/agents/behavioural-test-specialist.md
```

That handles the prose references. The two YAML blocks in
`qa-orchestrator.md` carry the key as a bare mapping key and need editing by
hand — at line 269:

```yaml
id_block:
  behavioural: [TS-001, TS-002, TS-003, TS-004]
  quality_attribute: [TS-005]
```

and in the `generation_brief` block at line 341:

```yaml
  id_block:
    behavioural: [TS-001, TS-002, TS-003, TS-004]  # allocated to the behavioural specialist
    quality_attribute: [TS-005]
  created_at: "YYYY-MM-DD"         # today's date, passed so all files agree
  assigned:
    behavioural: [FR-001, FR-002, CON-002, BR-001]
    quality_attribute: [NFR-004]
```

- [ ] **Step 4: Update the twelve name references**

```bash
grep -rl 'functional-test-specialist' plugin/ site/content/architecture/index.mdx \
  | xargs sed -i 's/functional-test-specialist/behavioural-test-specialist/g'
```

Then fix the two places where the surrounding prose reads wrong afterwards.
`qa-orchestrator.md:351` becomes:

```markdown
ID — `behavioural-test-specialist` covers the `assigned.behavioural` entries,
`quality-attribute-test-specialist` the `assigned.quality_attribute` entries.
```

and `qa-orchestrator.md:354`:

```markdown
**Every constraint and business rule goes in `assigned.behavioural`**, with the
FRs, drawing from the same `id_block.behavioural` range. There is no third key
```

- [ ] **Step 5: Verify no stale reference survives**

```bash
grep -rn 'functional-test-specialist\|id_block\.functional\|assigned\.functional' \
  plugin/ site/ tests/
```

Expected: no output. The only remaining hits anywhere in the repository must
be the five under `docs/superpowers/`, which are historical and stay:

```bash
grep -rln 'functional-test-specialist' docs/
```

Expected: exactly `docs/superpowers/specs/2026-09-06-sto-103-qa-strategy-design.md`
and `docs/superpowers/plans/2026-09-06-sto-103-qa-strategy.md`.

- [ ] **Step 6: Regenerate the reference export**

```bash
python3 site/scripts/export_reference.py
python3 site/scripts/export_reference.py --check
```

Expected: the second command exits 0. `agents.json` should now carry
`"name": "behavioural-test-specialist"` and
`"title": "Behavioural Test Specialist"`.

- [ ] **Step 7: Run the tests**

```bash
python3 -m pytest -q
```

Expected: PASS. `site/scripts/tests/test_export_reference.py:101` asserts the
roster is 19 agents and that every name matches a file on disk — a rename
keeps both true, and a failure here means Step 2 left the filename and the
export out of step.

- [ ] **Step 8: Commit**

```bash
git add -A plugin/agents site/content plugin/skills/qa/SKILL.md
git commit -m "$(cat <<'MSG'
refactor(sto-307): behavioural-test-specialist — the seam's name and keys follow its remit

The end-to-end run assigned CON- and BR- artifacts to the functional
specialist, making the seam FR + CON + BR versus NFR while the name and the
generation_brief keys still said "functional". The keys are where that
misleads: sizing id_block.functional from the FR count is the arithmetic
qa-orchestrator.md already warns forces a re-dispatch.

Mechanical only — no authoring rule changes meaning here.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 2: `verification_mode` in the schema and the fallback validator

Spec D6 and D7. The only Python in this plan. TDD: the fallback validator's
tests are written first, and the schema conditional is proved by fixtures
driven through `vq.main`.

**Files:**
- Modify: `plugin/skills/qa/schema/qa.schema.json:7-11` (required list),
  `:22-26` (`test_level`), plus a new `verification_mode` property and an
  `allOf` conditional
- Modify: `plugin/skills/qa/scripts/validate_qa.py:68-104` (`_fallback_validate`)
- Modify: all 12 existing fixture artifacts under `tests/qa/fixtures/`
- Create: `tests/qa/fixtures/invalid/bad_verification_mode/`
- Create: `tests/qa/fixtures/invalid/missing_test_level_for_test_mode/`
- Create: `tests/qa/fixtures/valid/strategy/TS-002-licence-inventory-audit.md`
- Create: `tests/qa/fixtures/valid/strategy/TS-003-network-egress-inspection.md`
- Modify: `tests/qa/test_validate_qa.py`
- Modify: the 4 artifacts under `tests/dod/fixtures/full/qa/strategy/`
- Modify: `plugin/agents/qa-orchestrator.md:400` and
  `plugin/agents/qa-formatter.md:94` (the two frontmatter contracts), plus the
  worked-example frontmatter in `plugin/agents/behavioural-test-specialist.md`
  and `plugin/agents/quality-attribute-test-specialist.md:151`
- Regenerate: `site/content/_generated/fields.json`, `agents.json`

**Interfaces:**
- Consumes: nothing from Task 1 (different files).
- Produces: the frontmatter field `verification_mode`, enum
  `test | inspection | analysis | demonstration`, required on every item; and
  `test_level` required only when `verification_mode` is `test`. Tasks 3, 4
  and 5 all write guidance against exactly these names and values.

- [ ] **Step 1: Write the failing fallback tests**

Append to `tests/qa/test_validate_qa.py`. The `_base_item()` helper mirrors
`tests/design/test_validate_design.py:284`'s `_base_component()`, which is how
this repository exercises the no-jsonschema path directly.

```python
# ---------------------------------------------------------------------------
# The stdlib fallback path (no jsonschema): verification_mode and the
# conditional test_level requirement (STO-307 D6, D7).
# ---------------------------------------------------------------------------
def _base_item():
    return {
        "id": "TS-001", "type": "test_strategy", "title": "x",
        "description": "x", "test_level": "unit", "risk_level": "medium",
        "risk_rationale": "x", "enforcement": "ci",
        "verification_mode": "test", "traces_from": ["FR-001"],
        "traces_to": {"tests": [], "code": []}, "status": "draft",
        "confidence": "high", "created_at": "2026-09-15",
    }


def test_fallback_accepts_a_valid_item():
    assert vq._fallback_validate(_base_item()) == []


def test_fallback_requires_verification_mode():
    item = _base_item()
    del item["verification_mode"]
    errors = vq._fallback_validate(item)
    assert any("verification_mode" in e for e in errors), errors


def test_fallback_flags_unknown_verification_mode():
    item = _base_item()
    item["verification_mode"] = "vibes"
    errors = vq._fallback_validate(item)
    assert any("verification_mode" in e for e in errors), errors


def test_fallback_requires_test_level_when_mode_is_test():
    item = _base_item()
    del item["test_level"]
    errors = vq._fallback_validate(item)
    assert any("test_level" in e for e in errors), errors


def test_fallback_allows_absent_test_level_for_a_non_test_mode():
    # A licence audit crosses no boundary and honestly has no level.
    item = _base_item()
    item["verification_mode"] = "inspection"
    del item["test_level"]
    assert vq._fallback_validate(item) == []


def test_fallback_allows_test_level_alongside_a_non_test_mode():
    # Optional, not forbidden (D7): an inspection that enumerates call sites
    # across two components is still about an integration boundary.
    item = _base_item()
    item["verification_mode"] = "inspection"
    item["test_level"] = "integration"
    assert vq._fallback_validate(item) == []
```

- [ ] **Step 2: Run them to verify they fail**

```bash
python3 -m pytest tests/qa/test_validate_qa.py -q -k fallback
```

Expected: FAIL. `test_fallback_accepts_a_valid_item` fails with
`unexpected field 'verification_mode'`, and the two requirement tests fail
because nothing checks the field yet.

- [ ] **Step 3: Add the field to the schema**

In `plugin/skills/qa/schema/qa.schema.json`, replace the `required` array
(lines 7–11) — `test_level` leaves it, `verification_mode` joins it:

```json
  "required": [
    "id", "type", "title", "description", "risk_level",
    "risk_rationale", "enforcement", "verification_mode", "traces_from",
    "traces_to", "status", "confidence", "created_at"
  ],
  "allOf": [
    {
      "description": "test_level answers which boundary is crossed, so it is required only for a check that is actually executed (STO-307 D7). A check verified by inspection or analysis may still carry one when it is about a boundary, and omits it when nothing is crossed.",
      "if": {
        "properties": { "verification_mode": { "const": "test" } },
        "required": ["verification_mode"]
      },
      "then": { "required": ["test_level"] }
    }
  ],
```

Then update the `test_level` property's description and add
`verification_mode` immediately after it:

```json
    "test_level": {
      "type": "string",
      "description": "Which boundary the check is about. Drives grouping in the rendered qa-strategy.md. Required when verification_mode is 'test'; optional otherwise, and omitted when the check crosses no boundary at all.",
      "enum": ["unit", "integration", "contract", "e2e", "performance", "security"]
    },
    "verification_mode": {
      "type": "string",
      "description": "Whether the check is executed at all, mirroring the requirement schema's verification_method. An item whose mode is not 'test' is verified by reading, reasoning or observation rather than by running something.",
      "enum": ["test", "inspection", "analysis", "demonstration"]
    },
```

- [ ] **Step 4: Mirror both in the fallback validator**

In `plugin/skills/qa/scripts/validate_qa.py`, `_fallback_validate` — drop
`test_level` from the `required` tuple, add `verification_mode`, add the enum,
add the conditional, and keep `test_level` known so it is not reported as an
unexpected field:

```python
    errors: List[str] = []
    required = (
        "id", "type", "title", "description", "risk_level",
        "risk_rationale", "enforcement", "verification_mode", "traces_from",
        "traces_to", "status", "confidence", "created_at",
    )
    for field in required:
        if field not in data:
            errors.append(f"missing required field '{field}'")

    # test_level is conditional, not unconditional: it answers which boundary
    # the check is about, and a check that is never executed may cross none.
    if data.get("verification_mode") == "test" and "test_level" not in data:
        errors.append(
            "missing required field 'test_level' "
            "(required when verification_mode is 'test')"
        )

    enums = {
        "test_level": {"unit", "integration", "contract", "e2e", "performance", "security"},
        "verification_mode": {"test", "inspection", "analysis", "demonstration"},
        "risk_level": {"high", "medium", "low"},
        "enforcement": {"ci", "manual", "none"},
        "status": {"draft", "approved", "obsolete"},
        "confidence": {"high", "medium", "low"},
        "scope": {"project", "epic", "story"},
    }
```

and further down, where the unexpected-field sweep builds its allow-list:

```python
    known = set(required) | {"test_level", "scope", "parent_scope"}
```

- [ ] **Step 5: Mirror the field everywhere the frontmatter is restated**

Four files restate the artifact's frontmatter, and a schema the instructions
contradict is worse than no schema. Add `verification_mode` after the
`enforcement` line in each, and mark `test_level` conditional where the block
annotates its fields.

`plugin/agents/qa-orchestrator.md:400` — the `draft_test_strategies` contract:

```yaml
      test_level: unit | integration | contract | e2e | performance | security   # required when verification_mode is test
      risk_level: high | medium | low
      risk_rationale: <the consequence-of-failure or attribute-severity reasoning>
      enforcement: ci | manual | none
      verification_mode: test | inspection | analysis | demonstration
```

`plugin/agents/qa-formatter.md:94` — the same contract, annotated the same way:

```yaml
test_level: unit | integration | contract | e2e | performance | security   # required when verification_mode is test
risk_level: high | medium | low
risk_rationale: <the consequence-of-failure or attribute-severity reasoning>
enforcement: ci | manual | none
verification_mode: test | inspection | analysis | demonstration
```

`plugin/agents/behavioural-test-specialist.md` — the fully-worked example's
frontmatter (after `enforcement: ci`) gains `verification_mode: test`. The
heading calls the example contract-conformant, so it has to stay so.

`plugin/agents/quality-attribute-test-specialist.md:151` — its worked example
gains `verification_mode: test` after `enforcement: manual`. A manual load rig
is still executed; `manual` is about who starts it, `test` about whether
anything runs.

- [ ] **Step 6: Run the fallback tests to verify they pass**

```bash
python3 -m pytest tests/qa/test_validate_qa.py -q -k fallback
```

Expected: PASS, 6 tests.

- [ ] **Step 7: Add the field to all 12 existing fixtures**

Every existing artifact is now missing a required field, which would make each
invalid fixture fail for a second reason and stop isolating its own rule.

```bash
find tests/qa/fixtures -name '*.md' -path '*/strategy/*' \
  -exec sed -i 's/^enforcement: \(.*\)$/enforcement: \1\nverification_mode: test/' {} +
grep -c 'verification_mode' $(find tests/qa/fixtures -name '*.md' -path '*/strategy/*')
```

Expected: 12 files, each reporting `1`.

- [ ] **Step 8: Add the two new invalid fixtures**

```bash
for case in bad_verification_mode missing_test_level_for_test_mode; do
  mkdir -p tests/qa/fixtures/invalid/$case/strategy
  cp tests/qa/fixtures/valid/qa-strategy.md tests/qa/fixtures/invalid/$case/qa-strategy.md
done
```

`tests/qa/fixtures/invalid/bad_verification_mode/strategy/TS-001-bad-verification-mode.md`:

```markdown
---
id: TS-001
type: test_strategy
title: Bad verification mode
description: verification_mode is not one of the allowed enum values.
test_level: unit
risk_level: medium
risk_rationale: "Exercises the verification_mode enum rule in isolation."
enforcement: ci
verification_mode: vibes
traces_from: [FR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Bad verification mode

Body prose.
```

`tests/qa/fixtures/invalid/missing_test_level_for_test_mode/strategy/TS-001-missing-test-level.md`:

```markdown
---
id: TS-001
type: test_strategy
title: Missing test level for an executed check
description: verification_mode is test, so test_level is required and absent.
risk_level: medium
risk_rationale: "Exercises the conditional test_level requirement in isolation."
enforcement: ci
verification_mode: test
traces_from: [FR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Missing test level for an executed check

Body prose.
```

- [ ] **Step 9: Add the two new valid fixtures**

These hold D7's "optional, not forbidden" open against a future tightening —
one item with no level, one non-`test` item that keeps its level.

`tests/qa/fixtures/valid/strategy/TS-002-licence-inventory-audit.md`:

```markdown
---
id: TS-002
type: test_strategy
title: Licence inventory audit
description: Enumerates every bundled dependency's licence against the permitted set.
risk_level: high
risk_rationale: "A non-permitted licence is silent until it is legally expensive, and no runtime signal reveals it."
enforcement: manual
verification_mode: inspection
traces_from: [CON-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Licence inventory audit

Body prose. No test_level: the audit crosses no component boundary.
```

`tests/qa/fixtures/valid/strategy/TS-003-network-egress-inspection.md`:

```markdown
---
id: TS-003
type: test_strategy
title: Network egress inspection
description: Enumerates the call sites that reach the network across both components.
test_level: integration
risk_level: high
risk_rationale: "An unnoticed egress path leaks data with no failing test to announce it."
enforcement: manual
verification_mode: inspection
traces_from: [CON-002]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Network egress inspection

Body prose. Inspected rather than executed, but genuinely about the boundary
between two components, so it keeps its test_level.
```

- [ ] **Step 10: Register the two invalid cases**

`test_every_invalid_fixture_is_exercised` fails on any fixture directory no
case names. In `tests/qa/test_validate_qa.py`, extend `INVALID_CASES`:

```python
INVALID_CASES = [
    "bad_id_pattern",
    "prefix_type_mismatch",
    "duplicate_id",
    "bad_test_level",
    "bad_verification_mode",
    "missing_test_level_for_test_mode",
    "bad_enforcement",
    "missing_risk_rationale",
    "empty_traces_from",
    "unknown_field",
    "unknown_prefix",
    "missing_strategy_artifact",
    "strategy_missing_heading",
]
```

- [ ] **Step 11: Run the whole QA suite**

```bash
python3 -m pytest tests/qa -q
```

Expected: PASS. `test_valid_fixture_passes` now drives three artifacts through
the real schema, proving the `allOf` conditional accepts both a level-less
inspection and an inspection that keeps its level.

- [ ] **Step 12: Update the DoD fixtures**

`tests/dod/fixtures/full/qa/strategy/` carries four artifacts that are not
run through `validate_qa.py` but should still be valid artifacts. Add
`verification_mode: test` after the `enforcement:` line of `TS-001` and
`TS-002`; for the two that are verified by reading rather than running, use
`inspection` instead — `TS-003-audit-log-inspection.md` keeps its
`test_level: security`, and `TS-004-fulfilment-cutoff-review.md` keeps its
`test_level: integration`.

```bash
python3 -m pytest tests/dod -q
```

Expected: PASS — the DoD generator reads `enforcement`, `test_level` and
`risk_level` and ignores the new field, so this proves the fixtures did not
break it.

- [ ] **Step 13: Regenerate, check drift, run everything**

```bash
python3 site/scripts/export_reference.py
python3 site/scripts/export_reference.py --check
python3 -m pytest -q
```

Expected: both commands exit 0. `fields.json` is exported from the schemas, so
the new property appears there.

- [ ] **Step 14: Commit**

```bash
git add -A plugin/skills/qa tests/qa tests/dod site/content
git commit -m "$(cat <<'MSG'
feat(sto-307): verification_mode — a second axis for checks that are not executed

test_level answers which boundary a check is about; whether it runs at all is
a different question, and the requirements schema already names it
(verification_method). Adding inspection/analysis to test_level instead would
have collapsed the two axes: an inspection enumerating call sites across two
components is genuinely about an integration boundary and could no longer say
so.

test_level is therefore required only when verification_mode is test, and
optional rather than forbidden otherwise. Both fixtures for that rule are in
the valid set, so a future tightening has to delete a test to pass.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: One section defines every level and mode

Spec D5 and D6. Both authoring paths read one definition list, and the
workaround the new field makes unnecessary is deleted.

**Files:**
- Modify: `plugin/agents/behavioural-test-specialist.md` — move the
  `test_level` bullet out of `## Authoring rules` into a new section, delete
  point 3 of `## Deriving an item from a constraint or a business rule`, add
  `verification_mode` to the body structure and the worked example
- Modify: `plugin/agents/quality-attribute-test-specialist.md:60-70` — the
  cross-reference and the mode rule
- Regenerate: `site/content/_generated/agents.json`

**Interfaces:**
- Consumes: `verification_mode` and the conditional `test_level` from Task 2;
  the file and key names from Task 1.
- Produces: the section titled ``## Choosing `test_level` and
  `verification_mode` ``, which Task 5's critic instructions cite by name.

- [ ] **Step 1: Add the new section**

Insert immediately before `## Deriving an item from a constraint or a business
rule` in `plugin/agents/behavioural-test-specialist.md`. The four boundary
definitions are moved verbatim from the `## Authoring rules` bullet — do not
reword them; `quality-attribute-test-specialist.md` cites them as shared.

```markdown
## Choosing `test_level` and `verification_mode`

Two independent judgments, and answering them in this order keeps them
independent. `verification_mode` says whether the check is executed at all.
`test_level` says which boundary it is about. Both specialists use this
section; it is the only place either level or mode is defined.

### `verification_mode` — is this executed?

Read the requirement's own `verification_method` and honour it. A requirement
the requirements stage recorded as `inspection` does not become a test
because a test would be more convenient to write.

- **test** — something runs and passes or fails on its own.
- **inspection** — a person or a script reads the artifact and counts:
  which call sites exist, which dependencies are declared, whether a required
  clause is present.
- **analysis** — the answer comes from reasoning over a model or a
  measurement rather than from exercising the system: a budget summed from
  component figures, a threat model walked against a data flow.
- **demonstration** — the behavior is observed being performed, without an
  assertion harness making the judgment.

FRs are almost always `test`. Constraints and business rules are routinely
`inspection` or `analysis`, and a `CON-`/`BR-` item whose mode is not `test`
describes the enumeration or the review that actually settles it — which call
sites are enumerated, what is counted, what a non-zero count invalidates —
not an automated test nobody will write.

### `test_level` — which boundary is crossed?

A judgment about the boundary being crossed, not about effort. Choose it
against what the behavior actually spans:

- **unit** — the behavior is contained entirely within one component's
  boundary; nothing outside it needs to be running for the test to be
  meaningful.
- **integration** — the behavior spans two or more components' boundaries,
  so the test needs their real collaboration (not a stub) to say anything.
- **contract** — the behavior is the shape of an interaction across a
  boundary itself (a request/response shape, an event schema) rather than
  the business behavior that flows through it — this is what an `IF-`
  interface entry in `design_digest` names, so a `contract` item cites the
  interface it validates, not only the components on either side of it.
- **e2e** — the behavior is only observable by performing it the way a user
  would, through the full stack, because no lower boundary reproduces what
  matters (ordering across requests, session state, everything wired
  together).
- **performance** — the thing being crossed is a resource budget rather than
  a component boundary: a latency, a throughput, a memory or cost ceiling.
- **security** — the thing being crossed is a trust boundary: what may leave
  the machine, what an unauthenticated caller can reach, what an adversary
  controls.

A test that is merely *hard to set up* is not automatically integration or
e2e — hard-to-set-up unit tests are still unit tests. The question is what
boundary must be crossed for the assertion to be true, not how much
scaffolding the test needs.

### When the two axes disagree

`test_level` is required when `verification_mode` is `test`, and **optional,
not forbidden**, otherwise. Record a level whenever the check is *about* a
boundary, whatever its mode: an inspection enumerating every call site that
reaches the network across two components is an `integration` inspection, and
saying so keeps information a mode alone would lose. Omit it only when nothing
is crossed — a licence audit over the dependency manifest has no boundary and
no honest level, and inventing one is exactly the dishonesty this field pair
exists to end.

Say in `Test Level Rationale` which boundary the level names, or — when you
omitted it — why no boundary applies.
```

- [ ] **Step 2: Remove the bullet the section replaces**

Delete the whole `- **`test_level` is a judgment about the boundary being
crossed, not about effort.**` bullet from `## Authoring rules` (old lines
50–69, ending with "…not how much scaffolding the test needs.") and put a
pointer in its place:

```markdown
- **`test_level` and `verification_mode` are chosen together**, by the rules
  in `## Choosing test_level and verification_mode` below. Neither is a
  judgment about effort.
```

- [ ] **Step 3: Delete the workaround**

In `## Deriving an item from a constraint or a business rule`, delete point 3
entirely — the paragraph beginning "**`test_level` may need a value outside
the four boundary definitions above.**". It exists to work around a missing
enum value that Task 2 supplied. Renumber point 4 (`bounds`) to 3.

In point 2, the sentence "`verification_method` tells you whether an
executable test is even the right answer" now has a field to land in; extend
it:

```markdown
2. **`verification_method` tells you whether an executable test is even the
   right answer, and it sets `verification_mode` directly.** FRs and NFRs are
   almost always `test`; constraints and business rules are routinely
   `inspection` or `analysis`. Carry the requirement's own value across rather
   than deciding afresh, and see `## Choosing test_level and
   verification_mode` for what each value obliges the item to describe. Where
   a rule has both an executable half and a static half (a suite that runs on
   each target *and* a count of conditionals outside a layer), write both into
   one item's `Test Design`, record the mode of the half that settles the
   rule, and say in `Test Level Rationale` which half the recorded
   `test_level` describes.
```

- [ ] **Step 4: Point the body structure at the new section**

The worked example's frontmatter already gained the field in Task 2 Step 5.
What remains is the `## Body structure` block, whose `## Test Level Rationale`
slot says "per the definitions above" — true only by accident of ordering now.
Replace that slot with:

```
## Test Level Rationale
<why this is the level named in frontmatter — which boundary is crossed, per
"Choosing `test_level` and `verification_mode`" — or, when no `test_level` is
recorded, why no boundary applies and what settles the check instead>
```

- [ ] **Step 5: Update the quality-attribute specialist**

Its `test_level` bullet cross-references the old bullet title by name
(`:68`). Replace that reference:

```markdown
  `performance`/`security` out of habit. The levels are defined once, in
  `behavioural-test-specialist.md`, "Choosing `test_level` and
  `verification_mode`" — that section is shared across both specialists.
```

Add a mode bullet directly after it:

```markdown
- **`verification_mode` is almost always `test` here.** A quality-attribute
  scenario states a measurable response, and a fitness function measures it.
  Use `analysis` only where the response measure is genuinely derived rather
  than observed — a budget summed across components, a capacity argued from a
  model — and say so in the body. An NFR whose scenario cannot be measured at
  all is a finding for the critic, not an `inspection` item.
```

- [ ] **Step 6: Verify the section title is cited consistently**

```bash
grep -rn 'Choosing `test_level` and `verification_mode`\|is a judgment about the boundary' plugin/
```

Expected: the new section heading in `behavioural-test-specialist.md`, plus
the cross-reference from `quality-attribute-test-specialist.md`. No hit may
still point at the deleted bullet title.

- [ ] **Step 7: Regenerate and test**

```bash
python3 site/scripts/export_reference.py
python3 site/scripts/export_reference.py --check
python3 -m pytest -q
```

Expected: both exit 0.

- [ ] **Step 8: Commit**

```bash
git add -A plugin/agents site/content
git commit -m "$(cat <<'MSG'
docs(sto-307): one section defines every level and mode, read by both paths

The performance and security levels were only ever defined inside the
constraint/business-rule section, which the FR authoring path never reads, so
half the enum was invisible to half the work. All six levels and all four
modes now live in one section both specialists are pointed at.

Deletes the workaround that told an author to record "the level its executable
half runs at" for a pure inspection. verification_mode makes it unnecessary,
and a rule with no executable half had no honest answer under it.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 4: The declared-unenforced register

Spec D1 and D2. `enforcement: none` reaches an artifact at the stage that
records it.

**Files:**
- Modify: `plugin/agents/qa-orchestrator.md:500-560` — the
  `qa_context_artifact` contract and Stage 6.5's source list
- Modify: `plugin/agents/qa-formatter.md` — the `## Input` list at `:33`, the
  strategy-document skeleton, and the projection rules near `:199`
- Modify: `plugin/skills/qa/SKILL.md:320` — the rendering rule and the
  artifact shape at `:251`
- Modify: `plugin/skills/qa/templates/qa-strategy.md` — a new section
- Regenerate: `site/content/_generated/agents.json`, `stages.json`,
  `pipeline.json`

**Interfaces:**
- Consumes: `enforcement: none`, unchanged from the existing schema.
- Produces: `qa_context_artifact.unenforced`, a list of
  `{id: UE-#, item: TS-###, covers: [ID, ...], rationale: string}`; and the
  rendered `## Declared Unenforced` heading, which Task 6 greps for.

- [ ] **Step 1: Add the list to the orchestrator's contract**

In the `qa_context_artifact` YAML block (`qa-orchestrator.md:504`), after
`accepted_risks`:

```yaml
  unenforced:                  # the "written but not gated" register
    - id: UE-1
      item: TS-014             # the strategy item, not a requirement
      covers: [BR-002]         # the item's traces_from, carried through
      rationale: string        # the item's own risk_rationale
```

- [ ] **Step 2: Add its assembly rule**

The numbered "Sources, in order" list gains a fourth entry. Place it after
`accepted_risks` (entry 1) so the two registers are read together, and
renumber the rest:

```markdown
2. **`unenforced`** — every approved item whose `enforcement` is `none`, one
   entry each, `UE-` IDs assigned here in item-ID order. `item` is the item's
   own ID, `covers` is its `traces_from` carried across unchanged, and
   `rationale` is its `risk_rationale`.

   Keyed by item rather than by requirement because what is being recorded is
   an item's enforcement status: one item covering three requirements is one
   ungated strategy, not three risks.

   **This is not a third feed into `accepted_risks`**, and the two are never
   de-duplicated against each other. `accepted_risks` answers "what is nobody
   testing"; this answers "what is written and gated by nothing". They cannot
   collide: a requirement with an item covering it is not an uncovered ASR,
   and a requirement the interview declined outright has no item to mark
   `none`. Merging them would leave a reader unable to tell a strategy that
   does not exist from one that exists and never runs.

   `generate_dod.py` renders the same set into the Definition of Done's
   `## Declared Unenforced` section from the artifacts on disk. The two agree
   because both read `enforcement: none` and key by item ID; neither reads
   the other.
```

- [ ] **Step 3: Extend the closing paragraph**

The paragraph at `:550` naming the four sections the formatter renders must
name five, and keep its reasoning:

```markdown
content into `.sdlc/qa/qa-strategy.md`: `accepted_risks` into `## Accepted
Risks`, `unenforced` into `## Declared Unenforced`, and `assumptions`,
`dependencies`, and `open_questions` into their own `## Assumptions`,
`## Dependencies`, and `## Open Questions` sections — none of the five are
among the validator's required headings (see `qa-formatter.md`), because each
must be able to be visibly, honestly empty rather than silently missing.
```

- [ ] **Step 4: Teach the formatter to render it**

In `qa-formatter.md`, add `unenforced` to the `## Input` list at `:33`, add
`## Declared Unenforced` to the document skeleton directly after
`## Accepted Risks`, and add the projection rule beside the others:

```markdown
- **Declared Unenforced.** One bullet per `qa_context_artifact.unenforced`
  entry: `- **<UE-id>** — <item>: <rationale> (covers: <covers, comma-joined>)`,
  ordered by `item` ID ascending. When the register is empty, the section body
  is the single line `None identified.` Never omit the heading: a strategy
  document that silently drops the section reads identically whether nothing
  was unenforced or nobody checked.
```

- [ ] **Step 5: Mirror it in the skill**

`SKILL.md` carries no copy of the artifact's YAML shape — it carries the
user-facing summary block and the rendering paragraph, and both name Accepted
Risks today. Add a bullet to the summary block, directly after the
`**Accepted Risks:**` one:

```markdown
**Declared Unenforced:**
- <TS-ID> <title> — covers <IDs>: <rationale>, or "None"
```

and extend the paragraph at `:320`, which currently explains why Accepted
Risks is surfaced before any file is written:

```markdown
Render **Declared Unenforced** from `qa_context_artifact.unenforced` the same
way, and for the same reason: an item nothing gates is a decision the user
should get to overturn while overturning it is still cheap. Keep the two
lists separate here exactly as they are separate in the artifact — one is
what nobody is testing, the other is what nobody is enforcing.
```

- [ ] **Step 6: Add the section to the template**

In `plugin/skills/qa/templates/qa-strategy.md`, after `## Accepted Risks`:

```markdown
## Declared Unenforced
The `qa_context_artifact.unenforced` register — every emitted item whose
`enforcement` is `none`: a strategy that exists and that nothing gates. Keyed
by item, not by requirement, and deliberately distinct from Accepted Risks,
which records what is not tested at all. Not one of the validator's five
required headings, so it can be visibly empty (`None identified`).
```

- [ ] **Step 7: Verify the heading is not accidentally gated**

```bash
grep -n 'REQUIRED_STRATEGY_HEADINGS' -A8 plugin/skills/qa/scripts/validate_qa.py
```

Expected: the same five headings as before. Adding the sixth here would break
every strategy document that honestly has nothing to report, which is the
opposite of the intent.

- [ ] **Step 8: Regenerate and test**

```bash
python3 site/scripts/export_reference.py
python3 site/scripts/export_reference.py --check
python3 -m pytest -q
```

Expected: both exit 0. The orchestrator's hand-off YAML feeds `stages.json`
and `pipeline.json`, so expect those to change.

- [ ] **Step 9: Commit**

```bash
git add -A plugin site/content
git commit -m "$(cat <<'MSG'
feat(sto-307): the declared-unenforced register — enforcement: none reaches an artifact

Three items in STO-103's 31-item run declared themselves unenforced and the QA
stage recorded that nowhere. STO-104 since gave them a DoD section; this gives
the stage its own, so qa-strategy.md stops claiming coverage its own items
disclaim without depending on a later stage to say so.

A separate register rather than a third feed into accepted_risks: that one
answers "what is nobody testing", and an unenforced item is tested, just
ungated. Merged, a reader could not tell a strategy that does not exist from
one that exists and never runs.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 5: The critic checks coherence and stops reading absence as a gap

Spec D8.

**Files:**
- Modify: `plugin/agents/qa-critic.md:93-104` — the paragraph built around the
  missing enum value
- Modify: `plugin/agents/qa-critic.md:199-204` — the `level_gaps` rule
- Regenerate: `site/content/_generated/agents.json`

**Interfaces:**
- Consumes: `verification_mode` from Task 2, the section title from Task 3.
- Produces: no new contract. `critique_report`'s shape, and the gate
  arithmetic at `:258`, are unchanged.

- [ ] **Step 1: Replace the workaround paragraph**

`qa-critic.md:93-104` instructs the critic not to `revise` an item that
stretched a level to cover an inspection. That accommodation is obsolete, and
leaving it would have the critic wave through exactly what Task 2 made
expressible. Replace the whole paragraph with:

```markdown
  **`performance` and `security` are not the quality-attribute specialist's
  exclusively.** A constraint-derived item from `behavioural-test-specialist`
  may legitimately carry either — a constraint bounding a resource budget is
  `performance`, one bounding what may leave the machine is `security`.

  **Check `verification_mode` and `test_level` for coherence.** They are
  independent axes (see `behavioural-test-specialist.md`, "Choosing
  `test_level` and `verification_mode`"), and each half is checkable:

  - An item whose mode is `inspection` or `analysis` but whose `Test Design`
    describes an automated suite, a harness or a CI job is a `revise`: one of
    the two is wrong, and the body says which.
  - An item whose mode is `test` but whose `Test Design` describes a review,
    a walkthrough or a manual count is a `revise` for the same reason,
    inverted.
  - An item that omits `test_level` must say in `Test Level Rationale` why no
    boundary applies. A missing level with no stated reason is a `revise`; a
    missing level on a licence or manifest audit that says so is correct and
    is not a finding.
  - An item that carries a `test_level` alongside a non-`test` mode is **not**
    a finding. An inspection enumerating call sites across two components is
    an `integration` inspection, and recording that is the point of keeping
    the axes apart.

  Do not `revise` an item for carrying a mode that its requirement's own
  `verification_method` also carries — that is the field being honoured, not
  a judgment being dodged.
```

- [ ] **Step 2: Exempt level-less items from `level_gaps`**

Append to the `level_gaps` paragraph at `:199`:

```markdown
  A level that is absent because every candidate item is verified by
  inspection or analysis is not a gap, and neither is an item that legitimately
  carries no `test_level` at all — check `verification_mode` before recording
  either as an omission. `level_gaps` counts levels the set *should* exercise
  and does not, never levels that nothing in the set could honestly reach.
```

- [ ] **Step 3: Confirm the gate arithmetic is untouched**

```bash
grep -n -A10 'Gate arithmetic' plugin/agents/qa-critic.md
```

Expected: unchanged — two conditions, `level_gaps` still advisory. Spec D8
adds findings, not failure modes; a coherence `revise` already fails the gate
through the existing `per_item` condition.

- [ ] **Step 4: Regenerate and test**

```bash
python3 site/scripts/export_reference.py
python3 site/scripts/export_reference.py --check
python3 -m pytest -q
```

Expected: both exit 0.

- [ ] **Step 5: Commit**

```bash
git add -A plugin/agents site/content
git commit -m "$(cat <<'MSG'
feat(sto-307): the critic checks mode/level coherence and stops reading absence as a gap

The critic was told not to revise an item that stretched a level to cover an
inspection — an accommodation for a missing enum value. verification_mode
removes the need, so the accommodation becomes a coherence check instead:
an inspection whose test design describes a CI job is now a finding, and so is
its inverse.

level_gaps also had to stop counting an honestly absent level as an omission.
It stays advisory; gate arithmetic is unchanged.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 6: Whole-stage verification

No production change. This is the pass that proves the five preceding commits
agree with each other, since most of what they changed is instructions no test
executes.

**Files:**
- Modify: `docs/superpowers/specs/2026-09-15-sto-307-qa-stage-shape-design.md`
  (one count correction, Step 3)
- Test: no new files

**Interfaces:**
- Consumes: everything.

- [ ] **Step 1: Sweep for stale references**

```bash
grep -rn 'functional-test-specialist\|id_block\.functional\|assigned\.functional' plugin/ site/ tests/
grep -rn "enum has no value\|its executable half runs at" plugin/
```

Expected: no output from either. The second catches any surviving prose that
still describes the pre-`verification_mode` world.

- [ ] **Step 2: Confirm the two registers are described consistently**

```bash
grep -rn 'Declared Unenforced' plugin/ | sort
```

Expected: five hits — the orchestrator's contract and closing paragraph, the
formatter's skeleton and projection rule, the template, and the DoD generator
(`plugin/skills/requirements/scripts/generate_dod.py:407`). Confirm by reading
that the QA-side bullet and the DoD-side section key on the same three things:
item ID, covers, rationale.

- [ ] **Step 3: Correct the spec's reference count**

The spec's D3 says "Thirteen live references". Twelve are hand-edited; the
thirteenth was `site/content/_generated/agents.json`, which is generated.
Change that sentence to:

```markdown
Twelve hand-edited references update: `qa-orchestrator.md` (4),
`qa-critic.md` (3), `quality-attribute-test-specialist.md` (2),
`qa-formatter.md`, the QA `SKILL.md`, and
`site/content/architecture/index.mdx`. A thirteenth, in
`site/content/_generated/agents.json`, is regenerated rather than edited.
```

- [ ] **Step 4: Run the full suite and the drift gate**

```bash
python3 -m pytest -q
python3 site/scripts/export_reference.py --check
```

Expected: both exit 0. These are the two commands CI runs
(`.github/workflows/ci.yml:29,32`).

- [ ] **Step 5: Prove the validator still gates a realistic set**

```bash
S=/tmp/qa-307; rm -rf $S; mkdir -p $S
cp -r tests/qa/fixtures/valid/* $S/
python3 plugin/skills/qa/scripts/validate_qa.py $S
```

Expected: exit 0 over the three artifacts, including the level-less
inspection. Then prove the conditional actually bites:

```bash
sed -i 's/^verification_mode: inspection$/verification_mode: test/' \
  $S/strategy/TS-002-licence-inventory-audit.md
python3 plugin/skills/qa/scripts/validate_qa.py $S
```

Expected: non-zero exit, reporting that `TS-002` is missing `test_level` — an
item claiming to be executed must say what boundary it executes across.

```bash
rm -rf $S
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-09-15-sto-307-qa-stage-shape-design.md
git commit -m "$(cat <<'MSG'
docs(sto-307): correct the spec's reference count

Twelve references are hand-edited; the thirteenth is generated.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

- [ ] **Step 7: Update the Linear ticket**

STO-307's description proposes two things this implementation deliberately did
not do — a third feed into `accepted_risks`, and new `test_level` enum values —
and states that `enforcement: none` "reaches nothing", which stopped being
true when STO-104 landed. Leave a comment naming the three decisions and
pointing at the spec, so the ticket does not read as unimplemented.

This step is the only one that touches anything outside the repository, and
it is not a blocker for opening the PR.

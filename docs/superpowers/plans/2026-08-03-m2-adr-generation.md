# M2 ADR Generation (MADR 4.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn architecture decisions the pipeline already records into first-class MADR 4.0 ADR artifacts, validated by the same structural gate as every other design artifact.

**Architecture:** A new `adr-generator` agent runs at Stage 9.5 — after the orchestrator synthesises `design_context_artifact`, before the formatter writes. It derives ADRs from `drivers.tradeoffs` (resolved `Q-` decisions) and `deferred_to_decision` ASRs, never eliciting and never inventing alternatives. The formatter writes `adr/` alongside `components/` and `interfaces/`, populates `traces_to.adr` inline, and runs one `validate_design.py` gate over everything. `ADR-` becomes a third artifact type in `design.schema.json`.

**Tech Stack:** Markdown agent-definition files with single-key YAML frontmatter; JSON Schema draft 2020-12; Python 3 (`pyyaml`, `jsonschema`) for the validator and pytest suite.

**Spec:** `docs/superpowers/specs/2026-08-03-m2-adr-generation-design.md`

## Global Constraints

- **Never invent alternatives.** An entry with no recoverable second option does not become an `accepted` ADR — not a stub, not a one-option ADR. It goes in `skipped` with a reason. (Spec D1.)
- **The `Q-` ID is the discriminator.** A `drivers.tradeoffs` entry qualifies only when its `decision` field names a `Q-` ID. Not prose sentiment about importance. (Spec D2.)
- **Structural tradeoffs stay in `drivers.md`.** Do not promote IF-002's flush timing, IF-003's sync commit, IF-007's pull-over-push, CMP-001's inlined platform behaviour, the shared webview, or the absent network surface.
- **The formatter stays the single writer and single structural gate.** Nothing after Stage 10 re-opens a written file. (Spec D3; this is what STO-215 and STO-99 fixed.)
- **The ADR↔artifact edge lives once**, on `CMP/IF.traces_to.adr`. Do not add a `components` key to `traces_to`. (Spec D6.)
- **`status` is always `draft` on generation** — matching all 23 shipped tamagotchi artifacts. `decision_status` is the separate MADR field.
- **`diagrams` stays in `SKIP_DIRNAMES`.** STO-101 owns it; this ticket does not touch it.
- No changes under `docs/requirements/examples/` — regeneration is STO-219.

---

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `skills/design/schema/design.schema.json` | Single source of truth for artifact shape | Modify — ADR in id pattern + type enum; adr branch; nested `decision_status` branch |
| `skills/design/scripts/validate_design.py` | Structural gate | Modify — `PREFIX_TO_TYPE`, `SKIP_DIRNAMES`, fallback lists, MADR heading gate, docstrings |
| `skills/design/scripts/tests/fixtures/valid/adr/ADR-001-single-writer-db.md` | Valid-set fixture | Rewrite — currently asserts it is skipped |
| `skills/design/scripts/tests/fixtures/invalid/adr_*/` | Failure fixtures | Create — four new cases |
| `skills/design/scripts/tests/test_validate_design.py` | Validator suite | Modify — two inverting tests + new ADR tests |
| `agents/adr-generator.md` | The specialist | Create |
| `agents/design-orchestrator.md` | Pipeline routing | Modify — Stage 9.5 replaces Stage 11 slot |
| `agents/design-formatter.md` | Writes artifacts | Modify — write `adr/`, populate `traces_to.adr` |
| `agents/design-critic.md` | Quality gate | Modify — `deferred_to_decision` routes to an ADR |
| `skills/design/SKILL.md` | Stage documentation | Modify — remove "does not write ADRs" |
| `lib/artifact_core.py` | Shared machinery | Modify — one docstring line naming `adr/` as skipped |

Six tasks. Tasks 1–2 make the schema and gate accept ADRs (independently testable end-to-end). Tasks 3–6 wire the pipeline that produces them (documentation files, verified by grep + frontmatter parse).

---

### Task 1: ADR as a third schema type

**Files:**
- Modify: `skills/design/schema/design.schema.json` — id pattern (line 22), type enum (lines 27-30), new `allOf` branch after the interface branch (after line 242)
- Test: `skills/design/scripts/tests/test_validate_design.py` — new schema-level tests

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: the `adr` type contract every later task depends on — frontmatter keys `decision_status` (enum `proposed|rejected|accepted|deprecated|superseded`), `considered_options` (array of string), `chosen_option` (string). Task 2 mirrors these in the stdlib fallback lists; Task 3's agent emits them; Task 5's formatter writes them. The exact spelling `decision_status` (not `decision-status`, not `adr_status`) is load-bearing across all four.

- [ ] **Step 1: Write the failing tests**

Append to `skills/design/scripts/tests/test_validate_design.py`:

```python
# ---------------------------------------------------------------------------
# ADR schema branch (STO-100)
# ---------------------------------------------------------------------------
import json  # `pytest` is already imported at the top of this file


def _adr(**overrides):
    """A minimal valid accepted-ADR frontmatter dict, with overrides applied."""
    data = {
        "id": "ADR-001",
        "type": "adr",
        "title": "Desktop runtime and UI shell",
        "description": "Which runtime and UI shell the desktop app is built on.",
        "traces_from": ["NFR-002", "CON-001"],
        "traces_to": {},
        "status": "draft",
        "decision_status": "accepted",
        "confidence": "high",
        "created_at": "2026-08-03",
        "considered_options": ["Tauri", "Electron", "native view per platform"],
        "chosen_option": "Tauri",
    }
    data.update(overrides)
    for key, value in list(overrides.items()):
        if value is None:
            del data[key]
    return data


def _schema_errors(data):
    """Validate a frontmatter dict against the real schema; return error strings."""
    validator = vd.core.make_validator(SCHEMA)
    assert validator is not None, "jsonschema is required for these tests"
    return vd.core.validate_against_schema(data, validator)


def test_accepted_adr_is_valid():
    assert _schema_errors(_adr()) == []


def test_proposed_adr_without_chosen_option_is_valid():
    """A deferred ASR has no chosen option yet — that is the honest record."""
    data = _adr(decision_status="proposed", chosen_option=None,
                considered_options=None)
    assert _schema_errors(data) == []


def test_accepted_adr_with_one_considered_option_is_rejected():
    """The D1 guard: never a fabricated single-option decision record."""
    assert _schema_errors(_adr(considered_options=["Tauri"])) != []


def test_accepted_adr_without_chosen_option_is_rejected():
    assert _schema_errors(_adr(chosen_option=None)) != []


def test_proposed_adr_with_chosen_option_is_rejected():
    """'Proposed' means undecided; a chosen option contradicts it."""
    assert _schema_errors(_adr(decision_status="proposed")) != []


def test_adr_bad_decision_status_is_rejected():
    assert _schema_errors(_adr(decision_status="pending")) != []


def test_component_carrying_decision_status_is_rejected():
    """Branch isolation: decision_status is meaningless on a component."""
    data = {
        "id": "CMP-001", "type": "component", "title": "t", "description": "d",
        "traces_from": [], "traces_to": {}, "status": "draft",
        "confidence": "high", "created_at": "2026-08-03",
        "responsibility": "r", "boundary": "internal", "depends_on": [],
        "decision_status": "accepted",
    }
    assert _schema_errors(data) != []


def test_adr_id_pattern_accepted_by_schema():
    raw = json.load(open(SCHEMA, encoding="utf-8"))
    assert "ADR" in raw["properties"]["id"]["pattern"]
    assert "adr" in raw["properties"]["type"]["enum"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k adr -v
```

Expected: FAIL. `test_accepted_adr_is_valid` reports errors because `type: adr` is not in the enum and `ADR-001` does not match the id pattern.

- [ ] **Step 3: Widen the id pattern and type enum**

In `skills/design/schema/design.schema.json`, change the `id` pattern (line 22):

```json
      "pattern": "^(CMP|IF|ADR)(-[A-Z0-9]+)*-[0-9]{3,}$"
```

And its description on line 21:

```json
      "description": "Categorical, zero-padded, stable ID. Prefix encodes type: CMP->component, IF->interface, ADR->adr. An optional uppercase category infix is allowed (e.g. CMP-AUTH-004).",
```

Change the `type` enum (lines 27-30):

```json
      "enum": [
        "component",
        "interface",
        "adr"
      ]
```

- [ ] **Step 4: Add the ADR branch**

Insert this object into the top-level `allOf` array, directly after the interface branch's closing brace (after line 242, before the `]` that closes `allOf`). Note the leading comma:

```json
    ,
    {
      "$comment": "ADR branch (STO-100). decision_status is separate from status because a JSON Schema branch can only NARROW an enum: MADR's 'accepted' is absent from the base status enum, so it could never validate there, and widening the base would put decision vocabulary on every component and interface. The nested allOf then splits on decision_status itself — an accepted decision must name what it chose and what it beat; a proposed one (a deferred ASR) must not claim a choice it has not made.",
      "if": {
        "properties": {
          "type": {
            "const": "adr"
          }
        },
        "required": [
          "type"
        ]
      },
      "then": {
        "required": [
          "decision_status"
        ],
        "properties": {
          "decision_status": {
            "type": "string",
            "description": "MADR decision status. Distinct from `status`, which is the artifact lifecycle.",
            "enum": [
              "proposed",
              "rejected",
              "accepted",
              "deprecated",
              "superseded"
            ]
          },
          "considered_options": {
            "type": "array",
            "description": "The options weighed. Never fabricated: when a second option cannot be recovered from the recorded decision, no ADR is emitted at all.",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true
          },
          "chosen_option": {
            "type": "string",
            "description": "The option taken. Absent while the decision is still proposed.",
            "minLength": 1
          }
        },
        "allOf": [
          {
            "$comment": "A settled decision names what it chose and at least one alternative it beat.",
            "if": {
              "properties": {
                "decision_status": {
                  "enum": [
                    "accepted",
                    "rejected",
                    "deprecated",
                    "superseded"
                  ]
                }
              },
              "required": [
                "decision_status"
              ]
            },
            "then": {
              "required": [
                "chosen_option",
                "considered_options"
              ],
              "properties": {
                "considered_options": {
                  "minItems": 2
                }
              }
            }
          },
          {
            "$comment": "A proposed decision has not been taken; claiming a chosen option would misrepresent it.",
            "if": {
              "properties": {
                "decision_status": {
                  "const": "proposed"
                }
              },
              "required": [
                "decision_status"
              ]
            },
            "then": {
              "not": {
                "required": [
                  "chosen_option"
                ]
              }
            }
          }
        ]
      }
    }
```

- [ ] **Step 5: Run the tests to verify they pass**

Run:

```bash
python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k adr -v
```

Expected: PASS, 8 tests.

- [ ] **Step 6: Verify the schema is still valid JSON and the existing suite is unbroken**

Run:

```bash
python3 -c "import json; json.load(open('skills/design/schema/design.schema.json')); print('valid json')"
python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q
```

Expected: `valid json`, then all pre-existing tests still pass. Two failures are expected here **only if** you have already started Task 2; at this point the suite should be green because the validator still skips `adr/`.

- [ ] **Step 7: Commit**

```bash
git add skills/design/schema/design.schema.json skills/design/scripts/tests/test_validate_design.py
git commit -m "feat(sto-100): add ADR as a third design-artifact type

decision_status is separate from status because a schema branch can only
narrow an enum — MADR's 'accepted' could never validate against the artifact
lifecycle enum, and widening that base would put decision vocabulary on every
component and interface.

The nested branch on decision_status is what lets a deferred ASR be recorded
honestly: an accepted decision must name what it chose and what it beat, while
a proposed one must not claim a choice nobody has made."
```

---

### Task 2: Validate the `adr/` subtree

**Files:**
- Modify: `skills/design/scripts/validate_design.py` — module docstring (lines 10, 18, 25), `SKIP_DIRNAMES` (line 89), `PREFIX_TO_TYPE` (lines 94-97), fallback lists (lines 120-140), new heading gate, `validate()` hook (lines 310-322)
- Modify: `lib/artifact_core.py` — `discover_files` docstring (line 333)
- Rewrite: `skills/design/scripts/tests/fixtures/valid/adr/ADR-001-single-writer-db.md`
- Create: four fixture dirs under `skills/design/scripts/tests/fixtures/invalid/`
- Modify: `skills/design/scripts/tests/test_validate_design.py` — two inverting tests

**Interfaces:**
- Consumes: the `adr` type and `decision_status` field from Task 1
- Produces: `vd.REQUIRED_ADR_HEADINGS` (the five MADR headings) and `vd.check_adr_headings(path)`. Task 3's agent and Task 5's formatter must emit exactly these five heading strings; this list is the authority on their spelling.

**Two existing tests invert in this task.** Both currently assert the behaviour being removed, so they fail before you touch them and must be edited, not deleted:
- `test_prefix_to_type_mapping` asserts the exact dict `{"CMP": "component", "IF": "interface"}`
- `test_skip_files_and_subtrees_are_ignored` asserts `"ADR-001" not in out`

- [ ] **Step 1: Write the failing tests**

First **edit** the two inverting tests in `skills/design/scripts/tests/test_validate_design.py`.

Replace `test_prefix_to_type_mapping`:

```python
def test_prefix_to_type_mapping():
    assert vd.PREFIX_TO_TYPE == {
        "CMP": "component",
        "IF": "interface",
        "ADR": "adr",
    }
```

Replace `test_skip_files_and_subtrees_are_ignored`:

```python
def test_skip_files_and_subtrees_are_ignored(capsys):
    """assumptions.md, index.yaml and the diagrams/ subtree must not be
    validated as artifacts. adr/ IS validated as of STO-100."""
    run(VALID_DIR)
    out = capsys.readouterr().out
    assert "assumptions.md" not in out
    assert "drivers.md" not in out
    assert "index.yaml" not in out
    assert "c4-container" not in out
    assert "ADR-001" in out
```

Then append the new tests:

```python
def test_adr_headings_all_present_passes(tmp_path):
    body = (
        "# ADR-001: X\n\n"
        "## Context and Problem Statement\nc\n\n"
        "## Decision Drivers\n- NFR-002\n\n"
        "## Considered Options\n- A\n- B\n\n"
        "## Decision Outcome\nA\n\n"
        "### Consequences\n- good: g\n- bad: b\n"
    )
    path = tmp_path / "ADR-001-x.md"
    path.write_text(body, encoding="utf-8")
    assert vd.check_adr_headings(str(path)) == []


def test_adr_missing_heading_is_flagged(tmp_path):
    body = (
        "# ADR-001: X\n\n"
        "## Context and Problem Statement\nc\n\n"
        "## Decision Drivers\n- NFR-002\n\n"
        "## Considered Options\n- A\n- B\n\n"
        "## Decision Outcome\nA\n"
    )
    path = tmp_path / "ADR-001-x.md"
    path.write_text(body, encoding="utf-8")
    errors = vd.check_adr_headings(str(path))
    assert any("Consequences" in e for e in errors)


def test_adr_non_utf8_is_reported_not_raised(tmp_path):
    path = tmp_path / "ADR-001-x.md"
    path.write_bytes(b"\xff\xfe## Decision Outcome\n")
    errors = vd.check_adr_headings(str(path))
    assert errors and any("could not read" in e for e in errors)


def test_adr_prefix_type_mismatch_is_flagged():
    df = vd.DesignFile("mem://a")
    df.frontmatter = {"id": "ADR-001", "type": "component"}
    vd.cross_file_checks([df])
    assert any("implies type" in e for e in df.errors)
```

And register the four new invalid fixture cases by adding these entries to the `INVALID_CASES` dict:

```python
    "adr_missing_heading": "missing required MADR heading",
    "adr_bad_decision_status": "decision_status",
    "adr_one_considered_option": "considered_options",
    "adr_proposed_with_chosen_option": "chosen_option",
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m pytest skills/design/scripts/tests/test_validate_design.py -v
```

Expected: FAIL. `check_adr_headings` does not exist (AttributeError), `PREFIX_TO_TYPE` lacks `ADR`, `ADR-001` is absent from the output, and the four new fixture dirs do not exist.

- [ ] **Step 3: Stop skipping `adr/` and teach the validator the prefix**

In `skills/design/scripts/validate_design.py`, change line 89:

```python
# Whole subtrees another stage owns in a non-artifact format.
SKIP_DIRNAMES = {"diagrams"}
```

And lines 94-97:

```python
# ID prefix -> expected `type`. Mirrors the schema contract.
PREFIX_TO_TYPE = {
    "CMP": "component",
    "IF": "interface",
    "ADR": "adr",
}
```

- [ ] **Step 4: Add the MADR heading gate**

Insert after the `REQUIRED_DRIVERS_HEADINGS` list (after line 114):

```python
# MADR 4.0 body headings, gated per ADR file (STO-100). Presence only —
# content is never gated, exactly as for assumptions.md and drivers.md.
# `### Consequences` is H3 by MADR convention: it sits under Decision Outcome.
REQUIRED_ADR_HEADINGS = [
    "## Context and Problem Statement",
    "## Decision Drivers",
    "## Considered Options",
    "## Decision Outcome",
    "### Consequences",
]
```

Then add this function directly after `check_drivers_artifact` (after line 294):

```python
def check_adr_headings(path: str) -> List[str]:
    """Gate one ADR body's MADR 4.0 headings.

    Presence only; content is never gated. Unlike assumptions.md and drivers.md
    this is per-file rather than per-directory, so it does not go through
    ``core._check_project_artifact`` (which resolves a fixed filename inside a
    root). The heading-anchoring regex is the same: a full-line match, so an
    H3 '### Considered Options' does not satisfy the H2 requirement.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"could not read ADR body: {exc}"]

    errors: List[str] = []
    for heading in REQUIRED_ADR_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(f"missing required MADR heading '{heading}'")
    return errors
```

- [ ] **Step 5: Hook the gate into `validate()`**

In `validate()`, replace the body of the discovery loop (lines 310-322) with:

```python
    for path in discover_files(design_dir):
        df = DesignFile(path)
        data, err = parse_frontmatter(path)
        if err:
            df.errors.append(err)
            files.append(df)
            continue
        df.frontmatter = data
        if validator is not None:
            df.errors.extend(core.validate_against_schema(data, validator))
        else:
            df.errors.extend(_fallback_validate(data))
        if data.get("type") == "adr":
            df.errors.extend(check_adr_headings(path))
        files.append(df)
```

- [ ] **Step 6: Extend the stdlib fallback path**

In `_FALLBACK_REQUIRED_BY_TYPE` (lines 129-132), add the adr row:

```python
_FALLBACK_REQUIRED_BY_TYPE = {
    "component": ["responsibility", "boundary", "depends_on"],
    "interface": ["provider", "operations", "interaction", "error_modes"],
    # `chosen_option`/`considered_options` are conditional on decision_status,
    # which this path cannot express — the schema is the source of truth.
    "adr": ["decision_status"],
}
```

And in `_FALLBACK_ENUMS` (lines 133-140), extend `type` and add `decision_status`:

```python
_FALLBACK_ENUMS = {
    "type": {"component", "interface", "adr"},
    "boundary": {"internal", "external"},
    "interaction": {"synchronous", "asynchronous"},
    "confidence": {"high", "medium", "low"},
    "status": {"draft", "reviewed", "approved", "implemented", "verified", "obsolete"},
    "decision_status": {
        "proposed", "rejected", "accepted", "deprecated", "superseded",
    },
    "scope": {"project", "epic", "story"},
}
```

- [ ] **Step 7: Correct the module docstring**

In `skills/design/scripts/validate_design.py`, change line 10:

```
      adr/           ADR-XXX-*.md
```

Change lines 17-19:

```
  1. Discovers every ``*.md`` under the design dir (recursively), skipping the
     ``diagrams/`` subtree and the
     ``assumptions.md``/``drivers.md``/``index.yaml`` companions.
```

Change line 25:

```
       - The ID prefix matches ``type`` (CMP->component, IF->interface,
         ADR->adr).
```

And add to the numbered list, after item 5 (line 34):

```
  6. Gates each ADR body's MADR 4.0 headings.
```

Renumber the old item 6 to 7.

In `lib/artifact_core.py`, change the `discover_files` docstring (line 333) so it no longer names `adr/` as skipped:

```
    ``skip_dirnames`` are whole subtrees a stage owns in another format (M2's
    ``diagrams/``); they are pruned in-place from the walk. A stray
```

- [ ] **Step 8: Rewrite the ADR fixture as a real ADR**

The existing fixture's body asserts the behaviour this task removes. Replace `skills/design/scripts/tests/fixtures/valid/adr/ADR-001-single-writer-db.md` entirely:

```markdown
---
id: ADR-001
type: adr
title: Single-writer database
description: Whether the order store admits concurrent writers.
traces_from:
  - NFR-001
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: 2026-07-18
considered_options:
  - Single writer
  - Multi-writer with optimistic locking
chosen_option: Single writer
---

# ADR-001: Single-writer database

## Context and Problem Statement

The order store is written by the order service and read by everything else.
Admitting a second writer would require a conflict-resolution story.

## Decision Drivers

- NFR-001

## Considered Options

- **Single writer** — one component owns every write.
- **Multi-writer with optimistic locking** — any component may write; conflicts
  are resolved on commit.

## Decision Outcome

Single writer. `CMP-001` owns every write to the order store.

### Consequences

- Good: no conflict-resolution path to design, test, or get wrong.
- Bad: every write funnels through one component, which becomes a throughput
  ceiling if order volume grows past a single process.
```

Note this fixture is referenced by `CMP-001-order-service.md`'s `traces_to.adr: [ADR-001]`, which now resolves to a real validated artifact.

- [ ] **Step 9: Create the four invalid fixtures**

Each invalid fixture dir needs `assumptions.md` and `drivers.md`, or it fails on the project-artifact gate instead of the case under test. Create all four by copying the companions from an existing case:

```bash
cd skills/design/scripts/tests/fixtures/invalid
for case in adr_missing_heading adr_bad_decision_status adr_one_considered_option adr_proposed_with_chosen_option; do
  mkdir -p "$case/adr"
  cp bad_enum/assumptions.md bad_enum/drivers.md "$case/"
done
cd -
```

`invalid/adr_missing_heading/adr/ADR-001-x.md` — valid frontmatter, no `### Consequences`:

```markdown
---
id: ADR-001
type: adr
title: X
description: d
traces_from: []
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: 2026-08-03
considered_options:
  - A
  - B
chosen_option: A
---

# ADR-001: X

## Context and Problem Statement
c

## Decision Drivers
- none

## Considered Options
- A
- B

## Decision Outcome
A
```

`invalid/adr_bad_decision_status/adr/ADR-001-x.md` — all five headings present; `decision_status` outside the MADR enum:

```markdown
---
id: ADR-001
type: adr
title: X
description: d
traces_from: []
traces_to: {}
status: draft
decision_status: pending
confidence: high
created_at: 2026-08-03
considered_options:
  - A
  - B
chosen_option: A
---

# ADR-001: X

## Context and Problem Statement
c

## Decision Drivers
- none

## Considered Options
- A
- B

## Decision Outcome
A

### Consequences
- good: g
- bad: b
```

`invalid/adr_one_considered_option/adr/ADR-001-x.md` — all five headings present; an accepted decision listing only one option, which is the D1 guard:

```markdown
---
id: ADR-001
type: adr
title: X
description: d
traces_from: []
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: 2026-08-03
considered_options:
  - A
chosen_option: A
---

# ADR-001: X

## Context and Problem Statement
c

## Decision Drivers
- none

## Considered Options
- A

## Decision Outcome
A

### Consequences
- good: g
- bad: b
```

`invalid/adr_proposed_with_chosen_option/adr/ADR-001-x.md` — all five headings present; a proposed decision claiming a choice it has not made:

```markdown
---
id: ADR-001
type: adr
title: X
description: d
traces_from: []
traces_to: {}
status: draft
decision_status: proposed
confidence: low
created_at: 2026-08-03
considered_options:
  - A
  - B
chosen_option: A
---

# ADR-001: X

## Context and Problem Statement
c

## Decision Drivers
- none

## Considered Options
- A
- B

## Decision Outcome
Pending.

### Consequences
- good: g
- bad: b
```

- [ ] **Step 10: Run the tests to verify they pass**

Run:

```bash
python3 -m pytest skills/design/scripts/tests -v
```

Expected: PASS, including the four new `test_invalid_case_fails[adr_*]` parametrised cases.

- [ ] **Step 11: Verify the shipped example still validates**

The tamagotchi design set has no `adr/` directory. Removing `adr` from `SKIP_DIRNAMES` must not change its result — this is the "zero ADRs is legal" contract.

Run:

```bash
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q
```

Expected: `Summary: 23/23 file(s) passed`, exit 0; then the full suite green.

- [ ] **Step 12: Commit**

```bash
git add skills/design/scripts/validate_design.py lib/artifact_core.py skills/design/scripts/tests/
git commit -m "feat(sto-100): validate the adr/ subtree

adr/ leaves SKIP_DIRNAMES and ADR joins PREFIX_TO_TYPE, so ADRs pass through
the same structural gate as every other artifact rather than being the one
type with no machine check.

Two existing tests inverted rather than being deleted: test_prefix_to_type_mapping
pinned the exact two-entry dict, and test_skip_files_and_subtrees_are_ignored
asserted ADR-001 was absent from the report. Both encoded the behaviour this
change removes. The valid ADR fixture likewise had a body explaining that it
was skipped; it is now a real ADR."
```

---

### Task 3: The `adr-generator` agent

**Files:**
- Create: `agents/adr-generator.md`

**Interfaces:**
- Consumes: `REQUIRED_ADR_HEADINGS` from Task 2 — the agent's body template must emit those five headings verbatim, or the Task 2 gate rejects every ADR it produces.
- Produces: the `draft_adrs` hand-off shape that Task 4's orchestrator dispatches for and Task 5's formatter writes. Keys: `adrs[]` (with `id`, `title`, `description`, `traces_from`, `decision_status`, `confidence`, `considered_options`, `chosen_option`, `body`, `affects`) and `skipped[]` (with `source`, `reason`).

- [ ] **Step 1: Create the agent file**

Create `agents/adr-generator.md`. The frontmatter is single-key `description`, matching all 13 existing agent files:

```markdown
---
description: Architecture decision record specialist. Converts decisions the pipeline already recorded — resolved Q- questions in drivers.tradeoffs and deferred_to_decision ASRs from the critique report — into atomic MADR 4.0 ADR specs (ADR-). Never elicits new decisions and never invents alternatives: an entry whose rejected options cannot be recovered is skipped with a reason rather than turned into a one-option decision record. Returns a draft_adrs object.
---

# ADR Generator

You convert decisions the pipeline has **already made and already written down**
into first-class architecture decision records. You are dispatched at Stage 9.5
by the design orchestrator, after `design_context_artifact` exists and before
the formatter writes anything.

## The core rule

**You never invent an alternative.**

An ADR's whole value is that it records a decision that was actually taken,
against alternatives that were actually weighed. An ADR whose "Considered
Options" you reverse-engineered from the chosen option is a fabrication of
project history — and it is worse than no ADR at all, because after the fact
nobody can tell it from a real one.

So when you cannot recover a second option from what was recorded, you do not
write an ADR. Not a stub. Not an ADR listing one option. You put the entry in
`skipped` with a reason, and the decision stays in `drivers.md` where it
already lives.

## What qualifies

Exactly two sources. Nothing else becomes an ADR.

### 1. Resolved `Q-` questions

These reach you as `drivers.tradeoffs` entries. Stage 9 of the orchestrator
routes every `inherited_open_questions` entry with `disposition: resolved`
into `tradeoffs`, one entry each.

**The discriminator is the `Q-` ID**, not how important the entry feels. A
qualifying entry's `decision` field names the question it settled:

> `"Q-4 resolved to Tauri — a Rust core with an OS-supplied system webview —
> over Electron and a native view per platform"`

That names a `Q-` ID, a chosen option, and two rejected ones. It qualifies.

Compare a structural tradeoff from the same set:

> `"IF-002 accepts diagnostic entries asynchronously and makes durability an
> explicit, separate flush rather than writing synchronously on the decay
> path"`

This has a chosen and a rejected shape, and it is a real engineering
trade. But it names no `Q-` ID: it describes a shape the decomposition took,
not a question that was posed and settled. It does **not** qualify. It stays in
`drivers.md`, and it goes in your `skipped` list so the omission is visible.

### 2. `deferred_to_decision` ASRs

The critic marks an ASR `deferred_to_decision` when it turns on a decision
nothing in the set has made yet. Each becomes an ADR with
`decision_status: proposed`.

A proposed ADR has **no `chosen_option`** — that is what "deferred" means, and
the schema rejects one. List whatever options are genuinely known; if none are,
`considered_options` may be omitted entirely.

**A deferred ASR is a different input shape from a resolved `Q-`.** It reaches
you as an `asr_coverage` row, not a `drivers.tradeoffs` entry, and it carries
none of `gains`, `costs`, or `affected`:

```yaml
asr_coverage:
  - requirement_id: NFR-002
    addressed_by: [ CMP-001, IF-001 ]
    verdict: deferred_to_decision
    note: string          # the evidence for the verdict
```

Derive a proposed ADR from it like this — and from nothing else:

| ADR field | Source |
| --- | --- |
| `traces_from` | `[row.requirement_id]` |
| `body.context` | `row.note` |
| `decision_status` | always `proposed` |
| `confidence` | always `low` |
| `chosen_option` | **omitted** |
| `considered_options` | only options `row.note` actually names; omitted otherwise |
| `body.consequences` | **omitted** — nothing has been decided, so nothing has consequences yet |
| `affects` | `row.addressed_by` when non-empty; omit `affects` otherwise |
| owner (prose only) | the `owner` of the paired `Q-` entry in `design_context_artifact.open_questions` |

The orchestrator mints one `Q-` open question for every `deferred_to_decision`
ASR, and that entry — `{ id, statement, owner }` — is where the owner comes
from. **If you cannot find the paired `Q-` entry, do not name an owner.** An
invented owner is the same failure as an invented option: it reads as a record
of a real assignment nobody made. Write the `## Decision Outcome` section to
say the decision is pending, and name the owner only when you have one.

This replaces the old fallback in which a deferred ASR became only a `Q-` open
question. Emit the ADR; the orchestrator keeps the `Q-` too, so the question
stays visible in `assumptions.md`.

## Parsing a resolved decision

The `decision` field carries the chosen option and the rejected ones in prose.
Read the "over" / "rather than" / "instead of" clause:

| Recorded `decision` | `chosen_option` | `considered_options` |
| --- | --- | --- |
| "Q-4 resolved to Tauri … over Electron and a native view per platform" | `Tauri` | `Tauri`, `Electron`, `native view per platform` |
| "Q-3 resolved to Windows first for v1, with macOS and Linux staged after it" | `Windows first for v1` | `Windows first for v1`, `all three platforms at v1` |
| "Q-2 resolved to permanent death: one terminal lifecycle path, no reset setting" | `permanent death` | `permanent death`, `reset to a new pet` |

`chosen_option` is always also a member of `considered_options`.

Where the rejected option is implied rather than stated — Q-2's "no reset
setting" implies the reset alternative it rules out — you may name it, because
you are reading it out of the text, not inventing it. Where nothing in the text
implies an alternative at all, skip the entry.

## Field derivation

| ADR field | Source |
| --- | --- |
| `id` | assigned by the orchestrator; never mint your own |
| `title` | a short noun phrase naming the decision, not the question |
| `traces_from` | the entry's `affected` requirement IDs |
| `decision_status` | `accepted` for a resolved `Q-`; `proposed` for a deferred ASR |
| `confidence` | `high` for a resolved `Q-`; `low` for a deferred ASR |
| `considered_options` | parsed from `decision` (see above) |
| `chosen_option` | parsed from `decision`; omitted when `proposed` |
| `body.context` | why the question arose, from the entry and the requirements it affects |
| `body.decision_drivers` | the `traces_from` IDs |
| `body.consequences.good` | the entry's `gains` |
| `body.consequences.bad` | the entry's `costs` |
| `affects` | the union of `critique_report.asr_coverage[].addressed_by` for every row whose `requirement_id` is in this ADR's `traces_from` — the artifacts that address the requirements this decision drove, not a field the generator fills from its own judgment |

**This table describes source 1 only** — a resolved `Q-` arriving as a
`drivers.tradeoffs` entry. A deferred ASR arrives in a different shape and has
its own derivation table, above. Do not read `gains`, `costs`, or `affected`
off an `asr_coverage` row; those fields do not exist there.

`status` is always `draft`. It is the artifact lifecycle, not the decision
status, and every artifact this pipeline generates starts at `draft`.

## The `affects` field is transient

You are the only agent that knows which components and interfaces a decision
shaped. Report them in `affects` so the formatter can populate
`traces_to.adr` on those artifacts.

`affects` never reaches disk. The ADR↔artifact edge lives once, on
`CMP/IF.traces_to.adr` — the same rule the schema already applies to
`CMP.depends_on -> IF.provider`, where there is no `consumers` field. Do not
put a component list in the ADR's own `traces_to`; an ADR's `traces_to` is `{}`.

This mirrors `consumed_by` in `draft_interfaces`, which is transient for
exactly the same reason.

## Body template

Every ADR body carries these five headings verbatim. The validator gates their
presence.

```markdown
# <ID>: <Title>

## Context and Problem Statement

## Decision Drivers

## Considered Options

## Decision Outcome

### Consequences
```

`### Consequences` is H3 and sits under Decision Outcome — that is MADR 4.0's
shape, and the gate matches the exact string. Content is never gated; headings
always are.

## Return shape

```yaml
draft_adrs:
  adrs:
    - id: ADR-001
      title: Desktop runtime and UI shell
      description: Which runtime and UI shell the desktop app is built on.
      traces_from: [NFR-002, CON-001]
      decision_status: accepted
      confidence: high
      considered_options: [Tauri, Electron, native view per platform]
      chosen_option: Tauri
      body:
        context: string
        decision_drivers: [NFR-002, CON-001]
        considered_options_detail:
          - { option: Tauri, pros: string, cons: string }
        decision_outcome: string
        consequences:
          good: [string]
          bad: [string]
      affects: [CMP-006]

    # A deferred ASR (source 2). No chosen_option, no consequences.
    - id: ADR-002
      title: Retention policy for diagnostic logs
      description: How long local diagnostic entries are kept before rotation.
      traces_from: [NFR-007]
      decision_status: proposed
      confidence: low
      body:
        context: string          # from the asr_coverage row's `note`
        decision_drivers: [NFR-007]
        decision_outcome: >
          Pending. Owned by product (Q-6).
      affects: [CMP-002]
  skipped:
    - source: "IF-002 async flush"
      reason: "structural tradeoff, no Q- ID"
```

Emit `skipped` even when it is the longer list. A decision that did not become
an ADR should be visible, not silently absent — the same honesty the worked
examples practise about their own deviations.

If nothing qualifies, return `adrs: []`. That is a legal, complete result: the
formatter creates no `adr/` directory and the run succeeds. Never pad the set
to look productive.

## Stopping conditions

Stop and report to the orchestrator rather than guessing when:

- a `drivers.tradeoffs` entry is malformed — missing `decision`, `gains`,
  `costs`, or `affected`
- an `asr_coverage` row marked `deferred_to_decision` is malformed — missing
  `requirement_id`, or carrying no `note` to build a context from
- an `affected` list names a requirement ID in no recognised form
- `affects` would name a component or interface absent from the artifact set

An ADR built on a half-specified decision is the failure this stage exists to
prevent.
```

- [ ] **Step 2: Verify the frontmatter parses as single-key**

Run:

```bash
python3 -c "
import yaml
t = open('agents/adr-generator.md').read()
assert t.startswith('---'), 'no frontmatter'
d = yaml.safe_load(t.split('---', 2)[1])
assert list(d.keys()) == ['description'], d.keys()
print('ok: single-key description frontmatter')
"
```

Expected: `ok: single-key description frontmatter`

- [ ] **Step 3: Verify the five headings match the validator exactly**

The agent's template and `REQUIRED_ADR_HEADINGS` must agree character for character.

Run:

```bash
python3 -c "
import sys
sys.path.insert(0, 'skills/design/scripts')
import validate_design as vd
body = open('agents/adr-generator.md').read()
missing = [h for h in vd.REQUIRED_ADR_HEADINGS if h not in body]
assert not missing, f'agent template missing: {missing}'
print(f'ok: all {len(vd.REQUIRED_ADR_HEADINGS)} MADR headings present')
"
```

Expected: `ok: all 5 MADR headings present`

- [ ] **Step 4: Verify the no-invention rule is stated, not implied**

Run:

```bash
grep -c "never invent\|Never invent\|not invent" agents/adr-generator.md
```

Expected: at least `1`.

- [ ] **Step 5: Commit**

```bash
git add agents/adr-generator.md
git commit -m "feat(sto-100): add the ADR generator specialist

The agent derives ADRs from two recorded sources and nothing else, with the
Q- ID as the discriminator between a settled question and a structural
tradeoff — the same 'name the test, don't describe the vibe' shape STO-217
gave the component specialist.

Its central rule is that it never invents a rejected option. A fabricated
considered-options list is indistinguishable from a real one after the fact,
so an unparseable entry is skipped and left in drivers.md instead."
```

---

### Task 4: Wire Stage 9.5 into the orchestrator

**Files:**
- Modify: `agents/design-orchestrator.md` — pipeline diagram (lines 43-49), ID allocation, new Stage 9.5 section, Stage 11 slot (lines 489-495)

**Interfaces:**
- Consumes: the `draft_adrs` shape from Task 3
- Produces: ADR ID allocation (`ADR-001`, zero-padded, categorical — the same scheme as CMP/IF) and the Stage 9.5 dispatch that Task 5's formatter receives `draft_adrs` from.

- [ ] **Step 1: Update the pipeline diagram**

In `agents/design-orchestrator.md`, replace lines 43-49:

```markdown
        ▼  on pass: orchestrator synthesises assumptions + drivers
   [ adr-generator ]   resolved Q- decisions + deferred ASRs → draft_adrs
        │
        ▼
[ design-formatter ]   CMP/IF/ADR files + assumptions.md + drivers.md + index.yaml
                    + traces_to.adr back-fill
                    + validate_design.py hard gate (the structural gate)
        │
        ▼
   [c4-generator]  ← STO-101 slot
```

And the paragraph that follows it:

```markdown
`component-specialist`, `interface-specialist`, `design-critic`,
`adr-generator`, and `design-formatter` are the agents you dispatch to.
`c4-generator` does not exist yet; Stage 12 declares its slot.
```

- [ ] **Step 2: Add the Stage 9.5 section**

Insert immediately before `## Stage 10 — Format: the formatter_result hand-off` (line 468):

```markdown
## Stage 9.5 — ADR generation

Dispatch `adr-generator` with the `design_context_artifact` you just assembled
and the `critique_report` from Stage 8. It needs `drivers.tradeoffs` (which
carries every resolved `Q-` decision) and `asr_coverage` (which carries the
`deferred_to_decision` rows).

**Allocate the ADR IDs before dispatching**, the same way you allocate CMP and
IF blocks at Stage 4: zero-padded, categorical, starting at `ADR-001`. The
generator never mints its own. Count the qualifying entries first — resolved
`Q-` tradeoffs plus `deferred_to_decision` ASRs — and hand down a block that
size.

It returns:

```yaml
draft_adrs:
  adrs: [ { id, title, description, traces_from, decision_status,
            confidence, considered_options, chosen_option, body, affects } ]
  skipped: [ { source, reason } ]
```

**`affects` is transient.** Carry it to the formatter, which uses it to
populate `traces_to.adr` on the named components and interfaces, then drops it.
It never reaches disk: the ADR↔artifact edge lives once, on
`CMP/IF.traces_to.adr`, exactly as the `CMP.depends_on -> IF.provider` edge
lives once. This is the same transient-field handling as `consumed_by` in
`draft_interfaces` at Stage 6.

Validate before advancing:

- Every `affects` entry names an artifact in the approved set. A dangling one
  means re-dispatch, not a silent drop.
- Every `id` is one you allocated.
- `adrs: []` is a legal, complete result. Nothing qualified; the formatter
  writes no `adr/` directory and the run proceeds normally. Do not treat an
  empty set as a failure and do not re-dispatch to get a bigger one.

**A `deferred_to_decision` ASR now produces both an ADR and its `Q-` open
question.** The ADR records the decision as `proposed`; the `Q-` keeps the
question visible in `assumptions.md`. Stage 9's rule that a
`deferred_to_decision` ASR forces a `Q-` entry is unchanged — the ADR is
additional, not a replacement. They are two views of one gap: what must be
decided, and the record that will hold the decision.
```

- [ ] **Step 3: Replace the Stage 11 slot**

Replace lines 489-495 (`## Stage 11 — ADR generation (SLOT — owned by STO-100)` and its paragraph):

```markdown
## Stage 11 — (retired)

ADR generation was originally slotted here, after the formatter. It runs at
Stage 9.5 instead, before the formatter.

The reason is the structural gate. At Stage 11 the generator would be a second
writer: it would re-open CMP/IF files the formatter had already written and the
validator had already passed, patch `traces_to.adr` into them, and re-run the
gate. STO-99 and STO-215 both landed fixes whose entire point was to make the
formatter the single writer and the single structural gate. Everything the
generator needs exists at Stage 9, and nothing it produces is needed before
Stage 10, so the earlier placement costs nothing and keeps one writer.
```

- [ ] **Step 4: Verify no stale slot language survives**

Run:

```bash
grep -n "STO-100\|Do not invent ADR" agents/design-orchestrator.md
```

Expected: no line claiming ADR generation is unimplemented or instructing the reader not to invent ADR files. A historical reference inside the Stage 11 retirement note is fine.

- [ ] **Step 5: Verify frontmatter still parses**

Run:

```bash
python3 -c "
import yaml
t = open('agents/design-orchestrator.md').read()
d = yaml.safe_load(t.split('---', 2)[1])
assert list(d.keys()) == ['description']
print('ok')
"
```

Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add agents/design-orchestrator.md
git commit -m "feat(sto-100): dispatch ADR generation at Stage 9.5

The Stage 11 slot put ADR generation after the formatter, which would have
made it a second writer re-opening files the structural gate had already
passed. That is what STO-99 and STO-215 fixed. Everything the generator needs
exists at Stage 9, so moving it earlier costs nothing and keeps one writer.

A deferred_to_decision ASR now yields both an ADR and its Q- question: the
ADR holds the decision, the Q- keeps the gap visible."
```

---

### Task 5: Teach the formatter to write `adr/`

**Files:**
- Modify: `agents/design-formatter.md` — directory tree (line 32), the `adr/`-belongs-to-STO-100 note (line 45), `traces_to` guidance (lines 153-156), the do-not-create rule (line 326)

**Interfaces:**
- Consumes: `draft_adrs` (Task 3's shape) forwarded by Task 4's orchestrator
- Produces: `.sdlc/design/adr/<ADR-ID>-<kebab-title>.md` files and `traces_to.adr` entries on components and interfaces. Task 6's SKILL.md documents this output.

- [ ] **Step 1: Update the directory tree**

In `agents/design-formatter.md`, change line 32 so `adr/` is no longer marked as someone else's:

```
├── adr/            ← ADR-XXX-<kebab-title>.md
```

- [ ] **Step 2: Replace the ownership note**

Replace line 45 (`adr/` and `diagrams/` belong to STO-100 and STO-101...):

```markdown
`diagrams/` belongs to STO-101, which does not exist yet — do not create it.
`adr/` you now write, from the `draft_adrs` the orchestrator forwards. Create
it only when `draft_adrs.adrs` is non-empty: an absent `adr/` directory is the
correct output when nothing qualified, not an omission to correct.
```

- [ ] **Step 3: Add the ADR writing rules**

Insert a subsection after the note from Step 2:

```markdown
### Writing ADRs

One file per entry in `draft_adrs.adrs`, named `<ID>-<kebab-title>.md` — the
same convention as components and interfaces.

Frontmatter comes straight from the entry, plus `type: adr`, `status: draft`,
and `traces_to: {}`:

```yaml
---
id: ADR-001
type: adr
title: Desktop runtime and UI shell
description: Which runtime and UI shell the desktop app is built on.
traces_from: [NFR-002, CON-001]
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: <today>
considered_options: [Tauri, Electron, native view per platform]
chosen_option: Tauri
---
```

**Omit `chosen_option` entirely when `decision_status` is `proposed`.** The
schema rejects a proposed ADR that claims a chosen option — a deferred
decision has not been made, and writing one would misrepresent it.

The body renders `entry.body` under the five MADR headings, in this order and
with these exact strings:

```markdown
# <ID>: <Title>

## Context and Problem Statement

## Decision Drivers

## Considered Options

## Decision Outcome

### Consequences
```

The validator gates all five. `### Consequences` is H3 and sits under Decision
Outcome.

### Back-filling `traces_to.adr`

Each entry carries a transient `affects` list of CMP/IF IDs. For every ID in
it, add the ADR's ID to that artifact's `traces_to.adr` **before** you write
the artifact file. You write every file in this stage, so this is one pass with
no re-opening.

`affects` itself is never written. The edge lives once, on
`CMP/IF.traces_to.adr` — an ADR's own `traces_to` stays `{}`. This is the rule
the schema already states for `CMP.depends_on -> IF.provider`: one direction on
disk, no mirror field.
```

- [ ] **Step 4: Update the `traces_to` guidance**

At lines 153-156, the text says `adr` and `diagrams` stay empty because STO-100 and STO-101 do not exist. Replace that clause:

```markdown
- `traces_to.adr` carries real entries whenever `draft_adrs` supplied an
  `affects` list naming this artifact. `traces_to.diagrams` stays empty until
  STO-101 exists. `code` and `tests` stay empty at this stage.
```

- [ ] **Step 5: Update the do-not-create rule**

At line 326, replace the rule forbidding both directories:

```markdown
- Do not create `diagrams/`. It belongs to STO-101, which does not exist yet.
  Create `adr/` only when `draft_adrs.adrs` is non-empty.
```

- [ ] **Step 6: Verify no stale claims survive**

Run:

```bash
grep -n "adr" agents/design-formatter.md | grep -i "not written\|do not create adr\|belong to STO-100"
```

Expected: no output.

Run:

```bash
python3 -c "
import sys
sys.path.insert(0, 'skills/design/scripts')
import validate_design as vd
body = open('agents/design-formatter.md').read()
missing = [h for h in vd.REQUIRED_ADR_HEADINGS if h not in body]
assert not missing, f'formatter template missing: {missing}'
print('ok: formatter emits all five MADR headings')
"
```

Expected: `ok: formatter emits all five MADR headings`

- [ ] **Step 7: Verify frontmatter still parses**

Run:

```bash
python3 -c "
import yaml
t = open('agents/design-formatter.md').read()
d = yaml.safe_load(t.split('---', 2)[1])
assert list(d.keys()) == ['description']
print('ok')
"
```

Expected: `ok`

- [ ] **Step 8: Commit**

```bash
git add agents/design-formatter.md
git commit -m "feat(sto-100): write adr/ and back-fill traces_to.adr

The formatter writes ADRs in the same pass as components and interfaces and
populates traces_to.adr from the generator's transient affects list before
writing each file, so nothing is re-opened and one structural gate still
covers everything.

An absent adr/ directory stays correct when nothing qualified — that contract
predates this ticket and survives it, now meaning 'nothing qualified' rather
than 'not implemented'."
```

---

### Task 6: Update the critic and the skill

**Files:**
- Modify: `agents/design-critic.md` — the `deferred_to_decision` bullet (lines 101-108)
- Modify: `skills/design/SKILL.md` — "What This Stage Does Not Produce" (lines 300-307), and the pipeline/output documentation

**Interfaces:**
- Consumes: the Stage 9.5 behaviour from Task 4 and the `adr/` output from Task 5
- Produces: nothing downstream depends on this task; it is the documentation catch-up that makes the four files agree.

- [ ] **Step 1: Update the critic's deferral bullet**

In `agents/design-critic.md`, replace lines 101-108:

```markdown
- **`deferred_to_decision`** — the ASR turns on a decision nothing in the set
  has made yet (a runtime choice, a framework choice, a still-open inherited
  question). This is legal and passes the gate, but it is not free: it produces
  an ADR with `decision_status: proposed` at Stage 9.5 **and** a `Q-` open
  question downstream. The ADR is where the decision will be recorded when it
  is taken; the `Q-` keeps the open gap visible in `assumptions.md` until then.
  Do not use `deferred_to_decision` as a way to avoid finding coverage that is
  actually there — reach for it only when the requirement genuinely cannot be
  addressed without a decision the set does not contain.
```

- [ ] **Step 2: Rewrite the SKILL.md section**

In `skills/design/SKILL.md`, replace lines 300-307 (`## What This Stage Does Not Produce` and its first paragraph):

```markdown
## ADRs

This stage writes architecture decision records to `.sdlc/design/adr/` in MADR
4.0 format, one atomic file per decision, validated by the same structural gate
as components and interfaces.

ADRs are **derived, never elicited**. The generator promotes decisions the
pipeline already recorded — resolved `Q-` questions from the architecture
interview, and ASRs the critic marked `deferred_to_decision` — and it never
invents a rejected option to fill out the template. A decision whose
alternatives cannot be recovered stays in `drivers.md` and is reported in the
generator's `skipped` list.

So an empty or absent `adr/` directory is a legal outcome: it means nothing
qualified, not that something failed.

## What This Stage Does Not Produce

This stage does not write C4 diagrams. `.sdlc/design/diagrams/` is a declared
dispatch slot owned by STO-101 — an absent `diagrams/` directory after this
skill runs is expected, not a bug.
```

- [ ] **Step 3: Verify the stale claims are gone**

Run:

```bash
grep -n "does not write ADRs\|STO-100 exists\|until STO-100" skills/design/SKILL.md agents/design-critic.md agents/design-formatter.md agents/design-orchestrator.md
```

Expected: no output. Every file that described ADR generation as pending now describes it as existing.

- [ ] **Step 4: Verify all 14 agent files still parse**

Run:

```bash
python3 -c "
import glob, yaml
files = sorted(glob.glob('agents/*.md'))
bad = []
for f in files:
    t = open(f).read()
    if not t.startswith('---'):
        bad.append((f, 'no frontmatter')); continue
    d = yaml.safe_load(t.split('---', 2)[1])
    if list(d.keys()) != ['description']:
        bad.append((f, list(d.keys())))
print(f'{len(files)} agent files checked')
assert not bad, bad
print('all single-key description frontmatter: OK')
"
```

Expected: `14 agent files checked`, then `all single-key description frontmatter: OK`.

- [ ] **Step 5: Run the full suite and both validators**

Run:

```bash
python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
```

Expected: all tests pass; `23/23` design; `22/22` requirements.

- [ ] **Step 6: Commit**

```bash
git add agents/design-critic.md skills/design/SKILL.md
git commit -m "docs(sto-100): retire the 'until STO-100 exists' fallbacks

Four files described ADR generation as pending and carried a temporary
fallback because of it. The critic's deferred_to_decision verdict now yields
both an ADR and its Q- question rather than only the Q-, and the skill
documents adr/ as output instead of as a slot.

An absent adr/ directory keeps its old meaning of 'expected, not a bug' but
now means nothing qualified rather than nothing is implemented."
```

---

## Verification Checklist

Run after all six tasks:

- [ ] `python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q` — all pass (95 pre-existing + ~16 new)
- [ ] `python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design` — exit 0, 23/23
- [ ] `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements` — exit 0, 22/22
- [ ] `python3 -c "import json; json.load(open('skills/design/schema/design.schema.json'))"` — valid JSON
- [ ] All 14 files in `agents/` parse to single-key `description` frontmatter
- [ ] `git status --short docs/requirements/examples/` — empty (STO-219 owns regeneration)
- [ ] `grep -rn "until STO-100\|does not write ADRs\|STO-100 owns" agents/ skills/ lib/` — no output
- [ ] `grep -n "diagrams" skills/design/scripts/validate_design.py` — `SKIP_DIRNAMES` still contains `diagrams`
- [ ] `grep -c "adr" skills/design/scripts/validate_design.py` — `SKIP_DIRNAMES` no longer contains `adr`
- [ ] The five strings in `vd.REQUIRED_ADR_HEADINGS` appear verbatim in both `agents/adr-generator.md` and `agents/design-formatter.md`
- [ ] No `components` key was added to `traces_to` in `design.schema.json`

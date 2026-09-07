# QA Strategy Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third `.sdlc/` stage that turns a validated requirement set and design set into atomic `TS-` test-strategy artifacts plus a rendered `qa-strategy.md`, so STO-104 has citable gates and STO-105 has its missing graph node.

**Architecture:** A new `qa` skill drives five agents — orchestrator, two specialists split the way M1 splits FR from NFR, critic, formatter — through the same dispatch → collect → gate → synthesise → format shape both existing stages use. One new schema and one new structural validator; `validate_traceability.py` is extended rather than duplicated. The formatter is the single writer and runs the structural gate against what it just wrote.

**Tech Stack:** Python 3.12 stdlib only (schema validation via the existing optional `jsonschema` path with a stdlib fallback), pytest, Markdown+YAML agent files.

**Spec:** `docs/superpowers/specs/2026-09-06-sto-103-qa-strategy-design.md`

## Global Constraints

- **The QA formatter writes nothing outside `.sdlc/qa/`.** Spec D3/E2: no stage writes into a previous stage's directory. The requirement↔design edge is stored once on the downstream artifact and walked backwards by the validator; QA follows that exactly. A step that back-fills `TS-` IDs into requirement or design files is a defect, not a shortcut.
- **`traces_to.tests` on requirements stays empty.** Spec D4: it holds real test file paths for when code exists, not SDLC artifact IDs. Nothing in this plan populates it.
- **Stdlib only** in every script, matching every other script in this repository.
- **One artifact per file**, named `<ID>-<kebab-title>.md`, in the subdirectory its type owns.
- **Only the orchestrator allocates IDs.** Categorical, zero-padded, three digits minimum. A specialist that mints a `TS-` ID is a re-dispatch.
- **The critic gates judgment; the formatter gates structure.** The critic never runs `validate_qa.py` — nothing is on disk when it runs.
- **No content linter in this ticket.** Spec D8: `lint_qa_content.py` is the M3 analogue of STO-136/STO-208 and gets its own ticket. Do not add one, and do not add a `RULES` registry to `validate_qa.py` beyond what the structural gate needs.
- **Never write `${CLAUDE_PLUGIN_ROOT}` into a SKILL.md or agent file.** It is empty in the Bash tool's shell and resolves to `/skills/…`. Script paths use the `<skill-base>` placeholder substituted per command block, per the section STO-257 added to both existing skills.
- **Commit prefix:** `feat(sto-103):` or `docs(sto-103):`, every commit ending with the two attribution trailers used on this branch.

---

### Task 1: The QA schema and `validate_qa.py`

**Files:**
- Create: `plugin/skills/qa/schema/qa.schema.json`
- Create: `plugin/skills/qa/scripts/validate_qa.py`
- Create: `plugin/skills/qa/scripts/README.md`
- Create: `tests/qa/conftest.py`, `tests/qa/test_validate_qa.py`
- Create: `tests/qa/fixtures/valid/`, `tests/qa/fixtures/invalid/*/`

**Interfaces:**
- Produces: `PREFIX_TO_TYPE = {"TS": "test_strategy"}`, `SKIP_FILENAMES = {"qa-strategy.md", "index.yaml"}`, `REQUIRED_STRATEGY_HEADINGS`, `validate(qa_dir, schema_path)`, `discover_files(qa_dir)`, `main(argv)`. Tasks 6 and 9 invoke `main`; Task 8 registers the schema path with the exporter.

- [ ] **Step 1: Write the schema**

Create `plugin/skills/qa/schema/qa.schema.json`. Note the deliberate difference from `design.schema.json`: that file uses `allOf` branches plus `unevaluatedProperties: false` because it carries four artifact types. QA has one type, so a flat schema with `additionalProperties: false` is correct — the same shape `requirement.schema.json` uses.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://groundwork.dev/schema/qa.schema.json",
  "title": "Groundwork QA artifact",
  "description": "Schema for a single atomic test-strategy file's YAML frontmatter. One artifact per Markdown file under .sdlc/qa/strategy/<ID>-<kebab-title>.md. Flat rather than branched: the QA stage emits one type, so additionalProperties:false is sufficient and the base-plus-branch composition design.schema.json needs would be ceremony here.",
  "type": "object",
  "required": [
    "id", "type", "title", "description", "test_level", "risk_level",
    "risk_rationale", "enforcement", "traces_from", "traces_to",
    "status", "confidence", "created_at"
  ],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "description": "Categorical, zero-padded, stable ID. Optional uppercase category infix allowed (e.g. TS-PERF-004).",
      "pattern": "^TS(-[A-Z0-9]+)*-[0-9]{3,}$"
    },
    "type": { "const": "test_strategy" },
    "title": { "type": "string", "minLength": 1 },
    "description": { "type": "string", "minLength": 1 },
    "test_level": {
      "type": "string",
      "description": "The level this strategy item operates at. Drives grouping in the rendered qa-strategy.md.",
      "enum": ["unit", "integration", "contract", "e2e", "performance", "security"]
    },
    "risk_level": {
      "type": "string",
      "description": "Derived from the quality-attribute scenarios and requirements this item covers. Orders the rendered prioritisation section.",
      "enum": ["high", "medium", "low"]
    },
    "risk_rationale": {
      "type": "string",
      "description": "Why this risk level. Mandatory at every level, including low: an unexplained 'low' is the one a reader cannot check.",
      "minLength": 1
    },
    "enforcement": {
      "type": "string",
      "description": "Whether CI actually checks this. STO-104 reads it to tell a real DoD gate from one a human must remember.",
      "enum": ["ci", "manual", "none"]
    },
    "traces_from": {
      "type": "array",
      "description": "The requirement and design IDs this item covers. The QA->upstream edge is stored here and nowhere else; validate_traceability.py walks it backwards.",
      "items": { "type": "string" },
      "minItems": 1,
      "uniqueItems": true
    },
    "traces_to": {
      "type": "object",
      "description": "Downstream references to real test and source files, filled in when code exists. Empty through M3 by design.",
      "additionalProperties": false,
      "properties": {
        "tests": { "type": "array", "items": { "type": "string" }, "uniqueItems": true },
        "code": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
      }
    },
    "status": { "type": "string", "enum": ["draft", "approved", "obsolete"] },
    "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
    "created_at": { "type": "string", "format": "date" },
    "scope": { "type": "string" },
    "parent_scope": { "type": "string" }
  }
}
```

`traces_from` has `minItems: 1` on purpose: a test-strategy item that covers no requirement and no component is untraceable by construction, and the whole point of the artifact is to be a graph node.

- [ ] **Step 2: Write the fixtures**

`tests/qa/fixtures/valid/qa-strategy.md` — the project companion the validator gates. Minimal, with all five headings:

```markdown
# QA Strategy

## Test Levels and Rationale
None identified.

## Scope by Component
None identified.

## Risk-Based Prioritisation
None identified.

## Tooling
None identified.

## Coverage Targets
None identified.
```

`tests/qa/fixtures/valid/strategy/TS-001-order-cancellation-unit-boundary.md`:

```markdown
---
id: TS-001
type: test_strategy
title: Order cancellation unit boundary
description: Exercises the cancellation state machine in isolation, without the order store.
test_level: unit
risk_level: medium
risk_rationale: "Cancellation is reversible and user-visible on failure, so a defect is loud rather than silent."
enforcement: ci
traces_from: [FR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-06"
scope: project
---

# Order cancellation unit boundary

Body prose.
```

One invalid fixture per rule, each a directory under `tests/qa/fixtures/invalid/` containing the same `qa-strategy.md` plus one broken artifact:

| Fixture directory | What is wrong |
| --- | --- |
| `bad_id_pattern/` | `id: TS-1` — not zero-padded to three digits |
| `prefix_type_mismatch/` | `id: TS-001` with `type: component` |
| `duplicate_id/` | two files both `id: TS-001` |
| `bad_test_level/` | `test_level: smoke` — not in the enum |
| `bad_enforcement/` | `enforcement: maybe` — not in the enum |
| `missing_risk_rationale/` | `risk_rationale` absent |
| `empty_traces_from/` | `traces_from: []` — violates `minItems: 1` |
| `unknown_field/` | an extra `owner: alice` key |
| `missing_strategy_artifact/` | valid artifact, no `qa-strategy.md` |
| `strategy_missing_heading/` | `qa-strategy.md` without `## Coverage Targets` |

- [ ] **Step 3: Write the failing tests**

Create `tests/qa/conftest.py` (mirroring `tests/design/conftest.py`, which was repointed by STO-257 — the scripts directory is no longer an ancestor of the tests):

```python
"""Pytest configuration: make the validator module importable.

The tests live outside the plugin (STO-257) so their fixtures stop shipping to
every user, so the scripts directory is no longer an ancestor of this file and
has to be named.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "plugin", "skills", "qa", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
```

Create `tests/qa/test_validate_qa.py`:

```python
"""Tests for the QA structural validator (STO-103)."""
import os

import pytest

import validate_qa as vq

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
SCHEMA = vq.default_schema_path()

INVALID_CASES = [
    "bad_id_pattern",
    "prefix_type_mismatch",
    "duplicate_id",
    "bad_test_level",
    "bad_enforcement",
    "missing_risk_rationale",
    "empty_traces_from",
    "unknown_field",
    "missing_strategy_artifact",
    "strategy_missing_heading",
]


def test_valid_fixture_passes():
    code = vq.main([os.path.join(FIXTURES, "valid")])
    assert code == 0


@pytest.mark.parametrize("case", INVALID_CASES)
def test_invalid_fixture_fails(case):
    code = vq.main([os.path.join(FIXTURES, "invalid", case)])
    assert code != 0, f"expected non-zero exit for fixture {case}"


def test_every_invalid_fixture_is_exercised():
    # A fixture directory nobody parametrizes is a rule nobody tests. This is
    # the guard that catches a fixture added without its case.
    on_disk = sorted(
        d for d in os.listdir(os.path.join(FIXTURES, "invalid"))
        if os.path.isdir(os.path.join(FIXTURES, "invalid", d))
    )
    assert on_disk == sorted(INVALID_CASES)


def test_strategy_companion_is_skipped_as_an_artifact():
    # qa-strategy.md and index.yaml sit beside the artifacts and are not
    # themselves artifacts; discovery must not try to parse them as one.
    found = vq.discover_files(os.path.join(FIXTURES, "valid"))
    assert all(os.path.basename(p).startswith("TS-") for p in found)
    assert found, "discovery returned nothing — the fixture set is not being read"


def test_prefix_to_type_is_the_single_id_authority():
    assert vq.PREFIX_TO_TYPE == {"TS": "test_strategy"}
```

`test_every_invalid_fixture_is_exercised` and the non-empty assertion in `test_strategy_companion_is_skipped_as_an_artifact` are both there because a validator suite that silently checks nothing is the failure mode this repository has already shipped twice.

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python3 -m pytest tests/qa -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_qa'`.

- [ ] **Step 5: Implement the validator**

Create `plugin/skills/qa/scripts/validate_qa.py`, mirroring `validate_design.py`'s structure and reusing `artifact_core`:

```python
#!/usr/bin/env python3
"""Structural validator for Groundwork QA artifacts (STO-103).

Gates .sdlc/qa/ the way validate_design.py gates .sdlc/design/: schema
conformance per file, ID uniqueness and prefix/type agreement across the set,
and the presence of the project-level qa-strategy.md with its five headings.

Deliberately does NOT resolve traces_from. Those targets live in the
requirements and design sets, which this tool does not read —
validate_traceability.py owns every cross-directory edge, and duplicating that
here would create a second place for the same rule to drift.

Stdlib only, like every other script in this repository.

Usage
-----
    python3 validate_qa.py .sdlc/qa
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
_LIB_DIR = os.path.join(_PLUGIN_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import artifact_core as core  # noqa: E402
from artifact_core import ArtifactFile, parse_frontmatter  # noqa: E402

STRATEGY_ARTIFACT = "qa-strategy.md"
SKIP_FILENAMES = {STRATEGY_ARTIFACT, "index.yaml"}
SKIP_DIRNAMES: set = set()

REQUIRED_STRATEGY_HEADINGS = [
    "## Test Levels and Rationale",
    "## Scope by Component",
    "## Risk-Based Prioritisation",
    "## Tooling",
    "## Coverage Targets",
]

# One prefix, one type. The QA stage emits a single artifact type; this dict
# exists so the prefix/type agreement check has a single source, matching the
# other two validators rather than hard-coding the pair at the call site.
PREFIX_TO_TYPE = {"TS": "test_strategy"}


class QAFile(ArtifactFile):
    """One QA artifact file plus the errors found in it."""

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.frontmatter: Optional[Dict[str, Any]] = None

    @property
    def qa_id(self) -> Optional[str]:
        if isinstance(self.frontmatter, dict):
            value = self.frontmatter.get("id")
            return value if isinstance(value, str) else None
        return None


def _fallback_validate(data: Dict[str, Any]) -> List[str]:
    """Schema checks that survive without jsonschema installed.

    The primary path is the real schema; this is the same degraded mode the
    other two validators carry, and it covers required-field presence and the
    three enums rather than pretending to be complete.
    """
    errors: List[str] = []
    required = (
        "id", "type", "title", "description", "test_level", "risk_level",
        "risk_rationale", "enforcement", "traces_from", "traces_to",
        "status", "confidence", "created_at",
    )
    for field in required:
        if field not in data:
            errors.append(f"missing required field '{field}'")

    enums = {
        "test_level": {"unit", "integration", "contract", "e2e", "performance", "security"},
        "risk_level": {"high", "medium", "low"},
        "enforcement": {"ci", "manual", "none"},
        "status": {"draft", "approved", "obsolete"},
        "confidence": {"high", "medium", "low"},
    }
    for field, allowed in enums.items():
        value = data.get(field)
        if value is not None and value not in allowed:
            errors.append(f"'{field}' is '{value}', not one of {sorted(allowed)}")

    traces_from = data.get("traces_from")
    if isinstance(traces_from, list) and not traces_from:
        errors.append("traces_from is empty; a strategy item must cover something")
    return errors


def cross_file_checks(files: List[QAFile]) -> List[str]:
    """Set-level checks. Appends per-file errors and returns global errors."""
    global_errors: List[str] = []
    parsed = [f for f in files if isinstance(f.frontmatter, dict)]

    seen: Dict[str, str] = {}
    for f in parsed:
        qid = f.qa_id
        if not qid:
            continue
        if qid in seen:
            f.errors.append(
                f"duplicate id '{qid}' (also defined in {os.path.basename(seen[qid])})"
            )
        else:
            seen[qid] = f.path

    for f in parsed:
        fm = f.frontmatter
        assert fm is not None
        qid = f.qa_id
        if not qid:
            continue
        prefix = qid.split("-", 1)[0]
        expected = PREFIX_TO_TYPE.get(prefix)
        if expected is None:
            f.errors.append(
                f"id prefix '{prefix}' is not one of {sorted(PREFIX_TO_TYPE)}"
            )
        elif fm.get("type") is not None and expected != fm.get("type"):
            f.errors.append(
                f"id prefix '{prefix}' implies type '{expected}', "
                f"but type is '{fm.get('type')}'"
            )
    return global_errors


def check_strategy_artifact(qa_dir: str) -> List[str]:
    """The qa-strategy.md companion (hard gate).

    Presence plus the five headings, gated by the shared core. Content is never
    gated: a section reading 'None identified' is legal and passes, the same
    standard assumptions.md and drivers.md are held to.
    """
    return core._check_project_artifact(
        qa_dir,
        STRATEGY_ARTIFACT,
        REQUIRED_STRATEGY_HEADINGS,
        "qa strategy artifact",
        "Test Levels and Rationale / Scope by Component / Risk-Based "
        "Prioritisation / Tooling / Coverage Targets",
    )


def discover_files(qa_dir: str) -> List[str]:
    """Every QA artifact ``*.md`` under ``qa_dir`` (companions skipped)."""
    return core.discover_files(qa_dir, SKIP_FILENAMES, SKIP_DIRNAMES)


def validate(qa_dir: str, schema_path: str) -> Tuple[List[QAFile], List[str]]:
    files: List[QAFile] = []
    validator = core.make_validator(schema_path)

    for path in discover_files(qa_dir):
        qf = QAFile(path)
        data, err = parse_frontmatter(path)
        if err:
            qf.errors.append(err)
            files.append(qf)
            continue
        qf.frontmatter = data
        if validator is not None:
            qf.errors.extend(core.validate_against_schema(data, validator))
        else:
            qf.errors.extend(_fallback_validate(data))
        files.append(qf)

    global_errors = cross_file_checks(files)
    global_errors.extend(check_strategy_artifact(qa_dir))
    return files, global_errors


def default_schema_path() -> str:
    return os.path.normpath(
        os.path.join(_HERE, "..", "schema", "qa.schema.json")
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Groundwork QA artifacts."
    )
    parser.add_argument(
        "qa_dir", nargs="?", default=".sdlc/qa",
        help="Directory of QA files (default: .sdlc/qa).",
    )
    parser.add_argument("--schema", default=None, help="Override the schema path.")
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-file PASS lines; errors and the summary always print.",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.qa_dir):
        print(f"error: no such directory: {args.qa_dir}", file=sys.stderr)
        return 2

    files, global_errors = validate(args.qa_dir, args.schema or default_schema_path())
    core.print_report(files, global_errors, args.qa_dir, args.quiet, noun="qa artifact")

    has_errors = bool(global_errors) or any(not f.ok for f in files)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`core.print_report` returns `None` and takes `(files, global_errors, root_dir, quiet, noun=...)` — the exit code is computed by the caller. This mirrors `validate_design.py:676-679` exactly rather than inventing a second convention for the shared core.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest tests/qa -q`
Expected: PASS, 14 tests (1 valid + 10 parametrized invalid + 3 structural).

Then confirm the invalid fixtures fail for the *right* reason, not incidentally:

```bash
for c in bad_id_pattern empty_traces_from missing_strategy_artifact; do
  echo "--- $c"; python3 plugin/skills/qa/scripts/validate_qa.py tests/qa/fixtures/invalid/$c 2>&1 | tail -3
done
```

Expected: each message names its own defect. A fixture failing with "missing required field" when it was meant to test an enum is a broken fixture, not a passing test.

- [ ] **Step 7: Write the scripts README**

Create `plugin/skills/qa/scripts/README.md`, following `plugin/skills/design/scripts/README.md`: what the validator gates, the dependency note (`pyyaml` and `jsonschema` preferred, stdlib fallback otherwise), and `pytest tests/qa` as the test command. Do not restate the schema — reference it.

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/qa tests/qa
git commit -m "$(cat <<'EOF'
feat(sto-103): the QA artifact schema and its structural validator

One artifact type, so the schema is flat with additionalProperties:false
rather than the base-plus-branch composition design.schema.json needs for its
four types. traces_from carries minItems:1 because a strategy item covering
nothing is untraceable by construction, and being a graph node is the whole
reason the artifact is atomic rather than a section of prose.

The validator deliberately does not resolve traces_from. Those targets live
in the requirement and design sets, which this tool does not read;
validate_traceability.py owns every cross-directory edge and duplicating the
rule here would give it two places to drift.

risk_rationale is required at every level including low. An unexplained
"low" is precisely the one a reader cannot check.

The suite carries two guards against the failure this repository has already
shipped twice: a test asserting every invalid fixture directory is
parametrized, and a non-empty assertion on discovery, so a validator suite
that silently checks nothing fails instead of passing.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 2: Extend `validate_traceability.py` for the QA edge

**Files:**
- Modify: `plugin/skills/design/scripts/validate_traceability.py`
- Modify: `tests/design/test_validate_traceability.py`
- Create: `tests/design/fixtures/traceability/qa_*/`

**Interfaces:**
- Consumes: Task 1's `TS-` artifact shape and `discover_files` conventions.
- Produces: `index_qa()`, `rule_dangling_qa_trace()`, `rule_uncovered_asr()`, and a `--qa` CLI flag. Task 6's formatter invokes the CLI; Task 9 runs it end to end.

The script stays where it is despite now spanning three stages — see spec D8. Moving it to `plugin/lib/` would break both `SKILL.md` files, the design formatter, `export_reference.py`'s rule registry and the gates page for a rename.

- [ ] **Step 1: Add the two rules to the `RULES` registry**

`RULES` is the single declaration of what this tool checks and is what `export_reference.py` publishes as the rule reference. Append two entries, matching the existing key shape exactly (`fields` is `[]` by construction — a traceability finding names an artifact and a path, never a frontmatter field):

```python
    {
        "id": "dangling-qa-trace",
        "severities": [ERROR],
        "applies_to": "qa artifact",
        "fields": [],
        "summary": (
            "A QA artifact's traces_from names an ID that exists in neither "
            "the requirements set nor the design set."
        ),
    },
    {
        "id": "uncovered-asr",
        "severities": [WARN],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "An architecturally significant requirement is covered by no test "
            "strategy item. Excludes priority: wont and status: obsolete."
        ),
    },
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/design/test_validate_traceability.py`:

```python
# --- QA edge (STO-103) ------------------------------------------------------

def test_qa_trace_resolving_to_a_requirement_passes():
    root = os.path.join(FIXTURES, "qa_clean")
    code = vt.main([
        os.path.join(root, "design"),
        "--requirements", os.path.join(root, "requirements"),
        "--qa", os.path.join(root, "qa"),
    ])
    assert code == 0


def test_qa_trace_resolving_to_a_component_passes():
    # A TS may cover a design artifact as well as a requirement; both halves
    # of the union must resolve, not just the requirements half.
    root = os.path.join(FIXTURES, "qa_traces_component")
    code = vt.main([
        os.path.join(root, "design"),
        "--requirements", os.path.join(root, "requirements"),
        "--qa", os.path.join(root, "qa"),
    ])
    assert code == 0


def test_dangling_qa_trace_is_an_error():
    root = os.path.join(FIXTURES, "qa_dangling")
    code = vt.main([
        os.path.join(root, "design"),
        "--requirements", os.path.join(root, "requirements"),
        "--qa", os.path.join(root, "qa"),
    ])
    assert code != 0


def test_uncovered_asr_warns_but_does_not_fail():
    root = os.path.join(FIXTURES, "qa_uncovered")
    findings = vt.collect_findings(
        os.path.join(root, "design"),
        os.path.join(root, "requirements"),
        qa_dir=os.path.join(root, "qa"),
    )
    ids = [f.rule for f in findings]
    assert "uncovered-asr" in ids
    assert all(f.severity == vt.WARN for f in findings if f.rule == "uncovered-asr")


def test_omitting_the_qa_directory_runs_the_old_rules_only():
    # The QA stage is optional: a project that has not run it must still
    # validate cleanly, and no QA rule may fire against an absent directory.
    root = os.path.join(FIXTURES, "clean")
    findings = vt.collect_findings(
        os.path.join(root, "design"),
        os.path.join(root, "requirements"),
        qa_dir=None,
    )
    assert not [f for f in findings if f.rule in ("dangling-qa-trace", "uncovered-asr")]


```

**Do not add a "every rule has a test" guard — three already exist**, and two of them will fail against your new rules until you update them. Read `tests/design/test_validate_traceability.py:478-514` before writing anything:

| Existing test | What it does | What your change breaks |
| --- | --- | --- |
| `test_rules_registry_matches_source_literals` | Sweeps the module source for rule-id literals and asserts they equal the declared set | Passes automatically once both rules are declared *and* emitted |
| `test_rules_registry_entries_are_complete` | Asserts each entry's `applies_to` is in the closed set `{"design artifact", "requirement", "adr", "the index"}` | **Fails.** `"qa artifact"` must be added to that set |
| `test_every_declared_rule_is_exercised_by_a_fixture` | Runs every fixture directory and asserts every declared rule fires at least once | **Fails.** The `run()` helper never passes `--qa`, so no QA rule can fire from any fixture |

The second is a one-word addition. The third needs the helper at `tests/design/test_validate_traceability.py:26-33` to pass `--qa` when a fixture has one:

```python
def run(case, *extra):
    """Invoke the CLI against a fixture case; return the exit code."""
    root = os.path.join(FIXTURES, case)
    argv = [
        os.path.join(root, "design"),
        "--requirements", os.path.join(root, "requirements"),
    ]
    # QA is optional: a fixture without a qa/ directory must keep invoking the
    # CLI exactly as before, or every pre-existing case changes behaviour.
    qa_dir = os.path.join(root, "qa")
    if os.path.isdir(qa_dir):
        argv += ["--qa", qa_dir]
    return vt.main([*argv, *extra])
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m pytest tests/design/test_validate_traceability.py -q -k qa`
Expected: FAIL — `collect_findings()` got an unexpected keyword argument `qa_dir`.

- [ ] **Step 4: Build the fixtures**

Four fixture roots under `tests/design/fixtures/traceability/`, each with `requirements/`, `design/` and `qa/` subdirectories. Copy the existing `clean/` fixture's requirements and design halves as the base for all four, then:

- `qa_clean/qa/strategy/TS-001-*.md` — `traces_from: [FR-001]`.
- `qa_traces_component/qa/strategy/TS-001-*.md` — `traces_from: [FR-001, CMP-001]`.
- `qa_dangling/qa/strategy/TS-001-*.md` — `traces_from: [FR-999]`.
- `qa_uncovered/` — a requirement the design set marks significant that no TS names.

Each `qa/` directory also needs the `qa-strategy.md` companion, since Task 1's validator gates it and Task 9 runs both tools over the same tree.

- [ ] **Step 5: Implement**

Add `index_qa()` alongside `index_requirements()` and `index_design()`, following their shape. Add the two rule functions. Thread an optional `qa_dir` through `collect_findings()` — **defaulting to `None`**, so every existing caller and the four existing fixture-based tests keep working unchanged. Add the CLI flag:

```python
    parser.add_argument(
        "--qa",
        default=None,
        help="Directory of QA files (default: none — QA rules are skipped).",
    )
```

`None` rather than `.sdlc/qa` is deliberate: the design stage runs this tool at its own Step 4, long before any QA artifacts exist, and defaulting to a path would make every M2 run report a missing directory.

For `rule_uncovered_asr`, reuse the significance signal `rule_uncovered_fr` already uses rather than inventing a second definition of "architecturally significant" — read that function first and follow it.

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest tests/design -q` then `python3 -m pytest -q`
Expected: all pass, with the pre-existing traceability tests unchanged in count and outcome.

- [ ] **Step 7: Regenerate and commit**

Adding to `RULES` changes the published rule reference, so the drift gate will red until the export is re-run:

```bash
python3 site/scripts/export_reference.py
git diff --stat site/content/_generated/rules.json
python3 site/scripts/export_reference.py --check && echo "GATE CLEAN"
git add plugin/skills/design/scripts/validate_traceability.py tests/design site/content/_generated/rules.json
git commit -m "$(cat <<'EOF'
feat(sto-103): resolve the QA traceability edge

validate_traceability.py already owns every cross-directory edge, so the QA
stage extends it rather than shipping a second resolver. Two rules: a
dangling QA trace is an error, and an architecturally significant requirement
no test strategy covers is a warning — the counterpart of the existing
uncovered-fr.

--qa defaults to None rather than .sdlc/qa. The design stage runs this tool
at its own Step 4, long before any QA artifact exists, and a path default
would make every M2 run report a missing directory.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 3: The `qa-orchestrator` agent

**Files:**
- Create: `plugin/agents/qa-orchestrator.md`

**Interfaces:**
- Consumes: Task 1's `TS-` frontmatter contract verbatim — every field the specialists return must be schema-shaped as returned.
- Produces: the `generation_brief`, `draft_test_strategies`, `critique_report`, `qa_context_artifact` and `formatter_result` contracts that Tasks 4, 5 and 6 implement against, and the stage headings Task 8's exporter parses.

**The heading form is load-bearing.** `export_pipeline()` in `site/scripts/export_reference.py` parses `## Stage <n> — <label>` and treats a backticked identifier following the word "the" as a contract name, then asserts that the stage's own YAML defines that top-level key. A heading that names a contract its section does not define **raises** and reddens CI. So every stage heading below must be written exactly as given, and every named contract must appear as a top-level key in a ```yaml fence inside that stage's section.

- [ ] **Step 1: Write the agent file**

Create `plugin/agents/qa-orchestrator.md` with frontmatter carrying a single `description:` key (the exporter publishes it verbatim on the site's agent roster — write it as the sentence you want published), then these sections:

```
## Pipeline overview
## Stage 1 — Consume the qa context
## Stage 2 — Read the requirement and design sets
## Stage 3 — Allocate categorical, zero-padded IDs
## Stage 4 — Dispatch: the `generation_brief` hand-off
## Stage 5 — Collect drafts: the `draft_test_strategies` hand-off
## Stage 6 — Critique gate: the `critique_report` hand-off
## Stage 6.5 — Synthesise the `qa_context_artifact`
## Stage 7 — Format: the `formatter_result` hand-off
## Gotchas
```

Stage 2 is where the orchestrator reads both prior sets **once, on everyone's behalf** — say so, and say why: four downstream agents would otherwise each re-read two full artifact sets and reach four slightly different readings. This is M2 Stage 2's reason, and it binds harder here because there are two sets rather than one.

The five contract blocks, each inside its own stage section:

```yaml
generation_brief:
  qa_context: { ...the Stage 1 object, forwarded verbatim... }
  scripts_dir: string           # absolute; supplied by the skill, threaded to the formatter
  requirement_digest:           # what Stage 2 read, so specialists do not re-read
    - id: FR-001
      title: string
      tier: string
      priority: string
      acceptance_criteria: string
    - id: NFR-004
      title: string
      quality_attribute: string
      fit_criterion: string
  design_digest:
    - id: CMP-013
      title: string
      responsibility: string
      boundary: string
  id_block:
    functional: [TS-001, TS-002]      # allocated to the functional specialist
    quality_attribute: [TS-003, TS-004]
  assigned:
    functional: [FR-001, FR-002]
    quality_attribute: [NFR-004]
```

```yaml
draft_test_strategies:
  items:
    - id: TS-001
      type: test_strategy
      title: string
      description: string
      test_level: unit | integration | contract | e2e | performance | security
      risk_level: high | medium | low
      risk_rationale: string
      enforcement: ci | manual | none
      traces_from: [ FR-001, CMP-013 ]
      traces_to: { tests: [], code: [] }
      status: draft
      confidence: high | medium | low
      created_at: "YYYY-MM-DD"
      body_markdown: |
        # ...rendered body...
  assumptions: [ ...optional sibling statements... ]
  dependencies: [ ...optional sibling statements... ]
```

```yaml
critique_report:
  gate: pass | fail
  validator:           # structural-gate result, folded back in from the formatter (Stage 7)
    command: "python3 <scripts>/validate_qa.py .sdlc/qa"
    exit_code: 0
    summary: string
  per_item:
    - id: TS-001
      verdict: pass | revise
      findings: [ ...quality and altitude notes... ]
  coverage:
    uncovered_asrs: [ ...requirement IDs no item covers, with justification... ]
    level_gaps: [ ...test levels the set omits, with justification... ]
```

```yaml
qa_context_artifact:
  assumptions:
    - id: A-1
      statement: string
  dependencies:
    - id: D-1
      statement: string
  open_questions:
    - id: Q-1
      statement: string
      owner: string
  accepted_risks:              # the "what we are not testing" register
    - id: AR-1
      statement: string
      requirement: FR-007      # or a design ID
      rationale: string
```

```yaml
formatter_result:
  files_written: [ ".sdlc/qa/strategy/TS-001-...md", ... ]
  strategy: ".sdlc/qa/qa-strategy.md"
  index: ".sdlc/qa/index.yaml"
  review_queue_count: 0
  validator_rerun: { exit_code: 0 }
  traceability_rerun: { exit_code: 0, warnings: [] }
```

Write the `command:` value in `critique_report.validator` exactly as shown — `<scripts>/`, never a repo-relative path. STO-257 fixed both existing critics' equivalents and left a regression guard in `tests/test_plugin_package.py` that fails on `skills/<stage>/scripts/*.py` appearing in any shipped file.

Under **Gotchas**, state at minimum: the orchestrator is the only ID authority; `traces_from` must name IDs that exist in the digests it built, since it is the only agent that has read both sets; and the formatter writes nothing outside `.sdlc/qa/`.

- [ ] **Step 2: Verify the exporter can parse it**

The exporter is not wired to this file until Task 8, so check the parse directly:

```bash
python3 -c "
import sys; sys.path.insert(0, 'site/scripts')
import export_reference as er
text = open('plugin/agents/qa-orchestrator.md').read()
for s in er._parse_pipeline(text, 'plugin/agents/qa-orchestrator.md'):
    names = ', '.join(c['name'] for c in s['contracts']) or '-'
    print(f\"  {s['number']:>4}  {names}\")
"
```

Expected: eight stages, with `generation_brief`, `draft_test_strategies`, `critique_report`, `qa_context_artifact` and `formatter_result` each appearing against their own stage. A `ValueError` here means a heading names a contract its section does not define — fix the file, not the exporter.

- [ ] **Step 3: Commit**

```bash
git add plugin/agents/qa-orchestrator.md
git commit -m "$(cat <<'EOF'
feat(sto-103): the QA orchestrator and its five hand-off contracts

Stage 2 reads both prior artifact sets once on everyone's behalf. That is M2
Stage 2's reason and it binds harder here: four downstream agents would each
re-read two full sets and reach four slightly different readings of them.

The brief carries digests rather than directory paths so the specialists
never re-read, and an id_block per specialist because two producers minting
TS- IDs need a single allocator.

qa_context_artifact carries an accepted-risk register. That is the reason it
exists rather than being skipped: a risk the team decided not to test is
worth more written down than a coverage number nobody believes.

Contract commands use the <scripts>/ shape, not a repo-relative path — the
regression guard STO-257 left behind fails on the latter in any shipped file.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 4: The two test-strategy specialists

**Files:**
- Create: `plugin/agents/functional-test-specialist.md`
- Create: `plugin/agents/quality-attribute-test-specialist.md`

**Interfaces:**
- Consumes: `generation_brief` from Task 3 — specifically `requirement_digest`, `design_digest`, `id_block` and `assigned`.
- Produces: `draft_test_strategies` exactly as Task 3 declares it. Every field is written to frontmatter verbatim by Task 6's formatter, so each must be schema-shaped as returned.

Both files follow `fr-specialist.md`'s shape: `## Input`, the authoring rules, `## Body structure (rendered into body_markdown)`, and one fully-worked contract-conformant example.

- [ ] **Step 1: Write `functional-test-specialist.md`**

Its input is the FRs in `assigned.functional` plus the components in `design_digest`. Its job is deriving test-strategy items from acceptance criteria and component boundaries.

Authoring rules it must state:

- **Never restate a threshold or an acceptance criterion.** The FR carries its Gherkin; this item says *how it is exercised and at what level*, citing the FR by ID. `dod-generator.md` already states this rule for the DoD ("reference each FR by ID... do not duplicate them here") — the same reason applies, and the same words are worth reusing.
- **`test_level` is a judgment about the boundary being crossed**, not about effort. A behaviour contained in one component is `unit`; one spanning a component boundary is `integration`; one a user performs end to end is `e2e`. Say what each level means here so the choice is checkable.
- **`traces_from` names what the item covers** — at least one FR, plus any component IDs whose boundary the test crosses. It may not name an ID absent from the brief's digests.
- **Never mint an ID.** Draw from `id_block.functional` in order. An item needing an ID beyond the block is a re-dispatch, not an improvisation.
- `risk_level` for a functional item comes from consequence-of-failure: is a defect loud or silent, recoverable or not.

- [ ] **Step 2: Write `quality-attribute-test-specialist.md`**

Its input is the NFRs in `assigned.quality_attribute` plus `design_digest`. This is where the ticket's "risk-based test prioritisation derived from NFR quality attribute scenarios" actually happens.

Authoring rules it must state:

- **An NFR's six-part quality-attribute scenario is the test design.** Source, stimulus, artifact, environment, response, response measure map onto what to set up, what to do, and what to measure. Say that mapping explicitly — it is the whole reason this specialist is separate from the functional one.
- **The `fit_criterion` is the threshold and stays in the NFR.** This item states the measurement method and the environment it is measured in, never the number. A second copy of a threshold is a second thing to update.
- **`risk_level` comes from the quality attribute's own severity**, not from test difficulty: an unmet security or data-integrity scenario outranks an unmet latency one at equal probability. Say so, since the opposite instinct — rank by how hard it is to test — is the common one.
- **`enforcement` is usually the honest constraint here.** Performance and security scenarios frequently cannot run in CI; recording `manual` is correct and useful, and inflating it to `ci` produces a DoD gate that lies.
- Draw IDs from `id_block.quality_attribute` in order. Never mint one.

- [ ] **Step 3: Verify both against the schema by hand**

Take the fully-worked example from each file, save its frontmatter to a scratch artifact under a temp `.sdlc/qa/` with a minimal `qa-strategy.md`, and run Task 1's validator over it:

```bash
python3 plugin/skills/qa/scripts/validate_qa.py /tmp/qa-check
```

Expected: exit 0 for both. A worked example that does not validate is the defect that teaches every future run to produce invalid artifacts — this check is the point of the step, not a formality.

- [ ] **Step 4: Commit**

```bash
git add plugin/agents/functional-test-specialist.md plugin/agents/quality-attribute-test-specialist.md
git commit -m "$(cat <<'EOF'
feat(sto-103): the functional and quality-attribute test specialists

The same seam M1 draws between fr-specialist and nfr-specialist. Deriving a
test item from an FR's Gherkin is different work from turning an NFR's
six-part quality-attribute scenario into a fitness function, and the second
is where the ticket's risk-based prioritisation actually comes from.

Neither restates a threshold or an acceptance criterion. The FR carries its
Gherkin and the NFR carries its fit_criterion; the strategy item says how
each is exercised and at what level, citing the ID. That is the rule
dod-generator.md already states, applied one stage earlier.

The quality-attribute specialist ranks risk by the attribute's severity
rather than by test difficulty, and is told to record enforcement: manual
honestly. A performance scenario CI cannot run is a real constraint; calling
it ci produces a DoD gate that lies.

Both worked examples were validated against the schema rather than eyeballed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 5: The `qa-critic` agent

**Files:**
- Create: `plugin/agents/qa-critic.md`

**Interfaces:**
- Consumes: the merged `draft_test_strategies` from Task 3's Stage 5.
- Produces: `critique_report` exactly as Task 3 declares it.

- [ ] **Step 1: Write the agent file**

Follow `requirements-critic.md`'s shape — a two-phase review keeping comprehension separate from critique, then explicit gates.

```
## Two-phase review — keep comprehension and critique separate
## Gate A — Per-item quality
## Gate B — Coverage
## Gate C — Where the structural gate lives
## Output — `critique_report`
## Gotchas
```

**Gate A** checks each item is testable as written, at a coherent level, with a `risk_rationale` that explains rather than asserts, and — the one most likely to be skipped — that it does not restate a threshold or acceptance criterion that already lives upstream.

**Gate B** checks the set: every architecturally significant requirement is covered by at least one item or listed in `coverage.uncovered_asrs` **with a justification**, and that the level mix is deliberate. An honest "no e2e items, because this is a library with no user-facing flow" passes; silence does not.

**Gate C** must state plainly that this critic does **not** run `validate_qa.py`, and why: nothing is on disk yet, and `qa-strategy.md` — which that validator hard-gates — is not assembled until Stage 6.5, after this gate passes. Write it in that form. STO-215 and STO-207 were both this invariant stated wrongly in an agent file, and this is the third stage to state it.

Under **Gotchas**: the critic never edits an item itself — a failing item is re-dispatched to its owning specialist; and a `gate: fail` blocks Stage 7 entirely rather than degrading to a partial write.

- [ ] **Step 2: Check the Gate C wording against the two existing critics**

```bash
grep -n -A6 "Gate C — Where the structural gate lives\|Gate D — Where the structural gate lives" \
  plugin/agents/qa-critic.md plugin/agents/requirements-critic.md plugin/agents/design-critic.md
```

Expected: the QA wording makes the same two claims the other two do — the critic does not run the validator, and the reason is that the files do not exist yet. If it makes a weaker or different claim, fix it now; a third phrasing of one invariant is how the first two came to disagree.

- [ ] **Step 3: Commit**

```bash
git add plugin/agents/qa-critic.md
git commit -m "$(cat <<'EOF'
feat(sto-103): the QA critic and its two judgment gates

Gate A is per-item quality, Gate B is set coverage — every architecturally
significant requirement either covered or listed as uncovered WITH a
justification. An honest "no e2e items, this is a library" passes; silence
does not.

Gate C states where the structural gate lives, in the same form both existing
critics state it: this critic does not run validate_qa.py, because nothing is
on disk yet and qa-strategy.md is not assembled until after this gate passes.
STO-215 and STO-207 were both that invariant written wrongly, so the wording
was diffed against the other two rather than composed fresh.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 6: The `qa-formatter` and the rendered strategy document

**Files:**
- Create: `plugin/agents/qa-formatter.md`
- Create: `plugin/skills/qa/templates/qa-strategy.md`

**Interfaces:**
- Consumes: the approved item set, the `qa_context_artifact`, and `scripts_dir` from the dispatch.
- Produces: `formatter_result` as Task 3 declares it; the on-disk layout Task 9 asserts.

- [ ] **Step 1: Write the template**

Create `plugin/skills/qa/templates/qa-strategy.md` carrying exactly the five H2 headings Task 1's validator gates, in this order, each with a one-line note on what fills it:

```
## Test Levels and Rationale
## Scope by Component
## Risk-Based Prioritisation
## Tooling
## Coverage Targets
```

Add a closing `## Accepted Risks` section for the `qa_context_artifact` register. It is **not** in `REQUIRED_STRATEGY_HEADINGS` — an absent section and an empty one would then be indistinguishable, and the register is exactly the thing that should be visibly empty when nothing was accepted rather than quietly missing.

- [ ] **Step 2: Write the formatter agent**

Follow `requirements-formatter.md`'s shape:

```
## Input
## Directory layout and file names
## File format (the on-disk contract)
## Render the strategy document
## Optional machine index
## Verify, then report — the structural gate
```

Layout: `test_strategy` → `.sdlc/qa/strategy/<ID>-<kebab-title>.md`, with `<kebab-title>` derived exactly as the other two formatters derive it (lowercase the `title`, non-alphanumerics to single hyphens).

**Render the strategy document** is the section that matters. State that `qa-strategy.md` is *projected from the emitted item set*, not authored: levels grouped from `test_level`, scope grouped from the component IDs in `traces_from`, prioritisation ordered by `risk_level` with `risk_rationale` as the reason, tooling and coverage targets from the interview answers in the `qa_context_artifact`, and accepted risks from its register. Say why in one line — a hand-written summary drifts from the artifacts it summarises, which is the same reason `generate_c4.py` projects diagrams rather than drawing them.

**The structural gate** section states that the formatter, as part of its own contract, re-runs both tools against what it just wrote:

```bash
python3 <scripts>/validate_qa.py .sdlc/qa
```

```bash
python3 <scripts>/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements \
  --qa .sdlc/qa
```

`<scripts>` is the absolute directory named in the dispatch. If the dispatch did not name one, **stop and report that** rather than guessing a relative path — the clause STO-257 added to both existing formatters, for the same reason: a silent fallback turns a locating failure into a confusing `No such file` at the moment the formatter is gating a write.

Both must exit 0. State explicitly that the formatter writes **nothing outside `.sdlc/qa/`** — not into `.sdlc/requirements/`, not into `.sdlc/design/`. This is the plan's first global constraint and the formatter is the only agent with the opportunity to violate it.

- [ ] **Step 3: Verify the template passes its own gate**

```bash
mkdir -p /tmp/qa-tmpl/strategy && cp plugin/skills/qa/templates/qa-strategy.md /tmp/qa-tmpl/
cp tests/qa/fixtures/valid/strategy/TS-001-*.md /tmp/qa-tmpl/strategy/
python3 plugin/skills/qa/scripts/validate_qa.py /tmp/qa-tmpl; echo "exit=$?"
rm -rf /tmp/qa-tmpl
```

Expected: exit 0. A template that fails the validator gating it would fail every run before a single artifact was written.

- [ ] **Step 4: Commit**

```bash
git add plugin/agents/qa-formatter.md plugin/skills/qa/templates/qa-strategy.md
git commit -m "$(cat <<'EOF'
feat(sto-103): the QA formatter and the projected strategy document

qa-strategy.md is rendered from the emitted item set, not authored: levels
from test_level, scope from the component IDs in traces_from, prioritisation
ordered by risk_level. A hand-written summary drifts from the artifacts it
summarises, which is why generate_c4.py projects diagrams rather than drawing
them.

Accepted Risks is deliberately NOT in the validator's required headings. If
it were, an absent section and an empty one would be indistinguishable, and
that register is the one thing that should be visibly empty rather than
quietly missing.

The formatter writes nothing outside .sdlc/qa/. It is the only agent with the
opportunity to break the one-directory-per-stage rule, so its own file states
it rather than relying on the spec.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---
### Task 7: The QA skill and its command entry

**Files:**
- Create: `plugin/skills/qa/SKILL.md`
- Modify: `plugin/commands/groundwork.md`

**Interfaces:**
- Consumes: every agent from Tasks 3–6, and Task 1's validator.
- Produces: the coverage-area list Task 8's exporter parses, and the `qa_context` object Task 3's Stage 1 consumes.

**Two shapes here are parsed by machine and must be exact.** `export_stages()` finds a skill's coverage areas by locating an anchor line and then matching `^\d+\.\s+\*\*(.+?)\*\*\s+—\s+(.+)$` on the lines after it. The em dash is required, and so is the bold. It raises rather than returning an empty list when the anchor moves, so a mismatch reddens CI rather than publishing an empty table.

- [ ] **Step 1: Write `SKILL.md`**

Frontmatter carries `name: qa` and a `description:` written as the sentence you want published on the site.

Structure, with the scripts section **before Phase 1** — the design skill runs a script inside its Phase 1, and this one does too, so anything later is too late:

```
## When This Applies
## Locating the scripts
## Phase 1 — Locate and Read the Input
## Phase 2 — Hypothesise
## Phase 3 — QA Interview
## Phase 4 — `qa_context` Synthesis
## Phase 5 — Generate
```

**Locating the scripts** is copied in form from the section STO-257 added to both existing skills: skill invocation supplies this skill's base directory as an absolute path, the scripts are in `scripts/` beneath it, substitute per command block because shell state does not persist between tool calls, and include that absolute path in the dispatch to the orchestrator so it reaches the formatter. Add the cross-skill note this stage needs: the entry gate runs the other two stages' validators, at `<skill-base>/../requirements/scripts/validate_requirements.py` and `<skill-base>/../design/scripts/validate_design.py`.

**Phase 1** requires both prior directories. Absent either, stop and route to the stage that produces it. Then the entry gate, three commands:

```bash
python3 <skill-base>/../requirements/scripts/validate_requirements.py .sdlc/requirements
```

```bash
python3 <skill-base>/../design/scripts/validate_design.py .sdlc/design
```

```bash
python3 <skill-base>/../design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements
```

State why the third is here rather than optional: this stage is about to add a third set of edges to that graph, and starting from a broken graph means the new edges land on sand. A non-zero exit from any of the three stops the stage.

**Phase 2** hypothesises before asking — proposed test levels, the two or three highest-risk areas drawn from the NFR quality-attribute scenarios, and a guess at the existing test setup from a bounded codebase scan. One message. Say explicitly that the stack is read from the ADRs and `drivers.md` rather than re-asked, and why: the design interview already elicited it and wrote it to disk.

**Phase 3** carries the coverage-area list. Write the anchor line exactly as below, because Task 8 registers this string verbatim:

```markdown
Three coverage areas neither prior stage carries:

1. **Test tooling and existing suite** — the framework in use, and any existing suite whose conventions new tests must match
2. **CI enforcement capability** — what the pipeline can actually run and fail on, which decides every item's `enforcement` value
3. **Coverage targets and risk appetite** — the targets the team holds itself to, and the areas it has decided not to test
```

Phrase the third area's question to make declining easy — "which of these are you *not* going to test" — and say why in one line: accepted risk recorded is worth more than a coverage number nobody believes.

**Phase 5** drives the pipeline in fixed order — orchestrator, functional specialist, quality-attribute specialist, critic, formatter — and carries the sign-off gate before any write, matching both existing skills: summarise in conversation, ask, and do not write until the user confirms. Corrections re-dispatch to the owning specialist rather than editing files, because at that point there are no files.

- [ ] **Step 2: Verify the coverage-area list parses**

```bash
python3 -c "
import sys; sys.path.insert(0, 'site/scripts')
import export_reference as er
text = open('plugin/skills/qa/SKILL.md').read()
for a in er._coverage_areas(text, 'Three coverage areas neither prior stage carries:'):
    print(f\"  {a['name']}: {a['detail'][:60]}\")
"
```

Expected: three areas with non-empty details. A `ValueError` means the anchor or the list shape does not match — fix the skill file, not the exporter.

- [ ] **Step 3: Add the workflow to the command entry**

`plugin/commands/groundwork.md` lists the available workflows with a trigger line each. Add a `### qa` entry in the same shape as the existing two, naming what it needs (a validated requirement set *and* design set) and what it writes.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/qa/SKILL.md plugin/commands/groundwork.md
git commit -m "$(cat <<'EOF'
feat(sto-103): the QA skill, its interview and its entry gate

Three coverage areas, not six. The design interview already elicits runtime,
stack, deployment and team constraints, and those reach disk as ADRs and
drivers.md — so this stage reads the stack rather than re-asking it, and asks
only what nothing upstream carries: test tooling, what CI can enforce, and
coverage targets including where the team has decided not to test.

The entry gate runs three validators rather than one. The third is the
traceability check across the existing pair: this stage is about to add a
third set of edges to that graph, and starting from a broken graph means the
new edges land on sand.

Script paths use the <skill-base> placeholder substituted per block, with the
cross-skill hops named explicitly — this stage runs both sibling stages'
validators, which no previous skill had to do.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 8: The exporter tax and the architecture guide

**Files:**
- Modify: `site/scripts/export_reference.py`
- Modify: `site/scripts/tests/test_export_reference.py`
- Modify: `site/content/architecture/index.mdx`, `contracts.mdx`, `rationale.mdx`
- Modify: `.github/workflows/ci.yml`
- Regenerate: `site/content/_generated/{agents,stages,pipeline,fields}.json`

**Interfaces:**
- Consumes: Task 3's stage headings, Task 7's coverage-area anchor, Task 1's schema path.

This is the largest exporter tax any single ticket has incurred — four of the five generated files change at once. The drift gate will red until every one is regenerated.

- [ ] **Step 1: Register the third stage in three places**

In `site/scripts/export_reference.py`:

```python
SCHEMAS = {
    "design": os.path.join(
        PLUGIN_ROOT, "skills", "design", "schema", "design.schema.json"
    ),
    "requirements": os.path.join(
        PLUGIN_ROOT, "skills", "requirements", "schema", "requirement.schema.json"
    ),
    "qa": os.path.join(
        PLUGIN_ROOT, "skills", "qa", "schema", "qa.schema.json"
    ),
}
```

```python
    "qa": {
        "skill": "plugin/skills/qa/SKILL.md",
        "heading": "Three coverage areas neither prior stage carries:",
    },
```

```python
PIPELINE_SOURCES = {
    "requirements": "plugin/agents/requirements-orchestrator.md",
    "design": "plugin/agents/design-orchestrator.md",
    "qa": "plugin/agents/qa-orchestrator.md",
}
```

The `skill` and `source` values keep their `plugin/` prefix — they are published as provenance and joined onto `REPO_ROOT` at read time, per STO-257.

- [ ] **Step 2: Update the exporter's tests**

`site/scripts/tests/test_export_reference.py` pins the shape of every export. Several assertions are exact-set or exact-list and will now fail correctly. Update:

- `test_pipeline_export_covers_both_orchestrators` — the name is now wrong as well as the assertion. Rename it to `test_pipeline_export_covers_every_orchestrator` and assert `set(payload) == {"requirements", "design", "qa"}`.
- Add `test_pipeline_export_reads_the_qa_stage_order` asserting the eight QA stage numbers.
- Add `test_pipeline_export_names_every_qa_contract` asserting the five contract names in heading order.
- Any `stages.json` or `fields.json` test asserting two stages gains the third.

Run `python3 -m pytest site/ -q` and fix each failure by updating the expectation, **not** by loosening the assertion. An exact-set assertion that becomes a subset check is how a missing stage stops being noticed.

- [ ] **Step 3: Regenerate and inspect**

```bash
python3 site/scripts/export_reference.py
git diff --stat site/content/_generated/
python3 site/scripts/export_reference.py --check && echo "GATE CLEAN"
```

Expected: `agents.json`, `stages.json`, `pipeline.json` and `fields.json` all modified; `rules.json` already changed in Task 2. Confirm the agent roster is now 19 dispatched agents across three stages, and that nothing else moved.

- [ ] **Step 4: Grow the architecture guide**

The guide currently says the map stops at the design stage, deliberately. That statement is now false, so it changes here rather than in a follow-up.

In `site/content/architecture/index.mdx`:
- Add a third `<PipelineMap stage="qa" />` with its introducing paragraph naming the five agents in dispatch order.
- Add the on-disk subsection after it, in the same shape as the other two: nothing exists under `.sdlc/qa/` until the formatter runs, and at that point the artifacts, the rendered strategy document and the index appear together, followed by both validator re-runs.
- Update the opening: **nineteen agents across three stages**, not fourteen across two. Do not write "fifteen" or "fourteen" anywhere.
- Rewrite the closing "Where the map stops" section: it now stops after QA, with M4 still backlog.

In `contracts.mdx`, add `<ContractTable stage="qa" />` under its own H2.

In `rationale.mdx`, the scope note claiming the pipeline ends at design is now wrong — update it, and add a short entry on why the QA stage emits atomic artifacts rather than the single document its ticket asked for, cross-referencing rather than restating.

- [ ] **Step 5: Assert the new page content in CI**

`ContractTable` and `PipelineMap` both degrade to an error paragraph rather than throwing, so `next build` exits 0 on a page that renders nothing. Add one grep to the existing step in `.github/workflows/ci.yml`:

```yaml
          grep -q 'draft_test_strategies' out/architecture/contracts/index.html
```

- [ ] **Step 6: Build and verify**

```bash
cd site && npm run build
grep -q 'qa-orchestrator' out/architecture/index.html && echo "QA MAP RENDERED"
grep -q 'draft_test_strategies' out/architecture/contracts/index.html && echo "QA CONTRACTS RENDERED"
grep -c 'fourteen\|fifteen' out/architecture/index.html
cd ..
```

Expected: both lines print, and the stale-count grep returns 0.

- [ ] **Step 7: Commit**

```bash
git add site plugin .github/workflows/ci.yml
git commit -m "$(cat <<'EOF'
docs(sto-103): publish the third stage, and pay the exporter tax

Four of the five generated files change at once — agents, stages, pipeline
and fields — which is the largest tax any single ticket has incurred and
exactly what the invariants page said would happen.

The architecture guide's stage map said it "ends where the built pipeline
ends", which stopped being true the moment the QA stage landed. Both that
statement and the agent count are corrected here rather than in a follow-up,
because a guide that describes two stages while three exist is the defect
class STO-220 was filed about.

The exporter's exact-set assertions were updated, not loosened. A set
assertion that becomes a subset check is how a missing stage stops being
noticed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 9: End-to-end run against the tamagotchi set

**Files:**
- No source changes expected. Any change this task forces is a defect in Tasks 1–8.

**Interfaces:**
- Consumes: everything.

The two published example sets carry requirements and design but no QA stage. This task proves the stage runs against a real set rather than against fixtures — the same shape as the M2 pipeline plan's final task.

- [ ] **Step 1: Stage a scratch project**

```bash
S=/tmp/qa-e2e; rm -rf $S; mkdir -p $S/.sdlc
cp -r docs/requirements/examples/tamagotchi/requirements $S/.sdlc/requirements
cp -r docs/requirements/examples/tamagotchi/design $S/.sdlc/design
cd $S && ls .sdlc/*
```

- [ ] **Step 2: Confirm the entry gate passes on a real set**

```bash
cd /tmp/qa-e2e
P=/home/storm/wsl-projects/groundwork/plugin
python3 $P/skills/requirements/scripts/validate_requirements.py .sdlc/requirements | tail -2
python3 $P/skills/design/scripts/validate_design.py .sdlc/design | tail -2
python3 $P/skills/design/scripts/validate_traceability.py .sdlc/design --requirements .sdlc/requirements | tail -3
```

Expected: all three exit 0. If the traceability run reports warnings, note them — they are pre-existing and not this ticket's to fix, but they belong in the report.

- [ ] **Step 3: Run the stage**

Drive the QA skill against `/tmp/qa-e2e` as a real user would: the interview (answer as the tamagotchi project would — a Rust/Tauri desktop app, per `ADR-003`), the sign-off, then the write. Do not hand-author artifacts; the point is to exercise the agents.

- [ ] **Step 4: Verify what landed**

```bash
cd /tmp/qa-e2e
P=/home/storm/wsl-projects/groundwork/plugin
find .sdlc/qa -type f | sort
python3 $P/skills/qa/scripts/validate_qa.py .sdlc/qa | tail -3
python3 $P/skills/design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements --qa .sdlc/qa | tail -5
```

Expected: `.sdlc/qa/strategy/TS-*.md`, `qa-strategy.md` and `index.yaml`; both tools exit 0.

- [ ] **Step 5: Assert the constraint that is easiest to break**

```bash
cd /tmp/qa-e2e
git -C /home/storm/wsl-projects/groundwork stash list >/dev/null 2>&1
diff -r .sdlc/requirements /home/storm/wsl-projects/groundwork/docs/requirements/examples/tamagotchi/requirements && echo "REQUIREMENTS UNTOUCHED"
diff -r .sdlc/design /home/storm/wsl-projects/groundwork/docs/requirements/examples/tamagotchi/design && echo "DESIGN UNTOUCHED"
```

Expected: both print. This is the plan's first global constraint, checked against a real run rather than trusted — if the formatter back-filled anything upstream, this is where it shows.

- [ ] **Step 6: Report, and decide whether the example set gains a QA stage**

Write up what the run produced: how many items, the level and risk distribution, whether the critic's coverage gate flagged uncovered ASRs, and any agent instruction that proved ambiguous in practice.

Committing the generated set into `docs/requirements/examples/tamagotchi/` is **out of scope** per the spec — that is the M3 analogue of STO-219 and belongs in its own ticket. File it as one, with this run's output as the evidence that the stage works.

- [ ] **Step 7: Final verification and commit**

```bash
cd /home/storm/wsl-projects/groundwork
python3 -m pytest -q
python3 site/scripts/export_reference.py --check && echo "reference clean"
python3 site/scripts/export_examples.py --check && echo "examples clean"
cd site && npm run build && cd ..
git status --short
```

Expected: all pass, both gates clean, build exits 0, and `git status` clean — this task should have produced no source changes. If it did, they are fixes to earlier tasks and belong in commits that say so.

---

## Self-Review

**Spec coverage.** D1 → Tasks 1, 6 (artifacts plus the rendered companion). D2 → Task 1's schema (one type, risk as fields). D3 → the first global constraint, enforced at Task 9 Step 5. D4 → the second global constraint; nothing populates `traces_to.tests`. D5 → Task 7's Phase 2 and Phase 3. D6 → Tasks 3, 4, 5, 6. D7 → Task 7 Phase 1 (entry gate), Task 5 (critic gate), Task 6 (structural gate). D8 → Task 1 (validator only) and Task 2 (traceability extended, not duplicated); the "no content linter" constraint is stated globally. D9 → Task 8 Step 4. Every evidence item E1–E5 is either encoded as a constraint or stated in a commit message. No spec section is unimplemented.

**Two machine-parsed shapes called out explicitly**, because getting either subtly wrong fails at CI rather than at authoring time: the orchestrator's stage headings (Task 3, verified at its Step 2) and the skill's coverage-area anchor and list format (Task 7, verified at its Step 2). Both verification steps run the real exporter functions against the new file rather than eyeballing the format.

**Type consistency.** `PREFIX_TO_TYPE`, `SKIP_FILENAMES`, `REQUIRED_STRATEGY_HEADINGS`, `discover_files`, `validate`, `default_schema_path` and `main` are named identically in Task 1's implementation, Task 1's tests, Task 6's formatter commands and Task 9's verification. The five contract names in Task 3 match their consumers in Tasks 4, 5 and 6 exactly. `qa_dir` is the keyword everywhere it appears in Task 2.

**One deliberate deviation from the M2 precedent.** The M2 pipeline plan gated `drivers.md` in Task 1 before building any agent; this plan builds the whole schema and validator first, including the `qa-strategy.md` companion gate, so every later task has a working oracle to check its worked examples against. Tasks 4 Step 3 and 6 Step 3 both use it that way, which is what makes those steps real checks rather than assertions of intent.

**Three interface details the existing suite would only have surfaced at execution time**, all now written into Task 2 rather than discovered: `test_rules_registry_entries_are_complete` asserts `applies_to` against a closed set that does not contain `"qa artifact"`; `test_every_declared_rule_is_exercised_by_a_fixture` runs every fixture and would never fire a QA rule because the `run()` helper does not pass `--qa`; and `core.print_report` returns `None` with a five-argument signature, so the caller computes the exit code. The first draft of this plan got all three wrong.

**Known risk this plan does not resolve.** The dispatched-agent roster goes 14 → 19 while STO-247's cost analysis is unstarted, so nobody has measured what the current 14 cost. The spec names it; the controller's ruling was to treat that measurement as a prerequisite to merging rather than to planning. If it turns out the pipeline is already expensive, the finding lands before this branch merges rather than after.

# M2 Cross-Artifact Traceability Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the requirement↔design traces that both existing validators deliberately leave unchecked, so a design set can no longer be structurally valid while citing requirements that do not exist.

**Architecture:** A new `validate_traceability.py` sits beside `validate_design.py` and imports both stage validators for discovery and parsing. It builds two ID indexes — requirements and design artifacts — then runs five rules over them. Three rules are errors (exit 1), two are warnings (exit 0 unless `--strict`). The `design-formatter` runs it immediately after `validate_design.py` exits 0.

**Tech Stack:** Python 3 standard library plus the optional `pyyaml`/`jsonschema` the shared core already handles; pytest for the suite; Markdown agent-definition files.

**Spec:** `docs/superpowers/specs/2026-08-07-m2-cross-artifact-traceability-design.md`

## Global Constraints

- **This tool never schema-validates.** It reads frontmatter and resolves IDs. Required fields, enums, and ID shape belong to `validate_design.py` and `validate_requirements.py`. Do not duplicate their checks. (Spec "Problem".)
- **This tool never writes.** It is a validator, not a mutator. Nothing in it opens a file for writing. (Spec D3.)
- **The requirement→design edge lives once, on `design.traces_from`.** Never require `traces_to.design` to be populated; never flag asymmetry. (Spec D3.)
- **Three severities do not exist.** Only `error` and `warn`. (Spec D2.)
- **Errors exit 1; warnings exit 0 unless `--strict`.** Exit 2 is reserved for a missing directory. (Spec "Tool shape".)
- **Coverage means FRs addressed by components.** Interfaces and ADRs are not coverage. `priority: wont` and `status: obsolete` are excluded from the sweep entirely. (Spec D4.)
- **ADR drivers accept any requirement type**, not NFR only — `agents/adr-generator.md` emits `[NFR-002, CON-001]`. (Spec D5.)
- **No schema changes.** Neither `design.schema.json` nor `requirement.schema.json` is touched. (Spec "Out of scope".)
- **`diagrams/` stays in `SKIP_DIRNAMES`.** STO-101 owns it. (Spec D1.)
- Do not add dependency-cycle or orphan-interface detection — STO-208 owns both. (Spec "Out of scope".)

---

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `skills/design/scripts/validate_traceability.py` | The five rules, indexes, CLI, report | Create |
| `skills/design/scripts/tests/test_validate_traceability.py` | Suite for the above | Create |
| `skills/design/scripts/tests/fixtures/traceability/<case>/` | Paired `design/` + `requirements/` trees | Create — 9 cases |
| `agents/design-formatter.md` | Writes artifacts, runs the gates | Modify — second command in "Validator re-run" |
| `skills/design/SKILL.md` | Stage documentation | Modify — Step 4 both commands; correct the scope list |
| `agents/constraint-specialist.md` | Constraint/BR tracing rules | Modify — both tracing bullets (spec D6) |
| `skills/design/scripts/README.md` | Design-stage script docs | Create |
| `docs/requirements/examples/tamagotchi/requirements/**` | Worked example data | Modify — 3 constraints + 4 bounded requirements |
| `docs/requirements/examples/gdpr/requirements/**` | Worked example data | Modify — 1 constraint |

Six tasks. Task 1 delivers a runnable CLI with one rule. Tasks 2–4 add one rule each, with fixtures. Task 5 fixes the upstream defect and its data. Task 6 wires the pipeline and writes the docs.

---

### Task 1: The validator skeleton and the `dangling-trace` rule

**Files:**
- Create: `skills/design/scripts/validate_traceability.py`
- Create: `skills/design/scripts/tests/test_validate_traceability.py`
- Create: `skills/design/scripts/tests/fixtures/traceability/clean/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/dangling_trace/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/unparseable/{design,requirements}/**`

**Interfaces:**
- Consumes: `validate_design.discover_files(design_dir)`, `validate_requirements.discover_files(reqs_dir)`, `artifact_core.parse_frontmatter(path) -> (dict|None, str|None)` — all already shipped.
- Produces: `Finding(rule, severity, artifact_id, path, message)` dataclass; `Requirement` and `DesignArtifact` dataclasses; `index_requirements(reqs_dir) -> (Dict[str, Requirement], List[str])`; `index_design(design_dir) -> (Dict[str, DesignArtifact], List[str])`; `collect_findings(design_dir, reqs_dir) -> (List[Finding], int, int, List[str])`; `main(argv=None) -> int`. Tasks 2–4 add `rule_*` functions and register them inside `collect_findings`.

**Note on fixtures:** requirement and design fixture files carry **only the fields this tool reads**, because it never schema-validates (Global Constraints). A fixture that is not schema-complete is correct here and must not be "fixed" by adding required fields.

- [ ] **Step 1: Create the `clean` fixture**

`skills/design/scripts/tests/fixtures/traceability/clean/requirements/functional/FR-001-place-an-order.md`:

```markdown
---
id: FR-001
type: functional
priority: must
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Place an order

Trimmed to the fields validate_traceability.py reads; it never schema-validates.
```

`skills/design/scripts/tests/fixtures/traceability/clean/requirements/non-functional/NFR-001-order-api-latency.md`:

```markdown
---
id: NFR-001
type: non_functional
priority: should
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Order API latency
```

`skills/design/scripts/tests/fixtures/traceability/clean/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
traces_from:
  - FR-001
traces_to: {}
---

# order-service
```

`skills/design/scripts/tests/fixtures/traceability/clean/design/interfaces/IF-001-order-api.md`:

```markdown
---
id: IF-001
type: interface
provider: CMP-001
traces_from:
  - NFR-001
traces_to: {}
---

# order-api
```

- [ ] **Step 2: Create the `dangling_trace` fixture**

The requirements side is identical to `clean`, so copy it rather than retyping:

```bash
cd skills/design/scripts/tests/fixtures/traceability
mkdir -p dangling_trace/design/components
cp -r clean/requirements dangling_trace/requirements
cd -
```

`skills/design/scripts/tests/fixtures/traceability/dangling_trace/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
traces_from:
  - FR-001
  - FR-404
traces_to: {}
---

# order-service

FR-404 does not exist in the paired requirements set.
```

- [ ] **Step 3: Create the `unparseable` fixture**

`.../unparseable/requirements/non-functional/NFR-001-order-api-latency.md`:

```markdown
---
id: NFR-001
type: non_functional
priority: should
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Order API latency
```

`.../unparseable/design/components/CMP-001-broken.md`:

```markdown
# Broken component

This file has no YAML frontmatter at all, so it cannot be indexed.
```

This case carries **no functional requirement on purpose.** The coverage rule
added in Task 2 would otherwise fire here, and this test exists to pin the
skip-note behaviour across every later task, not to exercise coverage.

- [ ] **Step 4: Write the failing tests**

`skills/design/scripts/tests/test_validate_traceability.py`:

```python
"""Tests for the Groundwork cross-artifact traceability validator (STO-102).

Run from anywhere::

    pytest skills/design/scripts/tests

Each fixture case is a paired `design/` + `requirements/` tree, so every test
runs the real CLI end to end. Fixture artifacts carry only the fields this
tool reads — it never schema-validates, so they are deliberately not
schema-complete.
"""
import json
import os

import validate_traceability as vt

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "traceability")


def run(case, *extra):
    """Invoke the CLI against a fixture case; return the exit code."""
    root = os.path.join(FIXTURES, case)
    return vt.main(
        [os.path.join(root, "design"),
         "--requirements", os.path.join(root, "requirements"),
         *extra]
    )


# ---------------------------------------------------------------------------
# Clean set
# ---------------------------------------------------------------------------
def test_clean_set_has_no_findings(capsys):
    code = run("clean")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out


def test_clean_set_reports_both_index_sizes(capsys):
    run("clean")
    out = capsys.readouterr().out
    assert "Indexed 2 design artifact(s), 2 requirement(s)." in out


# ---------------------------------------------------------------------------
# dangling-trace (error)
# ---------------------------------------------------------------------------
def test_dangling_trace_is_an_error(capsys):
    code = run("dangling_trace")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "ERROR" in out
    assert "dangling-trace" in out
    assert "FR-404" in out


def test_dangling_trace_does_not_flag_the_resolving_id(capsys):
    """CMP-001 cites FR-001 and FR-404. Only FR-404 is a finding."""
    run("dangling_trace")
    out = capsys.readouterr().out
    assert "Summary: 1 error(s), 0 warning(s)." in out


# ---------------------------------------------------------------------------
# Usage / environment
# ---------------------------------------------------------------------------
def test_missing_design_dir_exits_2(capsys):
    code = vt.main([os.path.join(FIXTURES, "nope"),
                    "--requirements", os.path.join(FIXTURES, "clean", "requirements")])
    assert code == 2
    assert "design directory not found" in capsys.readouterr().err


def test_missing_requirements_dir_exits_2(capsys):
    code = vt.main([os.path.join(FIXTURES, "clean", "design"),
                    "--requirements", os.path.join(FIXTURES, "nope")])
    assert code == 2
    assert "requirements directory not found" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# --json / --quiet
# ---------------------------------------------------------------------------
def test_json_shape(capsys):
    run("dangling_trace", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"] == {"error": 1, "warn": 0}
    finding = payload["findings"][0]
    assert set(finding) == {"rule", "severity", "artifact_id", "path", "message"}
    assert finding["rule"] == "dangling-trace"
    assert finding["severity"] == "error"
    assert finding["artifact_id"] == "CMP-001"


def test_quiet_suppresses_the_listing_but_keeps_the_summary(capsys):
    run("dangling_trace", "--quiet")
    out = capsys.readouterr().out
    assert "dangling-trace" not in out
    assert "Summary: 1 error(s), 0 warning(s)." in out


# ---------------------------------------------------------------------------
# Unparseable frontmatter
# ---------------------------------------------------------------------------
def test_unparseable_file_is_skipped_with_a_header_note(capsys):
    """An unindexable component has an invisible traces_from, which would
    manufacture false coverage warnings. The run continues, but says so."""
    code = run("unparseable")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "1 file(s) skipped (unparseable frontmatter)" in out
    assert "Indexed 0 design artifact(s), 1 requirement(s)." in out
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -v`
Expected: collection error — `ModuleNotFoundError: No module named 'validate_traceability'`

- [ ] **Step 6: Write the implementation**

`skills/design/scripts/validate_traceability.py`:

```python
#!/usr/bin/env python3
"""Cross-artifact traceability validator for Groundwork (STO-102).

Groundwork's two structural validators each see one stage directory by design,
and each explicitly declines to resolve the edge that crosses between them:
``validate_design.py`` checks that ``traces_from`` is requirement-SHAPED but
not that the requirement exists, and ``validate_requirements.py`` excludes
every ``traces_to`` sub-list from its dangling-reference sweep. This tool is
the one that reads both directories at once and resolves that edge.

It runs five rules::

    dangling-trace          error  design traces_from resolves to a requirement
    uncovered-fr            warn   every FR is cited by some component
    adr-driver-unresolved   error  IDs under '## Decision Drivers' resolve
    adr-driver-untraced     warn   a body driver absent from frontmatter
    dangling-reverse-trace  error  requirement traces_to.design resolves

It never schema-validates and never writes. Required fields, enums and ID
shape belong to the two structural validators; this tool only resolves IDs.

Usage
-----
    python3 validate_traceability.py [DESIGN_DIR] [--requirements DIR]
                                     [--json] [--strict] [--quiet]

Exit codes
----------
    0  no errors (warnings may be present, unless --strict)
    1  one or more errors, or any warning under --strict
    2  usage / environment error (either directory missing)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

# This script spans two stages, so both stage script dirs and the shared lib/
# go on the path. Resolved relative to this file, so cwd does not matter —
# the same handling both existing validators use.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
for _p in (
    _HERE,
    os.path.join(_REPO_ROOT, "lib"),
    os.path.join(_REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_design as vd  # noqa: E402
import validate_requirements as vr  # noqa: E402
from artifact_core import parse_frontmatter  # noqa: E402


# Severities. There are exactly two; see spec D2.
ERROR = "error"
WARN = "warn"
_SEVERITY_ORDER = {ERROR: 0, WARN: 1}


@dataclass
class Finding:
    rule: str
    severity: str
    artifact_id: str
    path: str
    message: str


@dataclass
class Requirement:
    req_id: str
    type: str
    priority: str
    status: str
    path: str
    traces_to_design: List[str] = field(default_factory=list)


@dataclass
class DesignArtifact:
    design_id: str
    type: str
    path: str
    traces_from: List[str] = field(default_factory=list)


def _str_list(value: Any) -> List[str]:
    """Coerce a frontmatter list field to a list of strings, tolerating None."""
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str)]


def _text(value: Any) -> str:
    return str(value) if isinstance(value, str) else ""


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------
def index_requirements(reqs_dir: str) -> Tuple[Dict[str, Requirement], List[str]]:
    """Index every requirement by ID. Returns (index, unparseable_paths)."""
    index: Dict[str, Requirement] = {}
    skipped: List[str] = []
    for path in vr.discover_files(reqs_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        traces_to = data.get("traces_to")
        design = _str_list(traces_to.get("design")) if isinstance(traces_to, dict) else []
        index[data["id"]] = Requirement(
            req_id=data["id"],
            type=_text(data.get("type")),
            priority=_text(data.get("priority")),
            status=_text(data.get("status")),
            path=os.path.relpath(path, reqs_dir),
            traces_to_design=design,
        )
    return index, skipped


def index_design(design_dir: str) -> Tuple[Dict[str, DesignArtifact], List[str]]:
    """Index every design artifact by ID. Returns (index, unparseable_paths)."""
    index: Dict[str, DesignArtifact] = {}
    skipped: List[str] = []
    for path in vd.discover_files(design_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        index[data["id"]] = DesignArtifact(
            design_id=data["id"],
            type=_text(data.get("type")),
            path=os.path.relpath(path, design_dir),
            traces_from=_str_list(data.get("traces_from")),
        )
    return index, skipped


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def rule_dangling_trace(
    design_index: Dict[str, DesignArtifact], req_index: Dict[str, Requirement]
) -> List[Finding]:
    """Every design artifact's traces_from must resolve to a requirement.

    validate_design.py has already checked these are requirement-SHAPED. An ID
    that failed that check simply will not resolve here and is reported as
    dangling — the shape error is reported separately, by the tool that owns it.
    """
    findings: List[Finding] = []
    for art in sorted(design_index.values(), key=lambda a: a.design_id):
        for target in art.traces_from:
            if target not in req_index:
                findings.append(Finding(
                    rule="dangling-trace",
                    severity=ERROR,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=f"traces_from -> '{target}' is not a known requirement id",
                ))
    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def collect_findings(
    design_dir: str, reqs_dir: str
) -> Tuple[List[Finding], int, int, List[str]]:
    """Run every rule. Returns (findings, design_count, req_count, skipped)."""
    req_index, req_skipped = index_requirements(reqs_dir)
    design_index, design_skipped = index_design(design_dir)

    findings: List[Finding] = []
    findings.extend(rule_dangling_trace(design_index, req_index))

    return (
        findings,
        len(design_index),
        len(req_index),
        req_skipped + design_skipped,
    )


def print_report(
    findings: List[Finding],
    design_dir: str,
    reqs_dir: str,
    design_count: int,
    req_count: int,
    skipped: List[str],
    quiet: bool,
) -> None:
    print(f"Validating traceability: {design_dir} <-> {reqs_dir}")
    print(f"Indexed {design_count} design artifact(s), {req_count} requirement(s).")
    if skipped:
        print(
            f"WARNING: {len(skipped)} file(s) skipped (unparseable frontmatter); "
            f"results may be incomplete. Run the structural validators for details."
        )
    print("-" * 60)
    if not quiet:
        for f in sorted(
            findings, key=lambda f: (_SEVERITY_ORDER[f.severity], f.rule, f.artifact_id)
        ):
            print(f"  {f.severity.upper():<6} {f.rule:<22} {f.artifact_id:<10} {f.message}")
        print("-" * 60)
    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)
    print(f"Summary: {errors} error(s), {warns} warning(s).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate traceability between Groundwork design and requirement artifacts."
    )
    parser.add_argument(
        "design_dir",
        nargs="?",
        default=".sdlc/design",
        help="Directory of design files (default: .sdlc/design).",
    )
    parser.add_argument(
        "--requirements",
        default=".sdlc/requirements",
        help="Directory of requirement files (default: .sdlc/requirements).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero on warnings as well as errors."
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Print only the summary line."
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.design_dir):
        print(f"ERROR: design directory not found: {args.design_dir}", file=sys.stderr)
        return 2
    if not os.path.isdir(args.requirements):
        print(f"ERROR: requirements directory not found: {args.requirements}", file=sys.stderr)
        return 2

    findings, design_count, req_count, skipped = collect_findings(
        args.design_dir, args.requirements
    )
    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)

    if args.json:
        print(json.dumps(
            {
                "findings": [asdict(f) for f in findings],
                "counts": {"error": errors, "warn": warns},
            },
            indent=2,
        ))
    else:
        print_report(
            findings, args.design_dir, args.requirements,
            design_count, req_count, skipped, args.quiet,
        )

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -v`
Expected: 9 passed

- [ ] **Step 8: Verify the existing suites still pass**

Run: `pytest skills/design/scripts/tests skills/requirements/scripts/tests`
Expected: all pass — this task added a module, it changed nothing shared.

- [ ] **Step 9: Commit**

```bash
git add skills/design/scripts/validate_traceability.py \
        skills/design/scripts/tests/test_validate_traceability.py \
        skills/design/scripts/tests/fixtures/traceability
git commit -m "feat(sto-102): traceability validator skeleton and dangling-trace rule

The one edge neither structural validator resolves: validate_design.py checks
traces_from is requirement-shaped and says resolution is this tool's job;
validate_requirements.py excludes traces_to from its sweep for the same reason.

Two severities live here rather than in lib/artifact_core.py, which the M1
validator also depends on — a warn/error model does not belong in shared code
two stages rely on."
```

---

### Task 2: The `uncovered-fr` coverage rule

**Files:**
- Modify: `skills/design/scripts/validate_traceability.py` (add `rule_uncovered_fr`, register it)
- Modify: `skills/design/scripts/tests/test_validate_traceability.py` (append)
- Create: `skills/design/scripts/tests/fixtures/traceability/uncovered_fr/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/excluded_fr/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/fr_covered_by_interface_only/{design,requirements}/**`

**Interfaces:**
- Consumes: `Finding`, `Requirement`, `DesignArtifact`, `WARN`, and `collect_findings` from Task 1.
- Produces: `rule_uncovered_fr(design_index, req_index) -> List[Finding]`; module constants `COVERAGE_EXCLUDED_PRIORITIES` and `COVERAGE_EXCLUDED_STATUSES`.

- [ ] **Step 1: Create the `uncovered_fr` fixture**

`.../uncovered_fr/requirements/functional/FR-001-place-an-order.md`:

```markdown
---
id: FR-001
type: functional
priority: must
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Place an order
```

`.../uncovered_fr/requirements/functional/FR-002-cancel-an-order.md`:

```markdown
---
id: FR-002
type: functional
priority: should
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Cancel an order

No component traces to this one.
```

`.../uncovered_fr/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
traces_from:
  - FR-001
traces_to: {}
---

# order-service
```

- [ ] **Step 2: Create the `excluded_fr` fixture**

FR-001 and the component are byte-identical to the `uncovered_fr` case just
created, so copy them:

```bash
cd skills/design/scripts/tests/fixtures/traceability
mkdir -p excluded_fr/requirements/functional excluded_fr/design/components
cp uncovered_fr/requirements/functional/FR-001-place-an-order.md excluded_fr/requirements/functional/
cp uncovered_fr/design/components/CMP-001-order-service.md excluded_fr/design/components/
cd -
```

FR-001 is covered by CMP-001, so it is never a finding here. The two files
below are the ones under test.

`.../excluded_fr/requirements/functional/FR-002-bulk-import.md`:

```markdown
---
id: FR-002
type: functional
priority: wont
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Bulk import

priority: wont — excluded from the coverage sweep entirely (spec D4).
```

`.../excluded_fr/requirements/functional/FR-003-legacy-export.md`:

```markdown
---
id: FR-003
type: functional
priority: must
status: obsolete
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Legacy export

status: obsolete — excluded from the coverage sweep entirely (spec D4).
```

- [ ] **Step 3: Create the `fr_covered_by_interface_only` fixture**

FR-001 is again identical to the `uncovered_fr` case:

```bash
cd skills/design/scripts/tests/fixtures/traceability
mkdir -p fr_covered_by_interface_only/requirements/functional \
         fr_covered_by_interface_only/design/components \
         fr_covered_by_interface_only/design/interfaces
cp uncovered_fr/requirements/functional/FR-001-place-an-order.md \
   fr_covered_by_interface_only/requirements/functional/
cd -
```

`.../fr_covered_by_interface_only/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
traces_from: []
traces_to: {}
---

# order-service

Traces to nothing. FR-001 is cited only by the interface below.
```

`.../fr_covered_by_interface_only/design/interfaces/IF-001-order-api.md`:

```markdown
---
id: IF-001
type: interface
provider: CMP-001
traces_from:
  - FR-001
traces_to: {}
---

# order-api
```

- [ ] **Step 4: Write the failing tests**

Append to `skills/design/scripts/tests/test_validate_traceability.py`:

```python
# ---------------------------------------------------------------------------
# uncovered-fr (warn)
# ---------------------------------------------------------------------------
def test_uncovered_fr_is_a_warning_and_does_not_block(capsys):
    code = run("uncovered_fr")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "WARN" in out
    assert "uncovered-fr" in out
    assert "FR-002" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


def test_uncovered_fr_blocks_under_strict(capsys):
    code = run("uncovered_fr", "--strict")
    assert code == 1, capsys.readouterr().out


def test_covered_fr_is_not_flagged(capsys):
    run("uncovered_fr")
    out = capsys.readouterr().out
    assert "FR-001" not in out


def test_wont_and_obsolete_frs_are_excluded_entirely(capsys):
    """Not warned about, not counted. A `wont` requirement having no component
    is the correct outcome, and warning about it trains the reader to ignore
    the rule (spec D4)."""
    code = run("excluded_fr")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out
    assert "FR-002" not in out
    assert "FR-003" not in out


def test_interface_only_coverage_still_warns(capsys):
    """An FR is behaviour, and behaviour is owned by a component. An interface
    citing it is not coverage (spec D4)."""
    code = run("fr_covered_by_interface_only")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "uncovered-fr" in out
    assert "FR-001" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -k "uncovered or excluded or interface_only" -v`
Expected: FAIL — the `uncovered-fr` findings are never produced, so the summary lines read `0 warning(s)` and the assertions on `WARN`/`uncovered-fr` fail.

- [ ] **Step 6: Add the rule**

Insert into `validate_traceability.py`, immediately after `rule_dangling_trace`:

```python
# A `wont` requirement having no component is the correct outcome, and an
# obsolete one is not part of the system. Both are excluded from the sweep
# entirely rather than warned about — warning trains the reader to ignore the
# rule (spec D4).
COVERAGE_EXCLUDED_PRIORITIES = {"wont"}
COVERAGE_EXCLUDED_STATUSES = {"obsolete"}


def rule_uncovered_fr(
    design_index: Dict[str, DesignArtifact], req_index: Dict[str, Requirement]
) -> List[Finding]:
    """Every functional requirement must be cited by at least one component.

    Components only. An FR is behaviour and behaviour is owned by a component,
    so an interface or ADR citing it is not coverage (spec D4).
    """
    covered: set = set()
    for art in design_index.values():
        if art.type == "component":
            covered.update(art.traces_from)

    findings: List[Finding] = []
    for req in sorted(req_index.values(), key=lambda r: r.req_id):
        if req.type != "functional":
            continue
        if req.priority in COVERAGE_EXCLUDED_PRIORITIES:
            continue
        if req.status in COVERAGE_EXCLUDED_STATUSES:
            continue
        if req.req_id in covered:
            continue
        findings.append(Finding(
            rule="uncovered-fr",
            severity=WARN,
            artifact_id=req.req_id,
            path=req.path,
            message="no component traces_from this functional requirement",
        ))
    return findings
```

Register it in `collect_findings`, after the `rule_dangling_trace` line:

```python
    findings.extend(rule_uncovered_fr(design_index, req_index))
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -v`
Expected: 14 passed

- [ ] **Step 8: Commit**

```bash
git add skills/design/scripts/validate_traceability.py \
        skills/design/scripts/tests/test_validate_traceability.py \
        skills/design/scripts/tests/fixtures/traceability
git commit -m "feat(sto-102): uncovered-fr coverage rule

Warns rather than blocks: an FR with no component may be deliberately
deferred or outside this increment, unlike a citation of a requirement that
does not exist. --strict promotes it for CI.

Coverage is components only. An interface citing an FR is not coverage, and
wont/obsolete requirements leave the sweep entirely rather than warning --
warning about a wont requirement teaches the reader to ignore the rule."
```

---

### Task 3: The ADR decision-driver rules

**Files:**
- Modify: `skills/design/scripts/validate_traceability.py` (add the scanner, `extract_decision_drivers`, `rule_adr_drivers`)
- Modify: `skills/design/scripts/tests/test_validate_traceability.py` (append)
- Create: `skills/design/scripts/tests/fixtures/traceability/adr_driver_unresolved/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/adr_driver_untraced/{design,requirements}/**`

**Interfaces:**
- Consumes: `Finding`, `DesignArtifact`, `Requirement`, `ERROR`, `WARN`, `collect_findings` from Task 1.
- Produces: `REQUIREMENT_ID_SCAN_RE`; `DECISION_DRIVERS_HEADING`; `extract_decision_drivers(path) -> List[str]`; `rule_adr_drivers(design_index, req_index, design_dir) -> List[Finding]`.

- [ ] **Step 1: Create the `adr_driver_unresolved` fixture**

`.../adr_driver_unresolved/requirements/non-functional/NFR-001-order-api-latency.md`:

```markdown
---
id: NFR-001
type: non_functional
priority: should
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Order API latency
```

`.../adr_driver_unresolved/design/adr/ADR-001-single-writer-db.md`:

```markdown
---
id: ADR-001
type: adr
traces_from:
  - NFR-001
traces_to: {}
decision_status: accepted
---

# ADR-001: Single-writer database

## Context and Problem Statement

Whether the order store admits concurrent writers.

## Decision Drivers

- NFR-001
- NFR-404

## Considered Options

- Single writer
- Multi-writer with optimistic locking

## Decision Outcome

Single writer.

### Consequences

- Good: no conflict-resolution path to get wrong.
```

- [ ] **Step 2: Create the `adr_driver_untraced` fixture**

NFR-001 is identical to the one just created:

```bash
cd skills/design/scripts/tests/fixtures/traceability
mkdir -p adr_driver_untraced/requirements/non-functional \
         adr_driver_untraced/requirements/constraints \
         adr_driver_untraced/design/adr
cp adr_driver_unresolved/requirements/non-functional/NFR-001-order-api-latency.md \
   adr_driver_untraced/requirements/non-functional/
cd -
```

`.../adr_driver_untraced/requirements/constraints/CON-001-oracle-19c.md`:

```markdown
---
id: CON-001
type: constraint
priority: must
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Oracle 19c
```

`.../adr_driver_untraced/design/adr/ADR-001-single-writer-db.md`:

```markdown
---
id: ADR-001
type: adr
traces_from:
  - NFR-001
traces_to: {}
decision_status: accepted
---

# ADR-001: Single-writer database

## Context and Problem Statement

Whether the order store admits concurrent writers.

## Decision Drivers

- NFR-001
- CON-001

## Considered Options

- Single writer
- Multi-writer with optimistic locking

## Decision Outcome

Single writer. CON-001 resolves, but is absent from frontmatter traces_from.

### Consequences

- Good: no conflict-resolution path to get wrong.
```

- [ ] **Step 3: Write the failing tests**

Append to `skills/design/scripts/tests/test_validate_traceability.py`:

```python
# ---------------------------------------------------------------------------
# adr-driver-unresolved (error) / adr-driver-untraced (warn)
# ---------------------------------------------------------------------------
def test_unresolved_adr_driver_is_an_error(capsys):
    code = run("adr_driver_unresolved")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "adr-driver-unresolved" in out
    assert "NFR-404" in out
    assert "Summary: 1 error(s), 0 warning(s)." in out


def test_nfr_prefix_is_not_scanned_as_an_fr(capsys):
    """'NFR-001' must not also match as 'FR-001'. If it did, the clean driver
    would produce a phantom finding for a requirement nobody named."""
    run("adr_driver_unresolved")
    out = capsys.readouterr().out
    assert "FR-001'" not in out


def test_untraced_adr_driver_is_a_warning(capsys):
    code = run("adr_driver_untraced")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "adr-driver-untraced" in out
    assert "CON-001" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


def test_adr_driver_check_accepts_any_requirement_type(capsys):
    """CON-001 resolves, so it is a warning about drift -- not an error about
    being the wrong type. agents/adr-generator.md emits [NFR-002, CON-001]
    (spec D5)."""
    run("adr_driver_untraced")
    out = capsys.readouterr().out
    assert "adr-driver-unresolved" not in out


def test_decision_drivers_section_stops_at_the_next_h2():
    """IDs under later headings are not decision drivers."""
    path = os.path.join(
        FIXTURES, "adr_driver_untraced", "design", "adr", "ADR-001-single-writer-db.md"
    )
    assert vt.extract_decision_drivers(path) == ["NFR-001", "CON-001"]
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -k "adr or nfr_prefix or decision_drivers" -v`
Expected: FAIL — `AttributeError: module 'validate_traceability' has no attribute 'extract_decision_drivers'` on the last test, and the rest fail on missing findings.

- [ ] **Step 5: Add the scanner and the rule**

Insert into `validate_traceability.py`, immediately after `rule_uncovered_fr`:

```python
# vd.REQUIREMENT_ID_RE is anchored with ^...$ and cannot scan a line, so the
# body scan needs its own pattern. The (?<!\w) guard is what stops 'NFR-001'
# also matching as 'FR-001'. 'ADR' is deliberately absent from the
# alternation: an ADR cross-reference in the prose is not a requirement.
REQUIREMENT_ID_SCAN_RE = re.compile(
    r"(?<!\w)(?:FR|NFR|CON|BR|UC)(?:-[A-Z0-9]+)*-[0-9]{3,}(?!\w)"
)

DECISION_DRIVERS_HEADING = "## Decision Drivers"


def extract_decision_drivers(path: str) -> List[str]:
    """Return the requirement IDs named under '## Decision Drivers', in order.

    The section runs from the heading line to the next '## ' line or EOF. An
    H3 such as '### Consequences' does not terminate it, because '^## ' needs
    a space as the third character.

    Returns [] when the heading is absent: validate_design.py gates the five
    MADR headings, so a missing one is that tool's finding, not ours.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return []

    match = re.search(
        rf"^{re.escape(DECISION_DRIVERS_HEADING)}\s*$", text, re.MULTILINE
    )
    if not match:
        return []
    rest = text[match.end():]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    section = rest[: nxt.start()] if nxt else rest

    ordered: List[str] = []
    seen: set = set()
    for m in REQUIREMENT_ID_SCAN_RE.finditer(section):
        if m.group(0) not in seen:
            seen.add(m.group(0))
            ordered.append(m.group(0))
    return ordered


def rule_adr_drivers(
    design_index: Dict[str, DesignArtifact],
    req_index: Dict[str, Requirement],
    design_dir: str,
) -> List[Finding]:
    """Check the IDs an ADR names under '## Decision Drivers'.

    agents/adr-generator.md derives body.decision_drivers as 'the traces_from
    IDs', so the two are the same list written twice. An unresolvable ID is an
    error; a resolving one absent from frontmatter means they have drifted.

    Deliberately one-directional: an ID in frontmatter but missing from the
    body is a rendering gap the formatter owns, not a traceability defect
    (spec D5).
    """
    findings: List[Finding] = []
    for art in sorted(design_index.values(), key=lambda a: a.design_id):
        if art.type != "adr":
            continue
        traced = set(art.traces_from)
        for driver in extract_decision_drivers(os.path.join(design_dir, art.path)):
            if driver not in req_index:
                findings.append(Finding(
                    rule="adr-driver-unresolved",
                    severity=ERROR,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=(
                        f"'{DECISION_DRIVERS_HEADING}' names '{driver}', "
                        f"which is not a known requirement id"
                    ),
                ))
            elif driver not in traced:
                findings.append(Finding(
                    rule="adr-driver-untraced",
                    severity=WARN,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=(
                        f"'{DECISION_DRIVERS_HEADING}' names '{driver}', "
                        f"which is absent from frontmatter traces_from"
                    ),
                ))
    return findings
```

Register it in `collect_findings`, after the `rule_uncovered_fr` line:

```python
    findings.extend(rule_adr_drivers(design_index, req_index, design_dir))
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -v`
Expected: 19 passed

- [ ] **Step 7: Commit**

```bash
git add skills/design/scripts/validate_traceability.py \
        skills/design/scripts/tests/test_validate_traceability.py \
        skills/design/scripts/tests/fixtures/traceability
git commit -m "feat(sto-102): ADR decision-driver rules

agents/adr-generator.md derives body.decision_drivers as 'the traces_from
IDs', so the two are one list written twice: an unresolvable body ID is an
error, a resolving one absent from frontmatter is drift.

The check accepts any requirement type rather than NFR only -- the ticket
says NFR, but the generator's own worked example emits [NFR-002, CON-001],
so an NFR-only rule would flag a conforming ADR.

The scan pattern is a non-anchored variant because the shipped
REQUIREMENT_ID_RE is ^...$ and cannot scan. Its (?<!\\w) guard is what stops
NFR-001 also matching as FR-001."
```

---

### Task 4: The `dangling-reverse-trace` rule

**Files:**
- Modify: `skills/design/scripts/validate_traceability.py` (add `rule_dangling_reverse_trace`, register it)
- Modify: `skills/design/scripts/tests/test_validate_traceability.py` (append)
- Create: `skills/design/scripts/tests/fixtures/traceability/dangling_reverse_trace/{design,requirements}/**`
- Create: `skills/design/scripts/tests/fixtures/traceability/empty_reverse_trace/{design,requirements}/**`

**Interfaces:**
- Consumes: `Finding`, `Requirement`, `DesignArtifact`, `ERROR`, `collect_findings` from Task 1.
- Produces: `rule_dangling_reverse_trace(req_index, design_index) -> List[Finding]`.

- [ ] **Step 1: Create the `dangling_reverse_trace` fixture**

`.../dangling_reverse_trace/requirements/functional/FR-001-place-an-order.md`:

```markdown
---
id: FR-001
type: functional
priority: must
status: approved
traces_from: []
traces_to:
  design: [CMP-999]
  tests: []
  code: []
---

# Place an order

CMP-999 does not exist in the paired design set.
```

`.../dangling_reverse_trace/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
traces_from:
  - FR-001
traces_to: {}
---

# order-service
```

- [ ] **Step 2: Create the `empty_reverse_trace` fixture**

`.../empty_reverse_trace/requirements/functional/FR-001-place-an-order.md`:

```markdown
---
id: FR-001
type: functional
priority: must
status: approved
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# Place an order

traces_to.design is empty while CMP-001 traces to this requirement. That
asymmetry is correct: the edge lives once, on design.traces_from (spec D3).
```

The component is identical to the `dangling_reverse_trace` case:

```bash
cd skills/design/scripts/tests/fixtures/traceability
mkdir -p empty_reverse_trace/design/components
cp dangling_reverse_trace/design/components/CMP-001-order-service.md \
   empty_reverse_trace/design/components/
cd -
```

- [ ] **Step 3: Write the failing tests**

Append to `skills/design/scripts/tests/test_validate_traceability.py`:

```python
# ---------------------------------------------------------------------------
# dangling-reverse-trace (error)
# ---------------------------------------------------------------------------
def test_dangling_reverse_trace_is_an_error(capsys):
    code = run("dangling_reverse_trace")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "dangling-reverse-trace" in out
    assert "CMP-999" in out
    assert "FR-001" in out


def test_empty_reverse_trace_and_asymmetry_are_never_findings(capsys):
    """The edge lives once, on design.traces_from. A requirement whose
    traces_to.design omits a component that traces to it is correct, not
    incomplete (spec D3)."""
    code = run("empty_reverse_trace")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -k reverse_trace -v`
Expected: `test_dangling_reverse_trace_is_an_error` FAILS (exit 0, no such finding). `test_empty_reverse_trace_and_asymmetry_are_never_findings` already passes — it pins behaviour that must not regress when the rule lands.

- [ ] **Step 5: Add the rule**

Insert into `validate_traceability.py`, immediately after `rule_adr_drivers`:

```python
def rule_dangling_reverse_trace(
    req_index: Dict[str, Requirement], design_index: Dict[str, DesignArtifact]
) -> List[Finding]:
    """A non-empty traces_to.design must resolve to a real design artifact.

    Presence is never required and asymmetry is never a finding: the
    requirement->design edge lives once, on design.traces_from (spec D3). This
    rule only says that if the slot is populated, its contents must be real.
    """
    findings: List[Finding] = []
    for req in sorted(req_index.values(), key=lambda r: r.req_id):
        for target in req.traces_to_design:
            if target not in design_index:
                findings.append(Finding(
                    rule="dangling-reverse-trace",
                    severity=ERROR,
                    artifact_id=req.req_id,
                    path=req.path,
                    message=(
                        f"traces_to.design -> '{target}' is not a known "
                        f"design artifact id"
                    ),
                ))
    return findings
```

Register it in `collect_findings`, after the `rule_adr_drivers` line:

```python
    findings.extend(rule_dangling_reverse_trace(req_index, design_index))
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest skills/design/scripts/tests/test_validate_traceability.py -v`
Expected: 21 passed

- [ ] **Step 7: Confirm the rule fires on the real defect**

Run:

```bash
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements
```

Expected: exit 1, with three `dangling-reverse-trace` errors — `CON-001 -> NFR-002`, `CON-002 -> NFR-005` and `-> FR-001`, `CON-003 -> NFR-006`. Zero `dangling-trace`, zero `uncovered-fr`. Task 5 fixes the data.

- [ ] **Step 8: Commit**

```bash
git add skills/design/scripts/validate_traceability.py \
        skills/design/scripts/tests/test_validate_traceability.py \
        skills/design/scripts/tests/fixtures/traceability
git commit -m "feat(sto-102): dangling-reverse-trace rule

Presence is never required and asymmetry is never a finding -- the edge lives
once, on design.traces_from, the same rule the schemas already state for
CMP.depends_on -> IF.provider. This rule only says a populated slot must hold
real design IDs.

It fires on the shipped tamagotchi example, which is the defect Task 5 fixes."
```

---

### Task 5: Fix the `traces_to.design` misuse at its source

**Files:**
- Modify: `agents/constraint-specialist.md:41-53` (the "Tracing — mandatory" bullets)
- Modify: `docs/requirements/examples/tamagotchi/requirements/constraints/CON-001-lightweight-always-on-runtime-footprint-boundary.md:16`
- Modify: `docs/requirements/examples/tamagotchi/requirements/constraints/CON-002-fully-offline-local-only-operation.md:16`
- Modify: `docs/requirements/examples/tamagotchi/requirements/constraints/CON-003-cross-platform-delivery-target.md:16`
- Modify: `docs/requirements/examples/tamagotchi/requirements/non-functional/NFR-002-idle-cpu-and-memory-footprint-budget.md:14`
- Modify: `docs/requirements/examples/tamagotchi/requirements/non-functional/NFR-005-local-only-data-handling.md:14`
- Modify: `docs/requirements/examples/tamagotchi/requirements/non-functional/NFR-006-cross-platform-desktop-support.md:14`
- Modify: `docs/requirements/examples/tamagotchi/requirements/functional/FR-001-persist-pet-state-to-local-storage.md:15`
- Modify: `docs/requirements/examples/gdpr/requirements/constraints/CON-001-statutory-retention-of-financial-records-overrides-erasure.md:16`

**Interfaces:**
- Consumes: the `dangling-reverse-trace` rule from Task 4 — this task's verification is that rule going quiet.
- Produces: no code. A corrected agent instruction and corrected example data.

**Why this is in scope:** shipping the validator without this lands a gate that fails the repo's own worked examples on day one — the same shape STO-215 fixed. See spec D6.

- [ ] **Step 1: Correct `agents/constraint-specialist.md`**

Replace the two bullets under "## Tracing — mandatory" (currently lines 42–53, beginning "Every constraint and business rule MUST record") with:

```markdown
Every constraint and business rule MUST be linked to the requirements it bounds
or that implement it, drawn from the `global_id_index`. **The link is recorded
on the other requirement, not on this one** — the edge lives once, in one
direction, the same rule the design schema states for `CMP.depends_on ->
IF.provider`.

- A **constraint** bounds the requirements whose design space it limits. Each
  bounded requirement lists the `CON-` ID in its own `traces_from`. Do not list
  those requirement IDs under this constraint's `traces_to.design` —
  `traces_to.design` holds design-artifact IDs (`CMP-`/`IF-`/`ADR-`) and
  nothing else, and the cross-artifact validator resolves it as such. Use this
  constraint's `traces_from` only for a higher-tier source (a business need or
  regulation reference expressed as an ID).
- A **business rule** is implemented by one or more FRs. Each implementing FR
  lists the `BR-` ID in its own `traces_from`. Do not list those FR IDs under
  this rule's `traces_to.tests` or `traces_to.code` — those slots hold test and
  source-file references, not requirement IDs.

Leave `traces_to.design`/`tests`/`code` empty. No downstream artifact exists
when the requirements stage runs; the design stage populates the
requirement->design edge on the design artifact's `traces_from`, never here.
```

- [ ] **Step 2: Clear the four `traces_to.design` slots**

In each of these four files, change the `  design: [...]` line to `  design: []`:

| File | From | To |
| --- | --- | --- |
| `tamagotchi/.../constraints/CON-001-lightweight-always-on-runtime-footprint-boundary.md:16` | `  design: [NFR-002]` | `  design: []` |
| `tamagotchi/.../constraints/CON-002-fully-offline-local-only-operation.md:16` | `  design: [NFR-005, FR-001]` | `  design: []` |
| `tamagotchi/.../constraints/CON-003-cross-platform-delivery-target.md:16` | `  design: [NFR-006]` | `  design: []` |
| `gdpr/.../constraints/CON-001-statutory-retention-of-financial-records-overrides-erasure.md:16` | `  design: [FR-002]` | `  design: []` |

- [ ] **Step 3: Move the edge onto the four bounded tamagotchi requirements**

| File | From | To |
| --- | --- | --- |
| `tamagotchi/.../non-functional/NFR-002-idle-cpu-and-memory-footprint-budget.md:14` | `traces_from: []` | `traces_from: [CON-001]` |
| `tamagotchi/.../non-functional/NFR-005-local-only-data-handling.md:14` | `traces_from: [FR-001]` | `traces_from: [FR-001, CON-002]` |
| `tamagotchi/.../non-functional/NFR-006-cross-platform-desktop-support.md:14` | `traces_from: []` | `traces_from: [CON-003]` |
| `tamagotchi/.../functional/FR-001-persist-pet-state-to-local-storage.md:15` | `traces_from: []` | `traces_from: [CON-002]` |

**gdpr needs no `traces_from` change.** `FR-002` already carries
`traces_from: [BR-001, BR-002, CON-001]` — its `traces_to.design: [FR-002]`
was a redundant second copy of an edge already recorded correctly, which is
itself evidence that the constraint bullet was the outlier.

- [ ] **Step 4: Verify no information was lost**

Run:

```bash
grep -rn "CON-00" docs/requirements/examples/tamagotchi/requirements --include=*.md | grep traces_from
```

Expected: four lines showing `CON-001` on NFR-002, `CON-002` on NFR-005 and FR-001, `CON-003` on NFR-006. Every edge deleted in Step 2 now exists in Step 3's direction.

- [ ] **Step 5: Verify both requirement sets still validate**

Run:

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
```

Expected: both exit 0. `validate_requirements.py` resolves `traces_from` against known requirement IDs, so the moved `CON-` references must resolve — this is the check that the move is legal, not just tidy.

- [ ] **Step 6: Verify the traceability validator is now clean on tamagotchi**

Run:

```bash
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements
```

Expected: exit 0, `Summary: 0 error(s), 0 warning(s).` This is the real-world calibration check — a 22-requirement, 23-artifact set nobody wrote to satisfy these rules.

- [ ] **Step 7: Confirm the tamagotchi consolidated view has not gone stale**

Run:

```bash
grep -n "traces_to\|design: \[" docs/requirements/examples/tamagotchi/CONSOLIDATED.md | head
```

If `CONSOLIDATED.md` reproduces any of the four edited `traces_to.design` values, update those lines to match. If it does not mention them, no change is needed — record which in the commit body.

- [ ] **Step 8: Commit**

```bash
git add agents/constraint-specialist.md docs/requirements/examples
git commit -m "fix(sto-102): record the constraint edge on the bounded requirement

agents/constraint-specialist.md told the specialist to list bounded
requirement IDs under a constraint's traces_to.design. That slot holds
design-artifact IDs, and the instruction contradicted the bullet directly
below it, which routes the analogous business-rule edge onto the requirement's
own traces_from.

Four requirement files across both worked examples carry the resulting bad
data. The bounded requirements recorded the constraint nowhere else, so the
edge moves rather than being deleted -- except in gdpr, where FR-002 already
carried CON-001 in traces_from and traces_to.design was simply a redundant
second copy. That redundancy is itself the evidence for which bullet was
right.

The sibling business-rule bullet had the same misuse of traces_to.tests/code
and is corrected in the same pass, though no rule here catches it."
```

---

### Task 6: Wire the formatter, correct the docs

**Files:**
- Modify: `agents/design-formatter.md` (the "Validator re-run" section, ~line 365, and the `formatter_result` shape)
- Modify: `skills/design/SKILL.md:298-317` (Step 4) and `:342-351` ("What This Stage Does Not Produce")
- Create: `skills/design/scripts/README.md`

**Interfaces:**
- Consumes: the CLI from Tasks 1–4 — `validate_traceability.py [DESIGN_DIR] --requirements DIR`, exit 0/1/2.
- Produces: no code. Documentation and agent instructions only, verified by grep and by the commands they contain actually running.

- [ ] **Step 1: Read the current formatter section**

Run: `sed -n '355,400p' agents/design-formatter.md`

Note the exact heading text and the `formatter_result` field names — the next step extends them rather than replacing them.

- [ ] **Step 2: Add the second command to `agents/design-formatter.md`**

After the existing `validate_design.py` command block in the "Validator re-run" section, add:

```markdown
Then, and **only if `validate_design.py` exited 0**, run the cross-artifact
validator:

```bash
python3 skills/design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements
```

Order is not a preference. Traceability findings computed over a structurally
invalid set are noise: a component whose frontmatter failed to parse has an
invisible `traces_from`, which manufactures false `uncovered-fr` warnings for
requirements that are in fact covered. Do not run it on a non-zero structural
exit — report the structural failure and stop.

A non-zero exit here is a **hard failure**, exactly like the structural gate:
report it and do not treat the write as done. Warnings (`uncovered-fr`,
`adr-driver-untraced`) do not exit non-zero; carry them forward so the skill
can surface them.

Report both outcomes in `formatter_result`:

```yaml
formatter_result:
  validation:
    structural:
      command: "python3 skills/design/scripts/validate_design.py .sdlc/design"
      exit_code: 0
    traceability:
      command: "python3 skills/design/scripts/validate_traceability.py .sdlc/design --requirements .sdlc/requirements"
      exit_code: 0
      warnings:
        - "uncovered-fr FR-007 — no component traces_from this functional requirement"
```

`warnings` is a list of the warning-severity lines the run reported, or empty.
An empty list means the sweep was clean, not that it was skipped.
```

- [ ] **Step 3: Add the second command to `skills/design/SKILL.md` Step 4**

After the existing `validate_design.py` block in "Step 4 — Write, then validate (hard gate)", add:

```markdown
The formatter then runs the cross-artifact validator, which resolves the
requirement↔design edge neither structural validator checks:

```bash
python3 skills/design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements
```

It must also exit 0. Three of its rules are errors — a design artifact citing
a requirement that does not exist, an ADR naming an unresolvable decision
driver, and a requirement whose `traces_to.design` names a design artifact
that does not exist. Two are warnings that do not block: an FR no component
addresses, and an ADR body driver missing from its own frontmatter.

Those warnings arrive **after** the write, not at the Step 3 sign-off. That
ordering is inherent — nothing is on disk before the formatter runs, and
computing coverage over drafts is the unreachable-gate mistake STO-215 fixed.
Surface them to the user with the post-write report; they are advisory, and
acting on them is the user's call.
```

- [ ] **Step 4: Correct the scope list in `skills/design/SKILL.md`**

Replace the closing paragraph of "## What This Stage Does Not Produce" (currently "This stage also does not resolve cross-artifact traceability (`traces_from` resolution, dependency-cycle detection, orphan-interface detection) — that is STO-102's and STO-208's territory, not this skill's.") with:

```markdown
Cross-artifact traceability *is* resolved, but not by this skill's judgment —
`validate_traceability.py` runs at Step 4 as a second hard gate and owns
`traces_from` resolution, FR coverage, ADR decision-driver resolution, and
`traces_to.design` resolution.

What is still not produced here: dependency-cycle detection, orphan-interface
detection, and prose-quality sweeps over design artifacts. Those are STO-208's
content linter, per `agents/design-critic.md`'s *Scope boundaries*.
```

This settles a contradiction: the previous wording assigned cycle and
orphan detection to STO-102, while `agents/design-critic.md:255-259` assigned
both to STO-208. The critic's version wins — those are graph and prose sweeps
over design-internal edges, not cross-artifact resolution.

- [ ] **Step 5: Create `skills/design/scripts/README.md`**

```markdown
# Design schema & validators

Structural and cross-artifact validation for Groundwork's atomic design
artifacts.

## Layout
- `../schema/design.schema.json` — JSON Schema (draft 2020-12) for a single
  design artifact's YAML frontmatter (the binding schema contract).
- `validate_design.py` — structural validator: schema, ID/type agreement, the
  `CMP.depends_on -> IF.provider` graph, project artifacts, MADR headings.
- `validate_traceability.py` — cross-artifact validator: resolves the
  requirement↔design edge that neither stage validator checks.
- `tests/` — pytest suite plus `valid/`, `invalid/` and `traceability/`
  fixtures.

## Dependencies

`validate_design.py` needs `pyyaml` and `jsonschema` for full validation and
degrades to a stdlib fallback without them; see
`skills/requirements/scripts/README.md` for the install and fallback details,
which are shared. `validate_traceability.py` does no schema validation, so it
only needs frontmatter parsing — the same fallback applies.

## Structural validator — `validate_design.py`

```bash
python3 validate_design.py .sdlc/design
python3 validate_design.py --quiet .sdlc/design
```

Exit codes: `0` valid, `1` one or more violations, `2` missing directory or
schema.

## Cross-artifact validator — `validate_traceability.py`

Reads both stage directories at once and resolves the edge between them.
`validate_design.py` checks `traces_from` is requirement-*shaped* but not that
the requirement exists; `validate_requirements.py` excludes `traces_to` from
its dangling-reference sweep. This tool is what closes that gap.

```bash
python3 validate_traceability.py .sdlc/design                      # human report
python3 validate_traceability.py --json .sdlc/design               # machine-readable
python3 validate_traceability.py --strict .sdlc/design             # warnings block too
python3 validate_traceability.py .sdlc/design --requirements other/reqs
```

| Rule | Severity | Check |
| --- | --- | --- |
| `dangling-trace` | error | A design artifact's `traces_from` ID resolves to a requirement |
| `uncovered-fr` | warn | Every FR (excluding `priority: wont`, `status: obsolete`) is cited by ≥1 component |
| `adr-driver-unresolved` | error | Requirement IDs under an ADR's `## Decision Drivers` resolve |
| `adr-driver-untraced` | warn | A resolving body driver absent from that ADR's `traces_from` |
| `dangling-reverse-trace` | error | A non-empty `traces_to.design` resolves to a real design ID |

Exit codes: `0` no errors, `1` any error (or any warning under `--strict`),
`2` either directory missing.

It never schema-validates and never writes. Required fields, enums and ID
shape belong to the two structural validators.

## Running the tests

```bash
pytest skills/design/scripts/tests
```
```

- [ ] **Step 6: Verify the documented commands actually run**

Run each command block exactly as written in the new README, from the repo
root, against the tamagotchi example:

```bash
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements --json
```

Expected: valid JSON with `"counts": {"error": 0, "warn": 0}`. A documented
command that does not run is the defect this step exists to catch.

- [ ] **Step 7: Verify no file still assigns cycle/orphan detection to STO-102**

Run:

```bash
grep -rn "STO-102" skills agents docs/superpowers/specs --include=*.md
```

Expected: every remaining mention describes `traces_from` resolution, FR
coverage, ADR drivers, or `traces_to.design` — none mentions dependency
cycles or orphan interfaces.

- [ ] **Step 8: Run the full suite**

Run: `pytest skills/design/scripts/tests skills/requirements/scripts/tests`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add agents/design-formatter.md skills/design/SKILL.md skills/design/scripts/README.md
git commit -m "feat(sto-102): run the traceability gate at the formatter

The formatter is the only stage that has written the files, which is the same
reasoning STO-215 used to move the structural gate there. The new command runs
only after validate_design.py exits 0 -- traceability findings over a
structurally invalid set are noise, because an unparseable component has an
invisible traces_from and manufactures false uncovered-fr warnings.

Warnings arrive after the write rather than at the Step 3 sign-off. That is
inherent: nothing is on disk before the formatter runs, and computing coverage
over drafts is the unreachable-gate mistake. The skill documents the ordering
rather than hiding it.

Also settles a contradiction the two files disagreed on: SKILL.md assigned
dependency-cycle and orphan-interface detection to STO-102 while
design-critic.md assigned both to STO-208. The critic's version wins -- those
are graph sweeps over design-internal edges, not cross-artifact resolution."
```

---

## Verification

After Task 6, the whole ticket is verifiable in four commands:

```bash
# 1. The suite
pytest skills/design/scripts/tests skills/requirements/scripts/tests

# 2. The real-world calibration check
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements

# 3. Both requirement sets still validate after the Task 5 data move
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements

# 4. The design set still validates structurally
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
```

All four must exit 0.

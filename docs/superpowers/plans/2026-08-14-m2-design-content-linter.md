# M2 Design Content-Quality Linter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the M2 design stage the advisory content-quality tier M1 has had since STO-136, as an eight-rule linter that never blocks the pipeline.

**Architecture:** Extract the machinery both linters share into `lib/lint_core.py` (mirroring what STO-197 did for the validators with `lib/artifact_core.py`), migrate the M1 linter onto it, then build `skills/design/scripts/lint_design_content.py` as a thin registry of design-specific rules. The linter reuses `validate_design.discover_files`/`parse_frontmatter`, so it sees exactly the artifacts the structural validator sees and skips exactly what it skips.

**Tech Stack:** Python 3, stdlib only (`argparse`, `dataclasses`, `re`, `json`). `pyyaml` and `jsonschema` are optional and inherited transitively from `artifact_core`; the linter must run without them. pytest for tests.

**Spec:** `docs/superpowers/specs/2026-08-14-m2-design-content-linter-design.md`

## Global Constraints

- **Advisory, always.** Every entry point exits 0 regardless of findings. `--strict` returns 1 only when an `error`-severity finding exists; no rule in this plan emits `error`, so `--strict` is a no-op today and that is intentional (spec D2).
- **Never rewrite a file.** The linter reads and reports. Findings route back through the critique loop to the owning specialist.
- **Exit codes:** `0` always (advisory), `1` only under `--strict` with an error-severity finding, `2` on a missing directory.
- **Severity vocabulary:** `"error" | "warn" | "info"` — unchanged from M1.
- **Four CLI flags, matching M1 exactly:** positional directory (default `.sdlc/design`), `--json`, `--strict`, `--quiet`.
- **The extraction in Task 1 is behavior-preserving.** The M1 suite is the regression net. Any M1 test needing an edit beyond the `artifact_id` rename means the extraction was wrong.
- **The stdlib fallback path must not crash.** The linter runs without `pyyaml`; findings may lose fidelity, the tool must not raise.
- **Baseline:** the suite is green at 168 tests on `main` at `d17cd1d`. This plan does not pin a final count — the previous ticket's plan had to be corrected twice for exactly that (see `d57c634`). The gate is "the whole suite passes", not a number.

---

### Task 1: Extract `lib/lint_core.py` and migrate the M1 linter onto it

This task is atomic by necessity. The shared module and the `artifact_id` rename cannot land separately: creating `lint_core.Finding` with `artifact_id` while `lint_requirements_content.py` still defines its own `Finding` with `req_id` leaves two competing records, and renaming the field without the extraction is a change with no purpose.

**Files:**
- Create: `lib/lint_core.py`
- Modify: `skills/requirements/scripts/lint_requirements_content.py` (whole-file rewrite of the scaffolding; rule bodies keep their logic)
- Modify: `skills/requirements/scripts/tests/test_lint_content.py:151`
- Modify: `skills/requirements/scripts/README.md:55-75`
- Test: `skills/requirements/scripts/tests/test_lint_content.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `lint_core.Finding(rule, severity, artifact_id, field, excerpt, message, suggested_rewrite_hint)`; `lint_core.flatten_text(value) -> str`; `lint_core.sentences(text) -> List[str]`; `lint_core.VAGUE_TERMS: Set[str]`; `lint_core.ACTION_VERBS: Set[str]`; `lint_core.print_report(findings, root_dir, quiet, noun) -> None`; `lint_core.run_cli(argv, *, default_dir, noun, lint_dir, description) -> int`. Tasks 2-5 consume all of these.

- [ ] **Step 1: Write the failing test — the JSON key is `artifact_id`**

Edit `skills/requirements/scripts/tests/test_lint_content.py`, replacing the assertion on line 151:

```python
def test_json_output_is_parseable(capsys):
    code = lc.main([os.path.join(CONTENT, "vague"), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert isinstance(data, list) and data
    # STO-208: the finding record is shared with the design linter, so the id
    # field is stage-agnostic. `validate_traceability.Finding` already spells it
    # this way; this is the M1 linter converging on it, not a new convention.
    assert {"rule", "severity", "artifact_id", "field", "message"} <= set(data[0])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest skills/requirements/scripts/tests/test_lint_content.py::test_json_output_is_parseable -v`

Expected: FAIL. The emitted JSON still carries `req_id`, so the subset assertion is false.

This is the only M1 test that names the field. Every other M1 test reaches through `lc.check_*` and asserts on `.rule`, `.severity`, or `.message`, which are unchanged — that is why the rest of the suite is a clean regression net for the extraction.

- [ ] **Step 3: Create `lib/lint_core.py`**

```python
#!/usr/bin/env python3
"""Stage-agnostic core for Groundwork content-quality linters.

Groundwork runs an advisory content linter per stage: M1's
``lint_requirements_content.py`` (STO-136) and M2's ``lint_design_content.py``
(STO-208). They share the *finding record, prose helpers, report format and CLI*;
only the rules differ.

This module is that shared surface. It is the linter-tier analogue of
``artifact_core.py``, which STO-197 extracted from the validators for the same
reason, and it deliberately holds no requirement- or design-specific knowledge:
the vocabularies here are the ones both stages use, stage-only word lists stay
in the per-stage module, and the CLI is parameterized by the caller's
``lint_dir``.

The extraction is behavior-preserving: the M1 suite is its regression net.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable, List, Optional


@dataclass
class Finding:
    """One content-quality observation about one artifact.

    ``artifact_id`` is stage-agnostic on purpose: this record is emitted for
    requirements, components, interfaces and ADRs alike. It matches
    ``artifact_core.ArtifactFile.artifact_id`` and
    ``validate_traceability.Finding.artifact_id``.
    """

    rule: str
    severity: str  # "error" | "warn" | "info"
    artifact_id: str
    field: str
    excerpt: str
    message: str
    suggested_rewrite_hint: str


def flatten_text(value: Any) -> str:
    """Coerce a frontmatter value to a clean single-space-joined string."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[.;\n]+", text) if s.strip()]


# Qualifiers that promise a property without committing to a measurement.
# Shared: a vague requirement and a vague component responsibility fail the
# same way.
VAGUE_TERMS = {
    "fast", "rapid", "quick", "user-friendly", "easy", "intuitive", "seamless",
    "efficient", "robust", "flexible", "scalable", "secure", "reliable",
    "performant", "minimize", "maximize", "optimize", "approximately",
    "appropriate", "adequate", "sufficient", "state-of-the-art", "modern", "tbd",
}

# Verbs that denote a distinct action. Shared: M1's `compound` rule and M2's
# `god-component` rule both ask "does an and/or here join two actions?".
ACTION_VERBS = {
    "create", "update", "delete", "remove", "send", "display", "show", "store",
    "save", "validate", "verify", "notify", "alert", "log", "record", "generate",
    "transition", "publish", "return", "reject", "accept", "allow", "prevent",
    "block", "provide", "calculate", "compute", "export", "import", "retry",
    "cancel", "archive", "encrypt", "decrypt", "authenticate", "authorize",
    "render", "email", "persist", "enqueue", "dispatch", "present", "list",
    "filter", "sort", "redirect", "set", "mark", "flag", "assign",
}


def print_report(
    findings: List[Finding], root_dir: str, quiet: bool, noun: str = "requirement"
) -> None:
    """Print the shared per-artifact + summary report.

    ``noun`` labels the stage in the header line only, matching
    ``artifact_core.print_report``'s existing parameter of the same name.
    """
    by_artifact: dict = {}
    for f in findings:
        by_artifact.setdefault(f.artifact_id, []).append(f)

    print(f"Content-linting {noun}s in: {root_dir}")
    if not findings:
        print("No content anti-patterns found.")
        return
    for artifact_id in sorted(by_artifact):
        print(f"\n{artifact_id}")
        for f in by_artifact[artifact_id]:
            print(f"  [{f.severity}] {f.rule} ({f.field}): {f.message}")
            if not quiet:
                print(f"        excerpt: {f.excerpt}")
                print(f"        suggest: {f.suggested_rewrite_hint}")
    counts = {sev: sum(1 for f in findings if f.severity == sev)
              for sev in ("error", "warn", "info")}
    print(
        f"\nSummary: {len(findings)} finding(s) "
        f"({counts['error']} error, {counts['warn']} warn, {counts['info']} info)."
    )


def run_cli(
    argv: Optional[List[str]],
    *,
    default_dir: str,
    noun: str,
    lint_dir: Callable[[str], List[Finding]],
    description: str,
) -> int:
    """The shared linter CLI. Returns the process exit code.

    Advisory by contract: 0 unless ``--strict`` meets an error-severity finding
    (1) or the directory is missing (2).
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("root_dir", nargs="?", default=default_dir)
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any error-severity finding exists.")
    parser.add_argument("--quiet", action="store_true",
                        help="Print one line per finding (no excerpt/suggestion).")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.root_dir):
        print(f"ERROR: {noun} directory not found: {args.root_dir}", file=sys.stderr)
        return 2

    findings = lint_dir(args.root_dir)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print_report(findings, args.root_dir, args.quiet, noun)

    if args.strict and any(f.severity == "error" for f in findings):
        return 1
    return 0
```

- [ ] **Step 4: Rewrite the M1 linter's scaffolding to import from `lint_core`**

In `skills/requirements/scripts/lint_requirements_content.py`:

Replace the import block and the `Finding`/`_text`/`_sentences`/`VAGUE_TERMS`/`ACTION_VERBS` definitions (lines 20-61 and 186-194 of the current file) with:

```python
from __future__ import annotations

import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Shared linter core lives at the repo root in ``lib/``; add it to the path
# before importing. Resolved relative to this file, so cwd does not matter.
# Mirrors validate_design.py's bootstrap.
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import lint_core as core  # noqa: E402
from lint_core import (  # noqa: E402  (re-exported for tests)
    ACTION_VERBS,
    VAGUE_TERMS,
    Finding,
)

import validate_requirements as vr  # noqa: E402
```

Then, mechanically through the rest of the file:

- `_text(` → `core.flatten_text(`
- `_sentences(` → `core.sentences(`
- every `Finding(... req_id=X ...)` → `Finding(... artifact_id=X ...)`

Delete `_print_report` entirely and replace `main` with:

```python
def main(argv: Optional[List[str]] = None) -> int:
    return core.run_cli(
        argv,
        default_dir=".sdlc/requirements",
        noun="requirement",
        lint_dir=lint_dir,
        description=(
            "Content-quality linter for Groundwork requirement artifacts."
        ),
    )
```

Leave `lint_dir`, `parse_glossary`, `_mentions`, every `check_*`, `TECH_TERMS`, `EARS_LEADS`, `GLOSSARY_SEARCH_FIELDS`, the glossary regexes, `CHECKS` and `SET_CHECKS` exactly where they are. They are stage knowledge.

Note the one internal rename `lint_dir` needs: its local `req_id` variable feeds `Finding(artifact_id=...)` now. Keep the local name `req_id` — inside a requirements-only function it is the honest name, and the record field is what had to become stage-agnostic, not every local.

- [ ] **Step 5: Run the M1 suite**

Run: `python3 -m pytest skills/requirements/scripts/tests -v`

Expected: PASS, the full M1 suite. If any test other than `test_json_output_is_parseable` needed an edit to get here, the extraction changed behavior — revert and redo it as a pure move.

- [ ] **Step 6: Update the M1 script README**

In `skills/requirements/scripts/README.md`, append to the content-linter section (after the exit-codes paragraph at line ~75):

```markdown
The `--json` payload is a list of findings, each with `rule`, `severity`,
`artifact_id`, `field`, `excerpt`, `message`, and `suggested_rewrite_hint`.
The record is shared with the design stage's linter via `lib/lint_core.py`,
which is why the id field is stage-agnostic rather than `req_id`.
```

- [ ] **Step 7: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS. This task adds no tests; it must not lose any either.

- [ ] **Step 8: Commit**

```bash
git add lib/lint_core.py skills/requirements/scripts/lint_requirements_content.py \
        skills/requirements/scripts/tests/test_lint_content.py \
        skills/requirements/scripts/README.md
git commit -m "refactor(sto-208): extract lib/lint_core.py from the M1 content linter

The design stage needs the same finding record, prose helpers, report format
and CLI the requirements linter already has. Extracted rather than copied,
mirroring what STO-197 did for the validators with artifact_core.py.

Finding.req_id becomes Finding.artifact_id: a shared record cannot keep a
requirements-flavoured field name, and validate_traceability.Finding already
spells it that way. This changes the M1 --json key; nothing in the repo reads
it, and the M1 suite is the regression net for the move."
```

---

### Task 2: The design linter, with the two component rules

**Files:**
- Create: `skills/design/scripts/lint_design_content.py`
- Create: `skills/design/scripts/tests/test_lint_design_content.py`
- Create: `skills/design/scripts/tests/fixtures/lint/clean/` (assumptions.md, drivers.md, components/CMP-001-order-service.md)
- Create: `skills/design/scripts/tests/fixtures/lint/vague-responsibility/` (assumptions.md, drivers.md, components/CMP-001-cache.md)
- Create: `skills/design/scripts/tests/fixtures/lint/god-component/` (assumptions.md, drivers.md, components/CMP-001-notifier.md)

**Interfaces:**
- Consumes: everything Task 1 produced.
- Produces: `lint_design_content.lint_dir(design_dir) -> List[Finding]`; `check_vague_responsibility(artifact_id, fm, body) -> List[Finding]`; `check_god_component(artifact_id, fm, body) -> List[Finding]`; the module-level `CHECKS` and `SET_CHECKS` registries. Tasks 3-5 append to those registries and follow the same `(artifact_id, fm, body)` signature.

- [ ] **Step 1: Create the three fixture sets**

Every design fixture set needs `assumptions.md` and `drivers.md` — `validate_design.py` gates them, and while the linter does not, keeping fixture sets structurally valid means they can be pointed at either tool. Each file below is complete; write it verbatim.

`skills/design/scripts/tests/fixtures/lint/clean/assumptions.md`:

```markdown
# Assumptions

## Assumptions

- None identified.

## Dependencies

- None identified.

## Open Questions

- None identified.
```

`skills/design/scripts/tests/fixtures/lint/clean/drivers.md`:

```markdown
# Architecture Drivers

## Architecturally Significant Requirements

- None identified.

## Tradeoffs

- None identified.

## Sensitivity Points

- None identified.
```

`skills/design/scripts/tests/fixtures/lint/clean/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
title: order-service
description: Owns the order aggregate.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
responsibility: Owns the order aggregate and every transition of its state.
boundary: internal
depends_on: []
---

# order-service

The near-miss for `god-component`: "and every transition" is a noun phrase, not
a second action verb, so this must stay clean.
```

Copy `assumptions.md` and `drivers.md` verbatim into the other two fixture dirs.

`skills/design/scripts/tests/fixtures/lint/vague-responsibility/components/CMP-001-cache.md`:

```markdown
---
id: CMP-001
type: component
title: cache
description: An in-memory cache.
traces_from:
  - NFR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Provides fast, scalable access to recently read records.
boundary: internal
depends_on: []
---

# cache

Two vague terms, no number anywhere: both findings must be `warn`.
```

`skills/design/scripts/tests/fixtures/lint/god-component/components/CMP-001-notifier.md`:

```markdown
---
id: CMP-001
type: component
title: notifier
description: Delivers notifications.
traces_from:
  - FR-002
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Persists the outbound queue and sends every queued notification.
boundary: internal
depends_on: []
---

# notifier

"and sends" joins a second action verb — two purposes in one component.
```

- [ ] **Step 2: Write the failing tests**

Create `skills/design/scripts/tests/test_lint_design_content.py`:

```python
"""Tests for the Groundwork design content-quality linter (STO-208)."""
import os

import lint_design_content as ldc

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "fixtures", "lint")


def rules_for(subdir):
    return {f.rule for f in ldc.lint_dir(os.path.join(LINT, subdir))}


def findings_for(subdir, rule):
    return [f for f in ldc.lint_dir(os.path.join(LINT, subdir)) if f.rule == rule]


def test_clean_fixture_has_no_findings():
    assert ldc.lint_dir(os.path.join(LINT, "clean")) == []


def test_advisory_exit_is_zero():
    assert ldc.main([os.path.join(LINT, "vague-responsibility")]) == 0


def test_missing_directory_exits_two():
    assert ldc.main([os.path.join(LINT, "does-not-exist")]) == 2


def test_strict_is_a_noop_without_error_severity(capsys):
    # No rule in STO-208 emits `error`, so --strict must still exit 0 even
    # over a fixture with findings. This pins the advisory contract.
    code = ldc.main([os.path.join(LINT, "god-component"), "--strict"])
    capsys.readouterr()
    assert code == 0


def test_vague_responsibility_flagged():
    assert "vague-responsibility" in rules_for("vague-responsibility")


def test_vague_responsibility_is_warn_when_unquantified():
    found = findings_for("vague-responsibility", "vague-responsibility")
    assert found
    assert all(f.severity == "warn" for f in found)


def test_vague_responsibility_downgraded_when_quantified():
    fm = {"type": "component",
          "responsibility": "Serves reads fast, within 50 ms at p99."}
    found = ldc.check_vague_responsibility("CMP-001", fm, "")
    assert found, "expected a finding for 'fast'"
    assert all(f.severity == "info" for f in found)


def test_god_component_flagged():
    assert "god-component" in rules_for("god-component")


def test_god_component_ignores_adverb_conjunction():
    # The noise case the verb anchoring exists to suppress.
    fm = {"type": "component",
          "responsibility": "Persists pet state durably and atomically."}
    assert ldc.check_god_component("CMP-001", fm, "") == []


def test_god_component_ignores_noun_conjunction():
    fm = {"type": "component",
          "responsibility": "Owns the order aggregate and every transition of "
                            "its state."}
    assert ldc.check_god_component("CMP-001", fm, "") == []


def test_component_rules_skip_non_components():
    fm = {"type": "interface", "responsibility": "Provides fast and easy access."}
    assert ldc.check_vague_responsibility("IF-001", fm, "") == []
    assert ldc.check_god_component("IF-001", fm, "") == []
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`

Expected: every test errors at collection with `ModuleNotFoundError: No module named 'lint_design_content'`. That is the correct red — the module does not exist yet.

- [ ] **Step 4: Create the linter**

Create `skills/design/scripts/lint_design_content.py`:

```python
#!/usr/bin/env python3
"""Content-quality linter for Groundwork atomic design artifacts (STO-208).

The M2 analogue of ``lint_requirements_content.py``. Distinct from
``validate_design.py`` (schema + cross-file structure) and from
``validate_traceability.py`` (design <-> requirements edges): this tool reads
the *prose and the shape* of a design set and flags what neither structural
tier can see — a responsibility that promises without measuring, a component
doing two jobs, an interface nobody consumes, a hand-waved failure mode, an ADR
whose consequences are all upside, and a dependency cycle in a graph where
every individual edge resolves.

It is ADVISORY: it prints a per-artifact diagnostic and exits 0. Pass
``--strict`` to exit non-zero on any ``error``-severity finding (no rule emits
one today). Pass ``--json`` for machine-readable findings.

It runs from ``skills/design/SKILL.md`` Step 4, after the formatter's two hard
gates have passed — not from the critic, which runs before anything is on disk.

Usage
-----
    python3 lint_design_content.py [DESIGN_DIR]
    python3 lint_design_content.py --json .sdlc/design
    python3 lint_design_content.py --strict --quiet design
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Shared linter core lives at the repo root in ``lib/``. Resolved relative to
# this file, so cwd does not matter. Mirrors validate_design.py's bootstrap.
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import lint_core as core  # noqa: E402
from lint_core import Finding  # noqa: E402  (re-exported for tests)

import validate_design as vd  # noqa: E402


def _read_body(path: str) -> str:
    """Return a file's text with the frontmatter block stripped.

    The ADR rules read prose under MADR headings, which lives in the body. A
    read failure yields '' rather than raising: this tool is advisory, and an
    unreadable file is the structural validator's finding to make.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return ""
    block = vd.extract_frontmatter_block(text)
    if block is None:
        return text
    return text[text.index(block) + len(block):]


# ---------------------------------------------------------------------------
# Component rules
# ---------------------------------------------------------------------------
def check_vague_responsibility(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a responsibility that promises a property without measuring it.

    The `vague-qualifier` analogue, including its severity demotion: a sentence
    carrying a digit has committed to a number somewhere, which is the failure
    this rule hunts, so it drops to `info`.
    """
    if fm.get("type") != "component":
        return []
    findings: List[Finding] = []
    text = core.flatten_text(fm.get("responsibility"))
    for sentence in core.sentences(text):
        low = sentence.lower()
        quantified = bool(re.search(r"\d", sentence))
        for term in sorted(core.VAGUE_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                findings.append(Finding(
                    rule="vague-responsibility",
                    severity="info" if quantified else "warn",
                    artifact_id=artifact_id,
                    field="responsibility",
                    excerpt=sentence.strip()[:120],
                    message=f"vague qualifier '{term}' without a concrete metric",
                    suggested_rewrite_hint=(
                        f"replace '{term}' with a measurable threshold, or move "
                        f"the property to an NFR the component traces to"
                    ),
                ))
    return findings


_GOD_COMPONENT_RE = re.compile(
    r"\b(and|or)\s+(" + "|".join(sorted(core.ACTION_VERBS)) + r")\b",
    re.IGNORECASE,
)


def check_god_component(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a responsibility gluing two purposes together.

    Ports M1's `compound` heuristic. M1 anchors its scan on 'shall' and searches
    the predicate after it; a responsibility has no such keyword, so the scan
    runs over the whole field. The verb anchoring is what keeps it quiet:
    'durably and atomically' does not fire, 'and sends notifications' does.
    """
    if fm.get("type") != "component":
        return []
    text = core.flatten_text(fm.get("responsibility"))
    match = _GOD_COMPONENT_RE.search(text)
    if not match:
        return []
    return [Finding(
        rule="god-component",
        severity="warn",
        artifact_id=artifact_id,
        field="responsibility",
        excerpt=text.strip()[:120],
        message=(
            f"two actions joined by '{match.group(1)}' ('{match.group(2)}') in "
            f"one responsibility"
        ),
        suggested_rewrite_hint=(
            "a component with two responsibilities is two components — split "
            "it, or name the single purpose that subsumes both"
        ),
    )]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
# Per-artifact checks: (artifact_id, frontmatter, body) -> [Finding].
# The body parameter is what M1's signature lacks: the ADR rules read prose
# under MADR headings, which is not in frontmatter.
CHECKS: List[Callable[[str, Dict[str, Any], str], List[Finding]]] = [
    check_vague_responsibility,
    check_god_component,
]

# Set-level checks: (artifacts) -> [Finding], where `artifacts` is the list of
# (artifact_id, frontmatter, body) triples. These need the whole set at once —
# "no component consumes this interface" is not decidable from one file, the
# same reason M1's glossary check needed SET_CHECKS.
SET_CHECKS: List[Callable[[List[Tuple[str, Dict[str, Any], str]]], List[Finding]]] = []


def lint_dir(design_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    artifacts: List[Tuple[str, Dict[str, Any], str]] = []
    for path in vd.discover_files(design_dir):
        fm, err = vd.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        artifact_id = fm.get("id") or os.path.basename(path)
        body = _read_body(path)
        artifacts.append((artifact_id, fm, body))
        for check in CHECKS:
            findings.extend(check(artifact_id, fm, body))
    for set_check in SET_CHECKS:
        findings.extend(set_check(artifacts))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    return core.run_cli(
        argv,
        default_dir=".sdlc/design",
        noun="design artifact",
        lint_dir=lint_dir,
        description=(
            "Content-quality linter for Groundwork design artifacts."
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`

Expected: PASS. (The plan deliberately does not pin test counts; see Global Constraints.)

- [ ] **Step 6: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/design/scripts/lint_design_content.py \
        skills/design/scripts/tests/test_lint_design_content.py \
        skills/design/scripts/tests/fixtures/lint/
git commit -m "feat(sto-208): design content linter, with the component rules

vague-responsibility and god-component, both ported from their M1 analogues.
The per-artifact check signature gains a body parameter that M1's lacks: the
ADR rules landing in Task 4 read prose under MADR headings, which is not in
frontmatter."
```

---

### Task 3: The interface rules

**Files:**
- Modify: `skills/design/scripts/lint_design_content.py`
- Modify: `skills/design/scripts/tests/test_lint_design_content.py`
- Create: `skills/design/scripts/tests/fixtures/lint/orphan-interface/` (assumptions.md, drivers.md, components/CMP-001-order-service.md, components/CMP-002-order-store.md, interfaces/IF-001-consumed.md, interfaces/IF-002-orphan.md)
- Create: `skills/design/scripts/tests/fixtures/lint/error-modes/` (assumptions.md, drivers.md, components/CMP-001-order-service.md, components/CMP-002-order-store.md, interfaces/IF-001-vague-failure.md)

**Fixture shape — read before writing them.** Both sets use the same
two-component base: `CMP-001` consumes, `CMP-002` provides. A single-component
set where the one component consumes the interface it also provides is a
*self-cycle*, which Task 5's `test_acyclic_set_is_clean` reads as a failure.
Keep the consumer and the provider distinct.

**Interfaces:**
- Consumes: `lint_core` (Task 1); `CHECKS`, `SET_CHECKS`, `lint_dir` (Task 2).
- Produces: `check_error_modes_handwaved(artifact_id, fm, body) -> List[Finding]`; `check_orphan_interfaces(artifacts) -> List[Finding]` — the first `SET_CHECK`, taking the triple list.

- [ ] **Step 1: Create the two fixture sets**

Copy `assumptions.md` and `drivers.md` from `fixtures/lint/clean/` into both new directories.

`fixtures/lint/orphan-interface/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
title: order-service
description: Owns the order aggregate.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
responsibility: Owns the order aggregate.
boundary: internal
depends_on:
  - IF-001
---

# order-service

Consumes IF-001 and nothing else, leaving IF-002 orphaned.
```

`fixtures/lint/orphan-interface/components/CMP-002-order-store.md`:

```markdown
---
id: CMP-002
type: component
title: order-store
description: Persists orders.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
responsibility: Persists the order aggregate.
boundary: internal
depends_on: []
---

# order-store

Provides both interfaces and consumes none, which keeps the set acyclic.
```

`fixtures/lint/orphan-interface/interfaces/IF-001-consumed.md`:

```markdown
---
id: IF-001
type: interface
title: order-lookup
description: Reads an order by id.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: get_order
    summary: Return the order with the given id.
    interaction: synchronous
error_modes:
  - The requested order id does not exist.
---

# order-lookup

Consumed by CMP-001 — the near-miss that must stay clean.
```

`fixtures/lint/orphan-interface/interfaces/IF-002-orphan.md`:

```markdown
---
id: IF-002
type: interface
title: order-archive
description: Archives an order.
traces_from:
  - FR-001
traces_to: {}
status: reviewed
confidence: high
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: archive_order
    summary: Move the order to cold storage.
    interaction: synchronous
error_modes:
  - The order is already archived.
---

# order-archive

No component lists IF-002 in depends_on — this is the orphan.
```

`fixtures/lint/error-modes/components/CMP-001-order-service.md` and
`fixtures/lint/error-modes/components/CMP-002-order-store.md`: copy both files
verbatim from `fixtures/lint/orphan-interface/components/`.

`fixtures/lint/error-modes/interfaces/IF-001-vague-failure.md`:

```markdown
---
id: IF-001
type: interface
title: order-lookup
description: Reads an order by id.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: get_order
    summary: Return the order with the given id.
    interaction: synchronous
error_modes:
  - Errors are handled gracefully.
  - The requested order id does not exist.
---

# order-lookup

One hand-waved mode and one real one: the rule must flag exactly the first.
CMP-001 consumes this, so the set has no orphan and no cycle either — the
handwaved mode is the only finding it should produce.
```

- [ ] **Step 2: Write the failing tests**

Append to `skills/design/scripts/tests/test_lint_design_content.py`:

```python
# ---------------------------------------------------------------------------
# Interface rules
# ---------------------------------------------------------------------------
def test_orphan_interface_flagged():
    found = findings_for("orphan-interface", "orphan-interface")
    assert len(found) == 1
    assert found[0].artifact_id == "IF-002"
    assert found[0].severity == "warn"


def test_consumed_interface_not_flagged():
    found = findings_for("orphan-interface", "orphan-interface")
    assert "IF-001" not in {f.artifact_id for f in found}


def test_error_modes_handwaved_flagged():
    found = findings_for("error-modes", "error-modes-handwaved")
    assert len(found) == 1
    assert "gracefully" in found[0].excerpt


def test_concrete_error_mode_not_flagged():
    fm = {"type": "interface",
          "error_modes": ["The requested order id does not exist."]}
    assert ldc.check_error_modes_handwaved("IF-001", fm, "") == []


def test_error_modes_rule_skips_non_interfaces():
    fm = {"type": "component", "error_modes": ["Handled gracefully."]}
    assert ldc.check_error_modes_handwaved("CMP-001", fm, "") == []
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -k "orphan or error_mode" -v`

Expected: FAIL — `AttributeError: module 'lint_design_content' has no attribute 'check_error_modes_handwaved'` for the direct-call tests, and empty finding lists for the fixture-driven ones.

- [ ] **Step 4: Add the two rules**

In `lint_design_content.py`, after `check_god_component`:

```python
# ---------------------------------------------------------------------------
# Interface rules
# ---------------------------------------------------------------------------
# Adverbs of intent: they describe an attitude toward failure rather than a
# failure. "Handled gracefully" tells a reader nothing they can design against.
_HANDWAVE_RE = re.compile(
    r"\b(gracefully|appropriately|properly|as needed|as appropriate)\b",
    re.IGNORECASE,
)


def check_error_modes_handwaved(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an error mode that names an attitude instead of a failure."""
    if fm.get("type") != "interface":
        return []
    findings: List[Finding] = []
    modes = fm.get("error_modes")
    if not isinstance(modes, list):
        return []
    for mode in modes:
        text = core.flatten_text(mode)
        match = _HANDWAVE_RE.search(text)
        if not match:
            continue
        findings.append(Finding(
            rule="error-modes-handwaved",
            severity="warn",
            artifact_id=artifact_id,
            field="error_modes",
            excerpt=text[:120],
            message=(
                f"error mode says '{match.group(1)}' rather than naming a "
                f"failure"
            ),
            suggested_rewrite_hint=(
                "name the condition and what the caller observes: 'the "
                "requested id does not exist', not 'errors are handled'"
            ),
        ))
    return findings


def check_orphan_interfaces(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> List[Finding]:
    """Flag an interface no component consumes.

    The `glossary-unused` analogue: defined-but-unused is a warning, not a gate.
    A contract nobody depends on is either dead or a missing `depends_on` edge,
    and the linter cannot tell which — so it reports rather than decides.
    """
    consumed: set = set()
    interfaces: List[Tuple[str, Dict[str, Any]]] = []
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") == "component":
            depends = fm.get("depends_on")
            if isinstance(depends, list):
                consumed.update(core.flatten_text(d) for d in depends)
        elif fm.get("type") == "interface":
            interfaces.append((artifact_id, fm))

    findings: List[Finding] = []
    for artifact_id, fm in interfaces:
        if artifact_id in consumed:
            continue
        findings.append(Finding(
            rule="orphan-interface",
            severity="warn",
            artifact_id=artifact_id,
            field="id",
            excerpt=core.flatten_text(fm.get("title")),
            message=f"interface '{artifact_id}' is consumed by no component",
            suggested_rewrite_hint=(
                "drop the contract, or add it to the depends_on of the "
                "component that should be consuming it"
            ),
        ))
    return findings
```

Then extend both registries:

```python
CHECKS: List[Callable[[str, Dict[str, Any], str], List[Finding]]] = [
    check_vague_responsibility,
    check_god_component,
    check_error_modes_handwaved,
]

SET_CHECKS: List[Callable[[List[Tuple[str, Dict[str, Any], str]]], List[Finding]]] = [
    check_orphan_interfaces,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`

Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/design/scripts/lint_design_content.py \
        skills/design/scripts/tests/test_lint_design_content.py \
        skills/design/scripts/tests/fixtures/lint/
git commit -m "feat(sto-208): interface rules — orphan contracts and handwaved failures

orphan-interface is the first SET_CHECK: 'no component consumes this' is not
decidable from one file, the same reason M1's glossary check needed the
registry. No error-modes-empty rule — the schema already sets minItems: 1."
```

---

### Task 4: `body_section` and the three ADR rules

**Files:**
- Modify: `lib/lint_core.py`
- Modify: `skills/design/scripts/lint_design_content.py`
- Modify: `skills/design/scripts/tests/test_lint_design_content.py`
- Create: `skills/design/scripts/tests/fixtures/lint/adr-smells/` (assumptions.md, drivers.md, adr/ADR-001-one-sided.md)
- Create: `skills/design/scripts/tests/fixtures/lint/adr-proposed/` (assumptions.md, drivers.md, adr/ADR-001-pending.md)

**Interfaces:**
- Consumes: everything Tasks 1-3 produced.
- Produces: `lint_core.body_section(text, heading) -> str`; `check_adr_consequences_one_sided`, `check_adr_vague_driver`, `check_adr_option_unexamined`, each `(artifact_id, fm, body) -> List[Finding]`.

- [ ] **Step 1: Add `body_section` to `lib/lint_core.py`**

Append to `lib/lint_core.py`:

```python
def body_section(text: str, heading: str) -> str:
    """Return the raw text under a Markdown heading, or '' if it is absent.

    The section runs to the next heading of the same or higher level, so
    ``body_section(body, "## Decision Outcome")`` stops at the next ``##`` but
    contains its own ``### Consequences`` subsection.

    ``validate_traceability.decision_drivers_section`` is a near-equivalent,
    hard-coded to one heading. It is deliberately not reused: importing a
    hard-gate validator into an advisory linter to save fifteen lines couples
    the two tiers in the wrong direction (STO-208 spec D5).
    """
    level = len(heading) - len(heading.lstrip("#"))
    if level == 0:
        return ""
    start = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not start:
        return ""
    rest = text[start.end():]
    nxt = re.search(rf"^#{{1,{level}}}\s+\S", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest
```

- [ ] **Step 2: Create the two ADR fixture sets**

Copy `assumptions.md` and `drivers.md` from `fixtures/lint/clean/` into both.

`fixtures/lint/adr-smells/adr/ADR-001-one-sided.md`:

```markdown
---
id: ADR-001
type: adr
title: Event-sourced order store
description: How the order store records state.
traces_from:
  - NFR-001
traces_to: {}
status: draft
decision_status: accepted
confidence: medium
created_at: 2026-08-14
considered_options:
  - Event sourcing
  - Snapshot table
chosen_option: Event sourcing
---

# ADR-001: Event-sourced order store

## Context and Problem Statement

The order store must answer "how did this order reach its current state".

## Decision Drivers

- The store must be scalable.
- NFR-001

## Considered Options

- **Event sourcing** — every state change is an appended event.

## Decision Outcome

Event sourcing.

### Consequences

- Good: the full history of every order is available by construction.
- Good: no separate audit log to keep in step with the store.
```

That file carries all three ADR smells at once: consequences with no Bad bullet, a vague driver ("scalable"), and `Snapshot table` named in frontmatter but never discussed under `## Considered Options`.

`fixtures/lint/adr-proposed/adr/ADR-001-pending.md`:

```markdown
---
id: ADR-001
type: adr
title: Transport for stat updates
description: How stat updates reach subscribers.
traces_from:
  - NFR-002
traces_to: {}
status: draft
decision_status: proposed
confidence: low
created_at: 2026-08-14
---

# ADR-001: Transport for stat updates

## Context and Problem Statement

Subscribers need stat updates; the mechanism is not yet decided.

## Decision Drivers

- NFR-002

## Considered Options

- None — no alternatives are recorded yet.

## Decision Outcome

Pending. The decision is deferred until the delivery constraints are known.

### Consequences

- None — the decision is pending.
```

This is the near-miss set: a `proposed` ADR carrying the formatter's honest placeholders. All three ADR rules must stay silent over it.

- [ ] **Step 3: Write the failing tests**

Append to `skills/design/scripts/tests/test_lint_design_content.py`:

```python
# ---------------------------------------------------------------------------
# body_section
# ---------------------------------------------------------------------------
def test_body_section_stops_at_same_level_heading():
    text = "## A\n\nalpha\n\n## B\n\nbeta\n"
    assert "alpha" in ldc.core.body_section(text, "## A")
    assert "beta" not in ldc.core.body_section(text, "## A")


def test_body_section_keeps_deeper_subsections():
    text = "## Decision Outcome\n\npicked\n\n### Consequences\n\n- Good: x\n\n## Next\n"
    section = ldc.core.body_section(text, "## Decision Outcome")
    assert "Consequences" in section and "Next" not in section


def test_body_section_absent_heading_is_empty():
    assert ldc.core.body_section("## A\n\nalpha\n", "## Missing") == ""


# ---------------------------------------------------------------------------
# ADR rules
# ---------------------------------------------------------------------------
def test_adr_consequences_one_sided_flagged():
    found = findings_for("adr-smells", "adr-consequences-one-sided")
    assert len(found) == 1
    assert found[0].artifact_id == "ADR-001"


def test_adr_vague_driver_flagged():
    found = findings_for("adr-smells", "adr-vague-driver")
    assert found
    assert any("scalable" in f.message for f in found)


def test_adr_option_unexamined_flagged():
    found = findings_for("adr-smells", "adr-option-unexamined")
    assert len(found) == 1
    assert "Snapshot table" in found[0].excerpt
    assert found[0].severity == "info"


def test_proposed_adr_with_placeholders_is_clean():
    # The formatter writes these placeholders on purpose for a decision that
    # has not been taken. Firing here would train the reader to ignore the rule.
    assert ldc.lint_dir(os.path.join(LINT, "adr-proposed")) == []


def test_balanced_consequences_not_flagged():
    body = ("## Decision Outcome\n\nx\n\n### Consequences\n\n"
            "- Good: fast reads.\n- Bad: writes fan out.\n")
    fm = {"type": "adr", "decision_status": "accepted"}
    assert ldc.check_adr_consequences_one_sided("ADR-001", fm, body) == []


def test_adr_rules_skip_non_adrs():
    body = "### Consequences\n\n- Good: only upside.\n"
    fm = {"type": "component", "decision_status": "accepted"}
    assert ldc.check_adr_consequences_one_sided("CMP-001", fm, body) == []
```

- [ ] **Step 4: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -k "body_section or adr" -v`

Expected: FAIL — `AttributeError` on `body_section` and on each `check_adr_*`.

- [ ] **Step 5: Add the three ADR rules**

In `lint_design_content.py`, after `check_orphan_interfaces`:

```python
# ---------------------------------------------------------------------------
# ADR rules
# ---------------------------------------------------------------------------
# MADR headings this stage writes. Gated for presence by validate_design.py;
# their prose is this linter's business.
DRIVERS_HEADING = "## Decision Drivers"
OPTIONS_HEADING = "## Considered Options"
CONSEQUENCES_HEADING = "### Consequences"

# `- Good: ...` / `- Bad: ...`, and MADR 4.0's `- Good, because ...`. Bold
# markers are tolerated because the formatter emits them in places.
_CONSEQUENCE_RE = re.compile(r"^\s*[-*]\s*(?:\*\*)?(Good|Bad)\b", re.MULTILINE)

# The formatter's honest placeholder for a section with nothing to record yet.
_PLACEHOLDER_RE = re.compile(r"^\s*[-*]\s*None\b", re.MULTILINE)


def check_adr_consequences_one_sided(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an accepted decision whose consequences are all upside.

    Every real decision costs something. A consequences section with Good
    bullets and no Bad bullet records a decision that was not weighed.

    Skipped for `proposed` decisions and for the placeholder: both are correct
    output for a decision that has not been taken.
    """
    if fm.get("type") != "adr" or fm.get("decision_status") == "proposed":
        return []
    section = core.body_section(body, CONSEQUENCES_HEADING)
    if not section.strip() or _PLACEHOLDER_RE.search(section):
        return []
    kinds = {m.group(1).lower() for m in _CONSEQUENCE_RE.finditer(section)}
    if "bad" in kinds or "good" not in kinds:
        return []
    return [Finding(
        rule="adr-consequences-one-sided",
        severity="warn",
        artifact_id=artifact_id,
        field="consequences",
        excerpt=core.flatten_text(section)[:120],
        message="consequences list only upsides; no cost is recorded",
        suggested_rewrite_hint=(
            "name what the decision costs — a decision with no downside was "
            "not a decision"
        ),
    )]


def check_adr_vague_driver(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a vague qualifier in an ADR's decision drivers.

    The driver is what the decision claims to answer, so it is the most
    load-bearing place a vague qualifier can sit: 'must be scalable' names no
    threshold the chosen option can be checked against.
    """
    if fm.get("type") != "adr":
        return []
    section = core.body_section(body, DRIVERS_HEADING)
    findings: List[Finding] = []
    for line in section.splitlines():
        text = core.flatten_text(line)
        if not text or _PLACEHOLDER_RE.match(line):
            continue
        low = text.lower()
        quantified = bool(re.search(r"\d", text))
        for term in sorted(core.VAGUE_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                findings.append(Finding(
                    rule="adr-vague-driver",
                    severity="info" if quantified else "warn",
                    artifact_id=artifact_id,
                    field="decision_drivers",
                    excerpt=text[:120],
                    message=(
                        f"decision driver '{term}' names no threshold the "
                        f"chosen option can be checked against"
                    ),
                    suggested_rewrite_hint=(
                        "cite the NFR that quantifies it, or state the "
                        "threshold in the driver"
                    ),
                ))
    return findings


def check_adr_option_unexamined(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an option named in frontmatter but never discussed in the body.

    `info`, not `warn`: an option can legitimately be weighed under
    `## Decision Outcome` instead, so this reports a smell it cannot prove.
    The schema's `minItems: 2` is what makes the smell worth reporting — an
    option can be added to clear that gate without ever being considered.
    """
    if fm.get("type") != "adr":
        return []
    options = fm.get("considered_options")
    if not isinstance(options, list):
        return []
    section = core.body_section(body, OPTIONS_HEADING)
    if not section.strip():
        return []
    low = section.lower()
    findings: List[Finding] = []
    for option in options:
        text = core.flatten_text(option)
        if not text or text.lower() in low:
            continue
        findings.append(Finding(
            rule="adr-option-unexamined",
            severity="info",
            artifact_id=artifact_id,
            field="considered_options",
            excerpt=text[:120],
            message=(
                f"option '{text}' is listed in frontmatter but never appears "
                f"under '{OPTIONS_HEADING}'"
            ),
            suggested_rewrite_hint=(
                "weigh it in the body, or drop it — an option listed only to "
                "clear the two-option gate was not considered"
            ),
        ))
    return findings
```

Extend `CHECKS`:

```python
CHECKS: List[Callable[[str, Dict[str, Any], str], List[Finding]]] = [
    check_vague_responsibility,
    check_god_component,
    check_error_modes_handwaved,
    check_adr_consequences_one_sided,
    check_adr_vague_driver,
    check_adr_option_unexamined,
]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`

Expected: PASS.

- [ ] **Step 7: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add lib/lint_core.py skills/design/scripts/lint_design_content.py \
        skills/design/scripts/tests/test_lint_design_content.py \
        skills/design/scripts/tests/fixtures/lint/
git commit -m "feat(sto-208): ADR content rules, and body_section in the core

ADR frontmatter carries only decision_status, considered_options and
chosen_option; drivers, options detail and consequences live under the MADR
headings in the body. Hence body_section, and hence the body parameter the
check signature has carried since Task 2.

All three rules stay silent on a proposed ADR carrying the formatter's
placeholders -- correct output for a decision not yet taken."
```

---

### Task 5: The `dependency-cycle` set check

**Files:**
- Modify: `skills/design/scripts/lint_design_content.py`
- Modify: `skills/design/scripts/tests/test_lint_design_content.py`
- Create: `skills/design/scripts/tests/fixtures/lint/cycle-one/` (assumptions.md, drivers.md, components/CMP-001-alpha.md, components/CMP-002-beta.md, interfaces/IF-001-a-to-b.md, interfaces/IF-002-b-to-a.md)
- Create: `skills/design/scripts/tests/fixtures/lint/cycle-self/` (assumptions.md, drivers.md, components/CMP-001-alpha.md, interfaces/IF-001-self.md)

**Interfaces:**
- Consumes: everything Tasks 1-4 produced.
- Produces: `check_dependency_cycles(artifacts) -> List[Finding]`, appended to `SET_CHECKS`.

- [ ] **Step 1: Create the two cycle fixture sets**

Copy `assumptions.md` and `drivers.md` from `fixtures/lint/clean/` into both.

`fixtures/lint/cycle-one/components/CMP-001-alpha.md`:

```markdown
---
id: CMP-001
type: component
title: alpha
description: One half of a mutual dependency.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Owns the alpha aggregate.
boundary: internal
depends_on:
  - IF-002
---

# alpha

Consumes IF-002, which CMP-002 provides.
```

`fixtures/lint/cycle-one/components/CMP-002-beta.md`:

```markdown
---
id: CMP-002
type: component
title: beta
description: The other half of a mutual dependency.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Owns the beta aggregate.
boundary: internal
depends_on:
  - IF-001
---

# beta

Consumes IF-001, which CMP-001 provides. Get this direction backwards and there
is no cycle to find — CMP-001 consumes IF-002 (provided by CMP-002), CMP-002
consumes IF-001 (provided by CMP-001).
```

`fixtures/lint/cycle-one/interfaces/IF-001-a-to-b.md`:

```markdown
---
id: IF-001
type: interface
title: alpha-query
description: Reads alpha state.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-001
operations:
  - name: read_alpha
    summary: Return the current alpha state.
    interaction: synchronous
error_modes:
  - Alpha has not been initialised.
---

# alpha-query

Provided by CMP-001, consumed by CMP-002.
```

`fixtures/lint/cycle-one/interfaces/IF-002-b-to-a.md`:

```markdown
---
id: IF-002
type: interface
title: beta-query
description: Reads beta state.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: read_beta
    summary: Return the current beta state.
    interaction: synchronous
error_modes:
  - Beta has not been initialised.
---

# beta-query

Provided by CMP-002, consumed by CMP-001.
```

`fixtures/lint/cycle-self/components/CMP-001-alpha.md`:

```markdown
---
id: CMP-001
type: component
title: alpha
description: A component that consumes its own contract.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Owns the alpha aggregate.
boundary: internal
depends_on:
  - IF-001
---

# alpha

Provides IF-001 and consumes it — a one-component cycle.
```

`fixtures/lint/cycle-self/interfaces/IF-001-self.md`:

```markdown
---
id: IF-001
type: interface
title: alpha-query
description: Reads alpha state.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-001
operations:
  - name: read_alpha
    summary: Return the current alpha state.
    interaction: synchronous
error_modes:
  - Alpha has not been initialised.
---

# alpha-query

Provided by CMP-001, which also consumes it.
```

- [ ] **Step 2: Write the failing tests**

Append to `skills/design/scripts/tests/test_lint_design_content.py`:

```python
# ---------------------------------------------------------------------------
# dependency-cycle
# ---------------------------------------------------------------------------
def test_dependency_cycle_flagged_once():
    # A naive DFS reports the same two-component cycle once per entry path.
    # This asserts the canonicalization, not just the detection.
    found = findings_for("cycle-one", "dependency-cycle")
    assert len(found) == 1
    assert found[0].severity == "warn"


def test_dependency_cycle_message_names_components_and_interfaces():
    found = findings_for("cycle-one", "dependency-cycle")
    message = found[0].message
    for token in ("CMP-001", "CMP-002", "IF-001", "IF-002"):
        assert token in message


def test_dependency_cycle_reported_on_lowest_component():
    found = findings_for("cycle-one", "dependency-cycle")
    assert found[0].artifact_id == "CMP-001"


def test_self_dependency_flagged():
    found = findings_for("cycle-self", "dependency-cycle")
    assert len(found) == 1
    assert "CMP-001" in found[0].message


def test_acyclic_set_is_clean():
    assert findings_for("orphan-interface", "dependency-cycle") == []


def _triple(artifact_id, **fields):
    return (artifact_id, dict(id=artifact_id, **fields), "")


def test_two_independent_cycles_reported_separately():
    # Built in memory rather than as a fixture: the assertion is about the
    # de-duplication key, not about file parsing. Canonicalization must collapse
    # each cycle's rotations without collapsing two distinct cycles into one.
    artifacts = [
        _triple("CMP-001", type="component", depends_on=["IF-002"]),
        _triple("CMP-002", type="component", depends_on=["IF-001"]),
        _triple("CMP-003", type="component", depends_on=["IF-004"]),
        _triple("CMP-004", type="component", depends_on=["IF-003"]),
        _triple("IF-001", type="interface", provider="CMP-001"),
        _triple("IF-002", type="interface", provider="CMP-002"),
        _triple("IF-003", type="interface", provider="CMP-003"),
        _triple("IF-004", type="interface", provider="CMP-004"),
    ]
    found = ldc.check_dependency_cycles(artifacts)
    assert len(found) == 2
    assert {f.artifact_id for f in found} == {"CMP-001", "CMP-003"}
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -k "cycle or acyclic" -v`

Expected: FAIL — every assertion sees an empty finding list, because `SET_CHECKS` has no cycle check yet.

- [ ] **Step 4: Add the cycle check**

In `lint_design_content.py`, after `check_adr_option_unexamined`:

```python
# ---------------------------------------------------------------------------
# Set-level: the dependency graph
# ---------------------------------------------------------------------------
def _component_graph(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> Dict[str, Dict[str, str]]:
    """Build {component_id: {target_component_id: via_interface_id}}.

    One edge type: component A depends on component B when A lists an interface
    whose provider is B. Where two interfaces produce the same A->B edge, the
    lowest-sorting interface id is kept, so the reported path is deterministic.
    """
    providers: Dict[str, str] = {}
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") == "interface":
            provider = core.flatten_text(fm.get("provider"))
            if provider:
                providers[artifact_id] = provider

    graph: Dict[str, Dict[str, str]] = {}
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") != "component":
            continue
        edges: Dict[str, str] = {}
        depends = fm.get("depends_on")
        if isinstance(depends, list):
            for raw in sorted(core.flatten_text(d) for d in depends):
                target = providers.get(raw)
                if target and target not in edges:
                    edges[target] = raw
        graph[artifact_id] = edges
    return graph


def _canonical(cycle: List[str]) -> Tuple[str, ...]:
    """Rotate a cycle to start at its lowest-sorting component id.

    Without this the same cycle is reported once per entry path — the shipped
    tamagotchi set yields its single CMP-003/CMP-004 cycle six times.
    """
    pivot = cycle.index(min(cycle))
    return tuple(cycle[pivot:] + cycle[:pivot])


def check_dependency_cycles(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> List[Finding]:
    """Flag cycles in the CMP.depends_on -> IF.provider -> CMP graph.

    Not a structural error: every edge resolves and every provider exists, so
    the structural validator is right to pass it. The *shape* is the defect,
    and shape is what the structural tier cannot see.
    """
    graph = _component_graph(artifacts)
    seen: set = set()
    cycles: List[List[str]] = []

    def walk(node: str, stack: List[str]) -> None:
        for target in sorted(graph.get(node, {})):
            if target in stack:
                cycle = stack[stack.index(target):]
                key = _canonical(cycle)
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(key))
                continue
            walk(target, stack + [target])

    for start in sorted(graph):
        walk(start, [start])

    findings: List[Finding] = []
    for cycle in sorted(cycles):
        # Render CMP-001 -> IF-002 -> CMP-002 -> IF-001 -> CMP-001, naming the
        # interfaces because the interfaces are where the fix is made.
        parts: List[str] = []
        for i, node in enumerate(cycle):
            nxt = cycle[(i + 1) % len(cycle)]
            parts.append(node)
            parts.append(graph[node][nxt])
        path = " -> ".join(parts + [cycle[0]])
        findings.append(Finding(
            rule="dependency-cycle",
            severity="warn",
            artifact_id=cycle[0],
            field="depends_on",
            excerpt=path[:120],
            message=f"dependency cycle: {path}",
            suggested_rewrite_hint=(
                "break the loop at one of the named interfaces — invert the "
                "dependency, or move the shared state into a component both "
                "can depend on"
            ),
        ))
    return findings
```

Extend `SET_CHECKS`:

```python
SET_CHECKS: List[Callable[[List[Tuple[str, Dict[str, Any], str]]], List[Finding]]] = [
    check_orphan_interfaces,
    check_dependency_cycles,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`

Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/design/scripts/lint_design_content.py \
        skills/design/scripts/tests/test_lint_design_content.py \
        skills/design/scripts/tests/fixtures/lint/
git commit -m "feat(sto-208): dependency-cycle detection over the component graph

Every edge in a cycle resolves and every provider exists, so the structural
validator is right to pass it -- the shape is the defect. Cycles are
canonicalized by rotating to the lowest-sorting component id before reporting,
without which the shipped tamagotchi set reports its single cycle six times."
```

---

### Task 6: The worked-example regression, and the deviation it records

**Files:**
- Modify: `skills/design/scripts/tests/test_lint_design_content.py`
- Modify: `docs/requirements/examples/tamagotchi/README.md`

**Interfaces:**
- Consumes: `lint_design_content.lint_dir` (Tasks 2-5).
- Produces: nothing consumed downstream.

- [ ] **Step 1: Write the worked-example tests**

Append to `skills/design/scripts/tests/test_lint_design_content.py`:

```python
# ---------------------------------------------------------------------------
# The shipped worked example (STO-208 spec D7)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
TAMAGOTCHI_DESIGN = os.path.join(
    REPO_ROOT, "docs", "requirements", "examples", "tamagotchi", "design"
)


def test_shipped_tamagotchi_example_has_no_error_findings():
    # Deliberately not "has no findings". The tool always exits 0, so `clean`
    # is not a state it guarantees, and STO-219 wants the example's remaining
    # deviations to be chosen rather than absent. No rule emits `error` today;
    # this is the pin that catches a future rule promoted to `error` silently
    # invalidating the shipped example.
    findings = ldc.lint_dir(TAMAGOTCHI_DESIGN)
    assert [f for f in findings if f.severity == "error"] == []


def test_shipped_tamagotchi_example_has_the_known_cycle():
    # The CMP-003/CMP-004 cycle is the only real-world input this rule has.
    # It is recorded as a named deviation in the example README, not fixed --
    # breaking it is a design change, and regeneration is STO-219.
    cycles = [f for f in ldc.lint_dir(TAMAGOTCHI_DESIGN)
              if f.rule == "dependency-cycle"]
    assert len(cycles) == 1
    for token in ("CMP-003", "CMP-004", "IF-005", "IF-006"):
        assert token in cycles[0].message
```

- [ ] **Step 2: Run them to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -k tamagotchi -v`

Expected: PASS both. Unlike every earlier task, these are green on first run — the linter already works and the example already carries the cycle. They are regression pins, not a red-green cycle. If `test_shipped_tamagotchi_example_has_the_known_cycle` fails with a count other than 1, the canonicalization in Task 5 is wrong; check it before touching the example.

- [ ] **Step 3: Record the deviation in the example README**

Find the section of `docs/requirements/examples/tamagotchi/README.md` listing the example's open findings (the "five findings remain open" section STO-216 corrected). Add:

```markdown
- **`CMP-003` and `CMP-004` are mutually dependent.** The Pet State Manager
  consumes `IF-006` (Pet Lifecycle State, provided by `CMP-004`) to gate stat
  mutations; the Pet Lifecycle Manager consumes `IF-005` (Pet Stat Observation,
  provided by `CMP-003`) to decide transitions. Both structural validators exit
  0 over this — every edge resolves — and STO-208's `dependency-cycle` rule is
  what surfaces it. It is left in place deliberately: breaking the loop means
  re-deciding how the two managers talk to each other, which is a design change
  to a worked example, and worked-example regeneration is STO-219. A
  regenerated set should either break this cycle or state why it keeps it.
```

Check the surrounding prose for a finding count. If the section opens with a
number ("five findings remain open"), increment it — that exact staleness is
what commit `617872f` had to fix on the last ticket.

- [ ] **Step 4: Run the whole suite**

Run: `python3 -m pytest -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/design/scripts/tests/test_lint_design_content.py \
        docs/requirements/examples/tamagotchi/README.md
git commit -m "test(sto-208): pin the worked example, and record the cycle it carries

Asserts no error-severity findings rather than no findings: the tool always
exits 0, and STO-219 wants the example's deviations chosen rather than absent.
The CMP-003/CMP-004 cycle is recorded in the README as a named deviation and
handed to STO-219 rather than fixed here."
```

---

### Task 7: Wire the linter into the pipeline

**Files:**
- Modify: `skills/design/scripts/README.md`
- Modify: `skills/design/SKILL.md` (Step 4, after the `validate_traceability.py` block)
- Modify: `agents/design-critic.md:260-264`

**Interfaces:**
- Consumes: the finished linter.
- Produces: nothing — this is the documentation surface that makes the tool reachable.

- [ ] **Step 1: Add the rule table to the design scripts README**

Append to `skills/design/scripts/README.md`:

```markdown
## Content-quality linter — `lint_design_content.py`

Advisory linter for design *prose and shape* (distinct from the two structural
validators). The M2 analogue of `lint_requirements_content.py`.

```bash
python3 lint_design_content.py .sdlc/design        # human report
python3 lint_design_content.py --json .sdlc/design # machine-readable
python3 lint_design_content.py --strict design     # exit non-zero on error-severity
```

| Rule | Severity | Fires on |
|---|---|---|
| `vague-responsibility` | warn / info | A vague qualifier in a component's `responsibility`; `info` when the sentence carries a number |
| `god-component` | warn | `and`/`or` joining two action verbs in a `responsibility` |
| `orphan-interface` | warn | An `IF-` no component lists in `depends_on` |
| `error-modes-handwaved` | warn | An error mode naming an attitude ("handled gracefully") rather than a failure |
| `adr-consequences-one-sided` | warn | An accepted ADR whose `### Consequences` are all upside |
| `adr-vague-driver` | warn / info | A vague qualifier under `## Decision Drivers` |
| `adr-option-unexamined` | info | An option in frontmatter never discussed under `## Considered Options` |
| `dependency-cycle` | warn | A cycle in the `CMP.depends_on → IF.provider → CMP` graph |

Exit codes: `0` always (advisory), except `--strict` returns `1` when an
`error`-severity finding exists, and `2` on a missing directory. No rule emits
`error` today, so `--strict` is currently a no-op.

The `--json` payload matches the M1 linter's: `rule`, `severity`, `artifact_id`,
`field`, `excerpt`, `message`, `suggested_rewrite_hint`. Both linters share
`lib/lint_core.py`.

It reuses `validate_design.discover_files`/`parse_frontmatter`, so it sees
exactly the same atomic artifacts as the structural validator and skips the same
non-atomic files and the `diagrams/` subtree.
```

- [ ] **Step 2: Add the invocation to SKILL.md Step 4**

In `skills/design/SKILL.md`, after the `validate_traceability.py` block and its
error-routing prose (the section ending with the `dangling-reverse-trace`
paragraph), add:

```markdown
Then run the advisory content-quality linter and address any `warn`-severity
findings (the two validators above are the hard gates; the content linter guides
prose and shape). This is the only script-backed lint run in the stage — the
critic applied the same checks by inspection at gate time, because the files did
not exist yet. Route anything it turns up back through the critique loop to the
owning specialist rather than editing the written files by hand:

```bash
python3 skills/design/scripts/lint_design_content.py .sdlc/design
```

It always exits 0. `dependency-cycle` is the finding most worth acting on: it
means two components each need the other, which no structural check can see
because every individual edge resolves. Breaking it is a decomposition change,
so it re-dispatches to the component specialist, not the interface specialist.
```

- [ ] **Step 3: Point the critic's deferral at the real script**

In `agents/design-critic.md`, in the deferral list at lines 260-264, replace
"These belong to STO-208's content linter" with:

```markdown
  lint tier.** These belong to the content linter,
  `skills/design/scripts/lint_design_content.py`, which the skill runs at Step 4
  once the files exist. Phase 1's
```

Leave the rest of the bullet — including the "leave the sweep to STO-208"
sentence's meaning — intact; only the forward reference becomes a real path.

- [ ] **Step 4: Verify by inspection**

Run: `grep -rn "lint_design_content" skills/ agents/`

Expected: three files — the script itself, `skills/design/scripts/README.md`,
`skills/design/SKILL.md` — plus `agents/design-critic.md`. Four hits minimum,
and no remaining prose that describes the linter as unbuilt.

- [ ] **Step 5: Run the whole suite and the linter over both real sets**

```bash
python3 -m pytest -q
python3 skills/design/scripts/lint_design_content.py \
  docs/requirements/examples/tamagotchi/design
echo "exit: $?"
```

Expected: suite PASS. The linter prints the `dependency-cycle` finding for
`CMP-003` and exits 0.

- [ ] **Step 6: Commit**

```bash
git add skills/design/scripts/README.md skills/design/SKILL.md \
        agents/design-critic.md
git commit -m "docs(sto-208): wire the content linter into the design stage

Step 4 of the skill, after both hard gates -- not the critic, which runs before
anything is on disk. The critic's existing deferral stops pointing at a ticket
and starts pointing at a script."
```

---

## Verification

Run from the repo root:

```bash
# Whole suite green.
python3 -m pytest -q

# The linter runs clean over the fixtures it should, and finds what it should.
python3 skills/design/scripts/lint_design_content.py \
  skills/design/scripts/tests/fixtures/lint/clean
python3 skills/design/scripts/lint_design_content.py \
  docs/requirements/examples/tamagotchi/design

# The M1 linter still works after the extraction.
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/tamagotchi/requirements

# Both structural gates still pass over the example (this ticket changed no
# artifact, so any failure here is a real regression).
python3 skills/design/scripts/validate_design.py \
  docs/requirements/examples/tamagotchi/design
python3 skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements

# The fallback path does not crash without pyyaml.
python3 -c "
import sys
for m in ('yaml', 'jsonschema'):
    sys.modules[m] = None
sys.path.insert(0, 'lib'); sys.path.insert(0, 'skills/design/scripts')
import lint_design_content as ldc
print('fallback findings:', len(ldc.lint_dir('docs/requirements/examples/tamagotchi/design')))
"
```

Ticket-completion criteria:

- The whole suite passes.
- All eight rules have a firing fixture and a near-miss fixture that stays clean.
- The M1 suite passes with only `test_json_output_is_parseable` edited.
- `lint_design_content.py` exits 0 over the shipped tamagotchi design set and
  reports exactly one `dependency-cycle` finding.
- `grep -rn "STO-208" agents/ skills/` turns up no text describing the linter as
  future work.

# Definition of Done Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the M1 `dod-generator` agent with `generate_dod.py`, a deterministic script that projects the requirements, design and QA artifact sets into `.sdlc/definition-of-done.md`, and invoke it from all three stage skills.

**Architecture:** A stdlib-only Python script reads YAML frontmatter (via `plugin/lib/artifact_core.py`) plus two fixed NFR body sections, and renders a Markdown checklist whose sections appear exactly when their input artifact sets do. Making those two body sections load-bearing means `validate_requirements.py` grows a gate for them. The agent file and the pseudo-handlebars template are deleted.

**Tech Stack:** Python 3 (stdlib only, per CLAUDE.md), pytest, Markdown + YAML frontmatter artifacts.

**Spec:** `docs/superpowers/specs/2026-09-07-sto-104-definition-of-done-design.md`

## Global Constraints

- **Python is stdlib-only, everywhere.** No new third-party imports. `pyyaml` and `jsonschema` are optional-with-fallback and are reached only through `artifact_core`; `generate_dod.py` must work when both are absent.
- **Output path is `.sdlc/definition-of-done.md`** — repo root of the `.sdlc/` tree, under no stage directory (spec D1).
- **No stage writes into a previous stage's directory.** The generator reads all three and writes only to the root path (spec E2).
- **Scripts are located by absolute path from the skill base.** Never a repo-relative path — `skills/…/scripts/…` resolves only inside a groundwork checkout. See each SKILL.md's "Locating the scripts".
- **`site/content/_generated/` is committed and CI fails on drift.** Deleting an agent changes `agents.json`; re-run `python3 site/scripts/export_reference.py`.
- **`python3 -m pytest -q` runs everything from the repository root.**
- **Exit codes:** `0` written, `1` an input the generator must parse is malformed, `2` usage / environment error. Mirrors `generate_c4.py`.

## Two refinements this plan makes to the spec

Both follow from spec decisions rather than departing from them; they are called out because the spec's section table does not spell them out.

1. **Section headings are unnumbered.** Spec D4's table numbers sections 1–7, but D3 makes sections conditional — a requirements-only DoD would read `1, 2, 5, 6`, which looks broken, and renumbering by presence makes every regeneration diff noisy. Headings are therefore names, not numbers (`## Functional Acceptance Gates`). Ordering is unchanged. This also suits STO-107, which slices by heading.

2. **Enforcement annotation degrades explicitly.** `[CI]` / `[manual]` / `[unenforced]` are derived from the QA items covering a requirement. With no QA stage on disk there is nothing to derive from, so gates carry `[verification: test]` (the requirement's own `verification_method`) instead. Claiming `[CI]` from `verification_method: test` would assert a pipeline nobody has seen.

---

## File Structure

**New**

| File | Responsibility |
|---|---|
| `plugin/skills/requirements/scripts/generate_dod.py` | Whole generator: load, parse, render, CLI |
| `tests/dod/conftest.py` | Put the scripts dir on `sys.path` |
| `tests/dod/test_generate_dod.py` | The suite |
| `tests/dod/fixtures/reqs_only/` | Requirements-only artifact set |
| `tests/dod/fixtures/full/` | Requirements + design + qa |
| `tests/dod/fixtures/invalid/<case>/` | One directory per exit-1 case |

**Modified**

| File | Change |
|---|---|
| `plugin/skills/requirements/scripts/validate_requirements.py` | NFR body-heading gate |
| `tests/requirements/fixtures/valid/non-functional/NFR-001-order-api-latency.md` | Gains the ISO heading the new gate requires |
| `plugin/skills/requirements/SKILL.md` | Step 5 becomes the script call |
| `plugin/skills/design/SKILL.md` | New Step 4c |
| `plugin/skills/qa/SKILL.md` | New Step 4c; sibling-script list gains an entry |
| `plugin/skills/requirements/scripts/README.md`, `plugin/skills/qa/scripts/README.md` | Document the generator |
| `site/content/architecture/index.mdx` | The "seventh agent" passage |
| `site/content/guide/requirements-stage.mdx` | Tree listing + derivation note |
| `site/content/guide/gates.mdx`, `site/content/guide/troubleshooting.mdx` | Path references |
| `site/scripts/export_examples.py` | Requirements file list + title map |
| `site/content/_generated/agents.json` | Regenerated |

**Deleted:** `plugin/agents/dod-generator.md`, `plugin/skills/requirements/templates/definition-of-done.md`

---

## Task 1: Script skeleton — loading, stage detection, document frame

**Files:**
- Create: `plugin/skills/requirements/scripts/generate_dod.py`
- Create: `tests/dod/conftest.py`, `tests/dod/test_generate_dod.py`
- Create: `tests/dod/fixtures/reqs_only/requirements/` (fixture set below)

**Interfaces:**
- Consumes: `artifact_core.parse_frontmatter`, `artifact_core.discover_files`
- Produces:
  - `class Artifact` with attributes `path: str`, `fm: Dict[str, Any]`, `body: str`, and property `id -> Optional[str]`
  - `load_set(root: str, skip: set) -> List[Artifact]`
  - `render_document(reqs, design, qa, title, today) -> str` — `reqs`/`design`/`qa` are `Optional[List[Artifact]]`; `None` means the stage is absent
  - `main(argv: Optional[List[str]] = None) -> int`

- [ ] **Step 1: Create the fixture set**

`tests/dod/fixtures/reqs_only/requirements/functional/FR-001-cancel-pending-order.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Cancel a pending order
description: When a customer requests cancellation of a pending order, the system shall cancel it and confirm within 5 seconds.
rationale: Customers abandon checkout when a mistaken order cannot be undone.
fit_criterion: 100% of cancellation requests against pending orders succeed within 5 seconds.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# FR-001 — Cancel a pending order

## Acceptance Criteria
Given a pending order, when the customer cancels, then the order is cancelled.
```

`tests/dod/fixtures/reqs_only/requirements/non-functional/NFR-001-order-api-latency.md`:

```markdown
---
id: NFR-001
type: non_functional
tier: solution
title: Order API latency
description: The Order API shall respond within a bounded latency budget under normal load.
rationale: Slow submission reduces checkout conversion.
fit_criterion: p95 <= 200 ms over a rolling 5-minute window.
priority: should
confidence: medium
verification_method: test
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# NFR-001 — Order API latency

## ISO 25010 Characteristic
Performance Efficiency → Time behavior

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated customer
- **Stimulus:** Submits an order via `POST /orders`
- **Environment:** Normal operations, load <= 80% capacity
- **Artifact:** Order API service
- **Response:** Order persisted and 201 returned
- **Response measure:** End-to-end latency <= 200 ms at p95 over a rolling
  5-minute window; error rate <= 0.1%
```

`tests/dod/fixtures/reqs_only/requirements/non-functional/NFR-002-audit-log-integrity.md`:

```markdown
---
id: NFR-002
type: non_functional
tier: solution
title: Audit log integrity
description: Order lifecycle events shall be recorded in a tamper-evident log.
rationale: Disputes are resolved from the audit trail.
fit_criterion: 100% of lifecycle events captured with actor, timestamp and outcome.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# NFR-002 — Audit log integrity

## ISO 25010 Characteristic
Security → Accountability

## Quality Attribute Scenario
- **Source of stimulus:** An order lifecycle event
- **Stimulus:** An order is placed, cancelled or fulfilled
- **Environment:** Normal operation
- **Artifact:** Audit logging subsystem
- **Response:** The event is appended immutably
- **Response measure:** 100% of events captured; 0 entries mutable after write
```

`tests/dod/fixtures/reqs_only/requirements/constraints/CON-001-oracle-19c.md`:

```markdown
---
id: CON-001
type: constraint
tier: solution
title: Oracle 19c is the system of record
description: The order store shall remain Oracle 19c for the life of this release.
rationale: Licensing and DBA capability are fixed for the fiscal year.
fit_criterion: 0 order-state writes target any store other than Oracle 19c.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# CON-001 — Oracle 19c is the system of record

## Description
Fixed for this release.
```

`tests/dod/fixtures/reqs_only/requirements/business-rules/BR-001-cancellation-window.md`:

```markdown
---
id: BR-001
type: business_rule
tier: business
title: Cancellation window closes at fulfilment
description: An order shall not be cancellable once fulfilment has begun.
rationale: Stock is committed at fulfilment and cannot be released.
fit_criterion: 0 cancellations succeed against an order in fulfilment.
priority: must
confidence: high
verification_method: test
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# BR-001 — Cancellation window closes at fulfilment

## Description
Fulfilment is the cut-off.
```

Plus two project companions the requirements validator gates, so the same fixture can be fed to it:

`tests/dod/fixtures/reqs_only/requirements/assumptions.md`:

```markdown
# Assumptions, Dependencies and Open Questions

## Assumptions
None identified.

## Dependencies
None identified.

## Open Questions
None identified.
```

`tests/dod/fixtures/reqs_only/requirements/glossary.md`:

```markdown
# Glossary

## Terms
None identified.
```

- [ ] **Step 2: Write `tests/dod/conftest.py`**

```python
"""Pytest configuration: make the generator module importable.

The tests live outside the plugin (STO-257) so their fixtures stop shipping to
every user, so the scripts directory is no longer an ancestor of this file and
has to be named. ``generate_dod`` itself adds ``plugin/lib/`` to the path when
imported, so the shared core still resolves.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(
    REPO_ROOT, "plugin", "skills", "requirements", "scripts"
)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
```

- [ ] **Step 3: Write the failing test**

`tests/dod/test_generate_dod.py`:

```python
"""Tests for the Definition of Done generator (STO-104)."""
import os

import pytest

import generate_dod as gd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
REQS_ONLY = os.path.join(FIXTURES, "reqs_only")


def generate(fixture_dir, tmp_path, **kwargs):
    """Run the CLI over a fixture tree; return (exit_code, document_text)."""
    out = os.path.join(str(tmp_path), "definition-of-done.md")
    argv = ["--out", out]
    for stage in ("requirements", "design", "qa"):
        stage_dir = os.path.join(fixture_dir, stage)
        if os.path.isdir(stage_dir):
            argv += [f"--{stage}", stage_dir]
    for key, value in kwargs.items():
        argv += [f"--{key.replace('_', '-')}", value]
    code = gd.main(argv)
    text = ""
    if os.path.isfile(out):
        with open(out, encoding="utf-8") as handle:
            text = handle.read()
    return code, text


def test_requirements_only_set_generates(tmp_path):
    code, text = generate(REQS_ONLY, tmp_path)
    assert code == 0
    assert text.startswith("# Definition of Done")


def test_header_names_the_stages_that_fed_it(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "requirements ✓" in text
    assert "design —" in text
    assert "qa —" in text


def test_title_flag_appears_when_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path, title="Order Cancellation")
    assert "**Project / feature:** Order Cancellation" in text


def test_title_line_omitted_when_not_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Project / feature" not in text


def test_missing_requirements_dir_is_usage_error(tmp_path):
    code = gd.main(["--requirements", str(tmp_path / "nope"),
                    "--out", str(tmp_path / "dod.md")])
    assert code == 2


def test_no_stages_at_all_is_usage_error(tmp_path):
    code = gd.main(["--out", str(tmp_path / "dod.md")])
    assert code == 2
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python3 -m pytest tests/dod -q`
Expected: collection error — `ModuleNotFoundError: No module named 'generate_dod'`

- [ ] **Step 5: Write the skeleton**

`plugin/skills/requirements/scripts/generate_dod.py`:

```python
#!/usr/bin/env python3
"""Deterministic Definition of Done generation for Groundwork (STO-104).

Every gate this tool emits is already stated somewhere in the artifact set: a
frontmatter field, or one of two fixed sections in an NFR body. So the DoD is a
projection of what the pipeline wrote, not a new authored document — the same
argument ``generate_c4.py`` makes for the C4 views, and the reason this
replaced the M1 ``dod-generator`` agent.

The output is written to ``.sdlc/definition-of-done.md``: root level, under no
stage directory, because the DoD is the one artifact no single stage owns. All
three stage skills run this tool and each run supersedes the last, so a project
that only ever runs ``/groundwork:requirements`` still gets a Definition of
Done — that is what the root path buys.

Sections appear exactly when their inputs do. A stage that was not run is
absent from the document and named as absent in the header, rather than
rendering an empty heading that reads as "nothing to do here".

Usage
-----
    python3 generate_dod.py --requirements DIR [--design DIR] [--qa DIR] \\
        --out .sdlc/definition-of-done.md [--title NAME] [--created-at DATE]

Exit codes
----------
    0  document written
    1  an artifact this tool must parse is malformed
    2  usage / environment error (no stage given, directory missing)
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from typing import Any, Dict, List, Optional

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import artifact_core as core  # noqa: E402
from artifact_core import parse_frontmatter  # noqa: E402

# Project-level companions that live beside atomic artifacts but are not ones.
SKIP_REQUIREMENTS = {
    "definition-of-done.md", "index.yaml", "assumptions.md", "glossary.md",
}
SKIP_DESIGN = {"index.yaml", "assumptions.md", "drivers.md"}
SKIP_QA = {"index.yaml", "qa-strategy.md"}
SKIP_DESIGN_DIRS = {"diagrams"}

GENERATED_BANNER = (
    "<!-- Generated by generate_dod.py. Do not hand-edit: change the source "
    "artifact under .sdlc/ and regenerate. -->"
)


class Artifact:
    """One parsed artifact: its frontmatter and its Markdown body."""

    __slots__ = ("path", "fm", "body")

    def __init__(self, path: str, fm: Dict[str, Any], body: str) -> None:
        self.path = path
        self.fm = fm
        self.body = body

    @property
    def id(self) -> Optional[str]:
        value = self.fm.get("id")
        return value if isinstance(value, str) else None

    @property
    def type(self) -> Optional[str]:
        value = self.fm.get("type")
        return value if isinstance(value, str) else None

    def get(self, key: str, default: Any = None) -> Any:
        return self.fm.get(key, default)


class GenerationError(Exception):
    """An artifact this tool must parse is malformed. Maps to exit 1."""


def _read_body(path: str) -> str:
    """Everything after the closing frontmatter fence."""
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    block = core.extract_frontmatter_block(text)
    if block is None:
        return text
    fence_end = text.index(block) + len(block)
    remainder = text[fence_end:]
    return remainder.split("---", 1)[1] if "---" in remainder else remainder


def load_set(root: str, skip: set, skip_dirs: set = frozenset()) -> List[Artifact]:
    """Every atomic artifact under ``root``, sorted by id.

    Raises GenerationError on unparseable frontmatter rather than skipping the
    file: a DoD that silently omits a requirement is claiming coverage it does
    not have, which is the failure mode this tool exists to prevent.
    """
    artifacts: List[Artifact] = []
    for path in core.discover_files(root, skip, skip_dirs):
        data, err = parse_frontmatter(path)
        if err:
            raise GenerationError(f"{os.path.relpath(path, root)}: {err}")
        artifacts.append(Artifact(path, data, _read_body(path)))
    return sorted(artifacts, key=lambda a: a.id or "")


def _stage_marker(present: bool) -> str:
    return "✓" if present else "—"


def render_document(
    reqs: Optional[List[Artifact]],
    design: Optional[List[Artifact]],
    qa: Optional[List[Artifact]],
    title: Optional[str],
    today: str,
) -> str:
    lines: List[str] = ["# Definition of Done", "", GENERATED_BANNER, ""]
    if title:
        lines.append(f"- **Project / feature:** {title}")
    lines.append(f"- **Generated:** {today}")
    lines.append(
        "- **Derived from:** "
        f"requirements {_stage_marker(reqs is not None)} · "
        f"design {_stage_marker(design is not None)} · "
        f"qa {_stage_marker(qa is not None)}"
    )
    lines += [
        "",
        "A work item is **Done** only when every gate below is satisfied.",
        "",
    ]
    lines += [
        "---",
        "",
        "*Generated from the artifact sets under `.sdlc/`. Change the source "
        "artifact and regenerate; do not edit this file.*",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Definition of Done from Groundwork artifact sets."
    )
    parser.add_argument("--requirements", default=None, help="Requirements dir.")
    parser.add_argument("--design", default=None, help="Design dir (optional).")
    parser.add_argument("--qa", default=None, help="QA dir (optional).")
    parser.add_argument("--out", required=True, help="Output path.")
    parser.add_argument("--title", default=None, help="Project or feature name.")
    parser.add_argument("--created-at", default=None, help="Override today's date.")
    args = parser.parse_args(argv)

    stages = {
        "requirements": args.requirements,
        "design": args.design,
        "qa": args.qa,
    }
    if not any(stages.values()):
        print(
            "ERROR: name at least one artifact directory "
            "(--requirements / --design / --qa)",
            file=sys.stderr,
        )
        return 2
    for name, path in stages.items():
        if path is not None and not os.path.isdir(path):
            print(f"ERROR: {name} directory not found: {path}", file=sys.stderr)
            return 2

    try:
        reqs = load_set(args.requirements, SKIP_REQUIREMENTS) if args.requirements else None
        design = (
            load_set(args.design, SKIP_DESIGN, SKIP_DESIGN_DIRS) if args.design else None
        )
        qa = load_set(args.qa, SKIP_QA) if args.qa else None
    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    today = args.created_at or datetime.date.today().isoformat()
    document = render_document(reqs, design, qa, args.title, today)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(document)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): generate_dod.py skeleton — loading, stage detection, document frame"
```

---

## Task 2: NFR body parsing — ISO characteristic and QAS bullets

The generator's only inputs that are not frontmatter. Spec E4 and D8.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`
- Create: `tests/dod/fixtures/invalid/nfr_missing_iso_heading/requirements/…`
- Create: `tests/dod/fixtures/invalid/nfr_missing_response_measure/requirements/…`

**Interfaces:**
- Produces:
  - `ISO_CHARACTERISTICS: frozenset` — the nine ISO/IEC 25010:2023 characteristics plus `Extension`
  - `parse_iso_characteristic(artifact: Artifact) -> str` — the head token; raises `GenerationError`
  - `parse_qas_field(artifact: Artifact, label: str) -> str` — one six-part bullet, continuation lines joined; raises `GenerationError` when the label is absent

- [ ] **Step 1: Write the failing tests**

Append to `tests/dod/test_generate_dod.py`:

```python
# ---------------------------------------------------------------------------
# NFR body parsing (spec E4, D8)
# ---------------------------------------------------------------------------
def _nfr(body):
    """An in-memory NFR artifact carrying only the body under test."""
    return gd.Artifact("NFR-999.md", {"id": "NFR-999", "type": "non_functional"}, body)


@pytest.mark.parametrize("line,expected", [
    ("Security → Confidentiality", "Security"),
    ("Reliability → Availability", "Reliability"),
    ("Performance Efficiency → Time behavior", "Performance Efficiency"),
    ("Functional Suitability → Functional completeness / correctness",
     "Functional Suitability"),
    ("Interaction Capability → Accessibility / Inclusivity",
     "Interaction Capability"),
    ("Compatibility → Interoperability", "Compatibility"),
    ("Flexibility → Adaptability", "Flexibility"),
    ("Maintainability → Analysability", "Maintainability"),
    ("Safety → Hazard warning", "Safety"),
    ("Extension: Observability", "Extension"),
    ("Extension: Deployability", "Extension"),
])
def test_iso_characteristic_head_token(line, expected):
    art = _nfr(f"\n## ISO 25010 Characteristic\n{line}\n\n## Quality Attribute Scenario\n")
    assert gd.parse_iso_characteristic(art) == expected


def test_iso_characteristic_tolerates_a_wrapped_line():
    art = _nfr(
        "\n## ISO 25010 Characteristic\n"
        "Extension: Observability (supporting Maintainability →\n"
        "Analysability)\n\n## Quality Attribute Scenario\n"
    )
    assert gd.parse_iso_characteristic(art) == "Extension"


def test_iso_characteristic_missing_heading_raises():
    with pytest.raises(gd.GenerationError):
        gd.parse_iso_characteristic(_nfr("\n# NFR-999\n\nNo heading here.\n"))


def test_iso_characteristic_unknown_head_raises():
    art = _nfr("\n## ISO 25010 Characteristic\nVibes → Good\n")
    with pytest.raises(gd.GenerationError):
        gd.parse_iso_characteristic(art)


def test_qas_response_measure_joins_continuation_lines():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Stimulus:** Submits an order\n"
        "- **Response measure:** End-to-end latency <= 200 ms at p95 over a\n"
        "  rolling 5-minute window; error rate <= 0.1%\n"
    )
    assert gd.parse_qas_field(art, "Response measure") == (
        "End-to-end latency <= 200 ms at p95 over a rolling 5-minute window; "
        "error rate <= 0.1%"
    )


def test_qas_field_stops_at_the_next_bullet():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Stimulus:** Submits an order\n"
        "- **Environment:** Normal operation\n"
    )
    assert gd.parse_qas_field(art, "Stimulus") == "Submits an order"


def test_qas_field_stops_at_the_next_heading():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Response measure:** Zero defects\n"
        "\n## Rationale\nBecause.\n"
    )
    assert gd.parse_qas_field(art, "Response measure") == "Zero defects"


def test_qas_missing_field_raises():
    art = _nfr("\n## Quality Attribute Scenario\n- **Stimulus:** Something\n")
    with pytest.raises(gd.GenerationError):
        gd.parse_qas_field(art, "Response measure")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/dod -q -k "iso or qas"`
Expected: FAIL — `AttributeError: module 'generate_dod' has no attribute 'parse_iso_characteristic'`

- [ ] **Step 3: Implement the parsers**

Insert into `generate_dod.py`, after the `_read_body` helper:

```python
# ---------------------------------------------------------------------------
# NFR body parsing
#
# Two sections of an NFR body are load-bearing here. Both are written by
# nfr-specialist.md for every NFR and are present in all 24 NFRs across both
# worked example sets; validate_requirements.py gates them so that a drift in
# the specialist's template fails at the validator rather than here.
# ---------------------------------------------------------------------------
ISO_HEADING = "## ISO 25010 Characteristic"

# The nine ISO/IEC 25010:2023 characteristics nfr-specialist.md walks, plus the
# "Extension:" prefix it uses for the four the standard omits (observability,
# deployability, compliance, cost). Only the head token is parsed: the text
# after the separator is free prose that wraps and carries parentheticals, so
# Extension: Observability and Extension: Compliance land in one bucket. That
# is deliberate — see spec D8.
ISO_CHARACTERISTICS = frozenset({
    "Functional Suitability",
    "Performance Efficiency",
    "Compatibility",
    "Interaction Capability",
    "Reliability",
    "Security",
    "Maintainability",
    "Flexibility",
    "Safety",
    "Extension",
})

_ISO_SECTION_RE = re.compile(
    r"^## ISO 25010 Characteristic\s*\n(.+?)(?=^##\s|\Z)", re.M | re.S
)
_QAS_SEPARATOR_RE = re.compile(r"→|->|:")


def parse_iso_characteristic(artifact: Artifact) -> str:
    """The head token of an NFR's ``## ISO 25010 Characteristic`` section."""
    match = _ISO_SECTION_RE.search(artifact.body)
    if not match:
        raise GenerationError(
            f"{artifact.id}: missing required heading '{ISO_HEADING}'"
        )
    text = " ".join(match.group(1).split())
    head = _QAS_SEPARATOR_RE.split(text, 1)[0].strip()
    if head not in ISO_CHARACTERISTICS:
        raise GenerationError(
            f"{artifact.id}: '{head}' is not an ISO 25010 characteristic or "
            f"an 'Extension'"
        )
    return head


def parse_qas_field(artifact: Artifact, label: str) -> str:
    """One six-part quality-attribute-scenario bullet, continuations joined.

    A bullet ends at the next bullet or the next heading, so a value wrapped
    across lines (which the specialist does routinely) survives intact.
    """
    pattern = re.compile(
        r"^-\s+\*\*" + re.escape(label) + r":\*\*\s*(.+?)(?=^-\s+\*\*|^#{1,6}\s|\Z)",
        re.M | re.S,
    )
    match = pattern.search(artifact.body)
    if not match:
        raise GenerationError(
            f"{artifact.id}: quality attribute scenario has no "
            f"'**{label}:**' bullet"
        )
    return " ".join(match.group(1).split())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed

- [ ] **Step 5: Add the two exit-1 fixtures**

`tests/dod/fixtures/invalid/nfr_missing_iso_heading/requirements/non-functional/NFR-001-no-iso.md` — copy `reqs_only`'s `NFR-001` exactly, then delete its `## ISO 25010 Characteristic` heading and the line under it.

`tests/dod/fixtures/invalid/nfr_missing_response_measure/requirements/non-functional/NFR-001-no-measure.md` — copy `reqs_only`'s `NFR-001` exactly, then delete only the `- **Response measure:**` bullet and its continuation line.

Both fixtures also need `assumptions.md` and `glossary.md` copied from `reqs_only/requirements/` so the same tree can be handed to the requirements validator.

- [ ] **Step 6: Add the invalid-case tests**

Append to `tests/dod/test_generate_dod.py`:

```python
# A fixture directory nobody parametrizes is a case nobody tests. This list and
# the guard below are the same pattern tests/qa/test_validate_qa.py uses.
INVALID_CASES = [
    "nfr_missing_iso_heading",
    "nfr_missing_response_measure",
]


@pytest.mark.parametrize("case", INVALID_CASES)
def test_invalid_fixture_exits_one(case, tmp_path):
    code, _ = generate(os.path.join(FIXTURES, "invalid", case), tmp_path)
    assert code == 1, f"expected exit 1 for fixture {case}"


def test_every_invalid_fixture_is_exercised():
    on_disk = sorted(
        d for d in os.listdir(os.path.join(FIXTURES, "invalid"))
        if os.path.isdir(os.path.join(FIXTURES, "invalid", d))
    )
    assert on_disk == sorted(INVALID_CASES)
```

These fail until Task 4 renders the NFR section (nothing calls the parsers yet). Mark them `@pytest.mark.xfail(reason="NFR section lands in Task 4", strict=True)` now and remove the marker in Task 4 Step 6.

- [ ] **Step 7: Run the suite**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed (the two invalid cases xfail as declared)

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): parse the two NFR body sections the DoD depends on"
```

---

## Task 3: Gate the NFR body sections in `validate_requirements.py`

The direct cost of Task 2: two body sections became a parsed contract, and a contract nothing enforces fails at generation time instead of validation time. Spec D8.

**Files:**
- Modify: `plugin/skills/requirements/scripts/validate_requirements.py`
- Modify: `tests/requirements/test_validate_requirements.py`
- Modify: `tests/requirements/fixtures/valid/non-functional/NFR-001-order-api-latency.md`
- Create: `tests/requirements/fixtures/invalid/nfr_missing_iso_heading/`
- Create: `tests/requirements/fixtures/invalid/nfr_missing_response_measure/`

**Interfaces:**
- Consumes: `core._check_project_artifact`'s heading-check shape (a model, not a call — that helper takes a filename, this check takes a parsed file)
- Produces: `REQUIRED_NFR_BODY = ["## ISO 25010 Characteristic", "## Quality Attribute Scenario"]` and a per-file check folded into `cross_file_checks`

- [ ] **Step 1: Write the failing test**

Append to `tests/requirements/test_validate_requirements.py`:

```python
# ---------------------------------------------------------------------------
# NFR body sections (STO-104): the DoD generator parses these, so they are gated
# ---------------------------------------------------------------------------
def test_nfr_missing_iso_heading_fails(capsys):
    code = run(os.path.join(INVALID_DIR, "nfr_missing_iso_heading"))
    out = capsys.readouterr().out
    assert code != 0
    assert "ISO 25010 Characteristic" in out


def test_nfr_missing_response_measure_fails(capsys):
    code = run(os.path.join(INVALID_DIR, "nfr_missing_response_measure"))
    out = capsys.readouterr().out
    assert code != 0
    assert "Response measure" in out


def test_functional_requirement_needs_no_nfr_body_sections(capsys):
    """The gate is NFR-only: an FR without a QAS is not a violation."""
    code = run(VALID_DIR)
    out = capsys.readouterr().out
    assert code == 0, out
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest tests/requirements -q -k nfr`
Expected: FAIL — the fixture directories do not exist

- [ ] **Step 3: Create the two invalid fixtures**

Copy the whole of `tests/requirements/fixtures/valid/` to each of
`tests/requirements/fixtures/invalid/nfr_missing_iso_heading/` and
`tests/requirements/fixtures/invalid/nfr_missing_response_measure/`, then in each copy edit `non-functional/NFR-001-order-api-latency.md`:

- in `nfr_missing_iso_heading/`, leave the body as it is today (it has no ISO heading — that is the case)
- in `nfr_missing_response_measure/`, delete the `- **Response measure:**` bullet and its continuation line

- [ ] **Step 4: Fix the valid fixture**

`tests/requirements/fixtures/valid/non-functional/NFR-001-order-api-latency.md` has no `## ISO 25010 Characteristic` heading and would start failing. Insert it above the existing `## Quality Attribute Scenario`:

```markdown
## ISO 25010 Characteristic
Performance Efficiency → Time behavior
```

- [ ] **Step 5: Implement the gate**

In `validate_requirements.py`, add beside the other heading constants (after `REQUIRED_GLOSSARY_HEADINGS`, around line 111):

```python
# Body sections of a non-functional requirement (STO-104). generate_dod.py
# parses both — the ISO characteristic head token drives the documentation and
# deployment-readiness sections, and the QAS response measure is the DoD's
# pass/fail oracle for every NFR fitness gate. Gated here so a drift in
# nfr-specialist.md's template fails at validation rather than at generation.
REQUIRED_NFR_BODY_HEADINGS = [
    "## ISO 25010 Characteristic",
    "## Quality Attribute Scenario",
]
REQUIRED_NFR_QAS_BULLET = "Response measure"
```

Add the check function beside `check_glossary_artifact`:

```python
def check_nfr_body_sections(files: List[RequirementFile]) -> None:
    """Gate the two NFR body sections generate_dod.py parses.

    Per-file rather than set-level, so the failure names the file. Presence
    only — the prose inside each section is never gated, matching the rule the
    project-artifact gates already follow.
    """
    for f in files:
        fm = f.frontmatter
        if not isinstance(fm, dict) or fm.get("type") != "non_functional":
            continue
        try:
            with open(f.path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            f.errors.append(f"could not read body: {exc}")
            continue
        for heading in REQUIRED_NFR_BODY_HEADINGS:
            if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
                f.errors.append(
                    f"non-functional requirement missing required heading "
                    f"'{heading}'"
                )
        if not re.search(
            rf"^-\s+\*\*{re.escape(REQUIRED_NFR_QAS_BULLET)}:\*\*", text, re.MULTILINE
        ):
            f.errors.append(
                f"quality attribute scenario missing "
                f"'**{REQUIRED_NFR_QAS_BULLET}:**' bullet"
            )
```

Add `import re` to the module imports if it is not already there, and call the check inside `validate`, immediately after the per-file loop and before `cross_file_checks`:

```python
    check_nfr_body_sections(files)
    global_errors = cross_file_checks(files)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest tests/requirements -q`
Expected: all passed

- [ ] **Step 7: Run the whole suite — worked-example sets are validated by CI**

Run: `python3 -m pytest -q`
Expected: all passed. If a worked-example NFR trips the new gate, that is a real finding — record it and fix the artifact, do not weaken the gate.

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/requirements/scripts/validate_requirements.py tests/requirements/
git commit -m "feat(sto-104): gate the two NFR body sections the DoD generator parses"
```

---

## Task 4: Functional acceptance and NFR fitness gates

The requirements-only DoD becomes real. Spec D4 sections 1 and 2.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`

**Interfaces:**
- Consumes: `Artifact`, `parse_qas_field`, `parse_iso_characteristic` (Task 2)
- Produces:
  - `enforcement_tag(req: Artifact, covering: List[Artifact], qa_present: bool) -> str` — one of `` `[CI]` ``, `` `[manual]` ``, `` `[unenforced]` ``, `` `[uncovered]` ``, or `` `[verification: <method>]` `` when `qa_present` is False
  - `render_functional_gates(reqs, coverage, qa_present) -> List[str]`
  - `render_nfr_gates(reqs, coverage, qa_present) -> List[str]`
  - `coverage_map(qa: Optional[List[Artifact]]) -> Dict[str, List[Artifact]]` — requirement/design id → the TS items citing it
  - `by_type(reqs, *types) -> List[Artifact]`

- [ ] **Step 1: Write the failing tests**

Append to `tests/dod/test_generate_dod.py`:

```python
# ---------------------------------------------------------------------------
# Functional acceptance + NFR fitness gates (spec D4)
# ---------------------------------------------------------------------------
def test_functional_section_has_one_gate_per_fr(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Functional Acceptance Gates" in text
    assert "**FR-001 — Cancel a pending order** (must)" in text


def test_functional_gate_carries_fit_criterion_and_source(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "100% of cancellation requests against pending orders succeed" in text
    assert "functional/FR-001-cancel-pending-order.md" in text


def test_functional_gate_does_not_inline_gherkin(tmp_path):
    """DoD is product-wide; acceptance criteria are item-specific and stay in
    the FR file. Referenced, never duplicated."""
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Given a pending order" not in text


def test_nfr_gate_uses_the_response_measure_as_the_oracle(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## NFR Fitness Gates" in text
    assert "Response measure: End-to-end latency <= 200 ms at p95" in text


def test_nfr_gate_names_the_scenario(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Submits an order via `POST /orders`" in text
    assert "Order API service" in text


def test_without_qa_gates_annotate_verification_method(tmp_path):
    """No QA set on disk means no evidence about CI, so the gate says what the
    requirement claims rather than asserting a pipeline nobody has seen."""
    _, text = generate(REQS_ONLY, tmp_path)
    assert "`[verification: test]`" in text
    assert "`[CI]`" not in text
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m pytest tests/dod -q -k "functional_section or nfr_gate or verification"`
Expected: FAIL — assertions on absent headings

- [ ] **Step 3: Implement**

Add to `generate_dod.py` before `render_document`:

```python
# ---------------------------------------------------------------------------
# Gate rendering
# ---------------------------------------------------------------------------
def by_type(artifacts: Optional[List[Artifact]], *types: str) -> List[Artifact]:
    if not artifacts:
        return []
    return [a for a in artifacts if a.type in types]


def coverage_map(qa: Optional[List[Artifact]]) -> Dict[str, List[Artifact]]:
    """requirement/design id -> the TS items whose traces_from cites it."""
    out: Dict[str, List[Artifact]] = {}
    for item in by_type(qa, "test_strategy"):
        for target in item.get("traces_from") or []:
            out.setdefault(str(target), []).append(item)
    return out


def enforcement_tag(
    req: Artifact, covering: List[Artifact], qa_present: bool
) -> str:
    """How strongly this requirement's gate is actually checked.

    With a QA set on disk the answer is derived from the items covering it.
    Without one there is nothing to derive from, so the tag reports the
    requirement's own verification_method instead of claiming a pipeline.
    """
    if not qa_present:
        return f"`[verification: {req.get('verification_method', 'unspecified')}]`"
    if not covering:
        return "`[uncovered]`"
    levels = {str(item.get("enforcement")) for item in covering}
    if "ci" in levels:
        return "`[CI]`"
    if "manual" in levels:
        return "`[manual]`"
    return "`[unenforced]`"


def _rel_source(artifact: Artifact, root: str, stage_dir: str) -> str:
    return f"`{stage_dir}/{os.path.relpath(artifact.path, root)}`"


def render_functional_gates(
    reqs: List[Artifact], root: str, coverage: Dict[str, List[Artifact]],
    qa_present: bool,
) -> List[str]:
    items = by_type(reqs, "functional")
    if not items:
        return []
    lines = [
        "## Functional Acceptance Gates",
        "",
        "One gate per functional requirement. The linked file holds the "
        "authoritative acceptance criteria; they are referenced here, never "
        "duplicated.",
        "",
    ]
    for req in items:
        tag = enforcement_tag(req, coverage.get(req.id or "", []), qa_present)
        lines += [
            f"- [ ] **{req.id} — {req.get('title')}** "
            f"({req.get('priority')}) {tag}",
            "  All acceptance-criteria scenarios in the source file pass.",
            f"  Fit criterion: {req.get('fit_criterion')}",
            f"  Source: {_rel_source(req, root, '.sdlc/requirements')}",
            "",
        ]
    return lines


def render_nfr_gates(
    reqs: List[Artifact], root: str, coverage: Dict[str, List[Artifact]],
    qa_present: bool,
) -> List[str]:
    items = by_type(reqs, "non_functional")
    if not items:
        return []
    lines = [
        "## NFR Fitness Gates",
        "",
        "The quality attribute scenario's response measure is the pass/fail "
        "oracle for each gate below.",
        "",
    ]
    for req in items:
        tag = enforcement_tag(req, coverage.get(req.id or "", []), qa_present)
        measure = parse_qas_field(req, "Response measure")
        stimulus = parse_qas_field(req, "Stimulus")
        artifact_under_test = parse_qas_field(req, "Artifact")
        environment = parse_qas_field(req, "Environment")
        lines += [
            f"- [ ] **{req.id} — {req.get('title')}** "
            f"({req.get('priority')}) {tag}",
            f"  Response measure: {measure}",
            f"  Scenario: *{stimulus}* on *{artifact_under_test}* "
            f"under *{environment}*.",
            f"  Source: {_rel_source(req, root, '.sdlc/requirements')}",
            "",
        ]
    return lines
```

Then thread them through `render_document`. Change its signature to take the roots, and insert the sections before the closing rule:

```python
def render_document(
    reqs: Optional[List[Artifact]],
    design: Optional[List[Artifact]],
    qa: Optional[List[Artifact]],
    title: Optional[str],
    today: str,
    roots: Dict[str, str],
) -> str:
    ...  # header as before
    coverage = coverage_map(qa)
    qa_present = qa is not None
    body: List[str] = []
    if reqs:
        body += render_functional_gates(reqs, roots["requirements"], coverage, qa_present)
        body += render_nfr_gates(reqs, roots["requirements"], coverage, qa_present)
    lines += body
    lines += ["---", "", "*Generated from the artifact sets under `.sdlc/`. …*"]
    return "\n".join(lines) + "\n"
```

And in `main`, build `roots` from the parsed args and pass it:

```python
    roots = {k: v for k, v in stages.items() if v}
    document = render_document(reqs, design, qa, args.title, today, roots)
```

`parse_qas_field` raises `GenerationError`, which `main` already catches — but the call now happens inside `render_document`, so move the `render_document` call inside the existing `try` block.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q -k "functional or nfr_gate or verification"`
Expected: PASS

- [ ] **Step 5: Remove the xfail markers from Task 2 Step 6**

The two invalid fixtures now reach the parsers through `render_nfr_gates`, so delete the `@pytest.mark.xfail(...)` decorator added in Task 2.

- [ ] **Step 6: Run the suite**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed, no xfail

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): functional acceptance and NFR fitness gates"
```

---

## Task 5: Architectural conformance gates

Spec D6: accepted ADRs and the declared `depends_on` edges. Nothing invented, because per E3 there is nothing else in `design.schema.json` to read.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`
- Create: `tests/dod/fixtures/full/` (requirements copied from `reqs_only`, plus `design/`)

**Interfaces:**
- Produces: `render_conformance_gates(design: List[Artifact], root: str) -> List[str]`

- [ ] **Step 1: Build the `full` fixture's requirements and design halves**

Copy `tests/dod/fixtures/reqs_only/requirements/` to `tests/dod/fixtures/full/requirements/` unchanged.

`tests/dod/fixtures/full/design/adr/ADR-001-oracle-as-the-order-store.md`:

```markdown
---
id: ADR-001
type: adr
title: Oracle as the order store
description: Whether order state lives in Oracle 19c or moves to a document store.
traces_from: [CON-001]
traces_to: {}
status: draft
confidence: high
created_at: '2026-09-07'
decision_status: accepted
considered_options:
- Oracle 19c as the system of record
- A document store fronting Oracle
chosen_option: Oracle 19c as the system of record
---

# ADR-001: Oracle as the order store

## Context and Problem Statement
CON-001 fixes the store for this release.
```

`tests/dod/fixtures/full/design/adr/ADR-002-rejected-event-sourcing.md` — identical shape, `id: ADR-002`, `title: Event sourcing for order state`, `decision_status: rejected`, `chosen_option: Direct state mutation`. This is the negative case: a rejected ADR must not become a gate.

`tests/dod/fixtures/full/design/components/CMP-001-order-service.md`:

```markdown
---
id: CMP-001
type: component
title: Order Service
description: Owns order state transitions and the cancellation rule.
traces_from: [FR-001, BR-001]
traces_to:
  adr: [ADR-001]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-09-07'
responsibility: Owns order state transitions.
boundary: internal
depends_on: [IF-001]
---

# CMP-001 — Order Service

## Responsibility
Owns order state transitions.
```

`tests/dod/fixtures/full/design/components/CMP-002-notification-adapter.md` — same shape, `id: CMP-002`, `title: Notification Adapter`, `boundary: external`, `depends_on: []`. The negative case for the dependency gate: nothing to assert, so no gate.

`tests/dod/fixtures/full/design/interfaces/IF-001-order-store-port.md`:

```markdown
---
id: IF-001
type: interface
title: Order store port
description: The persistence contract the Order Service depends on.
traces_from: [FR-001]
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-09-07'
provider: CMP-001
operations:
- name: save
  interaction: synchronous
error_modes:
- Write conflict on concurrent cancellation
---

# IF-001 — Order store port

## Operations
Described above.
```

- [ ] **Step 2: Write the failing tests**

```python
FULL = os.path.join(FIXTURES, "full")


# ---------------------------------------------------------------------------
# Architectural conformance (spec D6)
# ---------------------------------------------------------------------------
def test_accepted_adr_becomes_a_conformance_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Architectural Conformance Gates" in text
    assert "**ADR-001 — Oracle as the order store**" in text
    assert "Oracle 19c as the system of record" in text


def test_rejected_adr_is_not_a_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "ADR-002" not in text


def test_component_dependency_edges_become_a_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "**CMP-001 — Order Service**" in text
    assert "IF-001" in text


def test_component_without_dependencies_has_no_gate(tmp_path):
    """Nothing to assert is not the same as an empty assertion."""
    _, text = generate(FULL, tmp_path)
    assert "CMP-002" not in text


def test_conformance_section_absent_without_a_design_set(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Architectural Conformance Gates" not in text
```

- [ ] **Step 3: Run to verify they fail**

Run: `python3 -m pytest tests/dod -q -k "adr or component or conformance"`
Expected: FAIL

- [ ] **Step 4: Implement**

```python
def render_conformance_gates(design: List[Artifact], root: str) -> List[str]:
    """Accepted decisions and declared dependency edges.

    Not "fitness functions": design.schema.json carries no threshold, target or
    measure anywhere. A fitness function has a measure; these have a rule. The
    measurable architecture gates are the NFR fitness gates above.
    """
    adrs = [
        a for a in by_type(design, "adr")
        if a.get("decision_status") == "accepted"
    ]
    components = [
        c for c in by_type(design, "component") if c.get("depends_on")
    ]
    if not adrs and not components:
        return []
    lines = [
        "## Architectural Conformance Gates",
        "",
        "Decisions the implementation must not quietly reverse, and the "
        "dependency edges the design declared.",
        "",
    ]
    for adr in adrs:
        lines += [
            f"- [ ] **{adr.id} — {adr.get('title')}** `[manual]`",
            f"  The implementation conforms to the chosen option: "
            f"{adr.get('chosen_option')}",
            f"  Source: {_rel_source(adr, root, '.sdlc/design')}",
            "",
        ]
    for cmp_ in components:
        edges = ", ".join(str(d) for d in cmp_.get("depends_on") or [])
        lines += [
            f"- [ ] **{cmp_.id} — {cmp_.get('title')}** `[manual]`",
            f"  Depends on nothing outside its declared interfaces: {edges}.",
            f"  Source: {_rel_source(cmp_, root, '.sdlc/design')}",
            "",
        ]
    return lines
```

Call it in `render_document`, after the NFR gates:

```python
    if design:
        body += render_conformance_gates(design, roots["design"])
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): architectural conformance gates from accepted ADRs and depends_on"
```

---

## Task 6: Test coverage and the Declared Unenforced register

Spec D5 and D7. Coverage is derived from `TS-` `traces_from`, not re-checked — `validate_traceability.py` stays the one place the rule is enforced.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`
- Create: `tests/dod/fixtures/full/qa/`

**Interfaces:**
- Produces:
  - `render_coverage(reqs, coverage, root) -> List[str]`
  - `render_unenforced(qa, root) -> List[str]`

- [ ] **Step 1: Build the `full` fixture's QA half**

`tests/dod/fixtures/full/qa/strategy/TS-001-cancellation-state-machine.md`:

```markdown
---
id: TS-001
type: test_strategy
title: Cancellation state machine unit boundary
description: Exercises the cancellation state machine in isolation.
test_level: unit
risk_level: medium
risk_rationale: Cancellation is reversible and fails loudly.
enforcement: ci
traces_from: [FR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: '2026-09-07'
---

# TS-001 — Cancellation state machine unit boundary

Body prose.
```

`tests/dod/fixtures/full/qa/strategy/TS-002-order-api-latency-fitness.md` — `test_level: performance`, `risk_level: high`, `enforcement: ci`, `traces_from: [NFR-001]`.

`tests/dod/fixtures/full/qa/strategy/TS-003-audit-log-inspection.md` — `test_level: security`, `risk_level: high`, `risk_rationale: A mutable audit trail is undetectable from inside the system.`, `enforcement: manual`, `traces_from: [NFR-002]`.

`tests/dod/fixtures/full/qa/strategy/TS-004-fulfilment-cutoff-review.md` — `test_level: integration`, `risk_level: low`, `risk_rationale: The cut-off is a single conditional and rarely changes.`, `enforcement: none`, `traces_from: [BR-001]`.

`tests/dod/fixtures/full/qa/qa-strategy.md` — the projected document. Copy `tests/qa/fixtures/valid/qa-strategy.md` and adjust the item IDs; the generator skips it (`SKIP_QA`), but its presence makes the fixture a realistic QA directory.

Note `CON-001` is deliberately cited by no TS item: it is the uncovered case.

- [ ] **Step 2: Write the failing tests**

```python
# ---------------------------------------------------------------------------
# Coverage + declared-unenforced register (spec D5, D7)
# ---------------------------------------------------------------------------
def test_coverage_lists_the_items_covering_each_requirement(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Test Coverage" in text
    assert "TS-001" in text
    assert "TS-002" in text


def test_uncovered_requirement_is_visible_as_a_gap(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "no test-strategy item cites this requirement" in text


def test_enforcement_tag_is_derived_from_covering_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "**FR-001 — Cancel a pending order** (must) `[CI]`" in text
    assert "**NFR-002 — Audit log integrity** (must) `[manual]`" in text


def test_unenforced_items_get_their_own_register(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Declared Unenforced" in text
    assert "TS-004" in text
    assert "The cut-off is a single conditional" in text


def test_unenforced_register_is_not_a_checklist(tmp_path):
    """A register records what is not gated; a checkbox would imply it is."""
    _, text = generate(FULL, tmp_path)
    register = text.split("## Declared Unenforced", 1)[1]
    assert "- [ ]" not in register.split("---")[0]


def test_unenforced_section_absent_when_nothing_is_unenforced(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Declared Unenforced" not in text
```

- [ ] **Step 3: Run to verify they fail**

Run: `python3 -m pytest tests/dod -q -k "coverage or unenforced or enforcement_tag"`
Expected: FAIL

- [ ] **Step 4: Implement**

```python
def render_coverage(
    reqs: List[Artifact], coverage: Dict[str, List[Artifact]], root: str
) -> List[str]:
    """Which test-strategy items cite each requirement.

    Derivation, not enforcement. validate_traceability.py's uncovered-fr and
    uncovered-asr rules own the gate over this same edge; rendering it here
    twice would put the rule in two places.
    """
    items = by_type(reqs, "functional", "non_functional", "constraint", "business_rule")
    if not items:
        return []
    lines = [
        "## Test Coverage",
        "",
        "Derived from each test-strategy item's `traces_from`. A requirement "
        "no item cites is a gap, not a pass.",
        "",
    ]
    for req in items:
        covering = coverage.get(req.id or "", [])
        if covering:
            described = ", ".join(
                f"{item.id} ({item.get('test_level')}, {item.get('enforcement')})"
                for item in sorted(covering, key=lambda a: a.id or "")
            )
            lines.append(f"- [ ] **{req.id}** — covered by {described}")
        else:
            lines.append(
                f"- [ ] **{req.id}** — **no test-strategy item cites this "
                f"requirement**"
            )
    lines.append("")
    return lines


def render_unenforced(qa: List[Artifact], root: str) -> List[str]:
    """Items that declared themselves unenforced.

    A DoD that lists every gate but drops the items marked `enforcement: none`
    is claiming coverage the project does not have. Not a checklist: there is
    nothing here for anyone to tick.
    """
    items = [
        a for a in by_type(qa, "test_strategy") if a.get("enforcement") == "none"
    ]
    if not items:
        return []
    lines = [
        "## Declared Unenforced",
        "",
        "Test strategy the project decided not to enforce. Recorded so the "
        "coverage claimed above is not read as coverage delivered.",
        "",
    ]
    for item in items:
        covers = ", ".join(str(t) for t in item.get("traces_from") or [])
        lines += [
            f"- **{item.id} — {item.get('title')}** "
            f"(`{item.get('test_level')}`, risk: {item.get('risk_level')})",
            f"  Rationale: {item.get('risk_rationale')}",
            f"  Covers: {covers}. Source: {_rel_source(item, root, '.sdlc/qa')}",
            "",
        ]
    return lines
```

Wire both into `render_document`, after the conformance gates:

```python
    if qa:
        if reqs:
            body += render_coverage(reqs, coverage, roots["requirements"])
        body += render_unenforced(qa, roots["qa"])
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): test coverage derivation and the declared-unenforced register"
```

---

## Task 7: Documentation and deployment readiness

Spec D4 sections 5 and 6, keyed to the ISO characteristic head token from Task 2.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`

**Interfaces:**
- Produces:
  - `nfrs_by_characteristic(reqs) -> Dict[str, List[Artifact]]`
  - `render_documentation(reqs, by_char) -> List[str]`
  - `render_deployment(reqs, by_char) -> List[str]`

- [ ] **Step 1: Write the failing tests**

```python
# ---------------------------------------------------------------------------
# Documentation + deployment readiness (spec D4)
# ---------------------------------------------------------------------------
def test_documentation_section_lists_must_frs(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Documentation Requirements" in text
    docs = text.split("## Documentation Requirements", 1)[1]
    assert "FR-001" in docs


def test_documentation_section_lists_operational_nfrs(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    docs = text.split("## Documentation Requirements", 1)[1]
    assert "NFR-002 (Security)" in docs


def test_deployment_section_lists_security_nfrs_and_rules(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Deployment / Operational Readiness" in text
    deploy = text.split("## Deployment / Operational Readiness", 1)[1]
    assert "NFR-002" in deploy
    assert "CON-001" in deploy
    assert "BR-001" in deploy


def test_non_operational_nfr_is_not_a_deployment_gate(tmp_path):
    """NFR-001 is Performance Efficiency — neither Security nor Reliability."""
    _, text = generate(REQS_ONLY, tmp_path)
    deploy = text.split("## Deployment / Operational Readiness", 1)[1]
    security_line = [
        line for line in deploy.splitlines() if "Security NFR gates" in line
    ][0]
    assert "NFR-001" not in security_line
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m pytest tests/dod -q -k "documentation or deployment or operational"`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Characteristics whose NFRs need runbook or configuration notes. "Extension"
# is taken wholesale: only the head token is parsed, so Observability,
# Deployability, Compliance and Cost share one bucket (spec D8).
DOC_CHARACTERISTICS = ("Security", "Reliability", "Extension")
DEPLOY_CHARACTERISTICS = ("Security", "Reliability")


def nfrs_by_characteristic(reqs: List[Artifact]) -> Dict[str, List[Artifact]]:
    out: Dict[str, List[Artifact]] = {}
    for req in by_type(reqs, "non_functional"):
        out.setdefault(parse_iso_characteristic(req), []).append(req)
    return out


def _id_list(artifacts: List[Artifact], with_characteristic: Optional[str] = None) -> str:
    if not artifacts:
        return "none"
    if with_characteristic:
        return ", ".join(f"{a.id} ({with_characteristic})" for a in artifacts)
    return ", ".join(str(a.id) for a in artifacts)


def _chars(by_char: Dict[str, List[Artifact]], names) -> List[str]:
    parts: List[str] = []
    for name in names:
        for req in by_char.get(name, []):
            parts.append(f"{req.id} ({name})")
    return parts


def render_documentation(
    reqs: List[Artifact], by_char: Dict[str, List[Artifact]]
) -> List[str]:
    must_frs = [r for r in by_type(reqs, "functional") if r.get("priority") == "must"]
    operational = _chars(by_char, DOC_CHARACTERISTICS)
    return [
        "## Documentation Requirements",
        "",
        f"- [ ] Public-facing behaviour of every `must` functional requirement "
        f"is documented: {_id_list(must_frs)}.",
        f"- [ ] Operational NFRs have runbook or configuration notes: "
        f"{', '.join(operational) if operational else 'none'}.",
        "- [ ] Every implemented artifact carries `status: implemented` (or "
        "`verified`) and a populated `traces_to.code`.",
        "",
    ]


def render_deployment(
    reqs: List[Artifact], by_char: Dict[str, List[Artifact]]
) -> List[str]:
    security = by_char.get("Security", [])
    reliability = by_char.get("Reliability", [])
    rules = by_type(reqs, "constraint", "business_rule")
    return [
        "## Deployment / Operational Readiness",
        "",
        f"- [ ] Security NFR gates pass before release: {_id_list(security)}.",
        f"- [ ] Reliability targets are met or have an accepted waiver: "
        f"{_id_list(reliability)}.",
        "- [ ] Observability is in place for the response measures asserted "
        "above.",
        f"- [ ] Constraints and business rules hold in the deployed "
        f"configuration: {_id_list(rules)}.",
        "",
    ]
```

Wire into `render_document`, after the coverage and unenforced sections:

```python
    if reqs:
        by_char = nfrs_by_characteristic(reqs)
        body += render_documentation(reqs, by_char)
        body += render_deployment(reqs, by_char)
```

`nfrs_by_characteristic` calls `parse_iso_characteristic`, which raises `GenerationError` — already inside `main`'s `try`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): documentation and deployment readiness sections"
```

---

## Task 8: The `## PR Checklist` section

The reason the artifact is usable in a pull request. Spec D4. Must come last among the rendering tasks: it selects from every other section.

**Files:**
- Modify: `plugin/skills/requirements/scripts/generate_dod.py`
- Modify: `tests/dod/test_generate_dod.py`

**Interfaces:**
- Produces: `render_pr_checklist(reqs, design, qa, coverage, by_char, qa_present) -> List[str]`

- [ ] **Step 1: Write the failing tests**

```python
# ---------------------------------------------------------------------------
# PR checklist (spec D4)
# ---------------------------------------------------------------------------
def _pr_section(text):
    body = text.split("## PR Checklist", 1)[1]
    return body.split("\n## ", 1)[0]


def test_pr_checklist_leads_the_document(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert text.index("## PR Checklist") < text.index("## Functional Acceptance Gates")


def test_pr_checklist_carries_manual_qa_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "TS-003" in _pr_section(text)


def test_pr_checklist_omits_ci_enforced_items(tmp_path):
    """A passing build is their evidence; a checkbox would ask for it twice."""
    _, text = generate(FULL, tmp_path)
    section = _pr_section(text)
    assert "TS-001" not in section
    assert "TS-002" not in section


def test_pr_checklist_omits_unenforced_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "TS-004" not in _pr_section(text)


def test_pr_checklist_carries_non_test_nfrs(tmp_path):
    """NFR-002 is verification_method: inspection — a human records evidence."""
    _, text = generate(REQS_ONLY, tmp_path)
    section = _pr_section(text)
    assert "NFR-002" in section
    assert "NFR-001" not in section


def test_pr_checklist_carries_accepted_adrs(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "ADR-001" in _pr_section(text)


def test_pr_checklist_carries_a_documentation_line(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Documentation updated" in _pr_section(text)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m pytest tests/dod -q -k pr_checklist`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
NON_TEST_METHODS = ("inspection", "analysis", "demonstration")


def render_pr_checklist(
    reqs: Optional[List[Artifact]],
    design: Optional[List[Artifact]],
    qa: Optional[List[Artifact]],
) -> List[str]:
    """Only what a human must personally confirm.

    What separates the pasteable checklist from the traceable artifact is
    already in the data: a gate CI enforces needs a passing build, not a
    checkbox. Everything with automated evidence is left to the sections below.

    STO-107 slices this heading into the repository's PR template, so the
    heading text is a contract.
    """
    lines = [
        "## PR Checklist",
        "",
        "Everything below needs a person. CI-enforced gates are not listed — "
        "a passing build is their evidence.",
        "",
    ]
    entries: List[str] = []

    for item in by_type(qa, "test_strategy"):
        if item.get("enforcement") == "manual":
            entries.append(
                f"- [ ] **{item.id}** — {item.get('title')} "
                f"(`{item.get('test_level')}`, manual)."
            )

    for req in by_type(reqs, "non_functional"):
        if req.get("verification_method") in NON_TEST_METHODS:
            entries.append(
                f"- [ ] **{req.id}** — {req.get('title')}: evidence "
                f"recorded ({req.get('verification_method')})."
            )

    for adr in by_type(design, "adr"):
        if adr.get("decision_status") == "accepted":
            entries.append(
                f"- [ ] **{adr.id}** — implementation conforms to "
                f"“{adr.get('chosen_option')}”."
            )

    must_frs = [r for r in by_type(reqs, "functional") if r.get("priority") == "must"]
    if must_frs:
        entries.append(
            f"- [ ] Documentation updated for "
            f"{', '.join(str(r.id) for r in must_frs)}."
        )

    if not entries:
        entries.append("- [ ] Nothing requires manual confirmation.")

    lines += entries + [""]
    return lines
```

Insert into `render_document` as the first body section, before the functional gates:

```python
    body: List[str] = []
    body += render_pr_checklist(reqs, design, qa)
    if reqs:
        body += render_functional_gates(...)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/dod -q`
Expected: all passed

- [ ] **Step 5: Add the stage-degradation monotonicity test**

```python
def test_gate_count_only_grows_as_stages_are_added(tmp_path):
    """Spec D3: each stage's run supersedes the last and adds gates. A stage
    that removed gates would mean a later run had less information, which
    cannot happen."""
    reqs_only_dir = os.path.join(str(tmp_path), "r")
    os.makedirs(reqs_only_dir)
    out_a = os.path.join(str(tmp_path), "a.md")
    out_b = os.path.join(str(tmp_path), "b.md")
    full_reqs = os.path.join(FULL, "requirements")

    assert gd.main(["--requirements", full_reqs, "--out", out_a]) == 0
    assert gd.main([
        "--requirements", full_reqs,
        "--design", os.path.join(FULL, "design"),
        "--qa", os.path.join(FULL, "qa"),
        "--out", out_b,
    ]) == 0

    def gates(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read().count("- [ ] ")

    assert gates(out_b) > gates(out_a)
```

- [ ] **Step 6: Run the suite**

Run: `python3 -m pytest -q`
Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/requirements/scripts/generate_dod.py tests/dod/
git commit -m "feat(sto-104): the PR checklist section STO-107 will slice"
```

---

## Task 9: Wire the three skills; delete the agent and template

**Files:**
- Modify: `plugin/skills/requirements/SKILL.md:266-270`
- Modify: `plugin/skills/design/SKILL.md` (new step before `**Step 5 — Commit:**`, line 451)
- Modify: `plugin/skills/qa/SKILL.md` (new step before `**Step 5 — Commit:**`, line 373; sibling list at lines 55-63)
- Modify: `plugin/skills/requirements/scripts/README.md`, `plugin/skills/qa/scripts/README.md`
- Delete: `plugin/agents/dod-generator.md`, `plugin/skills/requirements/templates/definition-of-done.md`

- [ ] **Step 1: Write the failing test**

Append to `tests/dod/test_generate_dod.py`:

```python
# ---------------------------------------------------------------------------
# Wiring: every stage skill must invoke the generator, and the agent must be
# gone. A skill that stops calling it leaves a stale DoD on disk, which is the
# failure this ticket exists to end.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
PLUGIN = os.path.join(REPO_ROOT, "plugin")


@pytest.mark.parametrize("stage", ["requirements", "design", "qa"])
def test_every_stage_skill_invokes_the_generator(stage):
    path = os.path.join(PLUGIN, "skills", stage, "SKILL.md")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    assert "generate_dod.py" in text, f"{stage} SKILL.md does not run generate_dod.py"
    assert ".sdlc/definition-of-done.md" in text


def test_dod_generator_agent_is_gone():
    assert not os.path.exists(os.path.join(PLUGIN, "agents", "dod-generator.md"))


def test_dod_template_is_gone():
    assert not os.path.exists(
        os.path.join(PLUGIN, "skills", "requirements", "templates",
                     "definition-of-done.md")
    )
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m pytest tests/dod -q -k "stage_skill or agent_is_gone or template_is_gone"`
Expected: FAIL on all five

- [ ] **Step 3: Replace the requirements skill's step 5**

In `plugin/skills/requirements/SKILL.md`, replace the `**Step 5 — Generate the Definition of Done stub:**` block with:

````markdown
**Step 5 — Generate the Definition of Done:**

```bash
python3 <skill-base>/scripts/generate_dod.py \
  --requirements .sdlc/requirements \
  --out .sdlc/definition-of-done.md \
  --title "<feature name>"
```

The Definition of Done lives at the root of `.sdlc/`, not under this stage's
directory: it derives from every stage that has run, and the design and QA
stages regenerate it as they add gates of their own. This run produces the
requirements-only form — functional acceptance gates, NFR fitness gates,
documentation and deployment readiness — and the header records that design
and QA have not contributed.

Exit 1 means an artifact it must parse is malformed; fix the requirement and
re-run rather than hand-writing the output.
````

Also update the commit block that follows so it stages the new path:

```bash
git add .sdlc/requirements/ .sdlc/definition-of-done.md
```

- [ ] **Step 4: Add the design skill's step**

In `plugin/skills/design/SKILL.md`, insert before `**Step 5 — Commit:**`:

````markdown
**Step 4c — Regenerate the Definition of Done:**

```bash
python3 <skill-base>/../requirements/scripts/generate_dod.py \
  --requirements .sdlc/requirements \
  --design .sdlc/design \
  --out .sdlc/definition-of-done.md \
  --title "<feature name>"
```

The generator lives in the requirements skill and is reached sideways, the
same way this stage's validators are. It rewrites the file the requirements
stage wrote, adding architectural conformance gates from the accepted ADRs and
the declared `depends_on` edges. Skipping this step leaves a Definition of
Done on disk that predates the architecture it should reflect.
````

Update the following commit block to stage `.sdlc/definition-of-done.md`, and add a bullet to `## What This Stage Does Not Produce`:

```markdown
The Definition of Done *is* regenerated, but not by this skill's judgment —
`generate_dod.py` projects it from the requirement and design sets at Step 4c,
and the QA stage rewrites it again once test strategy exists.
```

- [ ] **Step 5: Add the QA skill's step**

In `plugin/skills/qa/SKILL.md`, insert before `**Step 5 — Commit:**`:

````markdown
**Step 4c — Regenerate the Definition of Done:**

```bash
python3 <skill-base>/../requirements/scripts/generate_dod.py \
  --requirements .sdlc/requirements \
  --design .sdlc/design \
  --qa .sdlc/qa \
  --out .sdlc/definition-of-done.md \
  --title "<feature name>"
```

This is the complete form. With the QA set on disk the generator can say which
gates CI actually enforces, which need a person, and which the project
declared unenforced — so `## PR Checklist` becomes accurate here and nowhere
earlier.
````

Add a fourth bullet to the sibling-script list in "Locating the scripts":

```markdown
- `<skill-base>/../requirements/scripts/generate_dod.py` — the Definition of
  Done generator. It reads all three stages, so it lives in the earliest one
  and every stage reaches it sideways.
```

Update the following commit block to stage `.sdlc/definition-of-done.md`.

- [ ] **Step 6: Delete the agent and template**

```bash
git rm plugin/agents/dod-generator.md
git rm plugin/skills/requirements/templates/definition-of-done.md
```

- [ ] **Step 7: Update both scripts READMEs**

Add to `plugin/skills/requirements/scripts/README.md`:

```markdown
### `generate_dod.py`

Projects the requirement, design and QA artifact sets into
`.sdlc/definition-of-done.md`. Every stage skill runs it and each run
supersedes the last, so the file exists as soon as requirements do and gains
gates as later stages land.

    python3 generate_dod.py --requirements .sdlc/requirements \
        [--design .sdlc/design] [--qa .sdlc/qa] \
        --out .sdlc/definition-of-done.md [--title NAME]

Exit 0 written, 1 an artifact it must parse is malformed, 2 usage error.

It parses two NFR body sections — `## ISO 25010 Characteristic` and the
quality attribute scenario's `**Response measure:**` bullet.
`validate_requirements.py` gates both, so drift fails at validation rather
than here.
```

Add a pointer to `plugin/skills/qa/scripts/README.md` noting the generator lives in the requirements skill.

- [ ] **Step 8: Run the tests**

Run: `python3 -m pytest -q`
Expected: all passed, including `tests/test_plugin_package.py`

- [ ] **Step 9: Commit**

```bash
git add -A plugin/ tests/
git commit -m "feat(sto-104): run generate_dod.py from all three stages; delete the agent and template"
```

---

## Task 10: Docs site and generated reference

CLAUDE.md: `site/content/_generated/` is committed and CI fails on drift.

**Files:**
- Modify: `site/content/architecture/index.mdx:36-37,66`
- Modify: `site/content/guide/requirements-stage.mdx:187,197`
- Modify: `site/content/guide/gates.mdx:62`
- Modify: `site/content/guide/troubleshooting.mdx:54`
- Modify: `site/scripts/export_examples.py:78,414`
- Regenerate: `site/content/_generated/agents.json`

- [ ] **Step 1: Fix `architecture/index.mdx`**

Lines 36-37 currently read that a seventh agent, `dod-generator`, runs after the pipeline and derives `definition-of-done.md`. Both halves are now wrong. Replace with prose stating that `generate_dod.py` — a script, not an agent — projects `.sdlc/definition-of-done.md` from whichever artifact sets exist, and that all three stages run it. Fix the same claim at line 66.

- [ ] **Step 2: Fix `guide/requirements-stage.mdx`**

Remove `definition-of-done.md` from the `.sdlc/requirements/` tree listing at line 187. Rewrite the derivation note at line 197 to point at `.sdlc/definition-of-done.md` and name the script.

- [ ] **Step 3: Fix `gates.mdx` and `troubleshooting.mdx`**

Both name `definition-of-done.md` as a file inside the requirements directory that the validator skips. The skip entry survives (a file left at the old path should not start failing), but the *generated* file no longer lands there. Adjust both to say so.

- [ ] **Step 4: Fix `export_examples.py`**

Line 78 lists `definition-of-done.md` among the requirements-stage files to export; line 414 maps its title. The worked examples still carry the file at the old path until the follow-up ticket regenerates them, so **leave both entries in place** and add a comment naming the follow-up:

```python
    # definition-of-done.md still sits under requirements/ in both committed
    # example sets. STO-104 moved the generated path to .sdlc/definition-of-done.md;
    # the follow-up ticket that regenerates the examples moves these entries.
```

- [ ] **Step 5: Regenerate the reference JSON**

Run: `python3 site/scripts/export_reference.py`
Expected: `site/content/_generated/agents.json` loses the `dod-generator` entry

- [ ] **Step 6: Verify no drift remains**

Run: `python3 site/scripts/export_reference.py --check`
Expected: exit 0, no `stale:` lines

- [ ] **Step 7: Confirm nothing else references the deleted agent**

Run: `grep -rn "dod-generator" --include='*.md' --include='*.mdx' --include='*.py' --include='*.json' plugin/ site/ tests/`
Expected: no hits outside `site/content/guide/examples/` (generated from the stale worked examples) and `docs/superpowers/` (historical plans and specs, which are records and stay as written)

- [ ] **Step 8: Run the suite**

Run: `python3 -m pytest -q`
Expected: all passed

- [ ] **Step 9: Commit**

```bash
git add site/
git commit -m "docs(sto-104): the DoD is a script at the root of .sdlc, not an agent under requirements"
```

---

## Task 11: End-to-end run and the follow-up ticket

**Files:**
- No production changes expected. Any finding is a fix in an earlier task's file.

- [ ] **Step 1: Run the generator against the tamagotchi worked example**

```bash
python3 plugin/skills/requirements/scripts/generate_dod.py \
  --requirements docs/requirements/examples/tamagotchi/requirements \
  --design docs/requirements/examples/tamagotchi/design \
  --out /tmp/claude-1000/tamagotchi-dod.md \
  --title "Tamagotchi"
```

Expected: exit 0. The QA stage is absent from this example set (STO-103's run was not committed), so this exercises the requirements+design degradation path against real artifacts rather than fixtures.

- [ ] **Step 2: Run it against the gdpr set**

```bash
python3 plugin/skills/requirements/scripts/generate_dod.py \
  --requirements docs/requirements/examples/gdpr/requirements \
  --out /tmp/claude-1000/gdpr-dod.md \
  --title "GDPR Data Export & Account Deletion"
```

Expected: exit 0, 3 functional gates and 15 NFR fitness gates.

- [ ] **Step 3: Read both outputs end to end**

Check by eye, and record anything found:
- every gate names a real ID and links a file that exists
- no Gherkin is inlined
- the `## PR Checklist` contains no `[CI]` item
- the header's stage markers match what was passed
- no section renders as an empty heading

Fix any finding in the task that owns the code, with a test, and re-run.

- [ ] **Step 4: Confirm the upstream directories are untouched**

```bash
git status --short docs/requirements/examples/
```

Expected: empty. The generator must never write into a stage directory.

- [ ] **Step 5: File the worked-example follow-up ticket**

Spec "Out of scope": both committed DoDs are M1-stub output and go stale on merge, and neither example set has a `qa/` directory, so a full three-stage DoD cannot be demonstrated. File a Linear ticket in the Groundwork project, M3 milestone, following STO-219's shape: regenerate both example sets' Definition of Done against the new generator, generate and commit a QA artifact set for at least one example so the complete form is demonstrable, and move `export_examples.py`'s two entries to the new path.

- [ ] **Step 6: Full suite**

Run: `python3 -m pytest -q`
Expected: all passed

- [ ] **Step 7: Commit any fixes**

```bash
git add -A
git commit -m "fix(sto-104): follow-ups from the first end-to-end run"
```

---

## Self-Review

**Spec coverage:**

| Spec | Task |
|---|---|
| D1 root output path | 1 (`--out`), 9 (skills pass it) |
| D2 script not agent | 1–8 (script), 9 (agent deleted) |
| D3 all three stages, superseding | 9; monotonicity test in 8 |
| D4 one file, source-grouped, PR checklist lead | 4, 5, 6, 7, 8 |
| D5 declared-unenforced register | 6 |
| D6 conformance not fitness functions | 5 |
| D7 coverage derived, not re-checked | 6 |
| D8 NFR body sections parsed and gated | 2 (parse), 3 (gate) |
| D9 no template file | 9 (deleted); rendering in code throughout |
| D10 scope stays project | No task — nothing reads `scope`; the stale promise dies with the agent file in Task 9 |
| Files-touched: docs site + exporter | 10 |
| Out-of-scope: worked-example follow-up | 11 Step 5 |

**Type consistency:** `Artifact` (Task 1) is used unchanged throughout. `enforcement_tag`, `coverage_map`, `by_type`, `_rel_source` are defined in Task 4 and reused in 5–8. `parse_iso_characteristic` / `parse_qas_field` are defined in Task 2 and called in 4 and 7. `render_document`'s signature changes once, in Task 4, when `roots` is added — every later task appends to `body` rather than changing the signature again.

**Known plan-level risk — checked, and clear.** Task 3's gate runs against the committed worked examples via the existing suite. Measured before writing this plan: gdpr 15/15 and tamagotchi 9/9 carry `## ISO 25010 Characteristic`, `## Quality Attribute Scenario` and a `- **Response measure:**` bullet, all as exact heading matches, and no non-NFR artifact carries them. Every head token across the 24 falls inside `ISO_CHARACTERISTICS`. The gate should land green. If a future artifact trips it, Task 3 Step 7 stands: fix the artifact, not the gate.

# M1 Content-Quality Linter + Assumptions Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic content-quality linter for requirement prose (STO-136) and a first-class Assumptions/Dependencies/Open-Questions artifact enforced by the structural validator (STO-134).

**Architecture:** A new advisory Python linter (`lint_requirements_content.py`) reuses the existing validator's discovery + frontmatter parsing and flags prose anti-patterns; it is wired into the critic agent as judgment input. A new hard-gate presence check in `validate_requirements.py` requires a project-level `assumptions.md` with three fixed headings; the orchestrator synthesizes its content and the formatter writes it.

**Tech Stack:** Python 3.12 stdlib + optional `pyyaml`/`jsonschema` (already used by the validator); pytest for tests. Agent/skill definitions are Markdown.

## Global Constraints

- Requirement files are atomic Markdown+YAML under `.sdlc/requirements/{functional,non-functional,constraints,business-rules,use-cases}/`.
- The content linter is **advisory**: it always exits 0 unless `--strict` is passed AND an `error`-severity finding exists (none are `error` today).
- The `assumptions.md` presence+headings check is a **hard gate** in the structural validator (non-zero exit on missing file or missing heading).
- Reuse `validate_requirements.discover_files` and `validate_requirements.parse_frontmatter`; do not duplicate parsing.
- Both scripts live in `skills/requirements/scripts/`; Python auto-adds the script's own directory to `sys.path`, and `tests/conftest.py` adds it for pytest, so `import validate_requirements` / `import lint_requirements_content` resolve.
- New fixture requirement files use **single-line quoted** `description:` values (avoids folded-scalar issues on the stdlib fallback parse path).
- Follow the existing test style in `tests/test_validate_requirements.py` (call `main([...])`, assert on exit code + captured stdout).

---

## Task 1: Scaffold the content linter (skeleton, CLI, report, exit policy)

**Files:**
- Create: `skills/requirements/scripts/lint_requirements_content.py`
- Create: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/clean/FR-001-clean.md`

**Interfaces:**
- Consumes: `validate_requirements.discover_files(reqs_dir) -> List[str]`, `validate_requirements.parse_frontmatter(path) -> Tuple[Optional[dict], Optional[str]]`.
- Produces: `Finding` dataclass (`rule, severity, req_id, field, excerpt, message, suggested_rewrite_hint`); `lint_dir(reqs_dir) -> List[Finding]`; `main(argv=None) -> int`; module-level `CHECKS: list` (empty for now); `_text(value) -> str`.

- [ ] **Step 1: Write the clean fixture**

Create `skills/requirements/scripts/tests/fixtures/content/clean/FR-001-clean.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: "When an authenticated customer cancels a Pending order, the system shall set the order status to Cancelled within 60 seconds."
rationale: "Customers expect to cancel before fulfillment."
fit_criterion: "100% of cancellation requests on Pending orders succeed in tests."
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# FR-001 — Cancel pending order
```

- [ ] **Step 2: Write the failing test**

Create `skills/requirements/scripts/tests/test_lint_content.py`:

```python
"""Tests for the Groundwork requirements content-quality linter."""
import json
import os

import lint_requirements_content as lc

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
CONTENT = os.path.join(FIXTURES, "content")


def rules_for(subdir):
    findings = lc.lint_dir(os.path.join(CONTENT, subdir))
    return {f.rule for f in findings}


def test_clean_fixture_has_no_findings():
    assert lc.lint_dir(os.path.join(CONTENT, "clean")) == []


def test_advisory_exit_is_zero_even_with_findings():
    # The clean dir yields no findings; still must exit 0.
    assert lc.main([os.path.join(CONTENT, "clean")]) == 0
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lint_requirements_content'`.

- [ ] **Step 4: Write the skeleton implementation**

Create `skills/requirements/scripts/lint_requirements_content.py`:

```python
#!/usr/bin/env python3
"""Content-quality linter for Groundwork atomic requirement artifacts.

Distinct from ``validate_requirements.py`` (which checks YAML schema + cross-file
structure). This tool reads the *prose* of each requirement and flags content
anti-patterns — vague qualifiers, compound requirements, EARS non-conformance,
passive voice with a nameless subject, and implementation bias at the
business/stakeholder tier.

It is ADVISORY: it prints a per-requirement diagnostic and, by default, exits 0.
Pass ``--strict`` to exit non-zero on any ``error``-severity finding. Pass
``--json`` for machine-readable findings (consumed by the requirements-critic).

Usage
-----
    python3 lint_requirements_content.py [REQUIREMENTS_DIR]
    python3 lint_requirements_content.py --json .sdlc/requirements
    python3 lint_requirements_content.py --strict --quiet reqs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional

import validate_requirements as vr


@dataclass
class Finding:
    rule: str
    severity: str  # "error" | "warn" | "info"
    req_id: str
    field: str
    excerpt: str
    message: str
    suggested_rewrite_hint: str


def _text(value: Any) -> str:
    """Coerce a frontmatter value to a clean single-space-joined string."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


# Registry of check functions, each (req_id, frontmatter) -> List[Finding].
# Populated in later tasks.
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = []


def lint_dir(reqs_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    for path in vr.discover_files(reqs_dir):
        fm, err = vr.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        req_id = fm.get("id") or os.path.basename(path)
        for check in CHECKS:
            findings.extend(check(req_id, fm))
    return findings


def _print_report(findings: List[Finding], reqs_dir: str, quiet: bool) -> None:
    by_req: Dict[str, List[Finding]] = {}
    for f in findings:
        by_req.setdefault(f.req_id, []).append(f)

    print(f"Content-linting requirements in: {reqs_dir}")
    if not findings:
        print("No content anti-patterns found.")
        return
    for req_id in sorted(by_req):
        print(f"\n{req_id}")
        for f in by_req[req_id]:
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Content-quality linter for Groundwork requirement artifacts."
    )
    parser.add_argument("requirements_dir", nargs="?", default=".sdlc/requirements")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any error-severity finding exists.")
    parser.add_argument("--quiet", action="store_true",
                        help="Print one line per finding (no excerpt/suggestion).")
    args = parser.parse_args(argv)

    reqs_dir = args.requirements_dir
    if not os.path.isdir(reqs_dir):
        print(f"ERROR: requirements directory not found: {reqs_dir}", file=sys.stderr)
        return 2

    findings = lint_dir(reqs_dir)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        _print_report(findings, reqs_dir, args.quiet)

    if args.strict and any(f.severity == "error" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/clean/
git commit -m "feat(sto-136): scaffold content-quality linter (skeleton + advisory CLI)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Vague-qualifier check

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/vague/FR-001-vague.md`

**Interfaces:**
- Produces: `check_vague_qualifiers(req_id, fm) -> List[Finding]` (rule `"vague-qualifier"`), appended to `CHECKS`. `VAGUE_TERMS: set`.

- [ ] **Step 1: Write the vague fixture**

Create `skills/requirements/scripts/tests/fixtures/content/vague/FR-001-vague.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Provide a fast and user-friendly search
description: "The system shall be fast and user-friendly when returning search results."
ears_pattern: ubiquitous
---

# FR-001
```

- [ ] **Step 2: Write the failing test**

Add to `test_lint_content.py`:

```python
def test_vague_qualifier_flagged():
    rules = rules_for("vague")
    assert "vague-qualifier" in rules


def test_vague_qualifier_downgraded_when_quantified():
    fm = {"title": "x", "description": "The system shall respond fast, within 200 ms."}
    findings = lc.check_vague_qualifiers("FR-001", fm)
    assert findings, "expected a finding for 'fast'"
    assert all(f.severity == "info" for f in findings)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -k vague -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'check_vague_qualifiers'`.

- [ ] **Step 4: Implement the check**

In `lint_requirements_content.py`, add after `_text`:

```python
VAGUE_TERMS = {
    "fast", "rapid", "quick", "user-friendly", "easy", "intuitive", "seamless",
    "efficient", "robust", "flexible", "scalable", "secure", "reliable",
    "performant", "minimize", "maximize", "optimize", "approximately",
    "appropriate", "adequate", "sufficient", "state-of-the-art", "modern", "tbd",
}


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[.;\n]+", text) if s.strip()]


def check_vague_qualifiers(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    findings: List[Finding] = []
    for field in ("title", "description"):
        text = _text(fm.get(field))
        for sentence in _sentences(text):
            low = sentence.lower()
            quantified = bool(re.search(r"\d", sentence))
            for term in sorted(VAGUE_TERMS):
                if re.search(rf"\b{re.escape(term)}\b", low):
                    findings.append(Finding(
                        rule="vague-qualifier",
                        severity="info" if quantified else "warn",
                        req_id=req_id,
                        field=field,
                        excerpt=sentence.strip()[:120],
                        message=f"vague qualifier '{term}' without a concrete metric",
                        suggested_rewrite_hint=(
                            f"replace '{term}' with a measurable threshold "
                            f"(a time, count, or percentage)"
                        ),
                    ))
    return findings
```

Then register it by replacing the `CHECKS` line:

```python
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (all tests, including `test_clean_fixture_has_no_findings`).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/vague/
git commit -m "feat(sto-136): add vague-qualifier check

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Compound-requirement check

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/compound/FR-001-compound.md`

**Interfaces:**
- Produces: `check_compound(req_id, fm) -> List[Finding]` (rule `"compound"`), appended to `CHECKS`. `ACTION_VERBS: set`.

- [ ] **Step 1: Write the compound fixture**

Create `skills/requirements/scripts/tests/fixtures/content/compound/FR-001-compound.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Record and notify on cancellation
description: "When a customer cancels an order, the system shall create a cancellation record and send a confirmation email."
ears_pattern: event
---

# FR-001
```

- [ ] **Step 2: Write the failing test**

Add to `test_lint_content.py`:

```python
def test_compound_requirement_flagged():
    assert "compound" in rules_for("compound")


def test_noun_conjunction_not_flagged_as_compound():
    fm = {"description": "The system shall accept the terms and conditions."}
    assert lc.check_compound("FR-001", fm) == []
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -k compound -v`
Expected: FAIL — `AttributeError: ... 'check_compound'`.

- [ ] **Step 4: Implement the check**

In `lint_requirements_content.py`, add:

```python
ACTION_VERBS = {
    "create", "update", "delete", "remove", "send", "display", "show", "store",
    "save", "validate", "verify", "notify", "alert", "log", "record", "generate",
    "transition", "publish", "return", "reject", "accept", "allow", "prevent",
    "block", "provide", "calculate", "compute", "export", "import", "retry",
    "cancel", "archive", "encrypt", "decrypt", "authenticate", "authorize",
    "render", "email", "persist", "enqueue", "dispatch", "present", "list",
    "filter", "sort", "redirect", "set", "mark", "flag", "assign",
}

_COMPOUND_RE = re.compile(
    r"\b(and|or)\s+(" + "|".join(sorted(ACTION_VERBS)) + r")\b"
)


def check_compound(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    text = _text(fm.get("description"))
    low = text.lower()
    idx = low.find("shall")
    if idx == -1:
        return []
    predicate = low[idx + len("shall"):]
    match = _COMPOUND_RE.search(predicate)
    if not match:
        return []
    return [Finding(
        rule="compound",
        severity="warn",
        req_id=req_id,
        field="description",
        excerpt=text.strip()[:120],
        message=(
            f"multiple actions joined by '{match.group(1)}' "
            f"('{match.group(2)}') in one requirement"
        ),
        suggested_rewrite_hint="split into one requirement per action",
    )]
```

Register it by appending to `CHECKS`:

```python
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
    check_compound,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (all tests; `clean` still yields no findings).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/compound/
git commit -m "feat(sto-136): add compound-requirement check

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: EARS-conformance check

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/ears/FR-001-ears-mismatch.md`

**Interfaces:**
- Produces: `check_ears(req_id, fm) -> List[Finding]` (rule `"ears-conformance"`), appended to `CHECKS`. `EARS_LEADS: dict`.

- [ ] **Step 1: Write the EARS-mismatch fixture**

Create `skills/requirements/scripts/tests/fixtures/content/ears/FR-001-ears-mismatch.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Show dashboard
description: "The system shall present the dashboard to the operator."
ears_pattern: event
---

# FR-001
```

(Declared `event` but the description has no `When` lead → mismatch.)

- [ ] **Step 2: Write the failing test**

Add to `test_lint_content.py`:

```python
def test_ears_mismatch_flagged():
    assert "ears-conformance" in rules_for("ears")


def test_event_pattern_with_when_is_clean():
    fm = {"type": "functional", "ears_pattern": "event",
          "description": "When a user logs in, the system shall record the timestamp."}
    assert lc.check_ears("FR-001", fm) == []


def test_ears_check_skips_non_functional():
    fm = {"type": "non_functional", "description": "no shall here"}
    assert lc.check_ears("NFR-001", fm) == []
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -k ears -v`
Expected: FAIL — `AttributeError: ... 'check_ears'`.

- [ ] **Step 4: Implement the check**

In `lint_requirements_content.py`, add:

```python
# ears_pattern -> required leading keyword (None = must have NO condition lead;
# "SKIP" = combination pattern, no single-lead rule).
EARS_LEADS: Dict[str, Optional[str]] = {
    "event": "when",
    "state": "while",
    "unwanted": "if",       # also requires a "then" clause
    "optional": "where",
    "ubiquitous": None,
    "complex": "SKIP",
}

_CONDITION_LEAD_RE = re.compile(r"^(when|while|if|where)\b")


def _ears_finding(req_id: str, desc: str, message: str) -> Finding:
    return Finding(
        rule="ears-conformance",
        severity="warn",
        req_id=req_id,
        field="description",
        excerpt=desc.strip()[:120],
        message=message,
        suggested_rewrite_hint="rephrase to the declared EARS pattern's shape",
    )


def check_ears(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    if fm.get("type") != "functional":
        return []
    desc = _text(fm.get("description"))
    low = desc.lower()
    if "shall" not in low:
        return [_ears_finding(
            req_id, desc,
            "functional requirement description does not contain 'shall'",
        )]

    pattern = fm.get("ears_pattern")
    lead = EARS_LEADS.get(pattern, "SKIP")
    if lead == "SKIP":
        return []
    if lead is None:
        # ubiquitous: must NOT open with a condition keyword.
        if _CONDITION_LEAD_RE.match(low):
            return [_ears_finding(
                req_id, desc,
                "ears_pattern 'ubiquitous' should have no leading condition, "
                "but the description opens with one",
            )]
        return []
    # Conditional patterns: must open with the required keyword.
    if not re.match(rf"^{lead}\b", low):
        return [_ears_finding(
            req_id, desc,
            f"ears_pattern '{pattern}' requires a leading '{lead}' clause",
        )]
    if pattern == "unwanted" and "then" not in low:
        return [_ears_finding(
            req_id, desc,
            "ears_pattern 'unwanted' requires an 'If ... then ...' structure",
        )]
    return []
```

Register it by appending to `CHECKS`:

```python
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
    check_compound,
    check_ears,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (all tests; the `clean` fixture is `event` + `When ...` so it stays clean).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/ears/
git commit -m "feat(sto-136): add EARS-conformance check

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Passive-voice nameless-subject check

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/passive/FR-001-passive.md`

**Interfaces:**
- Produces: `check_passive(req_id, fm) -> List[Finding]` (rule `"passive-nameless"`), appended to `CHECKS`.

- [ ] **Step 1: Write the passive fixture**

Create `skills/requirements/scripts/tests/fixtures/content/passive/FR-001-passive.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Archive cancelled orders
description: "When an order is cancelled, the order shall be archived within one hour."
ears_pattern: event
---

# FR-001
```

- [ ] **Step 2: Write the failing test**

Add to `test_lint_content.py`:

```python
def test_passive_nameless_flagged():
    assert "passive-nameless" in rules_for("passive")


def test_passive_with_named_actor_not_flagged():
    fm = {"description": "When triggered, the record shall be archived by the ledger service."}
    assert lc.check_passive("FR-001", fm) == []
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -k passive -v`
Expected: FAIL — `AttributeError: ... 'check_passive'`.

- [ ] **Step 4: Implement the check**

In `lint_requirements_content.py`, add:

```python
_PASSIVE_RE = re.compile(r"shall be \w+(?:ed|en)\b")


def check_passive(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    desc = _text(fm.get("description"))
    low = desc.lower()
    for match in _PASSIVE_RE.finditer(low):
        tail = low[match.end():match.end() + 40]
        if " by " in tail:
            continue  # actor is named
        return [Finding(
            rule="passive-nameless",
            severity="warn",
            req_id=req_id,
            field="description",
            excerpt=desc.strip()[:120],
            message="passive voice hides the responsible actor",
            suggested_rewrite_hint=(
                "name the actor: 'the <system/component> shall <verb> ...'"
            ),
        )]
    return []
```

Register it by appending to `CHECKS`:

```python
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
    check_compound,
    check_ears,
    check_passive,
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (all tests).

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/passive/
git commit -m "feat(sto-136): add passive-voice nameless-subject check

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Implementation-bias check

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py`
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/impl-bias/FR-001-impl-bias.md`

**Interfaces:**
- Produces: `check_impl_bias(req_id, fm) -> List[Finding]` (rule `"impl-bias"`, severity `"info"`), appended to `CHECKS`. `TECH_TERMS: set`.

- [ ] **Step 1: Write the impl-bias fixture**

Create `skills/requirements/scripts/tests/fixtures/content/impl-bias/FR-001-impl-bias.md`:

```markdown
---
id: FR-001
type: functional
tier: stakeholder
title: Cancel via a button
description: "When the user clicks the Cancel button, the system shall cancel the order."
ears_pattern: event
---

# FR-001
```

- [ ] **Step 2: Write the failing test**

Add to `test_lint_content.py`:

```python
def test_impl_bias_flagged_at_stakeholder_tier():
    findings = lc.lint_dir(os.path.join(CONTENT, "impl-bias"))
    impl = [f for f in findings if f.rule == "impl-bias"]
    assert impl
    assert all(f.severity == "info" for f in impl)


def test_impl_bias_not_flagged_at_solution_tier():
    fm = {"tier": "solution", "title": "x",
          "description": "When the user clicks the button, the system shall cancel."}
    assert lc.check_impl_bias("FR-001", fm) == []
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -k impl_bias -v`
Expected: FAIL — `AttributeError: ... 'check_impl_bias'`.

- [ ] **Step 4: Implement the check**

In `lint_requirements_content.py`, add:

```python
TECH_TERMS = {
    "button", "dropdown", "checkbox", "modal", "click", "tap", "page", "screen",
    "react", "vue", "angular", "postgres", "postgresql", "mysql", "mongodb",
    "redis", "kafka", "rest", "graphql", "endpoint", "sql", "css", "html",
    "javascript", "docker", "kubernetes",
}


def check_impl_bias(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    if fm.get("tier") not in ("business", "stakeholder"):
        return []
    tier = fm.get("tier")
    for field in ("title", "description"):
        text = _text(fm.get(field))
        low = text.lower()
        for term in sorted(TECH_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                return [Finding(
                    rule="impl-bias",
                    severity="info",
                    req_id=req_id,
                    field=field,
                    excerpt=text.strip()[:120],
                    message=(
                        f"implementation detail '{term}' in a "
                        f"{tier}-tier requirement"
                    ),
                    suggested_rewrite_hint=(
                        "move technology/UI choices to a constraint or the "
                        "solution tier"
                    ),
                )]
    return []
```

Register it by appending to `CHECKS`:

```python
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
    check_compound,
    check_ears,
    check_passive,
    check_impl_bias,
]
```

- [ ] **Step 5: Add a JSON-output shape test**

Add to `test_lint_content.py`:

```python
def test_json_output_is_parseable(capsys):
    code = lc.main([os.path.join(CONTENT, "vague"), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert isinstance(data, list) and data
    assert {"rule", "severity", "req_id", "field", "message"} <= set(data[0])
```

- [ ] **Step 6: Run the full linter suite**

Run: `pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS (all tests).

- [ ] **Step 7: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py skills/requirements/scripts/tests/fixtures/content/impl-bias/
git commit -m "feat(sto-136): add implementation-bias check + JSON output test

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Wire the content linter into the critic, skill, and README

**Files:**
- Modify: `agents/requirements-critic.md` (Gate C section, lines ~54-67)
- Modify: `skills/requirements/SKILL.md` (Phase 5 Step 4, lines ~178-187)
- Modify: `skills/requirements/scripts/README.md`

**Interfaces:**
- Consumes: `lint_requirements_content.py --json` output (list of finding objects).
- Produces: documentation only — no code, no new test.

- [ ] **Step 1: Update the critic's Gate C**

In `agents/requirements-critic.md`, replace the Gate C section (the block from `## Gate C — Light anti-pattern flags (prompt-level)` through the `(Deep content-quality linting is deferred to a later milestone; keep this at the prompt level.)` line) with:

```markdown
## Gate C — Content-quality lint (script-backed)

Run the content-quality linter and fold its findings into your per-requirement
verdicts. It is advisory (it never fails the pipeline by itself); you decide which
findings warrant a `revise`:

```bash
python3 skills/requirements/scripts/lint_requirements_content.py --json .sdlc/requirements
```

The linter reports, per requirement: `vague-qualifier`, `compound`,
`ears-conformance`, `passive-nameless`, and `impl-bias` findings, each with an
`excerpt` and a `suggested_rewrite_hint`. Treat `warn`-severity findings
(vague qualifiers, compound statements, EARS non-conformance, passive/nameless)
as defects requiring a `revise`; treat `impl-bias` (`info`) as a prompt to check
the tier and reword. Add your own judgment on top:

- **Implementation bias**: confirm the flagged tech/UI term truly leaks a
  solution decision into a `business`/`stakeholder` requirement before requiring
  a rewrite (the linter is deliberately conservative here).
- **Suggested rewrites**: author the concrete bad→good rewrite in your findings;
  the linter only hints at the shape.

If the linter is unavailable (missing interpreter/deps), fall back to flagging
these anti-patterns by inspection and note the degraded mode in your report.
```

- [ ] **Step 2: Update SKILL.md Phase 5 Step 4**

In `skills/requirements/SKILL.md`, in **Step 4 — Write atomic files, then validate**, immediately after the `python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements` line's paragraph, add:

```markdown
Then run the advisory content-quality linter and address any `warn`-severity
findings (the structural validator is the hard gate; the content linter guides
prose quality):

```bash
python3 skills/requirements/scripts/lint_requirements_content.py .sdlc/requirements
```
```

- [ ] **Step 3: Document the linter in the scripts README**

In `skills/requirements/scripts/README.md`, add a section:

```markdown
## Content-quality linter — `lint_requirements_content.py`

Advisory linter for requirement *prose* (distinct from the structural validator).
Flags vague qualifiers, compound requirements, EARS non-conformance, passive voice
with a nameless subject, and implementation bias at the business/stakeholder tier.

```bash
python3 lint_requirements_content.py .sdlc/requirements        # human report
python3 lint_requirements_content.py --json .sdlc/requirements # machine-readable
python3 lint_requirements_content.py --strict reqs             # exit non-zero on error-severity
```

Exit codes: `0` always (advisory), except `--strict` returns `1` when an
`error`-severity finding exists, and `2` on a missing directory. It reuses
`validate_requirements.discover_files`/`parse_frontmatter`, so it sees exactly the
same atomic requirement files and skips the same non-atomic files.
```

- [ ] **Step 4: Verify the whole script suite still passes**

Run: `pytest skills/requirements/scripts/tests -v`
Expected: PASS (existing validator tests + new content-linter tests).

- [ ] **Step 5: Commit**

```bash
git add agents/requirements-critic.md skills/requirements/SKILL.md skills/requirements/scripts/README.md
git commit -m "feat(sto-136): wire content linter into critic, skill, and README

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Enforce the assumptions.md context artifact in the structural validator

**Files:**
- Modify: `skills/requirements/scripts/validate_requirements.py` (add `SKIP_FILENAMES` entry ~line 94; new `check_context_artifact`; call it in `validate` ~line 444)
- Modify: `skills/requirements/scripts/tests/test_validate_requirements.py`
- Create: `skills/requirements/scripts/tests/fixtures/valid/assumptions.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/missing_context_artifact/functional/FR-001-ok.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/context_artifact_missing_heading/assumptions.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/context_artifact_missing_heading/functional/FR-001-ok.md`

**Interfaces:**
- Produces: `check_context_artifact(reqs_dir) -> List[str]`; `CONTEXT_ARTIFACT = "assumptions.md"`; `REQUIRED_CONTEXT_HEADINGS: list`. `assumptions.md` added to `SKIP_FILENAMES`.

- [ ] **Step 1: Add the valid fixture's assumptions.md**

Create `skills/requirements/scripts/tests/fixtures/valid/assumptions.md`:

```markdown
# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: Customers are authenticated before reaching the cancellation flow.

## Dependencies
- D-1: The order-fulfillment service exposes a status API.

## Open Questions
- None identified.
```

- [ ] **Step 2: Write the failing tests**

In `test_validate_requirements.py`, add the two new invalid cases to the `INVALID_CASES` dict:

```python
INVALID_CASES = {
    "missing_required_field": "rationale",
    "bad_enum": "priority",
    "duplicate_id": "duplicate id",
    "dangling_trace": "dangling",
    "fr_missing_ears": "ears_pattern",
    "missing_context_artifact": "context artifact",
    "context_artifact_missing_heading": "missing required heading",
}
```

And add a direct unit test for the new function:

```python
def test_context_artifact_present_passes(tmp_path):
    (tmp_path / "assumptions.md").write_text(
        "## Assumptions\n- none\n## Dependencies\n- none\n## Open Questions\n- none\n",
        encoding="utf-8",
    )
    assert vr.check_context_artifact(str(tmp_path)) == []


def test_context_artifact_missing_file_is_flagged(tmp_path):
    errors = vr.check_context_artifact(str(tmp_path))
    assert any("context artifact" in e for e in errors)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `pytest skills/requirements/scripts/tests/test_validate_requirements.py -k context -v`
Expected: FAIL — `AttributeError: ... 'check_context_artifact'` (and the parametrized new cases error on missing fixtures).

- [ ] **Step 4: Implement the check in the validator**

In `validate_requirements.py`, change `SKIP_FILENAMES`:

```python
SKIP_FILENAMES = {"definition-of-done.md", "index.yaml", "assumptions.md"}
```

Add, after the `PREFIX_TO_TYPE` block:

```python
# Project-level context artifact (STO-134): assumptions/dependencies/open-questions.
CONTEXT_ARTIFACT = "assumptions.md"
REQUIRED_CONTEXT_HEADINGS = ["## Assumptions", "## Dependencies", "## Open Questions"]
```

Add this function just above `discover_files`:

```python
def check_context_artifact(reqs_dir: str) -> List[str]:
    """Assumptions/Dependencies/Open-Questions artifact presence + headings (hard gate).

    Returns a list of set-level error strings (empty when the artifact is present
    and contains all three required H2 headings, even if a section reads
    'None identified').
    """
    path = os.path.join(reqs_dir, CONTEXT_ARTIFACT)
    if not os.path.isfile(path):
        return [
            f"missing required context artifact '{CONTEXT_ARTIFACT}' "
            f"(Assumptions / Dependencies / Open Questions)"
        ]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return [f"could not read context artifact '{CONTEXT_ARTIFACT}': {exc}"]

    errors: List[str] = []
    for heading in REQUIRED_CONTEXT_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(
                f"context artifact '{CONTEXT_ARTIFACT}' missing required heading "
                f"'{heading}'"
            )
    return errors
```

In `validate`, fold the context check into the returned global errors. Change the tail of `validate` from:

```python
    global_errors = cross_file_checks(files)
    return files, global_errors
```

to:

```python
    global_errors = cross_file_checks(files)
    global_errors.extend(check_context_artifact(reqs_dir))
    return files, global_errors
```

- [ ] **Step 5: Create the two invalid fixtures**

Create `skills/requirements/scripts/tests/fixtures/invalid/missing_context_artifact/functional/FR-001-ok.md` (a schema-valid requirement so the ONLY error is the missing artifact):

```markdown
---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: "When a customer cancels a Pending order, the system shall set its status to Cancelled within 60 seconds."
rationale: "Customers expect to cancel before fulfillment."
fit_criterion: "100% of cancellations on Pending orders succeed in tests."
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# FR-001 — Cancel pending order
```

Create `skills/requirements/scripts/tests/fixtures/invalid/context_artifact_missing_heading/functional/FR-001-ok.md` with the identical content as the file above.

Create `skills/requirements/scripts/tests/fixtures/invalid/context_artifact_missing_heading/assumptions.md` (deliberately missing the `## Dependencies` heading):

```markdown
# Assumptions & Open Questions

## Assumptions
- A-1: Something assumed.

## Open Questions
- None identified.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest skills/requirements/scripts/tests/test_validate_requirements.py -v`
Expected: PASS. `test_valid_set_passes` still passes (the valid dir now has `assumptions.md`); both new parametrized cases fail-as-expected with their needles; the two unit tests pass.

- [ ] **Step 7: Confirm the skip assertion still holds**

The existing `test_skip_files_are_ignored` asserts `definition-of-done.md` and `index.yaml` are not reported. Add one line to it:

```python
    assert "assumptions.md" not in out
```

Run: `pytest skills/requirements/scripts/tests/test_validate_requirements.py -k skip -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add skills/requirements/scripts/validate_requirements.py skills/requirements/scripts/tests/
git commit -m "feat(sto-134): enforce assumptions.md context artifact in structural validator

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Add assumptions.md to the GDPR example set

**Files:**
- Create: `docs/requirements/examples/assumptions.md`

**Interfaces:**
- Consumes: the new hard-gate check from Task 8.
- Produces: a conformant example artifact.

- [ ] **Step 1: Write the example artifact**

Create `docs/requirements/examples/assumptions.md`, drawn from the existing GDPR example requirements in `docs/requirements/examples/`:

```markdown
# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: Every data subject has exactly one authenticated account identity.
- A-2: "Personal data" is limited to records already catalogued in the data map.
- A-3: Re-authentication uses the existing identity provider; no new auth is built.

## Dependencies
- D-1: A durable object store is available for generated export archives.
- D-2: The identity provider exposes a step-up (re-authentication) flow.
- D-3: Statutory retention rules for financial records are supplied by legal.

## Open Questions
- Q-1: What is the maximum acceptable turnaround for an export request? (owner: product)
- Q-2: Which regulated record types override erasure, beyond financial? (owner: legal)
```

- [ ] **Step 2: Validate the example set (hard gate must pass)**

Run: `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples`
Expected: exit 0 — `assumptions.md` satisfies the context-artifact check and is itself skipped as a requirement.

- [ ] **Step 3: Run the content linter over the example set (advisory)**

Run: `python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples`
Expected: exit 0; prints any advisory findings. Review them but do not treat as blocking (example set is illustrative).

- [ ] **Step 4: Commit**

```bash
git add docs/requirements/examples/assumptions.md
git commit -m "docs(sto-134): add assumptions artifact to GDPR example set

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Document the context artifact across orchestrator, formatter, and skill

**Files:**
- Modify: `agents/requirements-orchestrator.md` (add Stage 6.5; extend `draft_requirements` note; add `context_artifact` shape)
- Modify: `agents/requirements-formatter.md` (write assumptions.md)
- Modify: `agents/fr-specialist.md`, `agents/nfr-specialist.md`, `agents/constraint-specialist.md` (optional assumptions/dependencies fields)
- Modify: `skills/requirements/SKILL.md` (Phase 5 pipeline list + Step 4 + summary)

**Interfaces:**
- Produces: documentation only — no code, no test. Verified against the example set from Task 9.

- [ ] **Step 1: Add Stage 6.5 to the orchestrator**

In `agents/requirements-orchestrator.md`, between **Stage 6 — Critique gate** and **Stage 7 — Format**, insert:

````markdown
## Stage 6.5 — Synthesize the context artifact

Before formatting, assemble a `context_artifact` capturing what the requirements
set assumes, depends on, and leaves open. This forces externalization of what the
model would otherwise silently bake into requirement prose (research Gap 5).

```yaml
context_artifact:
  assumptions:            # statements believed true without proof
    - id: A-1
      statement: string
  dependencies:           # external conditions the project relies on
    - id: D-1
      statement: string
  open_questions:         # unresolved items for human follow-up
    - id: Q-1
      statement: string
      owner: string       # who should resolve it (or "unassigned")
```

Sources, in order:
1. `open_questions` — carry every item from `clarification_context.open_questions`
   (each already implies an affected requirement is `confidence: low`).
2. `assumptions` / `dependencies` — merge any `assumptions`/`dependencies` a
   specialist surfaced in its return object (see Stage 5), then add anything the
   generated set implies that no requirement states outright. De-duplicate.

If a section has no items, emit a single `None identified` entry. Pass the
`context_artifact` to the formatter; it writes `.sdlc/requirements/assumptions.md`.
The structural validator hard-gates that file's presence and its three headings.
````

- [ ] **Step 2: Extend the Stage 5 draft_requirements note**

In `agents/requirements-orchestrator.md`, at the end of **Stage 5 — Collect drafts**, add:

```markdown
Each specialist MAY additionally return sibling `assumptions` and `dependencies`
lists (plain statements) alongside its `draft_requirements`. These are optional
and feed Stage 6.5; they are NOT written into individual requirement frontmatter.
```

- [ ] **Step 3: Document the write in the formatter**

In `agents/requirements-formatter.md`, after the **Optional machine index** section, add:

````markdown
## Context artifact — `assumptions.md`

When the orchestrator supplies a `context_artifact` (Stage 6.5), write
`.sdlc/requirements/assumptions.md` with exactly three H2 sections in this order —
`## Assumptions`, `## Dependencies`, `## Open Questions` — listing each item
(`A-#` / `D-#` / `Q-#`), or the literal `None identified` when a section is empty:

```markdown
# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: <statement>

## Dependencies
- D-1: <statement>

## Open Questions
- Q-1: <statement> (owner: <who>)
```

This is a project-level file, not an atomic requirement — the validator skips it
as a requirement but hard-gates its presence and its three headings. All three
headings MUST be present even when a section is empty.
````

- [ ] **Step 4: Note the optional fields in the three specialists**

In each of `agents/fr-specialist.md`, `agents/nfr-specialist.md`, and
`agents/constraint-specialist.md`, add this line to the section describing the
returned `draft_requirements` object (adjust wording to match each file's voice):

```markdown
You MAY also return optional sibling `assumptions` and `dependencies` lists (plain
statements you relied on but could not confirm). The orchestrator aggregates these
into the project-level `assumptions.md`; do not embed them in requirement frontmatter.
```

- [ ] **Step 5: Update SKILL.md Phase 5**

In `skills/requirements/SKILL.md`:

(a) In the **Step 1 — Generate** pipeline list, change the `requirements-formatter`
bullet to note the extra file:

```markdown
6. **requirements-formatter** — writes the atomic files plus the project-level
   `assumptions.md` (Assumptions / Dependencies / Open Questions), running only
   after the critic returns `gate: pass`.
```

(b) In the **Step 2 — Render in-conversation summary** template, add a section
before **Flagged for review**:

```markdown
**Assumptions & Dependencies:** [key A-#/D-# items, or "None identified"]
**Open Questions:** [Q-# items needing human follow-up, or "None"]
```

(c) In **Step 4**, update the `mkdir`/validate note to mention the artifact:

```markdown
The formatter also writes `.sdlc/requirements/assumptions.md`. The structural
validator hard-gates its presence and its three headings (`## Assumptions`,
`## Dependencies`, `## Open Questions`) — a missing file or heading fails the gate.
```

- [ ] **Step 6: Re-validate the example set as a regression check**

Run: `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples && pytest skills/requirements/scripts/tests -q`
Expected: validator exit 0; full pytest suite passes.

- [ ] **Step 7: Commit**

```bash
git add agents/ skills/requirements/SKILL.md
git commit -m "docs(sto-134): document context artifact in orchestrator, formatter, specialists, skill

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Run the entire script test suite**

Run: `pytest skills/requirements/scripts/tests -v`
Expected: all validator + content-linter tests PASS.

- [ ] **Validate + lint the example set end to end**

Run:
```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: validator exits 0; linter exits 0 and prints its advisory report.

- [ ] **Confirm no stray references** to the old "deep content-quality linting is deferred" wording remain in `agents/requirements-critic.md`.

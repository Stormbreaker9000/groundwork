# M1 Glossary Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit a `glossary.md` artifact alongside every generated requirement set, so the vocabulary M1 establishes survives the hand-off to M2 (architecture) and M3 (QA) without terminology drift.

**Architecture:** The glossary rides the pipeline's existing *context-artifact* seam rather than introducing a new agent or stage. The three specialists optionally return sibling `terms`; the orchestrator's Stage 6.5 merges them into the `context_artifact`; the formatter writes `.sdlc/requirements/glossary.md` next to `assumptions.md`. The structural validator hard-gates the file's presence and its `## Terms` heading (an honest `None identified` passes). The content linter gains a **set-level** check hook and one check on it — warn when a defined term is used by no requirement. Undefined-term detection is deliberately *not* in the linter; it is judgment about natural language and belongs to the critic agent.

**Tech Stack:** Python 3 (stdlib + `pyyaml`/`jsonschema`, already dependencies), pytest, Markdown+YAML artifacts, Claude Code agent definitions in `agents/*.md`.

**Spec:** `docs/superpowers/specs/2026-07-13-m1-glossary-artifact-design.md`
**Ticket:** STO-135 (last open M1 issue)

## Global Constraints

- The on-disk glossary format is exactly: one `# Glossary` H1, one `## Terms` H2, one bullet per term as `- **Term**: definition.`, with an optional trailing `*Also: alias, alias.*` clause. Terms sorted alphabetically. Empty glossary = the single line `None identified` under `## Terms`.
- `glossary.md` is a **project-level file, not an atomic requirement**: the validator must skip it as a requirement and gate it as an artifact.
- The validator gate is **presence + heading only**. Content is never gated — `None identified` is a legal, passing glossary.
- Glossary entries carry **no requirement-ID backlinks**. Term, definition, optional aliases. Nothing to keep in sync.
- The linter's glossary check is **advisory** (`severity="warn"`) and runs **only when `glossary.md` exists**. A missing glossary is the validator's problem, not the linter's — this is what keeps the existing `content/clean` fixture (which has no glossary) finding-free.
- Existing test needles must keep matching: the strings `context artifact`, `missing required heading`, and `could not read` must survive the validator refactor in Task 1.
- Each example set is a separate project with its own ID space. Never validate `docs/requirements/examples` as a whole — validate each set's own `requirements/` directory.

---

## Task 0: Fix the examples layout (prerequisite, no behavior change)

The examples tree currently holds two independent requirement sets sharing one ID space: the GDPR set at the root of `docs/requirements/examples/`, and the tamagotchi set nested beneath it. Each is clean alone (GDPR 8/8, tamagotchi 22/22), but a recursive walk of `docs/requirements/examples` sees both and fails with 11 duplicate-ID errors. Give the GDPR set its own directory so each example set is self-contained.

**Files:**
- Move: `docs/requirements/examples/{functional,non-functional,constraints,business-rules}/` → `docs/requirements/examples/gdpr/requirements/`
- Move: `docs/requirements/examples/assumptions.md` → `docs/requirements/examples/gdpr/requirements/assumptions.md`
- Move: `docs/requirements/examples/definition-of-done.md` → `docs/requirements/examples/gdpr/requirements/definition-of-done.md`
- Create: `docs/requirements/examples/README.md`

**Interfaces:**
- Produces: the path `docs/requirements/examples/gdpr/requirements` — every later task's GDPR verification command uses it.

- [ ] **Step 1: Confirm the problem exists (baseline)**

Run: `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples`
Expected: exit 1, summary line reading `22/33 file(s) passed, 11 failed`, with `duplicate id` errors.

- [ ] **Step 2: Move the GDPR set with git mv**

```bash
cd docs/requirements/examples
mkdir -p gdpr/requirements
git mv functional non-functional constraints business-rules gdpr/requirements/
git mv assumptions.md definition-of-done.md gdpr/requirements/
cd -
```

- [ ] **Step 3: Verify each set now validates independently**

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
```
Expected: exit 0 for both. GDPR reports `8/8 file(s) passed`; tamagotchi reports `22/22 file(s) passed`.

- [ ] **Step 4: Write the examples README**

Create `docs/requirements/examples/README.md`:

```markdown
# Example requirement sets

Two complete artifact sets produced by the Groundwork requirements pipeline. Each
is an independent project with its own ID space — `FR-001` in one has nothing to do
with `FR-001` in the other — so each is validated on its own:

| Set | Path | Size |
| --- | --- | --- |
| GDPR data-subject rights | `gdpr/requirements/` | 8 requirements |
| Desktop tamagotchi | `tamagotchi/requirements/` | 22 requirements |

Validate a set by pointing the tools at that set's `requirements/` directory:

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples/gdpr/requirements
```

Do **not** point them at `docs/requirements/examples` — the walk is recursive, and
the two sets' ID spaces collide.

The tamagotchi set also ships a single-document rendering (`tamagotchi/CONSOLIDATED.md`)
and the dev-log draft that discusses it.
```

- [ ] **Step 5: Commit**

```bash
git add docs/requirements/examples
git commit -m "refactor(sto-135): give each example set its own directory

The GDPR set lived at the examples root while the tamagotchi set was nested
inside it, so a recursive validator walk saw two projects sharing one ID space
and failed with duplicate-ID errors. Each set now owns a requirements/ dir and
is validated independently."
```

---

## Task 1: Validator — generalize the artifact check and gate `glossary.md`

**Files:**
- Modify: `skills/requirements/scripts/validate_requirements.py` (constants near line 94–107; `check_context_artifact` at 406–432; `validate()` at 450–479)
- Modify: `skills/requirements/scripts/tests/test_validate_requirements.py`
- Create: `skills/requirements/scripts/tests/fixtures/valid/glossary.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/missing_glossary/assumptions.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/missing_glossary/functional/FR-001-ok.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/glossary_missing_heading/assumptions.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/glossary_missing_heading/glossary.md`
- Create: `skills/requirements/scripts/tests/fixtures/invalid/glossary_missing_heading/functional/FR-001-ok.md`

**Interfaces:**
- Produces: `vr.GLOSSARY_ARTIFACT` (`"glossary.md"`), `vr.REQUIRED_GLOSSARY_HEADINGS` (`["## Terms"]`), `vr.check_glossary_artifact(reqs_dir) -> List[str]`, and `vr.SKIP_FILENAMES` now containing `"glossary.md"`. Task 2's linter relies on `glossary.md` being in `SKIP_FILENAMES` so `vr.discover_files()` does not hand it back as a requirement.
- Preserves: `vr.check_context_artifact(reqs_dir) -> List[str]` — same name, same return shape, same message substrings.

- [ ] **Step 1: Write the failing tests**

Append to `skills/requirements/scripts/tests/test_validate_requirements.py`:

```python
# ---------------------------------------------------------------------------
# Glossary artifact (STO-135) — presence + heading gate.
# ---------------------------------------------------------------------------
def test_glossary_artifact_present_passes(tmp_path):
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\n- **Decay**: the reduction of stat values over time.\n",
        encoding="utf-8",
    )
    assert vr.check_glossary_artifact(str(tmp_path)) == []


def test_glossary_artifact_empty_section_passes(tmp_path):
    """An honest 'None identified' glossary is legal — content is never gated."""
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\nNone identified\n", encoding="utf-8"
    )
    assert vr.check_glossary_artifact(str(tmp_path)) == []


def test_glossary_artifact_missing_file_is_flagged(tmp_path):
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("glossary artifact" in e for e in errors)


def test_glossary_artifact_missing_heading_is_flagged(tmp_path):
    (tmp_path / "glossary.md").write_text("# Glossary\n\n- **Decay**: x.\n", encoding="utf-8")
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("missing required heading" in e for e in errors)


def test_glossary_artifact_non_utf8_is_reported_not_raised(tmp_path):
    (tmp_path / "glossary.md").write_bytes(b"\xff\xfe## Terms\n")
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert errors and any("could not read" in e for e in errors)


def test_glossary_is_not_validated_as_a_requirement(capsys):
    run(VALID_DIR)
    out = capsys.readouterr().out
    assert "glossary.md" not in out
```

Also extend the existing `INVALID_CASES` dict (currently at line 53) with the two new cases:

```python
INVALID_CASES = {
    "missing_required_field": "rationale",
    "bad_enum": "priority",
    "duplicate_id": "duplicate id",
    "dangling_trace": "dangling",
    "fr_missing_ears": "ears_pattern",
    "missing_context_artifact": "context artifact",
    "context_artifact_missing_heading": "missing required heading",
    "missing_glossary": "glossary artifact",
    "glossary_missing_heading": "missing required heading",
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/requirements/scripts && python3 -m pytest tests/test_validate_requirements.py -v`
Expected: FAIL — `AttributeError: module 'validate_requirements' has no attribute 'check_glossary_artifact'`, and the two new `INVALID_CASES` fail because their fixture directories do not exist yet.

- [ ] **Step 3: Add the fixtures**

Create `skills/requirements/scripts/tests/fixtures/valid/glossary.md` (the `valid/` set must now carry a glossary or it stops being valid):

```markdown
# Glossary

## Terms
- **Pending order**: an order that has been placed but not yet dispatched, and is therefore still cancellable. *Also: unshipped order.*
```

Create `skills/requirements/scripts/tests/fixtures/invalid/missing_glossary/assumptions.md`:

```markdown
# Assumptions, Dependencies & Open Questions

## Assumptions
None identified

## Dependencies
None identified

## Open Questions
None identified
```

Create `skills/requirements/scripts/tests/fixtures/invalid/missing_glossary/functional/FR-001-ok.md`:

```markdown
---
id: FR-001
type: functional
tier: solution
title: Cancel pending order
description: When the customer cancels a pending order, the system shall release the reserved stock.
rationale: Reserved stock on abandoned orders blocks sales to other customers.
fit_criterion: Reserved stock returns to the available pool within 5 seconds of cancellation.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: "2026-07-13"
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Cancel pending order

## Acceptance Criteria

### AC-1 — Reserved stock is released
```gherkin
Given a pending order holding reserved stock
When the customer cancels the order
Then the reserved stock returns to the available pool
```
```

Create `skills/requirements/scripts/tests/fixtures/invalid/glossary_missing_heading/assumptions.md` with the **same content** as the `missing_glossary/assumptions.md` above, and `glossary_missing_heading/functional/FR-001-ok.md` with the **same content** as the `missing_glossary/functional/FR-001-ok.md` above.

Create `skills/requirements/scripts/tests/fixtures/invalid/glossary_missing_heading/glossary.md` — a glossary with no `## Terms` H2:

```markdown
# Glossary

- **Pending order**: an order placed but not yet dispatched.
```

- [ ] **Step 4: Refactor the artifact check and add the glossary gate**

In `skills/requirements/scripts/validate_requirements.py`, extend `SKIP_FILENAMES` (line 94) to include the glossary:

```python
# Files that live in the requirements dir but are not atomic requirements.
SKIP_FILENAMES = {
    "definition-of-done.md", "index.yaml", "assumptions.md", "glossary.md",
}
```

Add the glossary constants beside the existing context-artifact ones (after line 107):

```python
# Project-level context artifact (STO-134): assumptions/dependencies/open-questions.
CONTEXT_ARTIFACT = "assumptions.md"
REQUIRED_CONTEXT_HEADINGS = ["## Assumptions", "## Dependencies", "## Open Questions"]

# Project-level glossary artifact (STO-135): the shared vocabulary anchor that keeps
# downstream stages (M2 architecture, M3 QA) from drifting on terminology.
GLOSSARY_ARTIFACT = "glossary.md"
REQUIRED_GLOSSARY_HEADINGS = ["## Terms"]
```

Replace the whole of `check_context_artifact` (lines 406–432) with a generalized helper plus two thin callers. The helper keeps the non-UTF-8 handling in one place instead of duplicating it:

```python
def _check_project_artifact(
    reqs_dir: str, filename: str, required_headings: List[str], label: str, hint: str
) -> List[str]:
    """Gate a project-level artifact's presence and its required H2 headings.

    Presence and headings only — content is never gated. A section reading
    'None identified' is legal and passes.
    """
    path = os.path.join(reqs_dir, filename)
    if not os.path.isfile(path):
        return [f"missing required {label} '{filename}' ({hint})"]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"could not read {label} '{filename}': {exc}"]

    errors: List[str] = []
    for heading in required_headings:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(
                f"{label} '{filename}' missing required heading '{heading}'"
            )
    return errors


def check_context_artifact(reqs_dir: str) -> List[str]:
    """Assumptions/Dependencies/Open-Questions artifact (hard gate)."""
    return _check_project_artifact(
        reqs_dir,
        CONTEXT_ARTIFACT,
        REQUIRED_CONTEXT_HEADINGS,
        "context artifact",
        "Assumptions / Dependencies / Open Questions",
    )


def check_glossary_artifact(reqs_dir: str) -> List[str]:
    """Glossary artifact (hard gate). An empty 'None identified' Terms section passes."""
    return _check_project_artifact(
        reqs_dir,
        GLOSSARY_ARTIFACT,
        REQUIRED_GLOSSARY_HEADINGS,
        "glossary artifact",
        "Terms",
    )
```

In `validate()` (line 478), run the new gate alongside the existing one:

```python
    global_errors = cross_file_checks(files)
    global_errors.extend(check_context_artifact(reqs_dir))
    global_errors.extend(check_glossary_artifact(reqs_dir))
    return files, global_errors
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd skills/requirements/scripts && python3 -m pytest tests/test_validate_requirements.py -v`
Expected: PASS, all cases including the 9 parametrized `INVALID_CASES` and the 6 new glossary tests. The pre-existing context-artifact tests must still pass — that is the check on the refactor.

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/validate_requirements.py skills/requirements/scripts/tests/
git commit -m "feat(sto-135): hard-gate the glossary.md artifact in the structural validator

Generalizes the context-artifact check into a shared helper so assumptions.md
and glossary.md are gated by the same code path (presence + required headings,
content never gated). An empty 'None identified' Terms section passes."
```

---

## Task 2: Content linter — set-level check hook + `glossary-unused`

The linter's `CHECKS` registry holds per-requirement callables `(req_id, frontmatter) -> [Finding]`, which `lint_dir` runs file by file. "This term is used by no requirement" cannot be decided from one file, so it needs a **set-level** hook that runs once with the whole set.

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py` (add glossary parsing + the set-level hook; `lint_dir` at 257–267)
- Modify: `skills/requirements/scripts/tests/test_lint_content.py`
- Create: `skills/requirements/scripts/tests/fixtures/content/glossary-unused/glossary.md`
- Create: `skills/requirements/scripts/tests/fixtures/content/glossary-unused/FR-001-clean.md`
- Create: `skills/requirements/scripts/tests/fixtures/content/glossary-used/glossary.md`
- Create: `skills/requirements/scripts/tests/fixtures/content/glossary-used/FR-001-clean.md`

**Interfaces:**
- Consumes from Task 1: `vr.SKIP_FILENAMES` contains `glossary.md`, so `vr.discover_files()` never returns it as a requirement file.
- Produces: `lc.parse_glossary(reqs_dir) -> List[Tuple[str, List[str]]]` (list of `(term, aliases)`), `lc.check_glossary_unused(reqs_dir, frontmatters) -> List[Finding]`, and `lc.SET_CHECKS`, a registry of `(reqs_dir, List[frontmatter]) -> List[Finding]` callables.

- [ ] **Step 1: Write the failing tests**

Append to `skills/requirements/scripts/tests/test_lint_content.py`:

```python
# ---------------------------------------------------------------------------
# Glossary (STO-135) — set-level unused-term check.
# ---------------------------------------------------------------------------
def test_parse_glossary_reads_terms_and_aliases():
    entries = lc.parse_glossary(os.path.join(CONTENT, "glossary-used"))
    assert entries == [("Decay", ["stat decay"])]


def test_parse_glossary_absent_file_yields_no_entries():
    # The 'clean' fixture has no glossary.md — a missing glossary is the
    # structural validator's problem, not the linter's.
    assert lc.parse_glossary(os.path.join(CONTENT, "clean")) == []


def test_unused_glossary_term_is_flagged():
    findings = lc.lint_dir(os.path.join(CONTENT, "glossary-unused"))
    unused = [f for f in findings if f.rule == "glossary-unused"]
    assert len(unused) == 1
    assert "Quarantine" in unused[0].message
    assert unused[0].severity == "warn"


def test_used_glossary_term_is_not_flagged():
    findings = lc.lint_dir(os.path.join(CONTENT, "glossary-used"))
    assert [f for f in findings if f.rule == "glossary-unused"] == []


def test_glossary_term_matched_through_inflection():
    """'Decay' is used as 'decays' — inflection must count as usage."""
    fm = {"description": "The system shall apply decay while the app is closed."}
    assert lc._mentions("the pet's hunger decays over time", "Decay")
    assert lc._mentions("applying stat decay on launch", "stat decay")
    assert not lc._mentions(lc._text(fm.get("description")), "Quarantine")


def test_alias_counts_as_usage():
    findings = lc.check_glossary_unused(
        os.path.join(CONTENT, "glossary-used"),
        [{"description": "Apply stat decay on launch."}],
    )
    assert findings == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd skills/requirements/scripts && python3 -m pytest tests/test_lint_content.py -v`
Expected: FAIL — `AttributeError: module 'lint_requirements_content' has no attribute 'parse_glossary'`.

- [ ] **Step 3: Add the fixtures**

Create `skills/requirements/scripts/tests/fixtures/content/glossary-used/glossary.md`:

```markdown
# Glossary

## Terms
- **Decay**: the reduction of a pet's stat values over elapsed time. *Also: stat decay.*
```

Create `skills/requirements/scripts/tests/fixtures/content/glossary-used/FR-001-clean.md` — a requirement that *uses* the term (note "decays", an inflected form, in the description):

```markdown
---
id: FR-001
type: functional
tier: solution
title: Apply offline decay on launch
description: When the application starts, the system shall apply the elapsed-time decay to the pet's stat values.
rationale: The pet must age while the application is closed, or the neglect mechanic is meaningless.
fit_criterion: Stat values decay by the modelled rate for every hour of elapsed downtime, within a 1-minute tolerance.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: "2026-07-13"
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Apply offline decay on launch
```

Create `skills/requirements/scripts/tests/fixtures/content/glossary-unused/glossary.md` — defines a term (`Quarantine`) that no requirement uses:

```markdown
# Glossary

## Terms
- **Decay**: the reduction of a pet's stat values over elapsed time. *Also: stat decay.*
- **Quarantine**: the retention of an unreadable save file under a reserved name for diagnostics.
```

Create `skills/requirements/scripts/tests/fixtures/content/glossary-unused/FR-001-clean.md` with the **same content** as `glossary-used/FR-001-clean.md` above. (It uses `decay` but never `quarantine` — so `Quarantine` is the one unused term.)

- [ ] **Step 4: Implement glossary parsing, matching, and the set-level hook**

In `skills/requirements/scripts/lint_requirements_content.py`, add after the `_sentences` helper (line 61):

```python
# --- Glossary (STO-135) -----------------------------------------------------
# The on-disk contract: "- **Term**: definition. *Also: alias, alias.*"
_GLOSSARY_TERM_RE = re.compile(r"^\s*-\s+\*\*(?P<term>[^*]+)\*\*\s*:\s*(?P<rest>.*)$")
_GLOSSARY_ALIAS_RE = re.compile(r"\*Also:\s*(?P<aliases>[^*]+?)\.?\*")

# Requirement fields whose prose is searched for glossary-term usage.
GLOSSARY_SEARCH_FIELDS = ("title", "description", "rationale", "fit_criterion")


def parse_glossary(reqs_dir: str) -> List[Tuple[str, List[str]]]:
    """Return [(term, aliases)] parsed from glossary.md, or [] if it is absent.

    A missing glossary is the structural validator's hard gate, not a content
    finding — so this returns [] rather than raising or reporting.
    """
    path = os.path.join(reqs_dir, vr.GLOSSARY_ARTIFACT)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return []

    entries: List[Tuple[str, List[str]]] = []
    for line in text.splitlines():
        match = _GLOSSARY_TERM_RE.match(line)
        if not match:
            continue
        term = match.group("term").strip()
        aliases: List[str] = []
        alias_match = _GLOSSARY_ALIAS_RE.search(match.group("rest"))
        if alias_match:
            aliases = [
                a.strip() for a in alias_match.group("aliases").split(",") if a.strip()
            ]
        entries.append((term, aliases))
    return entries


def _mentions(haystack: str, phrase: str) -> bool:
    """True if `phrase` appears in `haystack`, tolerating ordinary inflection.

    'decay' matches 'decays' / 'decaying' / 'decayed'. Deliberately loose: the
    failure being hunted is an invented glossary entry nobody used, so being
    strict about word forms would only produce false warnings on normal English.
    """
    escaped = re.escape(phrase.strip()).replace(r"\ ", r"\s+")
    return re.search(
        rf"\b{escaped}(?:s|es|d|ed|ing)?\b", haystack, re.IGNORECASE
    ) is not None


def check_glossary_unused(
    reqs_dir: str, frontmatters: List[Dict[str, Any]]
) -> List[Finding]:
    """Warn for any glossary term (and its aliases) that no requirement uses."""
    entries = parse_glossary(reqs_dir)
    if not entries:
        return []

    corpus = " ".join(
        _text(fm.get(field)) for fm in frontmatters for field in GLOSSARY_SEARCH_FIELDS
    )

    findings: List[Finding] = []
    for term, aliases in entries:
        if any(_mentions(corpus, phrase) for phrase in (term, *aliases)):
            continue
        findings.append(Finding(
            rule="glossary-unused",
            severity="warn",
            req_id=vr.GLOSSARY_ARTIFACT,
            field="terms",
            excerpt=term,
            message=f"glossary term '{term}' is used by no requirement",
            suggested_rewrite_hint=(
                "drop the entry, or check whether a requirement should be using "
                "this term and is wording it differently"
            ),
        ))
    return findings
```

Add `Tuple` to the typing import on line 28:

```python
from typing import Any, Callable, Dict, List, Optional, Tuple
```

Register the set-level check next to the existing `CHECKS` registry (after line 254):

```python
# Registry of set-level checks, each (reqs_dir, [frontmatter]) -> List[Finding].
# These need the whole set at once — "no requirement uses this term" is not
# decidable from a single file.
SET_CHECKS: List[Callable[[str, List[Dict[str, Any]]], List[Finding]]] = [
    check_glossary_unused,
]
```

Rewrite `lint_dir` (lines 257–267) to collect the frontmatters and run both registries:

```python
def lint_dir(reqs_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    frontmatters: List[Dict[str, Any]] = []
    for path in vr.discover_files(reqs_dir):
        fm, err = vr.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        frontmatters.append(fm)
        req_id = fm.get("id") or os.path.basename(path)
        for check in CHECKS:
            findings.extend(check(req_id, fm))
    for set_check in SET_CHECKS:
        findings.extend(set_check(reqs_dir, frontmatters))
    return findings
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd skills/requirements/scripts && python3 -m pytest tests/ -v`
Expected: PASS — the whole suite, both files. `test_clean_fixture_has_no_findings` must still pass: the `clean` fixture has no `glossary.md`, so `parse_glossary` returns `[]` and the set-level check yields nothing.

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/
git commit -m "feat(sto-135): add set-level glossary-unused check to the content linter

The linter only had per-requirement checks; 'no requirement uses this term' is
not decidable from one file, so this adds a SET_CHECKS registry that runs once
with the whole set. Advisory (warn). Undefined-term detection is deliberately
left to the critic — deciding what counts as a domain term in free prose is
judgment, not regex."
```

---

## Task 3: Agent contracts — specialists, orchestrator, formatter, critic

Prose-only changes to the agent definitions. There is no test harness for agent markdown; the gate is a coherence read plus the end-to-end run in Task 5.

**Files:**
- Modify: `agents/fr-specialist.md`, `agents/nfr-specialist.md`, `agents/constraint-specialist.md` (add the optional sibling `terms` return field, next to the existing `assumptions`/`dependencies` siblings)
- Modify: `agents/requirements-orchestrator.md` (Stage 5 return shape; Stage 6.5 `glossary` block + merge rules; Stage 7 `formatter_result`; the ASCII pipeline diagram near line 33)
- Modify: `agents/requirements-formatter.md` (a `## Glossary artifact — glossary.md` section mirroring the existing `## Context artifact — assumptions.md` section at lines 127–149; `formatter_result` at 164–173)
- Modify: `agents/requirements-critic.md` (glossary pass in the coverage phase)

**Interfaces:**
- Consumes from Tasks 1–2: the on-disk format the validator gates and the linter parses. The formatter's output must match `_GLOSSARY_TERM_RE` exactly, or `glossary-unused` silently finds no terms to check.
- Produces: the `terms` / `glossary` field names the pipeline passes stage to stage.

- [ ] **Step 1: Add the optional `terms` sibling to the three specialists**

In each of `agents/fr-specialist.md`, `agents/nfr-specialist.md`, and `agents/constraint-specialist.md`, find the section describing the optional `assumptions` / `dependencies` siblings on the return object and add `terms` alongside them:

```markdown
You MAY additionally return a `terms` sibling — domain vocabulary you used whose
meaning is specific to this domain and not self-evident to a reader outside this
conversation. Apply the same bar you apply to surfacing an assumption: if a
competent engineer on another team would have to guess what the word means here,
define it.

```yaml
terms:
  - term: Decay
    definition: The reduction of a pet's stat values over elapsed time, applied whether or not the app was running.
    aliases: [stat decay]        # optional
```

Do not define ordinary English ("user", "system", "request"). Do not write terms
into requirement frontmatter — they are siblings, collected by the orchestrator at
Stage 6.5, exactly like `assumptions` and `dependencies`.
```

- [ ] **Step 2: Extend orchestrator Stage 5, Stage 6.5, and Stage 7**

In `agents/requirements-orchestrator.md`:

At **Stage 5** (the note near line 165 that specialists may return sibling `assumptions`/`dependencies`), add `terms` to that list so the collected shape is stated once.

At **Stage 6.5**, add the `glossary` block to the `context_artifact` shape:

```yaml
context_artifact:
  assumptions:            # statements believed true without proof
    - ...
  dependencies:
    - ...
  open_questions:
    - ...
  glossary:               # domain vocabulary — the M2/M3 anchor
    - term: Decay
      definition: The reduction of a pet's stat values over elapsed time, applied whether or not the app was running.
      aliases: [stat decay]
```

And add the merge rules — this is the stage that owns canonicalization:

```markdown
3. `glossary` — merge the `terms` siblings returned by the specialists (Stage 5)
   with any domain vocabulary established in the `clarification_context`. Each
   specialist saw only its own slice, so collisions are the expected case, not an
   edge case. You own the merge:

   - Collapse terms differing only in surface form (case, plural, word order) into
     one entry.
   - Collapse near-synonyms into a single canonical term, recording the losers as
     `aliases` — two specialists independently coining "stat decay" and "hunger
     decay" for one concept is the failure this prevents.
   - Drop terms that are ordinary English rather than domain vocabulary. A glossary
     defining "user" and "system" teaches a downstream agent nothing.
   - Sort entries alphabetically by `term`, so regenerated files diff cleanly.

   An empty `glossary` is legal: a project may have little domain vocabulary, and an
   honest empty section beats invented entries. The formatter renders it as
   `None identified`.
```

At **Stage 7**, add `glossary` to the `formatter_result` shape:

```yaml
formatter_result:
  files_written: [ ... ]
  index: ".sdlc/requirements/index.yaml"
  review_queue_count: 0
  context_artifact: ".sdlc/requirements/assumptions.md"
  glossary: ".sdlc/requirements/glossary.md"
  validator_rerun: { exit_code: 0 }
```

Update the ASCII pipeline diagram (near line 33) so the formatter line names the glossary alongside the other outputs:

```
[ requirements-formatter ]  writes atomic MD+YAML files + index.yaml + assumptions.md + glossary.md → formatter_result
```

- [ ] **Step 3: Teach the formatter to write `glossary.md`**

In `agents/requirements-formatter.md`, add a section immediately after the existing `## Context artifact — assumptions.md` section (which ends at line 149):

````markdown
## Glossary artifact — `glossary.md`

When the orchestrator supplies a `glossary` on the `context_artifact` (Stage 6.5),
write `.sdlc/requirements/glossary.md`. The format is a contract — the structural
validator gates the `## Terms` heading, and the content linter parses the bullets to
find terms nobody uses. Deviating from it means the linter silently finds nothing.

```markdown
# Glossary

## Terms
- **Decay**: the reduction of a pet's stat values over elapsed time, applied whether or not the app was running. *Also: stat decay.*
- **Neglect**: a sustained period during which the pet's needs go unmet, progressing toward sickness and death.
```

Rules:
- One `# Glossary` H1, one `## Terms` H2.
- One bullet per term: `- **Term**: definition.` — the term bolded, a colon, then the
  definition as a sentence.
- Aliases, when present, go in a trailing italic clause: `*Also: alias, alias.*`
- Entries sorted alphabetically by term.
- When the glossary is empty, the `## Terms` section contains the single line
  `None identified`. Never invent entries to fill it.

Like `assumptions.md`, this is a project-level file, not an atomic requirement: the
validator skips it as a requirement and hard-gates its presence and its heading.
````

Then add `glossary` to the `formatter_result` block (lines 164–173):

```yaml
formatter_result:
  files_written: [ ".sdlc/requirements/functional/FR-002-cancel-pending-order.md", ... ]
  index: ".sdlc/requirements/index.yaml"
  review_queue_count: 0            # number of confidence:low items in index.yaml's review_queue
  context_artifact: ".sdlc/requirements/assumptions.md"
  glossary: ".sdlc/requirements/glossary.md"
  validator_rerun: { exit_code: 0 }
```

- [ ] **Step 4: Give the critic the undefined-term pass**

In `agents/requirements-critic.md`, add to the coverage phase:

```markdown
### Glossary coverage

Read `glossary.md` against the approved requirement set and flag:

- **Undefined terms** — domain vocabulary used in requirement text that the glossary
  never defines. This is the direction the content linter deliberately does *not*
  check: deciding what counts as a domain term in free prose is a judgment call, and
  a regex attempting it fires on ordinary English. It is your job.
- **Circular or vacuous definitions** — "Decay: the process of decaying."
- **Padding** — entries that restate ordinary English rather than domain vocabulary.

These are advisory findings in the `critique_report`, not gate failures. The linter's
complementary `glossary-unused` finding (a defined term no requirement uses) arrives
in the `--json` output you already consume.
```

- [ ] **Step 5: Coherence read**

Read the four changed agent files end to end. Confirm: the field is called `terms` on the specialist return and `glossary` on the `context_artifact` everywhere it appears; the formatter's rendered format matches the format the validator gates and the linter parses (bold term, colon, `*Also:*` clause); no agent claims the glossary is a requirement.

- [ ] **Step 6: Commit**

```bash
git add agents/
git commit -m "feat(sto-135): wire the glossary through the agent contracts

Specialists return an optional sibling 'terms'; orchestrator Stage 6.5 merges and
canonicalizes them onto the context_artifact (collapsing near-synonyms into
aliases); the formatter writes glossary.md; the critic owns undefined-term
detection, which the linter deliberately does not attempt."
```

---

## Task 4: Wire the glossary into SKILL.md

**Files:**
- Modify: `skills/requirements/SKILL.md` (Phase 5 Step 1 formatter bullet at lines 159–162; Step 4 validation section at lines 204–225)

**Interfaces:**
- Consumes from Tasks 1–3: the validator gate and the formatter's output path.

- [ ] **Step 1: Name the glossary in the pipeline description**

In `skills/requirements/SKILL.md`, replace the formatter bullet (item 6 of the Phase 5 agent list, lines 159–162):

```markdown
6. **requirements-formatter** — writes the atomic files plus the project-level
   `assumptions.md` (Assumptions / Dependencies / Open Questions), `glossary.md`
   (the domain vocabulary that anchors the hand-off to architecture and QA), and an
   `index.yaml` carrying a `review_queue` of every `confidence: low` requirement,
   running only after the critic returns `gate: pass`.
```

- [ ] **Step 2: Name the glossary in the validation gate**

In the Step 4 section, extend the paragraph that currently describes only the `assumptions.md` gate (lines 215–217):

```markdown
The formatter also writes `.sdlc/requirements/assumptions.md` and
`.sdlc/requirements/glossary.md`. The structural validator hard-gates both: the
assumptions file must carry its three headings (`## Assumptions`, `## Dependencies`,
`## Open Questions`) and the glossary must carry `## Terms`. A missing file or
heading fails the gate. Content is never gated — a section reading `None identified`
is legal, and an honest empty glossary beats invented entries.
```

- [ ] **Step 3: Coherence read**

Read Phase 5 end to end. Confirm the glossary is mentioned in the formatter step and the validation step, and that the described gate matches what Task 1 actually implemented (presence + `## Terms`, content ungated).

- [ ] **Step 4: Commit**

```bash
git add skills/requirements/SKILL.md
git commit -m "docs(sto-135): name the glossary artifact in the requirements skill"
```

---

## Task 5: Backfill both example sets (the acceptance check)

The validator gate is breaking by construction: every set without a `glossary.md` now fails. Both committed example sets must gain one, or they fail their own validator — and the tamagotchi set is what the dev-log post (STO-198) points readers at.

Write these glossaries **from the requirement text that already exists**, not from imagination — every term must actually be used by a requirement, or the `glossary-unused` check from Task 2 will (correctly) warn.

**Files:**
- Create: `docs/requirements/examples/tamagotchi/requirements/glossary.md`
- Create: `docs/requirements/examples/gdpr/requirements/glossary.md`

**Interfaces:**
- Consumes: everything from Tasks 0–4. This task is the end-to-end acceptance check.

- [ ] **Step 1: Confirm both sets now FAIL the new gate**

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
```
Expected: exit 1 for both, each reporting `missing required glossary artifact 'glossary.md' (Terms)` under "Set-level errors". This is the gate proving it works.

- [ ] **Step 2: Read the tamagotchi requirements before writing its glossary**

Run: `grep -h "^title:\|^description:" docs/requirements/examples/tamagotchi/requirements/*/*.md`

Take the domain vocabulary from what you read. The set is about a pet with stats that degrade over elapsed time, a neglect-to-sickness-to-death progression, mood expression, and a corrupted-save recovery path.

- [ ] **Step 3: Write the tamagotchi glossary**

Create `docs/requirements/examples/tamagotchi/requirements/glossary.md`:

```markdown
# Glossary

## Terms
- **Decay**: the reduction of a pet's stat values over elapsed time, applied whether or not the application was running. *Also: stat decay.*
- **Elapsed decay**: the decay accrued while the application was closed, computed from the wall-clock interval since the last save and applied on launch.
- **Mood**: the pet's outward expression, derived from its current stat values and shown to the user as a visual state.
- **Neglect**: a sustained period during which the pet's needs go unmet, progressing it toward sickness and, ultimately, death.
- **Quarantine**: the retention of an unreadable or corrupted save file under a reserved name for diagnostics, rather than deleting it.
- **Stat**: a single numeric dimension of the pet's condition — hunger, happiness, cleanliness, or health.
```

- [ ] **Step 4: Write the GDPR glossary**

Run: `grep -h "^title:\|^description:" docs/requirements/examples/gdpr/requirements/*/*.md` and read the terms in use.

Create `docs/requirements/examples/gdpr/requirements/glossary.md`:

```markdown
# Glossary

## Terms
- **Data subject**: the identified or identifiable natural person whose personal data the system holds, and who exercises the rights these requirements implement.
- **Erasure**: the permanent, irreversible removal of a data subject's personal data on request. *Also: right to be forgotten.*
- **Personal data**: any information relating to an identified or identifiable natural person, as defined by the GDPR.
- **Statutory retention**: a legal obligation to retain specified records for a defined period, which overrides an erasure request for the data it covers.
```

- [ ] **Step 5: Run both gates on both sets**

```bash
for set in tamagotchi gdpr; do
  echo "=== $set ==="
  python3 skills/requirements/scripts/validate_requirements.py "docs/requirements/examples/$set/requirements" | tail -1
  python3 skills/requirements/scripts/lint_requirements_content.py "docs/requirements/examples/$set/requirements" | tail -3
done
```

Expected: tamagotchi `22/22 file(s) passed, 0 failed`; GDPR `8/8 file(s) passed, 0 failed`; both linters print `No content anti-patterns found.`

If a `glossary-unused` warning appears, the term is not actually used in that set's requirement prose — **remove the term rather than editing requirements to justify it.** The glossary describes the requirements; it does not drive them.

- [ ] **Step 6: Run the full test suite**

Run: `cd skills/requirements/scripts && python3 -m pytest tests/ -v`
Expected: PASS, entire suite.

- [ ] **Step 7: Commit**

```bash
git add docs/requirements/examples
git commit -m "docs(sto-135): add glossary.md to both example requirement sets

Terms are taken from each set's existing requirement prose, so the linter's
glossary-unused check stays clean."
```

---

## Self-Review

**Spec coverage.** Every spec section maps to a task: Part A (agent contracts) → Task 3; Part B (on-disk format) → the Global Constraints plus Task 3 Step 3; Part C (validator) → Task 1; Part D (linter) → Task 2; Part E (critic) → Task 3 Step 4; Part F (layout prerequisite) → Task 0; Part G (backfill + docs) → Tasks 4 and 5. The spec's build order (0→5) is the task order.

**Type/name consistency.** The specialist sibling is `terms` (a list of `{term, definition, aliases?}`) everywhere; the `context_artifact` key is `glossary`; the linter helpers are `parse_glossary`, `_mentions`, `check_glossary_unused`, registered in `SET_CHECKS`; the validator exposes `check_glossary_artifact` and `GLOSSARY_ARTIFACT`, and the linter imports the latter as `vr.GLOSSARY_ARTIFACT` (defined in Task 1, consumed in Task 2 — the ordering holds).

**Known-good invariants to protect.** Task 1's refactor must keep the substrings `context artifact`, `missing required heading`, and `could not read` in its messages, because existing tests match on them. Task 2's set-level check must return `[]` when `glossary.md` is absent, or the `content/clean` fixture stops being finding-free and `test_clean_fixture_has_no_findings` breaks.

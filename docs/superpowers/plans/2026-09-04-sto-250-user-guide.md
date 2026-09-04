# User Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Groundwork user guide — five prose pages following the shape of a run, two generated reference pages, and the two worked example sets as 15 generated pages — on the site pass 1 deployed.

**Architecture:** Two Python exporters read the repository's own sources and write committed output that CI re-checks: `export_reference.py` (extended with a traceability rule registry and the two interviews' coverage-area lists) and a new `export_examples.py` (the example sets, consolidated by artifact type). Hand-written pages are `.mdx` and render that generated data through components; generated pages are `.md` so an artifact body cannot break the build.

**Tech Stack:** Python 3.12 stdlib, pytest, Nextra 4 / Next 16, React 19, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-04-sto-250-user-guide-design.md`

## Global Constraints

- **Stdlib only** in every Python script under `site/scripts/` and `skills/`. No third-party imports outside tests.
- **The site build stays Python-free.** No workflow step may put Python on the critical path of `npm run build`.
- **Generated output is committed and gated.** Every exporter supports `--check`, which exits 1 on drift and writes nothing.
- **Generated pages are `.md`. Hand-written pages are `.mdx`.** No exceptions in either direction.
- **Cross-links use absolute site-relative paths with a trailing slash and no `basePath`** — the form `site/content/index.mdx` already uses, e.g. `/guide/examples/tamagotchi/requirements/functional/#fr-001`. Never prefix `/groundwork`.
- **Heading anchors are explicit**, via Nextra's `[#custom-id]` syntax. Never rely on the slugifier.
- **No artifact prose is hand-written into the site.** Every requirement, component, interface, ADR and diagram body reaches a page through the generator.
- **TDD**: the failing test is written and observed failing before the implementation, in every task that has one.
- Run the full suite with `python3 -m pytest -q` from the repo root. Baseline at the start of this plan: **291 passed**.

---

### Task 1: CI hardening — action bumps, a site build, and a built-output assertion

Folds in STO-263 B1, B2 and B3. It goes first so every task after it lands on a workflow that actually builds the site.

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: a `build` job in `ci.yml` named `Site builds`, running on every pull request. Task 9 adds a second `grep` assertion to its final step.

- [ ] **Step 1: Confirm the built output path before asserting on it**

Do not guess where `next build` writes the rule reference. Find out:

```bash
cd site && npm ci && npm run build && find out -name 'index.html' | sort | head -20
```

Expected: `out/guide/reference/rules/index.html` exists (`trailingSlash: true` gives directory-per-route; `basePath` does not change the output tree). If the real path differs, use the real path in Step 3 and note the difference in the commit body.

- [ ] **Step 2: Bump the six action pins**

Current pins are several majors behind. In **both** workflow files, replace:

| Old | New |
|---|---|
| `actions/checkout@v4` | `actions/checkout@v7` |
| `actions/setup-python@v5` | `actions/setup-python@v7` |
| `actions/setup-node@v4` | `actions/setup-node@v7` |
| `actions/configure-pages@v5` | `actions/configure-pages@v6` |
| `actions/upload-pages-artifact@v3` | `actions/upload-pages-artifact@v5` |

`actions/deploy-pages@v5` is already current — leave it.

Before committing, check each bump against GitHub's own current Pages starter workflow, which is the authority pass 1 pinned to:

```bash
gh api repos/actions/starter-workflows/contents/pages/nextjs.yml \
  --jq '.content' | base64 -d | grep -n 'uses:'
```

If the starter pins something lower than the table above, follow the starter and record why in the commit body. `upload-pages-artifact` v3→v5 and `configure-pages` v5→v6 are the two that can carry breaking changes; read their release notes rather than assuming.

- [ ] **Step 3: Add the Node-only build job to `ci.yml`**

Append to `.github/workflows/ci.yml`, as a second job under `jobs:`:

```yaml
  build:
    name: Site builds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-node@v7
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: site/package-lock.json

      - name: Install
        run: npm ci
        working-directory: site

      # No Python step, on purpose: this job proves the site builds from
      # committed generated data alone, which is the property pages.yml
      # depends on. Adding Python here would hide a missing committed file.
      - name: Build
        run: npm run build
        working-directory: site

      # The generated tables render from committed JSON. RuleTable degrades to
      # an error paragraph rather than throwing when a top-level key is absent
      # from rules.json, so `next build` would exit 0 on a broken page. Assert
      # a known row actually reached the HTML.
      - name: Built pages carry their generated rows
        run: grep -q 'god-component' out/guide/reference/rules/index.html
        working-directory: site
```

- [ ] **Step 4: Verify the assertion fails when it should**

Prove the grep is load-bearing rather than decorative:

```bash
cd site
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('content/_generated/rules.json')
d = json.loads(p.read_text())
d.pop('design')
p.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
PY
npm run build && grep -q 'god-component' out/guide/reference/rules/index.html; echo "grep exit: $?"
```

Expected: `next build` exits 0 (the silent-degrade path) and `grep exit: 1`. Then restore:

```bash
python3 scripts/export_reference.py && git diff --exit-code content/_generated/rules.json
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/pages.yml
git commit -m "ci(sto-250): build the site on every PR, assert its generated rows, bump action pins

Folds in STO-263 B1, B2 and B3. The build job runs no Python, so the
Python-free-build constraint holds and a missing committed file fails
rather than being regenerated out of sight.

The grep is verified load-bearing: removing the design key from rules.json
leaves next build exiting 0 and the grep exiting 1."
```

---

### Task 2: `RULES` registry in `validate_traceability.py`

**Files:**
- Modify: `skills/design/scripts/validate_traceability.py` (docstring lines 11–23; new `RULES` near the `ERROR`/`WARN` constants at line 72)
- Test: `skills/design/scripts/tests/test_validate_traceability.py`

**Interfaces:**
- Produces: `validate_traceability.RULES`, a `List[Dict[str, Any]]`. Each entry has exactly the keys `id`, `severities`, `applies_to`, `fields`, `summary` — the same five the two linters' registries use, so `RuleTable` can render it unchanged. `fields` is always `[]` here, because this module's `Finding` has no `field` attribute.

- [ ] **Step 1: Write the failing tests**

Append to `skills/design/scripts/tests/test_validate_traceability.py`:

```python
# ---------------------------------------------------------------------------
# Rule registry (STO-250 pass 2)
# ---------------------------------------------------------------------------
import inspect
import re

_RULE_LITERAL_RE = re.compile(r'rule=["\']([a-z0-9-]+)["\']')


def test_rules_registry_matches_source_literals():
    # Source-derived, not corpus-derived. This module has no CHECKS list to
    # enumerate, and a source sweep also catches the case a fixture-derived
    # test cannot: a rule that is both undeclared AND unexercised (STO-263 A2).
    emitted = set(_RULE_LITERAL_RE.findall(inspect.getsource(vt)))
    declared = {r["id"] for r in vt.RULES}
    assert emitted == declared


def test_rules_registry_entries_are_complete():
    for rule in vt.RULES:
        assert set(rule) == {"id", "severities", "applies_to", "fields", "summary"}
        assert rule["id"] and rule["summary"]
        assert rule["severities"]
        # Traceability findings carry no `field`, unlike the content linters'.
        assert rule["fields"] == []
        assert rule["applies_to"] in {
            "design artifact", "requirement", "adr", "the index",
        }


def test_declared_severities_are_the_ones_the_tool_can_emit():
    for rule in vt.RULES:
        assert set(rule["severities"]) <= {vt.ERROR, vt.WARN}


def test_every_declared_rule_is_exercised_by_a_fixture(capsys):
    # The second direction the source sweep cannot give: a declared rule that
    # no fixture proves. Runs every fixture case and collects what fires.
    seen = set()
    for case in sorted(os.listdir(FIXTURES)):
        if not os.path.isdir(os.path.join(FIXTURES, case)):
            continue
        run(case, "--json")
        payload = json.loads(capsys.readouterr().out)
        seen.update(f["rule"] for f in payload["findings"])
    assert {r["id"] for r in vt.RULES} <= seen
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_traceability.py -q -k rules`
Expected: FAIL — `AttributeError: module 'validate_traceability' has no attribute 'RULES'`.

- [ ] **Step 3: Add the registry**

Insert into `skills/design/scripts/validate_traceability.py`, immediately after `_SEVERITY_ORDER` (line 74):

```python
# The published rule reference is generated from this list (STO-250 pass 2).
# It is the single declaration of what this tool checks: the module docstring
# used to restate it in prose, which was a second place for the same facts to
# drift. Keys match the two content linters' registries so one component
# renders all three. `fields` is empty by construction — a traceability
# Finding names an artifact and a path, never a frontmatter field.
RULES: List[Dict[str, Any]] = [
    {
        "id": "dangling-trace",
        "severities": [ERROR],
        "applies_to": "design artifact",
        "fields": [],
        "summary": (
            "A design artifact's traces_from names a requirement ID that "
            "does not exist in the requirements set."
        ),
    },
    {
        "id": "adr-driver-unresolved",
        "severities": [ERROR],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A requirement ID listed under '## Decision Drivers' does not "
            "resolve. A listed driver is the leading token of a list item."
        ),
    },
    {
        "id": "dangling-reverse-trace",
        "severities": [ERROR],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A requirement's non-empty traces_to.design names a design ID "
            "that does not exist. Fixed by hand in the requirements stage — "
            "there is no migration script and no bypass flag."
        ),
    },
    {
        "id": "misplaced-requirement-trace",
        "severities": [ERROR],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A requirement ID sits in traces_to.tests or traces_to.code, "
            "which hold test and code references. Fixed by hand in the "
            "requirements stage; the message names the exact edit."
        ),
    },
    {
        "id": "uncovered-fr",
        "severities": [WARN],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A functional requirement is cited by no component. Excludes "
            "priority: wont and status: obsolete."
        ),
    },
    {
        "id": "adr-driver-untraced",
        "severities": [WARN],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A listed decision driver resolves but is absent from that ADR's "
            "traces_from."
        ),
    },
    {
        "id": "adr-driver-unlisted",
        "severities": [WARN],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A requirement ID appears in the drivers prose but not as a list "
            "item, so it was never checked as a driver. A warning rather than "
            "an error: ordinary English mentioning an ID is history, not a "
            "defect."
        ),
    },
    {
        "id": "index-unparseable",
        "severities": [WARN],
        "applies_to": "the index",
        "fields": [],
        "summary": (
            "A file's frontmatter did not parse, so it is missing from the "
            "index and the sweep was not complete."
        ),
    },
    {
        "id": "duplicate-id",
        "severities": [WARN],
        "applies_to": "the index",
        "fields": [],
        "summary": (
            "Two files claim the same ID; only the last one read was indexed."
        ),
    },
]
```

- [ ] **Step 4: Replace the docstring's prose table with a pointer**

In the module docstring, delete the `It runs these rules::` block (lines 11–23 — the nine indented lines and their heading) and put in its place:

```
The rules it runs are declared in ``RULES`` below, which is also what the
documentation site renders. There is deliberately no second list here: a
restated table is a place for the same facts to drift.
```

Leave the paragraph that follows about index caveats travelling the findings channel — it explains *why* two of the rules exist and is not a restatement.

- [ ] **Step 5: Run the tests**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_traceability.py -q`
Expected: PASS, all of them.

Then the full suite: `python3 -m pytest -q` — expected 291 + 4 = **295 passed**.

If `test_every_declared_rule_is_exercised_by_a_fixture` fails, it has found a
real gap: a rule this tool can emit that no fixture proves. Add the missing
fixture case rather than removing the rule from `RULES` or relaxing the
assertion — a rule the site publishes and no test exercises is exactly what
the registry exists to make visible.

- [ ] **Step 6: Verify the sync test is load-bearing**

Rename one literal and confirm the test catches it:

```bash
sed -i 's/rule="duplicate-id"/rule="duplicate-ids"/' skills/design/scripts/validate_traceability.py
python3 -m pytest skills/design/scripts/tests/test_validate_traceability.py -q -k rules_registry_matches
```

Expected: FAIL. Then revert: `git checkout skills/design/scripts/validate_traceability.py` and re-apply Steps 3–4, or `sed` the name back.

- [ ] **Step 7: Commit**

```bash
git add skills/design/scripts/validate_traceability.py skills/design/scripts/tests/test_validate_traceability.py
git commit -m "feat(sto-250): declare validate_traceability's rules in a RULES registry

The docstring restated all nine rules in prose; the gates page would have
restated them a third time. One declaration now, rendered by the site.

The sync test is source-derived rather than corpus-derived — this module has
no CHECKS list, and a source sweep also closes STO-263 A2's gap for this
registry. The two existing linter registries are untouched."
```

---

### Task 3: Export the traceability rules and drop `RuleTable`'s unused column

**Files:**
- Modify: `site/scripts/export_reference.py` (`export_rules`, ~line 50)
- Modify: `site/components/RuleTable.jsx`
- Modify: `site/content/_generated/rules.json` (regenerated, not hand-edited)
- Test: `site/scripts/tests/test_export_reference.py`

**Interfaces:**
- Consumes: `validate_traceability.RULES` from Task 2.
- Produces: `rules.json` gains a third top-level key, `traceability`, with the same `{linter, rules}` shape as `design` and `requirements`. Task 12's `gates.mdx` renders it as `<RuleTable linter="traceability" />`.

- [ ] **Step 1: Write the failing test**

Append to `site/scripts/tests/test_export_reference.py`:

```python
def test_rules_export_carries_the_traceability_registry():
    payload = export_reference.export_rules()
    assert set(payload) == {"design", "requirements", "traceability"}
    section = payload["traceability"]
    assert section["linter"] == "validate_traceability.py"
    assert {r["id"] for r in section["rules"]} == {
        "dangling-trace",
        "adr-driver-unresolved",
        "dangling-reverse-trace",
        "misplaced-requirement-trace",
        "uncovered-fr",
        "adr-driver-untraced",
        "adr-driver-unlisted",
        "index-unparseable",
        "duplicate-id",
    }


def test_traceability_rules_declare_no_fields():
    # The Fields column is meaningless for this tool; RuleTable drops it.
    for rule in export_reference.export_rules()["traceability"]["rules"]:
        assert rule["fields"] == []
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -q -k traceability`
Expected: FAIL — `AssertionError` on the key set, since only two keys exist.

- [ ] **Step 3: Extend the exporter**

In `site/scripts/export_reference.py`, add to the import block after `lint_requirements_content`:

```python
import validate_traceability as vt  # noqa: E402
```

`skills/design/scripts` is already on `sys.path` (the loop at the top of the file), so no path change is needed.

Then extend `export_rules`:

```python
        "traceability": {
            "linter": "validate_traceability.py",
            "rules": vt.RULES,
        },
```

Update that function's docstring to say three registries rather than two, and note that traceability's are gating while the other two are advisory.

- [ ] **Step 4: Regenerate and run the tests**

```bash
python3 site/scripts/export_reference.py
python3 -m pytest site/scripts/tests -q
python3 site/scripts/export_reference.py --check
```

Expected: tests pass; `--check` exits 0 after the regenerate.

- [ ] **Step 5: Drop the Fields column when no rule declares one**

In `site/components/RuleTable.jsx`, after the `section` guard, add:

```jsx
  // Traceability findings name an artifact and a path, never a frontmatter
  // field, so their registry declares fields: []. Render the column only
  // where it carries something, rather than a column of em dashes.
  const hasFields = section.rules.some(rule => rule.fields.length > 0)
```

Then make the header cell and body cell conditional:

```jsx
          <Table.Th>Applies to</Table.Th>
          {hasFields && <Table.Th>Fields</Table.Th>}
          <Table.Th>What it catches</Table.Th>
```

```jsx
            <Table.Td>{rule.applies_to}</Table.Td>
            {hasFields && (
              <Table.Td><code>{rule.fields.join(' / ')}</code></Table.Td>
            )}
            <Table.Td>{rule.summary}</Table.Td>
```

- [ ] **Step 6: Confirm both table shapes render**

```bash
cd site && npm run build
grep -c '<th' out/guide/reference/rules/index.html
```

Expected: the two existing tables still render five columns each. The traceability table has no page yet — Task 12 adds it; this step only confirms nothing regressed.

- [ ] **Step 7: Commit**

```bash
git add site/scripts/export_reference.py site/scripts/tests/test_export_reference.py \
        site/content/_generated/rules.json site/components/RuleTable.jsx
git commit -m "feat(sto-250): export the traceability rule registry; RuleTable drops an empty column"
```

---

### Task 4: `stages.json` — the two interviews' coverage areas

**Files:**
- Modify: `site/scripts/export_reference.py`
- Create: `site/content/_generated/stages.json`
- Create: `site/components/CoverageAreas.jsx`
- Test: `site/scripts/tests/test_export_reference.py`

**Interfaces:**
- Produces: `stages.json`, shaped
  `{"requirements": {"skill": str, "heading": str, "areas": [{"name": str, "detail": str}]}, "design": {...}}`.
  Tasks 10 and 11 render it as `<CoverageAreas stage="requirements" />` / `stage="design"`.

- [ ] **Step 1: Write the failing test**

Append to `site/scripts/tests/test_export_reference.py`:

```python
def test_stages_export_carries_six_areas_each():
    payload = export_reference.export_stages()
    assert set(payload) == {"requirements", "design"}
    for stage in payload.values():
        assert len(stage["areas"]) == 6
        for area in stage["areas"]:
            assert set(area) == {"name", "detail"}
            assert area["name"] and area["detail"]


def test_stages_export_reads_the_real_skill_files():
    payload = export_reference.export_stages()
    req = [a["name"] for a in payload["requirements"]["areas"]]
    des = [a["name"] for a in payload["design"]["areas"]]
    assert req[0] == "Core functionality"
    assert req[-1] == "Out of scope"
    assert des[0] == "Runtime and stack"
    assert des[-1] == "Team constraints"


def test_stages_export_raises_when_the_anchor_moves():
    # A silent empty result is the failure mode this parser must not have:
    # the drift gate compares committed JSON to current output, so a
    # consistently empty extraction would read as "current" forever.
    with pytest.raises(ValueError, match="anchor not found"):
        export_reference._coverage_areas("no such anchor here", "## Missing")
```

Add `import pytest` at the top of the test file if it is not already imported.

- [ ] **Step 2: Run it and watch it fail**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -q -k stages`
Expected: FAIL — `AttributeError: module 'export_reference' has no attribute 'export_stages'`.

- [ ] **Step 3: Implement the parser**

Add to `site/scripts/export_reference.py`, after `export_agents`:

```python
# The two interviews' coverage areas, by the exact line each list follows.
# Anchors rather than heading names because the two skills phrase the
# introduction differently and neither is a heading.
STAGE_SOURCES = {
    "requirements": {
        "skill": "skills/requirements/SKILL.md",
        "heading": "**Coverage areas:**",
    },
    "design": {
        "skill": "skills/design/SKILL.md",
        "heading": (
            "Six coverage areas the requirement set cannot carry, "
            "by construction:"
        ),
    },
}

_AREA_ITEM_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s+—\s+(.+)$")


def _coverage_areas(text: str, anchor: str) -> List[Dict[str, str]]:
    """Parse the numbered coverage-area list that follows ``anchor``.

    Raises rather than returning an empty list when the anchor moves or the
    list shape changes. A parser that degrades silently here would be worse
    than none: the drift gate only compares the committed JSON to what this
    function currently produces, so a consistently empty extraction reads as
    "current" forever and the published page quietly lists nothing.
    """
    index = text.find(anchor)
    if index == -1:
        raise ValueError(f"anchor not found: {anchor!r}")

    areas: List[Dict[str, str]] = []
    for line in text[index + len(anchor):].splitlines():
        stripped = line.strip()
        if not stripped:
            if areas:
                break
            continue
        match = _AREA_ITEM_RE.match(stripped)
        if not match:
            break
        areas.append(
            {"name": match.group(1).strip(), "detail": match.group(2).strip()}
        )

    if not areas:
        raise ValueError(f"no numbered areas found after anchor: {anchor!r}")
    return areas


def export_stages() -> Dict[str, Dict[str, Any]]:
    """The two interviews' coverage areas, read from the skill files.

    Deliberately narrow. Generating the area *names* means a page cannot list
    five areas when the skill has six. Generating the surrounding narrative
    would turn the two stage pages into tables, which is the opposite of what
    they are for.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for stage, source in STAGE_SOURCES.items():
        path = os.path.join(REPO_ROOT, source["skill"])
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out[stage] = {
            "skill": source["skill"],
            "heading": source["heading"],
            "areas": _coverage_areas(text, source["heading"]),
        }
    return out
```

Register the output:

```python
OUTPUTS = {
    "rules.json": export_rules,
    "fields.json": export_fields,
    "agents.json": export_agents,
    "stages.json": export_stages,
}
```

- [ ] **Step 4: Run the tests and generate**

```bash
python3 -m pytest site/scripts/tests -q
python3 site/scripts/export_reference.py
cat site/content/_generated/stages.json
```

Expected: tests pass; the JSON carries six areas per stage with the names from Step 1's assertions.

- [ ] **Step 5: Write the component**

Create `site/components/CoverageAreas.jsx`:

```jsx
import { Table } from 'nextra/components'
import stages from '../content/_generated/stages.json'

/**
 * Renders one interview's coverage areas from generated data.
 *
 * The names and one-line details come from the skill file that implements
 * the interview, so this list cannot show five areas when the skill asks
 * about six. The prose around it on the page is hand-written on purpose —
 * generating the explanation would turn a guide into a schema dump.
 */
export function CoverageAreas({ stage }) {
  const section = stages[stage]

  if (!section) {
    return (
      <p>
        <strong>CoverageAreas error:</strong> no data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(stages).join(', ')}.
      </p>
    )
  }

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Area</Table.Th>
          <Table.Th>What it covers</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {section.areas.map(area => (
          <Table.Tr key={area.name}>
            <Table.Td><strong>{area.name}</strong></Table.Td>
            <Table.Td>{area.detail}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add site/scripts/export_reference.py site/scripts/tests/test_export_reference.py \
        site/content/_generated/stages.json site/components/CoverageAreas.jsx
git commit -m "feat(sto-250): generate the two interviews' coverage areas as stages.json

The parser raises on a missing anchor rather than returning an empty list.
A silent degrade here would be invisible to the drift gate, which only
compares committed JSON to current output."
```

---

### Task 5: `reference/fields` — the frontmatter field reference

**Files:**
- Create: `site/components/FieldTable.jsx`
- Create: `site/content/guide/reference/fields.mdx`
- Modify: `site/content/guide/reference/_meta.js`

**Interfaces:**
- Consumes: `site/content/_generated/fields.json`, generated and gated since pass 1. Entry shape: `{name, type, enum, required_for, description}`. `type` may be a string or a list (e.g. `parent_scope` is `["string", "null"]`). `required_for` is `["*"]` for always-required, a list of type names for conditionally-required, or `[]` for optional.

- [ ] **Step 1: Write the component**

Create `site/components/FieldTable.jsx`:

```jsx
import { Table } from 'nextra/components'
import fields from '../content/_generated/fields.json'

/**
 * Renders one stage's frontmatter fields from the artifact JSON Schema.
 *
 * The schema is the binding contract a validator enforces; this table is a
 * projection of it, never a restatement. Adding a field to the schema and
 * re-running the exporter adds a row here.
 */
export function FieldTable({ stage }) {
  const rows = fields[stage]

  if (!rows) {
    return (
      <p>
        <strong>FieldTable error:</strong> no field data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(fields).join(', ')}.
      </p>
    )
  }

  const required = entry => {
    if (entry.required_for.length === 0) return 'optional'
    if (entry.required_for.includes('*')) return 'always'
    return entry.required_for.join(', ')
  }

  const type = entry =>
    Array.isArray(entry.type) ? entry.type.join(' | ') : entry.type

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Field</Table.Th>
          <Table.Th>Type</Table.Th>
          <Table.Th>Required</Table.Th>
          <Table.Th>Values</Table.Th>
          <Table.Th>Meaning</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {rows.map(entry => (
          <Table.Tr key={entry.name}>
            <Table.Td><code>{entry.name}</code></Table.Td>
            <Table.Td>{type(entry)}</Table.Td>
            <Table.Td>{required(entry)}</Table.Td>
            <Table.Td>
              {entry.enum.length > 0
                ? entry.enum.map(v => <code key={v}>{v} </code>)
                : '—'}
            </Table.Td>
            <Table.Td>{entry.description}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
```

- [ ] **Step 2: Write the page**

Create `site/content/guide/reference/fields.mdx`:

```mdx
import { FieldTable } from '../../../components/FieldTable'

# Frontmatter fields

Every artifact Groundwork writes is a Markdown file whose YAML frontmatter is
validated against a JSON Schema. These tables are generated from those two
schemas, so a field that exists in the schema appears here and a field that
does not, does not.

The structural validators — `validate_requirements.py` and
`validate_design.py` — enforce exactly what these tables describe. See
[Gates](/guide/gates/) for what happens when one fails, and
[Reading an artifact](/guide/reading-an-artifact/) for what the fields mean
in practice rather than in schema terms.

## Requirement fields

Required by `validate_requirements.py` over `.sdlc/requirements`.

<FieldTable stage="requirements" />

## Design fields

Required by `validate_design.py` over `.sdlc/design`.

<FieldTable stage="design" />

## Reading the Required column

`always` means every artifact of that stage carries the field. A list of type
names means the field is required only for those types — `ears_pattern` is
required for `functional` requirements and meaningless for the rest.
`optional` means the schema permits it and never demands it.
```

- [ ] **Step 3: Add it to the nav**

Replace `site/content/guide/reference/_meta.js` with:

```js
export default {
  rules: 'Content rules',
  fields: 'Frontmatter fields'
}
```

- [ ] **Step 4: Build and check the page renders rows**

```bash
cd site && npm run build
grep -c '<tr' out/guide/reference/fields/index.html
grep -q 'ears_pattern' out/guide/reference/fields/index.html && echo OK
```

Expected: a row count well above 20 (both schemas), and `OK`.

- [ ] **Step 5: Commit**

```bash
git add site/components/FieldTable.jsx site/content/guide/reference/fields.mdx \
        site/content/guide/reference/_meta.js
git commit -m "feat(sto-250): publish the frontmatter field reference, generated from both schemas"
```

---

### Task 6: `reference/agents` — the agent roster

**Files:**
- Create: `site/components/AgentTable.jsx`
- Create: `site/content/guide/reference/agents.mdx`
- Modify: `site/content/guide/reference/_meta.js`

**Interfaces:**
- Consumes: `site/content/_generated/agents.json`, a flat list of `{name, title, description}`, generated and gated since pass 1.

- [ ] **Step 1: Write the component**

Create `site/components/AgentTable.jsx`:

```jsx
import { Table } from 'nextra/components'
import agents from '../content/_generated/agents.json'

/**
 * The agent roster, from each agent file's frontmatter and H1.
 *
 * A roster, not an explanation: stage order, hand-off contracts and the
 * reasoning behind the pipeline's shape belong to the architecture guide,
 * and this page links there rather than reproducing any of it.
 */
export function AgentTable() {
  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Agent</Table.Th>
          <Table.Th>Role</Table.Th>
          <Table.Th>What it does</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {agents.map(agent => (
          <Table.Tr key={agent.name}>
            <Table.Td><code>{agent.name}</code></Table.Td>
            <Table.Td>{agent.title}</Table.Td>
            <Table.Td>{agent.description}</Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
```

- [ ] **Step 2: Write the page**

Create `site/content/guide/reference/agents.mdx`:

```mdx
import { AgentTable } from '../../../components/AgentTable'

# Agents

Groundwork's two stages are pipelines of specialist agents, each with one job
and an explicit hand-off to the next. This table is generated from the agent
files themselves — their frontmatter descriptions and titles — so it is the
roster as it actually ships.

It is only a roster. Which agent runs when, what each one passes to the next,
and why the pipeline is shaped this way are the architecture guide's subject:
see [Architecture](/architecture/).

You do not invoke these directly. The two skills dispatch them; see
[The requirements stage](/guide/requirements-stage/) and
[The design stage](/guide/design-stage/) for what that looks like from the
outside.

<AgentTable />
```

- [ ] **Step 3: Add it to the nav**

Replace `site/content/guide/reference/_meta.js` with:

```js
export default {
  rules: 'Content rules',
  fields: 'Frontmatter fields',
  agents: 'Agents'
}
```

- [ ] **Step 4: Build and confirm all fifteen rows render**

```bash
cd site && npm run build
grep -o 'requirements-orchestrator' out/guide/reference/agents/index.html | head -1
grep -c '<tr' out/guide/reference/agents/index.html
```

Expected: the agent name is found; the row count is 16 (fifteen agents plus the header row).

- [ ] **Step 5: Commit**

```bash
git add site/components/AgentTable.jsx site/content/guide/reference/agents.mdx \
        site/content/guide/reference/_meta.js
git commit -m "feat(sto-250): publish the agent roster, generated from the agent files"
```

---

### Task 7: `export_examples.py` — set discovery and the artifact model

The generator is split across three tasks: this one reads and models, Task 8 renders, Task 9 writes and gates.

**Files:**
- Create: `site/scripts/export_examples.py`
- Create: `site/scripts/tests/test_export_examples.py`

**Interfaces:**
- Produces, for Task 8:
  - `Artifact` dataclass: `artifact_id: str`, `title: str`, `source: str` (repo-relative), `meta: Dict[str, Any]`, `body: str`.
  - `GROUPS: List[Tuple[str, str, str]]` — `(stage, directory, page title)`.
  - `PROJECT_FILES: Dict[str, List[str]]` — stage to filenames.
  - `discover_sets() -> List[str]` — sorted set names.
  - `load_group(set_name, stage, directory) -> List[Artifact]` — ID-sorted.
  - `split_frontmatter(text) -> str` — the body after the frontmatter block.

- [ ] **Step 1: Write the failing tests**

Create `site/scripts/tests/test_export_examples.py`:

```python
"""Tests for the worked-example exporter (STO-250 pass 2).

These run against the real example sets under docs/requirements/examples/,
not fixtures. The sets are committed, regenerated deliberately by STO-219,
and are exactly what the site publishes — a fixture copy would be a second
thing to keep in step.
"""
import os

import export_examples as ee


def test_discovers_both_sets():
    assert ee.discover_sets() == ["gdpr", "tamagotchi"]


def test_loads_every_functional_requirement_in_id_order():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    assert len(artifacts) == 12
    assert [a.artifact_id for a in artifacts] == [
        f"FR-{n:03d}" for n in range(1, 13)
    ]


def test_artifact_carries_title_meta_and_body():
    first = ee.load_group("tamagotchi", "requirements", "functional")[0]
    assert first.artifact_id == "FR-001"
    assert first.title == "Persist pet state on stat change and app close"
    assert first.meta["type"] == "functional"
    assert first.meta["ears_pattern"] == "event"
    assert first.body.startswith("# FR-001")
    assert "## Acceptance Criteria" in first.body


def test_group_counts_match_the_committed_sets():
    expected = {
        ("tamagotchi", "requirements", "functional"): 12,
        ("tamagotchi", "requirements", "non-functional"): 9,
        ("tamagotchi", "requirements", "constraints"): 3,
        ("tamagotchi", "requirements", "business-rules"): 2,
        ("tamagotchi", "design", "components"): 19,
        ("tamagotchi", "design", "interfaces"): 31,
        ("tamagotchi", "design", "adr"): 7,
        ("tamagotchi", "design", "diagrams"): 4,
        ("gdpr", "requirements", "functional"): 3,
        ("gdpr", "requirements", "non-functional"): 15,
        ("gdpr", "requirements", "constraints"): 1,
        ("gdpr", "requirements", "business-rules"): 2,
    }
    for (set_name, stage, directory), count in expected.items():
        got = ee.load_group(set_name, stage, directory)
        assert len(got) == count, f"{set_name}/{stage}/{directory}"


def test_missing_group_is_empty_not_an_error():
    # gdpr has no design stage at all. That is a legal shape, not a failure.
    assert ee.load_group("gdpr", "design", "components") == []


def test_split_frontmatter_returns_the_body_only():
    text = "---\nid: FR-001\n---\n\n# FR-001 — Title\n\nProse.\n"
    assert ee.split_frontmatter(text) == "# FR-001 — Title\n\nProse.\n"


def test_split_frontmatter_leaves_a_file_without_frontmatter_alone():
    text = "# Assumptions\n\nProse.\n"
    assert ee.split_frontmatter(text) == text
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'export_examples'`. The existing `site/scripts/tests/conftest.py` already puts `site/scripts/` on the path, so no conftest change is needed.

- [ ] **Step 3: Write the module**

Create `site/scripts/export_examples.py`:

```python
#!/usr/bin/env python3
"""Publish the worked example artifact sets to the documentation site.

Reads ``docs/requirements/examples/`` and writes one Markdown page per
artifact type per set into ``site/content/guide/examples/``.

Consolidated by type rather than one page per artifact: the two sets hold 108
atomic artifacts between them, and 108 sidebar entries is a listing rather
than navigation. Each artifact keeps a stable anchor, so a link to a single
requirement still resolves.

Output is ``.md``, not ``.mdx``. Nextra compiles ``.md`` in markdown mode,
where ``<`` and ``{`` are literal text — so an artifact body cannot break the
site build by containing them. No example body currently does, and nothing
guarantees that stays true: these sets are regenerated deliberately.

Stdlib only, like every other script in this repository. The outputs are
committed and the site build does not run this script; CI re-runs it and
fails on any diff.

Usage
-----
    python3 site/scripts/export_examples.py
    python3 site/scripts/export_examples.py --check
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "docs", "requirements", "examples")
OUT_DIR = os.path.join(
    REPO_ROOT, "site", "content", "guide", "examples"
)

# Frontmatter is parsed with the validators' own parser, so this script sees
# exactly what the gates see. artifact_core lives in lib/ and is imported
# directly here rather than through a validator, so lib/ goes on the path
# explicitly — the validators bootstrap it for themselves, which does not
# help a module that never imports one.
for _dir in (
    os.path.join(REPO_ROOT, "lib"),
    os.path.join(REPO_ROOT, "skills", "design", "scripts"),
    os.path.join(REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import artifact_core  # noqa: E402

# (stage, directory, page title). Order is page order in the sidebar.
GROUPS: List[Tuple[str, str, str]] = [
    ("requirements", "functional", "Functional requirements"),
    ("requirements", "non-functional", "Non-functional requirements"),
    ("requirements", "constraints", "Constraints"),
    ("requirements", "business-rules", "Business rules"),
    ("design", "components", "Components"),
    ("design", "interfaces", "Interfaces"),
    ("design", "adr", "Architecture decision records"),
    ("design", "diagrams", "C4 diagrams"),
]

# Project-level artifacts: prose files with no artifact ID, published together
# on one page per stage. Order is reading order, not alphabetical.
PROJECT_FILES: Dict[str, List[str]] = {
    "requirements": ["glossary.md", "assumptions.md", "definition-of-done.md"],
    "design": ["drivers.md", "assumptions.md"],
}

# Excluded on purpose. The critique report and dev log are pipeline internals;
# CONSOLIDATED.md is the hand-assembled artifact STO-264 exists to replace,
# and republishing it here would give a known-stale document a second and more
# authoritative home; the READMEs address a reader of the repository.
EXCLUDED = {
    "CONSOLIDATED.md",
    "README.md",
    "REGENERATION.md",
    "dev-log-followup.md",
}

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n\s*", re.DOTALL)
_TITLE_RE = re.compile(r"^#\s+(?:[A-Z]+-\d+\s+—\s+)?(.+)$", re.MULTILINE)


@dataclass
class Artifact:
    artifact_id: str
    title: str
    source: str
    meta: Dict[str, Any]
    body: str


def split_frontmatter(text: str) -> str:
    """Return the body after a leading frontmatter block, or the text as-is."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def discover_sets() -> List[str]:
    """Every example set: a directory holding a ``requirements/`` subtree."""
    return sorted(
        name
        for name in os.listdir(EXAMPLES_DIR)
        if os.path.isdir(os.path.join(EXAMPLES_DIR, name, "requirements"))
    )


def _sort_key(artifact_id: str) -> Tuple[str, int]:
    """Sort IDs by prefix then numeric suffix, so FR-2 precedes FR-10."""
    prefix, _, number = artifact_id.rpartition("-")
    try:
        return (prefix, int(number))
    except ValueError:
        return (artifact_id, 0)


def load_group(set_name: str, stage: str, directory: str) -> List[Artifact]:
    """Load one artifact type's files, ID-sorted.

    A directory that does not exist yields an empty list. That is a legal
    shape, not an error: gdpr carries no design stage, and an absent ``adr/``
    or ``diagrams/`` means nothing qualified rather than something failed.
    """
    root = os.path.join(EXAMPLES_DIR, set_name, stage, directory)
    if not os.path.isdir(root):
        return []

    artifacts: List[Artifact] = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".md") or name in EXCLUDED:
            continue
        path = os.path.join(root, name)
        meta, error = artifact_core.parse_frontmatter(path)
        if error is not None or not isinstance(meta, dict):
            raise ValueError(f"{path}: {error or 'frontmatter is not a mapping'}")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        artifacts.append(
            Artifact(
                artifact_id=str(meta["id"]),
                title=str(meta.get("title", "")),
                source=os.path.relpath(path, REPO_ROOT),
                meta=meta,
                body=split_frontmatter(text),
            )
        )

    artifacts.sort(key=lambda a: _sort_key(a.artifact_id))
    return artifacts
```

- [ ] **Step 4: Run the tests**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -q`
Expected: PASS, all eight.

If `test_group_counts_match_the_committed_sets` fails, the committed sets have changed since this plan was written — update the expected counts to what is on disk and say so in the commit body. Do not loosen the assertion; the point of hard-coded counts is that a silently truncated walk fails here.

- [ ] **Step 5: Commit**

```bash
git add site/scripts/export_examples.py site/scripts/tests/test_export_examples.py
git commit -m "feat(sto-250): read the worked example sets, parsed by the validators' own parser"
```

---

### Task 8: `export_examples.py` — rendering and cross-links

**Files:**
- Modify: `site/scripts/export_examples.py`
- Test: `site/scripts/tests/test_export_examples.py`

**Interfaces:**
- Consumes: Task 7's `Artifact`, `load_group`, `GROUPS`.
- Produces, for Task 9:
  - `demote_headings(body: str) -> str`
  - `render_group(set_name, stage, directory, title, artifacts, index) -> str`
  - `build_index(set_name) -> Dict[str, str]` — artifact ID to its page URL with anchor.

- [ ] **Step 1: Write the failing tests**

Append to `site/scripts/tests/test_export_examples.py`:

```python
def test_demote_headings_shifts_every_level_by_one():
    body = "# Title\n\n## Section\n\n### Sub\n"
    assert ee.demote_headings(body) == "## Title\n\n### Section\n\n#### Sub\n"


def test_demote_headings_ignores_hashes_inside_fenced_blocks():
    # Gherkin and Mermaid blocks contain lines that start with '#'. Demoting
    # them would corrupt the fenced content, and a naive regex would.
    body = "# Title\n\n```gherkin\n# not a heading\n```\n\n## After\n"
    out = ee.demote_headings(body)
    assert "# not a heading" in out
    assert "## not a heading" not in out
    assert out.startswith("## Title")
    assert "### After" in out


def test_demote_headings_handles_an_unbalanced_fence():
    # An unterminated fence must not silently re-enable demotion below it.
    body = "# Title\n\n```\n# inside\n"
    out = ee.demote_headings(body)
    assert "# inside" in out
    assert "## inside" not in out


def test_index_maps_ids_to_anchored_urls():
    index = ee.build_index("tamagotchi")
    assert index["FR-001"] == (
        "/guide/examples/tamagotchi/requirements/functional/#fr-001"
    )
    assert index["CMP-001"] == (
        "/guide/examples/tamagotchi/design/components/#cmp-001"
    )


def test_rendered_page_anchors_every_artifact():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    index = ee.build_index("tamagotchi")
    page = ee.render_group(
        "tamagotchi", "requirements", "functional",
        "Functional requirements", artifacts, index,
    )
    assert "## FR-001 — Persist pet state on stat change and app close [#fr-001]" in page
    for artifact in artifacts:
        assert f"[#{artifact.artifact_id.lower()}]" in page


def test_rendered_page_links_resolvable_traces_and_leaves_the_rest_as_text():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    index = ee.build_index("tamagotchi")
    page = ee.render_group(
        "tamagotchi", "requirements", "functional",
        "Functional requirements", artifacts, index,
    )
    # FR-001 traces_from: [CON-002, BR-002] — both exist in this set.
    assert "[CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002)" in page
    # An ID absent from the set must render as plain text, never a dead link.
    assert "](/guide/examples/tamagotchi/requirements/functional/#fr-999)" not in page


def test_rendered_page_is_byte_identical_across_runs():
    args = ("tamagotchi", "design", "components", "Components")
    index = ee.build_index("tamagotchi")
    first = ee.render_group(*args, ee.load_group(*args[:3]), index)
    second = ee.render_group(*args, ee.load_group(*args[:3]), index)
    assert first == second
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -q -k "demote or index or rendered"`
Expected: FAIL — `AttributeError: module 'export_examples' has no attribute 'demote_headings'`.

- [ ] **Step 3: Implement the fence-aware heading demoter**

Append to `site/scripts/export_examples.py`:

```python
_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^(#{1,5})(\s+)(.*)$")


def demote_headings(body: str) -> str:
    """Shift every heading down one level, outside fenced code blocks.

    An artifact body opens with ``# FR-001 — Title``; on a consolidated page
    that has to become an H2 under the page's own H1.

    A state machine rather than a regex over the whole document. Artifact
    bodies carry Gherkin and Mermaid fences whose lines can begin with ``#``,
    and a fence is closed only by a fence of at least the same length using
    the same character — the rule CommonMark actually specifies. An
    unterminated fence runs to the end of the file rather than silently
    re-enabling demotion, which is the residual STO-263 C1 records against
    the exporter's regex approach.
    """
    out: List[str] = []
    fence: Optional[Tuple[str, int]] = None

    for line in body.split("\n"):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            char = fence_match.group(2)[0]
            length = len(fence_match.group(2))
            info = fence_match.group(3).strip()
            if fence is None:
                # An opening fence may carry an info string; a closing one
                # may not.
                fence = (char, length)
            elif char == fence[0] and length >= fence[1] and not info:
                fence = None
            out.append(line)
            continue

        if fence is None:
            heading = _HEADING_RE.match(line)
            if heading:
                out.append(
                    "#" + heading.group(1) + heading.group(2) + heading.group(3)
                )
                continue

        out.append(line)

    return "\n".join(out)
```

- [ ] **Step 4: Implement the index and the renderer**

Append:

```python
def page_url(set_name: str, stage: str, directory: str) -> str:
    """Site-relative page URL, trailing slash, no basePath.

    The form ``site/content/index.mdx`` already uses and pass 1 confirmed
    resolves on the deployed project page.
    """
    return f"/guide/examples/{set_name}/{stage}/{directory}/"


def build_index(set_name: str) -> Dict[str, str]:
    """Map every artifact ID in a set to its anchored URL."""
    index: Dict[str, str] = {}
    for stage, directory, _title in GROUPS:
        url = page_url(set_name, stage, directory)
        for artifact in load_group(set_name, stage, directory):
            index[artifact.artifact_id] = f"{url}#{artifact.artifact_id.lower()}"
    return index


def _link_ids(ids: List[Any], index: Dict[str, str]) -> str:
    """Render an ID list as links, leaving unresolvable IDs as plain text.

    A generated page must not publish a dead cross-reference — least of all
    on pages about traceability.
    """
    if not ids:
        return "—"
    parts: List[str] = []
    for raw in ids:
        value = str(raw)
        target = index.get(value)
        parts.append(f"[{value}]({target})" if target else value)
    return ", ".join(parts)


# Frontmatter keys worth surfacing per artifact, in display order. Anything
# not listed stays in the source file; this is a reading view, not a dump.
META_ROWS = [
    ("type", "Type"),
    ("tier", "Tier"),
    ("priority", "Priority"),
    ("status", "Status"),
    ("confidence", "Confidence"),
    ("ears_pattern", "EARS pattern"),
    ("verification_method", "Verification"),
    ("boundary", "Boundary"),
    ("responsibility", "Responsibility"),
    ("provider", "Provider"),
    ("interaction", "Interaction"),
    ("level", "C4 level"),
]

LINK_ROWS = [
    ("traces_from", "Traces from"),
    ("depends_on", "Depends on"),
]


def _meta_table(artifact: Artifact, index: Dict[str, str]) -> str:
    rows: List[str] = []
    for key, label in META_ROWS:
        value = artifact.meta.get(key)
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        rows.append(f"| {label} | {value} |")
    for key, label in LINK_ROWS:
        value = artifact.meta.get(key)
        if not value:
            continue
        rows.append(f"| {label} | {_link_ids(list(value), index)} |")

    if not rows:
        return ""
    header = "| Field | Value |\n| --- | --- |"
    return header + "\n" + "\n".join(rows) + "\n"


def render_group(
    set_name: str,
    stage: str,
    directory: str,
    title: str,
    artifacts: List[Artifact],
    index: Dict[str, str],
) -> str:
    """Render one artifact type as a single consolidated page."""
    lines = [
        "<!--",
        "  GENERATED FILE — do not edit.",
        "  Source: docs/requirements/examples/"
        f"{set_name}/{stage}/{directory}/",
        "  Regenerate: python3 site/scripts/export_examples.py",
        "-->",
        "",
        f"# {title}",
        "",
        f"The {len(artifacts)} {title.lower()} from the "
        f"`{set_name}` worked example, exactly as the pipeline wrote them.",
        "",
    ]

    for artifact in artifacts:
        anchor = artifact.artifact_id.lower()
        heading = f"{artifact.artifact_id} — {artifact.title}".rstrip(" —")
        lines.append(f"## {heading} [#{anchor}]")
        lines.append("")
        table = _meta_table(artifact, index)
        if table:
            lines.append(table)
        body = demote_headings(artifact.body).strip()
        # The artifact's own H1 became an H2 identical to the heading above.
        body = re.sub(r"\A##\s+.*\n+", "", body)
        lines.append(body)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"
```

- [ ] **Step 5: Run the tests**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -q`
Expected: PASS, all fifteen.

- [ ] **Step 6: Eyeball one rendered page before trusting the suite**

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, 'site/scripts')
import export_examples as ee
idx = ee.build_index('tamagotchi')
arts = ee.load_group('tamagotchi', 'requirements', 'functional')
print(ee.render_group('tamagotchi', 'requirements', 'functional',
                      'Functional requirements', arts, idx)[:2500])
PY
```

Check by eye: the H1 is the page title; each artifact is an H2 with a `[#fr-00n]` anchor; the metadata table renders; the Gherkin fences are intact; `CON-002` is a link.

- [ ] **Step 7: Commit**

```bash
git add site/scripts/export_examples.py site/scripts/tests/test_export_examples.py
git commit -m "feat(sto-250): render example sets as consolidated pages with anchored artifacts

The heading demoter is a fence state machine rather than a regex: artifact
bodies carry Gherkin and Mermaid fences whose lines begin with '#', and an
unterminated fence must not re-enable demotion below it."
```

---

### Task 9: `export_examples.py` — write, gate, and wire into the nav

**Files:**
- Modify: `site/scripts/export_examples.py`
- Modify: `site/scripts/tests/test_export_examples.py`
- Create: `site/content/guide/examples/**` (generated — 15 pages, one index, four `_meta.js`)
- Modify: `site/content/guide/_meta.js`
- Modify: `site/package.json` (an `examples` script beside `reference`)
- Modify: `.github/workflows/ci.yml`, `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: Task 8's `render_group`, `build_index`.
- Produces: `main(argv) -> int`, matching `export_reference.py`'s CLI exactly — bare invocation writes, `--check` exits 1 on drift and writes nothing.

- [ ] **Step 1: Write the failing tests**

Append to `site/scripts/tests/test_export_examples.py`:

```python
def test_check_passes_against_committed_output():
    # The gate's real contract: what is on disk equals what the exporter
    # produces right now.
    assert ee.main(["--check"]) == 0


def test_check_fails_when_a_page_is_stale(capsys):
    target = os.path.join(ee.OUT_DIR, "tamagotchi", "requirements", "functional.md")
    original = open(target, encoding="utf-8").read()
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original + "\nstale\n")
        assert ee.main(["--check"]) == 1
        assert "stale:" in capsys.readouterr().err
    finally:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original)
    assert ee.main(["--check"]) == 0


def test_project_artifact_pages_carry_the_prose_files():
    page = ee.render_project_artifacts("tamagotchi", "requirements")
    assert "## Glossary" in page
    assert "## Assumptions" in page
    assert "## Definition of done" in page


def test_gdpr_has_no_design_pages():
    assert not os.path.isdir(os.path.join(ee.OUT_DIR, "gdpr", "design"))
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -q -k "check or project or gdpr"`
Expected: FAIL — `AttributeError` on `main` / `render_project_artifacts` / `OUT_DIR` contents.

- [ ] **Step 3: Implement project-artifact rendering, the writer, and the CLI**

Append to `site/scripts/export_examples.py`:

```python
# Sidebar labels for the sets. A set with no entry here uses its directory
# name, so adding a set does not require touching this map.
SET_TITLES = {
    "tamagotchi": "Desktop tamagotchi",
    "gdpr": "GDPR compliance",
}

PROJECT_TITLES = {
    "glossary.md": "Glossary",
    "assumptions.md": "Assumptions",
    "definition-of-done.md": "Definition of done",
    "drivers.md": "Architecture drivers",
}


def render_project_artifacts(set_name: str, stage: str) -> str:
    """Render one stage's project-level prose files as a single page.

    These carry no artifact ID and no frontmatter — they are the stage's
    shared context, not atomic artifacts, and the structural validators skip
    them for the same reason.
    """
    root = os.path.join(EXAMPLES_DIR, set_name, stage)
    sections: List[str] = []
    for name in PROJECT_FILES[stage]:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        body = demote_headings(split_frontmatter(text)).strip()
        body = re.sub(r"\A##\s+.*\n+", "", body)
        anchor = os.path.splitext(name)[0]
        sections.append(
            f"## {PROJECT_TITLES[name]} [#{anchor}]\n\n{body}\n"
        )

    if not sections:
        return ""

    header = [
        "<!--",
        "  GENERATED FILE — do not edit.",
        f"  Source: docs/requirements/examples/{set_name}/{stage}/",
        "  Regenerate: python3 site/scripts/export_examples.py",
        "-->",
        "",
        "# Project artifacts",
        "",
        "The stage-level files that sit alongside the atomic artifacts: the "
        "vocabulary they are written in, what was assumed, and what is still "
        "open.",
        "",
    ]
    return "\n".join(header) + "\n".join(sections).rstrip("\n") + "\n"


def _meta_js(entries: List[Tuple[str, str]]) -> str:
    lines = ["export default {"]
    lines += [f"  '{key}': '{label}'," for key, label in entries]
    lines.append("}")
    return "\n".join(lines).replace(",\n}", "\n}") + "\n"


def build_pages() -> Dict[str, str]:
    """Every file this exporter owns: relative path to content."""
    pages: Dict[str, str] = {}
    set_entries: List[Tuple[str, str]] = []

    for set_name in discover_sets():
        index = build_index(set_name)
        stages_present: List[str] = []

        for stage in ("requirements", "design"):
            group_entries: List[Tuple[str, str]] = []
            for group_stage, directory, title in GROUPS:
                if group_stage != stage:
                    continue
                artifacts = load_group(set_name, stage, directory)
                if not artifacts:
                    continue
                pages[f"{set_name}/{stage}/{directory}.md"] = render_group(
                    set_name, stage, directory, title, artifacts, index
                )
                group_entries.append((directory, title))

            project = render_project_artifacts(set_name, stage)
            if project:
                pages[f"{set_name}/{stage}/project-artifacts.md"] = project
                group_entries.append(("project-artifacts", "Project artifacts"))

            if group_entries:
                pages[f"{set_name}/{stage}/_meta.js"] = _meta_js(group_entries)
                stages_present.append(stage)

        if stages_present:
            pages[f"{set_name}/_meta.js"] = _meta_js(
                [
                    (s, "Requirements" if s == "requirements" else "Design")
                    for s in stages_present
                ]
            )
            set_entries.append((set_name, SET_TITLES.get(set_name, set_name)))

    pages["_meta.js"] = _meta_js(set_entries)
    return pages


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish the worked example sets to the docs site."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any committed page is stale, writing nothing",
    )
    args = parser.parse_args(argv)

    pages = build_pages()
    stale: List[str] = []

    for relative, content in sorted(pages.items()):
        path = os.path.join(OUT_DIR, relative)
        if args.check:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    if handle.read() != content:
                        stale.append(relative)
            except (OSError, UnicodeDecodeError):
                stale.append(relative)
        else:
            _write(path, content)

    if args.check:
        # A page on disk that the exporter no longer produces is drift too.
        for root, _dirs, names in os.walk(OUT_DIR):
            for name in names:
                relative = os.path.relpath(
                    os.path.join(root, name), OUT_DIR
                ).replace(os.sep, "/")
                if relative not in pages:
                    stale.append(f"{relative} (orphaned)")

    if args.check and stale:
        for relative in sorted(stale):
            print(f"stale: site/content/guide/examples/{relative}", file=sys.stderr)
        print("run: python3 site/scripts/export_examples.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Add the missing import at the top of the file if it is not already there: `import argparse`.

- [ ] **Step 4: Generate the pages and run the tests**

```bash
python3 site/scripts/export_examples.py
find site/content/guide/examples -type f | sort
python3 -m pytest site/scripts/tests/test_export_examples.py -q
python3 site/scripts/export_examples.py --check
```

Expected: 15 `.md` pages, four `_meta.js` files, `--check` exits 0, tests pass.

- [ ] **Step 5: Add the examples section to the guide nav**

Replace `site/content/guide/_meta.js` with:

```js
export default {
  installation: 'Installation',
  examples: 'Worked examples',
  reference: 'Reference'
}
```

The stage and gate pages get inserted into this file by Tasks 10–12; keep the ordering `installation` first and `reference` last.

- [ ] **Step 6: Build and confirm the pages render**

```bash
cd site && npm run build
grep -q 'id="fr-001"' out/guide/examples/tamagotchi/requirements/functional/index.html && echo "anchor OK"
grep -q 'href="/guide/examples/tamagotchi/requirements/constraints/#con-002"' \
  out/guide/examples/tamagotchi/requirements/functional/index.html && echo "link OK"
grep -qi 'mermaid' out/guide/examples/tamagotchi/design/diagrams/index.html && echo "mermaid OK"
```

Expected: all three print OK. If the cross-link assertion fails, check whether Nextra rewrote the href — inspect the actual `href` in the built HTML and adjust `page_url` to match, rather than weakening the test.

- [ ] **Step 7: Wire the second gate into both workflows**

In `.github/workflows/ci.yml`, after the existing drift step in the `tests` job:

```yaml
      - name: Generated examples are not stale
        run: python3 site/scripts/export_examples.py --check
```

In `.github/workflows/pages.yml`, after the existing drift step in the `build` job, add the same step.

In `ci.yml`'s `build` job, extend the assertion step from Task 1:

```yaml
      - name: Built pages carry their generated rows
        run: |
          grep -q 'god-component' out/guide/reference/rules/index.html
          grep -q 'id="fr-001"' out/guide/examples/tamagotchi/requirements/functional/index.html
        working-directory: site
```

In `site/package.json`, add beside the existing `reference` script:

```json
    "examples": "python3 scripts/export_examples.py",
```

- [ ] **Step 8: Verify the gate is load-bearing**

```bash
echo "" >> site/content/guide/examples/tamagotchi/requirements/functional.md
python3 site/scripts/export_examples.py --check; echo "check exit: $?"
python3 site/scripts/export_examples.py
python3 site/scripts/export_examples.py --check; echo "check exit: $?"
```

Expected: `check exit: 1` then `check exit: 0`.

- [ ] **Step 9: Commit**

```bash
git add site/scripts/export_examples.py site/scripts/tests/test_export_examples.py \
        site/content/guide/examples site/content/guide/_meta.js \
        site/package.json .github/workflows/ci.yml .github/workflows/pages.yml
git commit -m "feat(sto-250): publish the worked example sets as 15 generated pages

Consolidated by artifact type: 108 sidebar entries is a listing, not
navigation. Every artifact keeps a stable anchor, so a link to one
requirement still resolves.

--check also reports orphans, so deleting an example set fails the gate
rather than leaving a page nothing produces."
```

---

### Task 10: The requirements stage page and the artifact anatomy page

Prose tasks. There is no test to write first; the discipline instead is that **every factual claim is sourced from a named file, and the claim list below is the acceptance criterion**. Do not assert anything about the pipeline that is not in one of the cited sources.

**Files:**
- Create: `site/content/guide/requirements-stage.mdx`
- Create: `site/content/guide/reading-an-artifact.mdx`
- Modify: `site/content/guide/_meta.js`

**Sources — read all of these before writing:**
- `skills/requirements/SKILL.md` (phases 1–6)
- `skills/requirements/scripts/README.md`
- `docs/requirements/examples/tamagotchi/requirements/functional/FR-001-*.md`
- `site/content/_generated/fields.json`

- [ ] **Step 1: Write `requirements-stage.mdx`**

Structure and required claims:

1. **What triggers it** — the skill is trigger-matched on a description of something to build, not invoked by name; `/groundwork` lists it. It explicitly does not trigger on questions, bug reports with clear repro, or requests to explain existing code (`SKILL.md` "When This Applies").
2. **What it will not do** — no code is written at any point during the stage.
3. **The interview** — hypothesis-led: 3–5 domain hypotheses first, then one question per exchange, numbered options where the answer space is enumerable. Render the six areas with `<CoverageAreas stage="requirements" />`. Mention the commonly-omitted-category sweep as a gap check that may surface nothing.
4. **The two sign-off gates** — the Phase 4.5 context block confirmed before generation, and the summary confirmed before any file is written. Say plainly that nothing is written to disk until the second confirmation.
5. **What the interview produces before generation** — quote the tamagotchi set's `clarification-context.yaml` as a short fenced block, so a reader can see what the Phase 4.5 block actually serialises to. Per spec D4 this file is not published as an example page; the stage page is where it belongs, because this is where the interview is being explained. Copy it from `docs/requirements/examples/tamagotchi/clarification-context.yaml` rather than paraphrasing, and trim to the keys rather than inventing values.
6. **What lands on disk** — the `.sdlc/requirements/` tree: `functional/`, `non-functional/`, `constraints/`, `business-rules/`, `use-cases/`, plus `assumptions.md`, `glossary.md`, `definition-of-done.md`, `index.yaml`. State that `index.yaml` carries a `review_queue` of every `confidence: low` requirement.
7. **What to do next** — link to [Reading an artifact](/guide/reading-an-artifact/), [Gates](/guide/gates/), and the worked examples.

Use `import { CoverageAreas } from '../../components/CoverageAreas'` at the top. Quote any `<feature-name>`-shaped string from `SKILL.md` inside a fenced code block.

- [ ] **Step 2: Write `reading-an-artifact.mdx`**

Structure and required claims:

1. **One artifact, one file** — the filename is `<ID>-<kebab-title>.md`; the ID is categorical and zero-padded; IDs are never reused, and an artifact that stops applying gets `status: obsolete` rather than being deleted (`fields.json`, the `status` field description).
2. **A real example** — show `FR-001` from the tamagotchi set as a fenced block, and link to its published page. Copy it from the file rather than retyping it.
3. **The frontmatter** — render `<FieldTable stage="requirements" />`, then explain in prose only the fields that need judgement: `rationale` and `fit_criterion` (why every requirement carries both), `ears_pattern` (functional only), `traces_from` / `traces_to`, `confidence`, `priority`.
4. **`confidence: low` and the review queue** — a low-confidence artifact is not a defect; it is the pipeline saying which items to check first. The same list is persisted in `index.yaml` as `review_queue`.
5. **The body** — Description, Rationale, Acceptance Criteria in Gherkin, Fit Criterion. Say that acceptance criteria are Gherkin because they are meant to become tests.
6. **Design artifacts differ** — `<FieldTable stage="design" />` and a one-paragraph note on `responsibility`, `boundary`, `depends_on`, `provider`.

- [ ] **Step 3: Add both to the nav**

Replace `site/content/guide/_meta.js` with:

```js
export default {
  installation: 'Installation',
  'requirements-stage': 'The requirements stage',
  'reading-an-artifact': 'Reading an artifact',
  examples: 'Worked examples',
  reference: 'Reference'
}
```

- [ ] **Step 4: Verify every claim against its source**

Re-read the two pages beside `skills/requirements/SKILL.md` and `fields.json`. For each factual sentence, point at the line that supports it. Delete or correct any sentence you cannot source. Pass 1 shipped two false claims caught only in review — both were about what the pipeline emits.

Specifically check: does the page claim EARS applies to all requirement types? It must not — EARS is functional-only.

- [ ] **Step 5: Build**

```bash
cd site && npm run build
grep -q 'Core functionality' out/guide/requirements-stage/index.html && echo "areas OK"
grep -q 'ears_pattern' out/guide/reading-an-artifact/index.html && echo "fields OK"
```

- [ ] **Step 6: Commit**

```bash
git add site/content/guide/requirements-stage.mdx site/content/guide/reading-an-artifact.mdx \
        site/content/guide/_meta.js
git commit -m "docs(sto-250): the requirements stage, and how to read an artifact"
```

---

### Task 11: The design stage page

**Files:**
- Create: `site/content/guide/design-stage.mdx`
- Modify: `site/content/guide/_meta.js`

**Sources:**
- `skills/design/SKILL.md` — all of it, especially Phase 3, the `## ADRs` section, and `## What This Stage Does Not Produce`
- `docs/requirements/examples/tamagotchi/design/`

- [ ] **Step 1: Write the page**

Structure and required claims:

1. **It needs a validated requirement set** — the stage reads `.sdlc/requirements/` as its input.
2. **Why it runs its own interview** — this is the page's most important paragraph. The requirement set *cannot* carry technology context by construction: the content linter treats implementation bias as a defect and the critic flags it, so nothing in `.sdlc/requirements/` says "Tauri" or "Postgres" and nothing should. The stage therefore either asks or invents, and the project's own history settled it — an earlier build took an unexamined Electron recommendation and paid to rip it out. Source: `skills/design/SKILL.md` Phase 3, "Why this interview exists."
3. **Inherited open questions come first** — many `Q-` items in `assumptions.md` are architecture decisions by nature. Use the tamagotchi `Q-4` example (framework choice given the footprint constraint, with `NFR-002` and `CON-001` both resting on it).
4. **The six areas** — `<CoverageAreas stage="design" />`. Follow it with the tamagotchi set's `design-context.yaml`, quoted as a fenced block, so a reader sees what the interview's answers become. Per spec D4 this file is not published as an example page; here is where it earns its place. Copy it from `docs/requirements/examples/tamagotchi/design-context.yaml`; trim it if it is long, but do not invent values.
5. **What lands on disk** — `.sdlc/design/` with `components/`, `interfaces/`, `adr/`, `diagrams/`, plus `assumptions.md`, `drivers.md`, `index.yaml`.
6. **An empty `adr/` or `diagrams/` is legal** — ADRs are derived, never elicited: the generator promotes decisions the pipeline already recorded and never invents a rejected option to fill a template. A decision whose alternatives cannot be recovered stays in `drivers.md` and is reported as skipped. Say explicitly that an absent `adr/` means nothing qualified, not that something failed. This is troubleshooting content the ticket names, and it belongs here as well as on the troubleshooting page — say it once here, link from there.
7. **Diagrams are projected, not authored** — `generate_c4.py` projects the component graph into Context, Container and Component views; the `c4-generator` agent supplies only container grouping and actors. Link to the tamagotchi diagrams page.
8. **Next** — link to [Gates](/guide/gates/).

- [ ] **Step 2: Add to nav**

```js
export default {
  installation: 'Installation',
  'requirements-stage': 'The requirements stage',
  'reading-an-artifact': 'Reading an artifact',
  'design-stage': 'The design stage',
  examples: 'Worked examples',
  reference: 'Reference'
}
```

- [ ] **Step 3: Verify claims against `skills/design/SKILL.md`**

Check in particular that the page does not claim the design skill decides diagram content, traceability resolution, or cycle detection — `## What This Stage Does Not Produce` is explicit that all three belong to scripts, not to the skill's judgement.

- [ ] **Step 4: Build and commit**

```bash
cd site && npm run build && grep -q 'Runtime and stack' out/guide/design-stage/index.html && echo OK
cd .. && git add site/content/guide/design-stage.mdx site/content/guide/_meta.js
git commit -m "docs(sto-250): the design stage, and why it runs its own interview"
```

---

### Task 12: The gates page and the troubleshooting page

**Files:**
- Create: `site/content/guide/gates.mdx`
- Create: `site/content/guide/troubleshooting.mdx`
- Modify: `site/content/guide/_meta.js`

**Sources:**
- `skills/requirements/scripts/README.md`
- `skills/design/scripts/README.md` (all of it — it carries the exit codes, the `--strict`/`--json`/`--quiet` semantics, and the hand-edit paragraph)
- `validate_traceability.RULES` from Task 2

- [ ] **Step 1: Write `gates.mdx`**

Required structure and claims:

1. **Two kinds of check.** Three structural validators that can stop a stage, and two advisory content linters that never do. Make the distinction before anything else — it is the thing a user most needs to know when something exits non-zero.
2. **The three gates**, one short section each:
   - `validate_requirements.py` — per-file schema, ID pattern, `created_at` format, `ears_pattern` required for functional; cross-file unique IDs, prefix/type agreement, `traces_from` resolution. Hard-gates `assumptions.md`'s three headings and `glossary.md`'s `## Terms`; content is never gated, and `None identified` is legal.
   - `validate_design.py` — schema, ID/type agreement, the `CMP.depends_on → IF.provider` graph, project artifacts, MADR headings.
   - `validate_traceability.py` — the requirement↔design edge neither stage validator resolves. Render `<RuleTable linter="traceability" />` here, introduced as rules that **fail the stage**, unlike the advisory tables on [Content rules](/guide/reference/rules/).
3. **Exit codes, stated once and shared:** `0` clean, `1` violations, `2` an *environment* error — a missing directory or schema — which is not a validation failure and is routed separately by the agent contracts.
4. **The two failures a human fixes by hand.** `dangling-reverse-trace` and `misplaced-requirement-trace` are fixed by editing the requirement file in the requirements stage. There is no migration script and no bypass flag, on purpose: a tool that rewrote requirement files from the design stage would be the second writer the pipeline exists to avoid. Everything else is re-dispatched to the owning specialist through the critique loop rather than hand-edited.
5. **The advisory linters** — always exit 0 unless `--strict`; no design rule currently emits `error`, so `--strict` is a no-op there today. Link to [Content rules](/guide/reference/rules/).

Import `RuleTable` with `import { RuleTable } from '../../components/RuleTable'`.

- [ ] **Step 2: Write `troubleshooting.mdx`**

One section per problem, each stating the symptom first:

1. **`pyyaml` / `jsonschema` are missing.** The validators degrade to a stdlib-only fallback doing required-field, enum and cross-file checks with no full JSON Schema validation, and print an install hint. All three tools print a `reduced (stdlib fallback) mode` warning. Fix: `pip install pyyaml jsonschema`. Note that `validate_traceability.py` does no schema validation but should still have `pyyaml`, because reading list fields out of frontmatter is its entire job and the fallback parser is deliberately limited.
2. **Exit code 2.** An environment error — a missing directory or an unreadable schema — not a validation failure. Nothing is wrong with the artifacts. Check the path you passed.
3. **A `README.md` in a `.sdlc/` stage directory fails the validator.** Known, tracked as STO-218. The validator treats every `.md` file in a stage directory as an atomic artifact except the named project-level companions. Workaround: keep notes outside the stage directory.
4. **`adr/` or `diagrams/` is empty or absent.** Legal. ADRs are derived from decisions the pipeline already recorded; nothing qualifying means no file. Link to the design stage page.
5. **The validator failed after the formatter wrote files.** Do not hand-edit the written artifacts. Re-dispatch the flagged items to the owning specialist through the critique loop — except the two hand-edit cases named on the gates page.

- [ ] **Step 3: Add both to nav**

```js
export default {
  installation: 'Installation',
  'requirements-stage': 'The requirements stage',
  'reading-an-artifact': 'Reading an artifact',
  'design-stage': 'The design stage',
  gates: 'Gates and validators',
  troubleshooting: 'Troubleshooting',
  examples: 'Worked examples',
  reference: 'Reference'
}
```

- [ ] **Step 4: Build and verify the traceability table rendered without a Fields column**

```bash
cd site && npm run build
grep -q 'dangling-reverse-trace' out/guide/gates/index.html && echo "rules OK"
python3 - <<'PY'
import re, pathlib
html = pathlib.Path('out/guide/gates/index.html').read_text()
table = html[html.index('dangling-trace') - 2000:]
print('Fields column present:', 'Fields' in table[:1500])
PY
```

Expected: `rules OK`, and `Fields column present: False`.

- [ ] **Step 5: Commit**

```bash
git add site/content/guide/gates.mdx site/content/guide/troubleshooting.mdx site/content/guide/_meta.js
git commit -m "docs(sto-250): the gates, and what to do when one of them fails"
```

---

### Task 13: Landing page, full verification, and the deploy

**Files:**
- Modify: `site/content/index.mdx`
- Modify: `README.md` (only if a claim it makes is now contradicted by the guide)

- [ ] **Step 1: Rewrite the landing page's "Where to go"**

Replace the existing list in `site/content/index.mdx` with one that reflects the real guide:

```mdx
## Where to go

- **[Installation](/guide/installation/)** — add the plugin and run your first
  stage.
- **[The requirements stage](/guide/requirements-stage/)** — what the
  interview asks, and what lands in `.sdlc/requirements/`.
- **[Reading an artifact](/guide/reading-an-artifact/)** — frontmatter, trace
  edges, and what `confidence: low` is telling you.
- **[The design stage](/guide/design-stage/)** — the architecture interview,
  and the six things the requirement set cannot carry.
- **[Gates and validators](/guide/gates/)** — what each checker owns, and what
  to do when one exits non-zero.
- **[Worked examples](/guide/examples/tamagotchi/requirements/functional/)** —
  two complete artifact sets, exactly as the pipeline wrote them.
- **[Architecture](/architecture/)** — how the pipeline works, and why.
```

- [ ] **Step 2: Full local verification**

```bash
python3 -m pytest -q
python3 site/scripts/export_reference.py --check
python3 site/scripts/export_examples.py --check
cd site && rm -rf .next out && npm run build
```

Expected: all tests pass; both gates exit 0; the build exits 0.

- [ ] **Step 3: Check every internal link resolves**

```bash
cd site
python3 - <<'PY'
import os, re
roots = {}
for base, _dirs, names in os.walk('out'):
    if 'index.html' in names:
        roots['/' + os.path.relpath(base, 'out').replace(os.sep, '/') + '/'] = True
roots['//'] = True
missing = set()
for base, _dirs, names in os.walk('out'):
    for name in names:
        if not name.endswith('.html'):
            continue
        html = open(os.path.join(base, name), encoding='utf-8').read()
        for href in re.findall(r'href="(/[^"#]*)(?:#[^"]*)?"', html):
            if href.startswith('/_next') or href.startswith('/groundwork/_next'):
                continue
            probe = href if href.endswith('/') else href + '/'
            probe = probe.replace('/groundwork/', '/', 1)
            if probe not in roots:
                missing.add(probe)
print('unresolved internal links:', sorted(missing) or 'none')
PY
```

Expected: `none`. Any hit is a real broken link — fix the source page, do not weaken the check.

- [ ] **Step 4: Verify search finds an artifact**

Pagefind indexes the built output. Confirm an artifact ID is in the index:

```bash
cd site && grep -rl 'FR-001' out/_pagefind/ | head -3
```

Expected: at least one index fragment matches. If the index is empty, the `postbuild` step did not run — check `npm run build` output.

- [ ] **Step 5: Commit and open the PR**

```bash
git add site/content/index.mdx
git commit -m "docs(sto-250): point the landing page at the guide that now exists"
git push -u origin markdadamo/sto-250-user-guide
gh pr create --fill
```

- [ ] **Step 6: Confirm CI is green, then confirm the deploy**

Watch both workflows. The `Site builds` job must pass on the PR. After merge, `pages.yml` runs — load the deployed site and check, on the live URL rather than locally:

- the sidebar shows the full guide,
- `/guide/examples/tamagotchi/requirements/functional/` renders with working anchors,
- a search for `FR-001` returns a result,
- the gates page's traceability table renders.

Report these as observed. Pass 1 held the same standard: the deploy and the search index cannot be asserted from a working tree.

---

## Notes for the executor

**Do not hand-edit anything under `site/content/guide/examples/` or `site/content/_generated/`.** Both are generated and both are gated. If a page is wrong, the generator is wrong.

**The two prose-page tasks (10–12) have no failing test to write first.** Their discipline is the claim list: every factual sentence must be traceable to a cited source file, and Step 4 of each task is the check. Pass 1 shipped two false claims that only review caught, both about what the pipeline emits — that is the specific failure mode to guard against here.

**If a task's expected test count or artifact count does not match what you find**, the committed sets or the suite have moved since this plan was written. Update the expectation to the real value and say so in the commit body. Never loosen an assertion to make it pass.

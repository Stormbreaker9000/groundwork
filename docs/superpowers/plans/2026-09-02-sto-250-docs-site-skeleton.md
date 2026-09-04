# Docs Site Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a deployed, green, four-page Nextra documentation site on GitHub Pages, with a generated rule reference that cannot drift from the linters it documents.

**Architecture:** A self-contained Next.js/Nextra app under `site/` with its own `package.json`, static-exported and deployed by GitHub Actions. A Python exporter imports the repository's own sources of truth — the two content linters' rule registries, both artifact JSON Schemas, and the agent frontmatter — and writes committed JSON that the site renders. Each linter gains a declarative `RULES` registry that a test holds equal to the rule identifiers the suite actually emits, so a new check with no registry entry fails the suite before it can reach the docs.

**Tech Stack:** Nextra 4 + Next.js (App Router, `output: 'export'`), React 19, Node 22, Python 3.12 (stdlib only), pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-sto-250-docs-site-skeleton-design.md`

## Global Constraints

- **Python is stdlib-only.** `export_reference.py` may not import `yaml`, `jsonschema`, or any third-party package. The linters it imports already bootstrap `lib/` onto `sys.path` themselves.
- **The root `package.json` is not touched.** It is the plugin's. All JavaScript dependencies live in `site/package.json`.
- **`site/content/_generated/*.json` is committed**, and the site build must not require Python. `npm run build` runs `next build` only. The exporter is a separate `npm run reference` script, gated by CI.
- **Static export config, exactly:** `output: 'export'`, `basePath: '/groundwork'`, `trailingSlash: true`, `images: { unoptimized: true }`. Omitting any one produces a site that works locally and 404s in production.
- **The published URL is** `https://stormbreaker9000.github.io/groundwork/`. No custom domain.
- **JSON output is written with** `indent=2, sort_keys=True` **and a trailing newline**, so the CI drift check diffs cleanly.
- **Do not modify any `check_*` function's behaviour.** The `RULES` registries are purely additive.
- **Existing test suite must stay green:** `python3 -m pytest` from the repo root, 267 tests passing before this plan starts.

---

## File Structure

**New — site application**

| File | Responsibility |
|---|---|
| `site/package.json` | JS dependencies and the `build` / `reference` scripts. Isolated from the plugin package. |
| `site/next.config.mjs` | Nextra wrapper plus the four static-export settings. |
| `site/app/layout.jsx` | Root layout: navbar, footer, page map. |
| `site/app/[[...mdxPath]]/page.jsx` | Catch-all route that renders MDX from `content/`. |
| `site/mdx-components.js` | MDX component mapping required by Nextra 4. |
| `site/components/RuleTable.jsx` | Renders one linter's rules from `rules.json`. The only consumer of generated data in this pass. |
| `site/.gitignore` | `node_modules`, `.next`, `out`, and the search index directory. |

**New — content**

| File | Responsibility |
|---|---|
| `site/content/_meta.js` | Top-level navigation order. |
| `site/content/index.mdx` | Landing page. |
| `site/content/guide/_meta.js` | Guide section order. |
| `site/content/guide/installation.mdx` | Install and first run. |
| `site/content/guide/reference/_meta.js` | Reference section order. |
| `site/content/guide/reference/rules.mdx` | Generated rule reference — the proof obligation. |
| `site/content/architecture/index.mdx` | Stub owned by STO-220. |
| `site/content/_generated/rules.json` | Committed. Both linters' registries. |
| `site/content/_generated/fields.json` | Committed. Both schemas' frontmatter fields. |
| `site/content/_generated/agents.json` | Committed. The 15-agent roster. |

**New — tooling**

| File | Responsibility |
|---|---|
| `site/scripts/export_reference.py` | Reads the real sources, writes the three JSON files. |
| `site/scripts/tests/conftest.py` | Puts `site/scripts/` on `sys.path`, mirroring the two existing conftests. |
| `site/scripts/tests/test_export_reference.py` | Asserts exporter output shape against real repository sources. |
| `.github/workflows/ci.yml` | pytest + the generated-output drift gate. First CI in this repo. |
| `.github/workflows/pages.yml` | Build and deploy to GitHub Pages. |

**Modified**

| File | Change |
|---|---|
| `skills/design/scripts/lint_design_content.py` | Add `RULES` (8 entries) below the `CHECKS`/`SET_CHECKS` registries. |
| `skills/requirements/scripts/lint_requirements_content.py` | Add `RULES` (6 entries) below its registries. |
| `skills/design/scripts/tests/test_lint_design_content.py` | Add two registry-sync tests. |
| `skills/requirements/scripts/tests/test_lint_content.py` | Add two registry-sync tests. |
| `README.md` | Remove statements that are no longer true; link the site. |

---

## Task 1: Prove Nextra 4 static-exports

This task exists because the spec's D9 risk is unresolved: nothing published confirms that Nextra 4.6.1 with Next 16 produces a working search index under `output: 'export'`. Resolve it before any content exists to lose.

**Files:**
- Create: `site/package.json`, `site/next.config.mjs`, `site/app/layout.jsx`, `site/app/[[...mdxPath]]/page.jsx`, `site/mdx-components.js`, `site/.gitignore`, `site/content/index.mdx`, `site/content/_meta.js`

**Interfaces:**
- Consumes: nothing.
- Produces: a working `site/` app. Later tasks add `content/**` pages and `components/RuleTable.jsx`; they assume `npm run build` in `site/` emits static HTML into `site/out/`.

- [ ] **Step 1: Read the current Nextra 4 App Router setup before writing any of it**

The scaffold below is the expected shape, not gospel — this plan was written against Nextra 4.6.1 metadata, not a live install. Fetch `https://nextra.site/docs/docs-theme/start` and `https://nextra.site/docs/guide/static-exports` first and reconcile. **If the official scaffold differs from the snippets below, follow the official scaffold and note the difference in the commit message.**

Pay specific attention to how search works in Nextra 4 under `output: 'export'`. If it requires a postbuild indexing step, that step belongs in `site/package.json`'s `build` script and must be recorded in Step 7.

- [ ] **Step 2: Create the package manifest**

```bash
mkdir -p site/app/'[[...mdxPath]]' site/content
```

```json
{
  "name": "groundwork-docs",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "reference": "python3 scripts/export_reference.py"
  },
  "dependencies": {
    "next": "^16.3.4",
    "nextra": "^4.6.1",
    "nextra-theme-docs": "^4.6.1",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }
}
```

`build` is `next build` alone. The generated JSON is committed, so the site builds without Python — see the Global Constraints.

- [ ] **Step 3: Create the Next config with all four export settings**

```js
// site/next.config.mjs
import nextra from 'nextra'

const withNextra = nextra({})

export default withNextra({
  output: 'export',
  basePath: '/groundwork',
  trailingSlash: true,
  images: { unoptimized: true }
})
```

- [ ] **Step 4: Create the layout, route, and MDX mapping**

```jsx
// site/app/layout.jsx
import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'

export const metadata = {
  title: { default: 'Groundwork', template: '%s — Groundwork' },
  description: 'SDLC discipline workflows for Claude Code'
}

export default async function RootLayout({ children }) {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={<Navbar logo={<b>Groundwork</b>} />}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/Stormbreaker9000/groundwork/tree/main/site"
          footer={<Footer>MIT © Mark D&apos;Adamo</Footer>}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
```

```jsx
// site/app/[[...mdxPath]]/page.jsx
import { generateStaticParamsFor, importPage } from 'nextra/pages'
import { useMDXComponents as getMDXComponents } from '../../mdx-components'

export const generateStaticParams = generateStaticParamsFor('mdxPath')

export async function generateMetadata(props) {
  const params = await props.params
  const { metadata } = await importPage(params.mdxPath)
  return metadata
}

const Wrapper = getMDXComponents().wrapper

export default async function Page(props) {
  const params = await props.params
  const result = await importPage(params.mdxPath)
  const { default: MDXContent, toc, metadata } = result
  return (
    <Wrapper toc={toc} metadata={metadata}>
      <MDXContent {...props} params={params} />
    </Wrapper>
  )
}
```

```js
// site/mdx-components.js
import { useMDXComponents as getThemeComponents } from 'nextra-theme-docs'

const themeComponents = getThemeComponents()

export function useMDXComponents(components) {
  return { ...themeComponents, ...components }
}
```

- [ ] **Step 5: Add a single placeholder page and the nav order**

```mdx
<!-- site/content/index.mdx -->
# Groundwork

Placeholder. Replaced in Task 6.
```

```js
// site/content/_meta.js
export default {
  index: 'Introduction'
}
```

- [ ] **Step 6: Ignore build artifacts**

```
# site/.gitignore
node_modules/
.next/
out/
.pagefind/
```

- [ ] **Step 7: Install and build**

Run:
```bash
cd site && npm install && npm run build
```
Expected: exits 0, and `site/out/index.html` exists.

If it fails, walk the spec's D9 ladder in order and record which rung worked in the commit message: (1) pin `next` to `^15`, reinstall, rebuild; (2) if that also fails, stop and report — the fallback is deploying to Vercel instead of Pages, which is a change to Task 8 and needs a decision, not a workaround.

- [ ] **Step 8: Verify the export actually produced a static site**

Run:
```bash
ls site/out/ && grep -c "Groundwork" site/out/index.html
```
Expected: `index.html` present, and the grep count is 1 or more — proving MDX rendered rather than a shell that hydrates client-side.

- [ ] **Step 9: Verify search survived the export**

Run:
```bash
cd site && npx serve out -l 3000
```
Open `http://localhost:3000/groundwork/`, use the search box, confirm a query for "groundwork" returns a result. **This is the D9 risk and the one thing a green build does not prove.** Record the outcome — mechanism used, and any postbuild step added — in the commit message.

- [ ] **Step 10: Commit**

```bash
git add site/ && git commit -m "feat(sto-250): Nextra 4 app that static-exports for GitHub Pages"
```

---

## Task 2: `RULES` registry for the design linter

**Files:**
- Modify: `skills/design/scripts/lint_design_content.py` (append after `SET_CHECKS`, around line 512)
- Test: `skills/design/scripts/tests/test_lint_design_content.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `lint_design_content.RULES`, a `List[Dict[str, Any]]` where each entry has keys `id` (str), `severities` (List[str]), `applies_to` (str), `field` (str), `summary` (str). Task 4's exporter reads exactly these five keys.

`severities` is a **list**, not a scalar, because `check_vague_responsibility` and `check_adr_vague_driver` emit `"info" if quantified else "warn"` (lines 98 and 329). A scalar cannot describe them honestly.

- [ ] **Step 1: Write the failing tests**

Append to `skills/design/scripts/tests/test_lint_design_content.py`:

```python
def _all_emitted_findings():
    """Every finding the whole lint fixture corpus produces."""
    findings = []
    for name in sorted(os.listdir(LINT)):
        path = os.path.join(LINT, name)
        if os.path.isdir(path):
            findings.extend(ldc.lint_dir(path))
    return findings


def test_rules_registry_matches_emitted_rules():
    # Bidirectional: a new check with no RULES entry fails here, and so does
    # a RULES entry no fixture exercises. The second direction doubles as a
    # coverage assertion — every documented rule has a fixture proving it.
    emitted = {f.rule for f in _all_emitted_findings()}
    declared = {r["id"] for r in ldc.RULES}
    assert emitted == declared


def test_emitted_severities_are_declared():
    declared = {r["id"]: set(r["severities"]) for r in ldc.RULES}
    for finding in _all_emitted_findings():
        assert finding.severity in declared[finding.rule], (
            f"{finding.rule} emitted severity {finding.severity!r}, "
            f"registry declares {sorted(declared[finding.rule])}"
        )


def test_rules_registry_entries_are_complete():
    for rule in ldc.RULES:
        assert set(rule) == {"id", "severities", "applies_to", "field", "summary"}
        assert rule["id"] and rule["summary"] and rule["field"]
        assert rule["severities"]
        assert rule["applies_to"] in {"component", "interface", "adr"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -k registry -v`
Expected: FAIL with `AttributeError: module 'lint_design_content' has no attribute 'RULES'`

- [ ] **Step 3: Add the registry**

Insert into `skills/design/scripts/lint_design_content.py` immediately after the `SET_CHECKS` list and before `def lint_dir`:

```python
# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------
# Declarative description of every rule the checks above can emit, read by
# site/scripts/export_reference.py to build the published rule reference.
# ``test_rules_registry_matches_emitted_rules`` holds this equal, in both
# directions, to what the fixture corpus actually produces — so a new check
# with no entry here fails the suite before it can reach the documentation,
# and an entry no fixture exercises fails too.
#
# ``severities`` is a list because two rules demote to "info" when the text
# they flag carries a number.
RULES: List[Dict[str, Any]] = [
    {
        "id": "vague-responsibility",
        "severities": ["warn", "info"],
        "applies_to": "component",
        "field": "responsibility",
        "summary": (
            "A component responsibility uses a vague qualifier with no "
            "concrete metric. Demoted to info when the sentence carries a "
            "number."
        ),
    },
    {
        "id": "god-component",
        "severities": ["warn"],
        "applies_to": "component",
        "field": "responsibility",
        "summary": (
            "Two actions joined by a conjunction in one responsibility — "
            "the component is doing two jobs."
        ),
    },
    {
        "id": "error-modes-handwaved",
        "severities": ["warn"],
        "applies_to": "interface",
        "field": "error_modes",
        "summary": (
            "An error mode gestures at failure rather than naming one."
        ),
    },
    {
        "id": "orphan-interface",
        "severities": ["warn"],
        "applies_to": "interface",
        "field": "id",
        "summary": (
            "The contract is provided but consumed by no component. Set-level "
            "check: not decidable from a single file."
        ),
    },
    {
        "id": "adr-consequences-one-sided",
        "severities": ["warn"],
        "applies_to": "adr",
        "field": "consequences",
        "summary": (
            "Consequences list only upsides; no cost is recorded. A decision "
            "with no downside was not a decision."
        ),
    },
    {
        "id": "adr-vague-driver",
        "severities": ["warn", "info"],
        "applies_to": "adr",
        "field": "decision_drivers",
        "summary": (
            "A decision driver names no threshold the chosen option can be "
            "checked against. Demoted to info when the line carries a number."
        ),
    },
    {
        "id": "adr-option-unexamined",
        "severities": ["info"],
        "applies_to": "adr",
        "field": "considered_options",
        "summary": (
            "An option listed in frontmatter never appears under the "
            "'Considered Options' heading, so it was named but not weighed."
        ),
    },
    {
        "id": "dependency-cycle",
        "severities": ["warn"],
        "applies_to": "component",
        "field": "depends_on",
        "summary": (
            "A cycle in the component graph where every individual edge "
            "resolves. Set-level check: invisible one file at a time."
        ),
    },
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_lint_design_content.py -v`
Expected: PASS, 45 tests (42 existing + 3 new)

- [ ] **Step 5: Run the whole suite for regressions**

Run: `python3 -m pytest -q`
Expected: 270 passed

- [ ] **Step 6: Commit**

```bash
git add skills/design/scripts/lint_design_content.py skills/design/scripts/tests/test_lint_design_content.py
git commit -m "feat(sto-250): declarative RULES registry for the design linter"
```

---

## Task 3: `RULES` registry for the requirements linter

Same shape as Task 2, different module and a different rule set. The code is repeated in full rather than referenced, because tasks are executed independently and possibly out of order.

**Files:**
- Modify: `skills/requirements/scripts/lint_requirements_content.py` (append after `SET_CHECKS`, around line 335)
- Test: `skills/requirements/scripts/tests/test_lint_content.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `lint_requirements_content.RULES`, same five-key entry shape as Task 2 except that `applies_to` is `"requirement"` for every entry — the requirements linter's checks are not typed by artifact category the way the design linter's are.

- [ ] **Step 1: Write the failing tests**

Append to `skills/requirements/scripts/tests/test_lint_content.py`. Note this file's fixture constant is `CONTENT`, and the module alias is `lc` — not `LINT`/`ldc` as in the design suite.

```python
def _all_emitted_findings():
    """Every finding the whole content fixture corpus produces."""
    findings = []
    for name in sorted(os.listdir(CONTENT)):
        path = os.path.join(CONTENT, name)
        if os.path.isdir(path):
            findings.extend(lc.lint_dir(path))
    return findings


def test_rules_registry_matches_emitted_rules():
    emitted = {f.rule for f in _all_emitted_findings()}
    declared = {r["id"] for r in lc.RULES}
    assert emitted == declared


def test_emitted_severities_are_declared():
    declared = {r["id"]: set(r["severities"]) for r in lc.RULES}
    for finding in _all_emitted_findings():
        assert finding.severity in declared[finding.rule], (
            f"{finding.rule} emitted severity {finding.severity!r}, "
            f"registry declares {sorted(declared[finding.rule])}"
        )


def test_rules_registry_entries_are_complete():
    for rule in lc.RULES:
        assert set(rule) == {"id", "severities", "applies_to", "field", "summary"}
        assert rule["id"] and rule["summary"] and rule["field"]
        assert rule["severities"]
        assert rule["applies_to"] == "requirement"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest skills/requirements/scripts/tests/test_lint_content.py -k registry -v`
Expected: FAIL with `AttributeError: module 'lint_requirements_content' has no attribute 'RULES'`

- [ ] **Step 3: Add the registry**

Insert into `skills/requirements/scripts/lint_requirements_content.py` immediately after the `SET_CHECKS` list and before `def lint_dir`:

```python
# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------
# Declarative description of every rule the checks above can emit, read by
# site/scripts/export_reference.py to build the published rule reference.
# ``test_rules_registry_matches_emitted_rules`` holds this equal, in both
# directions, to what the fixture corpus actually produces.
#
# ``severities`` is a list because two rules demote to "info" when the text
# they flag carries a number.
RULES: List[Dict[str, Any]] = [
    {
        "id": "vague-qualifier",
        "severities": ["warn", "info"],
        "applies_to": "requirement",
        "field": "description",
        "summary": (
            "A vague qualifier with no concrete metric. Demoted to info when "
            "the sentence carries a number."
        ),
    },
    {
        "id": "compound",
        "severities": ["warn"],
        "applies_to": "requirement",
        "field": "description",
        "summary": (
            "Multiple actions joined by a conjunction in one requirement, "
            "which cannot be verified or traced as a single unit."
        ),
    },
    {
        "id": "ears-conformance",
        "severities": ["warn"],
        "applies_to": "requirement",
        "field": "description",
        "summary": (
            "The description does not match the shape of the EARS pattern "
            "the requirement declares."
        ),
    },
    {
        "id": "passive-nameless",
        "severities": ["warn"],
        "applies_to": "requirement",
        "field": "description",
        "summary": "Passive voice hides the responsible actor.",
    },
    {
        "id": "impl-bias",
        "severities": ["info"],
        "applies_to": "requirement",
        "field": "description",
        "summary": (
            "An implementation detail appears in a requirement whose tier "
            "should stay solution-free."
        ),
    },
    {
        "id": "glossary-unused",
        "severities": ["warn"],
        "applies_to": "requirement",
        "field": "terms",
        "summary": (
            "A glossary term no requirement uses. Set-level check: not "
            "decidable from a single file."
        ),
    },
]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest skills/requirements/scripts/tests/test_lint_content.py -v`
Expected: PASS, 34 tests (31 existing + 3 new)

- [ ] **Step 5: Run the whole suite for regressions**

Run: `python3 -m pytest -q`
Expected: 273 passed

- [ ] **Step 6: Commit**

```bash
git add skills/requirements/scripts/lint_requirements_content.py skills/requirements/scripts/tests/test_lint_content.py
git commit -m "feat(sto-250): declarative RULES registry for the requirements linter"
```

---

## Task 4: Exporter — `rules.json`

**Files:**
- Create: `site/scripts/export_reference.py`, `site/scripts/tests/conftest.py`, `site/scripts/tests/test_export_reference.py`
- Create: `site/content/_generated/rules.json` (generated, committed)

**Interfaces:**
- Consumes: `lint_design_content.RULES` and `lint_requirements_content.RULES` from Tasks 2 and 3 — the five-key entry shape.
- Produces:
  - `export_reference.REPO_ROOT: str` — absolute path to the repository root
  - `export_reference.OUT_DIR: str` — absolute path to `site/content/_generated`
  - `export_reference.export_rules() -> Dict[str, Any]`
  - `export_reference.write_json(name: str, payload: Any) -> str` — writes `OUT_DIR/<name>`, returns the path
  - `export_reference.main(argv: Optional[List[str]] = None) -> int` — `--check` exits 1 when output is stale
  - Task 5 adds `export_fields()` and `export_agents()` to this same module. Task 6 imports the emitted `rules.json`.

- [ ] **Step 1: Create the test conftest**

```python
# site/scripts/tests/conftest.py
"""Pytest configuration: make the exporter module importable.

The exporter lives one directory up (site/scripts/). Add that directory to
sys.path so `import export_reference` works regardless of the directory
pytest is invoked from. Mirrors the two conftests under skills/.
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
```

- [ ] **Step 2: Write the failing test**

```python
# site/scripts/tests/test_export_reference.py
"""Tests for the documentation-site reference exporter (STO-250)."""
import json
import os

import export_reference as er

ENTRY_KEYS = {"id", "severities", "applies_to", "field", "summary"}


def test_export_rules_has_both_linters():
    payload = er.export_rules()
    assert set(payload) == {"design", "requirements"}


def test_export_rules_records_its_source_module():
    payload = er.export_rules()
    assert payload["design"]["linter"] == "lint_design_content.py"
    assert payload["requirements"]["linter"] == "lint_requirements_content.py"


def test_export_rules_carries_every_registry_entry():
    payload = er.export_rules()
    assert len(payload["design"]["rules"]) == 8
    assert len(payload["requirements"]["rules"]) == 6
    for section in payload.values():
        for rule in section["rules"]:
            assert set(rule) == ENTRY_KEYS


def test_export_rules_is_the_registry_not_a_copy():
    # The exporter must not restate rule text. If it drifts from the
    # registry, this fails.
    import lint_design_content as ldc
    payload = er.export_rules()
    assert [r["id"] for r in payload["design"]["rules"]] == [
        r["id"] for r in ldc.RULES
    ]


def test_written_json_is_stable_and_newline_terminated():
    target = os.path.join(er.OUT_DIR, "rules.json")
    with open(target, "r", encoding="utf-8") as handle:
        text = handle.read()
    assert text.endswith("\n")
    assert json.loads(text) == json.loads(
        json.dumps(er.export_rules(), indent=2, sort_keys=True)
    )
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'export_reference'`

- [ ] **Step 4: Write the exporter**

```python
#!/usr/bin/env python3
"""Export machine-readable reference data for the documentation site (STO-250).

Reads the repository's own sources of truth — the two content linters' RULES
registries, both artifact JSON Schemas, and the agent frontmatter — and writes
JSON into ``site/content/_generated/`` for the site to render.

Python rather than Node because it *imports* the linter modules and reads
their actual registries, instead of regexing Python source from JavaScript.

The outputs are committed and the site build does not run this script; CI
re-runs it and fails on any diff, so a change to a rule cannot land without
the published reference changing with it.

Stdlib only, like every other script in this repository.

Usage
-----
    python3 site/scripts/export_reference.py
    python3 site/scripts/export_reference.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "site", "content", "_generated")

# The linters bootstrap lib/ onto sys.path themselves when imported; this only
# has to make the linter modules findable.
for _scripts_dir in (
    os.path.join(REPO_ROOT, "skills", "design", "scripts"),
    os.path.join(REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)

import lint_design_content as ldc  # noqa: E402
import lint_requirements_content as lrc  # noqa: E402


def export_rules() -> Dict[str, Any]:
    """Both linters' rule registries, verbatim.

    Deliberately does not restate or reformat rule text: the registry is the
    source, and any transformation here would be a place for drift to live.
    """
    return {
        "design": {
            "linter": "lint_design_content.py",
            "rules": ldc.RULES,
        },
        "requirements": {
            "linter": "lint_requirements_content.py",
            "rules": lrc.RULES,
        },
    }


def write_json(name: str, payload: Any) -> str:
    """Write ``payload`` to ``OUT_DIR/name``, stably and diff-cleanly."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


OUTPUTS = {
    "rules.json": export_rules,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export reference data for the Groundwork docs site."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any committed output is stale, writing nothing",
    )
    args = parser.parse_args(argv)

    stale: List[str] = []
    for name, builder in sorted(OUTPUTS.items()):
        expected = json.dumps(builder(), indent=2, sort_keys=True) + "\n"
        path = os.path.join(OUT_DIR, name)
        if args.check:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    if handle.read() != expected:
                        stale.append(name)
            except OSError:
                stale.append(name)
        else:
            write_json(name, builder())

    if args.check and stale:
        for name in stale:
            print(f"stale: site/content/_generated/{name}", file=sys.stderr)
        print(
            "run: python3 site/scripts/export_reference.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Generate the output**

Run: `python3 site/scripts/export_reference.py && cat site/content/_generated/rules.json | head -20`
Expected: exits 0; the file exists. `sort_keys` alphabetises each object's keys but does not reorder the rules array, so the first design entry is `vague-responsibility` — registry order — with its own keys printed `applies_to, field, id, severities, summary`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -v`
Expected: PASS, 5 tests

- [ ] **Step 7: Verify the check mode detects staleness**

Run:
```bash
python3 site/scripts/export_reference.py --check; echo "clean exit: $?"
printf 'garbage\n' > site/content/_generated/rules.json
python3 site/scripts/export_reference.py --check; echo "stale exit: $?"
python3 site/scripts/export_reference.py
```
Expected: `clean exit: 0`, then `stale exit: 1` with a `stale: ...` line on stderr, then regenerated.

- [ ] **Step 8: Run the whole suite**

Run: `python3 -m pytest -q`
Expected: 278 passed

- [ ] **Step 9: Commit**

```bash
git add site/scripts site/content/_generated
git commit -m "feat(sto-250): reference exporter, and the generated rule data"
```

---

## Task 5: Exporter — `fields.json` and `agents.json`

Neither output has a page rendering it until pass 2. They are built now so the drift gate covers the schemas and the agent roster from day one — the guides written in passes 2 and 3 are then written against data that cannot silently go stale underneath them.

**Files:**
- Modify: `site/scripts/export_reference.py`
- Modify: `site/scripts/tests/test_export_reference.py`
- Create: `site/content/_generated/fields.json`, `site/content/_generated/agents.json` (generated, committed)

**Interfaces:**
- Consumes: `export_reference.REPO_ROOT`, `OUT_DIR`, `write_json`, `OUTPUTS` from Task 4.
- Produces:
  - `export_fields() -> Dict[str, List[Dict[str, Any]]]` keyed `"design"` / `"requirements"`; each field entry has `name`, `type`, `enum`, `required_for`, `description`. `required_for` is `["*"]` for unconditionally required fields, a list of artifact-type strings for conditionally required ones, and `[]` for optional.
  - `export_agents() -> List[Dict[str, str]]` — 15 entries with `name` (filename stem), `title` (H1), `description` (frontmatter).

- [ ] **Step 1: Write the failing tests**

Append to `site/scripts/tests/test_export_reference.py`:

```python
def test_export_fields_covers_both_schemas():
    payload = er.export_fields()
    assert set(payload) == {"design", "requirements"}


def test_design_fields_include_base_and_conditional_properties():
    fields = {f["name"]: f for f in er.export_fields()["design"]}
    # Base property, required for every design artifact.
    assert fields["id"]["required_for"] == ["*"]
    # Conditional: only components must declare a responsibility.
    assert fields["responsibility"]["required_for"] == ["component"]
    # Conditional: only interfaces must declare a provider.
    assert fields["provider"]["required_for"] == ["interface"]
    # Enums survive.
    assert set(fields["type"]["enum"]) == {
        "component", "interface", "adr", "diagram"
    }


def test_requirement_conditional_required_without_added_properties():
    # requirement.schema.json's only allOf branch adds a `required` entry for
    # a property already declared in the base `properties` block. The
    # extractor must annotate the existing field rather than skip the branch.
    fields = {f["name"]: f for f in er.export_fields()["requirements"]}
    assert fields["ears_pattern"]["required_for"] == ["functional"]


def test_export_agents_covers_every_agent_file():
    agents = er.export_agents()
    on_disk = [
        n[:-3] for n in os.listdir(os.path.join(er.REPO_ROOT, "agents"))
        if n.endswith(".md")
    ]
    assert len(agents) == len(on_disk) == 15
    assert {a["name"] for a in agents} == set(on_disk)


def test_export_agents_reads_title_and_description():
    by_name = {a["name"]: a for a in er.export_agents()}
    assert by_name["design-critic"]["title"] == "Design Critic"
    assert by_name["design-critic"]["description"].startswith(
        "Architecture quality critic."
    )
    for agent in er.export_agents():
        assert agent["title"], f"{agent['name']} has no H1"
        assert agent["description"], f"{agent['name']} has no description"


def test_all_outputs_are_written_and_current():
    assert er.main(["--check"]) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -k "fields or agents" -v`
Expected: FAIL with `AttributeError: module 'export_reference' has no attribute 'export_fields'`

- [ ] **Step 3: Add the two extractors**

Insert into `site/scripts/export_reference.py` after `export_rules`:

First add `re` to the import block at the top of the file, alongside `argparse`, `json`, `os` and `sys`. Then append the following after `export_rules`:

```python
SCHEMAS = {
    "design": os.path.join(
        REPO_ROOT, "skills", "design", "schema", "design.schema.json"
    ),
    "requirements": os.path.join(
        REPO_ROOT, "skills", "requirements", "schema", "requirement.schema.json"
    ),
}

_H1_RE = re.compile(r"^# (.+)$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(
    r"\A---\s*\n\s*description:\s*(.+?)\s*\n---\s*$", re.MULTILINE
)


def _field_entry(name: str, prop: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": name,
        "type": prop.get("type", ""),
        "enum": prop.get("enum", []),
        "required_for": [],
        "description": prop.get("description", ""),
    }


def _schema_fields(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten one artifact schema into a renderable field list.

    Both schemas share a shape: a base ``properties``/``required`` block, then
    an ``allOf`` of ``if type == <const>`` / ``then`` branches. A branch may
    add properties (design), or only mark an existing base property required
    for one type (requirements' ``ears_pattern``) — both are handled.

    Nested ``allOf`` inside a ``then`` is not descended into. Today that only
    affects two ADR/diagram sub-constraints, neither of which introduces a
    field name the base or branch blocks do not already declare.
    """
    fields: List[Dict[str, Any]] = []
    by_name: Dict[str, Dict[str, Any]] = {}

    for name, prop in schema.get("properties", {}).items():
        entry = _field_entry(name, prop)
        fields.append(entry)
        by_name[name] = entry

    for name in schema.get("required", []):
        if name in by_name:
            by_name[name]["required_for"] = ["*"]

    for branch in schema.get("allOf", []):
        const = (
            branch.get("if", {})
            .get("properties", {})
            .get("type", {})
            .get("const")
        )
        if const is None:
            continue
        then = branch.get("then", {})
        for name, prop in then.get("properties", {}).items():
            if name not in by_name:
                entry = _field_entry(name, prop)
                fields.append(entry)
                by_name[name] = entry
        for name in then.get("required", []):
            entry = by_name.get(name)
            if entry is None:
                continue
            if entry["required_for"] == ["*"]:
                continue
            if const not in entry["required_for"]:
                entry["required_for"].append(const)

    return fields


def export_fields() -> Dict[str, List[Dict[str, Any]]]:
    """Frontmatter field tables, read from the two canonical JSON Schemas."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    for stage, path in SCHEMAS.items():
        with open(path, "r", encoding="utf-8") as handle:
            out[stage] = _schema_fields(json.load(handle))
    return out


def export_agents() -> List[Dict[str, str]]:
    """The agent roster, from each file's frontmatter description and H1.

    Every agent file carries a three-line frontmatter block whose single key
    is ``description``; the agent's name is its filename, not a frontmatter
    field. ``test_export_agents_reads_title_and_description`` fails if that
    stops being true.
    """
    agents_dir = os.path.join(REPO_ROOT, "agents")
    out: List[Dict[str, str]] = []
    for filename in sorted(os.listdir(agents_dir)):
        if not filename.endswith(".md"):
            continue
        with open(
            os.path.join(agents_dir, filename), "r", encoding="utf-8"
        ) as handle:
            text = handle.read()
        heading = _H1_RE.search(text)
        description = _DESCRIPTION_RE.search(text)
        raw = description.group(1).strip() if description else ""
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        out.append(
            {
                "name": filename[:-3],
                "title": heading.group(1).strip() if heading else "",
                "description": raw,
            }
        )
    return out
```

- [ ] **Step 4: Register the two new outputs**

Replace the `OUTPUTS` dict in `site/scripts/export_reference.py`:

```python
OUTPUTS = {
    "rules.json": export_rules,
    "fields.json": export_fields,
    "agents.json": export_agents,
}
```

- [ ] **Step 5: Generate and inspect**

Run:
```bash
python3 site/scripts/export_reference.py
python3 -c "
import json
f=json.load(open('site/content/_generated/fields.json'))
a=json.load(open('site/content/_generated/agents.json'))
print('design fields:', len(f['design']), 'requirement fields:', len(f['requirements']))
print('agents:', len(a))
"
```
Expected: agents 15; both field lists non-empty (design ≥ 11 base + 8 conditional, requirements ≥ 17).

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -v`
Expected: PASS, 11 tests

- [ ] **Step 7: Run the whole suite**

Run: `python3 -m pytest -q`
Expected: 284 passed

- [ ] **Step 8: Commit**

```bash
git add site/scripts site/content/_generated
git commit -m "feat(sto-250): export schema field tables and the agent roster"
```

---

## Task 6: The four pages, with the rule reference rendered from generated data

**Files:**
- Create: `site/components/RuleTable.jsx`, `site/content/guide/_meta.js`, `site/content/guide/installation.mdx`, `site/content/guide/reference/_meta.js`, `site/content/guide/reference/rules.mdx`, `site/content/architecture/index.mdx`
- Modify: `site/content/index.mdx`, `site/content/_meta.js`

**Interfaces:**
- Consumes: `site/content/_generated/rules.json` from Task 4 — specifically `rules[linter].rules[]` with keys `id`, `severities`, `applies_to`, `field`, `summary`. The working Nextra app from Task 1.
- Produces: four routes — `/`, `/guide/installation/`, `/guide/reference/rules/`, `/architecture/`.

- [ ] **Step 1: Write the rule table component**

```jsx
// site/components/RuleTable.jsx
import rules from '../content/_generated/rules.json'

/**
 * Renders one linter's rules from generated data.
 *
 * Nothing here restates a rule. Change a severity in the linter, re-run the
 * exporter, and this table changes with it — which is the whole point.
 */
export function RuleTable({ linter }) {
  const section = rules[linter]

  return (
    <table>
      <thead>
        <tr>
          <th>Rule</th>
          <th>Severity</th>
          <th>Applies to</th>
          <th>Field</th>
          <th>What it catches</th>
        </tr>
      </thead>
      <tbody>
        {section.rules.map(rule => (
          <tr key={rule.id}>
            <td><code>{rule.id}</code></td>
            <td>{rule.severities.join(' / ')}</td>
            <td>{rule.applies_to}</td>
            <td><code>{rule.field}</code></td>
            <td>{rule.summary}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

- [ ] **Step 2: Write the landing page**

```mdx
<!-- site/content/index.mdx -->
# Groundwork

Groundwork is a Claude Code plugin that puts structure in front of code. It
runs two stages before anything gets built, and each one emits atomic,
validated artifacts rather than a document you have to trust.

**The requirements stage** turns a vague request into functional and
non-functional requirements, constraints and business rules — one file each,
in EARS notation with acceptance criteria, gated by a structural validator.

**The design stage** turns a validated requirement set into components,
interface contracts, architecture decision records and C4 diagrams, traced
back to the requirements that motivated them.

## Where to go

- **[Installation](/guide/installation/)** — add the plugin and run your first
  stage.
- **[Content rules](/guide/reference/rules/)** — every quality rule the
  linters enforce, generated from the linters themselves.
- **[Architecture](/architecture/)** — how the pipeline works, and why.
```

- [ ] **Step 3: Write the installation page**

````mdx
<!-- site/content/guide/installation.mdx -->
# Installation

Groundwork is distributed as a Claude Code plugin.

## Add the marketplace

```
/plugin marketplace add https://github.com/Stormbreaker9000/groundwork
```

## Install the plugin

```
/plugin install groundwork@groundwork-dev
```

## Run it

```
/groundwork
```

That lists the available workflows. You do not have to invoke them by name —
each stage is a skill with its own trigger:

| Stage | Triggers when you | Produces |
|---|---|---|
| `requirements` | describe something to build or add | `.sdlc/requirements/` — one file per requirement, plus assumptions, a glossary and a Definition of Done |
| `design` | have a validated requirement set and want an architecture | `.sdlc/design/` — components, interfaces, ADRs and C4 diagrams |

The design stage expects the requirements stage to have run first: it reads
the validated requirement set as its input.
````

- [ ] **Step 4: Write the generated rule reference**

```mdx
<!-- site/content/guide/reference/rules.mdx -->
import { RuleTable } from '../../../components/RuleTable'

# Content rules

Both stages run a content-quality linter after their structural gates pass.
These linters are **advisory**: they print findings and exit 0, so nothing
here blocks a pipeline run. Pass `--strict` to exit non-zero on an
`error`-severity finding, and `--json` for machine-readable output.

The tables below are generated from the linters' own rule registries. They
cannot describe a rule that does not exist, or miss one that does.

## Design rules

Run by `lint_design_content.py` over `.sdlc/design`.

<RuleTable linter="design" />

## Requirements rules

Run by `lint_requirements_content.py` over `.sdlc/requirements`.

<RuleTable linter="requirements" />

## Reading a severity

A rule listed as `warn / info` demotes itself to `info` when the text it
flagged carries a number — a vague word next to a concrete threshold is
usually prose, not a missing measurement.
```

- [ ] **Step 5: Write the architecture stub**

```mdx
<!-- site/content/architecture/index.mdx -->
# Architecture

This section is not written yet.

It will cover the pipeline as a whole — the stage map, the hand-off contracts
between the fifteen agents, the cross-cutting invariants, and the reasoning
behind the parts of the design that cannot be reconstructed from the code.

Tracked as **STO-220**. Until it lands, the agent files under `agents/` are
the only complete description of the pipeline, and each one describes only
itself.
```

- [ ] **Step 6: Write the navigation metadata**

```js
// site/content/_meta.js
export default {
  index: 'Introduction',
  guide: 'User guide',
  architecture: 'Architecture'
}
```

```js
// site/content/guide/_meta.js
export default {
  installation: 'Installation',
  reference: 'Reference'
}
```

```js
// site/content/guide/reference/_meta.js
export default {
  rules: 'Content rules'
}
```

- [ ] **Step 7: Build and verify all four routes exist**

Run:
```bash
cd site && npm run build && find out -name "*.html" | sort
```
Expected: exits 0, and the output includes `out/index.html`, `out/guide/installation/index.html`, `out/guide/reference/rules/index.html`, `out/architecture/index.html`.

- [ ] **Step 8: Verify the rule table rendered from generated data**

Run:
```bash
grep -c "god-component" site/out/guide/reference/rules/index.html
grep -c "glossary-unused" site/out/guide/reference/rules/index.html
```
Expected: both ≥ 1. These strings exist nowhere in the MDX — if they are in the HTML, the generated JSON reached the page.

- [ ] **Step 9: Prove the generation loop end-to-end**

This is the pass's central claim. Verify it rather than assume it:

```bash
# Temporarily demote a rule in the linter
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("skills/design/scripts/lint_design_content.py")
s = p.read_text()
s = s.replace('"id": "god-component",\n        "severities": ["warn"],',
              '"id": "god-component",\n        "severities": ["warn", "info"],')
p.write_text(s)
PY
python3 site/scripts/export_reference.py
cd site && npm run build && grep -o "warn / info" out/guide/reference/rules/index.html | head -3
```
Expected: `warn / info` now appears for the god-component row, with no MDX edited.

Then revert:
```bash
git checkout skills/design/scripts/lint_design_content.py
python3 site/scripts/export_reference.py
```

- [ ] **Step 10: Commit**

```bash
git add site/
git commit -m "feat(sto-250): the four skeleton pages, with a generated rule reference"
```

---

## Task 7: CI — tests and the drift gate

This repository has no `.github/` directory. The 267 tests have never run anywhere but a developer's machine. This task creates CI, and the drift gate is what makes the generated pages trustworthy.

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `export_reference.main(["--check"])` from Task 4 — exit 1 when stale.
- Produces: a required-status-checkable workflow named `CI`.

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  tests:
    name: Tests and reference drift
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # The validators and linters fall back to stdlib parsing when these are
      # absent, but the primary path is the one users get, so CI exercises it.
      - name: Install test dependencies
        run: pip install pytest pyyaml jsonschema

      - name: Run the test suite
        run: python3 -m pytest -q

      - name: Generated reference is not stale
        run: python3 site/scripts/export_reference.py --check
```

The drift gate uses the exporter's own `--check` rather than a regenerate-then-`git diff`, so the failure message names the stale file and the command that fixes it.

- [ ] **Step 2: Verify the workflow's steps pass locally first**

Run:
```bash
python3 -m pytest -q && python3 site/scripts/export_reference.py --check && echo "CI steps pass locally"
```
Expected: `284 passed`, then `CI steps pass locally`.

- [ ] **Step 3: Verify the gate actually catches drift**

Run:
```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("skills/design/scripts/lint_design_content.py")
s = p.read_text().replace(
    '"summary": (\n            "Two actions joined by a conjunction in one responsibility — "',
    '"summary": (\n            "CHANGED: two actions joined by a conjunction in one responsibility — "')
p.write_text(s)
PY
python3 site/scripts/export_reference.py --check; echo "exit: $?"
git checkout skills/design/scripts/lint_design_content.py
```
Expected: `stale: site/content/_generated/rules.json` on stderr and `exit: 1`. A linter edit without a re-export fails the build.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(sto-250): run the test suite and gate generated reference drift"
```

---

## Task 8: Deploy to GitHub Pages

**Files:**
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: `site/` producing `site/out/` via `npm run build` (Tasks 1 and 6), and `site/package-lock.json` from Task 1's `npm install`.
- Produces: the live site at `https://stormbreaker9000.github.io/groundwork/`.

- [ ] **Step 1: Confirm the lockfile is committed**

Run: `git ls-files site/package-lock.json`
Expected: the path is printed. `npm ci` in the workflow requires it. If absent, run `cd site && npm install` and commit it.

- [ ] **Step 2: Write the deploy workflow**

```yaml
# .github/workflows/pages.yml
name: Deploy docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

# One deploy at a time; never cancel a run that is mid-publish.
concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: site/package-lock.json

      - name: Install
        run: npm ci
        working-directory: site

      # No Python here on purpose: the generated JSON is committed, and CI
      # already fails if it is stale. The site build stays Python-free.
      - name: Build
        run: npm run build
        working-directory: site

      - uses: actions/configure-pages@v5

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/out

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Commit and push**

```bash
git add .github/workflows/pages.yml
git commit -m "ci(sto-250): build and deploy the docs site to GitHub Pages"
git push
```

- [ ] **Step 4: STOP — a human step is required**

The deploy job will fail until someone sets **Settings → Pages → Source** to **GitHub Actions** on `Stormbreaker9000/groundwork`, and the repository must be public for Pages to be free. This cannot be done from a working tree. Ask, wait for confirmation, then re-run the workflow.

- [ ] **Step 5: Verify the deployed site, not the green check**

Open `https://stormbreaker9000.github.io/groundwork/` and confirm, one at a time:

1. The landing page renders with styling — not an unstyled HTML dump, which is the signature of a wrong `basePath`.
2. All three sidebar links load without a 404.
3. `/guide/reference/rules/` shows both tables, populated.
4. Search returns a result for "rules". This is the D9 risk and the thing a green build does not prove.

Report what you actually see. If styling is broken or links 404, the cause is almost always `basePath` or `trailingSlash` — re-check `next.config.mjs` against the Global Constraints before changing anything else.

- [ ] **Step 6: Commit any fixes from Step 5**

```bash
git add site/next.config.mjs && git commit -m "fix(sto-250): correct static-export paths for the project subpath"
```

---

## Task 9: Reconcile the README

The README is the site's front door and currently contradicts it: it documents a `## Requirements Brief` markdown format the pipeline has not emitted since M1, its workflow table has no `design` row, and its roadmap shows "Architecture design workflow" unchecked three months after M2 shipped it. Shipping a site whose entry point states a format the tool does not emit would reproduce, on day one, the failure mode this pass exists to prevent.

This is a correction, not a rewrite. Do not restructure the README.

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the live site URL confirmed in Task 8.
- Produces: nothing other tasks depend on.

- [ ] **Step 1: Read the current README in full**

Run: `cat README.md`

- [ ] **Step 2: Delete the stale Requirements Brief section**

Remove the entire `### Requirements Brief format` subsection — the fenced block showing `## Requirements Brief`, `**Problem:**`, `**Acceptance Criteria:**` and the sentence after it. The pipeline emits atomic Markdown+YAML files under `.sdlc/requirements/`, one per requirement; this block describes output that no longer exists.

- [ ] **Step 3: Replace the workflow table**

```markdown
## Workflows

| Workflow | Trigger | Description |
|---|---|---|
| `requirements` | "build X", "add Y", "make it do Z" | Turns a vague request into atomic, validated requirement artifacts under `.sdlc/requirements/` — functional and non-functional requirements, constraints, business rules, assumptions, a glossary and a Definition of Done |
| `design` | a validated requirement set exists | Turns requirements into an architecture under `.sdlc/design/` — components, interface contracts, MADR architecture decision records and C4 diagrams, each traced back to the requirements that motivated it |

Claude will not write code until you sign off.
```

- [ ] **Step 4: Correct the roadmap**

```markdown
## Roadmap

- [x] Architecture design workflow
- [ ] QA strategy workflow
- [ ] Full Definition of Done generator
- [ ] End-to-end traceability graph and `/sdlc trace`
- [ ] Agile scope parameterization
```

Drop the `requirements-analyst` agent line — that agent exists (`agents/requirements-analyst.md`) and listing it as unbuilt is a third false statement. Drop the `PreToolUse` hooks line only if no ticket still tracks it; otherwise leave it.

- [ ] **Step 5: Add the documentation link under Installation**

```markdown
## Documentation

Full documentation, including the content-rule reference, is at
**https://stormbreaker9000.github.io/groundwork/**.
```

- [ ] **Step 6: Verify no false statements remain**

Run:
```bash
grep -n "Requirements Brief" README.md; echo "---"
grep -n "^- \[ \] Architecture design" README.md; echo "--- (no output above both markers = clean)"
grep -n "design" README.md | head
```
Expected: no `Requirements Brief` matches, no unchecked architecture line, and a `design` workflow row present.

- [ ] **Step 7: Commit**

```bash
git add README.md
git commit -m "docs(sto-250): correct the README's stale workflow and roadmap claims"
```

---

## Definition of Done for this pass

- `python3 -m pytest -q` passes (284 tests) and runs in CI on every push and PR.
- `python3 site/scripts/export_reference.py --check` exits 0, and exits 1 when a linter changes without a re-export — verified by deliberately breaking it, not assumed.
- The site is live at `https://stormbreaker9000.github.io/groundwork/` with four working routes, styling intact, and working search.
- The rule reference page's content changes when a linter's registry changes, with no MDX edited — verified in Task 6 Step 9.
- The README states nothing that is no longer true.

## Notes for the executor

**The version risk is real and lives in Task 1.** This plan was written against npm registry metadata (`nextra@4.6.1`, peers `next >=14`, latest `next` 16.3.4), not a live install. Task 1 Step 1 tells you to read the official Nextra setup before writing the scaffold, and to prefer it over this plan's snippets where they differ. That is not a formality.

**Two steps need a human**, both in Task 8: the Pages source setting, and the repository being public. Stop and ask rather than working around them.

**`fields.json` and `agents.json` have no renderer in this pass.** That is intentional — they are gated by CI from day one so passes 2 and 3 are written against data that cannot go stale underneath them. Do not add pages for them here.

**Out of scope, do not drift into it:** the user guide body, STO-220's architecture content, the STO-257 repo restructure, custom domains, versioned docs, analytics.

# Plugin Subdirectory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the plugin runtime under `plugin/` and repoint the marketplace at it, so a user's install drops from 4.7M to 532K and stops carrying `docs/`, `site/` and 888K of pytest fixtures — and fix the script paths that have never resolved from an installed copy.

**Architecture:** A `git mv` of five directories plus two manifests, the pytest tree lifted out to a top-level `tests/`, one `PLUGIN_ROOT` constant in each of the two site exporters, and a resolution fix that replaces repo-relative script paths with the skill base directory the harness injects — threaded to the two formatter agents through the dispatch they already receive. A new `tests/test_plugin_package.py` turns the ticket's three prose acceptance criteria into assertions.

**Tech Stack:** Python 3.12 stdlib only, pytest, Next.js 16 / Nextra 4, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-06-sto-257-plugin-subdirectory-design.md`

## Global Constraints

- **`skills/` and `lib/` move together.** Every script walks `../../..` from its own `__file__` to find `lib/`. Preserving their relative positions is the entire reason this move needs no Python source changes (spec E1). Splitting them breaks six scripts silently.
- **Stdlib only.** Every script in this repository is stdlib-only, including the new test.
- **The site build stays Python-free.** Generated JSON is committed; the build reads it.
- **Never write `${CLAUDE_PLUGIN_ROOT}` into a SKILL.md or agent command.** It is expanded by the hooks runtime only and is **empty** in the Bash tool's shell, so it silently resolves to `/skills/…` (spec E3). Its one legitimate use is `plugin/hooks/hooks.json`, which is left alone.
- **Never carry a resolved path between command blocks in a variable.** Shell state does not persist across tool calls (spec E4). Each block substitutes the path itself.
- **Parsers and agents raise; they never degrade silently.** A formatter that cannot locate its validator stops and says so rather than falling back to a relative path.
- **Commit message prefix:** `refactor(sto-257):`, `fix(sto-257):` or `docs(sto-257):`, and every commit ends with the two attribution trailers used on this branch.

---

### Task 1: The package gate, then the move

**Files:**
- Create: `tests/test_plugin_package.py`
- Move: `agents/`, `commands/`, `hooks/`, `lib/`, `skills/`, `CLAUDE.md`, `.claude-plugin/plugin.json` → under `plugin/`; `skills/*/scripts/tests/` → `tests/<stage>/`
- Modify: `.claude-plugin/marketplace.json`, `tests/requirements/conftest.py`, `tests/design/conftest.py`, `site/scripts/export_reference.py`, `site/scripts/export_examples.py`, `site/scripts/tests/conftest.py`, `README.md`, `plugin/skills/*/scripts/README.md`
- Create: `CLAUDE.md` (new, contributor-facing)

**Interfaces:**
- Produces: `plugin/` as the published surface; `tests/{requirements,design}/` as the pytest tree; `PLUGIN_ROOT` in both site exporters. Tasks 2 and 3 assume all three exist.
- Produces: `tests/test_plugin_package.py` with `_shipped_paths()`, `REPO_ROOT`, `PLUGIN_DIR` module-level names. Task 2 appends a fourth check to this file.

- [ ] **Step 1: Write the failing package test**

Create `tests/test_plugin_package.py`:

```python
"""The directory boundary is the plugin manifest, so the boundary gets a test.

Installing a Claude Code plugin copies the whole tree under the marketplace
entry's ``source``, minus ``.git``. No ``files``, ``exclude`` or ``ignore``
field exists in any ``plugin.json`` — there is no way to ship a subset of a
directory. So what ships is decided entirely by where the files sit, and
nothing but this test notices when something wanders in.

STO-257 moved the runtime under ``plugin/`` for that reason: before it, every
install carried 2.1M of ``docs/``, 1.1M of Nextra source and 888K of pytest
fixtures, against 532K of actual runtime.
"""
import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
PLUGIN_DIR = os.path.join(REPO_ROOT, "plugin")

# Everything a plugin install is allowed to contain, at the top level.
RUNTIME_TOPLEVEL = {
    ".claude-plugin",
    "CLAUDE.md",
    "agents",
    "commands",
    "hooks",
    "lib",
    "skills",
}

# Path segments that must never appear anywhere under plugin/.
NEVER_SHIP = ("/docs/", "/site/", "/assets/", "/tests/", "/fixtures/")


def _shipped_paths():
    """Every tracked path under ``plugin/``, exactly as an install would copy it.

    Reads ``git ls-files`` rather than walking the filesystem: an install
    copies the tree minus ``.git``, and untracked scratch files in a working
    directory are not what ships. Raises rather than returning an empty list —
    an empty result would make every assertion below vacuously true.
    """
    result = subprocess.run(
        ["git", "ls-files", "plugin"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = result.stdout.split()
    if not paths:
        raise AssertionError(
            "git ls-files plugin returned nothing — is plugin/ tracked?"
        )
    return paths


def test_marketplace_source_points_at_the_plugin_directory():
    # The one line that makes the whole arrangement real. If this reverts to
    # "./" the tree below is still tidy and every user still downloads 4.7M.
    path = os.path.join(REPO_ROOT, ".claude-plugin", "marketplace.json")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    assert [entry["source"] for entry in data["plugins"]] == ["./plugin"]


def test_plugin_ships_only_runtime_directories():
    tops = {path.split("/")[1] for path in _shipped_paths()}
    assert tops == RUNTIME_TOPLEVEL


def test_no_documentation_site_or_fixtures_ship():
    offenders = [
        path
        for path in _shipped_paths()
        if any(segment in path for segment in NEVER_SHIP)
    ]
    assert offenders == []


def test_an_installed_copy_runs_its_own_validator(tmp_path):
    # The check that would have caught the broken path at any point in the
    # last four months. Copy the plugin somewhere else, stand in a directory
    # that is NOT a groundwork checkout, and run the validator by absolute
    # path — which is the only shape available to an installed plugin.
    install = tmp_path / "install"
    shutil.copytree(PLUGIN_DIR, install)

    project = tmp_path / "project"
    (project / ".sdlc").mkdir(parents=True)
    shutil.copytree(
        os.path.join(REPO_ROOT, "tests", "requirements", "fixtures", "valid"),
        project / ".sdlc" / "requirements",
    )

    script = install / "skills" / "requirements" / "scripts" / "validate_requirements.py"
    result = subprocess.run(
        [sys.executable, str(script), ".sdlc/requirements"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_plugin_package.py -q`
Expected: FAIL on all four — `marketplace.json` still says `"./"`, and `git ls-files plugin` returns nothing, so `_shipped_paths()` raises the `is plugin/ tracked?` AssertionError.

- [ ] **Step 3: Move the tree**

Order matters: the runtime goes into `plugin/` first, then the pytest tree is lifted back out of it.

```bash
mkdir -p plugin/.claude-plugin tests
git mv agents commands hooks lib skills plugin/
git mv CLAUDE.md plugin/CLAUDE.md
git mv .claude-plugin/plugin.json plugin/.claude-plugin/plugin.json
git mv plugin/skills/requirements/scripts/tests tests/requirements
git mv plugin/skills/design/scripts/tests tests/design
git status --short | head -20
```

Expected: renames only, no deletions or additions beyond the two new directories.

- [ ] **Step 4: Repoint the marketplace**

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('.claude-plugin/marketplace.json')
data = json.loads(p.read_text())
assert [e["source"] for e in data["plugins"]] == ["./"]
for entry in data["plugins"]:
    entry["source"] = "./plugin"
p.write_text(json.dumps(data, indent=2) + "\n")
PY
cat .claude-plugin/marketplace.json
```

Expected: `"source": "./plugin"`.

- [ ] **Step 5: Repoint the two conftest files**

Both currently resolve the scripts directory as "my own parent directory", which stops being true the moment the tests leave `scripts/`.

`tests/requirements/conftest.py` in full:

```python
"""Pytest configuration: make the validator module importable.

The tests live outside the plugin (STO-257) so their fixtures stop shipping to
every user, so the scripts directory is no longer an ancestor of this file and
has to be named. ``validate_requirements`` itself adds ``plugin/lib/`` to the
path when imported, so the shared core still resolves.
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

`tests/design/conftest.py` in full:

```python
"""Pytest configuration: make the validator module importable.

The tests live outside the plugin (STO-257) so their fixtures stop shipping to
every user, so the scripts directory is no longer an ancestor of this file and
has to be named. ``validate_design`` itself adds ``plugin/lib/`` to the path
when imported, so the shared core still resolves.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "plugin", "skills", "design", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
```

The fixture paths inside the test modules resolve from each test file's own
directory (`HERE = os.path.dirname(os.path.abspath(__file__))`), so they moved
with the tests and need no edit.

- [ ] **Step 6: Run the suite to confirm the move broke no Python**

Run the moved suites only. The site exporters still join `skills/…` onto the
repository root and cannot find it, so `site/scripts/tests/` is expected to be
red until Step 7 — running everything here would bury the signal you want.

```bash
python3 -m pytest tests/ -q
```

Expected: **283 passed** — the 279 that `pytest skills/` reported before the
move, plus the four new package tests. A lower number means pytest stopped
discovering a directory; check that both `conftest.py` files landed.

For contrast, confirm the site suite is red for the reason you expect and no
other:

```bash
python3 -m pytest site/ -q 2>&1 | tail -3
```

Expected: failures naming a missing `skills/…` path, not import errors from
somewhere else.

- [ ] **Step 7: Add `PLUGIN_ROOT` to both exporters**

In `site/scripts/export_reference.py`, immediately after the `OUT_DIR` assignment:

```python
# The plugin runtime moved under plugin/ in STO-257 so that docs/, site/ and
# the pytest fixtures stop shipping to every install. REPO_ROOT still means
# the repository; everything the plugin owns hangs off PLUGIN_ROOT, so a
# future rename is one line.
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugin")
```

Then five joins change from `REPO_ROOT` to `PLUGIN_ROOT`:

```python
for _scripts_dir in (
    os.path.join(PLUGIN_ROOT, "skills", "design", "scripts"),
    os.path.join(PLUGIN_ROOT, "skills", "requirements", "scripts"),
):
```

```python
SCHEMAS = {
    "design": os.path.join(
        PLUGIN_ROOT, "skills", "design", "schema", "design.schema.json"
    ),
    "requirements": os.path.join(
        PLUGIN_ROOT, "skills", "requirements", "schema", "requirement.schema.json"
    ),
}
```

```python
    agents_dir = os.path.join(PLUGIN_ROOT, "agents")
```

And four **published strings** gain a literal prefix. These are emitted verbatim into `stages.json` and `pipeline.json` as the `skill` and `source` provenance fields and rendered on the site, and both are joined onto `REPO_ROOT` at read time — so the prefix goes in the string, and the join stays as it is:

```python
STAGE_SOURCES = {
    "requirements": {
        "skill": "plugin/skills/requirements/SKILL.md",
        "heading": "**Coverage areas:**",
    },
    "design": {
        "skill": "plugin/skills/design/SKILL.md",
        "heading": (
            "Six coverage areas the requirement set cannot carry, "
            "by construction:"
        ),
    },
}
```

```python
PIPELINE_SOURCES = {
    "requirements": "plugin/agents/requirements-orchestrator.md",
    "design": "plugin/agents/design-orchestrator.md",
}
```

In `site/scripts/export_examples.py`, add the same `PLUGIN_ROOT` line after `REPO_ROOT` and change its three joins:

```python
    os.path.join(PLUGIN_ROOT, "lib"),
    os.path.join(PLUGIN_ROOT, "skills", "design", "scripts"),
    os.path.join(PLUGIN_ROOT, "skills", "requirements", "scripts"),
```

`EXAMPLES_DIR` and the `os.path.relpath(path, REPO_ROOT)` at line 147 point at `docs/`, which stays at the repository root. Leave both alone.

- [ ] **Step 8: Regenerate and confirm what changed**

```bash
python3 site/scripts/export_reference.py
git diff --stat site/content/_generated/
git diff site/content/_generated/stages.json | head -20
```

Expected: `stages.json` and `pipeline.json` modified and nothing else. The diff is the `skill` and `source` provenance strings gaining their `plugin/` prefix. `agents.json`, `rules.json` and `fields.json` are unchanged — their content does not carry paths.

If `pipeline.json` shows changes to `critique_report`, you have run Task 2's edits early; that is fine but commit them separately.

- [ ] **Step 9: Split the two CLAUDE.md jobs**

`plugin/CLAUDE.md` moved in Step 3 and keeps its current text — it addresses a user's session and now reaches only users. Create a new contributor-facing `CLAUDE.md` at the repository root:

```markdown
# Groundwork

This repository builds the **groundwork** Claude Code plugin: SDLC discipline
workflows that put structure in front of code.

## Layout

`plugin/` is the published surface — the whole of it, and nothing outside it,
is copied into every install (`.claude-plugin/marketplace.json` points at it).
Adding a file there adds it to every user's download; `tests/test_plugin_package.py`
is what enforces the boundary.

Everything else is repository-only: `tests/` (pytest, with the fixtures that
used to ship), `site/` (the Nextra documentation site), `docs/` (specs, plans
and research), `assets/` (brand).

## Working here

- Python is stdlib-only, everywhere, including the site scripts.
- `site/content/_generated/` is committed and CI fails on drift. After editing
  a linter rule, either JSON Schema, an agent's frontmatter `description:`,
  either `SKILL.md`'s coverage list, or an orchestrator's stage headings or
  hand-off YAML, re-run `python3 site/scripts/export_reference.py`.
- `python3 -m pytest -q` runs everything from the repository root.
```

- [ ] **Step 10: Update the three stale path references**

`README.md`'s repo tree (around line 91) becomes:

```
groundwork/
├── .claude-plugin/       # Marketplace manifest — points at plugin/
├── plugin/               # Everything that ships to an install
│   ├── .claude-plugin/   # Plugin manifest
│   ├── skills/           # Markdown instruction sets (skill triggers)
│   ├── commands/         # Slash commands (/groundwork)
│   ├── hooks/            # Event-driven scripts (SessionStart)
│   ├── agents/           # Dispatched subagents
│   └── lib/              # Shared Python modules used by the linting/validation scripts
├── tests/                # Pytest suites and fixtures — repository-only
├── site/                 # Nextra documentation site, published to GitHub Pages
├── assets/               # Brand assets — the plumb-bob mark, icon and social preview
├── docs/                 # Internal planning docs (specs, plans, research) — not the published site
└── .github/              # CI and GitHub Pages deploy workflows
```

`plugin/skills/requirements/scripts/README.md:56` — `pytest skills/requirements/scripts/tests` becomes `pytest tests/requirements`.

`plugin/skills/design/scripts/README.md:122` — `pytest skills/design/scripts/tests` becomes `pytest tests/design`. Its line 20 cross-reference to `skills/requirements/scripts/README.md` becomes `plugin/skills/requirements/scripts/README.md`.

`site/scripts/tests/conftest.py:5` says "Mirrors the two conftests under `skills/`" — change `skills/` to `tests/`.

- [ ] **Step 11: Run everything**

```bash
python3 -m pytest -q
python3 site/scripts/export_reference.py --check && echo "reference clean"
python3 site/scripts/export_examples.py --check && echo "examples clean"
cd site && npm run build && cd ..
```

Expected: 348 passed (344 + the four new package tests), both gates clean, build exits 0.

- [ ] **Step 12: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(sto-257): move the plugin runtime under plugin/

Installing a Claude Code plugin copies the whole tree under the marketplace
entry's source, and there is no exclusion mechanism — no files, exclude or
ignore field exists in any plugin.json. The directory boundary IS the
manifest, so the fix is a directory boundary.

Before this, every install carried 4.7M: 2.1M of docs/, 1.1M of Nextra
source and 888K of pytest fixtures, against 532K of actual runtime. The
tests move out to a top-level tests/ for the same reason the docs stay put.

skills/ and lib/ move together on purpose. Every script walks ../../.. from
its own __file__ to find the shared core, so preserving their relative
positions is what makes this a pure move with no Python source changes.

tests/test_plugin_package.py turns the ticket's three prose acceptance
criteria into assertions, including one that copies the plugin elsewhere and
runs a validator from a working directory that is not a checkout — the check
that would have caught the path defect fixed in the next commit.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 2: Script paths that resolve from an installed plugin

**Files:**
- Modify: `plugin/skills/requirements/SKILL.md`, `plugin/skills/design/SKILL.md`
- Modify: `plugin/agents/requirements-orchestrator.md`, `plugin/agents/design-orchestrator.md`
- Modify: `plugin/agents/requirements-formatter.md`, `plugin/agents/design-formatter.md`
- Modify: `plugin/agents/requirements-critic.md`, `plugin/agents/design-critic.md`
- Modify: `tests/test_plugin_package.py` (append one check)
- Regenerate: `site/content/_generated/pipeline.json`

**Interfaces:**
- Consumes: `plugin/` and `tests/test_plugin_package.py` from Task 1.
- Produces: the `<skill-base>` placeholder convention, and `test_no_shipped_file_invokes_a_repo_relative_script_path` as a standing regression guard.

- [ ] **Step 1: Write the failing regression check**

Append to `tests/test_plugin_package.py`:

```python
def test_no_shipped_file_invokes_a_repo_relative_script_path():
    # A bare `python3 skills/...` resolves only when the working directory is
    # a groundwork checkout. For an installed plugin the working directory is
    # the user's own project, so the command fails with No such file. The
    # fix is the skill base directory the harness injects; this guards it.
    offenders = []
    for path in _shipped_paths():
        if not path.endswith(".md"):
            continue
        with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if "python3 skills/" in line or "python3 plugin/skills/" in line:
                    offenders.append(f"{path}:{number}")
    assert offenders == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_plugin_package.py -q -k repo_relative`
Expected: FAIL listing 10 offenders — 6 in the two `SKILL.md` files, 4 in `agents/`.

- [ ] **Step 3: Add the *Locating the scripts* section to both skills**

It goes **before the first phase** in each file, not beside the first command —
the design skill runs a script inside Phase 1, so anything later is too late.

In `plugin/skills/requirements/SKILL.md`, insert between `## When This Applies`
(line 10) and `## Phase 1: Detect Project Context` (line 26):

```markdown
## Locating the scripts

Every command below runs a script that ships with this plugin. Skill invocation
gives you this skill's base directory as an absolute path — the line reading
`Base directory for this skill: …`. The scripts are in `scripts/` beneath it.

Substitute that absolute path for `<skill-base>` in each command block before
running it, and substitute it **per block**: shell state does not persist
between tool calls, so a variable set in one command is gone by the next.

Do not "simplify" it to a repo-relative path. `skills/requirements/scripts/…`
resolves only when the working directory is a checkout of the groundwork
repository. For an installed plugin the working directory is the user's own
project, and the command fails with `No such file or directory`.
```

Insert the same section into `plugin/skills/design/SKILL.md`, between
`## When This Applies` (line 13) and `## Phase 1 — Locate and Read the Input`
(line 34), with one extra paragraph — its entry gate runs the *requirements*
validator from the sibling skill:

```markdown
The entry gate at Phase 1 runs the requirements stage's validator, which lives
in the sibling skill: `<skill-base>/../requirements/scripts/validate_requirements.py`.
Every other command here is under this skill's own `scripts/`.
```

- [ ] **Step 4: Rewrite the six command blocks**

`plugin/skills/requirements/SKILL.md`:

```bash
python3 <skill-base>/scripts/validate_requirements.py .sdlc/requirements
```

```bash
python3 <skill-base>/scripts/lint_requirements_content.py .sdlc/requirements
```

`plugin/skills/design/SKILL.md` — the entry gate first, then its own three:

```bash
python3 <skill-base>/../requirements/scripts/validate_requirements.py .sdlc/requirements
```

```bash
python3 <skill-base>/scripts/validate_design.py .sdlc/design
```

```bash
python3 <skill-base>/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements
```

```bash
python3 <skill-base>/scripts/lint_design_content.py .sdlc/design
```

Leave the `mkdir -p .sdlc/requirements/{...}` line above the first block
untouched — it is relative to the user's project, which is correct.

- [ ] **Step 5: Thread the path to the two formatters**

In `plugin/agents/requirements-orchestrator.md`, Stage 7, after the sentence
beginning "On a passing gate, hand the approved set to `requirements-formatter`":

```markdown
Include the absolute scripts directory the skill resolved in that dispatch. The
formatter shells out to `validate_requirements.py` as part of its own contract
and has no other way to locate it: an installed plugin's working directory is
the user's project, not a checkout of this repository.
```

In `plugin/agents/design-orchestrator.md`, Stage 10, after "Hand the approved
artifact set, the `design_context_artifact`, `draft_adrs`, and
`draft_diagram_model` to `design-formatter` — all four":

```markdown
Include the absolute scripts directory the skill resolved alongside them. The
formatter shells out to `generate_c4.py`, `validate_design.py` and
`validate_traceability.py`, and has no other way to locate any of the three.
```

- [ ] **Step 6: Make both formatters run at the dispatched path, and fail loudly without it**

In `plugin/agents/requirements-formatter.md`, replace the command at line 228
and add the clause below it:

```bash
python3 <scripts>/validate_requirements.py .sdlc/requirements
```

```markdown
`<scripts>` is the absolute scripts directory named in your dispatch. If your
dispatch did not name one, **stop and report that** rather than guessing a
relative path. A repo-relative path resolves only inside a groundwork checkout,
so the guess turns a locating failure into a confusing `No such file or
directory` at the exact moment you are supposed to be gating the write.
```

In `plugin/agents/design-formatter.md`, the same three commands become:

```bash
python3 <scripts>/generate_c4.py .sdlc/design \
```

```bash
python3 <scripts>/validate_design.py .sdlc/design
```

```bash
python3 <scripts>/validate_traceability.py .sdlc/design \
```

Keep each command's existing continuation lines and arguments exactly as they
are — only the path to the script changes. Add the same `<scripts>` paragraph
once, beneath the first of the three.

- [ ] **Step 7: Turn the four illustrative strings into shapes**

These are `command:` string *values* recording what was run, not commands to
execute. Two of them sit inside the published `critique_report` contract, so
this step is what regenerates `pipeline.json`.

`plugin/agents/requirements-critic.md:150` and
`plugin/agents/requirements-orchestrator.md:200`:

```yaml
    command: "python3 <scripts>/validate_requirements.py .sdlc/requirements"
```

`plugin/agents/design-critic.md:207` and
`plugin/agents/design-orchestrator.md:364`:

```yaml
    command: "python3 <scripts>/validate_design.py .sdlc/design"
```

Three prose mentions carry the same stale path and are corrected the same way:
`plugin/agents/requirements-critic.md:116`, `plugin/agents/design-critic.md:159`
and `plugin/agents/design-critic.md:262`.

- [ ] **Step 8: Run the guard and the suite**

```bash
python3 -m pytest -q
```

Expected: 349 passed, including `test_no_shipped_file_invokes_a_repo_relative_script_path`.

- [ ] **Step 9: Regenerate and inspect the contract diff**

```bash
python3 site/scripts/export_reference.py
git diff site/content/_generated/pipeline.json | grep '^[-+].*command' 
python3 site/scripts/export_reference.py --check && echo "GATE CLEAN"
```

Expected: exactly two changed `command:` lines, one per stage's
`critique_report.validator`, each losing its repo-relative literal for the
`<scripts>` shape. Then `GATE CLEAN`.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix(sto-257): resolve script paths from the skill, not from the repo root

Every script invocation in the skills was a bare repo-relative path, and none
of them has ever worked from an installed plugin: the working directory is
the user's project, where skills/ does not exist. Verified before fixing —
the documented command exits 2 with No such file, while the same script by
absolute path passes 21/21 from the same directory. The scripts were always
fine; only the paths in the prose were wrong.

Not fixed with ${CLAUDE_PLUGIN_ROOT}, which the ticket proposed. That
variable is expanded by the hooks runtime and is empty in the Bash tool's
shell, so a SKILL.md command using it resolves to /skills/... and points at
the filesystem root — a worse failure than the one being fixed, because it
looks like a path. The mechanism that exists is the skill base directory the
harness injects on invocation.

The two formatter agents shell out too, and they are dispatched rather than
invoked, so they have no base directory of their own. The orchestrator passes
the resolved directory in the dispatch it already sends. A formatter that is
not given one stops and says so instead of falling back: a silent fallback
turns a locating failure into a confusing No such file at the moment the
formatter is gating a write.

The critics' command: strings are records of what ran, not commands to run,
so they become shapes. Two sit inside the published critique_report contract,
which is why pipeline.json regenerates.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
```

---

### Task 3: The site's citations, verification, and the PR

**Files:**
- Modify: `site/content/architecture/{index,contracts,invariants,rationale}.mdx`

**Interfaces:**
- Consumes: everything from Tasks 1 and 2.

- [ ] **Step 1: Prefix the 18 plugin-path citations**

All 18 sit inside backticks and begin with `agents/`, `skills/` or `lib/`, so
the rewrite is mechanical. Assert the count before and after rather than
trusting the substitution:

```bash
before=$(grep -ohE '`(agents|skills|lib)/' site/content/architecture/*.mdx | wc -l)
echo "before: $before (expect 18)"
sed -i -E 's/`(agents|skills|lib)\//`plugin\/\1\//g' site/content/architecture/*.mdx
after=$(grep -ohE '`plugin/(agents|skills|lib)/' site/content/architecture/*.mdx | wc -l)
echo "after: $after (expect 18)"
grep -ohE '`(agents|skills|lib)/' site/content/architecture/*.mdx | wc -l
```

Expected: `before: 18`, `after: 18`, and `0` unprefixed left.

- [ ] **Step 2: Verify every citation resolves**

Nothing gates these, so check them by hand once, now:

```bash
grep -ohE '`plugin/[A-Za-z0-9_./-]+' site/content/architecture/*.mdx \
  | tr -d '`' | sed 's/:.*$//' | sort -u \
  | while read -r p; do [ -e "$p" ] || echo "MISSING: $p"; done
echo "(no MISSING lines above means every cited path exists)"
```

Expected: no `MISSING` lines. This checks paths, not line numbers — the
line-number half is what STO-263 would gate.

- [ ] **Step 3: Rebuild and confirm the pages still carry their generated rows**

```bash
cd site && npm run build
grep -q 'generation_brief' out/architecture/index.html && echo "MAP OK"
grep -q 'draft_interfaces' out/architecture/contracts/index.html && echo "CONTRACTS OK"
grep -q 'plugin/agents' out/architecture/invariants/index.html && echo "CITATIONS OK"
cd ..
```

Expected: all three print.

- [ ] **Step 4: Run the whole suite and every gate**

```bash
python3 -m pytest -q
python3 site/scripts/export_reference.py --check && echo "reference clean"
python3 site/scripts/export_examples.py --check && echo "examples clean"
```

Expected: 349 passed, both gates clean.

- [ ] **Step 5: Prove the package gate actually fails when it should**

A gate nobody has seen fail is a gate nobody knows works.

```bash
mkdir -p plugin/docs && echo "stray" > plugin/docs/notes.md && git add plugin/docs/notes.md
python3 -m pytest tests/test_plugin_package.py -q; echo "exit=$? (expected 1)"
git rm -q --cached plugin/docs/notes.md && rm -rf plugin/docs
python3 -m pytest tests/test_plugin_package.py -q && echo "restored, gate clean"
```

Expected: two failures naming the stray path (`test_plugin_ships_only_runtime_directories` and `test_no_documentation_site_or_fixtures_ship`), then clean. Confirm `git status` is clean before continuing.

- [ ] **Step 6: Re-verify the local dev marketplace by hand**

Not automatable — `known_marketplaces.json` points `groundwork-dev` at this
working directory as a `directory` source, which copies the tree literally.

Ask the user to reinstall the plugin from the local marketplace and confirm
that `/groundwork` still resolves and that the installed tree under
`~/.claude/plugins/cache/groundwork-dev/groundwork/<version>/` now contains
only the seven runtime entries. Report what they observe; do not assert it
from the working tree.

- [ ] **Step 7: Commit, push, and open the PR**

```bash
git add -A
git commit -m "$(cat <<'EOF'
docs(sto-257): repoint the architecture guide's 18 path citations

The invariants page is built almost entirely out of "here is the file that
enforces this", so a directory move invalidates fourteen of its citations at
once. Nothing gates them — a wrong path:line fails silently forever, which is
the rot the guide warns about, now aimed at the guide.

Checked by resolving every cited path against the filesystem once, by hand.
The line-number half stays unguarded; noted on STO-263, which owns the
docs-site drift gate.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E4ZBy7EtUuB3WehbBLXcn
EOF
)"
git push -u origin markdadamo/sto-257-plugin-subdirectory
```

Then open the PR titled
`refactor(sto-257): move the plugin runtime under plugin/ so docs and fixtures stop shipping`,
covering: the before/after sizes, the three ticket premises that did not
survive being run (spec E1–E3), the resolution mechanism and why
`${CLAUDE_PLUGIN_ROOT}` was rejected, and the new package gate with the
tamper test from Step 5. End the body with the PR trailer used on this
repository.

- [ ] **Step 8: File the STO-263 note and report CI**

Add a comment to STO-263 recording that the architecture pages carry
hand-written `path:line` citations with no gate, that STO-257 corrected 18 of
them by hand after a directory move, and that a test resolving each citation
to a real file and line would close it.

Then watch the run and report the result observed, not presumed. The
deployed-site checks cannot be asserted from a working tree and are confirmed
after merge, which is the standard passes 1–3 of STO-250 held themselves to.

---

## Self-Review

**Spec coverage.** D1 → Task 1 Steps 3–4. D2 → Task 1 Steps 3, 5. D3 → Task 1 Step 9. D4 → Task 1 Step 10 (README) and Task 1 Step 3 (the three root files are simply not moved). D5 → Task 2 Steps 3–7. D6 → Task 1 Step 7. D7 → Task 1 Step 1 and Task 2 Step 1, proven at Task 3 Step 5. D8 → Task 3 Steps 1–2 and Step 8. Evidence E1–E6 are all either encoded as a test or stated in a commit message. No spec section is unimplemented.

**Two deliberate refinements over the spec.** The spec's D7 lists three checks; the plan implements four, splitting "the shippable tree is only runtime" into an exact-set assertion on top-level entries and a substring guard on never-ship segments, because the two fail with very different messages. And it adds a fifth check in Task 2 — the repo-relative-path guard — which the spec did not name but which is the only automated hold on D5 surviving a future edit.

**One thing no task can cover, stated in the spec and repeated here.** Whether the model substitutes `<skill-base>` correctly at runtime is unreachable by test. The mitigation is Task 2 Step 6's fail-loud clause, and Task 3 Step 6's manual re-verification is the only end-to-end look at it.

**Count arithmetic.** 344 tests today; Task 1 adds four (348), Task 2 adds one (349). Every "Expected:" line uses those numbers. If the baseline has moved, the deltas are what matter.

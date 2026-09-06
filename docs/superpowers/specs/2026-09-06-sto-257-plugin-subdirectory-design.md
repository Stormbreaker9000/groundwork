# Plugin Subdirectory — Design

**Ticket:** STO-257
**Date:** 2026-09-06
**Status:** approved

## Problem

Installing a Claude Code plugin copies the entire tree under the marketplace
entry's `source`, minus `.git`. `.claude-plugin/marketplace.json` declares
`"source": "./"`, so the source is the repo root and every tracked file ships
to every user.

Measured against `main` at `5e0bd92`:

| What ships today | Size |
| --- | --- |
| Whole tracked tree | 4.7M |
| Actual plugin runtime | 532K |
| Not runtime | ~89% |

`docs/` is 2.1M of research, specs, plans and worked examples. `site/` is 1.1M
of Nextra source added by STO-250. `skills/*/scripts/tests/` is 888K of pytest
fixtures across 185 files. None of it runs.

STO-257 was filed before STO-250 landed and states the figure as 85% of 3.3M.
The three docs-site passes have since added `site/`, and the ticket records
that STO-250 "proceeds on the understanding that this one exists." STO-250 is
now Done, so the deferral has come due.

There is no exclusion mechanism. No `files`, `exclude`, or `ignore` field
exists in any `plugin.json` across the installed cache. The only lever is the
marketplace `source`, which is how Anthropic's own marketplace scopes its
third-party entries (`42crunch` → `plugins/api-security-testing`).

## Evidence

Everything below was verified by running it, not by reading.

### E1 — The scripts are already working-directory independent

Each script resolves `lib/` by walking `../../..` from its own `__file__` and
takes its target directory as an argument. Copying the runtime tree to a
scratch directory and invoking the validator **by absolute path** from an
unrelated working directory holding a requirement set:

```
$ cd /tmp/userproj && python3 /tmp/fakeinstall/skills/requirements/scripts/validate_requirements.py .sdlc/requirements
Summary: 21/21 file(s) passed, 0 failed, 0 error(s) total.
exit=0
```

So no Python source change is required by the move itself, provided `skills/`
and `lib/` move **together** — the relative walk is preserved by construction.

### E2 — The documented command is broken from an installed plugin

Every script invocation in the skills is a bare repo-relative path. Run
exactly as `skills/requirements/SKILL.md:224` writes it, from a user's
project rather than a checkout:

```
$ cd /tmp/userproj && python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements
python3: can't open file '/tmp/userproj/skills/requirements/scripts/validate_requirements.py': [Errno 2] No such file or directory
exit=2
```

This is a **pre-existing defect**, independent of the move. The move does not
cause it and does not fix it; it makes the wrong path one segment deeper.
STO-257's third acceptance criterion already demands the fix, so it is in
scope here.

### E3 — `${CLAUDE_PLUGIN_ROOT}` is not available to skill-invoked bash

The ticket proposes "the `${CLAUDE_PLUGIN_ROOT}` convention... should be used
rather than hand-patched relative paths." It cannot be. The variable is
expanded by the hooks runtime when launching a hook command — its single use
in this repository is `hooks/hooks.json:9` — and is empty in the Bash tool's
shell:

```
$ echo "CLAUDE_PLUGIN_ROOT=[${CLAUDE_PLUGIN_ROOT}]"
CLAUDE_PLUGIN_ROOT=[]
```

A SKILL.md command reading `python3 "${CLAUDE_PLUGIN_ROOT}/skills/…"` would
expand to `python3 "/skills/…"` — broken, and silently pointing at the
filesystem root. The mechanism that does exist is the skill base directory the
harness injects on invocation (`Base directory for this skill: <abs path>`),
which is how the superpowers plugin locates its own reference files.

### E4 — Shell state does not persist between Bash calls

Resolving the scripts directory once into a variable and reusing it across
later command blocks does not work: env vars set in one Bash call are gone by
the next. Each command block must carry the path itself.

### E5 — Only two agent files execute a script

Seven `python3 …/scripts/…` occurrences across `agents/`, of which:

- **Executed:** `design-formatter.md` (3), `requirements-formatter.md` (1).
- **Illustrative:** `design-critic.md:207`, `requirements-critic.md:150`,
  `design-orchestrator.md:364`, `requirements-orchestrator.md:200` — all four
  are a `command:` string *value* inside a YAML block, documenting the command
  the critic deliberately does not run.

Two of those four sit inside the published `critique_report` contract
(`validator.command`), so they are rendered on the site's contracts page as
though they were correct.

### E6 — The site carries 18 hand-written plugin-path citations

`site/content/architecture/invariants.mdx` (14), `index.mdx` (2),
`contracts.mdx` (1), `rationale.mdx` (1). Nothing gates them.

## Decisions

### D1 — `plugin/` holds the entire published surface

```
repo/
├── .claude-plugin/marketplace.json     "source": "./plugin"
├── plugin/                             532K — everything that ships
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/  commands/  hooks/  lib/
│   └── skills/{requirements,design}/{SKILL.md,schema/,scripts/}
├── tests/{requirements,design}/        888K — conftest.py, fixtures/, test_*.py
├── docs/  site/  assets/  .github/
└── README.md  CLAUDE.md  LICENSE  package.json  .gitignore
```

Every move is a `git mv`, so history follows the files. `skills/` and `lib/`
move together, which is what makes E1 hold.

### D2 — The test tree moves out of the plugin

`skills/*/scripts/tests/` → `tests/<stage>/`, mirroring the layout. Without
this the plugin ships at 1.4M, 888K of it pytest fixtures a user never runs;
with it, 532K.

The two `conftest.py` files repoint `SCRIPTS_DIR` from "my own parent
directory" to `<repo>/plugin/skills/<stage>/scripts`. Fixture paths are
resolved relative to the test file and move with it. `python3 -m pytest -q`
from the repo root still discovers `tests/` and `site/scripts/tests/`.

### D3 — Root `CLAUDE.md` is plugin-contributed context, and moves

Its text addresses a user's session — "The **groundwork** plugin is active…
Run `/groundwork`" — while also serving as this repository's own project
instructions. Today the whole repo ships, so it accidentally does both jobs.
After the split it moves to `plugin/CLAUDE.md` and keeps reaching users; the
repo gains a new contributor-facing `CLAUDE.md` in its place.

### D4 — Three root files stay and stop shipping

`assets/` (README banner, plus the SVG `GroundworkMark.jsx` inlines),
`package.json` (three keys, referenced by nothing in the plugin; the site has
its own), and `README.md`. Named explicitly because dropping them silently in
a move commit is how this kind of change goes wrong. `README.md:99` documents
the repo tree and is updated as part of the move.

### D5 — The scripts path is resolved by the skill and threaded to the formatter

Rejected: `${CLAUDE_PLUGIN_ROOT}` (E3), and a per-file "resolve the root
yourself" preamble in nine files — nine copies of one instruction is the drift
class STO-269 exists to track, and the formatters have nothing to derive the
root *from*.

The chosen mechanism, in four parts:

1. **Both `SKILL.md` files** gain a *Locating the scripts* section: skill
   invocation supplies this skill's base directory as an absolute path, the
   scripts live in `scripts/` beneath it, and every command block below shows a
   `<skill-base>/scripts/…` placeholder to substitute. Per E4 the placeholder
   is substituted per block; no variable is carried between calls. The reason
   is stated alongside the rule, because a bare instruction gets "corrected"
   by the next reader: a repo-relative path resolves only when the working
   directory is a groundwork checkout, and an installed plugin's working
   directory is the user's own project.

2. **Both orchestrators**, at Stage 7 / Stage 10, state that the dispatch to
   the formatter carries the absolute scripts directory the skill supplied.
   These dispatches are prose, not named YAML contracts — the block in each
   stage is the `formatter_result` the formatter *returns* — so no contract
   gains a field.

3. **Both formatters** run the validator at the path named in their dispatch
   and, **if it is absent, stop and report rather than falling back to a
   relative path.** This is the pipeline's "parsers raise, they never degrade
   silently" rule applied to an agent: a silent fallback produces a confusing
   `No such file` at the exact moment the formatter is gating a write.

4. **The four illustrative strings** (E5) become shapes rather than literals,
   including the two inside `critique_report.validator.command`.

### D6 — One `PLUGIN_ROOT` constant per exporter

`REPO_ROOT` in both site scripts stays the repo root; each gains
`PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugin")` and routes its plugin-facing
paths — twelve across the two files — through it, so there is one place to
change if the directory is ever renamed.

Four of the twelve are not joins but **published strings**:
`STAGE_SOURCES[…]["skill"]` and `PIPELINE_SOURCES[…]` are emitted verbatim
into `stages.json` and `pipeline.json` as the `skill` and `source` fields and
rendered on the site as provenance. They become `plugin/skills/…` and
`plugin/agents/…`.

### D7 — The acceptance criteria become a test

STO-257's criteria are three sentences no one can run. `tests/test_plugin_package.py`,
driven off `git ls-files plugin`, makes them enforceable:

1. **The shippable tree is only runtime.** `docs/`, `site/`, `tests/`,
   `assets/`, root `README.md` and `package.json` absent; `agents/`,
   `commands/`, `hooks/`, `lib/`, `skills/`, `.claude-plugin/plugin.json`
   present.
2. **No pytest fixtures ship.** No path under `plugin/` matches `tests/` or
   `fixtures/`.
3. **An installed copy runs its own validators.** Copy `plugin/` to a temp
   directory, `chdir` to a *different* temp directory holding a fixture
   artifact set, invoke the validator by absolute path, assert exit 0 — the
   E1/E2 experiment, automated.

Check 3 is the one that would have caught E2 at any point in the last four
months.

### D8 — The site's 18 citations are corrected, and the gap is recorded

The 18 references (E6) gain the `plugin/` prefix. Nothing gates them, and a
wrong `agents/foo.md:103` fails silently forever — the rot the architecture
guide warns about, now aimed at the guide.

A test asserting every `path:line` citation in the MDX resolves to a real file
would close it. That is STO-263's subject (docs-site drift gate hardening) and
is filed there as a comment rather than built here, because folding it in
grows this ticket past its own acceptance criteria.

## Files touched

**Moved (`git mv`, no content change):** `agents/`, `commands/`, `hooks/`,
`lib/`, `skills/` (minus tests), `.claude-plugin/plugin.json`, `CLAUDE.md` →
under `plugin/`. `skills/*/scripts/tests/` → `tests/<stage>/`.

**Edited:**

| File | Change |
| --- | --- |
| `.claude-plugin/marketplace.json` | `"source": "./plugin"` |
| `plugin/skills/{requirements,design}/SKILL.md` | *Locating the scripts* section; command blocks take the placeholder |
| `plugin/agents/{requirements,design}-orchestrator.md` | Stage 7 / Stage 10 dispatch carries the scripts directory; `critique_report.validator.command` example becomes a shape |
| `plugin/agents/{requirements,design}-formatter.md` | Run at the dispatched path; stop if absent |
| `plugin/agents/{requirements,design}-critic.md` | Illustrative `command:` becomes a shape |
| `tests/{requirements,design}/conftest.py` | `SCRIPTS_DIR` → `<repo>/plugin/skills/<stage>/scripts` |
| `site/scripts/export_reference.py` | `PLUGIN_ROOT`; five joins; four published strings |
| `site/scripts/export_examples.py` | `PLUGIN_ROOT`; three joins |
| `site/content/architecture/*.mdx` | 18 citations gain `plugin/` |
| `README.md` | Repo tree at :99 |
| `CLAUDE.md` (new, root) | Contributor-facing |

**Created:** `tests/test_plugin_package.py`.

**Regenerated:** `site/content/_generated/{pipeline,stages}.json` — via
`python3 site/scripts/export_reference.py`. Three independent reasons:
`critique_report.validator.command` in both stages, and the `source` / `skill`
provenance strings.

## Testing

| Property | How |
| --- | --- |
| Nothing but runtime ships | `test_plugin_package.py` checks 1–2, off `git ls-files plugin` |
| An installed plugin runs its validators | `test_plugin_package.py` check 3 — copy, foreign cwd, absolute path, exit 0 |
| The move broke no Python | `python3 -m pytest -q` from the repo root, unchanged pass count |
| Generated data matches its sources | `export_reference.py --check` and `export_examples.py --check` |
| The site still builds and renders | `npm run build`; the four existing CI greps |
| The local dev marketplace still installs | Manual re-check after the `source` repoint — `known_marketplaces.json` points `groundwork-dev` at this working directory as a `directory` source, which copies the tree literally |

## Out of scope

- **Whether the model substitutes `<skill-base>` correctly at runtime.** No
  test reaches it. The mitigation is D5.3's fail-loud clause.
- **A citation-resolution gate for the docs site.** D8 — filed on STO-263.
- **Renaming `_REPO_ROOT` inside the moved scripts.** It resolves to the plugin
  root after the move and the variable name becomes mildly inaccurate. A pure
  rename touching six files, deferred rather than mixed into a move commit.
- **The `requirements-analyst` orphan** (STO-270). It moves with the rest of
  `agents/` and is deleted or wired in under its own ticket.

## Known consequence

The published contracts page changes, and `pipeline.json` regenerates, in a
commit whose headline is a directory move. That is the exporter tax the
architecture guide documented last week arriving on schedule — it is working
as designed, and the drift gate will red the build if the regeneration is
forgotten.

# Worked Example DoD Regeneration and QA Set — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Republish both worked examples' Definition of Done from
`generate_dod.py` at the set root, and commit a tamagotchi QA set so the
complete three-stage form of the artifact is demonstrable in the docs.

**Architecture:** `site/scripts/export_examples.py` learns a third kind of
file — prose owned by the *set* rather than by one of its stages — and
publishes it as a page on the set's own index. The Definition of Done moves
out of `PROJECT_FILES["requirements"]` and becomes the first such file. A
second pass adds `qa` to the exporter's stage tables and regenerates the
tamagotchi DoD with `--qa`.

**Tech Stack:** Python 3 (stdlib only, everywhere — including the site
scripts), pytest, Nextra/MDX output consumed by GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-09-18-sto-309-example-dod-and-qa-set-design.md`

## Global Constraints

- **Python is stdlib-only**, including `site/scripts/`. No new dependency
  may be introduced by any task here.
- **`python3 -m pytest -q` runs from the repository root** and must stay
  green. Baseline on this branch is **457 passed**.
- **Two CI drift gates, not one.** `python3 site/scripts/export_reference.py --check`
  and `python3 site/scripts/export_examples.py --check` must both exit 0
  before any commit that touches `docs/requirements/examples/` or
  `site/`. Both are green at the branch point.
- **`export_examples.py` writes to `site/content/guide/examples/`.**
  `site/content/_generated/` belongs to `export_reference.py`; do not
  confuse them.
- **Example DoD titles are fixed strings:** `GDPR Data Export & Account
  Deletion` and `Tamagotchi Virtual Pet`, taken from the files being
  replaced.
- **Do not pass `--created-at`** (spec D6). Each file records the date it
  was really produced.
- **`plugin/` is the published surface.** No task here adds a file to it;
  `tests/test_plugin_package.py` enforces the boundary.

---

# PR 1 — The DoD path move

Tasks 1–4. Self-contained: touches no stage plumbing, fixes the live
defect. Land this before the PR 2 session.

---

### Task 1: Set-level project-file discovery

Pure addition. Nothing calls the new function yet, so both drift gates stay
green and no published page changes.

**Files:**
- Modify: `site/scripts/tests/test_export_examples.py` (append 3 tests to the existing 34-test module)
- Modify: `site/scripts/export_examples.py` (add after `PROJECT_FILES`, ~line 88; add function after `present_project_files`, ~line 438)

**Interfaces:**
- Consumes: `export_examples.EXAMPLES_DIR` (module-level absolute path; monkeypatched in tests)
- Produces: `SET_FILES: List[str]` and `present_set_files(set_name: str) -> List[str]`, used by Task 2

- [ ] **Step 1: Read the existing suite's conventions**

`site/scripts/tests/test_export_examples.py` already holds 34 tests for
this exporter, and `site/scripts/tests/conftest.py` already puts
`site/scripts/` on `sys.path`. No new directory and no new conftest — the
tests append to that module and follow its conventions, chief of which is
`import export_examples as ee`.

- [ ] **Step 2: Write the failing tests**

Append to `site/scripts/tests/test_export_examples.py`:

```python
"""Tests for the worked-example exporter's set-level file handling.

The exporter at large is gated by its own ``--check`` drift comparison in
CI, so these cover what that gate cannot: both committed example sets
carry a Definition of Done, so the drift comparison only ever exercises
the branch where a set-level file is present.
"""
def _set(tmp_path, name="widget"):
    """A minimal example set: a directory holding a ``requirements/``."""
    set_dir = tmp_path / name
    (set_dir / "requirements").mkdir(parents=True)
    return set_dir


def test_present_set_files_finds_the_definition_of_done(tmp_path, monkeypatch):
    set_dir = _set(tmp_path)
    (set_dir / "definition-of-done.md").write_text("# Definition of Done\n")
    monkeypatch.setattr(ee, "EXAMPLES_DIR", str(tmp_path))

    assert ee.present_set_files("widget") == [
        "definition-of-done.md"
    ]


def test_present_set_files_is_empty_when_no_set_level_prose_exists(
    tmp_path, monkeypatch
):
    """The branch the drift gate cannot reach.

    Both committed sets have a Definition of Done at their root, so only a
    third set — or a project that ran no stage — would hit this.
    """
    _set(tmp_path)
    monkeypatch.setattr(ee, "EXAMPLES_DIR", str(tmp_path))

    assert ee.present_set_files("widget") == []


def test_present_set_files_ignores_a_stage_level_copy(tmp_path, monkeypatch):
    """A ``definition-of-done.md`` under ``requirements/`` is not set-level.

    This is exactly the state STO-104 left behind and this ticket removes:
    the file at the superseded path must not be mistaken for the new one.
    """
    set_dir = _set(tmp_path)
    (set_dir / "requirements" / "definition-of-done.md").write_text("# Stale\n")
    monkeypatch.setattr(ee, "EXAMPLES_DIR", str(tmp_path))

    assert ee.present_set_files("widget") == []
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -v`
Expected: FAIL — `AttributeError: module 'export_examples' has no attribute 'present_set_files'`

- [ ] **Step 4: Add `SET_FILES` after `PROJECT_FILES`**

In `site/scripts/export_examples.py`, immediately after the `PROJECT_FILES`
dict (ends ~line 85), add:

```python
# Set-level project artifacts: prose the set owns rather than any one of its
# stages. generate_dod.py writes the Definition of Done to the root of the
# .sdlc/ tree because it is "the one artifact no single stage owns" — all
# three stage skills run the tool, and each run supersedes the last. The
# exporter mirrors that: these publish on the set's own index, not under a
# stage.
SET_FILES: List[str] = ["definition-of-done.md"]
```

- [ ] **Step 5: Add `present_set_files` after `present_project_files`**

```python
def present_set_files(set_name: str) -> List[str]:
    """The set-level prose files that exist, in reading order.

    Reads from disk for the same reason ``present_project_files`` does:
    which of them exist varies by set, and a list written down twice drifts
    from the set it describes.
    """
    root = os.path.join(EXAMPLES_DIR, set_name)
    return [
        name
        for name in SET_FILES
        if os.path.isfile(os.path.join(root, name))
    ]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -v`
Expected: PASS — the 3 new tests, and the 34 already in the module.

- [ ] **Step 7: Verify nothing else moved**

```bash
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: `460 passed`; both `--check` exit 0 (nothing calls the new
function yet, so no page changes).

- [ ] **Step 8: Commit**

```bash
git add site/scripts/tests/test_export_examples.py site/scripts/export_examples.py
git commit -m "$(cat <<'MSG'
feat(sto-309): set-level project files are a thing the exporter knows about

PROJECT_FILES is keyed by stage, and the Definition of Done stopped
belonging to one when STO-104 moved it to the root of the .sdlc/ tree.
present_set_files reads the set root the way present_project_files reads a
stage directory. Nothing calls it yet.

The tests join the exporter's existing suite and cover the branch the
drift gate cannot: both committed sets carry the file, so only its
absence needs a test.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 2: Publish set-level files as their own pages

Still no behaviour change on disk — both sets' roots are empty of prose
until Task 3 — so the drift gates stay green.

**Files:**
- Modify: `site/scripts/export_examples.py` (add `set_file_url` after `stage_url` ~line 267; add `render_set_file` after `render_project_artifacts` ~line 474; change `render_set_index` ~line 543; change `build_pages` ~line 634-645)
- Test: `site/scripts/tests/test_export_examples.py`

**Interfaces:**
- Consumes: `present_set_files(set_name)` and `SET_FILES` from Task 1; `_header(source)`, `split_frontmatter(text)`, `PROJECT_TITLES`, `_meta_js(entries)` (all pre-existing)
- Produces: `set_file_url(set_name: str, name: str) -> str`, `render_set_file(set_name: str, name: str) -> str`, and `render_set_index(set_name, summaries, set_files)` — note the **third positional parameter**, which Task 6 also calls

- [ ] **Step 1: Write the failing test**

Append to `site/scripts/tests/test_export_examples.py`:

```python
def test_render_set_file_keeps_the_documents_own_headings(
    tmp_path, monkeypatch
):
    """Set-level files are pages of their own, so nothing is demoted.

    A stage's project artifacts share one bucket page and are demoted under
    per-file H2s. A set-level file is published alone, so its own H1 is the
    page's H1.
    """
    set_dir = _set(tmp_path)
    (set_dir / "definition-of-done.md").write_text(
        "# Definition of Done\n\n## Acceptance gates\n\n- [ ] FR-001 `[CI]`\n"
    )
    monkeypatch.setattr(ee, "EXAMPLES_DIR", str(tmp_path))

    page = ee.render_set_file("widget", "definition-of-done.md")

    assert "# Definition of Done" in page
    assert "## Acceptance gates" in page
    assert "GENERATED FILE — do not edit." in page
    assert "docs/requirements/examples/widget/definition-of-done.md" in page


def test_set_file_url_drops_the_extension():
    assert (
        ee.set_file_url("widget", "definition-of-done.md")
        == "/guide/examples/widget/definition-of-done/"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -v`
Expected: FAIL — no attribute `render_set_file`.

- [ ] **Step 3: Add `set_file_url` after `stage_url`**

```python
def set_file_url(set_name: str, name: str) -> str:
    """Site-relative URL of one set-level page."""
    return f"/guide/examples/{set_name}/{os.path.splitext(name)[0]}/"
```

- [ ] **Step 4: Add `render_set_file` after `render_project_artifacts`**

```python
def render_set_file(set_name: str, name: str) -> str:
    """Render one set-level prose file as a page of its own.

    Stage-level project artifacts share a single bucket page; these do not.
    There is one of them, it is a document in its own right, and a sidebar
    entry reading "Definition of done" tells a reader what "Project
    artifacts" would not. Headings are left alone for the same reason — the
    file's own H1 is the page's H1, so there is nothing to demote.
    """
    path = os.path.join(EXAMPLES_DIR, set_name, name)
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    body = split_frontmatter(text).strip()
    header = _header(f"docs/requirements/examples/{set_name}/{name}")
    return "\n".join(header) + "\n" + body + "\n"
```

- [ ] **Step 5: Give `render_set_index` the set's files**

Change the signature and add the advertisement. The `for summary in
summaries:` loop is unchanged; insert the new loop between it and
`lines.append("")`:

```python
def render_set_index(
    set_name: str, summaries: List[StageSummary], set_files: List[str]
) -> str:
```

```python
    for name in set_files:
        lines.append(
            f"- **[{PROJECT_TITLES[name]}]({set_file_url(set_name, name)})**"
            " — projected from every stage above, and owned by none of "
            "them."
        )
    lines.append("")
```

- [ ] **Step 6: Wire it into `build_pages`**

Replace the `if summaries:` block at the end of the per-set loop with:

```python
        set_files = present_set_files(set_name)
        for name in set_files:
            slug = os.path.splitext(name)[0]
            pages[f"{set_name}/{slug}.md"] = render_set_file(set_name, name)

        if summaries:
            pages[f"{set_name}/index.md"] = render_set_index(
                set_name, summaries, set_files
            )
            pages[f"{set_name}/_meta.js"] = _meta_js(
                [("index", "Overview")]
                + [(s.stage, STAGE_TITLES[s.stage]) for s in summaries]
                + [
                    (os.path.splitext(name)[0], PROJECT_TITLES[name])
                    for name in set_files
                ]
            )
            set_entries.append(
                (set_name, SET_TITLES.get(set_name, set_name))
            )
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
python3 -m pytest site/scripts/tests/test_export_examples.py -v
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
```
Expected: the 2 new tests pass; `462 passed` overall; `--check`
exits 0 — no set root holds prose yet, so no page changed.

- [ ] **Step 8: Commit**

```bash
git add site/scripts/tests/test_export_examples.py site/scripts/export_examples.py
git commit -m "$(cat <<'MSG'
feat(sto-309): publish set-level files on the set's own index

One page per set-level file rather than a bucket: there is one of them, it
is a document in its own right, and a sidebar entry reading "Definition of
done" tells a reader what "Project artifacts" would not.

No output changes — neither set root holds prose until the next commit.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: Regenerate both Definition of Done files at the set root

The deliverable. This is the commit where published output changes.

**Files:**
- Create: `docs/requirements/examples/gdpr/definition-of-done.md` (generated)
- Create: `docs/requirements/examples/tamagotchi/definition-of-done.md` (generated)
- Delete: `docs/requirements/examples/gdpr/requirements/definition-of-done.md`
- Delete: `docs/requirements/examples/tamagotchi/requirements/definition-of-done.md`
- Modify: `site/scripts/export_examples.py` — `PROJECT_FILES` (~line 81) and both STO-104 deferral comments (~lines 78-80, ~415-416)
- Modify: `site/content/guide/examples/**` (regenerated, not hand-edited)

**Interfaces:**
- Consumes: `present_set_files` / `render_set_file` from Tasks 1–2
- Produces: two committed DoD files at the set roots, which Task 7 regenerates for tamagotchi

- [ ] **Step 1: Generate the gdpr Definition of Done**

```bash
python3 plugin/skills/requirements/scripts/generate_dod.py \
  --requirements docs/requirements/examples/gdpr/requirements \
  --out docs/requirements/examples/gdpr/definition-of-done.md \
  --title "GDPR Data Export & Account Deletion"
```
Expected: exit 0. gdpr has no design or QA stage, so no `--design` / `--qa`.

- [ ] **Step 2: Generate the tamagotchi Definition of Done**

```bash
python3 plugin/skills/requirements/scripts/generate_dod.py \
  --requirements docs/requirements/examples/tamagotchi/requirements \
  --design docs/requirements/examples/tamagotchi/design \
  --out docs/requirements/examples/tamagotchi/definition-of-done.md \
  --title "Tamagotchi Virtual Pet"
```
Expected: exit 0.

- [ ] **Step 3: Confirm the defect is gone and the QA sections are correctly absent**

```bash
grep -c 'M1 STUB\|dod-generator' \
  docs/requirements/examples/*/definition-of-done.md
grep -c 'Test Coverage\|Declared Unenforced' \
  docs/requirements/examples/*/definition-of-done.md
```
Expected: `0` for every file on both greps. The second is not a failure —
spec D3: those sections appear only once a QA stage has run, which is PR 2
and only for tamagotchi.

- [ ] **Step 4: Delete the superseded files**

```bash
git rm docs/requirements/examples/gdpr/requirements/definition-of-done.md \
       docs/requirements/examples/tamagotchi/requirements/definition-of-done.md
```

- [ ] **Step 5: Take `definition-of-done.md` out of `PROJECT_FILES`**

Replace the STO-104 deferral comment and the dict with:

```python
# Project-level artifacts: prose files with no artifact ID, published
# together on one page per stage. Order is reading order, not alphabetical.
# The Definition of Done is not among them — it belongs to the set, not to a
# stage, and SET_FILES carries it.
PROJECT_FILES: Dict[str, List[str]] = {
    "requirements": ["glossary.md", "assumptions.md"],
    "design": ["drivers.md", "assumptions.md"],
}
```

Then delete the second deferral comment above `PROJECT_TITLES` (the two
lines beginning `# See the STO-104 note above PROJECT_FILES:`). **Leave the
`"definition-of-done.md": "Definition of done"` entry in `PROJECT_TITLES`
itself** — `render_set_index` and the `_meta.js` builder both title the new
page from it.

- [ ] **Step 6: Update the pre-existing test that asserts the old layout**

`site/scripts/tests/test_export_examples.py` has a test asserting the
Definition of Done appears on the requirements stage's project-artifacts
page. Step 5 just removed it from there by design, so that test now fails —
correctly. Amend it to assert the new layout, and add one that pins where
the file went:

```python
def test_project_artifact_pages_carry_the_prose_files():
    page = ee.render_project_artifacts("tamagotchi", "requirements")
    assert "## Glossary" in page
    assert "## Assumptions" in page
    # The Definition of Done left this page in STO-309: it belongs to the
    # set, not to a stage, so it publishes on the set's own index.
    assert "## Definition of done" not in page


def test_definition_of_done_is_published_at_the_set_root():
    pages = ee.build_pages()
    assert "tamagotchi/definition-of-done.md" in pages
    assert "gdpr/definition-of-done.md" in pages
    assert "tamagotchi/requirements/definition-of-done.md" not in pages
```

One test amended and one added, so the suite goes to **463**, not 462. Use
463 in the next step and treat any other number as a real failure.

- [ ] **Step 7: Regenerate the site pages**

```bash
python3 site/scripts/export_examples.py
git status --short site/content/guide/examples/
```
Expected: `gdpr/definition-of-done.md` and `tamagotchi/definition-of-done.md`
added; both `index.md` and both `_meta.js` modified; both
`requirements/project-artifacts.md` modified (they lose a section).

- [ ] **Step 8: Verify every gate**

```bash
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: `463 passed`; both `--check` exit 0.

- [ ] **Step 9: Commit**

```bash
git add -A docs/requirements/examples/ site/scripts/export_examples.py \
          site/scripts/tests/test_export_examples.py \
          site/content/guide/examples/
git commit -m "$(cat <<'MSG'
feat(sto-309): regenerate both example DoDs at the set root

Both files were M1-stub output telling the reader to re-run the
dod-generator agent, which STO-104 deleted. The published guide has been
documenting a regeneration path that does not exist since that merged.

gdpr gets the requirements-only form and tamagotchi the requirements+design
form, which is the contrast: sections appear exactly when their stage has
run. The QA-dependent sections stay absent until a QA set exists.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 4: Update the prose that names the old path

**Files:**
- Modify: `docs/requirements/examples/tamagotchi/README.md:22,113`
- Modify: `docs/requirements/examples/REGENERATION.md:494-496,708-713`
- Modify: `docs/requirements/examples/gdpr/clarification-context.yaml:5`

**Interfaces:**
- Consumes: the committed layout from Task 3
- Produces: nothing other tasks read

- [ ] **Step 1: Fix the tamagotchi README**

At line 22, `definition-of-done.md` is listed among the *requirements*
stage's companion files. Remove it from that list, leaving
`assumptions.md`, `glossary.md`, and `index.yaml`. Then add a sibling
bullet after the `design/` bullet:

```markdown
- **[`definition-of-done.md`](./definition-of-done.md)** — the acceptance
  gates projected from every stage above by `generate_dod.py`. It sits at
  the set root rather than under a stage because no single stage owns it;
  each stage that runs supersedes the last one's output.
```

At line 113, the bullet begins "A generated `definition-of-done.md`
deriving an acceptance gate per functional requirement and a fitness gate
per NFR." Leave the claim, drop any implication that it lives under
`requirements/`.

- [ ] **Step 2: Fix REGENERATION.md**

At 494-496, the paragraph lists the companion files both M1 sets now carry
and names `definition-of-done.md` among them. Reword so the shared
companions are `assumptions.md`, `glossary.md` and `index.yaml`, and note
the Definition of Done now sits at each set's root.

At 708-713, the bullet says both files "want a `generate_dod.py` re-run in a
later pass, writing to the root-level `.sdlc/definition-of-done.md`".
That pass is this ticket. Rewrite it in the past tense as resolved, and
**keep** the note that `traces_to.tests` is empty on every `must` item —
that is still true and is not a regression (spec, Known consequences).

- [ ] **Step 3: Fix the gdpr clarification-context header only**

Line 5 lists where the recorded values are traceable to, including
`requirements/definition-of-done.md`. Change that one path to
`definition-of-done.md`.

**Do not touch line 71.** It sits inside the recorded
`clarification_context` — a replayed interview transcript. Editing what an
interview recorded to keep a path current falsifies the record (spec D8).

- [ ] **Step 4: Verify**

```bash
grep -rn 'requirements/definition-of-done' docs/requirements/examples/
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: the only surviving hit is `gdpr/clarification-context.yaml:71`,
which is deliberate. `463 passed`; both `--check` exit 0. The READMEs and
REGENERATION.md are in `EXCLUDED`, so no page is regenerated by this task.

- [ ] **Step 5: Commit and open the PR**

```bash
git add docs/requirements/examples/
git commit -m "$(cat <<'MSG'
docs(sto-309): the prose follows the Definition of Done to the set root

REGENERATION.md's note asking for this re-run is resolved; its separate
warning that traces_to.tests is empty on every must item stays, because a
QA set adds strategy items and not test code.

gdpr/clarification-context.yaml's header comment is updated and its
recorded body is not — editing what an interview recorded to keep a path
current would falsify the record.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
git push -u origin markdadamo/sto-309-regenerate-the-worked-examples-against-the-new-dod-generator
```

Then open the PR. Stop here and hand back — PR 2 is a separate session.

---

# PR 2 — The tamagotchi QA set

Tasks 5–8. **Task 5 is interactive and needs the repository owner present**
(spec D5). Do not start it unattended.

---

### Task 5: Run the QA stage against the tamagotchi set

**Files:**
- Create: a scratch tree outside the repository (spec D4) — use the session
  scratchpad directory, never `/tmp` directly and never the working tree

**Interfaces:**
- Consumes: the committed `docs/requirements/examples/tamagotchi/{requirements,design}/`
- Produces: `strategy/TS-*.md`, `qa-strategy.md` and `index.yaml` in scratch, which Task 6 swaps in

- [ ] **Step 1: Stage the inputs where the skill expects them**

The QA skill reads `.sdlc/requirements/` and `.sdlc/design/`. Build a
scratch `.sdlc/` whose stage directories are copies of the committed
example set:

```bash
# Set SCRATCH to a directory inside THIS session's scratchpad directory —
# the path is session-specific, so substitute the one this session was
# given. Not /tmp directly, and never the working tree.
SCRATCH="<this-session-scratchpad>/tamagotchi-qa"
mkdir -p "$SCRATCH/.sdlc"
cp -r docs/requirements/examples/tamagotchi/requirements "$SCRATCH/.sdlc/"
cp -r docs/requirements/examples/tamagotchi/design "$SCRATCH/.sdlc/"
echo "$SCRATCH"
```

- [ ] **Step 2: Run the QA skill against it**

Invoke `/groundwork:qa` with that `.sdlc/` as the project root.

The **repository owner answers Phase 3** — test tooling, CI enforcement
capability, coverage targets, and `declined_coverage` — and confirms the
Phase 4 `qa_context` synthesis. That confirmation is a hard stop in the
skill; nothing downstream runs without it.

- [ ] **Step 3: Review the emitted set as a delta, before swapping**

Read what the pipeline wrote. Check, without correcting by hand:

- Every `TS-` item carries a `verification_mode`, and a `test_level` exactly
  when that mode is `test` (STO-307 D7).
- `qa-strategy.md` carries its required headings plus Accepted Risks.
- `index.yaml` exists and lists every item.
- `enforcement: none` items reached the accepted-risk register, and are
  **not** sourced from `declined_coverage` (commit `583e5aa`).

A finding here is a finding about the pipeline worth recording, not a
result to force by hand (spec D9).

- [ ] **Step 4: No commit**

Nothing enters the repository in this task. Hand the scratch path to Task 6.

---

### Task 6: Swap the set in and teach the exporter the `qa` stage

**Files:**
- Create: `docs/requirements/examples/tamagotchi/qa/` (from Task 5's scratch)
- Modify: `site/scripts/export_examples.py` — `GROUPS` (~line 64), `STAGE_TITLES` (~line 410), the stage loop (~line 594)
- Test: `site/scripts/tests/test_export_examples.py`

**Interfaces:**
- Consumes: Task 5's reviewed scratch set; `render_set_index(set_name, summaries, set_files)` from Task 2 — three positional parameters
- Produces: a published `qa` stage, which Task 7's DoD run reads from disk

- [ ] **Step 1: Write the failing test**

```python
def test_qa_is_a_published_stage():
    """The stage loop and both title tables agree on three stages.

    A committed qa/ directory publishes nothing at all unless GROUPS,
    STAGE_TITLES and the loop in build_pages each carry a qa entry, and a
    set that has one of the three but not the others fails silently by
    emitting no page.
    """
    assert "qa" in ee.STAGE_TITLES
    assert any(stage == "qa" for stage, _d, _t in ee.GROUPS)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -v -k qa`
Expected: FAIL — `assert 'qa' in {...}`.

- [ ] **Step 3: Add the three `qa` entries**

Append to `GROUPS`:

```python
    ("qa", "strategy", "Test strategy"),
```

Add to `STAGE_TITLES`:

```python
    "qa": "QA",
```

Change the stage loop at ~line 594:

```python
        for stage in ("requirements", "design", "qa"):
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python3 -m pytest site/scripts/tests/test_export_examples.py -v`
Expected: PASS — the new qa test included.

- [ ] **Step 5: Swap the reviewed set in**

```bash
cp -r "$SCRATCH/.sdlc/qa" docs/requirements/examples/tamagotchi/qa
```

- [ ] **Step 6: Gate the swapped-in set**

```bash
python3 plugin/skills/qa/scripts/validate_qa.py \
  docs/requirements/examples/tamagotchi/qa

python3 plugin/skills/design/scripts/validate_traceability.py \
  docs/requirements/examples/tamagotchi/design \
  --requirements docs/requirements/examples/tamagotchi/requirements \
  --qa docs/requirements/examples/tamagotchi/qa
```
Expected: both exit 0.

`validate_traceability.py` lives under `design/scripts/`, not `qa/scripts/`
— it takes the design directory positionally and reaches the other two
stages through flags. Without `--qa` it skips every QA rule silently, which
would pass while checking nothing.

- [ ] **Step 7: Regenerate and verify**

```bash
python3 site/scripts/export_examples.py
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: `464 passed`; both `--check` exit 0; new pages under
`site/content/guide/examples/tamagotchi/qa/`.

- [ ] **Step 8: Commit**

```bash
git add -A docs/requirements/examples/tamagotchi/qa/ \
          site/scripts/export_examples.py site/scripts/tests/ \
          site/content/guide/examples/
git commit -m "$(cat <<'MSG'
feat(sto-309): commit the tamagotchi QA set and publish the qa stage

Generated by running /groundwork:qa against the committed requirements and
design sets, with the interview answered by hand — scratch-generated,
reviewed as a delta, then swapped in, so main never held a half-migrated
set.

The exporter's stage loop was hardcoded to two stages, so a committed qa/
directory published nothing until GROUPS, STAGE_TITLES and the loop each
grew an entry.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 7: Regenerate the tamagotchi DoD with `--qa`

The payoff: the run that finally renders the QA-dependent sections.

**Files:**
- Modify: `docs/requirements/examples/tamagotchi/definition-of-done.md` (regenerated)
- Modify: `site/content/guide/examples/tamagotchi/definition-of-done.md` (regenerated)

**Interfaces:**
- Consumes: the committed `qa/` from Task 6
- Produces: the complete three-stage DoD, which Task 8 describes

- [ ] **Step 1: Regenerate with all three stages**

```bash
python3 plugin/skills/requirements/scripts/generate_dod.py \
  --requirements docs/requirements/examples/tamagotchi/requirements \
  --design docs/requirements/examples/tamagotchi/design \
  --qa docs/requirements/examples/tamagotchi/qa \
  --out docs/requirements/examples/tamagotchi/definition-of-done.md \
  --title "Tamagotchi Virtual Pet"
```
Expected: exit 0.

- [ ] **Step 2: Confirm the ticket's acceptance property**

```bash
grep -c '## Test Coverage' docs/requirements/examples/tamagotchi/definition-of-done.md
grep -c '## Declared Unenforced' docs/requirements/examples/tamagotchi/definition-of-done.md
grep -c '\[CI\]' docs/requirements/examples/tamagotchi/definition-of-done.md
grep -c '\[manual\]' docs/requirements/examples/tamagotchi/definition-of-done.md
```
Expected: `1`, `1`, and at least `1` for each annotation. This is the
acceptance property the whole ticket exists for.

`## Declared Unenforced` renders only if the run produced unenforced items.
If it is absent because the interview declined nothing and every item is
CI-enforced, that is a true result — record it in Task 8 rather than
forcing it.

- [ ] **Step 3: Confirm gdpr did not move**

```bash
git status --short docs/requirements/examples/gdpr/
```
Expected: empty. gdpr stays requirements-only (spec D3).

- [ ] **Step 4: Regenerate and verify**

```bash
python3 site/scripts/export_examples.py
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: `464 passed`; both `--check` exit 0.

- [ ] **Step 5: Commit**

```bash
git add docs/requirements/examples/tamagotchi/definition-of-done.md \
        site/content/guide/examples/
git commit -m "$(cat <<'MSG'
feat(sto-309): the complete Definition of Done, with its QA sections

The third --qa run renders Test Coverage, Declared Unenforced and the
[CI]/[manual] enforcement annotations — the sections that exist only once
a test strategy does, and that no committed example has demonstrated.

gdpr keeps the requirements-only form on purpose. The contrast is the
teaching: sections appear exactly when their stage has run.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 8: Describe the QA set in the example prose

**Files:**
- Modify: `docs/requirements/examples/tamagotchi/README.md`
- Modify: `docs/requirements/examples/REGENERATION.md`

**Interfaces:**
- Consumes: everything committed in Tasks 5–7
- Produces: nothing

- [ ] **Step 1: Add the `qa/` bullet to the tamagotchi README**

After the `design/` bullet, matching its shape — name the directory, its
item count, and what it holds:

```markdown
- **[`qa/`](./qa/)** — the test strategy generated from those requirements
  and that design: N atomic `TS-` items under `strategy/`, the projected
  `qa-strategy.md`, and a machine `index.yaml`.
```

Replace `N` with the real count from
`ls docs/requirements/examples/tamagotchi/qa/strategy | wc -l`. Also update
the Definition of Done bullet added in Task 4 to say it now projects all
three stages.

- [ ] **Step 2: Record the run in REGENERATION.md**

Add a section covering: that the QA set was generated by a real interactive
run with the interview answered by hand; the `qa_context` answers that
shaped it; anything Task 5 Step 3 found about the pipeline; and — if it
came out that way — that `## Declared Unenforced` is absent because nothing
was declined.

- [ ] **Step 3: Verify**

```bash
python3 -m pytest -q
python3 site/scripts/export_examples.py --check
python3 site/scripts/export_reference.py --check
```
Expected: `464 passed`; both `--check` exit 0.

- [ ] **Step 4: Commit and push**

```bash
git add docs/requirements/examples/
git commit -m "$(cat <<'MSG'
docs(sto-309): describe the QA set in the example prose

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
)"
git push
```

---

## Acceptance

Acceptance is by property, not by count (spec, Testing; STO-219 D6):

1. Neither DoD names an agent the plugin does not ship —
   `grep -rc 'dod-generator\|M1 STUB' docs/requirements/examples/*/definition-of-done.md`
   is `0` for both.
2. Neither DoD sits under `requirements/`.
3. The tamagotchi DoD carries `## Test Coverage` and at least one `[CI]`
   and one `[manual]` annotation.
4. gdpr demonstrates the requirements-only form.
5. `python3 -m pytest -q` is green; both `--check` gates exit 0.

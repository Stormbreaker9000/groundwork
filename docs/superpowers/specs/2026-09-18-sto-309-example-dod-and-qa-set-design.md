# Worked Example DoD Regeneration and QA Set — Design

**Ticket:** STO-309 — Regenerate the worked examples against the new DoD
generator, and commit a QA set so the complete form is demonstrable. Its
one sequencing blocker, STO-307, merged as `bd5ddaf`.

## Problem

`docs/requirements/examples/` holds the two sets the plugin teaches from,
and the docs site publishes both. Since STO-104 replaced the M1
`dod-generator` agent with `generate_dod.py` and moved the generated
Definition of Done from `.sdlc/requirements/definition-of-done.md` to the
root-level `.sdlc/definition-of-done.md`, both sets have carried a
Definition of Done the pipeline can no longer produce.

The published guide currently instructs the reader to regenerate by
running an agent that does not ship. That is the live defect, and it is
independent of everything else in this ticket.

Underneath it sits a second, slower problem. `generate_dod.py` emits each
section exactly when its input exists, so `## Test Coverage`,
`## Declared Unenforced` and the `[CI]` / `[manual]` enforcement
annotations appear only for a project that has run the QA stage. Neither
committed set has a `qa/` directory, so the complete form of the
artifact — the form STO-103 and STO-307 exist to produce — is
undemonstrated in the published docs.

## Evidence

### E1 — Both DoD files are M1-stub output at the superseded path

`docs/requirements/examples/{gdpr,tamagotchi}/requirements/definition-of-done.md`
both open with an `M1 STUB` banner, cite `**M3 (STO-104)**` as future
work, and close the header by telling the reader to regenerate via the
`dod-generator` agent. `plugin/` ships no such agent; STO-104 deleted
`plugin/agents/dod-generator.md` and
`plugin/skills/requirements/templates/definition-of-done.md`.

### E2 — `PROJECT_FILES` is keyed by stage, and the DoD is stage-less

`site/scripts/export_examples.py:82` maps a stage name to its
project-level prose files. The ticket's step 4 says to move the two
`definition-of-done.md` entries "to the new location", but the new
location is the set root, and the exporter has no representation for a
file that belongs to a set rather than to one of its stages.

This is not incidental. `generate_dod.py`'s module docstring argues the
root path deliberately: the DoD is "the one artifact no single stage
owns", and all three stage skills run the tool with each run superseding
the last. An exporter that can only publish stage-owned prose cannot
express that.

### E3 — The export loop is hardcoded to two stages

`site/scripts/export_examples.py:594` reads
`for stage in ("requirements", "design"):`, and `STAGE_TITLES` carries
only those two keys. `GROUPS` likewise has no `qa` row. A committed
tamagotchi `qa/` directory would publish nothing at all until each of
those three grows a `qa` entry.

### E4 — Both exporters are CI gates; the ticket names one

`.github/workflows/ci.yml:32,35` and `pages.yml:56,59` each run
`export_reference.py --check` *and* `export_examples.py --check`. The
ticket's step 5 names only the former, which is the script that does not
touch the examples. Both currently exit 0, so the branch starts from a
clean baseline and any drift introduced here is attributable.

### E5 — Three further files reference the old path

`tamagotchi/README.md:22,113`, `REGENERATION.md:494-496,712` and
`gdpr/clarification-context.yaml:5,71` all name the DoD at its
requirements-level path. `REGENERATION.md:712` already anticipates this
ticket, noting both files "want a `generate_dod.py` re-run in a later
pass, writing to the root-level `.sdlc/definition-of-done.md`".

### E6 — Neither set has a `qa/` directory

STO-103 ran the QA stage end to end against the tamagotchi set, but the
run was not kept — only its findings were, as STO-307. Regenerating today
therefore yields the requirements-only form for gdpr and the
requirements+design form for tamagotchi, and exercises none of the
QA-dependent sections.

### E7 — The site scripts' tests live outside tests/

The suite collects 457 tests; 69 of them live in `site/scripts/tests/`,
covering both exporters against the real committed sets, and the rest under
`tests/`. A set-level file's absence is not among them, because both
committed sets carry a Definition of Done.

## Decisions

### D1 — Set-level project files are a new exporter concept

`export_examples.py` gains a representation for prose that belongs to the
set rather than to a stage: discovered beside the stage directories,
rendered onto the set's own `index.md`, and titled from the same
`PROJECT_TITLES` map. The `definition-of-done.md` entry leaves
`PROJECT_FILES["requirements"]` and becomes the first set-level entry.

The alternative — parking the DoD under `requirements/` in the published
site while it lives at the set root on disk — was rejected. It would make
the docs contradict the layout they document, which is the defect this
ticket exists to remove, only moved one level down.

### D2 — The work splits into two PRs at the stage seam

**PR 1** moves the DoD: the D1 exporter change, both regenerated files,
the deleted originals, and the E5 reference updates. It touches no stage
plumbing and depends on nothing that does not already exist.

**PR 2** adds the stage: the generated tamagotchi QA set, the E3 exporter
entries, and the tamagotchi DoD re-run with `--qa`.

The split is not ceremonial. PR 1 fixes a live defect in the published
docs and can land immediately; PR 2 requires an interactive pipeline run
with a human answering the QA interview, which is a scheduled session
rather than a task. Holding the first behind the second would leave a
reference to a non-existent agent in the published guide for no gain.

The ticket warns that regenerating before the QA set means regenerating
twice. That warning costs one `generate_dod.py` invocation here, which is
deterministic and takes no judgement. It is the right trade against a day
of known-wrong documentation.

### D3 — gdpr stays requirements-only

Only tamagotchi gains a QA set. gdpr has no design stage and will not
acquire one in this ticket, so its DoD demonstrates the
requirements-only form — the shape a project gets from running
`/groundwork:requirements` and stopping there.

The contrast is the teaching, not a gap: the two sets together show that
sections appear exactly when their stage has run, which is the central
claim of `generate_dod.py`'s design and is otherwise only assertable in
prose.

### D4 — The QA set is scratch-generated, diffed, then swapped

PR 2 inherits STO-219 D4 verbatim. The QA stage generates into a scratch
directory outside the repository; the result is reviewed as a delta
before it is swapped into the example set and gated. A discarded run
costs nothing, and a committed-then-reverted one costs a window where
`main` holds a half-migrated set.

### D5 — A human answers the QA interview

The Phase 3 interview is answered by the repository owner, not
in-character by the agent from the committed `drivers.md` and ADRs. The
four things it elicits — test tooling, CI enforcement capability,
coverage targets, and `declined_coverage` — are carried by nothing
upstream, so any answer the agent supplied would be invention published
as reference material.

This is what makes the committed set reproducible by following the
documented instructions, which is precisely the property STO-219 was
filed to restore and which the "hand-author to match" alternative would
have surrendered again.

### D6 — The DoD files carry their true generation date

`--created-at` is not passed. Each file records the date it was actually
produced, and tamagotchi's shifts when PR 2's `--qa` run supersedes it.
The committed output is stable once written, so this introduces no drift.

### D7 — The new tests join the exporter's existing suite

Both committed sets will carry a DoD at the set root, so the drift gate
exercises only the present branch of D1's discovery. The absent branch —
a set with no set-level prose at all — would ship untested, and it is
the branch a third example set would hit first.

Three tests append to `site/scripts/tests/test_export_examples.py`; they
test the new discovery function deliberately narrowly, not the exporter at
large, whose drift comparison remains the gate it has always been.

### D8 — `clarification-context.yaml`'s header is updated; its body is not

Line 5 is a header comment describing where the set's files live, and it
is updated with the layout. The reference at line 71 sits inside the
recorded `clarification_context` — a replayed interview transcript.
Editing what an interview recorded would falsify the record to keep a
path current, and the record is the artifact's whole value.

### D9 — Deferred to the run, deliberately

Three outcomes are not pre-decided, because settling them before seeing
what the pipeline produces would be inventing the result:

- **The `qa_context` content.** It is whatever D5's interview yields.
- **The `TS-` item count and its level distribution.** A target set
  before the run would be a number to hit rather than a result.
- **The `[CI]` / `[manual]` split, and what lands in
  `## Declared Unenforced`.** These follow from the interview's
  enforcement answers and `declined_coverage`, which is exactly the
  seam STO-307 built and the thing this example exists to demonstrate.

## Files touched

**PR 1**

| Path | Change |
|---|---|
| `site/scripts/export_examples.py` | D1 set-level discovery; `definition-of-done.md` leaves `PROJECT_FILES["requirements"]`; both STO-104 deferral comments removed |
| `docs/requirements/examples/gdpr/definition-of-done.md` | New — `--requirements` only |
| `docs/requirements/examples/tamagotchi/definition-of-done.md` | New — `--requirements --design` |
| `docs/requirements/examples/{gdpr,tamagotchi}/requirements/definition-of-done.md` | Deleted |
| `docs/requirements/examples/tamagotchi/README.md` | Lines 22, 113 — path and generator |
| `docs/requirements/examples/REGENERATION.md` | Lines 494-496, 712 — path; the 712 note resolves |
| `docs/requirements/examples/gdpr/clarification-context.yaml` | Line 5 header only (D8) |
| `site/scripts/tests/test_export_examples.py` | 3 tests appended |
| `site/content/guide/examples/**` | Regenerated (`export_examples.py`'s output tree; `_generated/` belongs to `export_reference.py`) |

**PR 2**

| Path | Change |
|---|---|
| `docs/requirements/examples/tamagotchi/qa/` | New — `strategy/TS-*.md`, `qa-strategy.md`, `index.yaml` |
| `site/scripts/export_examples.py` | `qa` added to `GROUPS`, `STAGE_TITLES`, and the line-594 loop |
| `docs/requirements/examples/tamagotchi/definition-of-done.md` | Regenerated with `--qa` |
| `docs/requirements/examples/tamagotchi/README.md` | Describes the `qa/` directory |
| `docs/requirements/examples/REGENERATION.md` | Records the QA run and any divergence |
| `site/content/guide/examples/**` | Regenerated (`export_examples.py`'s output tree; `_generated/` belongs to `export_reference.py`) |

## Testing

- `python3 -m pytest -q` from the repository root — 460 tests pass (457
  baseline + 3 new set-level discovery tests); none may regress.
- `python3 site/scripts/export_reference.py --check` exits 0.
- `python3 site/scripts/export_examples.py --check` exits 0.
- `site/scripts/tests/test_export_examples.py` includes 3 tests covering D7's absent branch.
- PR 2 additionally: `validate_qa.py` and `validate_traceability.py` pass
  against the swapped-in set, as the `qa-formatter` re-runs them.

Acceptance is by property, not by count, matching STO-219 D6: neither
regenerated DoD names an agent the plugin does not ship, neither sits
under `requirements/`, and after PR 2 the tamagotchi file carries
`## Test Coverage`, `## Declared Unenforced`, and at least one `[CI]` and
one `[manual]` annotation.

## Out of scope

- **Generating a design or QA set for gdpr** (D3).
- **Writing test code for either example.** The QA stage produces test
  *strategy*; no example acquires a runnable suite here.
- **STO-264's consolidated read-view.** `CONSOLIDATED.md` stays stale
  and excluded from the export; this ticket does not become its
  replacement.
- **Re-running the requirements or design stages.** STO-219 regenerated
  both and nothing since has invalidated them.

## Known consequences

- **`traces_to.tests` stays empty on every `must` item, and
  `REGENERATION.md:708`'s "flagged as currently unmet" note survives.**
  A QA set adds `TS-` strategy items, not test code. The flag is honest
  output and must not be read as a regression introduced here.
- **tamagotchi's DoD is regenerated twice**, once per PR, and the second
  supersedes the first (D2, D6).

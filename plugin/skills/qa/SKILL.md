---
name: qa
description: Use when a validated requirement set and an approved architecture both exist and the user is ready to define how the system will be tested — guides a QA interview covering only what neither prior stage carries (test tooling, CI enforcement, and coverage targets and risk appetite), then runs a multi-agent generation pipeline that produces atomic test-strategy artifacts before any test code is written.
---

# QA

Turn an approved requirement set and architecture into a structured test
strategy through an interview that covers only what those two stages
deliberately cannot carry, followed by a multi-agent generation pipeline.
This is phase 3 of the groundwork SDLC workflow — it follows `requirements`
and `design`, and precedes implementation.

## When This Applies

Invoke when both `.sdlc/requirements/` and `.sdlc/design/` hold a validated
set and the user is ready to define the test strategy:
- "What should we test?"
- "Let's define the QA strategy"
- "Write the test plan"
- "How do we know this is covered?"

Do NOT invoke for:
- Questions or explanations
- Bug reports
- Requests to read, explore, or explain existing code
- A request for this when no requirement set exists yet — send the user to
  the `requirements` workflow first
- A request for this when a requirement set exists but no design set
  does — send the user to the `design` workflow first

**Do not write any test code at any point during this skill.** This skill
produces test-strategy artifacts only — `TS-` items describing what to test,
at what level, and why. Nothing under `.sdlc/qa/` is executable, and this
skill never writes a test file.

## Locating the scripts

Every command below runs a script that ships with this plugin. Skill
invocation gives you this skill's base directory as an absolute path — the
line reading `Base directory for this skill: …`. This skill's own scripts are
in `scripts/` beneath it (`validate_qa.py`).

Substitute that absolute path for `<skill-base>` in each command block before
running it, and substitute it **per block**: shell state does not persist
between tool calls, so a variable set in one command is gone by the next.

Do not "simplify" it to a repo-relative path. `skills/qa/scripts/…` resolves
only when the working directory is a checkout of the groundwork repository.
For an installed plugin the working directory is the user's own project, and
the command fails with `No such file or directory`.

This skill needs an addition neither `requirements` nor `design` does: it
runs **both sibling stages' validators**, because it is the first stage to
read both directories at once. Those scripts live in the sibling skills, not
here:
- `<skill-base>/../requirements/scripts/validate_requirements.py`
- `<skill-base>/../design/scripts/validate_design.py`
- `<skill-base>/../design/scripts/validate_traceability.py` — this is also
  where the cross-artifact traceability check lives; there is no separate
  copy under this skill's own `scripts/`.

When you dispatch to `qa-orchestrator`, include this skill's absolute
`scripts/` path (as `scripts_dir`) in the hand-off — it forwards it on to
`qa-formatter`, which shells out to `validate_qa.py` and
`validate_traceability.py` and has no other way to locate them.

## Phase 1 — Locate and Read the Input

Find `.sdlc/requirements/` and `.sdlc/design/`. Both must exist. Absent
either, stop and route to the stage that produces it — `requirements` if
neither exists, `design` if only the requirement set does. There is nothing
to strategize a test plan against otherwise.

Once both are present, run the entry gate — **three validators, not one**:

```bash
python3 <skill-base>/../requirements/scripts/validate_requirements.py .sdlc/requirements
```

```bash
python3 <skill-base>/../design/scripts/validate_design.py .sdlc/design
```

```bash
python3 <skill-base>/../design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements
```

The third validator is here, not optional, for a reason specific to this
stage: this is the first pass that is about to add a third set of edges to
the requirement↔design graph — `TS-` items tracing back into both. Starting
from a graph that is already broken means the new edges land on sand; a
`dangling-trace` or `misplaced-requirement-trace` the earlier two stages left
unresolved will silently corrupt this stage's own traceability the moment a
test-strategy item cites the ID on the wrong side of it.

A non-zero exit from any of the three stops the stage. Fix it, or send the
user back to the stage that owns the fix, before proceeding — see
`design/SKILL.md`'s Step 4 for how design-artifact versus requirement-artifact
findings from `validate_traceability.py` are routed differently; the same
routing applies here, since this skill never writes into either upstream
directory.

**This is a structural gate only.** A non-empty `review_queue` in either
stage's `index.yaml`, or a `still_open` entry in `design/assumptions.md`'s
`## Open Questions`, does **not** block — see Phase 3, where both are opened
with rather than treated as defects to clear first.

Once the gate passes, read:
- Every requirement file, plus `.sdlc/requirements/index.yaml`'s
  `review_queue`.
- Every design file (components, interfaces, ADRs), plus
  `.sdlc/design/index.yaml`'s `review_queue`, `drivers.md`'s
  `## Architecturally Significant Requirements` section, and
  `assumptions.md`'s `## Open Questions`.

Hold three things out of this read, for Phases 3–4:
- The **union** of both `review_queue`s (e.g. `NFR-002` from requirements,
  `CMP-013` from design) — this stage is two steps removed from
  `requirements`, so its own inherited review queue is the accumulation of
  both prior stages', not just the one immediately before it.
- Every `Q-` item in `design/assumptions.md`'s `## Open Questions`. Only
  still-open questions ever land there — `design-formatter.md` promotes a
  resolved one into a `drivers.md` tradeoff instead — so this list is already
  exactly the candidate set Phase 3 opens with.
- The ASR list from `drivers.md`, for grounding the hypothesis in Phase 2.

**If an existing codebase is present**, scan it the same bounded way
`requirements` and `design` do — 3–5 targeted files, not a full audit. Here
the target is the test setup specifically: a test-runner config
(`pytest.ini`/`pyproject.toml`'s `[tool.pytest]`, `jest.config.*`,
`vitest.config.*`), the `test`/`ci` script in `package.json` or equivalent,
an existing `tests/`/`spec/` directory's shape, and any CI workflow file
(`.github/workflows/*.yml` or equivalent). Stop once you have enough to form
a grounded hypothesis about tooling and CI in Phase 2.

## Phase 2 — Hypothesise

One message, one question — the same shape as M1's and M2's hypothesis
phase.

Propose:
- A candidate set of test levels (from `unit`, `integration`, `contract`,
  `e2e`, `performance`, `security`), grounded in the design set's interface
  count and shape.
- The two or three highest-risk areas, drawn from the NFR quality-attribute
  scenarios held from Phase 1 — a QAS with a demanding response measure or a
  severe failure consequence is exactly what a risk-based test strategy
  should name first.
- A guess at the existing test setup, from the bounded codebase scan.

Say explicitly that the runtime, stack, and deployment target are **not**
being re-asked here: the design interview already elicited them and wrote
them to disk as ADRs and `drivers.md`, and re-asking would be the same
mistake M2's Phase 3 already refuses to make with the requirement set. Cite
what you read from the ADRs directly (e.g. "since ADR-002 fixed the stack on
pytest + FastAPI, I'd guess...") rather than asking again.

Present as a single message and ask whether it matches.

## Phase 3 — QA Interview

**Open with the inherited open questions**, before the three coverage areas —
the same discipline `design/SKILL.md`'s Phase 3 uses for the requirements
stage's leftovers. Present each `Q-` item held from Phase 1, in order, and ask
whether this stage's answers resolve it:

*"Design left one question open: Q-4 — [statement]. Does anything about the
test strategy resolve it, or is it still open?"*

Record a disposition for every one — `resolved` (with the resolution stated)
or `still_open` — before moving to the coverage areas.

Three coverage areas neither prior stage carries:

1. **Test tooling and existing suite** — the framework in use, and any existing suite whose conventions new tests must match
2. **CI enforcement capability** — what the pipeline can actually run and fail on, which decides every item's `enforcement` value
3. **Coverage targets and risk appetite** — the targets the team holds itself to, and the areas it has decided not to test

**Why only three, not six.** The design interview already elicited runtime,
stack, deployment target, integration points, and operational and team
constraints, and those reach disk as ADRs and `drivers.md` — re-asking any of
that would be the same mistake this stage's Phase 2 already declines to make.
What remains unasked by construction is how testing itself is tooled,
enforced, and bounded — nothing upstream has a reason to carry that.

**Rules, matching both existing interviews:**
- **One question per message.**
- **Prefer 2–4 numbered options** where the answer space is enumerable
  (e.g. test levels, enforcement tiers). Reserve open-ended questions for
  genuinely open spaces such as "what would you rather not test."
- **Infer from the codebase where obvious.** If Phase 1's scan already shows
  a `pytest.ini` and a GitHub Actions job running `pytest --cov`, state the
  inference for areas 1 and 2 and ask only for confirmation.

**Phrase area 3's declining question to make declining easy** — ask "which of
these are you *not* going to test" rather than "what will you test and to
what percentage." An accepted risk recorded honestly is worth more than a
coverage number nobody believes; a target stated without also naming what it
excludes tends to be the latter. Record the answer verbatim as
`declined_coverage`, or "None declined" if the team declines nothing — it
becomes the seed of the accepted-risk register at Phase 5, and it is not
paraphrased away between here and there.

Proceed to Phase 4 once all three areas are covered (by answer or by
confident inference) and every inherited open question has a recorded
disposition.

## Phase 4 — `qa_context` Synthesis

Before dispatching the pipeline, synthesise everything elicited into a
structured context object. This confirms shared understanding and serves as
the direct input to the `qa-orchestrator`.

Render in-conversation:

```
**QA context:**

**Test tooling & existing suite:** ...
**CI enforcement:** ...
**Coverage targets:** ...
**Declined coverage:** ... (or "None declined")
**Inherited open questions:** [each Q-# with resolved / still open]
**Inherited review queue:** [requirement/design IDs, or "None"]
```

Ask: *"Does this capture the QA context correctly, or should I adjust
anything before generating the test strategy?"*

**Do not proceed to Phase 5 until the user confirms.** If corrections are
needed, update the context object and re-confirm. This is a hard stop, not a
formality — nothing downstream runs on an unconfirmed context.

## Phase 5 — Generate

The confirmed Phase 4 block serialises 1:1 to the `qa_context` the
`qa-orchestrator` consumes:

```yaml
qa_context:
  requirements_root: ".sdlc/requirements"
  design_root: ".sdlc/design"
  test_tooling: string            # framework in use, and any existing suite's conventions
  ci_enforcement: string          # what the pipeline can actually run and fail on
  coverage_targets: string        # the targets and risk appetite the team holds itself to
  declined_coverage: string       # what the team decided not to test, in their own words — or "None declined"
  inherited_open_questions:
    - id: Q-4                     # ID preserved from design/assumptions.md
      statement: string
      disposition: resolved | still_open
      resolution: string          # present only when resolved
  inherited_review_queue: [ NFR-002, CMP-013 ]
```

**Step 1 — Generate (multi-agent pipeline):**

Drive the pipeline through the agents under `agents/`, in this fixed order:

1. **qa-orchestrator** — reads the approved requirement and design sets once
   on everyone's behalf, allocates the shared `TS-` ID space split into two
   disjoint ranges, and dispatches a `generation_brief` to each specialist.
   Include the absolute `scripts/` path from "Locating the scripts" above as
   `scripts_dir` in this dispatch — the orchestrator threads it, unchanged,
   all the way to the formatter.
2. **functional-test-specialist** and **quality-attribute-test-specialist** —
   dispatched together; neither needs the other's output, so run them in
   parallel or in either order.
3. **qa-critic** — runs once, on the merged set from both specialists:
   per-item quality and an ASR-coverage check keyed to `drivers.md`'s
   architecturally-significant list. Returns `gate: pass` or `gate: fail`.
   It does not run `validate_qa.py` — nothing is on disk yet at this stage,
   and `qa-strategy.md`'s gated headings are not assembled until the
   formatter projects them, so the structural check belongs downstream.
4. **qa-formatter** — writes the atomic `TS-` files, projects
   `qa-strategy.md` from the approved set and the synthesised
   `qa_context_artifact`, writes `index.yaml` (mandatory, not optional),
   then re-runs
   `validate_qa.py` and `validate_traceability.py` against everything it just
   wrote — the pipeline's single structural gate. **Runs only on
   `gate: pass`.** Do not advance past the critic on a failing or partial
   gate — the orchestrator re-dispatches only the affected items back to the
   owning specialist (the one whose `id_block` range the item's ID came
   from) and re-runs the critic on the full set.

**Step 2 — Render in-conversation summary (before writing anything):**

```
## QA Strategy Summary: <Feature Name>

**Overview:** [2-3 sentences: what's being tested, and the shape of the strategy]

**Test Levels:**
- unit — <count> items
- integration — <count> items
- ...

**Items:**
- TS-001 <title> — <test_level> / <risk_level>: <one-line rationale>

**Accepted Risks:**
- <statement> (traces: <requirement/design ID>) — <rationale>, or "None"

**Assumptions & Dependencies:** [key A-#/D-# items, or "None identified"]
**Open Questions:** [Q-# items still open, or "None"]

**⚠️ Triage before sign-off — review these specifically:**
- **Low-confidence items:** [each `confidence: low` TS-ID with its one-line reason — or "None"]
- **Open questions:** the items listed under **Open Questions** above.

  These are the uncertain items; confirm or correct *these* rather than re-scanning the whole set. The same low-confidence list is persisted as `review_queue` in `index.yaml`.

**Next Step:** Implementation
```

Render **Accepted Risks** from `qa_context_artifact.accepted_risks` — every
entry the orchestrator assembled at Stage 6.5, from the critic's justified
`uncovered_asrs` plus `qa_context.declined_coverage` parsed into one entry
per distinct declined item. This is the one point in the pipeline where
"what we decided not to test" reaches a human before any file is written —
surfacing it here, rather than only in the written `qa-strategy.md`, means
the user can push back on an accepted risk before it is committed.

**Step 3 — Sign-off gate:**

Ask: *"Does this capture the test strategy accurately, or should we adjust
anything before I write the files?"*

**No files are written until the user confirms.** Corrections re-dispatch to
the owning specialist through the orchestrator — the one whose `id_block`
range the affected item's ID came from — then re-summarise. There is nothing
to edit directly at this point, because there are no files: this mirrors M1
and M2's invariant exactly and it is not relaxed here.

**Step 4 — Write, then validate (hard gate):**

On confirmation, run the formatter. It writes the `TS-` files, projects
`qa-strategy.md`, writes `index.yaml` (mandatory, not optional), then
immediately re-runs
the structural gate against everything it just wrote — the first point at
which structure *can* be checked, since nothing was on disk before now. The
critic's earlier `gate: pass` was judgment only; it never ran these
commands.

```bash
python3 <skill-base>/scripts/validate_qa.py .sdlc/qa
```

Then, only if that exits 0:

```bash
python3 <skill-base>/../design/scripts/validate_traceability.py .sdlc/design \
  --requirements .sdlc/requirements \
  --qa .sdlc/qa
```

Both MUST exit 0. If either exits non-zero, do not treat the write as done:
this re-opens the critique loop rather than being patched by hand — attach
the failing findings and re-dispatch the affected items to their owning
specialist, then re-run the critic and the formatter on the corrected set.
Exit 2 from the traceability check is an environment error (a missing
directory), not a traceability failure — report it as such and stop.

**Step 4b — Report traceability warnings:**

Read `formatter_result.traceability_rerun.warnings` (empty if the sweep was
clean) and surface them to the user before committing. An `uncovered-asr`
warning surviving here is not necessarily wrong — Stage 6.5 may already have
recorded it as an accepted risk — so report the warning and its disposition
together. Warnings are advisory and do not block the commit.

**Step 5 — Commit:**

```bash
git add .sdlc/qa/
git commit -m "docs: add test-strategy artifact set for <feature-name>"
```

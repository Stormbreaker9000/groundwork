# Design: M1 Content-Quality Linter + Assumptions Artifact

**Date:** 2026-07-10
**Tickets:** STO-136 (content-quality linter), STO-134 (Assumptions/Dependencies/Open Questions as first-class artifact sections)
**Milestone:** M1 — Foundation & Requirements Stage
**Closes:** Gap 6 content side, Gap 5 (from `docs/requirements/requirements_research_gap_analysis.md`)

## Context

The requirements generation pipeline already emits atomic Markdown+YAML requirement
files and gates them with a **structural** validator
(`skills/requirements/scripts/validate_requirements.py`, STO-97) — YAML schema +
cross-file checks (unique IDs, prefix↔type, dangling traces, FR `ears_pattern`
presence). The critic agent (STO-96) runs that validator as a hard gate and adds a
prompt-level "Gate C — Light anti-pattern flags," which explicitly defers *deep*
content linting to a later milestone.

Two High-priority M1 gaps remain:

- **STO-136** — the deferred deep content-quality linter (anti-pattern detection on
  requirement *prose*, distinct from the structural validator).
- **STO-134** — dedicated **Assumptions / Dependencies / Open Questions** artifact
  sections instead of burying these in requirement text.

This spec covers both. The two remaining Medium M1 tickets (STO-137 elicitation
quality, STO-138 confidence scoring) are lighter, prompt-level changes and are
specced separately.

## Part A — STO-136: content-quality linter (hybrid)

Hybrid approach: a **deterministic Python script** catches the mechanical
anti-patterns (matching the `validate_requirements.py` pattern — reproducible,
unit-tested); the **LLM critic** keeps the judgment calls (implementation-bias
nuance and suggested rewrites).

### New script: `skills/requirements/scripts/lint_requirements_content.py`

Reuses `discover_files` and `parse_frontmatter` from `validate_requirements.py`
(import, do not duplicate). Operates on the same atomic requirement files; skips
the same non-atomic files (`definition-of-done.md`, `index.yaml`, `assumptions.md`).

**Checks.** Each finding is `{rule, severity, req_id, field, excerpt, message,
suggested_rewrite_hint}`:

1. **Vague qualifiers** (`vague-qualifier`) — word list: fast, rapid, quick,
   user-friendly, easy, intuitive, seamless, efficient, robust, flexible,
   scalable, secure, reliable, minimize, maximize, optimize, approximately, as
   appropriate, TBD, etc. Scanned in `title` and `description`. Downgraded from
   `warn` to `info` when a number+unit appears in the same sentence (the qualifier
   is quantified).
2. **Compound requirement** (`compound`) — `and`/`or` joining verb phrases in the
   predicate after `shall`. `warn`. Excludes obvious noun-phrase conjunctions
   ("terms and conditions") by requiring a following verb.
3. **EARS conformance** (`ears-conformance`) — for FRs, the `description` text must
   contain `shall` and the leading keyword implied by its declared `ears_pattern`:
   ubiquitous → no leading condition; event → `When`; state → `While`; unwanted →
   `If … then`; optional → `Where`; complex → a combination. Mismatch → `warn`.
4. **Passive voice, nameless subject** (`passive-nameless`) — `shall be
   <participle>` with no `by <actor>` clause hides the responsible actor. `warn`.
5. **Implementation bias** (`impl-bias`) — light tech/UI keyword list (button,
   dropdown, click, page, screen, React, Postgres, REST endpoint, table, …)
   appearing inside a `tier: business` or `tier: stakeholder` requirement.
   `info` (the critic does the nuanced version).

**Severity + exit policy.** Advisory by default: always exits 0 and prints a
per-requirement report. `--strict` makes any `error`-severity finding exit
non-zero (none are `error` today; the flag is forward-looking and lets CI opt in).
`--json` emits structured findings for the critic agent to consume. `--quiet`
prints only findings + summary. The content linter is **not** a hard pipeline
gate — it feeds the critic's `revise` verdicts and the human reviewer.

**Tests.** `skills/requirements/scripts/tests/test_lint_content.py` with fixtures
under `tests/fixtures/content/`: a clean requirement that yields no findings, plus
one fixture per rule that yields exactly that finding. Mirrors the existing
`test_validate_requirements.py` structure.

### Wire-in

- **Critic agent** (`agents/requirements-critic.md`) — Gate C upgraded: run
  `lint_requirements_content.py --json` and fold its findings into
  `per_requirement.findings`; the critic still applies judgment for
  implementation-bias edge cases and authors suggested rewrites. Update the
  "deep content-quality linting is deferred" note.
- **SKILL.md** Phase 5 Step 4 — run the content linter (advisory) alongside the
  structural validator.
- **`scripts/README.md`** — document the new script, its flags, and exit behavior.

## Part B — STO-134: assumptions / dependencies / open-questions artifact

### New file: `.sdlc/requirements/assumptions.md`

Project-level, non-atomic (like `definition-of-done.md`). Three H2 sections in a
fixed order, each listing IDed items or the literal `None identified`:

```markdown
# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: <statement believed true without proof>

## Dependencies
- D-1: <external condition the project relies on>

## Open Questions
- Q-1: <unresolved item> (owner: <who follows up>)
```

### Ownership + data flow

- **Orchestrator** (`agents/requirements-orchestrator.md`) gains **Stage 6.5 —
  context synthesis**, producing a `context_artifact` object:
  - `open_questions` — derived from `clarification_context.open_questions`.
  - `assumptions` / `dependencies` — synthesized from the generated requirement set
    plus anything specialists surface.
- **Specialists** (`fr-`/`nfr-`/`constraint-specialist`) get an **optional**
  `assumptions` / `dependencies` array on their returned object, so an assumption a
  specialist relied on is captured rather than silently baked into prose. The
  orchestrator merges + dedupes; it is the single writer of artifact *content*.
- **Formatter** (`agents/requirements-formatter.md`) writes `assumptions.md` from
  the `context_artifact`, alongside the atomic files and `index.yaml`.

### Validation (hard gate — in the STO-97 structural validator)

- `validate_requirements.py` gains `check_context_artifact(reqs_dir)`: verifies
  `assumptions.md` exists at the requirements-dir root and contains all three
  required H2 headings (`## Assumptions`, `## Dependencies`, `## Open Questions`),
  even if a section reads `None identified`. Missing file or heading →
  set-level error → non-zero exit.
- Add `assumptions.md` to `SKIP_FILENAMES` so it is never parsed as a requirement.

This makes the artifact's *presence and structure* a hard gate, consistent with
STO-134 ("validated as present, even if empty"). Section *content* quality is not
gated here.

### Fixture + example updates (required to keep suites green)

- Add `assumptions.md` to `tests/fixtures/valid/` (the presence check would
  otherwise fail the existing valid fixture set).
- Add new invalid fixtures: `missing_context_artifact/` (no file) and
  `context_artifact_missing_heading/` (file present, one heading absent).
- Add `assumptions.md` to the GDPR example set under
  `docs/requirements/examples/`.

### Agent + skill doc updates

- Orchestrator — document Stage 6.5 and the `context_artifact` hand-off shape.
- Formatter — document writing `assumptions.md`.
- SKILL.md Phase 5 — list the assumptions artifact in the outputs and the
  in-conversation summary.

## Build order

1. **STO-136** — new `lint_requirements_content.py` + tests + critic/SKILL/README
   wire-in. Isolated; no change to the structural validator.
2. **STO-134** — `check_context_artifact` in the structural validator + tests +
   fixtures/example updates + orchestrator/formatter/SKILL doc changes.

TDD on both Python scripts (write failing tests first). Agent `.md` changes are
prose; verify by running the validator + content linter against the updated
example set and confirming clean/expected output.

## Out of scope

- STO-137 (elicitation quality) and STO-138 (confidence scoring) — separate specs.
- Content-quality *gating* (making anti-patterns block the pipeline) — advisory only.
- Machine-readable (YAML) assumptions format — human-readable Markdown only.

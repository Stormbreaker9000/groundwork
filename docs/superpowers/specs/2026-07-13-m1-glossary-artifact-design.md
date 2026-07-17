# Design: M1 Glossary Artifact

**Date:** 2026-07-13
**Tickets:** STO-135 (generate a glossary artifact — `glossary.md`)
**Milestone:** M1 — Foundation & Requirements Stage
**Closes:** the last open M1 gap — a shared vocabulary anchor for the requirements → architecture → QA hand-off

## Context

Groundwork's requirements pipeline hands artifacts across stages: M1 emits requirements,
M2 turns them into an architecture, M3 derives QA strategy and the Definition of Done.
Each hand-off is read by a fresh agent with no memory of the conversation that produced
the text. Without a shared vocabulary the stages drift — M1's "decay" becomes M2's
"degradation" becomes M3's "state reduction", and the traceability that the whole
pipeline exists to preserve quietly stops meaning anything.

STO-135 closes that gap with a `glossary.md` artifact emitted alongside the requirement
set: domain terms with definitions, written once and read by every downstream stage.

The pipeline already has the exact seam this needs. The orchestrator's **Stage 6.5**
synthesizes a `context_artifact` (assumptions / dependencies / open questions) from two
sources — the `clarification_context` and optional sibling `assumptions`/`dependencies`
fields the specialists return alongside their drafts — and the **formatter** writes it to
`.sdlc/requirements/assumptions.md`, whose presence and headings the structural validator
hard-gates (STO-134). Glossary terms surface in those same two places and are context
rather than requirements, so they ride the same seam rather than introducing a new one.

## Decisions

Four decisions shape the design; each was taken against a viable alternative.

**Presence is gated; content is not.** The validator requires `glossary.md` to exist with
its `## Terms` heading, but an empty section reading `None identified` passes — the same
honest-empty convention `assumptions.md` uses. The glossary's value is being *reliably
there* for M2/M3 to read, so presence must be guaranteed; but a project can legitimately
have little domain vocabulary, and forcing invented entries to satisfy a gate is worse
than an honest empty section.

**Entries are a dictionary, not a traceability surface.** An entry is a term, a
definition, and an optional alias clause. Entries do *not* carry `used_by` requirement
IDs. Backlinks would duplicate what the requirement files already own (every requirement
names its own terms), and would introduce a second class of dangling reference for the
formatter to reconcile and the validator to check. That is a real cost for a view that is
derivable by grep.

**Term *finding* is judgment, so it belongs to agents; term *auditing* is decidable, so
part of it belongs to a script.** The linter gets the direction of the check that a script
can actually decide — a defined term that no requirement uses (cheap, exact, and it
catches the specific way an LLM glossary goes wrong: padding it with plausible entries
nobody needed). The opposite direction — a requirement using a domain term the glossary
never defines — requires deciding what counts as a "domain term" in free prose, where any
heuristic fires on ordinary English and a noisy linter is one people learn to ignore.
That direction goes to the critic, which is already doing exactly this kind of judgment.

**No new agent.** A dedicated `glossary-specialist` would write better definitions by
seeing the final approved set rather than in-flight drafts — but that is an argument for a
better prompt, not a new pipeline stage. The pipeline's fixed agent ordering is its main
invariant; a whole stage for one small file is not worth perturbing it.

## Part A — Producing the glossary (agent contracts)

### Specialists — optional sibling `terms`

`fr-specialist`, `nfr-specialist`, and `constraint-specialist` may return a `terms` field
alongside the `assumptions` and `dependencies` siblings they can already return (Stage 5):

```yaml
terms:
  - term: Decay
    definition: The reduction of a pet's stat values over elapsed time, applied whether or not the app was running.
    aliases: [stat decay]        # optional
```

A specialist emits a term when it uses a word whose meaning is domain-specific and not
self-evident to a reader outside the conversation — the same bar it already applies to
surfacing an assumption. The field is optional and additive: a specialist returning no
`terms` remains valid. Terms are not written into requirement frontmatter.

### Orchestrator Stage 6.5 — merge and canonicalize

Stage 6.5 gains a `glossary` block on the `context_artifact`, assembled from the
`clarification_context` and the specialists' sibling `terms`:

```yaml
context_artifact:
  assumptions: [...]
  dependencies: [...]
  open_questions: [...]
  glossary:
    - term: Decay
      definition: ...
      aliases: [stat decay]
```

The orchestrator owns the merge, and this is where the design's real risk lives: each
specialist sees only its own slice, so two of them independently coining "stat decay" and
"hunger decay" for one concept is the expected failure, not an edge case. Stage 6.5 must:

- collapse terms that differ only in surface form (case, plural, word order) into one entry;
- collapse near-synonyms into a single canonical term, recording the losers as `aliases`;
- drop terms that are ordinary English rather than domain vocabulary (a glossary that
  defines "user" and "system" teaches a downstream agent nothing);
- sort entries alphabetically, so regenerated files diff cleanly.

### Formatter Stage 7 — write `glossary.md`

The formatter writes `.sdlc/requirements/glossary.md` from the `glossary` block, exactly as
it writes `assumptions.md` today, and reports it in `formatter_result` under a new
`glossary` key beside `context_artifact`. Like `assumptions.md`, this is a project-level
file, not an atomic requirement.

## Part B — The on-disk format

```markdown
# Glossary

## Terms
- **Decay**: the reduction of a pet's stat values over elapsed time, applied whether or not the app was running. *Also: stat decay.*
- **Neglect**: a sustained period during which the pet's needs go unmet, progressing toward sickness and death.
- **Quarantine**: the retention of an unreadable save file under a reserved name for diagnostics, rather than deleting it.
```

One H1; one `## Terms` H2; one bullet per term as `- **Term**: definition.`, with an
optional trailing `*Also: alias, alias.*` clause when a synonym genuinely exists. Terms
are sorted alphabetically. When a project has no domain vocabulary worth defining, the
section contains the single line `None identified`.

## Part C — Structural validator (hard gate)

`skills/requirements/scripts/validate_requirements.py`:

- Add `glossary.md` to `SKIP_FILENAMES` so it is never parsed as an atomic requirement.
- Gate its presence and its `## Terms` heading as a set-level check, exactly as
  `assumptions.md` is gated. A missing file or missing heading fails the set; a section
  reading `None identified` passes.

`check_context_artifact()` is currently hardcoded to one filename and one heading list.
Generalize it to a helper taking `(reqs_dir, filename, required_headings)` and call it
twice — once for `assumptions.md`, once for `glossary.md`. This keeps the non-UTF-8 read
handling added in STO-134 in one place rather than duplicating it, and is a targeted
cleanup in service of this change rather than unrelated refactoring.

## Part D — Content linter (advisory)

`skills/requirements/scripts/lint_requirements_content.py` currently exposes `CHECKS`, a
list of per-requirement callables `(req_id, frontmatter) -> [Finding]`, which `lint_dir`
runs over each file. The unused-term check is inherently **set-level** — a term is unused
only if *no* requirement uses it — so it cannot be a `CHECKS` entry. Add a set-level check
hook that `lint_dir` runs once after the per-file loop, and implement one check on it:

**`glossary-unused`** — parse the terms out of `glossary.md`; for each term, search the
`title`, `description`, `rationale`, and `fit_criterion` of every requirement in the set;
warn when neither the term nor any of its aliases appears anywhere.

- Severity `warn`, consistent with the linter's other findings — it guides, it does not block.
- Matching is case-insensitive and tolerant of ordinary inflection (`decay` matches
  `decays`/`decaying`), because the failure being hunted is *an invented entry nobody
  used*; being strict about word forms would fire false warnings on normal English.
- A `glossary.md` whose Terms section reads `None identified` yields no findings.

## Part E — Critic (judgment)

`requirements-critic` gains a glossary pass in its existing coverage phase: read
`glossary.md` against the approved requirement set and flag

- domain terms used in requirement text but never defined in the glossary;
- definitions that are circular or vacuous ("Decay: the process of decaying");
- entries that restate ordinary English rather than domain vocabulary.

These are advisory findings in the `critique_report`, not gate failures. This is the
undefined-term direction that was deliberately kept out of the linter: it is a judgment
about natural language, which is what the critic is for.

## Part F — Prerequisite: fix the examples layout

The examples tree currently holds **two independent requirement sets sharing one ID
space**. The GDPR set sits at the root of `docs/requirements/examples/`, and PR #6 nested
the tamagotchi set beneath it at `examples/tamagotchi/requirements/`. Each set validates
cleanly in isolation (GDPR 8/8, tamagotchi 22/22), but the validator walks recursively, so
pointing it at `docs/requirements/examples` sees both sets at once and fails with 11
duplicate-ID errors — both sets define `FR-001`, `NFR-001`, and so on. The validator is
built to validate one project's requirements directory; the examples tree is two projects
wearing one.

This predates the glossary work (it landed with PR #6) but blocks it: the glossary backfill
must place a file in the GDPR set, and under the current layout that file lands at
`docs/requirements/examples/glossary.md`, where it reads as a glossary for the *examples
directory* rather than for the GDPR set — the same ambiguity that already afflicts
`examples/assumptions.md`.

Fix the layout first, making each example set self-contained and mirroring tamagotchi:

```
docs/requirements/examples/
  gdpr/requirements/       <- moved from examples/ root
    functional/ non-functional/ constraints/ business-rules/
    assumptions.md
    definition-of-done.md
  tamagotchi/requirements/
    ...
```

The move is cheap: outside of the historical plan/spec documents (records of past work,
which are not rewritten), the only live reference to these paths is
`docs/requirements/examples/tamagotchi/README.md`. Neither `SKILL.md` nor the scripts point
at the examples tree. A `docs/requirements/examples/README.md` gets added to say what the
two sets are and that each is validated independently.

Note that the two earlier specs' verification lines cite
`validate_requirements.py docs/requirements/examples` as passing. That command passed when
those specs were written (before tamagotchi landed) and fails today. Those documents stay
as they are — they are historical records — but the corrected per-set commands are the ones
carried forward below.

## Part G — Backfill and documentation

The presence gate is breaking by construction: every set without a `glossary.md` starts
failing validation the moment it lands. Both committed example sets must therefore gain one
in the same change, or they fail their own validator — and the tamagotchi set is the
artifact the dev-log post (STO-198) points readers at, so leaving it red is not an option.

- `docs/requirements/examples/tamagotchi/requirements/glossary.md` — real terms (decay,
  neglect, mood, quarantine, and the like), written from the existing requirement text.
- `docs/requirements/examples/gdpr/requirements/glossary.md` — likewise (erasure,
  personal data, data subject, statutory retention).
- `skills/requirements/SKILL.md` — name the glossary in the Phase 5 formatter step and in
  the Step 4 validation step (it is part of the hard gate).
- `agents/requirements-formatter.md`, `agents/requirements-orchestrator.md`,
  `agents/{fr,nfr,constraint}-specialist.md`, `agents/requirements-critic.md` — the
  contract changes above.

## Build order

0. Move the GDPR set to `examples/gdpr/requirements/`; add an `examples/README.md`; update
   the tamagotchi README's path reference. Confirm both sets validate green per-set.
1. Validator: generalize the context-artifact check, add the `glossary.md` gate + fixtures.
2. Linter: add the set-level check hook and the `glossary-unused` check + fixtures.
3. Agent contracts: specialist `terms`, orchestrator Stage 6.5 merge, formatter write,
   critic pass.
4. `SKILL.md` wiring.
5. Backfill both example sets' `glossary.md`; re-run both gates until green.

Step 0 is a pure move with no behavior change and lands first so the rest has a coherent
target. Steps 1 and 2 are independently testable against fixtures before any agent prose
changes. Step 5 is the acceptance check for the whole change.

## Verification

Each example set is validated independently — there is no combined command, because the two
sets are separate projects with separate ID spaces.

- `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements` → exit 0 (22/22, new glossary gate satisfied).
- `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements` → exit 0 (8/8, new glossary gate satisfied).
- `python3 skills/requirements/scripts/lint_requirements_content.py <each set>` → exit 0, no `glossary-unused` findings.
- `python3 -m pytest skills/requirements/scripts/tests/` → green, including the new
  validator fixtures (valid / missing `glossary.md` / missing `## Terms` heading) and the
  new linter fixtures (unused term → one `warn`; clean → none).

## Out of scope

- `used_by` requirement-ID backlinks on glossary entries (rejected above — derivable, and
  a new dangling-reference class to maintain).
- Undefined-term detection in the linter (given to the critic — it is a judgment call).
- A dedicated glossary specialist agent (rejected above — a prompt problem, not a stage).
- Cross-stage glossary enforcement in M2/M3. The glossary is *emitted* here and read
  downstream; making architecture and QA artifacts validate their terminology against it
  belongs with those stages, not with M1.

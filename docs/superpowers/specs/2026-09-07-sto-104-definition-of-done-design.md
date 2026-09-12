# Definition of Done Generator — Design

**Ticket:** STO-104 (M3, second of three)
**Date:** 2026-09-07
**Status:** approved

## Problem

M1 emits a Definition of Done, but only a stub: `dod-generator` runs at the end
of the requirements pipeline and derives gates from FR and NFR frontmatter
alone. Its own text says so — "This is an **M1 stub**… **STO-104 (M3)** expands
this into the full DoD generator."

The ticket asks that expansion to pull in acceptance criteria from FRs, NFR
fitness functions, architectural fitness functions from the design stage, QA
coverage gates from the QA strategy, documentation requirements, and a
deployment readiness checklist, emitting a checklist-style Markdown file usable
directly in a PR template.

The ticket was written 2026-05-30, before M2 and M3 existed. Three of its
assumptions no longer hold, and one of the things it asks for has no schema to
stand on. Those are E1, E2 and E3 below.

## Evidence

### E1 — The generator runs at a stage that cannot see its inputs

`plugin/skills/requirements/SKILL.md:268` dispatches `dod-generator` as step 5
of the requirements stage, and the agent writes
`.sdlc/requirements/definition-of-done.md`.

Two of the ticket's six input sources — design artifacts and the QA strategy —
do not exist at that point in the pipeline. The generator cannot be expanded in
place; it has to move to run after the stage that produces its last input.

### E2 — No stage writes into a previous stage's directory

STO-103 established this as the pipeline's strongest structural constraint and
spent a spec section (its D3) defending it: the design formatter contains no
write path under `.sdlc/requirements/`, and the requirement↔design edge is
stored once on the downstream artifact with `validate_traceability.py` walking
it backwards.

Moving the generator to the QA stage while leaving its output at
`.sdlc/requirements/definition-of-done.md` would be the first violation of that
invariant. The output path has to move with the generator.

### E3 — "Architectural fitness functions" have no field to read

`design.schema.json` carries, across its four branches: `responsibility`,
`boundary`, `depends_on` (component); `provider`, `operations`, `error_modes`
(interface); `decision_status`, `considered_options`, `chosen_option` (adr);
`level`, `container` (diagram). Plus the shared `id` / `title` / `description` /
`traces_*` / `status` / `confidence`.

Nothing measurable. No threshold, no target, no response measure. The
measurable oracles in the artifact set are the NFRs' six-part quality attribute
scenarios, which the M1 stub already reads, and the QA items' `enforcement`
field, which nothing reads yet.

What the design stage *can* contribute is different in kind: accepted ADRs are
decisions that must hold, and the `depends_on` graph is a structural rule.
Those are conformance gates, not fitness functions.

### E4 — The NFR quality characteristic is on disk, and the M1 agent guesses it

Every NFR body carries a `## ISO 25010 Characteristic` heading —
`Security → Confidentiality`, `Reliability → Availability`,
`Extension: Observability`. Present in 24 of 24 NFRs across both worked example
sets.

`dod-generator.md` step 2 nonetheless says to derive the operational categories
by inferring "security, reliability, observability, deployability… from
title/description". It title-sniffs data that is sitting in a fixed heading.

The heading is not gated by `validate_requirements.py`, and the text after the
arrow is free prose that sometimes wraps or carries a parenthetical. The token
*before* the separator is a closed set of eight: Compatibility, Extension,
Flexibility, Functional Suitability, Interaction Capability, Performance
Efficiency, Reliability, Security.

### E5 — `enforcement` was added for this ticket, and `none` reaches nothing

`qa.schema.json`'s `enforcement` property documents itself as
"STO-104 reads it to tell a real DoD gate from one a human must remember", with
values `ci | manual | none`.

STO-307's first finding is that `ci` and `manual` both reach a consumer but
`none` reaches nothing: STO-103's end-to-end run emitted 22 `ci`, 6 `manual` and
3 `none` over 31 items, and no artifact records the three. STO-307 proposes
routing them into the QA stage's `accepted_risks`.

### E6 — Deterministic projection is a script here, not an agent

`generate_c4.py`'s module docstring states the rule: "The component graph is
already fully described in frontmatter… so the three C4 views are a projection
of the artifact set, not a new authored document. This tool performs that
projection."

The same sentence is true of the DoD. Every line the M1 agent emits is derived
from a frontmatter field or a fixed body heading — its "Process" section is a
rendering algorithm written in prose.

`plugin/agents/` currently holds 20 agent files. STO-247, the pipeline's token
and cost analysis, is unstarted, so nothing has measured what the existing
roster costs.

### E7 — Cross-skill script references already have a precedent

The QA skill's "Locating the scripts" section reaches sideways for three
scripts it does not own — `../requirements/scripts/validate_requirements.py`,
`../design/scripts/validate_design.py`, `../design/scripts/validate_traceability.py`
— and states explicitly that there is no separate copy under its own `scripts/`.

`validate_traceability.py` is itself a cross-stage script living in one stage's
directory.

## Decisions

### D1 — The output moves to `.sdlc/definition-of-done.md`

Root level, not under any stage directory.

The alternative placements both fail on something. Keeping it at
`.sdlc/requirements/definition-of-done.md` breaks E2's invariant outright.
Moving it to `.sdlc/qa/definition-of-done.md` is consistent with every other
artifact living under a stage, but it makes the DoD unreachable for a team that
runs only `/groundwork:requirements` — and that team is the one most likely to
want a Definition of Done, since they have no other gate artifact at all.

The DoD is the one artifact no single stage owns: it derives from all three and
gets sharper as the pipeline runs. The root path says that.

### D2 — A deterministic script; the `dod-generator` agent is deleted

`generate_dod.py`, following E6's precedent. The agent file is removed and the
roster goes 20 → 19.

The argument for keeping an agent is that an LLM degrades gracefully over a
malformed NFR where a parser raises. That points the wrong way here. The DoD's
entire value is that every gate traces to a file; one that quietly papers over a
requirement it could not parse is claiming coverage it does not have. Failing
loudly is the correct behaviour, and it is only available to the script.

C4 needed an agent alongside its script because container grouping and external
actors appear nowhere in the frontmatter. The DoD has no equivalent gap — see
E4, where the one judgment the M1 agent claimed to make turns out to be a
parse.

### D3 — All three stages invoke it; each run supersedes the last

`/groundwork:requirements` writes a requirements-only DoD;
`/groundwork:design` rewrites it with conformance gates added;
`/groundwork:qa` rewrites it again with coverage gates and the enforcement
split. A header line names which stages fed the current file.

This is what makes D1's root path honest rather than merely tidy. It also gives
the generator a natural regression test: run it after each stage against one
example set and the gate count only grows.

Invoking at QA only would reintroduce the gap D1 rejected. Skipping the design
stage would leave a DoD on disk that silently predates the architecture it
should reflect — worse than either extreme, because it looks current.

### D4 — One file, source-grouped, with a lead `## PR Checklist`

The gdpr DoD is 186 lines from requirements alone; adding design and QA roughly
doubles it. Nobody pastes 350 lines into a pull request. But the traceable
artifact and the PR checklist are the same document at different resolutions,
and what separates them is already in the data: a gate CI enforces does not
need a human checkbox, it needs a passing build.

So `## PR Checklist` comes first and holds only what a human must personally
confirm — `manual` QA items, NFRs whose `verification_method` is
`inspection` / `analysis` / `demonstration`, accepted-ADR conformance, and the
documentation gates. Everything else follows, grouped by source, each gate
annotated `[CI]` / `[manual]` / `[unenforced]`.

| § | Section | Derived from |
|---|---------|--------------|
| 1 | Functional Acceptance Gates | one gate per FR: `fit_criterion`, `verification_method`, link to file |
| 2 | NFR Fitness Gates | the QAS **Response measure** as pass/fail oracle, plus stimulus, artifact, environment |
| 3 | Architectural Conformance Gates | accepted ADRs and the `depends_on` graph |
| 4 | Test Coverage | per FR/NFR, the `TS-` items whose `traces_from` cites it |
| 5 | Documentation Requirements | `must` FRs; NFRs whose ISO characteristic head is Security, Reliability or Extension |
| 6 | Deployment / Operational Readiness | Security and Reliability NFRs; `CON-` / `BR-` IDs holding in the deployed config |
| 7 | Declared Unenforced | every `enforcement: none` item with its `risk_rationale` |

Two rejected shapes. Two files (full plus short) would be a drift surface
between generated documents that must agree, where the repo's pattern is one
artifact with gated headings that downstream tooling reads by heading —
`qa-strategy.md` is projected exactly that way. Grouping the whole document by
enforcement strength rather than by source would break the per-stage reading
that makes the DoD auditable, and would move a requirement's gate between
sections when someone flips a QA item from `manual` to `ci` — a noisy
regeneration diff for a change that is not about that requirement.

### D5 — `enforcement: none` gets section 7 regardless of STO-307

STO-307 proposes routing unenforced items into the QA stage's `accepted_risks`.
That is the right fix at that stage and stays in that ticket.

Section 7 is not the same thing and does not wait on it. A DoD that lists 28
gates and silently omits the 3 items which declared themselves unenforced is
claiming coverage the project does not have. If STO-307 lands, the two
registers agree and the redundancy is harmless; if it does not, the DoD is
still honest.

### D6 — Section 3 stays modest, and is named for what it is

Accepted ADRs (`decision_status: accepted` → the `chosen_option` must hold) and
the declared `depends_on` edges (no dependency outside the graph). Nothing
invented, because per E3 there is nothing else to read.

Named "Architectural Conformance Gates" rather than the ticket's "architectural
fitness functions". A fitness function has a measure; these have a rule. Using
the ticket's words would promise a threshold that section cannot deliver, and
would obscure that section 2 is where the measurable architecture gates
actually live.

### D7 — Coverage is derived from `TS-` `traces_from`, not re-checked

Section 4 lists, for each FR and NFR, the `TS-` items whose `traces_from` cites
it. A requirement with none shows as a visible gap.

`validate_traceability.py` already has `uncovered-fr` and `uncovered-asr` rules
over the same edge. Section 4 does not re-implement them and does not shell out
to the validator: it renders the derivation, and the rules stay the single
place the gate is enforced. Same information, one copy of the logic.

### D8 — Two NFR body sections become a parsed contract, and get gated

`generate_dod.py` reads `## ISO 25010 Characteristic` (the head token before
`→` or `:`) and the QAS `**Response measure:**` bullet out of the NFR body.

Per E4 both are present in every NFR and neither is gated today. Making them
load-bearing without gating them would leave the generator's most likely
failure mode undetectable until it ran. So `validate_requirements.py` gains a
body-heading check for `type: non_functional`, in the shape it already uses for
`assumptions.md`'s three headings and `glossary.md`'s `## Terms`.

Only the head token is parsed. `Extension: Observability`,
`Extension: Deployability` and `Extension: Compliance` therefore collapse into
one bucket, which sections 5 and 6 take wholesale rather than splitting. The M1
stub distinguished observability from deployability by title-sniffing; both
land in section 5 either way, and pulling them apart would mean parsing the
free prose after the separator — the part E4 shows is not stable.

Scope addition, deliberately taken inside this ticket rather than deferred: it
is the direct cost of D2, and splitting it out would ship a parser whose
contract nothing enforces.

### D9 — No template file; the document is generated in code

`plugin/skills/requirements/templates/definition-of-done.md` is deleted.

Its `{{...}}` / `{{#each FR}}` pseudo-handlebars was written for an LLM to
interpret loosely. A real renderer needs conditionals for absent stages (D3),
which is code, not template syntax — and `generate_c4.py` sets the precedent of
building its output in code with no template.

`qa-strategy.md` keeps its template because an agent projects it. Nothing
projects the DoD any more.

### D10 — `scope` remains `project`

`dod-generator.md` step 3 promises that STO-104 will group requirements by
`scope` / `parent_scope` to emit per-epic and per-story gate subsets. That
promise predates STO-106 (M4), "Implement agile scope parameterization
(project/epic/story granularity)", which owns the parameterization end to end.

Slicing the DoD before the pipeline can populate the fields would be a feature
with no input. The stale promise is corrected rather than inherited.

## Files touched

**New**
- `plugin/skills/requirements/scripts/generate_dod.py`
- `tests/dod/` — `conftest.py`, `test_generate_dod.py`, `fixtures/`

**Modified**
- `plugin/skills/requirements/scripts/validate_requirements.py` — NFR body-heading gate (D8)
- `plugin/skills/requirements/SKILL.md` — step 5 replaced by the script call; scripts section notes the new file
- `plugin/skills/design/SKILL.md` — DoD regeneration step, reaching `../requirements/scripts/`
- `plugin/skills/qa/SKILL.md` — DoD regeneration step; "Locating the scripts" gains a fourth sibling entry
- `plugin/skills/requirements/scripts/README.md`, `plugin/skills/qa/scripts/README.md`
- `site/content/architecture/index.mdx` — the "seventh agent runs after the pipeline" passage is wrong twice over
- `site/content/guide/requirements-stage.mdx` — the tree listing and the derivation note
- `site/content/guide/gates.mdx`, `site/content/guide/troubleshooting.mdx`
- `site/scripts/export_examples.py` — the requirements file list and the title map
- `site/content/_generated/agents.json` — via `export_reference.py`

**Deleted**
- `plugin/agents/dod-generator.md`
- `plugin/skills/requirements/templates/definition-of-done.md`

`validate_requirements.py`'s `SKIP_FILENAMES` keeps its `definition-of-done.md`
entry: a file left at the old path by an earlier run should not start failing
the validator.

## Testing

Fixtures on the `test_every_invalid_fixture_is_exercised` pattern already used
by `tests/qa/test_validate_qa.py` — a fixture directory nobody parametrizes is
a case nobody tests.

- **Stage degradation (D3):** requirements-only, +design, +qa over one fixture
  set. Asserts each section appears exactly when its inputs do, the header
  names the right stages, and gate count is monotonic across the three.
- **Section derivation (D4):** one test per section, asserting the gate text
  carries the ID it derives from and links the file it came from.
- **`## PR Checklist` composition:** contains every `manual` item and no `ci`
  item; contains non-`test` NFRs and no `test` NFR.
- **Declared Unenforced (D5):** `enforcement: none` items appear with their
  `risk_rationale`; absent from the PR checklist.
- **Body parsing (D8):** the eight ISO characteristic heads, the `Extension:`
  colon form, a wrapped characteristic line, a missing heading (exit 1), a
  missing response measure (exit 1).
- **`validate_requirements.py` gate (D8):** invalid fixtures for each missing
  NFR body heading; a `type: functional` file without them still passes.
- **Package boundary:** `tests/test_plugin_package.py` is unchanged and must
  stay green — the new script lives under an existing skill's `scripts/`.

## Out of scope

- **`scope` / `parent_scope` slicing.** STO-106. See D10.
- **The PR template file itself.** STO-107, "GitHub repo scaffolding command
  (rulesets, CODEOWNERS, PR template, CI stubs)". This ticket makes
  `## PR Checklist` a stable heading for it to slice.
- **Routing `enforcement: none` into `accepted_risks`.** STO-307. See D5.
- **Worked-example regeneration.** Both committed DoDs are M1-stub output and
  go stale the moment this lands. Worse, neither example set has a committed
  `qa/` directory — STO-103's end-to-end run was not kept — so a full
  three-stage DoD cannot be demonstrated without generating a QA set first.
  That is STO-219's shape and wants its own ticket, filed rather than
  absorbed: STO-309.
- **A DoD content linter.** M1 and M2 each got theirs as a separate ticket
  (STO-136, STO-208), and M3's is already filed as STO-306.

## Known consequences

- **The committed worked examples are stale on merge.** Both
  `definition-of-done.md` files still carry the M1-STUB banner and point at an
  agent that no longer exists. The follow-up ticket above closes this; until it
  lands, the docs site renders a DoD the pipeline can no longer produce.
- **The DoD is generated three times per full pipeline run.** Twice
  redundantly, in the sense that only the last one survives. This is accepted:
  the cost is one script invocation, and the alternative is a DoD that only
  exists if you run all three stages.
- **`## ISO 25010 Characteristic` becomes a breaking-change surface.** After
  D8, changing that heading in `nfr-specialist.md` breaks the generator. The
  validator gate is what turns that from a silent failure into a caught one,
  but the coupling is real and new.
- **Nothing gates `.sdlc/definition-of-done.md` structurally.** It sits under
  no stage validator, so the generator self-checks its own output and the tests
  carry the contract. A hand-edited DoD is caught by regeneration, not by a
  gate — which matches its "generated, do not hand-edit" footer.
- **The roster drops to 19 while STO-247 is still unstarted.** This ticket
  makes the cost question no worse, but does not answer it.

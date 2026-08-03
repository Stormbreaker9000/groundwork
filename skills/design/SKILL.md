---
name: design
description: Use when a validated requirement set exists and the user is ready to turn it into an architecture — guides an architecture interview and a multi-agent pipeline that produces atomic component and interface specs before any code is written.
---

# Design

Turn a validated requirement set into a structured architecture artifact through
an interview that covers what requirements deliberately cannot carry, followed by
a multi-agent generation pipeline. This is phase 2 of the groundwork SDLC
workflow — it follows `requirements` and precedes implementation.

## When This Applies

Invoke when a validated requirement set exists under `.sdlc/requirements/` and
the user is ready to turn it into an architecture:
- "Design this"
- "Let's do the architecture"
- "Turn the requirements into components"
- "What should the system look like structurally?"

Do NOT invoke for:
- Questions or explanations
- Bug reports
- Requests to read, explore, or explain existing code
- A request to build something for which no requirement set exists yet — send
  the user to the `requirements` workflow first

**Do not write any application code at any point during this skill.** This
skill produces design artifacts only — component and interface specs, ADRs,
plus `assumptions.md` and `drivers.md`. Nothing under `.sdlc/design/` is
executable.

## Phase 1 — Locate and Read the Input

Find `.sdlc/requirements/`. If it is absent, stop and direct the user to the
`requirements` workflow — there is nothing to design against.

Run the entry gate:

```bash
python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements
```

A non-zero exit stops the stage: designing against a structurally invalid
requirement set is meaningless. Fix or send the user back to `requirements`
before proceeding.

**This is a structural gate only.** A non-empty `review_queue` in `index.yaml`
does **not** block — do not treat it as a defect to clear before moving on.
Those low-confidence requirements and the open questions in `assumptions.md`
are frequently architecture decisions that correctly landed in the
requirements stage's out-tray. They are carried forward on purpose and opened
with, not resolved here in Phase 1 — see Phase 3.

Once the gate passes, read:
- Every requirement file (functional, non-functional, constraints, business
  rules, use cases)
- `index.yaml`'s `review_queue`
- `assumptions.md`'s `## Open Questions`

**If an existing codebase is present**, scan it the same way `requirements`
does — a bounded 3–5 file read (root config, entry point, most relevant
existing modules), not a full audit. Stop once you have enough to form
grounded hypotheses about the runtime and stack in Phase 2.

## Phase 2 — Hypothesise

One message, one question — the same shape as M1's hypothesis phase.

Propose:
- A candidate decomposition: 4–6 named components in plain terms (not yet
  `CMP-` IDs — those are allocated by the orchestrator in Phase 5)
- A stack hypothesis: your best guess at runtime, persistence, and deployment
  target, grounded in the requirement set and any codebase scan from Phase 1

Present as a single message and ask whether it matches.

**Example — the tamagotchi requirement set:**

*"Based on the requirements, here's a candidate decomposition: a Pet State
Store (persisted state, single source of truth), a Decay Engine (time-based
state degradation, including offline-elapsed catch-up), a UI Renderer (mood
display, interaction surface), an Input Handler (feed/play/clean/sleep
actions), and a Save/Recovery layer (corrupted-file recovery, per NFR-004).
Given the offline-only, single-user, low-footprint constraints, I'd guess a
lightweight desktop-app stack with local file-based persistence and no backend
service — but the specific runtime is still open (see Q-4 below). Does this
decomposition match your vision, or are there pieces missing or wrong?"*

This is ONE question. Do not ask multiple questions in this message.

## Phase 3 — Architecture Interview

Six coverage areas the requirement set cannot carry, by construction:
1. **Runtime and stack** — language, framework, runtime
2. **Persistence** — storage mechanism, data model shape
3. **Deployment target** — where this runs (desktop, server, edge, mobile, CLI)
4. **Integration points** — external systems, third-party services, APIs
5. **Operational constraints** — hosting, monitoring, on-call, resource budgets
6. **Team constraints** — existing team skills, timeline, org standards

**Why this interview exists.** The requirement set *cannot* carry this
context — that is by construction, not omission. M1's content linter treats
implementation bias as a defect and its critic flags it, so nothing in
`.sdlc/requirements/` says "Tauri" or "Postgres", and nothing should. This
stage therefore either asks or invents. The project's own history settles
which: an earlier build took an unexamined Electron recommendation and paid
to rip it out later. So this stage asks.

**Open with the inherited open questions.** Many of the `Q-` items in
`assumptions.md` are architecture decisions by nature — they landed in the
requirements stage's out-tray because they genuinely belong here, not because
they were missed. Surface them first, before the six coverage areas, not
after.

**Worked example.** The tamagotchi requirement set left `Q-4` open: *"Which
framework/runtime is chosen given the footprint constraint (Electron vs Tauri
vs native)?"* `NFR-002` (idle CPU/memory budget) and `CON-001` (runtime
footprint boundary) both sit in `review_queue` because they rest on this
question. This is exactly this stage's call to make — it goes first:

*"The requirements stage left one open question for architecture: Q-4 — which
framework, given the footprint constraint? (1) Electron, (2) Tauri, (3) a
native toolkit per platform. Idle CPU/memory (NFR-002) and the runtime
footprint boundary (CON-001) both depend on this answer. Pick one, or
describe another."*

**Rules for the remaining six areas:**
- **One question per message.**
- **Prefer 2–4 numbered options** over open-ended questions when the answer
  space is enumerable — this measurably improves answer quality, the same
  rationale `skills/requirements/SKILL.md` applies to its own interview.
  Reserve open-ended questions for genuinely open spaces. For example: *"For
  persistence, should the pet state live in (1) a single local JSON/binary
  file, (2) an embedded database (e.g. SQLite), or (3) something else? Pick
  one, or describe another."*
- **Infer from the codebase where obvious.** Only ask what you cannot
  determine. If Phase 1's scan already shows a Postgres connection string and
  a `docker-compose.yml`, do not ask about persistence or deployment target —
  state the inference and ask only for confirmation, or skip asking entirely
  if it is unambiguous.
- A well-scoped request typically needs a handful of exchanges once the
  inherited questions are resolved. A greenfield system with no prior
  decisions may need more.

Proceed to Phase 4 once all six areas are covered (by answer or by confident
inference) and every inherited open question has a recorded disposition —
`resolved` (with the resolution) or `still_open`.

## Phase 4 — `design_context` Synthesis

Before dispatching the pipeline, synthesise everything elicited into a
structured context object. This confirms shared understanding and serves as
the direct input to the `design-orchestrator`.

Render in-conversation:

```
**Design context:**

**System purpose:** ...
**Runtime & stack:** ...
**Persistence:** ...
**Deployment target:** ...
**Integration points:** ...
**Operational constraints:** ...
**Team constraints:** ...
**Out of scope:** ...
**Inherited questions:** [each Q-# with resolved / still open]
**Inherited review queue:** [requirement IDs, or "None"]
```

Ask: *"Does this capture the design context correctly, or should I adjust
anything before generating the architecture?"*

**Do not proceed to Phase 5 until the user confirms.** If corrections are
needed, update the context object and re-confirm. This is a hard stop, not a
formality — nothing downstream runs on an unconfirmed context.

## Phase 5 — Generate

The confirmed Phase 4 block serialises 1:1 to the `design_context` the
`design-orchestrator` consumes:

```yaml
design_context:
  requirements_root: ".sdlc/requirements"
  system_purpose: string             # restated from the requirement set, not re-elicited
  runtime_and_stack: string
  persistence: string
  deployment_target: string
  integration_points: string         # external systems → boundary: external components
  operational_constraints: string
  team_constraints: string
  out_of_scope: string               # or "None identified"
  inherited_open_questions:
    - id: Q-4                        # ID preserved from requirements/assumptions.md
      statement: string
      disposition: resolved | still_open
      resolution: string             # present only when resolved
  inherited_review_queue: [ NFR-002, CON-001 ]
```

**Step 1 — Generate (multi-agent pipeline):**

Drive the pipeline through the agents under `agents/`, in this fixed order:

1. **design-orchestrator** — reads the requirement set once on everyone's
   behalf, identifies architecturally significant requirements (ASRs),
   allocates `CMP-`/`IF-` ID blocks, and dispatches a `generation_brief` to
   each specialist.
2. **component-specialist** — decomposes the system into components, each
   with a single declared responsibility, tracing to the requirements that
   drove it.
3. **interface-specialist** — receives the component set and turns every
   declared capability into an interface with a `provider`, operations,
   interaction style, and error modes.
4. **design-critic** — runs a two-phase review, judgment only: per-artifact
   quality (ISO/IEC/IEEE 42010) and ASR coverage with tradeoffs and
   sensitivity points named (ATAM-lite). Returns `gate: pass` or
   `gate: fail`. It does not run `validate_design.py` — nothing is on disk
   yet at this stage, and `drivers.md`'s gated headings are this critic's own
   output, so the structural check belongs downstream, at the formatter.
5. **adr-generator** — dispatched at Stage 9.5, after `gate: pass`. Promotes
   resolved `Q-` decisions and `deferred_to_decision` ASRs into architecture
   decision records; never invents a rejected option, so a decision whose
   alternatives can't be recovered stays in `drivers.md` and is reported in
   `skipped` instead. Returns `draft_adrs` — an empty set is legal and means
   nothing qualified.
6. **design-formatter** — writes the atomic component/interface/ADR files plus
   `assumptions.md` and `drivers.md`, and `index.yaml`'s `review_queue`,
   back-fills `traces_to.adr` on the artifacts each ADR affects, then re-runs
   `validate_design.py` against what it just wrote — the pipeline's single
   structural gate (see Step 4). **Runs only on `gate: pass`.** Do not advance
   past the critic on a failing or partial gate — the orchestrator
   re-dispatches only the affected artifacts back to their owning specialist
   and re-runs the critic.

**Step 2 — Render in-conversation summary (before writing anything):**

```
## Design Summary: <Feature Name>

**Overview:** [2-3 sentences: what's being architected, and the core shape of the solution]

**Components:**
- CMP-001 <title> — <one-line responsibility>

**Interfaces:**
- IF-001 <title> — provider: CMP-XXX, interaction: synchronous | asynchronous

**Drivers:**
- ASRs: [requirement ID → why it shapes structure]
- Tradeoffs: [decision → gains vs. costs]
- Sensitivity points: [what would change the decision]

**Assumptions & Dependencies:** [key A-#/D-# items, or "None identified"]
**Open Questions:** [Q-# items still open, or "None"]

**⚠️ Triage before sign-off — review these specifically:**
- **Low-confidence artifacts:** [each `confidence: low` CMP/IF ID with its one-line reason — or "None"]
- **Open questions:** the items listed under **Open Questions** above.

  These are the uncertain items; confirm or correct *these* rather than re-scanning the whole set. The same low-confidence list is persisted as `review_queue` in `index.yaml`.

**Next Step:** Implementation
```

**Step 3 — Sign-off gate:**

Ask: *"Does this capture the architecture accurately, or should we adjust
anything before I write the files?"*

**No files are written until the user confirms.** If corrections are needed,
re-dispatch the affected artifacts to the owning specialist via the
orchestrator, then re-summarise. This mirrors M1's invariant exactly and it
is not relaxed here.

**Step 4 — Write, then validate (hard gate):**

On confirmation, run the formatter. The formatter writes the files and, as
part of its own contract, immediately re-runs the structural validator
against them (`agents/design-formatter.md`'s "Validator re-run" section) —
this is the pipeline's single structural gate, and it is the first point at
which structure *can* be checked, since nothing was on disk before now. The
critic's earlier `gate: pass` was judgment only (per-artifact quality and ASR
coverage); it never ran this command.

```bash
python3 skills/design/scripts/validate_design.py .sdlc/design
```

The validator MUST exit 0. If it exits non-zero, do not treat the write as
done: fix the flagged files (re-dispatch to the owning specialist through the
critique loop) and re-run until clean. It requires `pyyaml` and `jsonschema`
(`pip install pyyaml jsonschema`); see `skills/requirements/scripts/README.md`
for the install and fallback details (the design validator shares the same
dependency story).

**Step 5 — Commit:**

```bash
git add .sdlc/design/
git commit -m "docs: add design artifact set for <feature-name>"
```

## ADRs

This stage writes architecture decision records to `.sdlc/design/adr/` in MADR
4.0 format, one atomic file per decision, validated by the same structural gate
as components and interfaces.

ADRs are **derived, never elicited**. The generator promotes decisions the
pipeline already recorded — resolved `Q-` questions from the architecture
interview, and ASRs the critic marked `deferred_to_decision` — and it never
invents a rejected option to fill out the template. A decision whose
alternatives cannot be recovered stays in `drivers.md` and is reported in the
generator's `skipped` list.

So an empty or absent `adr/` directory is a legal outcome: it means nothing
qualified, not that something failed.

## What This Stage Does Not Produce

This stage does not write C4 diagrams. `.sdlc/design/diagrams/` is a declared
dispatch slot owned by STO-101 — an absent `diagrams/` directory after this
skill runs is expected, not a bug.

This stage also does not resolve cross-artifact traceability (`traces_from`
resolution, dependency-cycle detection, orphan-interface detection) — that is
STO-102's and STO-208's territory, not this skill's.

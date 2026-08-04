# M2 ADR Generation (MADR 4.0) — Design

**Ticket:** STO-100
**Date:** 2026-08-03
**Status:** approved, ready for implementation planning

## Problem

The M2 pipeline decides architecture but does not record its decisions as
first-class artifacts. Three agent files and the design skill all describe an
ADR generator that does not exist, and each carries a temporary fallback that
exists only because it is missing:

- `agents/design-critic.md` emits `deferred_to_decision` for an ASR that turns
  on an undecided question, and calls a `Q-` open question "the honest
  disposition until STO-100 exists to write the ADR."
- `agents/design-orchestrator.md` declares Stage 11 as a slot: "Not
  implemented... Do not invent ADR files."
- `agents/design-formatter.md` writes `traces_to.adr: []` on every artifact and
  is told not to create `adr/`.
- `skills/design/SKILL.md` documents an absent `adr/` directory as "expected,
  not a bug."

The decisions themselves are not missing. They are already being made and
already being written down — just flattened into one-line prose in
`drivers.md`, in a section whose heading says "Tradeoffs" rather than
"Decisions".

## Evidence

The shipped tamagotchi example proves the raw material is present and
ADR-shaped. Its `drivers.md` Tradeoffs section contains nine entries. Three of
them are resolved interview questions that name a chosen option *and* the
options it beat:

| Entry | Chosen | Rejected | Affected |
| --- | --- | --- | --- |
| Q-4 | Tauri (Rust core + OS webview) | Electron; native view per platform | NFR-002, CON-001 |
| Q-3 | Windows first for v1 | all three platforms at once | CON-003 |
| Q-2 | permanent death | reset-to-new-pet | FR-008, BR-001 |

Each already carries `gains`, `costs`, and `affected` requirement IDs. Mapped
onto MADR 4.0 that is: `considered_options`, `chosen_option`, good and bad
consequences, and decision drivers. The conversion is mechanical.

The remaining six entries are structural tradeoffs — IF-002's async flush,
IF-003's synchronous commit, IF-007's pull over push, CMP-001's inlined
platform behaviour, the shared webview, and the absent network surface. They
name a chosen and a rejected shape too ("rather than", "instead of"), but they
are properties of the decomposition rather than decisions taken against
alternatives that were genuinely weighed. They belong where they already are.

A second source exists but has never fired in a shipped example: an ASR the
critic marks `deferred_to_decision`. The tamagotchi run produced none, so the
fallback path (record it as a `Q-`) is the only one exercised to date.

## Decisions

### D1 — Derive from recorded pipeline data; never elicit, never invent

The generator reads what the pipeline already recorded. It does not re-open the
architecture interview, and it does not infer rejected options that nobody
considered.

This is the load-bearing constraint of the whole design. An ADR's value is that
it records a decision that was actually taken with alternatives that were
actually weighed. An ADR whose "Considered Options" were reverse-engineered by
an agent from the chosen option is a plausible-looking fabrication of project
history, and it is worse than no ADR because it is indistinguishable from a
real one after the fact.

**Consequence, stated plainly:** an entry with no recoverable alternative does
not become an ADR. Not a stub, not an ADR with one option listed. It stays in
`drivers.md`.

### D2 — Scope: resolved `Q-` decisions and deferred ASRs only

Two admissible sources:

1. **Resolved `Q-` questions**, which reach the generator as
   `drivers.tradeoffs` entries. Stage 9 of the orchestrator already routes every
   `inherited_open_questions` entry with `disposition: resolved` into
   `tradeoffs`, one entry each.
2. **`deferred_to_decision` ASRs** from the `critique_report`, which become ADRs
   with `decision_status: proposed`.

Structural tradeoffs are out of scope. Promoting all nine would make `adr/` a
near-duplicate of `drivers.md`'s Tradeoffs section, and would file IF-002's
flush timing — a contract detail the interface's own body already explains — as
an architecture decision record.

Tamagotchi under this rule yields three ADRs, from Q-2, Q-3 and Q-4.

**Distinguishing rule.** A `drivers.tradeoffs` entry qualifies when its
`decision` field identifies a question that was posed and settled — in practice,
when it names a `Q-` ID. A structural tradeoff describes a shape the design
took. The `Q-` ID is the discriminator, not prose sentiment about how important
the entry feels.

### D3 — Stage 9.5: before the formatter, not after

The declared slot puts ADR generation at Stage 11, after the formatter. This
design moves it to Stage 9.5, between the orchestrator's
`design_context_artifact` synthesis (Stage 9) and the formatter (Stage 10).

```
Stage 9    orchestrator synthesises design_context_artifact
             (drivers.tradeoffs and open_questions are ready here)
             │
Stage 9.5  [ adr-generator ]  → draft_adrs
             │
Stage 10   [ design-formatter ]
             writes components/ interfaces/ adr/
             populates traces_to.adr inline
             runs validate_design.py    ← one gate, over everything
```

Rationale: at Stage 11 the generator would be a *second writer*, re-opening
CMP/IF files the formatter had already written and the validator had already
passed, then re-running the gate. STO-215 and STO-99 both landed fixes whose
whole point was to make the formatter the single writer and the single
structural gate. Reintroducing a second writer immediately after would undo
that.

Everything the generator needs exists at Stage 9. Nothing it produces is needed
before Stage 10. The slot's placement was a guess made before the gate moved;
this is that guess corrected.

### D4 — ADR is a third artifact type in `design.schema.json`

`ADR-` joins `CMP-` and `IF-` as a schema type with YAML frontmatter and gated
MADR headings in the body, validated by the existing `validate_design.py` in the
same pass as every other artifact. `adr` is removed from `SKIP_DIRNAMES`.

The alternative — a separate `adr.schema.json` — would leave two schemas
describing one artifact set and two validation passes over one directory. The
alternative of unvalidated MADR prose would make ADRs the only artifact type in
the system with no machine check.

### D5 — `decision_status` is separate from `status`

The base schema's `status` enum is the artifact lifecycle:
`[draft, reviewed, approved, implemented, verified, obsolete]`. MADR's status
vocabulary is `[proposed, rejected, accepted, deprecated, superseded]`.

These cannot be merged. A JSON Schema branch can only narrow an enum, so
`accepted` can never validate against the base enum; and widening the base to
admit MADR's values would put decision vocabulary on every component and
interface, where it is meaningless.

They are also genuinely different facts. A superseded decision can live in a
verified artifact — `status` describes the document, `decision_status` describes
the decision.

So: `status` stays the shared base field; `decision_status` is an ADR-branch
field carrying MADR's enum.

### D5a — `decision_status` selects a nested branch

An `accepted` ADR records a decision that was taken: it must carry a
`chosen_option` and at least two `considered_options`. A `proposed` ADR records
a decision that is still open — by definition nothing has been chosen, and
under D1 the generator may not invent the alternatives nobody has enumerated
yet.

One shape cannot serve both. The adr branch therefore nests a second `if/then`
on `decision_status`, using the same mechanism the schema already uses for
`type`:

| `decision_status` | `chosen_option` | `considered_options` |
| --- | --- | --- |
| `accepted` | required | required, `minItems: 2` |
| `proposed` | must be absent | optional; any length |

This is what makes a deferred ASR expressible without fabrication. The ADR
states the question, its drivers, and whatever options are known — and its
`## Decision Outcome` section says the decision is pending, which is the honest
record. When the decision is later taken, the ADR gains a `chosen_option` and
flips to `accepted`.

`rejected`, `deprecated` and `superseded` are legal in the enum for
hand-authored and later-edited ADRs, and follow the `accepted` shape. The
generator only ever emits `accepted` or `proposed`.

### D6 — The ADR↔artifact edge lives once, on `CMP/IF.traces_to.adr`

The schema already settles this pattern for dependencies: *"The dependency edge
lives once as `CMP.depends_on -> IF.provider` (there is no consumers field)."*

The same rule applies here. `traces_to` is `additionalProperties: false` over
`{adr, diagrams, code, tests}`; there is no `components` key and none is added.
An ADR carries `traces_from` (the requirement IDs that drove the decision) and
names affected components in its Decision Outcome prose. It stores no artifact
ID list, so `traces_to` on an ADR is `{}`.

This keeps STO-102 from having to reconcile two directions of the same edge and
keeps one copy of the fact on disk.

`decision_drivers` does not appear in frontmatter either: it would duplicate
`traces_from` exactly. The `## Decision Drivers` body heading renders those IDs.

## Artifact shape

`.sdlc/design/adr/ADR-001-desktop-runtime-and-ui-shell.md`:

```yaml
---
id: ADR-001
type: adr
title: Desktop runtime and UI shell
description: Which runtime and UI shell the desktop app is built on.
traces_from: [NFR-002, CON-001]
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: 2026-08-03
considered_options: [Tauri, Electron, native view per platform]
chosen_option: Tauri
---
```

Body, with all five headings gated:

```markdown
# ADR-001: Desktop runtime and UI shell

## Context and Problem Statement
## Decision Drivers
## Considered Options
## Decision Outcome
### Consequences
```

Heading gating follows the precedent already set by `assumptions.md` (gated on
`## Assumptions` / `## Dependencies` / `## Open Questions`) and `drivers.md`.
Headings are gated; content never is.

### Field derivation

| ADR field | Source |
| --- | --- |
| `id` | orchestrator-allocated, zero-padded, categorical |
| `status` | always `draft` on generation, matching every other artifact the pipeline emits |
| `traces_from` | `tradeoffs[].affected` |
| `considered_options` | parsed from `tradeoffs[].decision` ("X over Y and Z") |
| `chosen_option` | parsed from `tradeoffs[].decision` |
| `decision_status` | `accepted` for resolved `Q-`; `proposed` for deferred ASR |
| `## Decision Drivers` | `traces_from` IDs, rendered |
| `### Consequences` good | `tradeoffs[].gains` |
| `### Consequences` bad | `tradeoffs[].costs` |
| `confidence` | `low` when the source ASR was `deferred_to_decision`, else `high` |
| `affects` | for every requirement ID in the ADR's `traces_from`, look up the `critique_report.asr_coverage` row whose `requirement_id` matches, and take its `addressed_by`; union those lists across all of `traces_from` |

## Hand-off shapes

`adr-generator` returns:

```yaml
draft_adrs:
  adrs:
    - id: ADR-001
      title: string
      description: string
      traces_from: [NFR-002, CON-001]
      decision_status: accepted | proposed
      confidence: high | medium | low
      considered_options: [string, ...]     # minItems 2 when accepted (D5a)
      chosen_option: string                 # omitted entirely when proposed
      body:
        context: string
        decision_drivers: [string, ...]
        considered_options_detail: [ { option: string, pros: string, cons: string } ]
        decision_outcome: string
        consequences: { good: [string], bad: [string] }
      affects: [CMP-006, IF-002]            # transient — formatter uses it to
                                            # populate traces_to.adr, then drops it
  skipped:
    - { source: "IF-002 async flush", reason: "structural tradeoff, no Q- ID" }
```

`affects` is derived, not judged, and it uses only data Stage 9.5 already
receives — no dispatch-contract change. For every requirement ID in the ADR's
`traces_from`, look up the `critique_report.asr_coverage` row whose
`requirement_id` matches, and take that row's `addressed_by` list; the union
of those lists across every ID in `traces_from` is `affects`. Semantically,
this names the artifacts that address the requirements the decision drove.
The rule is the same for both sources: a deferred ASR's `traces_from` is a
single ID (`[row.requirement_id]`), so its `affects` reduces to that one row's
own `addressed_by` directly.

`affects` is transient in exactly the way `consumed_by` already is in
`draft_interfaces`: the orchestrator/formatter consumes it to back-fill the edge
on the other side and it never reaches disk. This is what keeps D6 true while
still letting the generator, which is the only agent that carries this value
forward, communicate it.

`skipped` exists so a decision that did not become an ADR is visible rather than
silently dropped — the same honesty the example READMEs already practise.

## Files changed

| File | Change |
| --- | --- |
| `agents/adr-generator.md` | **New.** The specialist. |
| `agents/design-orchestrator.md` | Stage 9.5 replaces the Stage 11 slot; dispatch + `draft_adrs` contract; ADR ID allocation |
| `agents/design-formatter.md` | Write `adr/`; populate `traces_to.adr` from `affects`; drop "do not create adr/" |
| `agents/design-critic.md` | `deferred_to_decision` now routes to an ADR, not only a `Q-` |
| `skills/design/schema/design.schema.json` | `ADR` in id pattern and type enum; adr branch with `decision_status`, `considered_options`, `chosen_option`, plus D5a's nested `decision_status` branch |
| `skills/design/scripts/validate_design.py` | `PREFIX_TO_TYPE["ADR"]`; drop `adr` from `SKIP_DIRNAMES`; gate MADR headings |
| `skills/design/SKILL.md` | Remove "this stage does not write ADRs"; document `adr/` |

## Error handling

- **Zero qualifying decisions is legal.** No `adr/` directory is created and the
  run succeeds. This preserves the existing contract that an absent `adr/` is
  expected rather than a bug — it just now means "nothing qualified" instead of
  "not implemented".
- **A malformed `drivers.tradeoffs` entry stops the stage** and reports to the
  orchestrator rather than guessing, matching the Stage 1 rule that an
  architecture built on a half-specified context is the failure being prevented.
- **An unparseable alternative is a skip, not a stub.** If the generator cannot
  recover a second option from a resolved `Q-` entry's `decision` text, the
  entry lands in `skipped` with a reason. Per D1 it must never emit an
  `accepted` ADR with a single considered option — D5a's schema branch enforces
  `minItems: 2` there, so this cannot be violated silently. This applies to
  resolved decisions only: a `proposed` ADR from a deferred ASR is legitimately
  allowed to have no alternatives yet.
- **A non-zero validator exit at Stage 10 re-opens the critique loop**, exactly
  as it does today. ADRs are inside that gate, so a malformed ADR fails the run
  rather than shipping.

## Testing

Extends `skills/design/scripts/tests/`:

- valid ADR fixture (frontmatter + all five headings) passes
- `decision_status` outside the MADR enum fails
- `decision_status: accepted` with one `considered_options` entry fails
  (`minItems: 2` — the D1 guard)
- `decision_status: accepted` with no `chosen_option` fails
- `decision_status: proposed` carrying a `chosen_option` fails (D5a)
- `decision_status: proposed` with no `considered_options` passes — the deferred
  ASR case
- prefix/type mismatch: `ADR-001` declared `type: component` fails
- a missing MADR heading fails
- a component carrying `decision_status` fails (branch isolation, mirroring the
  existing CMP/IF branch tests)
- zero-ADR run: no `adr/` directory, exit 0

**One existing fixture inverts.** `skills/design/scripts/tests/fixtures/valid/adr/ADR-001-single-writer-db.md` currently asserts that the
`adr/` subtree is skipped, and its body says so in prose. That assertion becomes
false under D4. The fixture must be rewritten as a real ADR, and its prose note
removed.

## Out of scope

- **C4 diagrams** (STO-101). `diagrams/` stays in `SKIP_DIRNAMES`.
- **Cross-artifact traceability** (STO-102). This design does not resolve whether
  an ADR's `traces_from` IDs exist — that is STO-102's job, as it already is for
  CMP/IF.
- **Design content linting** (STO-208). No prose-quality check on ADR bodies.
- **Regenerating the worked examples** (STO-219). The tamagotchi set is not
  re-run here; it will gain its three ADRs when STO-219 executes.

## Sequencing note

This ticket edits `skills/design/schema/design.schema.json`, which STO-216 also
needs to change to make `interaction` mixed-mode. Both touch the interface
branch's neighbourhood in the same file. Whichever lands second rebases; they
should not run in parallel.

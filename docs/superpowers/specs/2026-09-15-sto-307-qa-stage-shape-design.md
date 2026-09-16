# QA Stage Shape Adjustments — Design

**Ticket:** STO-307 (M3, third of three)
**Date:** 2026-09-15
**Status:** approved

## Problem

STO-103 built the QA stage and ran it end to end once, against the tamagotchi
worked example. That run produced eleven instruction-level findings. The
blocking ones were fixed inside STO-103; three survived as shape questions,
each needing a decision rather than an edit:

1. `enforcement: none` declares an item unenforced, and the QA stage records
   that nowhere.
2. `functional-test-specialist` authors against `CON-` and `BR-` as well as
   `FR-`, so its name and its contract keys understate its remit.
3. `test_level` has no value for a check that is not executed.

They are one class — places where first contact with a real artifact set showed
the stage's shape to be slightly wrong, in ways only a run could reveal. Two of
the three are resolved here by a different route than the ticket proposes, for
reasons E2 and E5 give.

## Evidence

### E1 — The run, and what it emitted

STO-103's task-9 run produced 31 items over the tamagotchi set: 22
`enforcement: ci`, 6 `manual`, 3 `none`, with all 20 ASRs covered and both
upstream directories verified byte-identical afterwards. The enforcement
counts quoted in this spec are from that run; the verification-method counts in
E6 are from the requirement set it ran against.

### E2 — `enforcement: none` already reaches the DoD, so the ticket's premise is stale

The ticket says the three unenforced items reach nothing and "no artifact
records the three". That was true when it was filed, on 2026-09-07. STO-104
landed five days later and added `render_unenforced()`
(`plugin/skills/requirements/scripts/generate_dod.py:396`), which gives them a
`## Declared Unenforced` section in `.sdlc/definition-of-done.md`, keyed by
item ID with its covers and rationale.

STO-104's spec ruled on the overlap deliberately (D5): "STO-307 proposes
routing unenforced items into the QA stage's `accepted_risks`. That is the
right fix at that stage and stays in that ticket… If STO-307 lands, the two
registers agree and the redundancy is harmless."

So the remaining case is narrower than the ticket's, and it is about
self-containment rather than about nothing existing: `qa-strategy.md` claims
coverage that its own items disclaim, and the QA stage should not depend on a
later stage to be honest about itself.

### E3 — `accepted_risks` is defined as the untested register

`plugin/agents/qa-orchestrator.md:514` introduces it as "the 'what we are not
testing' register", fed at Stage 6.5 from exactly two sources: the critic's
justified `coverage.uncovered_asrs`, and `qa_context.declined_coverage` from
the interview.

An `enforcement: none` item is not that. It *is* tested — a strategy item
exists, with a test design, a level and a risk rationale. What it lacks is a
gate. Feeding it into `accepted_risks` as a third source would make the
register answer two questions at once, and a reader could no longer tell
"nobody wrote a test for this" from "somebody did, and nothing runs it".

### E4 — The seam's contract keys say `functional`; its own prose says `behavioural`

`drivers.md` lists `CON-` and `BR-` artifacts as architecturally significant,
and both the critic's Gate B and `validate_traceability.py`'s `uncovered-asr`
rule demand they be covered. STO-103 assigned them to the functional
specialist rather than adding a third specialist for five artifacts.

The contract keys still carry the pre-run name: `id_block.functional` and
`assigned.functional` (`qa-orchestrator.md:269`, `:350`). The prose four lines
below the second already describes their contents correctly — "a constraint or
a business rule is a behavioural or compliance check over boundaries the
functional specialist already reasons about" (`:353`). The name is the only
part that did not follow the run.

The second cost the ticket names is real: the `performance` and `security`
level guidance sits inside `## Deriving an item from a constraint or a business
rule` (`functional-test-specialist.md:120`), which the FR authoring path never
reads, while `unit`/`integration`/`contract`/`e2e` are defined in the
Authoring-rules bullet above it.

### E5 — The missing enum value already has a workaround, and an upstream vocabulary

`functional-test-specialist.md:148` instructs: "The schema's enum has no value
for a pure inspection or analysis, so where that is all there is, record the
level its executable half runs at and state in the rationale that the static
half has no level of its own."

That silently assumes there is an executable half. A licence constraint or an
architectural rule about which component may touch the network has none.

The vocabulary for saying so exists one stage upstream:
`requirement.schema.json:90` defines `verification_method` as
`test | inspection | analysis | demonstration`, and the CON/BR section already
tells the specialist to read it ("`verification_method` tells you whether an
executable test is even the right answer").

### E6 — Non-executed requirements are a real minority, not a hypothetical

The tamagotchi requirement set carries 22 `verification_method: test`, 3
`inspection` and 1 `analysis`. Those four are precisely the ones the run had to
file under a level implying execution.

### E7 — No QA example set is committed yet

`find docs -type d -name qa` returns nothing: neither published example set
carries a QA stage (tamagotchi has requirements and design, gdpr requirements
alone). STO-309 is the ticket that commits the first QA set. Every schema change here is therefore free of example
regeneration, and stops being free once STO-309 lands.

## Decisions

### D1 — Two registers, not a third feed

`accepted_risks` keeps its meaning and its two feeds, unchanged. The
`qa_context_artifact` gains a fifth list:

```yaml
  unenforced:                  # the "written but not gated" register
    - id: UE-1
      item: TS-014             # the strategy item, not a requirement
      covers: [BR-002]         # the item's traces_from, carried through
      rationale: string        # the item's own risk_rationale
```

Assembled at Stage 6.5 by scanning the approved item set for
`enforcement: none`. Keyed by item ID rather than by requirement, because the
thing being recorded is an item's enforcement status — a single item covering
three requirements is one ungated strategy, not three risks.

No de-duplication against `accepted_risks`. The two registers cannot collide:
a requirement with an item is covered, so it is not an uncovered ASR, and a
requirement the interview declined outright has no item to mark `none`.

### D2 — The register is rendered, and is not a required heading

The formatter renders `unenforced` into `## Declared Unenforced` in
`qa-strategy.md`, one bullet per entry, emitting `None identified` when the
list is empty — the same rule the other four artifact-fed sections follow.

Like those four, it stays out of `REQUIRED_STRATEGY_HEADINGS`
(`validate_qa.py:39`), for the reason `qa-orchestrator.md:550` already gives:
each must be able to be visibly, honestly empty rather than silently missing.

This is the reconciliation STO-104's D5 anticipated. Both registers are keyed
the same way — item ID, covers, rationale — so a reader comparing
`.sdlc/qa/qa-strategy.md` with `.sdlc/definition-of-done.md` sees the same
three items described the same way.

### D3 — `functional-test-specialist` becomes `behavioural-test-specialist`

It names the seam by what unites the three artifact types it authors against:
FRs, constraints and business rules are all assertions about behaviour and
compliance, as against the quality-attribute scenarios its sibling handles. The
pair reads symmetrically — `behavioural-test-specialist` and
`quality-attribute-test-specialist`, each named for the kind of claim it tests.

Thirteen live references update: `qa-orchestrator.md` (4), `qa-critic.md` (3),
`quality-attribute-test-specialist.md` (2), `qa-formatter.md`, the QA
`SKILL.md`, and `site/content/architecture/index.mdx`. The five hits under
`docs/superpowers/` are STO-103's own spec and plan — historical records of
what was built then, and left alone.

### D4 — The contract keys rename with it

`id_block.functional` becomes `id_block.behavioural`, and
`assigned.functional` becomes `assigned.behavioural`. `quality_attribute` is
unchanged in both.

The keys are where the misleading name does its real damage: an orchestrator
sizing `id_block.functional` from the FR count is the arithmetic
`qa-orchestrator.md:275` already warns forces a re-dispatch on the first run.
Renaming the agent while leaving the keys saying `functional` preserves exactly
the misreading the ticket opened with. Both keys live in files this ticket
already edits.

### D5 — Level guidance consolidates into one section both paths read

A new `## Choosing test_level and verification_mode` section in the renamed
agent defines all six levels and all four modes in one place, and both the FR
path and the CON/BR path are pointed at it.

`## Deriving an item from a constraint or a business rule` keeps only what is
genuinely specific to rules: the fit-criterion shape, honouring
`verification_method`, and the `bounds` de-duplication rule. Its rule 3 — the
workaround quoted in E5 — is deleted rather than reworded: D6 removes the
condition it exists to work around.

### D6 — `verification_mode` is a second axis, not new `test_level` values

The item gains:

```yaml
verification_mode: test | inspection | analysis | demonstration
```

`test_level` continues to answer one question — what boundary does this cross —
and `verification_mode` answers the other: is this executed at all.

Adding `inspection` and `analysis` to `test_level` instead, as the ticket
proposes, collapses the two axes: an inspection that enumerates call sites
across two components is genuinely about an `integration` boundary, and under a
single enum it could no longer say so. The two-axis form also reuses a
vocabulary the pipeline already speaks (E5) rather than inventing a second one
that means almost the same thing.

`demonstration` is included, though no finding demanded it, so that a
requirement carrying it upstream can be mirrored rather than forced into
`test`. Adding it later would be a second round of the same churn across the
same five files.

### D7 — `test_level` is optional exactly when the mode is not `test`

`test_level` leaves the schema's `required` list and is reinstated by a
conditional: required when `verification_mode` is `test`, optional otherwise.

Optional, not forbidden. An inspection that enumerates call sites across a
component boundary should still record `integration` and keep that
information; a licence audit with no meaningful boundary omits the field. The
specialists' guidance states the test: record a level when the check is *about*
a boundary, omit it when nothing is being crossed.

`validate_qa.py`'s fallback validator mirrors both the enum and the
conditional, so the two validation paths stay in agreement — the invariant
`tests/qa/test_validate_qa.py` already exists to hold.

### D8 — The critic checks coherence, and stops reading absence as a gap

Two adjustments to `qa-critic.md`:

- The per-item quality gate gains a coherence check: an item whose
  `verification_mode` is `inspection` or `analysis` but whose Test Design
  describes an automated suite is a `revise`, and so is the converse.
- The `coverage.level_gaps` rule (`:199`) must not read a legitimately
  level-less item as an omitted level. A set with no `e2e` items because every
  candidate is verified by inspection is not a gap.

Gate arithmetic is unchanged: `level_gaps` stays advisory and never fails the
gate on its own, exactly as `iso_25010_gaps` is advisory in
`requirements-critic.md`.

### D9 — This lands before STO-309, and no example is regenerated

Per E7 there is no committed QA example set to regenerate. STO-309 commits the
first one, so every ordering where STO-307 follows it pays for a regeneration
this ordering avoids. Nothing in this ticket regenerates
`docs/requirements/examples/`.

## Files touched

**Schema and validation**

- `plugin/skills/qa/schema/qa.schema.json` — add `verification_mode`; remove
  `test_level` from `required`; add the conditional (D6, D7).
- `plugin/skills/qa/scripts/validate_qa.py` — mirror both in the fallback
  validator's `enums` and required-field handling (D7).

**Agents**

- `plugin/agents/functional-test-specialist.md` → `behavioural-test-specialist.md`
  — rename, new `## Choosing test_level and verification_mode` section, rule 3
  deleted, frontmatter `description:` and the body H1 updated (D3, D5, D6).
  `export_agents()` derives the agent's name from its filename and its title
  from that H1 (`site/scripts/export_reference.py:216`), so all three must
  change together for the generated roster to read correctly.
- `plugin/agents/quality-attribute-test-specialist.md` — mode guidance; 2
  sibling references (D3, D6).
- `plugin/agents/qa-orchestrator.md` — `unenforced` in the
  `qa_context_artifact` contract and its Stage 6.5 assembly rule; `id_block`
  and `assigned` key renames; 4 dispatch references (D1, D3, D4).
- `plugin/agents/qa-critic.md` — coherence check, `level_gaps` exemption, 3
  references (D3, D8).
- `plugin/agents/qa-formatter.md` — render `## Declared Unenforced`; level
  grouping gains a trailing group for level-less items; 1 reference (D2, D3).

**Skill and template**

- `plugin/skills/qa/SKILL.md` — the `qa_context_artifact` shape, the rendering
  rule, 1 dispatch reference (D1, D2, D3).
- `plugin/skills/qa/templates/qa-strategy.md` — `## Declared Unenforced`; the
  stated enum order at `:10` gains the trailing group (D2, D6).

**Site**

- `site/content/architecture/index.mdx` — 1 hand-written reference (D3).
- `site/content/_generated/` — regenerated by
  `python3 site/scripts/export_reference.py`, required by CLAUDE.md for the
  frontmatter `description:` change and the schema change.

## Testing

Following the shape `tests/qa/` already uses — one fixture directory per
invalid case, asserted through both the jsonschema and fallback paths:

- `invalid/bad_verification_mode/` — a value outside the four.
- `invalid/missing_test_level_for_test_mode/` — `mode: test` with no
  `test_level`, which the conditional must reject.
- A valid fixture carrying `mode: inspection` with no `test_level`, which both
  paths must accept.
- A valid fixture carrying `mode: inspection` *with* a `test_level`, holding
  D7's "optional, not forbidden" open against a future tightening.

`tests/qa/test_validate_qa.py` gains cases for the conditional in both paths,
and `tests/dod/fixtures/full/qa/strategy/` carries two `TS-` fixtures that need
the new required field. `tests/test_plugin_package.py` needs no edit: it
enumerates shipped directories (`:32`), not agent filenames, so the rename
passes it unchanged.

## Out of scope

- **Regenerating the worked examples.** STO-309 (D9).
- **A third specialist for constraints and business rules.** STO-103 decided
  against it for five artifacts; nothing in the run reopened that.
- **`traces_to.tests`.** Still populated by nothing, per STO-103's second
  global constraint.
- **Any content linter for the QA stage.** STO-103's D8 stands: the validator
  and the traceability checker are the only script-backed gates here.

## Known consequences

- **Two registers describe the same three items.** `qa-strategy.md`'s
  `## Declared Unenforced` and `definition-of-done.md`'s section of the same
  name overlap by design (D2). STO-104's D5 accepted this in advance: the DoD
  stays honest whether or not the QA stage repeats it.
- **`verification_mode` is required on every item, including the 22 that are
  plainly `test`.** The alternative — defaulting it — hides the axis from the
  authoring agents, which is what made the workaround at E5 necessary.
- **The rename breaks any in-flight branch dispatching the old agent name.**
  Only STO-309 is queued behind this, and it has no branch yet.

# QA Strategy Stage — Design

**Ticket:** STO-103 (M3, first of three)
**Date:** 2026-09-06
**Status:** approved

## Problem

M1 turns an interview into a validated requirement set. M2 turns that into an
architecture. Nothing turns either into a test strategy, so the question "how
do we know this works" is answered nowhere in the pipeline, and the two M3
tickets that depend on an answer — STO-104's Definition of Done and STO-105's
traceability graph — have nothing to consume.

The ticket asks for a QA strategy document covering test types and rationale,
scope by component, risk-based prioritisation derived from NFR quality
attribute scenarios, tooling recommendations, and coverage targets, written to
`.sdlc/qa/qa-strategy.md`.

## Evidence

### E1 — `traces_to.tests` is a declared slot that nothing fills

The requirement schema declares `traces_to.tests`, and it is `[]` in all 47
requirement files across both worked example sets. The only check on it is
negative: `validate_traceability.py` rejects a *requirement* ID parked there.

This looked at first like the gap M3 should close. It is not — see D4.

### E2 — No stage writes into a previous stage's directory

`plugin/agents/design-formatter.md` contains no write path under
`.sdlc/requirements/`. The requirement↔design edge is stored once, on the
downstream artifact's `traces_from`, and `validate_traceability.py` walks it
backwards (`check_dangling_reverse_trace`, and the "no component traces_from
this functional requirement" warning) to answer the forward question.

Each stage owns exactly one directory. This is the strongest constraint on the
QA stage's shape and was nearly missed: an earlier sketch of this design had
the QA formatter back-filling `TS-` IDs into requirement files, which would
have made it the first thing in the pipeline to mutate an upstream stage.

### E3 — Document-shaped output has precedent, atomic output has the invariant

`assumptions.md`, `glossary.md`, `drivers.md` and `definition-of-done.md` are
project-level companions: single documents, listed in both validators'
`SKIP_FILENAMES`, not atomic artifacts. So a `qa-strategy.md` is not
unprecedented.

But STO-104 says the DoD pulls "QA coverage gates **from** QA strategy", and
STO-105 walks `FR → component → ADR → test → DoD gate`. Prose is neither a
citable gate nor a graph node.

### E4 — The design interview already elicits the stack, and it lands on disk

`stages.json` records the design interview's six areas: runtime and stack,
persistence, deployment target, integration points, operational constraints,
team constraints. Those answers reach disk as ADRs and `drivers.md` — the
tamagotchi set records its runtime choice in `ADR-003`.

So the QA stage can read the stack rather than re-ask it. What no prior stage
captures: test tooling and any existing suite, what CI can enforce, and
coverage targets or risk appetite.

### E5 — The M2 content linter arrived as its own ticket

STO-208 is titled "design content-quality linter (M2 analogue of STO-136)" and
landed separately from the generation work. That is the precedent for what
belongs in this ticket and what follows it.

## Decisions

### D1 — Atomic `TS-` artifacts, plus the document the ticket asked for

`.sdlc/qa/strategy/TS-<n>-<kebab-title>.md`, one per file, schema-gated, with
`qa-strategy.md` and `index.yaml` as project-level companions beside them.

`qa-strategy.md` is **rendered by the formatter**, not authored: it projects the
emitted TS set into the ticket's five sections — test types and rationale, scope
by component, risk-based prioritisation ordered by `risk_level`, tooling, and
coverage targets — with the last two coming from the interview and the
accepted-risk register from the `qa_context_artifact`. Rendering rather than
authoring is what keeps the document from drifting out of agreement with the
artifacts it summarises, the same reason `generate_c4.py` projects diagrams from
the component graph instead of drawing them.

Rejected: a single prose document (E3 — leaves both downstream tickets with
nothing addressable), and document-now-artifacts-later (that is the shape of
the M1 DoD stub, which STO-104 exists to undo).

### D2 — One artifact type, with risk as fields

`TS-` only. Rejected a second `QR-` quality-risk type: STO-104's gates cite
test scenarios and STO-105's chain names a test node, so neither consumer
addresses a risk artifact. Risk that is *accepted rather than tested* — the one
case a separate type would have served — is recorded in the
`qa_context_artifact`'s accepted-risk register and rendered into
`qa-strategy.md`.

Frontmatter:

```yaml
id: TS-002
type: test_strategy
title: Save integrity under interrupted writes
test_level: integration        # unit | integration | contract | e2e | performance | security
risk_level: high               # high | medium | low
risk_rationale: "Silent corruption is unrecoverable and user-invisible until next load"
enforcement: ci                # ci | manual | none
status: draft
confidence: high
created_at: "YYYY-MM-DD"
traces_from: [NFR-004, CMP-013]
traces_to: {}
scope: project
```

Three things it does not carry, each because the fact already lives somewhere:

- **Thresholds.** `NFR-004` has a `fit_criterion`. The TS says how it is
  measured, never what the number is — the rule `dod-generator.md` already
  states for acceptance criteria ("reference each FR by ID... do not duplicate
  them here").
- **Test code.** Strategy altitude, as components describe responsibility
  without implementation.
- **Coverage targets and tooling.** Project-wide; they belong in
  `qa-strategy.md` rather than repeated across dozens of files.

`enforcement` exists so STO-104 can tell a gate CI actually checks from one a
human must remember. A coverage target nothing enforces is a wish, and the DoD
should not present it as a gate.

### D3 — The edge is stored on the TS artifact only

`TS.traces_from` names the requirement and design IDs it covers. The QA
formatter writes nothing outside `.sdlc/qa/`, per E2.
`validate_traceability.py` resolves the edge backwards, exactly as it already
does for design→requirements.

### D4 — `traces_to.tests` stays empty, and that is correct

It holds **real test file paths**, filled in when code exists — not SDLC
artifact IDs. `TS-` IDs are SDLC artifacts and their edge lives per D3.
Recorded here explicitly because E1 makes the slot look like an M3 gap, and the
next reader will otherwise "fix" it by having the QA stage populate it, which
would violate D3 and E2 at once.

### D5 — A short interview, three areas

Hypothesise first from the two artifact sets and a bounded codebase scan —
proposed test levels, the two or three highest-risk areas drawn from the NFR
quality-attribute scenarios, and a guess at the existing test setup. One
message, confirm or correct.

Then only what E4 shows is missing:

1. **Test tooling and existing suite** — framework, and any suite with
   conventions to match.
2. **What CI can enforce** — decides which gates are real, and populates
   `enforcement`.
3. **Coverage targets and risk appetite** — phrased to make declining easy
   ("which of these are you *not* going to test"), because accepted risk
   recorded is worth more than a coverage number nobody believes.

Rejected: no interview at all (the stage would invent tooling and targets —
the "ask or invent" failure the design stage exists to avoid), and a full
six-area interview (most of it re-asks what E4 shows is already on disk).

### D6 — Five agents, mirroring M1's specialist split

| Stage | Agent | Hand-off |
| --- | --- | --- |
| Dispatch | `qa-orchestrator` | `generation_brief` |
| Collect | `functional-test-specialist`, `quality-attribute-test-specialist` | `draft_test_strategies` |
| Gate | `qa-critic` | `critique_report` |
| Synthesise | `qa-orchestrator` | `qa_context_artifact` |
| Format | `qa-formatter` | `formatter_result` |

The two specialists are the same seam M1 draws between `fr-specialist` and
`nfr-specialist`. Deriving test items from an FR's Gherkin scenarios is
different work from turning an NFR's six-part quality-attribute scenario into a
fitness function, and the second is where the ticket's "risk-based
prioritisation derived from NFR quality attribute scenarios" comes from. Two
producers minting `TS-` IDs require a single allocator, which is why M1 has an
orchestrator.

The orchestrator reads both prior sets once on everyone's behalf (M2 Stage 2's
reason, and more pressing here: four agents would otherwise each re-read two
full sets).

Rejected: three agents with no orchestrator (carves the first exception into
"only an orchestrator mints IDs"), and adding coverage-target/tooling
generators mirroring M2's ADR and C4 generators (those outputs are project-level
prose, not artifacts).

### D7 — Three gates, in the established order

**Entry gate:** `validate_requirements.py`, `validate_design.py`, and
`validate_traceability.py` across the pair. The third is not ceremony — the QA
stage is about to add a third set of edges to that graph, and starting from a
broken graph means the new edges land on sand. Non-zero exit stops the stage.

**Critic gate:** judgment only — per-artifact quality and coverage of the
architecturally significant requirements. It cannot run a structural check
because nothing is on disk yet, the same reason stated in both existing stages.

**Structural gate:** `validate_qa.py` re-run inside the formatter against what
it just wrote, then the extended `validate_traceability.py`. One writer, one
structural gate.

### D8 — One new script; the content linter is a separate ticket

`validate_qa.py` ships here. `lint_qa_content.py` does not: per E5, M2's
content linter was its own ticket, and the M3 analogue should follow that path
rather than inflate this one. The critic applies content checks by inspection
in the meantime, exactly as M1 and M2 did before their linters landed.

`validate_traceability.py` is extended rather than replaced: it gains
QA→(requirements ∪ design) resolution and a warning for an architecturally
significant requirement that no TS covers — the counterpart of its existing "no
component traces_from this functional requirement".

**It stays where it is**, at `plugin/skills/design/scripts/validate_traceability.py`,
despite now spanning three stages. Moving it to `plugin/lib/` would be tidier by
name and would break every path that references it — both `SKILL.md` files, the
design formatter, `export_reference.py`'s rule registry, and the gates page — for
a rename. The precedent is already set in the other direction: the design skill
runs the *requirements* validator as its entry gate, so a stage reaching into a
sibling skill's `scripts/` is established rather than novel. If the name becomes
actively misleading, that is a follow-up rename, not this ticket.

### D9 — The architecture guide grows a third stage in this ticket

`/architecture/`'s stage map stops at the design stage deliberately, and the
rationale page says the map "ends where the built pipeline ends". Landing M3
makes both statements false, so the guide changes here rather than in a
follow-up: a third `PipelineMap`, the new contracts on the contracts page, and
the scope note rewritten.

## Files touched

**Created:** `plugin/agents/qa-orchestrator.md`,
`functional-test-specialist.md`, `quality-attribute-test-specialist.md`,
`qa-critic.md`, `qa-formatter.md`; `plugin/skills/qa/SKILL.md`;
`plugin/skills/qa/schema/qa.schema.json`;
`plugin/skills/qa/scripts/validate_qa.py`;
`plugin/skills/qa/templates/qa-strategy.md`; `tests/qa/`.

**Modified:** `plugin/skills/design/scripts/validate_traceability.py` (QA edge
resolution, uncovered-ASR warning); `plugin/commands/groundwork.md` (the new
workflow); `site/scripts/export_reference.py` (a third stage in
`STAGE_SOURCES`, `PIPELINE_SOURCES`, `SCHEMAS`);
`site/content/architecture/*.mdx` (D9).

**Regenerated:** `agents.json`, `stages.json`, `pipeline.json`, `fields.json` —
all four, which is the largest exporter tax any single ticket has incurred.

## Testing

| Property | How |
| --- | --- |
| Schema accepts a valid TS and rejects each malformed shape | Fixture pairs under `tests/qa/fixtures/`, mirroring `tests/design/` |
| Structural gate catches a bad artifact | `validate_qa.py` against invalid fixtures, one case per rule |
| QA→requirements/design edges resolve; dangling ones fail | `validate_traceability.py` fixtures with a TS naming an unknown ID |
| An ASR no TS covers warns rather than fails | Traceability fixture with an uncovered NFR |
| Generated reference data matches its sources | `export_reference.py --check` |
| Nothing but runtime ships | `tests/test_plugin_package.py`, unchanged and still exact-match |

## Out of scope

- `lint_qa_content.py` — D8, its own ticket.
- Populating `traces_to.tests` — D4; it waits for code to exist.
- The DoD expansion (STO-104) and the traceability graph plus `/sdlc trace`
  (STO-105) — this ticket produces what both consume, and nothing more.
- Worked-example regeneration for the two published sets. They gain a QA stage
  only when someone runs it; that is the M3 analogue of STO-219 and is not
  folded in here.

## Known consequences

The dispatched-agent roster goes from 14 to 19. **STO-247 (token and cost
analysis of the pipeline) is unstarted**, so nobody has measured what the
current 14 cost — adding 36% more agents before that measurement exists is a
real risk this spec names rather than resolves. Sequencing STO-247 ahead of
implementation is a decision for the plan stage, not the design.

`plugin/agents/dod-generator.md` carries a repo-relative template path that
does not resolve from an installed plugin (STO-302). STO-104 owns the fix; this
ticket does not touch that file.

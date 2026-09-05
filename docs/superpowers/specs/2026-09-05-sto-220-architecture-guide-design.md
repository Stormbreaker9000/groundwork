# Architecture Guide — Design

**Ticket:** STO-220 (STO-250 pass 3 of 3)
**Date:** 2026-09-05
**Status:** approved

## Problem

Pass 1 shipped the site and stubbed `/architecture/`. Pass 2 wrote the user
guide and deliberately left that stub alone: its D8 routes every question about
stage order, hand-off contracts and why the pipeline is shaped the way it is
to a page that says "this section is not written yet".

So the pipeline is still described only by the files that implement it,
each describing only itself. You can understand any single agent by reading it.
You cannot understand the system without reading all of them at once and holding
the result in your head.

STO-220 argues this is not tidiness. Three defects found in one day — STO-215's
unreachable structural gate, the identical defect in the same file's Gate C, and
STO-207's omitted project-artifact gates — were one shape: the stated contract
and the actual pipeline order disagreed, and nothing surfaced the disagreement
because no artifact describes the pipeline as a whole. STO-217 is the same story
from the other side: both specialists independently reported capability
granularity as their biggest instructional gap, and neither could see it from
inside its own file.

This pass writes that description, generates the half of it that can be
generated, and gates the generated half against the files it came from.

## Evidence

**The pipeline is 14 dispatched agents, not 13 and not 15.** The ticket says 13;
the pass-1 stub says fifteen; `agents/` holds fifteen files. Seven are dispatched
by `skills/requirements/SKILL.md` and seven by `skills/design/SKILL.md`. The
fifteenth, `agents/requirements-analyst.md`, is referenced by no skill, no agent
and no script — the only mentions in the repository are in
`docs/superpowers/specs/2026-05-05-groundwork-plugin-design.md`, which calls it
"Stub agent for requirements gathering", and the scaffold plan that created it.
The orchestrator pipeline superseded it and the file stayed. `export_agents()`
reads every file in `agents/`, so the published roster advertises it as live.

**The contracts are already structured enough to extract.** Both orchestrators
carry their hand-offs as fenced YAML under `## Stage N — …` headings. Enumerated:

| Orchestrator | Contract stages | Contracts |
|---|---|---|
| requirements | 4, 5, 6, 7 | `generation_brief`, `draft_requirements`, `critique_report`, `formatter_result` |
| design | 5, 6, 8, 9, 10 | `generation_brief`, `draft_components` + `draft_interfaces`, `critique_report`, `design_context_artifact`, `formatter_result` |

**Three shapes defeat a naive extractor**, all found by enumerating the headings
against their YAML rather than assuming:

- Design Stage 6 puts `draft_components` and `draft_interfaces` in a *single*
  fence as two top-level keys, so "the block's top-level key" must mean any
  top-level key in the section, not the first one.
- Design Stage 8's heading names `critique_report`, but the first fenced block
  in its section is `capability_map`; `critique_report` is the second. "First
  block after the heading" extracts the wrong contract.
- Design Stage 7, ``Back-fill `depends_on` ``, backticks a *field* and carries no
  YAML at all. A rule keyed on "the heading contains backticks" raises on a
  stage that was never a contract.

**Transients are already marked in the source.** `required_capabilities`,
`consumed_by` and `satisfies_capabilities` carry inline `# ← TRANSIENT` comments
in the YAML, and design-orchestrator:274 states the rule in prose. The single
most useful thing a contract table can tell a contributor comes free with the
extraction.

**The design orchestrator has retired stages.** `## Stage 11 — (retired)` and
`## Stage 12 — (retired)`. The numbering gap is real and a reader will notice it.

**M3 and M4 do not exist.** STO-103, STO-104 and STO-105 — QA strategy, the full
DoD generator, the traceability graph — are all Backlog, as is every M4 ticket
including this one. The ticket's requested M1 → M2 → M3 → M4 stage map would be
half description and half promise.

## Decisions

### D1 — The stage map ends where the pipeline ends

M1 and M2 only. No M3 or M4 sections, and no roadmap sketch of them. A guide
whose stated contract runs ahead of the code is the exact defect this ticket was
filed about; writing STO-103 as though it ships would reproduce it in the
document meant to prevent it. The map notes that it ends where the built
pipeline ends, and says nothing further.

### D2 — Four pages, split by rot profile

```
architecture/
├── index         the stage map          generated + prose
├── contracts     the hand-off shapes    generated + prose
├── invariants    the cross-cutting rules      prose
└── rationale     the why, and the standards   prose
```

The four areas STO-220 asks for are not four topics, they are two kinds of
content. The stage map and contracts derive from the agent files and are gated
against them; the invariants and the rationale are hand-written and change only
when the design does. Splitting on that seam keeps the drift gate's blast radius
to two pages, and lets a contributor editing an orchestrator see at a glance
which pages can be affected. The granularity also matches `/guide/` next door.

### D3 — `export_pipeline()` joins headings to YAML, and asserts the join

A fifth output, `content/_generated/pipeline.json`, from a new
`export_pipeline()` in `site/scripts/export_reference.py`. It splits each
orchestrator on `^## Stage N — `, and for each section collects every top-level
key across every fenced YAML block in it.

A stage is a **contract stage** when its heading matches the contract form —
``…: the `X` hand-off``, ``…: the `X` / `Y` hand-offs``, or
``Synthesise the `X` `` — and for a contract stage, **every** name backticked in
the heading must appear among that section's YAML top-level keys. When one does
not, the exporter raises.

The assertion is the point. A silent skip would mean that renaming a contract in
the heading but not the YAML quietly shrinks the published table while CI stays
green, because the generated JSON would still match itself. This is pass 2's B2
lesson — `RuleTable` degrading to an error paragraph while `next build` exits 0 —
applied one level up, and it follows house style rather than introducing it:
`test_stages_export_raises_when_the_anchor_moves` already holds the stages
exporter to the same standard.

Recognising the contract form by heading shape, rather than by the presence of
backticks, is what keeps design Stage 7 from raising. Searching the whole
section, rather than the first block, is what makes design Stage 8 extract
`critique_report` instead of `capability_map`. Both are asserted in tests.

### D4 — Retired stages are emitted, not dropped

`retired: true`, rendered as a visible gap with a one-line explanation. Dropping
them silently would leave a reader counting to 10 and finding nothing where 11
and 12 should be, wondering what the document was not telling them. The exporter learns nothing about *why* they
retired; that sentence is hand-written on the index page.

### D5 — Requirements Stage 6.5 gets backticks

`## Stage 6.5 — Synthesize the context artifact` is the M1 sibling of design's
``## Stage 9 — Synthesise the `design_context_artifact` ``, but names its contract
in bare prose, so it fails the contract form and its `context_artifact` block
would not be extracted. The fix is one local edit to the heading — adding the
backticks its sibling already has — rather than widening the extractor to guess
at unmarked contracts. Widening the rule to "any Synthesi[sz]e heading" would
make the extractor's idea of a contract depend on a verb, which is exactly the
kind of implicit coupling this pass exists to remove.

### D6 — Two components render it, and CI greps the built page

`site/components/PipelineMap.jsx` renders the stage order for the index page and
`site/components/ContractTable.jsx` the hand-off shapes for the contracts page,
both from `pipeline.json` and both following the named-export and JSDoc
conventions of `RuleTable` and `AgentTable`. `ContractTable` surfaces the
`# ← TRANSIENT` markers as a first-class column.

It will degrade the way `RuleTable` does if a top-level key goes missing, so
`ci.yml`'s existing built-output block gains one assertion: a known contract name
must appear in `out/architecture/contracts/index.html`. Without it, the page can
empty silently and the build still exits 0.

### D7 — Source claims: fix self-contradiction, file judgment

In scope: correcting a source file that contradicts itself or the code it
describes, where the fix is factual and local. Out of scope: anything requiring a
decision about what the pipeline *should* do — those are filed, and the guide
documents observed behaviour, which is pass 2's rule and the reason STO-269
exists.

`requirements-analyst` is filed, not deleted. Whether it is dead or unwired is a
judgment call about the pipeline, and deleting an agent is not a documentation
change. The guide says fourteen dispatched agents and does not describe it.

### D8 — The exporter tax is documented, not discovered

Pass 2's spec recorded that the exporter taxes unrelated edits: changing an agent
`description:` reddens CI until the exporter is re-run, and pass 2's own D6
extended that to both `SKILL.md` files. `pipeline.json` extends it again, to every hand-off
heading and its YAML. Pass 2 said this "should be stated in the contributor
documentation pass 3 writes rather than discovered". The `invariants` page states
it, with the fixing command. That closes the loop pass 2 opened.

## Files touched

**New**

- `site/content/architecture/index.mdx` — replaces the stub
- `site/content/architecture/contracts.mdx`
- `site/content/architecture/invariants.mdx`
- `site/content/architecture/rationale.mdx`
- `site/content/architecture/_meta.js`
- `site/components/ContractTable.jsx`
- `site/components/PipelineMap.jsx`
- `site/content/_generated/pipeline.json` — generated, committed

**Modified**

- `site/scripts/export_reference.py` — `export_pipeline()`, joins `OUTPUTS`
- `site/scripts/tests/test_export_reference.py`
- `agents/requirements-orchestrator.md` — D5, one heading
- `.github/workflows/ci.yml` — one built-output assertion

**Not modified**

- `pages.yml`. `pipeline.json` joins `OUTPUTS`, so the existing
  `export_reference.py --check` step covers it in both workflows unchanged.

## Testing

| Behaviour | How |
|---|---|
| Join asserts | heading names a contract absent from its section's YAML → raises |
| Multi-name heading | design Stage 6 yields both `draft_components` and `draft_interfaces` |
| Not-the-first-block | design Stage 8 yields `critique_report`, not `capability_map` |
| Field, not contract | design Stage 7 does not raise and emits no contract |
| Retired preserved | Stages 11 and 12 emitted with `retired: true` |
| Coverage | every contract stage in both orchestrators appears in the output |
| Drift | `export_reference.py --check` fails when an orchestrator changes |
| Built output | a contract name appears in the built `architecture/contracts` HTML |

The last is asserted in CI rather than locally, and reported from a real run.

## Out of scope

- **STO-269's five.** Filed by pass 2, unresolved, and each needs its own
  decision. New findings of the same class are filed alongside them.
- **Deleting or wiring `requirements-analyst`.** D7.
- **STO-264's plugin-side renderer**, **STO-257's restructure**, **STO-108's
  devblog post**.
- **M3 and M4.** D1.
- Custom domain, versioned docs, i18n, analytics.

## Known consequence

The generated contract table publishes its source verbatim, so a wrong claim in
an orchestrator's YAML now reaches the site rendered faithfully rather than being
written around. That is STO-269 #4's second-order effect — the stale
`interface-specialist` frontmatter already published on the agent roster — and
this pass widens the surface it applies to. D7 mitigates it for
self-contradictions; it does not mitigate it for a claim that is internally
consistent and simply wrong. Nothing checks the prose of the files that instruct
the agents, and this pass does not change that.

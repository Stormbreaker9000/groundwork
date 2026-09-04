# User Guide — Design

**Ticket:** STO-250 (pass 2 of 3)
**Date:** 2026-09-04
**Status:** approved

## Problem

Pass 1 shipped a deployed site with four pages: a landing page, installation,
a generated rule reference, and a stub owned by STO-220. It also generated
and gated two data files — `fields.json` and `agents.json` — that nothing
renders. The site is live and it teaches almost nothing.

Everything a user needs to run the plugin still exists only inside the skill
and agent files that implement it: what the two interviews ask and why, what
lands in `.sdlc/`, how to read one of the files that lands there, which of
the five checkers owns which failure, and what to do when one of them exits
non-zero. This pass writes that guide, and publishes the worked example sets
alongside it so a reader can see real output rather than a description of it.

STO-220's architecture guide remains pass 3.

## Evidence

**The example sets are 108 atomic artifacts, not 126 files.** Tamagotchi
carries 26 requirements (12 FR, 9 NFR, 3 CON, 2 BR) and 61 design artifacts
(19 CMP, 31 IF, 7 ADR, 4 DIA); gdpr carries 21 requirements (3 FR, 15 NFR,
1 CON, 2 BR). The remainder are project-level artifacts (`assumptions.md`,
`glossary.md`, `definition-of-done.md`, `drivers.md`), pipeline internals
(`clarification-context.yaml`, `critique-report.yaml`, `design-context.yaml`)
and repo-facing prose (`README.md`, `dev-log-followup.md`, `CONSOLIDATED.md`).

**A page per artifact is not browsing.** 108 sidebar entries is a listing, not
navigation. Consolidating by type gives 15 pages carrying the same content,
with heading anchors preserving per-artifact deep links and Nextra's
right-rail table of contents doing the work the sidebar could not. This also
drops the committed generated-file count from roughly 135 to 15, which
removes the repo-noise cost the per-artifact approach would have added on top
of STO-257.

**The repo has already proven that consolidation is wanted, and that hand
-assembling it rots.** `tamagotchi/CONSOLIDATED.md` is 1398 lines rendering
the whole M1 set as one document. STO-219's spec records that it has no
generator behind it — *"No renderer script exists — it is assembled from the
set, and it hard-codes counts and validator results (`22/22 pass`, `10
functional, 7 non_functional, 3 constraint, 2 business_rule`) that all
change"* — and it has needed manual repair twice (`20522b0`, `bf60ed2`). The
plugin-side fix is **STO-264**, filed alongside this spec. This pass is
deliberately site-only so the guide is not blocked on it.

**Nextra compiles `.md` in markdown mode.** `mdxOptions.format` defaults to
`'detect'` (`site/node_modules/nextra/dist/server/schemas.js:27`), and
`compile.js:59` resolves `detect` to `mdx` only for a `.mdx` extension. In
markdown mode `<` and `{` are literal text and no JSX is parsed, so an
artifact body cannot break the build by containing them.

**That hazard is absent from today's corpus and present in the source the
prose pages quote.** A sweep for `<tag>`-shaped and `{ident`-shaped
constructs across every example artifact body returns zero hits. The same
sweep over `skills/requirements/SKILL.md` returns `<title>` (three times),
`<feature-name>`, and `{f`. So `.md` for the generated pages is insurance
rather than a fix for a present defect — nothing keeps the corpus clean, and
STO-219 will regenerate it — while the hand-written pages that quote
`SKILL.md` must put those strings in fenced code blocks, which is ordinary
practice rather than a constraint.

**`validate_traceability.py` has the rule literals but no dispatch table.**
Its nine rule identifiers are string literals inside check bodies
(`rule="dangling-trace"` at line 197, through `rule="duplicate-id"` at 520),
the same shape pass 1 found in the two content linters. Unlike them it
declares no `CHECKS` list, so the corpus-derived sync test pass 1 wrote does
not transfer. The source-derived assertion STO-263 A2 recommends is the only
option here — and is the stronger one.

**Nothing builds the site before merge, and the action pins are several
majors behind.** `ci.yml` runs pytest and the drift check but never
`npm run build`; `pages.yml` never runs on a pull request. Meanwhile
`actions/checkout` is pinned at v4 against a current v7.0.1,
`setup-python` v5 against v7.0.0, `setup-node` v4 against v7.0.0,
`configure-pages` v5 against v6.0.0, and `upload-pages-artifact` v3 against
v5.0.0. Only `deploy-pages@v5` is current. This is STO-263 B1, B2 and B3,
folded in here because adding a second generator and twelve generated pages
makes a green-CI-broken-`main` materially likelier.

## Decisions

### D1 — The guide follows the run, not the artifact taxonomy

Pages are ordered as a user experiences the tool: install, run the
requirements stage, read what came out, run the design stage, understand the
gates, recover when one fails. Reference material is a subsection reached
from links rather than a parallel structure a reader must choose between.

```
guide/
  installation             exists, unchanged
  requirements-stage       NEW
  reading-an-artifact      NEW
  design-stage             NEW
  gates                    NEW
  troubleshooting          NEW
  examples/                NEW, generated
  reference/
    rules                  exists, gains a third table
    fields                 NEW, generated
    agents                 NEW, generated
```

The alternative — a page per artifact type and per tool — is denser and
faster to write, and serves a reader who already knows what they are looking
for. That reader is not the one this pass exists for.

### D2 — The examples are consolidated by type, generated, and committed

`site/scripts/export_examples.py` walks `docs/requirements/examples/` and
emits one page per artifact type per set:

```
guide/examples/tamagotchi/
  requirements/functional          12 FRs      #fr-001 …
  requirements/non-functional       9 NFRs
  requirements/constraints          3 CONs
  requirements/business-rules       2 BRs
  requirements/project-artifacts    assumptions · glossary · DoD
  design/components                19 CMPs
  design/interfaces                31 IFs
  design/adr                        7 ADRs
  design/diagrams                   4 Mermaid views
  design/project-artifacts          assumptions · drivers
guide/examples/gdpr/
  requirements/functional           3 FRs
  requirements/non-functional      15 NFRs
  requirements/constraints          1 CON
  requirements/business-rules       2 BRs
  requirements/project-artifacts    assumptions · glossary · DoD
```

Each artifact contributes an H2 anchored on its ID, a plain-Markdown
metadata table drawn from its frontmatter, and its body verbatim. No artifact
prose is ever hand-written into the site.

Output is `.md`, not `.mdx`, per the evidence above. It is committed and
gated by `--check`, exactly as `_generated/*.json` is: the build stays
Python-free, and the first time the generator's output changes unexpectedly
it changes in a reviewable diff.

**The extension follows authorship.** Generated pages are `.md`, because their
bodies are artifact prose this repo does not author and cannot constrain.
Hand-written pages are `.mdx`, matching the two that already exist. Four of
the five new ones need it outright — `CoverageAreas` on the two stage pages,
`FieldTable` on `reading-an-artifact`, `RuleTable` on `gates` — and JSX
requires MDX mode; `troubleshooting` carries no component today and takes the
same extension so the rule is authorship, not a per-page judgement. The
`<title>` and `<feature-name>` strings these pages quote from `SKILL.md` go in
fenced code blocks, which is where quoted syntax belongs anyway.

### D3 — Cross-references resolve within a set, or render as text

`traces_from`, `depends_on` and `traces_to.design` become relative links to
the anchor of the referenced artifact. An ID that does not resolve inside the
set renders as plain text. A generated page must not emit a broken link;
publishing a dead cross-reference on a page about traceability would be its
own kind of lie.

### D4 — Pipeline internals are excluded

`critique-report.yaml`, `CONSOLIDATED.md`, `dev-log-followup.md` and each
set's `README.md` are not published. The critique report and the dev log are
pass 3's material if they are anyone's; `CONSOLIDATED.md` is the artifact
STO-264 exists to replace, and republishing it here would give a
known-stale document a second, more authoritative home.

`clarification-context.yaml` and `design-context.yaml` are excluded from the
examples tree for the same reason, and quoted in the two stage pages instead,
where the interview that produced them is being explained.

### D5 — `validate_traceability.py` gains a `RULES` registry

The gates page's nine-rule traceability table is the most authoritative-
looking thing this pass publishes, and restating it by hand is exactly the
rot the ticket names. It gets the pass-1 treatment: a declarative `RULES`
list in the module, exported under a third key in `rules.json`, rendered by
the existing `RuleTable` component.

The sync test is **source-derived**, not corpus-derived: it asserts that the
set of `rule="…"` literals in `inspect.getsource(module)` equals
`{r["id"] for r in RULES}`. There is no `CHECKS` list to enumerate, and this
form also closes the declared-and-unexercised gap that STO-263 A2 raises
against the two existing registries. Retrofitting A2 to those two remains
STO-263's work; this pass does not touch their tests.

### D6 — The coverage-area lists are generated; the prose around them is not

`export_reference.py` gains a `stages.json` output carrying the two interviews'
coverage-area names — the six in `skills/requirements/SKILL.md` Phase 4, the
six in `skills/design/SKILL.md` Phase 3 — parsed from the numbered list under
each known heading. A small component renders them.

Scope here is deliberately narrow. Generating the names means the page cannot
list five areas when the skill has six. Generating the *narrative* would turn
the two pages this pass exists to write into tables. The names are structured
and stable; the explanation is prose and stays prose.

### D7 — The rot ledger is explicit

Generated, and therefore incapable of drifting: the rule reference (now three
tables), the field reference, the agent roster, every example page, and the
two coverage-area lists.

Hand-written, and named here as rot candidates:

| Page | Duplicates | Mitigation |
|---|---|---|
| `requirements-stage` | `skills/requirements/SKILL.md` phases | area list generated (D6); prose accepted |
| `design-stage` | `skills/design/SKILL.md` phases | area list generated (D6); prose accepted |
| `gates` | validator exit codes and ownership | traceability rules generated (D5); exit codes accepted, small and stable |
| `reading-an-artifact` | frontmatter semantics | field table from `fields.json`; narrative accepted |
| `troubleshooting` | the STO-218 trap, the stdlib fallback | accepted; stable facts |

"Accepted" means the duplication is known, deliberate, and cheaper than the
machinery that would remove it — not that it is safe.

### D8 — The agent roster is a roster, and points at pass 3

`reference/agents` renders `agents.json` as a flat table: name, title, what it
does. It does not describe stage order, hand-off contracts, or why the
pipeline is shaped the way it is. Every such question links forward to
`/architecture/`. STO-220 then writes that narrative against a section no
other page has claimed.

### D9 — CI builds the site, and asserts the built output

Three changes to the workflows, folded in from STO-263:

- **B1.** A Node-only `build` job in `ci.yml`, running on every pull request.
  No Python step, so the Python-free-build constraint holds.
- **B2.** After that build, assert the output contains what it should:
  `grep -q 'god-component' out/guide/reference/rules/index.html` and the
  equivalent for one example page. This catches `RuleTable`'s silent-degrade
  path, where a missing top-level key in `rules.json` renders an error
  paragraph and still exits 0.
- **B3.** The six action pins move to current. These are major bumps rather
  than the Node-20 warning STO-263 B3 described, so the plan verifies each
  against `actions/starter-workflows`' current `pages/nextjs.yml` and confirms
  on a real run — `upload-pages-artifact` v3→v5 and `configure-pages` v5→v6
  in particular.

## Files touched

**New**

- `site/scripts/export_examples.py` — the examples generator
- `site/scripts/tests/test_export_examples.py`
- `site/content/guide/requirements-stage.mdx`
- `site/content/guide/reading-an-artifact.mdx`
- `site/content/guide/design-stage.mdx`
- `site/content/guide/gates.mdx`
- `site/content/guide/troubleshooting.mdx`
- `site/content/guide/reference/fields.mdx`
- `site/content/guide/reference/agents.mdx`
- `site/content/guide/examples/**` — 15 generated `.md` pages plus `_meta.js`
- `site/content/_generated/stages.json`
- `site/components/FieldTable.jsx`, `AgentTable.jsx`, `CoverageAreas.jsx`

**Modified**

- `skills/design/scripts/validate_traceability.py` — additive `RULES`
- `skills/design/scripts/tests/test_validate_traceability.py` — sync test
- `site/scripts/export_reference.py` — third rules key, `stages.json`
- `site/scripts/tests/test_export_reference.py`
- `site/content/_generated/rules.json`
- `site/content/guide/reference/rules.mdx` — traceability table
- `site/content/index.mdx` — the "Where to go" list
- `site/content/_meta.js`, `site/content/guide/_meta.js`,
  `site/content/guide/reference/_meta.js`
- `.github/workflows/ci.yml` — build job, B2 assertions, action bumps
- `.github/workflows/pages.yml` — action bumps, second `--check`

## Testing

| What | How |
|---|---|
| `RULES` registry, traceability | pytest: `rule="…"` literals in `inspect.getsource()` == `RULES` ids, both directions. Written before the registry exists; must fail first. |
| `export_examples.py` | pytest against the real sets: every artifact reaches a page; ID order preserved; resolvable `traces_from` becomes a link; unresolvable renders as text; output byte-identical across two runs |
| `stages.json` | pytest: the twelve area names match the numbered lists in both `SKILL.md` files |
| Drift gate | both exporters under `--check`, in `ci.yml` and the `pages.yml` build job |
| Site build | Node-only job in `ci.yml`, every PR (B1) |
| Built output | `grep` for a known rule row and a known artifact anchor (B2) |
| Action bumps | a real CI run and a real deploy, green, before the pass is called done (B3) |
| Search | a query for an artifact ID returns its example page on the deployed site |

The last two cannot be asserted from a working tree. They are confirmed after
the first push and reported as observed rather than presumed — the same
standard pass 1 held itself to.

## Out of scope

- **STO-220's architecture guide.** Pass 3.
- **STO-264's plugin-side renderer.** Filed alongside this spec. The
  consolidation logic here stays in `site/scripts/`; if STO-264 lands, the
  site generator becomes a caller and that refactor is STO-264's.
- **STO-263's A-series and C-series.** A2's source-derived assertion is used
  for the *new* registry because it is the only option there; the two
  existing registries are untouched.
- **The devblog post (STO-108).**
- **STO-257**, the repo restructure. D2's consolidation reduces the payload
  this pass adds, but does not address the underlying problem.
- Custom domain, versioned docs, i18n, analytics.

## Known consequence

STO-263 C2 records that the exporter taxes unrelated edits: changing any
agent file's `description:` reddens CI until the exporter is re-run. D6
extends that to both `SKILL.md` files. The behaviour is correct and the
failure names the fixing command, but it is now three classes of file that
trip it, and that should be stated in the contributor documentation pass 3
writes rather than discovered.

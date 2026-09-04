# Docs Site Skeleton — Design

**Ticket:** STO-250 (pass 1 of 3)
**Date:** 2026-09-02
**Status:** approved

## Problem

Groundwork has no user-facing documentation. Everything a user needs to
actually run the plugin — what `/groundwork` asks them, what lands in
`.sdlc/`, how to read an artifact, what to do when a validator exits
non-zero — exists only inside the skill and agent files that implement it.

The README does not attempt it, and is now actively wrong. It documents a
`## Requirements Brief` markdown format that the pipeline has not emitted
since M1; the workflow table lists only `requirements` with no `design` row;
and the roadmap still shows "Architecture design workflow" unchecked, three
months after M2 shipped it.

STO-250 answers two questions STO-220 raised and could not resolve from
inside its own scope — *one document or two?* and *where does it live?* —
with **two documents, one site**. This spec covers only the site and the
machinery that keeps it honest. The guides themselves are later passes.

## Evidence

**The ticket is three independent workstreams.** Site infrastructure, the
user guide, and STO-220's architecture guide share a destination and nothing
else. Specced together they produce one document too large to review or
execute. This pass takes the infrastructure, because it is the only piece
whose central risk — *does Nextra 4 static-export cleanly?* — is unresolved,
and because it is the piece that makes every later page publishable the day
it is written.

**Installing a plugin copies the entire repo.** Verified against the local
plugin cache: `~/.claude/plugins/cache/groundwork-dev/groundwork/0.1.0/`
contains `docs/`, `README.md`, `CLAUDE.md`, `package.json` and `.gitignore`
alongside the four runtime directories. `superpowers`, installed from GitHub,
caches at 2.4M carrying `.github/`, `tests/`, `scripts/` and `assets/`. No
`files`/`exclude`/`ignore` field exists in any `plugin.json` in the cache;
the only lever is the marketplace `source`, which is `"./"` here.

So `site/` will ship to every user. Today's payload is 3.3M across 392
tracked files, of which `docs/` alone is 1.9M and roughly 85% of the total is
not plugin runtime. The site's source is text and adds little next to that.
Fixing the underlying problem is **STO-257**, filed alongside this spec; it
is not a precondition.

**There is no CI.** No `.github/` directory is tracked. The 267 tests have
never run anywhere but a developer's machine. Any claim this spec makes about
a gate failing the build requires CI to exist first, so this pass creates it.

**The linters already have dispatch tables.** `lint_design_content.py:495`
and `lint_requirements_content.py:321` both declare
`CHECKS` / `SET_CHECKS` as lists of check functions, and every check emits a
`lint_core.Finding` carrying `rule`, `severity`, `field` and `message`. The
functions are enumerable by import. The rule identifiers are not: they are
string literals inside the check bodies (`rule="god-component"`,
`rule="ears-conformance"`). That gap is what D5 closes.

**The other two sources are already uniform.** All 15 agent files carry a
frontmatter block with exactly one key, `description:`, and an H1 title —
none declares `name:`, which derives from the filename. Both artifact schemas
are ordinary JSON Schema (`skills/design/schema/design.schema.json`,
`skills/requirements/schema/requirement.schema.json`). Both are mechanically
readable as they stand, with no source changes.

**The toolchain pairing is plausible but unproven.** `nextra@4.6.1` and
`nextra-theme-docs@4.6.1` declare peers `next >=14, react >=18`; latest
`next` is 16.3.4. Local toolchain is Node 22.22.0 / npm 10.9.4. Nextra 4 is
App Router-based. Nothing in the published metadata confirms that
`output: 'export'` produces a working search index under that pairing, and
the ticket is explicit that this must be verified rather than assumed.

## Decisions

### D1 — This pass ships a deployed, green, nearly-empty site

The deliverable is four pages and the machinery behind them, not prose. Three
pages are hand-written and short; the fourth is generated end to end from
repository sources.

Shipping infrastructure against a thin real slice — rather than scaffolding
in the abstract, or writing guides against a toolchain that may not survive
static export — means the version risk is resolved before there is any
content to lose, and the first guide page written in pass 2 is publishable
the moment it exists.

### D2 — `site/` is self-contained; the plugin package is untouched

A Next.js/Nextra app under `site/` with its own `package.json` and
`node_modules`. The root `package.json` — which is the plugin's — gains no
dependencies, and no Next build output lands at the repo root.

`docs/` stays what it is: internal research, specs, plans, and the worked
example artifact sets. The site does not publish it wholesale. Superpowers
specs and plans are process artifacts, not audience documentation, and
pointing Nextra at `docs/` would publish them and force one navigation over
two unrelated audiences.

The site must live in the same working tree as the code it documents,
because D4's exporter reads that code. A separate repository or an orphan
`site` branch would break the rot defense, and both are therefore rejected.

### D3 — GitHub Pages via Actions, at the default project subpath

Deployment is `actions/upload-pages-artifact` + `actions/deploy-pages` on
push to `main`. No `gh-pages` branch.

The site serves from `https://stormbreaker9000.github.io/groundwork/`, which
requires three settings that are individually easy to omit and together
produce a site that works locally and 404s in production:

```js
// site/next.config.mjs
output: 'export',
basePath: '/groundwork',
trailingSlash: true,
images: { unoptimized: true },
```

No custom domain. The ticket's own reasoning applies — one less account in
the loop for an open-source project — and attaching one later is a
`basePath` deletion plus a DNS record.

**Two steps require a human.** The repository's Pages source must be set to
"GitHub Actions" in Settings, and the repository must be public for Pages to
be free. Neither is doable from a working tree.

### D4 — Reference data is exported by Python, rendered by the site

`site/scripts/export_reference.py` imports the real modules and writes JSON
into `site/content/_generated/`:

| Output | Source | Rendered as |
|---|---|---|
| `rules.json` | `CHECKS`/`SET_CHECKS` + `RULES` in both linters | rule id, severity, what it catches |
| `fields.json` | both `*.schema.json` files | frontmatter field tables, enums, required flags |
| `agents.json` | `agents/*.md` frontmatter + H1 | the 15-agent roster and each one's job |

Python rather than JavaScript because it can `import` the linter modules and
read the actual dispatch tables, instead of regexing Python source from
Node. JSON rather than generated MDX because the rendering belongs to the
site and the data belongs to the source; a table's presentation should be
changeable without re-running an exporter.

The generated files are **committed**. That is what makes D6's drift check a
diff rather than a rebuild, and it keeps the site buildable by anyone without
a Python environment.

### D5 — Each linter grows a declarative `RULES` registry, enforced by a test

The exporter cannot recover rule identifiers or severities from the check
functions, because both are literals inside the bodies. So each linter gains:

```python
RULES = [
    {"id": "god-component", "severity": "warn", "summary": "..."},
    ...
]
```

and a pytest assertion that the set of `rule=` values the suite actually
emits and the set of `RULES` ids are equal in both directions.

This is the decision that changes drift from *detected* to *impossible*: a
new check whose rule is missing from the registry fails the existing test
suite before it ever reaches the docs. It is the instinct behind the
structural validators, applied one level up — which is what STO-220 asks for
when it says the guide's contract sections should be generated from, or at
least checked against, the source.

It is also the only change this pass makes to working pipeline code, and it
is additive: no check function changes behaviour.

### D6 — CI exists for the first time, and owns the drift gate

`.github/workflows/ci.yml` runs `python3 -m pytest` on push and pull request
— the 267 tests currently run only locally — and then re-runs the exporter
and fails on `git diff --exit-code site/content/_generated/`.

Published documentation reads as more authoritative than a file in `docs/`,
which makes drift worse here than anywhere else in the project. The gate is
the reason a generated page is worth more than a hand-written one.

`.github/workflows/pages.yml` builds and deploys, and does not duplicate the
test run.

### D7 — Four pages, one of them generated end to end

- `content/index.mdx` — what groundwork is: two stages emitting atomic,
  validated artifacts before code. Two cards. No feature tour.
- `content/guide/installation.mdx` — marketplace add, install, `/groundwork`,
  and what the two skills trigger on.
- `content/guide/reference/rules.mdx` — brief prose plus a table rendered
  from `rules.json`.
- `content/architecture/index.mdx` — a stub naming STO-220 as owner.

`rules.mdx` is the proof obligation for this whole pass: changing a rule's
severity in `lint_design_content.py` must change the published page on the
next push, with no MDX edited. It was chosen over the other two generated
sources because rule tables are the highest-rot-risk content, and because
validating the pipeline should not require anyone to write prose first.

The architecture stub is deliberate. An honest placeholder that names its
owner is better than an empty navigation entry or a page that implies
content exists.

### D8 — README reconciliation is in scope, as a correction and not a rewrite

The README becomes the site's front door and currently contradicts it.
Delete the `## Requirements Brief` block describing output the pipeline no
longer produces, add the `design` row to the workflow table, tick the
roadmap items M2 delivered, and link to the site.

Shipping a site whose entry point states a format the tool does not emit
would reproduce, on day one, exactly the failure mode this pass is built to
prevent. Rewriting the README is not in scope; removing false statements is.

### D9 — The static-export risk has a declared fallback ladder

Verification is task one, before any content exists. If `nextra@4.6.1` with
Next 16 cannot static-export with a working search index: pin Next 15, and
if that also fails, deploy to Vercel, which the ticket names as the
sanctioned fallback and for which the repo already has the integration.

The search index is the specific component most likely not to survive
`output: 'export'`, and is the one to test first.

## Files changed

**New**

- `.github/workflows/ci.yml` — pytest + exporter drift check
- `.github/workflows/pages.yml` — build + deploy to Pages
- `site/package.json`, `site/next.config.mjs`, `site/.gitignore`
- `site/scripts/export_reference.py`
- `site/content/index.mdx`
- `site/content/guide/installation.mdx`
- `site/content/guide/reference/rules.mdx`
- `site/content/architecture/index.mdx`
- `site/content/_generated/{rules,fields,agents}.json` — committed
- `site/scripts/tests/test_export_reference.py` — exporter output shape,
  mirroring the `skills/*/scripts/tests/` convention

**Modified**

- `skills/design/scripts/lint_design_content.py` — add `RULES`
- `skills/requirements/scripts/lint_requirements_content.py` — add `RULES`
- `skills/design/scripts/tests/test_lint_design_content.py` — registry sync
- `skills/requirements/scripts/tests/test_lint_content.py` — registry sync
- `README.md` — per D8

## Testing

| What | How |
|---|---|
| `RULES` registries | pytest, both linters: emitted `rule=` set == `RULES` id set, both directions. Written before the registries exist; must fail first. |
| `export_reference.py` | pytest against the existing `tests/fixtures/lint/*` trees — known input, asserted JSON shape and key set |
| Drift gate | CI re-runs the exporter, `git diff --exit-code` on `_generated/` |
| Static export | `next build` exits 0; `out/` contains all four routes |
| Search index | a query in the deployed site returns a result — the D9 risk, checked explicitly rather than assumed from a green build |
| The deploy | the live URL loads with working navigation and no `basePath` 404s |

The last two cannot be asserted from a working tree. They are confirmed by
loading the deployed site after the first push, and reported as observed
rather than presumed.

## Out of scope

- **The user guide body.** Pass 2.
- **STO-220's architecture guide.** Pass 3; that ticket keeps its content
  scope and this one stops owning the delivery question.
- **The devblog post (STO-108).** Same source material, different artifact,
  different job. Not a section of this site.
- **Rewriting agent or skill files.** The site documents the pipeline; it
  does not become a second copy of it. D5's `RULES` addition is the single
  exception, and is additive.
- **STO-257**, the repo restructure that would stop `docs/` and the site
  shipping to plugin users. Filed, related, not a precondition.
- Custom domain, versioned docs, i18n, analytics.

## Sequencing note

STO-219 is already merged, which resolves the ticket's fourth open question:
the worked examples are stable and can be published without publishing them
twice. They are referenced by pass 2, not this one.

STO-218 — a `README.md` in a `.sdlc/` stage directory fails the validator —
is troubleshooting content the user guide must cover in pass 2. It does not
block this pass.

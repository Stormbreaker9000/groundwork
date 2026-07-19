# M2 Design-Artifact Schema & Structural Validator — Design

**Issue:** STO-197
**Date:** 2026-07-16
**Status:** approved

The M2 analogue of STO-97. Defines the canonical YAML frontmatter contract for atomic
design artifacts — component specs (`CMP-`) and interface specs (`IF-`) — plus a
structural validator, mirroring what STO-97 did for requirements in M1.

Nothing in M2 can be built against a contract that does not exist. STO-99's specialists
have nothing to emit against and STO-102's cross-artifact validator has nothing to check
until this lands. It is the first M2 issue for that reason.

---

## Part A — Settled decisions

Five decisions were taken during brainstorming. They are recorded here with their
reasoning because each one closes off an alternative that will look attractive again
later.

### A.1 `traces_from` is checked for format only

A component's `traces_from` points at *requirement* IDs (`FR-001`), which live in
`.sdlc/requirements/`, not `.sdlc/design/`. The validator asserts the ID *shape* matches
a known requirement prefix and stops there. Whether `FR-001` exists is STO-102's job.

This mirrors M1 exactly: `validate_requirements.py` only resolves IDs *within its own
set*. The design analogue of "within-set" is `depends_on` and `provider`, not
`traces_from`.

**Consequence, accepted:** a typo'd `FR-999` survives until STO-102 runs. Acceptable
because STO-102 is in the same milestone.

**Note:** the STO-197 ticket contradicts itself here — its Deliverables list "no dangling
`traces_from`" as a check while its Boundaries assign design↔requirements validation to
STO-102. This spec resolves that contradiction in favour of the Boundaries. One owner per
edge.

### A.2 `.sdlc/design/` gets `assumptions.md`, and no glossary

Architecture generates its own assumptions ("we assume a single-writer database") that
are not requirements assumptions and have nowhere else to live. ADRs are not that home:
an ADR records a *decision*, and plenty of design assumptions never rise to a decision,
so they would be silently dropped.

The design stage does **not** get its own glossary. It inherits
`requirements/glossary.md`. A second glossary that can redefine `Decay` is the exact
drift STO-135 was built to prevent. Design terms worth defining are components, and
components already carry a `responsibility` field — a better definition of `CMP-003` than
a glossary line.

**Consequence:** the *agents* (STO-99) read `requirements/glossary.md` to inherit
vocabulary. The *validator* does not — consistent with A.1, it never reaches into the
requirements set. The validator gates `assumptions.md` presence only, exactly as M1 does.

### A.3 One schema, shared base plus a per-type branch

M1 uses a single schema for five types because FRs and NFRs genuinely share a shape.
Components and interfaces do not: `responsibility` and `depends_on` are component
concepts; `provider`, `operations`, and `interaction` are interface concepts.

Two separate schemas would drift on the fields they share. One flat schema would make
half its properties meaningless for either type. So: one file, a shared base, and a
branch per type composed in.

### A.4 The dependency edge lives exactly once: `CMP → IF → CMP`

A component declares `depends_on: [IF-…]` — the *contracts it consumes*, never the
components. An interface declares its `provider`. There is **no `consumers` field**;
consumers are derived by reverse lookup.

If both `CMP.depends_on` and `IF.consumers` existed, the same edge would be written twice
and two places can disagree. Same argument as A.1: one owner per edge.

This makes interface specs load-bearing — a dependency *cannot be expressed* without one.
That is more ceremony than "component A uses component B", and the ceremony is the
deliverable. An architecture stage whose interfaces are optional is not specifying
interfaces.

**Consequence:** external systems must *be* components, so `CMP` carries
`boundary: internal | external`. C4 already models external systems as boxes outside the
boundary, so this costs one enum and keeps the graph total.

### A.5 A shared core is extracted; the validators are not duplicated

Of `validate_requirements.py`'s 20 functions, ~6 are requirements-specific. The other
~400 of 613 lines are stage-agnostic scaffolding.

Copying that into `validate_design.py` would duplicate every hard-won edge case — the
STO-134 non-UTF-8 handling, the STO-135 heading anchoring, the PyYAML-absent fallback —
and the second copy will rot, because nobody re-fixes a bug they do not know they have
twice.

This is the same move the glossary work already validated one level down:
`_check_project_artifact` was generalized so two artifacts shared one code path and
STO-134's fix stayed in one place. This is that at file scope.

**Scope discipline:** extract only what is provably identical today. `cross_file_checks`
stays fully per-stage. The shared surface is *parsing and reporting*, not domain logic —
the part least likely to diverge. If M2 later needs different parsing, that is a signal
the extraction was wrong, and un-sharing is easy while de-duplicating is not.

---

## Part B — Directory layout

```
.sdlc/design/
├── components/    CMP-001-<kebab-title>.md
├── interfaces/    IF-001-<kebab-title>.md
├── adr/           ADR-001-<kebab-title>.md   ← STO-100 owns the format
├── diagrams/      <name>.md (mermaid)        ← STO-101 owns the format
├── assumptions.md ← gated: ## Assumptions / ## Dependencies / ## Open Questions
└── index.yaml     ← optional machine index
```

Mirrors `.sdlc/requirements/`. The `.sdlc/<stage>/` convention is already locked across
STO-99, STO-100, STO-101, and STO-103 and is not revisited here.

**IDs:** `^(CMP|IF)(-[A-Z0-9]+)*-[0-9]{3,}$` — M1's pattern with the prefixes swapped, so
the category infix (`CMP-AUTH-004`) carries over for free.

**Discovery** uses M1's skip-list idiom lifted to directories:

- `SKIP_DIRNAMES = {"adr", "diagrams"}`
- `SKIP_FILENAMES = {"assumptions.md", "index.yaml"}`

Everything else under `.sdlc/design/` must parse as a `CMP-` or `IF-` artifact — same as
M1, where anything not skipped must be a requirement. A stray file is an error, not
silently ignored.

---

## Part C — The schema

One `skills/design/schema/design.schema.json`, JSON Schema draft 2020-12.

### C.1 Shared base

| Field | Notes |
| --- | --- |
| `id` | `^(CMP\|IF)(-[A-Z0-9]+)*-[0-9]{3,}$` |
| `type` | `component` \| `interface` |
| `title` | short human-readable, matches the kebab-case filename |
| `description` | one clear statement |
| `traces_from` | requirement IDs this element satisfies; may be empty |
| `traces_to` | `{ adr: [], diagrams: [], code: [], tests: [] }` |
| `status` | copied from M1 unchanged: draft/reviewed/approved/implemented/verified/obsolete |
| `confidence` | copied from M1 unchanged: high/medium/low |
| `created_at` | `YYYY-MM-DD` |
| `scope`, `parent_scope` | RESERVED, mirrors the requirement schema |

`confidence` is copied deliberately: it carries the STO-138 review-queue triage thesis
into M2 rather than reinventing it.

### C.2 Component branch

| Field | Required | Notes |
| --- | --- | --- |
| `responsibility` | yes | the single clear purpose of the unit |
| `boundary` | yes | `internal` \| `external` (see A.4) |
| `depends_on` | yes | `IF-` IDs only; may be empty |

### C.3 Interface branch

| Field | Required | Notes |
| --- | --- | --- |
| `provider` | yes | exactly one `CMP-` ID |
| `operations` | yes | `[{name, summary}]`, minItems 1 |
| `interaction` | yes | `synchronous` \| `asynchronous` |
| `error_modes` | yes | array of strings, minItems 1 |

**Deliberately excluded:** request/response payload schemas, versioning, auth, transport.
Those are code-level or ADR-level. This plugin works at architecture altitude.
`operations` as `{name, summary}` is enough for STO-101 to draw a C4 component diagram
and STO-102 to trace, without writing OpenAPI in YAML.

`error_modes` is retained despite looking like the first thing to cut. This project's own
history argues for it: the first tamagotchi run missing error paths is gap #3 on the dev
log scoreboard. An interface that does not say how it fails is how that gap returns at
the architecture layer.

### C.4 The composition wrinkle — `unevaluatedProperties`

M1 uses `additionalProperties: false` to keep frontmatter strict. **That flag does not
compose through `allOf`/`$ref`** — it only sees properties declared in the same schema
object, so a base-plus-branch schema with `additionalProperties: false` would reject
every component-specific field.

The fix is **`unevaluatedProperties: false` at the top level**, which does see through
composition. Draft 2020-12, already targeted; requires jsonschema 4.x, already required.

**Knock-on:** the stdlib fallback path (`_fallback_validate`, used when jsonschema is not
installed) cannot do composition at all, so it needs its own flat required-field list per
type — the same shape of compromise M1 already made there.

---

## Part D — Validator checks

`skills/design/scripts/validate_design.py`. Hard gate, non-zero exit on any failure —
same contract as M1.

1. Frontmatter parses (shared core)
2. Schema-valid against `design.schema.json`
3. Unique IDs across the set
4. Prefix ↔ type agreement — `CMP-`→`component`, `IF-`→`interface`
5. **`depends_on` resolves** — every `IF-` a component consumes exists in this set
6. **`provider` resolves** — every interface's provider is a known `CMP-` in this set
7. **`traces_from` format only** — shape matches `^(FR|NFR|CON|BR|UC)…` (see A.1)
8. `assumptions.md` present with its three headings (the extracted gate, reused verbatim)

Checks 5 and 6 are the `CMP → IF → CMP` graph closing on itself. They are in scope
precisely because they are *within-set* — the same reason `traces_from` is not.

### D.1 Out of scope — the advisory tier

All of the following are quality concerns, not structural ones. M1 established the
tiering: the hard validator does structure, a content linter does quality.

- **Dependency cycles.** A real architecture smell. Belongs to a design content linter.
- **Orphan interfaces** — an `IF-` nothing depends on. This is precisely
  `glossary-unused`: defined-but-unused is a `warn`, not a gate. Same tier, same
  reasoning.
- **Vague `responsibility` prose** ("handles stuff"). The `vague-qualifier` analogue.

**This tier does not exist in M2 yet.** See Part H.1.

### D.2 Out of scope — directory placement

The STO-197 ticket lists "`.sdlc/design/` layout" as a check. It is deliberately **not**
implemented here, because **M1 does not gate placement either** — an `FR-001` file in
`non-functional/` passes today.

M2 should not be silently stricter than M1. Placement checks should be added to *both*
validators together, so they stay honest mirrors. Filed as **STO-209**.

---

## Part E — The extraction

### E.1 What moves to `lib/artifact_core.py`

`extract_frontmatter_block`, `_strip_inline_comment`, `_coerce_scalar`,
`_stdlib_parse_frontmatter`, `parse_frontmatter`, `_normalize_dates`, `load_schema`,
`validate_against_schema`, `_check_project_artifact`, `print_report`, `discover_files`
(parameterized by the skip sets), and `RequirementFile` generalized to `ArtifactFile`.

### E.2 What stays per-stage

`cross_file_checks`, `default_schema_path`, `_fallback_validate`'s required-field list,
and the artifact gates.

### E.3 Location

**`lib/artifact_core.py` at the repo root**, with a `sys.path` shim in each validator.

`skills/` is where the plugin loader looks for skills; a subdirectory with no `SKILL.md`
may or may not be ignored cleanly, and that is not worth discovering in a user's install.
The root is unambiguous, outside anything the loader scans, and "loose scripts import a
sibling lib" survives the plugin's packaging.

This is plugin **source**: it ships with the plugin, is never gitignored, and is distinct
from plugin *output* (`.sdlc/`, committed in the user's repo) and plugin *state*
(gitignored). Those categories are not conflated.

### E.4 The load-bearing constraint

`validate_requirements.py` **must keep re-exporting every name its tests reach for**:
`PREFIX_TO_TYPE`, `RequirementFile`, `extract_frontmatter_block`, `cross_file_checks`,
`check_context_artifact`, `check_glossary_artifact`, `main`, `default_schema_path` — plus
`GLOSSARY_ARTIFACT`, which `lint_requirements_content.py` imports directly.

The 58 existing tests *are* the safety net for this refactor, and they only work as one if
the module's public surface does not move. Re-export via `from artifact_core import …`;
behavior unchanged.

**If a test needs changing to accommodate the refactor, the refactor changed behavior and
is wrong.**

---

## Part F — Testing

Mirrors M1: `skills/design/scripts/tests/` with a `conftest.py` doing the same `sys.path`
insert, plus `fixtures/valid/` and `fixtures/invalid/`.

**Valid fixture:** two components (one `internal`, one `external`) and one interface
wiring them, so the `CMP → IF → CMP` graph actually closes.

**Invalid cases,** one directory each, mirroring M1's parametrized table:
`missing_required_field`, `bad_enum`, `duplicate_id`, `prefix_type_mismatch`,
`dangling_depends_on`, `dangling_provider`, `traces_from_bad_format`,
`missing_assumptions`, `assumptions_missing_heading`.

Two cases matter more than the rest:

- **`component_field_on_interface`** — asserts `responsibility` on an `IF-` is *rejected*.
  This is the test that proves `unevaluatedProperties` actually composed. Get it wrong and
  the schema silently accepts anything — the exact failure mode the STO-135 heading-anchoring
  mutation test caught: shipped code was right, but nothing would have noticed if it were not.
- **The stdlib fallback path** — M1 degrades gracefully without jsonschema, and the design
  fallback needs its own per-type required lists. Untested, that path rots quietly until
  someone runs the plugin on a machine without the dep.

**The extraction's gate is the existing suite:** all 58 M1 tests stay green and
*unmodified*.

---

## Part G — Sequencing

Three commits, in this order:

1. **Extract the core.** M1 imports it. 58 tests green. **Zero behavior change.** Also
   fixes the stale `_collect_trace_targets` docstring (below).
2. **`design.schema.json` + fixtures.**
3. **`validate_design.py` + its pytest suite.**

Commit 1 is the only one that can break something that already ships, which is why it is
alone.

### G.1 Drive-by fix in commit 1

`_collect_trace_targets`'s docstring claims it cross-checks "`traces_from` and
`traces_to.design` requirement-style entries". The code only collects `traces_from`.

**The code is correct** — `traces_to.design` points at `CMP-`/`IF-` IDs, so checking it
against requirement IDs would flag every design reference as dangling the moment M2 ships.
Only the docstring is wrong, and it is wrong in a way that would mislead whoever builds
STO-102.

---

## Part H — Boundaries

This ticket is **schema + validator only**.

| Not here | Owner |
| --- | --- |
| Agents that emit these files (SKILL.md, orchestrator, specialists) | STO-99 |
| ADR format (MADR 4.0) — we only define that ADRs are referenced via `traces_to.adr` | STO-100 |
| C4 Mermaid diagrams — referenced via `traces_to.diagrams` | STO-101 |
| Cross-artifact validation: `traces_from` resolution, FR coverage, ADR drivers → NFR IDs | STO-102 |
| Cycles, orphan interfaces, vague prose | STO-208 — design content linter |

### H.1 A gap in the milestone

M1 shipped two tiers: a hard structural gate (STO-97) **and** an advisory content linter
(STO-136). M2 has STO-197, 99, 100, 101, 102 — every one structural or generative.

**There is no design content linter.** Nothing owns cycle detection, orphan interfaces, or
vague `responsibility` prose — exactly the class of thing that made the requirements linter
worth building. This design leans on that tier existing; Part D.1 defers to it repeatedly.

Filed as a separate M2 issue. It does not block STO-197.

---

## Deliverables

- `lib/artifact_core.py` — extracted shared core
- `skills/design/schema/design.schema.json` — the contract
- `skills/design/scripts/validate_design.py` — the structural gate
- `skills/design/scripts/tests/` — conftest, fixtures, pytest suite
- `validate_requirements.py` refactored onto the core, public surface unchanged, 58 tests green

## Follow-ups filed

- Directory-placement checks for **both** validators (Part D.2)
- Design content linter — the STO-136 analogue for M2 (Part H.1)

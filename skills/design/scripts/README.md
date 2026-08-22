# Design schema & validators

Structural and cross-artifact validation for Groundwork's atomic design
artifacts.

## Layout
- `../schema/design.schema.json` — JSON Schema (draft 2020-12) for a single
  design artifact's YAML frontmatter (the binding schema contract).
- `validate_design.py` — structural validator: schema, ID/type agreement, the
  `CMP.depends_on -> IF.provider` graph, project artifacts, MADR headings.
- `validate_traceability.py` — cross-artifact validator: resolves the
  requirement↔design edge that neither stage validator checks.
- `tests/` — pytest suite plus `valid/`, `invalid/` and `traceability/`
  fixtures.

## Dependencies

`validate_design.py` needs `pyyaml` and `jsonschema` for full validation and
degrades to a stdlib fallback without them; see
`skills/requirements/scripts/README.md` for the install and fallback details,
which are shared. `validate_traceability.py` does no schema validation, so it
only needs frontmatter parsing — the same fallback applies, and all three
tools print a `reduced (stdlib fallback) mode` warning when it is in use.
Install `pyyaml` anyway: the fallback is a deliberately limited YAML-ish
parser, and this tool's entire job is reading list fields out of frontmatter.

## Structural validator — `validate_design.py`

```bash
# Validate the default location (.sdlc/design):
python3 validate_design.py

# Validate a specific directory:
python3 validate_design.py .sdlc/design

# Only print failures + summary:
python3 validate_design.py --quiet .sdlc/design
```

Exit codes: `0` valid, `1` one or more violations, `2` missing directory or
schema.

## Cross-artifact validator — `validate_traceability.py`

Reads both stage directories at once and resolves the edge between them.
`validate_design.py` checks `traces_from` is requirement-*shaped* but not that
the requirement exists; `validate_requirements.py` excludes `traces_to` from
its dangling-reference sweep. This tool is what closes that gap.

`design_dir` defaults to `.sdlc/design` and `--requirements` defaults to
`.sdlc/requirements`, both resolved relative to the current working
directory (project root, in normal use) — same defaulting convention as
`validate_design.py` above.

```bash
# Validate the default locations (.sdlc/design <-> .sdlc/requirements):
python3 validate_traceability.py

python3 validate_traceability.py .sdlc/design                      # human report
python3 validate_traceability.py --json .sdlc/design               # machine-readable
python3 validate_traceability.py --strict .sdlc/design             # warnings block too
python3 validate_traceability.py --quiet .sdlc/design              # errors + summary only
python3 validate_traceability.py .sdlc/design --requirements other/reqs
```

`--quiet` suppresses the warning lines and keeps every error line, matching
the flag's meaning in `validate_design.py` and `validate_requirements.py`
(both drop PASS lines and keep failures). This is a gate; it never hides what
failed. The summary line still counts the suppressed warnings.

`--json` emits `findings`, `counts`, `skipped` (paths whose frontmatter would
not parse, so the index is incomplete) and `duplicate_ids` (IDs claimed by
more than one file, where only the last one read was indexed). The last two
are also findings in their own right, so they reach the warning count, the
`--strict` exit code and the formatter's hand-off — a caveat carried outside
the findings channel is one that gets dropped at the first boundary, and the
contract downstream reads an empty warning list as proof of a clean sweep.

Every reported line ends with the artifact's path in brackets. Both agent
contracts require the stage to name the offending file, and the formatter runs
this tool without `--json`.

| Rule | Severity | Check |
| --- | --- | --- |
| `dangling-trace` | error | A design artifact's `traces_from` ID resolves to a requirement |
| `adr-driver-unresolved` | error | Requirement IDs *listed* under an ADR's `## Decision Drivers` resolve |
| `dangling-reverse-trace` | error | A non-empty `traces_to.design` resolves to a real design ID |
| `misplaced-requirement-trace` | error | No requirement ID sits in `traces_to.tests` or `traces_to.code` |
| `uncovered-fr` | warn | Every FR (excluding `priority: wont`, `status: obsolete`) is cited by ≥1 component |
| `adr-driver-untraced` | warn | A resolving listed driver absent from that ADR's `traces_from` |
| `adr-driver-unlisted` | warn | A requirement ID in the drivers *prose* that was not checked as a driver |
| `index-unparseable` | warn | A file's frontmatter did not parse, so it is absent from the index |
| `duplicate-id` | warn | Two files claim one ID; only the last was indexed |

A *listed* driver is the leading token of a list item (`- NFR-001: ...`),
which is the only shape `agents/adr-generator.md` emits. Anything else under
the heading is prose and is reported as `adr-driver-unlisted`, never as an
error: a sentence like "supersedes the earlier FR-014 framing" is history, and
hard-failing a stage until an author deletes ordinary English is not a defect
this tool found. The warning exists so a drivers list written as a paragraph
is not silently left unchecked.

`dangling-reverse-trace` and `misplaced-requirement-trace` both fire on the
pre-STO-102 shape, where the constraint specialist's own instructions put
requirement IDs in those three slots. Their messages name the exact edit —
move the edge onto the named requirement's `traces_from`. The fix is a hand
edit in the requirements stage: there is no migration script and no bypass
flag, because a tool that rewrites requirement files from the design stage is
the second writer this pipeline exists to avoid.

Exit codes: `0` no errors, `1` any error (or any warning under `--strict`),
`2` either directory missing. Exit `2` produces no findings — it is an
environment error, not a traceability failure, and the agent contracts route
it separately.

It never schema-validates and never writes. Required fields, enums and ID
shape belong to the two structural validators.

## Running the tests

```bash
pytest skills/design/scripts/tests
```

## Content-quality linter — `lint_design_content.py`

Advisory linter for design *prose and shape* (distinct from the two structural
validators). The M2 analogue of `lint_requirements_content.py`.

```bash
python3 lint_design_content.py .sdlc/design        # human report
python3 lint_design_content.py --json .sdlc/design # machine-readable
python3 lint_design_content.py --strict design     # exit non-zero on error-severity
```

| Rule | Severity | Fires on |
|---|---|---|
| `vague-responsibility` | warn / info | A vague qualifier in a component's `responsibility`; `info` when the sentence carries a number |
| `god-component` | warn | `and`/`or` joining two action verbs in a `responsibility` |
| `orphan-interface` | warn | An `IF-` no component lists in `depends_on` |
| `error-modes-handwaved` | warn | An error mode naming an attitude ("handled gracefully") rather than a failure |
| `adr-consequences-one-sided` | warn | An accepted ADR whose `### Consequences` are all upside |
| `adr-vague-driver` | warn / info | A vague qualifier under `## Decision Drivers`; `info` when the driver line carries a digit |
| `adr-option-unexamined` | info | An option in frontmatter never discussed under `## Considered Options` |
| `dependency-cycle` | warn | A cycle in the `CMP.depends_on → IF.provider → CMP` graph |

Exit codes: `0` always (advisory), except `--strict` returns `1` when an
`error`-severity finding exists, and `2` on a missing directory. No rule emits
`error` today, so `--strict` is currently a no-op.

The `--json` payload matches the M1 linter's: `rule`, `severity`, `artifact_id`,
`field`, `excerpt`, `message`, `suggested_rewrite_hint`. Both linters share
`lib/lint_core.py`.

It reuses `validate_design.discover_files`/`parse_frontmatter`, so it sees
exactly the same atomic artifacts as the structural validator — the
`diagrams/` subtree included, as of STO-101 — and skips the same non-atomic
files (`assumptions.md`, `drivers.md`, `index.yaml`).

## C4 diagram generator — `generate_c4.py`

Projects the already-approved component graph (`CMP.depends_on -> IF.provider`)
into the three C4 views — System Context, Container, and one Component view
per internal container — as a deterministic function of the design set plus
a `draft_diagram_model`. It does not decide anything: container grouping and
actors are the `c4-generator` agent's judgment, supplied as the model; this
script only projects.

```bash
python3 generate_c4.py DESIGN_DIR --model MODEL.json --created-at YYYY-MM-DD
```

`design_dir` defaults to `.sdlc/design`, same convention as the two
validators above. `--model` is required: the path to the `draft_diagram_model`
JSON the `c4-generator` returned. `--created-at` is required too, so every
diagram carries the same date as the rest of the set — there is no default.

Prints a JSON summary on stdout: the diagrams written (`id`, `path`, `level`)
and the `traces_to.diagrams` back-fill the formatter applies to the named
components.

Exit codes: `0` diagrams written, `1` the model contradicts the design set
(re-dispatch to the `c4-generator`, do not repair the model or hand-write a
diagram), `2` environment error (missing `design_dir`, unreadable model) —
not a design failure.

It is normally run by the design formatter, inside its write, after
`drivers.md` (whose `## Architecturally Significant Requirements` section the
Context view's `traces_from` is parsed from) and before `validate_design.py`,
which then runs once over the CMP/IF/ADR files and the diagrams together —
see `agents/design-formatter.md`'s "Diagrams" section. Running it by hand is
mainly useful for regenerating an existing set's views; a design set fully on
disk regenerates the same `DIA-` IDs from the same model, since they are
assigned deterministically from emission order rather than hand-allocated.

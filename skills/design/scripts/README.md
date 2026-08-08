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

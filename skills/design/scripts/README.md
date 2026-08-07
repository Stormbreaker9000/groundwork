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
only needs frontmatter parsing — the same fallback applies.

## Structural validator — `validate_design.py`

```bash
python3 validate_design.py .sdlc/design
python3 validate_design.py --quiet .sdlc/design
```

Exit codes: `0` valid, `1` one or more violations, `2` missing directory or
schema.

## Cross-artifact validator — `validate_traceability.py`

Reads both stage directories at once and resolves the edge between them.
`validate_design.py` checks `traces_from` is requirement-*shaped* but not that
the requirement exists; `validate_requirements.py` excludes `traces_to` from
its dangling-reference sweep. This tool is what closes that gap.

```bash
python3 validate_traceability.py .sdlc/design                      # human report
python3 validate_traceability.py --json .sdlc/design               # machine-readable
python3 validate_traceability.py --strict .sdlc/design             # warnings block too
python3 validate_traceability.py .sdlc/design --requirements other/reqs
```

| Rule | Severity | Check |
| --- | --- | --- |
| `dangling-trace` | error | A design artifact's `traces_from` ID resolves to a requirement |
| `uncovered-fr` | warn | Every FR (excluding `priority: wont`, `status: obsolete`) is cited by ≥1 component |
| `adr-driver-unresolved` | error | Requirement IDs under an ADR's `## Decision Drivers` resolve |
| `adr-driver-untraced` | warn | A resolving body driver absent from that ADR's `traces_from` |
| `dangling-reverse-trace` | error | A non-empty `traces_to.design` resolves to a real design ID |

Exit codes: `0` no errors, `1` any error (or any warning under `--strict`),
`2` either directory missing.

It never schema-validates and never writes. Required fields, enums and ID
shape belong to the two structural validators.

## Running the tests

```bash
pytest skills/design/scripts/tests
```

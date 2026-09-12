# QA schema & validator

Structural validation for Groundwork's atomic QA (test-strategy) artifacts.

## Layout
- `../schema/qa.schema.json` — JSON Schema (draft 2020-12) for a single
  test-strategy file's YAML frontmatter (the binding schema contract).
- `validate_qa.py` — structural validator: schema, ID/type agreement, ID
  uniqueness, and the project-level `qa-strategy.md` companion.
- `tests/` (at `tests/qa` — see STO-257) — pytest suite plus `valid/` and
  `invalid/` fixtures.

## Dependencies

`validate_qa.py` needs `pyyaml` and `jsonschema` for full validation:

```bash
pip install pyyaml jsonschema
# or, without a virtualenv:
python3 -m pip install --user pyyaml jsonschema
```

If they are missing, the validator degrades to a stdlib-only fallback that
does required-field, enum, `traces_from` non-emptiness, and unknown-field
checks (no full JSON Schema validation, including no `id` pattern check) and
prints an install hint — the same reduced mode `validate_requirements.py` and
`validate_design.py` carry.

## Usage

```bash
# Validate the default location (.sdlc/qa):
python3 validate_qa.py

# Validate a specific directory:
python3 validate_qa.py path/to/qa

# Point at an explicit schema (default: ../schema/qa.schema.json):
python3 validate_qa.py --schema path/to/qa.schema.json path/to/qa

# Only print failures + summary:
python3 validate_qa.py --quiet path/to/qa
```

Exit codes: `0` all files valid, `1` one or more validation errors, `2` usage
error (missing directory).

This tool deliberately does not resolve `traces_from`: those IDs live in the
requirements and design sets, which it does not read. `validate_traceability.py`
owns every cross-directory edge, so that resolution stays in one place instead
of being duplicated here.

## Running the tests

```bash
pytest tests/qa
```

## The Definition of Done generator lives elsewhere

`generate_dod.py`, which projects this stage's artifacts (along with
requirements and design) into `.sdlc/definition-of-done.md`, is not in this
directory. It lives at
`../../requirements/scripts/generate_dod.py`, because it reads all three
stages and the requirements skill is the earliest one; see that skill's
`scripts/README.md` for its usage.

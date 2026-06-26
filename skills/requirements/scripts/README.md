# Requirements schema & validator

Structural validation for Groundwork's atomic requirement artifacts.

## Layout
- `../schema/requirement.schema.json` — JSON Schema (draft 2020-12) for a single
  requirement file's YAML frontmatter (the binding schema contract).
- `validate_requirements.py` — CLI validator/linter.
- `tests/` — pytest suite + `valid/` and `invalid/` fixtures.

## Dependencies
Full validation uses two third-party packages:

```bash
pip install pyyaml jsonschema
# or, without a virtualenv:
python3 -m pip install --user pyyaml jsonschema
```

If they are missing, the validator degrades to a stdlib-only fallback that does
required-field, enum, and cross-file checks (no full JSON Schema validation) and
prints an install hint.

## Usage
```bash
# Validate the default location (.sdlc/requirements):
python3 validate_requirements.py

# Validate a specific directory:
python3 validate_requirements.py path/to/requirements

# Point at an explicit schema (default: ../schema/requirement.schema.json):
python3 validate_requirements.py --schema path/to/requirement.schema.json path/to/reqs

# Only print failures + summary:
python3 validate_requirements.py --quiet path/to/reqs
```

Exit codes: `0` = all valid, `1` = validation errors, `2` = usage error
(missing dir/schema).

## What it checks
Per file (via JSON Schema): field presence (required vs optional), types, enums,
the `id` pattern, `created_at` date format, and `ears_pattern` required only when
`type: functional`.

Cross-file (set level): globally unique IDs; `id` prefix matches `type`
(FR→functional, NFR→non_functional, CON→constraint, BR→business_rule,
UC→use_case); `traces_from` references resolve to known requirement IDs (no
dangling); functional requirements declare an `ears_pattern`.

`definition-of-done.md` and `index.yaml` are skipped.

## Tests
```bash
pytest skills/requirements/scripts/tests
```

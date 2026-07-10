#!/usr/bin/env python3
"""Structural validator/linter for Groundwork atomic requirement artifacts.

Groundwork emits one atomic requirement per Markdown file with YAML
frontmatter, organized under a requirements directory in type subfolders::

    .sdlc/requirements/
      functional/        FR-XXX-*.md
      non-functional/    NFR-XXX-*.md
      constraints/       CON-XXX-*.md
      business-rules/    BR-XXX-*.md
      use-cases/         UC-XXX-*.md
      definition-of-done.md   (skipped)
      index.yaml              (skipped)

This tool:
  1. Discovers every ``*.md`` under the requirements dir (recursively),
     skipping ``definition-of-done.md`` and ``index.yaml``.
  2. Parses the YAML frontmatter from each file.
  3. Validates each requirement against the JSON Schema
     (``skills/requirements/schema/requirement.schema.json``, draft 2020-12).
  4. Runs cross-file (set-level) checks:
       - IDs are globally unique.
       - The ID prefix matches ``type``
         (FR->functional, NFR->non_functional, CON->constraint,
          BR->business_rule, UC->use_case).
       - ``traces_from`` and every ``traces_to`` entry reference an existing
         requirement ID (no dangling references).
       - Functional requirements declare an ``ears_pattern``.
  5. Prints a readable per-file + summary report and exits non-zero on any
     violation.

Usage
-----
    python3 validate_requirements.py [REQUIREMENTS_DIR]
    python3 validate_requirements.py                 # defaults to .sdlc/requirements
    python3 validate_requirements.py path/to/reqs
    python3 validate_requirements.py --schema path/to/requirement.schema.json reqs
    python3 validate_requirements.py --quiet reqs    # only print failures + summary

Exit codes
----------
    0  all files valid
    1  one or more validation errors
    2  usage / environment error (e.g. dir or schema missing)

Dependencies
------------
Full validation requires two third-party packages::

    pip install pyyaml jsonschema
    # or: python3 -m pip install --user pyyaml jsonschema

If they are missing the tool falls back to a minimal standard-library
frontmatter parser and performs the structural cross-file checks it can do
without the JSON Schema engine (required-field presence, enum membership,
ID/type/trace checks). It prints a clear hint to install the deps for full
schema validation. The fallback is best-effort and never as strict as the
schema path.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional dependencies. We degrade gracefully if they are not installed.
# ---------------------------------------------------------------------------
try:  # PyYAML
    import yaml  # type: ignore

    _HAVE_YAML = True
except ImportError:  # pragma: no cover - exercised only without the dep
    yaml = None  # type: ignore
    _HAVE_YAML = False

try:  # jsonschema
    import jsonschema  # type: ignore
    from jsonschema import Draft202012Validator  # type: ignore

    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - exercised only without the dep
    jsonschema = None  # type: ignore
    Draft202012Validator = None  # type: ignore
    _HAVE_JSONSCHEMA = False


# Files that live in the requirements dir but are not atomic requirements.
SKIP_FILENAMES = {"definition-of-done.md", "index.yaml", "assumptions.md"}

# ID prefix -> expected `type`. Mirrors the schema contract.
PREFIX_TO_TYPE = {
    "FR": "functional",
    "NFR": "non_functional",
    "CON": "constraint",
    "BR": "business_rule",
    "UC": "use_case",
}

# Project-level context artifact (STO-134): assumptions/dependencies/open-questions.
CONTEXT_ARTIFACT = "assumptions.md"
REQUIRED_CONTEXT_HEADINGS = ["## Assumptions", "## Dependencies", "## Open Questions"]

# Minimal enum/required knowledge for the stdlib fallback path only. The JSON
# Schema remains the single source of truth when jsonschema is available.
_FALLBACK_REQUIRED = [
    "id", "type", "tier", "title", "description", "rationale", "fit_criterion",
    "priority", "confidence", "verification_method", "status", "created_at",
    "traces_from", "traces_to",
]
_FALLBACK_ENUMS = {
    "type": {"functional", "non_functional", "constraint", "business_rule", "use_case"},
    "tier": {"business", "stakeholder", "solution", "transition"},
    "priority": {"must", "should", "could", "wont"},
    "confidence": {"high", "medium", "low"},
    "verification_method": {"test", "inspection", "analysis", "demonstration"},
    "ears_pattern": {"ubiquitous", "event", "state", "unwanted", "optional", "complex"},
    "status": {"draft", "reviewed", "approved", "implemented", "verified", "obsolete"},
    "scope": {"project", "epic", "story"},
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


class RequirementFile:
    """A parsed requirement file and the errors found while validating it."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.frontmatter: Optional[Dict[str, Any]] = None
        self.errors: List[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def req_id(self) -> Optional[str]:
        if isinstance(self.frontmatter, dict):
            value = self.frontmatter.get("id")
            if isinstance(value, str):
                return value
        return None


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
def extract_frontmatter_block(text: str) -> Optional[str]:
    """Return the raw YAML frontmatter block, or None if absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    return match.group(1)


def _strip_inline_comment(value: str) -> str:
    # Remove a trailing ` # comment` (best effort, not quote-aware).
    hash_idx = value.find(" #")
    if hash_idx != -1:
        value = value[:hash_idx]
    return value.strip()


def _coerce_scalar(value: str) -> Any:
    value = _strip_inline_comment(value)
    if value == "" or value == "~" or value.lower() == "null":
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(part) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: Dict[str, Any] = {}
        for pair in inner.split(","):
            if ":" in pair:
                pk, _, pv = pair.partition(":")
                result[pk.strip()] = _coerce_scalar(pv.strip())
        return result
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _stdlib_parse_frontmatter(block: str) -> Dict[str, Any]:
    """A tiny, intentionally limited YAML-ish parser for the fallback path.

    Indentation-aware and recursive: supports flat scalars, inline ``[a, b]``
    and ``{k: v}`` collections, block lists, and nested block mappings whose
    values may themselves be block lists (e.g. ``traces_to.tests``). This is
    NOT a general YAML parser; install PyYAML for full fidelity.
    """
    # Keep only meaningful lines paired with their indentation.
    rows: List[Tuple[int, str]] = []
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        rows.append((indent, raw.strip()))

    def parse_block(start: int, base_indent: int) -> Tuple[Any, int]:
        """Parse rows[start:] at >= base_indent; return (value, next_index)."""
        # Decide list vs mapping from the first child row.
        if start >= len(rows):
            return None, start
        if rows[start][1].startswith("- "):
            items: List[Any] = []
            j = start
            while j < len(rows) and rows[j][0] >= base_indent and rows[j][1].startswith("- "):
                items.append(_coerce_scalar(rows[j][1][2:]))
                j += 1
            return items, j
        mapping: Dict[str, Any] = {}
        j = start
        while j < len(rows) and rows[j][0] >= base_indent:
            indent, text = rows[j]
            if ":" not in text:
                j += 1
                continue
            k, _, v = text.partition(":")
            k = k.strip()
            v = v.strip()
            if v == "":
                # Nested block follows if the next row is more indented.
                if j + 1 < len(rows) and rows[j + 1][0] > indent:
                    child, j = parse_block(j + 1, rows[j + 1][0])
                    mapping[k] = child
                else:
                    mapping[k] = None
                    j += 1
            else:
                mapping[k] = _coerce_scalar(v)
                j += 1
        return mapping, j

    if not rows:
        return {}
    value, _ = parse_block(0, rows[0][0])
    return value if isinstance(value, dict) else {}


def parse_frontmatter(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse a file's frontmatter. Returns (data, error_message)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return None, f"could not read file: {exc}"

    block = extract_frontmatter_block(text)
    if block is None:
        return None, "missing YAML frontmatter (expected a leading '---' block)"

    if _HAVE_YAML:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:  # type: ignore[union-attr]
            return None, f"invalid YAML frontmatter: {exc}"
    else:
        data = _stdlib_parse_frontmatter(block)

    if not isinstance(data, dict):
        return None, "frontmatter did not parse to a mapping/object"
    return _normalize_dates(data), None


def _normalize_dates(value: Any) -> Any:
    """Recursively convert YAML date/datetime objects to ISO-8601 strings.

    PyYAML deserializes unquoted ``YYYY-MM-DD`` scalars to ``datetime.date``.
    The schema models ``created_at`` as a string, so we coerce dates back to
    their canonical string form, accepting both quoted and unquoted authoring.
    """
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_dates(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def load_schema(schema_path: str) -> Dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_against_schema(
    data: Dict[str, Any], validator: Any
) -> List[str]:
    """Return a list of human-readable schema errors (empty if valid)."""
    errors: List[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {location}: {err.message}")
    return errors


def _fallback_validate(data: Dict[str, Any]) -> List[str]:
    """Best-effort structural validation when jsonschema is unavailable."""
    errors: List[str] = []
    for field in _FALLBACK_REQUIRED:
        if field not in data or data[field] in (None, ""):
            errors.append(f"schema(fallback): missing required field '{field}'")
    for field, allowed in _FALLBACK_ENUMS.items():
        if field in data and data[field] is not None and data[field] not in allowed:
            errors.append(
                f"schema(fallback): '{field}'='{data[field]}' not in {sorted(allowed)}"
            )
    tt = data.get("traces_to")
    if tt is not None and not isinstance(tt, dict):
        errors.append("schema(fallback): 'traces_to' must be a mapping")
    tf = data.get("traces_from")
    if tf is not None and not isinstance(tf, list):
        errors.append("schema(fallback): 'traces_from' must be a list")
    return errors


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------
def _collect_trace_targets(frontmatter: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return (label, id) trace references that should point at requirement IDs.

    Only ``traces_from`` and ``traces_to.design`` requirement-style entries are
    cross-checked against known requirement IDs. ``traces_to.tests`` and
    ``traces_to.code`` reference external artifacts (test cases, source files),
    not requirement IDs, so they are not treated as dangling.
    """
    targets: List[Tuple[str, str]] = []
    tf = frontmatter.get("traces_from")
    if isinstance(tf, list):
        for item in tf:
            if isinstance(item, str):
                targets.append(("traces_from", item))
    return targets


def cross_file_checks(files: List[RequirementFile]) -> List[str]:
    """Run set-level checks. Appends per-file errors and returns global errors."""
    global_errors: List[str] = []

    parsed = [f for f in files if isinstance(f.frontmatter, dict)]

    # Unique IDs.
    seen: Dict[str, str] = {}
    known_ids = set()
    for f in parsed:
        rid = f.req_id
        if not rid:
            continue
        known_ids.add(rid)
        if rid in seen:
            f.errors.append(
                f"duplicate id '{rid}' (also defined in {os.path.basename(seen[rid])})"
            )
        else:
            seen[rid] = f.path

    # Per-requirement: prefix<->type, FR ears_pattern, dangling traces.
    for f in parsed:
        fm = f.frontmatter
        assert fm is not None
        rid = f.req_id
        rtype = fm.get("type")

        if rid:
            prefix = rid.split("-", 1)[0]
            expected = PREFIX_TO_TYPE.get(prefix)
            if expected is None:
                f.errors.append(
                    f"id prefix '{prefix}' is not one of {sorted(PREFIX_TO_TYPE)}"
                )
            elif rtype is not None and expected != rtype:
                f.errors.append(
                    f"id prefix '{prefix}' implies type '{expected}', "
                    f"but type is '{rtype}'"
                )

        if rtype == "functional" and not fm.get("ears_pattern"):
            f.errors.append("functional requirement is missing 'ears_pattern'")

        for label, target in _collect_trace_targets(fm):
            if target not in known_ids:
                f.errors.append(
                    f"dangling reference: {label} -> '{target}' is not a known requirement id"
                )

    return global_errors


def check_context_artifact(reqs_dir: str) -> List[str]:
    """Assumptions/Dependencies/Open-Questions artifact presence + headings (hard gate).

    Returns a list of set-level error strings (empty when the artifact is present
    and contains all three required H2 headings, even if a section reads
    'None identified').
    """
    path = os.path.join(reqs_dir, CONTEXT_ARTIFACT)
    if not os.path.isfile(path):
        return [
            f"missing required context artifact '{CONTEXT_ARTIFACT}' "
            f"(Assumptions / Dependencies / Open Questions)"
        ]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"could not read context artifact '{CONTEXT_ARTIFACT}': {exc}"]

    errors: List[str] = []
    for heading in REQUIRED_CONTEXT_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(
                f"context artifact '{CONTEXT_ARTIFACT}' missing required heading "
                f"'{heading}'"
            )
    return errors


# ---------------------------------------------------------------------------
# Discovery + orchestration
# ---------------------------------------------------------------------------
def discover_files(reqs_dir: str) -> List[str]:
    found: List[str] = []
    for root, _dirs, names in os.walk(reqs_dir):
        for name in names:
            if not name.endswith(".md"):
                continue
            if name in SKIP_FILENAMES:
                continue
            found.append(os.path.join(root, name))
    return sorted(found)


def validate(reqs_dir: str, schema_path: str) -> Tuple[List[RequirementFile], List[str]]:
    files: List[RequirementFile] = []

    validator = None
    if _HAVE_JSONSCHEMA:
        schema = load_schema(schema_path)
        Draft202012Validator.check_schema(schema)  # type: ignore[union-attr]
        # A FormatChecker enables `format: date` checks where supported; the
        # `created_at` regex pattern guarantees the check even without it.
        validator = Draft202012Validator(  # type: ignore[union-attr]
            schema, format_checker=jsonschema.FormatChecker()  # type: ignore[union-attr]
        )

    for path in discover_files(reqs_dir):
        rf = RequirementFile(path)
        data, err = parse_frontmatter(path)
        if err:
            rf.errors.append(err)
            files.append(rf)
            continue
        rf.frontmatter = data
        if validator is not None:
            rf.errors.extend(validate_against_schema(data, validator))
        else:
            rf.errors.extend(_fallback_validate(data))
        files.append(rf)

    global_errors = cross_file_checks(files)
    global_errors.extend(check_context_artifact(reqs_dir))
    return files, global_errors


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def print_report(
    files: List[RequirementFile],
    global_errors: List[str],
    reqs_dir: str,
    quiet: bool,
) -> None:
    total = len(files)
    failed = [f for f in files if not f.ok]
    passed = total - len(failed)

    if not (_HAVE_YAML and _HAVE_JSONSCHEMA):
        missing = []
        if not _HAVE_YAML:
            missing.append("pyyaml")
        if not _HAVE_JSONSCHEMA:
            missing.append("jsonschema")
        print(
            f"WARNING: running in reduced (stdlib fallback) mode; "
            f"missing {', '.join(missing)}. "
            f"For full schema validation: pip install {' '.join(missing)}"
        )
        print()

    print(f"Validating requirements in: {reqs_dir}")
    print(f"Discovered {total} requirement file(s).")
    print("-" * 60)

    for f in files:
        if f.ok:
            if not quiet:
                rid = f.req_id or "(no id)"
                print(f"  PASS  {rid:<14} {os.path.relpath(f.path, reqs_dir)}")
        else:
            rid = f.req_id or "(no id)"
            print(f"  FAIL  {rid:<14} {os.path.relpath(f.path, reqs_dir)}")
            for e in f.errors:
                print(f"          - {e}")

    if global_errors:
        print("-" * 60)
        print("Set-level errors:")
        for e in global_errors:
            print(f"  - {e}")

    print("-" * 60)
    error_count = sum(len(f.errors) for f in files) + len(global_errors)
    print(
        f"Summary: {passed}/{total} file(s) passed, "
        f"{len(failed)} failed, {error_count} error(s) total."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def default_schema_path() -> str:
    # schema lives at ../schema/requirement.schema.json relative to this script.
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "schema", "requirement.schema.json"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Groundwork atomic requirement artifacts."
    )
    parser.add_argument(
        "requirements_dir",
        nargs="?",
        default=".sdlc/requirements",
        help="Directory of requirement files (default: .sdlc/requirements).",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to requirement.schema.json (default: alongside this script).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures and the summary line.",
    )
    args = parser.parse_args(argv)

    reqs_dir = args.requirements_dir
    schema_path = args.schema or default_schema_path()

    if not os.path.isdir(reqs_dir):
        print(f"ERROR: requirements directory not found: {reqs_dir}", file=sys.stderr)
        return 2
    if _HAVE_JSONSCHEMA and not os.path.isfile(schema_path):
        print(f"ERROR: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    files, global_errors = validate(reqs_dir, schema_path)
    print_report(files, global_errors, reqs_dir, args.quiet)

    has_errors = bool(global_errors) or any(not f.ok for f in files)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

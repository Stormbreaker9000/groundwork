#!/usr/bin/env python3
"""Structural validator for Groundwork QA artifacts (STO-103).

Gates .sdlc/qa/ the way validate_design.py gates .sdlc/design/: schema
conformance per file, ID uniqueness and prefix/type agreement across the set,
and the presence of the project-level qa-strategy.md with its five headings.

Deliberately does NOT resolve traces_from. Those targets live in the
requirements and design sets, which this tool does not read —
validate_traceability.py owns every cross-directory edge, and duplicating that
here would create a second place for the same rule to drift.

Stdlib only, like every other script in this repository.

Usage
-----
    python3 validate_qa.py .sdlc/qa
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
_LIB_DIR = os.path.join(_PLUGIN_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import artifact_core as core  # noqa: E402
from artifact_core import ArtifactFile, parse_frontmatter  # noqa: E402

STRATEGY_ARTIFACT = "qa-strategy.md"
SKIP_FILENAMES = {STRATEGY_ARTIFACT, "index.yaml"}
SKIP_DIRNAMES: set = set()

REQUIRED_STRATEGY_HEADINGS = [
    "## Test Levels and Rationale",
    "## Scope by Component",
    "## Risk-Based Prioritisation",
    "## Tooling",
    "## Coverage Targets",
]

# One prefix, one type. The QA stage emits a single artifact type; this dict
# exists so the prefix/type agreement check has a single source, matching the
# other two validators rather than hard-coding the pair at the call site.
PREFIX_TO_TYPE = {"TS": "test_strategy"}


class QAFile(ArtifactFile):
    """One QA artifact file plus the errors found in it."""

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.frontmatter: Optional[Dict[str, Any]] = None

    @property
    def qa_id(self) -> Optional[str]:
        if isinstance(self.frontmatter, dict):
            value = self.frontmatter.get("id")
            return value if isinstance(value, str) else None
        return None


def _fallback_validate(data: Dict[str, Any]) -> List[str]:
    """Schema checks that survive without jsonschema installed.

    The primary path is the real schema; this is the same degraded mode the
    other two validators carry, and it covers required-field presence and the
    three enums rather than pretending to be complete.
    """
    errors: List[str] = []
    required = (
        "id", "type", "title", "description", "test_level", "risk_level",
        "risk_rationale", "enforcement", "traces_from", "traces_to",
        "status", "confidence", "created_at",
    )
    for field in required:
        if field not in data:
            errors.append(f"missing required field '{field}'")

    enums = {
        "test_level": {"unit", "integration", "contract", "e2e", "performance", "security"},
        "risk_level": {"high", "medium", "low"},
        "enforcement": {"ci", "manual", "none"},
        "status": {"draft", "approved", "obsolete"},
        "confidence": {"high", "medium", "low"},
        "scope": {"project", "epic", "story"},
    }
    for field, allowed in enums.items():
        value = data.get(field)
        if value is not None and value not in allowed:
            errors.append(f"'{field}' is '{value}', not one of {sorted(allowed)}")

    traces_from = data.get("traces_from")
    if isinstance(traces_from, list) and not traces_from:
        errors.append("traces_from is empty; a strategy item must cover something")

    known = set(required) | {"scope", "parent_scope"}
    for field in sorted(set(data) - known):
        errors.append(f"unexpected field '{field}'")
    return errors


def cross_file_checks(files: List[QAFile]) -> List[str]:
    """Set-level checks. Appends per-file errors and returns global errors."""
    global_errors: List[str] = []
    parsed = [f for f in files if isinstance(f.frontmatter, dict)]

    seen: Dict[str, str] = {}
    for f in parsed:
        qid = f.qa_id
        if not qid:
            continue
        if qid in seen:
            f.errors.append(
                f"duplicate id '{qid}' (also defined in {os.path.basename(seen[qid])})"
            )
        else:
            seen[qid] = f.path

    for f in parsed:
        fm = f.frontmatter
        assert fm is not None
        qid = f.qa_id
        if not qid:
            continue
        prefix = qid.split("-", 1)[0]
        expected = PREFIX_TO_TYPE.get(prefix)
        if expected is None:
            f.errors.append(
                f"id prefix '{prefix}' is not one of {sorted(PREFIX_TO_TYPE)}"
            )
        elif fm.get("type") is not None and expected != fm.get("type"):
            f.errors.append(
                f"id prefix '{prefix}' implies type '{expected}', "
                f"but type is '{fm.get('type')}'"
            )
    return global_errors


def check_strategy_artifact(qa_dir: str) -> List[str]:
    """The qa-strategy.md companion (hard gate).

    Presence plus the five headings, gated by the shared core. Content is never
    gated: a section reading 'None identified' is legal and passes, the same
    standard assumptions.md and drivers.md are held to.
    """
    return core._check_project_artifact(
        qa_dir,
        STRATEGY_ARTIFACT,
        REQUIRED_STRATEGY_HEADINGS,
        "qa strategy artifact",
        "Test Levels and Rationale / Scope by Component / Risk-Based "
        "Prioritisation / Tooling / Coverage Targets",
    )


def discover_files(qa_dir: str) -> List[str]:
    """Every QA artifact ``*.md`` under ``qa_dir`` (companions skipped)."""
    return core.discover_files(qa_dir, SKIP_FILENAMES, SKIP_DIRNAMES)


def validate(qa_dir: str, schema_path: str) -> Tuple[List[QAFile], List[str]]:
    files: List[QAFile] = []
    validator = core.make_validator(schema_path)

    for path in discover_files(qa_dir):
        qf = QAFile(path)
        data, err = parse_frontmatter(path)
        if err:
            qf.errors.append(err)
            files.append(qf)
            continue
        qf.frontmatter = data
        if validator is not None:
            qf.errors.extend(core.validate_against_schema(data, validator))
        else:
            qf.errors.extend(_fallback_validate(data))
        files.append(qf)

    global_errors = cross_file_checks(files)
    global_errors.extend(check_strategy_artifact(qa_dir))
    return files, global_errors


def default_schema_path() -> str:
    return os.path.normpath(
        os.path.join(_HERE, "..", "schema", "qa.schema.json")
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Groundwork QA artifacts."
    )
    parser.add_argument(
        "qa_dir", nargs="?", default=".sdlc/qa",
        help="Directory of QA files (default: .sdlc/qa).",
    )
    parser.add_argument("--schema", default=None, help="Override the schema path.")
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-file PASS lines; errors and the summary always print.",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.qa_dir):
        print(f"error: no such directory: {args.qa_dir}", file=sys.stderr)
        return 2

    files, global_errors = validate(args.qa_dir, args.schema or default_schema_path())
    core.print_report(files, global_errors, args.qa_dir, args.quiet, noun="qa artifact")

    has_errors = bool(global_errors) or any(not f.ok for f in files)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

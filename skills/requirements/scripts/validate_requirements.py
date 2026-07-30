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
       - ``traces_from`` references an existing requirement ID (no dangling
         references).
       - Functional requirements declare an ``ears_pattern``.
  5. Prints a readable per-file + summary report and exits non-zero on any
     violation.

The stage-agnostic machinery (frontmatter parsing, the stdlib fallback parser,
schema validation, project-artifact gating, discovery, reporting) lives in
``lib/artifact_core.py`` and is shared with the M2 design validator. Only the
requirement-specific cross-file checks and fallback field lists live here.

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
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Shared core lives at the repo root in ``lib/``; add it to the path before
# importing. Resolved relative to this file, so cwd does not matter.
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import artifact_core as core  # noqa: E402
from artifact_core import (  # noqa: E402  (re-exported for tests/linter)
    ArtifactFile,
    extract_frontmatter_block,
    parse_frontmatter,
)


# Files that live in the requirements dir but are not atomic requirements.
SKIP_FILENAMES = {
    "definition-of-done.md", "index.yaml", "assumptions.md", "glossary.md",
}

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

# Project-level glossary artifact (STO-135): the shared vocabulary anchor that keeps
# downstream stages (M2 architecture, M3 QA) from drifting on terminology.
GLOSSARY_ARTIFACT = "glossary.md"
REQUIRED_GLOSSARY_HEADINGS = ["## Terms"]

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


class RequirementFile(ArtifactFile):
    """A parsed requirement file. ``req_id`` reads the generic ``artifact_id``."""

    @property
    def req_id(self) -> Optional[str]:
        return self.artifact_id


# ---------------------------------------------------------------------------
# Schema validation (fallback path — requirement-specific field knowledge)
# ---------------------------------------------------------------------------
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
    """Return (label, id) trace references that must point at requirement IDs.

    Only ``traces_from`` is cross-checked against known requirement IDs. Every
    ``traces_to`` sub-list references external artifacts — design IDs
    (``traces_to.design``), test cases (``traces_to.tests``), or source files
    (``traces_to.code``) — none of which are requirement IDs, so they are not
    treated as dangling here. Design<->requirement resolution is M2's job.
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
    """Assumptions/Dependencies/Open-Questions artifact (hard gate)."""
    return core._check_project_artifact(
        reqs_dir,
        CONTEXT_ARTIFACT,
        REQUIRED_CONTEXT_HEADINGS,
        "context artifact",
        "Assumptions / Dependencies / Open Questions",
    )


def check_glossary_artifact(reqs_dir: str) -> List[str]:
    """Glossary artifact (hard gate). An empty 'None identified' Terms section passes."""
    return core._check_project_artifact(
        reqs_dir,
        GLOSSARY_ARTIFACT,
        REQUIRED_GLOSSARY_HEADINGS,
        "glossary artifact",
        "Terms",
    )


# ---------------------------------------------------------------------------
# Discovery + orchestration
# ---------------------------------------------------------------------------
def discover_files(reqs_dir: str) -> List[str]:
    """Every requirement ``*.md`` under ``reqs_dir`` (project companions skipped)."""
    return core.discover_files(reqs_dir, SKIP_FILENAMES)


def validate(reqs_dir: str, schema_path: str) -> Tuple[List[RequirementFile], List[str]]:
    files: List[RequirementFile] = []

    validator = core.make_validator(schema_path)

    for path in discover_files(reqs_dir):
        rf = RequirementFile(path)
        data, err = parse_frontmatter(path)
        if err:
            rf.errors.append(err)
            files.append(rf)
            continue
        rf.frontmatter = data
        if validator is not None:
            rf.errors.extend(core.validate_against_schema(data, validator))
        else:
            rf.errors.extend(_fallback_validate(data))
        files.append(rf)

    global_errors = cross_file_checks(files)
    global_errors.extend(check_context_artifact(reqs_dir))
    global_errors.extend(check_glossary_artifact(reqs_dir))
    return files, global_errors


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
    if core.HAVE_JSONSCHEMA and not os.path.isfile(schema_path):
        print(f"ERROR: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    files, global_errors = validate(reqs_dir, schema_path)
    core.print_report(files, global_errors, reqs_dir, args.quiet, noun="requirement")

    has_errors = bool(global_errors) or any(not f.ok for f in files)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

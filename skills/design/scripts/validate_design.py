#!/usr/bin/env python3
"""Structural validator for Groundwork atomic design artifacts.

Groundwork's M2 design stage emits one atomic artifact per Markdown file with
YAML frontmatter, organized under a design directory::

    .sdlc/design/
      components/    CMP-XXX-*.md
      interfaces/    IF-XXX-*.md
      adr/           ADR-XXX-*.md   (skipped — STO-100 owns the format)
      diagrams/      *.md           (skipped — STO-101 owns the format)
      assumptions.md                (gated: Assumptions/Dependencies/Open Questions)
      index.yaml                    (skipped)

This tool:
  1. Discovers every ``*.md`` under the design dir (recursively), skipping the
     ``adr/`` and ``diagrams/`` subtrees and the ``assumptions.md``/``index.yaml``
     companions.
  2. Parses the YAML frontmatter from each file.
  3. Validates each artifact against the JSON Schema
     (``skills/design/schema/design.schema.json``, draft 2020-12).
  4. Runs cross-file (set-level) checks:
       - IDs are globally unique.
       - The ID prefix matches ``type`` (CMP->component, IF->interface).
       - ``depends_on`` resolves: every interface a component consumes exists
         in this set.
       - ``provider`` resolves: every interface's provider is a known component
         in this set.
       - ``traces_from`` entries are requirement-SHAPED (FR/NFR/CON/BR/UC…);
         their existence in .sdlc/requirements/ is the cross-artifact
         validator's job (STO-102), not this one.
  5. Gates the project-level ``assumptions.md`` (presence + three headings).
  6. Prints a readable per-file + summary report and exits non-zero on any
     violation.

The stage-agnostic machinery (frontmatter parsing, stdlib fallback, schema
validation, project-artifact gating, discovery, reporting) is shared with the
M1 requirements validator via ``lib/artifact_core.py``. Only the
design-specific cross-file checks and fallback field lists live here.

Usage
-----
    python3 validate_design.py [DESIGN_DIR]
    python3 validate_design.py                 # defaults to .sdlc/design
    python3 validate_design.py path/to/design
    python3 validate_design.py --schema path/to/design.schema.json design
    python3 validate_design.py --quiet design  # only print failures + summary

Exit codes
----------
    0  all files valid
    1  one or more validation errors
    2  usage / environment error (e.g. dir or schema missing)

Dependencies
------------
Full validation requires ``pyyaml`` and ``jsonschema``. Without them the tool
falls back to a minimal stdlib parser and a best-effort, per-type structural
check (never as strict as the schema path); it prints a hint to install them.
"""
from __future__ import annotations

import argparse
import os
import re
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
from artifact_core import (  # noqa: E402  (re-exported for tests)
    ArtifactFile,
    extract_frontmatter_block,
    parse_frontmatter,
)


# Whole subtrees another stage owns in a non-artifact format.
SKIP_DIRNAMES = {"adr", "diagrams"}
# Companions that live in the design dir but are not atomic artifacts.
SKIP_FILENAMES = {"assumptions.md", "index.yaml"}

# ID prefix -> expected `type`. Mirrors the schema contract.
PREFIX_TO_TYPE = {
    "CMP": "component",
    "IF": "interface",
}

# Project-level assumptions artifact (design analogue of M1's context artifact).
# Design does NOT get its own glossary — it inherits requirements/glossary.md
# (STO-135), and this validator never reaches into the requirements set.
ASSUMPTIONS_ARTIFACT = "assumptions.md"
REQUIRED_ASSUMPTIONS_HEADINGS = ["## Assumptions", "## Dependencies", "## Open Questions"]

# traces_from points at requirement IDs. We check the SHAPE only; resolution is
# STO-102's job. This mirrors the requirement schema's id pattern.
REQUIREMENT_ID_RE = re.compile(r"^(FR|NFR|CON|BR|UC)(-[A-Z0-9]+)*-[0-9]{3,}$")

# Minimal per-type required/enum knowledge for the stdlib fallback path only.
# The JSON Schema is the single source of truth when jsonschema is available;
# unevaluatedProperties composition cannot be reproduced here, hence the flat
# per-type lists (design.schema.json C.4 knock-on).
_FALLBACK_REQUIRED_BASE = [
    "id", "type", "title", "description", "traces_from", "traces_to",
    "status", "confidence", "created_at",
]
_FALLBACK_REQUIRED_BY_TYPE = {
    "component": ["responsibility", "boundary", "depends_on"],
    "interface": ["provider", "operations", "interaction", "error_modes"],
}
_FALLBACK_ENUMS = {
    "type": {"component", "interface"},
    "boundary": {"internal", "external"},
    "interaction": {"synchronous", "asynchronous"},
    "confidence": {"high", "medium", "low"},
    "status": {"draft", "reviewed", "approved", "implemented", "verified", "obsolete"},
    "scope": {"project", "epic", "story"},
}


class DesignFile(ArtifactFile):
    """A parsed design artifact. ``design_id`` reads the generic ``artifact_id``."""

    @property
    def design_id(self) -> Optional[str]:
        return self.artifact_id

    @property
    def artifact_type(self) -> Optional[str]:
        if isinstance(self.frontmatter, dict):
            value = self.frontmatter.get("type")
            if isinstance(value, str):
                return value
        return None


# ---------------------------------------------------------------------------
# Schema validation (fallback path — design-specific, per-type field knowledge)
# ---------------------------------------------------------------------------
def _fallback_validate(data: Dict[str, Any]) -> List[str]:
    """Best-effort structural validation when jsonschema is unavailable.

    Required-field presence is per-type because the schema's branch is not
    reproducible without jsonschema's unevaluatedProperties support.
    """
    errors: List[str] = []
    required = list(_FALLBACK_REQUIRED_BASE)
    branch = _FALLBACK_REQUIRED_BY_TYPE.get(data.get("type"))
    if branch:
        required.extend(branch)
    for field in required:
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
def cross_file_checks(files: List[DesignFile]) -> List[str]:
    """Run set-level checks. Appends per-file errors and returns global errors."""
    global_errors: List[str] = []

    parsed = [f for f in files if isinstance(f.frontmatter, dict)]

    # Unique IDs, and the by-type id sets the graph checks resolve against.
    seen: Dict[str, str] = {}
    component_ids = set()
    interface_ids = set()
    for f in parsed:
        did = f.design_id
        if not did:
            continue
        if did in seen:
            f.errors.append(
                f"duplicate id '{did}' (also defined in {os.path.basename(seen[did])})"
            )
        else:
            seen[did] = f.path
        if f.artifact_type == "component":
            component_ids.add(did)
        elif f.artifact_type == "interface":
            interface_ids.add(did)

    for f in parsed:
        fm = f.frontmatter
        assert fm is not None
        did = f.design_id
        dtype = fm.get("type")

        # Prefix <-> type agreement.
        if did:
            prefix = did.split("-", 1)[0]
            expected = PREFIX_TO_TYPE.get(prefix)
            if expected is None:
                f.errors.append(
                    f"id prefix '{prefix}' is not one of {sorted(PREFIX_TO_TYPE)}"
                )
            elif dtype is not None and expected != dtype:
                f.errors.append(
                    f"id prefix '{prefix}' implies type '{expected}', "
                    f"but type is '{dtype}'"
                )

        # depends_on resolves to a known interface (CMP -> IF edge).
        depends_on = fm.get("depends_on")
        if isinstance(depends_on, list):
            for target in depends_on:
                if isinstance(target, str) and target not in interface_ids:
                    f.errors.append(
                        f"dangling depends_on -> '{target}' is not a known interface id"
                    )

        # provider resolves to a known component (IF -> CMP edge).
        provider = fm.get("provider")
        if isinstance(provider, str) and provider not in component_ids:
            f.errors.append(
                f"dangling provider -> '{provider}' is not a known component id"
            )

        # traces_from is checked for requirement-shape only (STO-102 resolves).
        traces_from = fm.get("traces_from")
        if isinstance(traces_from, list):
            for target in traces_from:
                if isinstance(target, str) and not REQUIREMENT_ID_RE.match(target):
                    f.errors.append(
                        f"traces_from -> '{target}' is not a requirement-shaped id "
                        f"(expected FR/NFR/CON/BR/UC-###)"
                    )

    return global_errors


def check_assumptions_artifact(design_dir: str) -> List[str]:
    """Assumptions/Dependencies/Open-Questions artifact (hard gate).

    The design analogue of M1's context artifact, gated by the shared core.
    An honest 'None identified' section is legal — content is never gated.
    """
    return core._check_project_artifact(
        design_dir,
        ASSUMPTIONS_ARTIFACT,
        REQUIRED_ASSUMPTIONS_HEADINGS,
        "assumptions artifact",
        "Assumptions / Dependencies / Open Questions",
    )


# ---------------------------------------------------------------------------
# Discovery + orchestration
# ---------------------------------------------------------------------------
def discover_files(design_dir: str) -> List[str]:
    """Every design artifact ``*.md`` under ``design_dir`` (companions/subtrees skipped)."""
    return core.discover_files(design_dir, SKIP_FILENAMES, SKIP_DIRNAMES)


def validate(design_dir: str, schema_path: str) -> Tuple[List[DesignFile], List[str]]:
    files: List[DesignFile] = []

    validator = core.make_validator(schema_path)

    for path in discover_files(design_dir):
        df = DesignFile(path)
        data, err = parse_frontmatter(path)
        if err:
            df.errors.append(err)
            files.append(df)
            continue
        df.frontmatter = data
        if validator is not None:
            df.errors.extend(core.validate_against_schema(data, validator))
        else:
            df.errors.extend(_fallback_validate(data))
        files.append(df)

    global_errors = cross_file_checks(files)
    global_errors.extend(check_assumptions_artifact(design_dir))
    return files, global_errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def default_schema_path() -> str:
    # schema lives at ../schema/design.schema.json relative to this script.
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "schema", "design.schema.json"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Groundwork atomic design artifacts."
    )
    parser.add_argument(
        "design_dir",
        nargs="?",
        default=".sdlc/design",
        help="Directory of design files (default: .sdlc/design).",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to design.schema.json (default: alongside this script).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures and the summary line.",
    )
    args = parser.parse_args(argv)

    design_dir = args.design_dir
    schema_path = args.schema or default_schema_path()

    if not os.path.isdir(design_dir):
        print(f"ERROR: design directory not found: {design_dir}", file=sys.stderr)
        return 2
    if core.HAVE_JSONSCHEMA and not os.path.isfile(schema_path):
        print(f"ERROR: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    files, global_errors = validate(design_dir, schema_path)
    core.print_report(files, global_errors, design_dir, args.quiet, noun="design artifact")

    has_errors = bool(global_errors) or any(not f.ok for f in files)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

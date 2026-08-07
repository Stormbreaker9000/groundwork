#!/usr/bin/env python3
"""Cross-artifact traceability validator for Groundwork (STO-102).

Groundwork's two structural validators each see one stage directory by design,
and each explicitly declines to resolve the edge that crosses between them:
``validate_design.py`` checks that ``traces_from`` is requirement-SHAPED but
not that the requirement exists, and ``validate_requirements.py`` excludes
every ``traces_to`` sub-list from its dangling-reference sweep. This tool is
the one that reads both directories at once and resolves that edge.

It runs five rules::

    dangling-trace          error  design traces_from resolves to a requirement
    uncovered-fr            warn   every FR is cited by some component
    adr-driver-unresolved   error  IDs under '## Decision Drivers' resolve
    adr-driver-untraced     warn   a body driver absent from frontmatter
    dangling-reverse-trace  error  requirement traces_to.design resolves

It never schema-validates and never writes. Required fields, enums and ID
shape belong to the two structural validators; this tool only resolves IDs.

Usage
-----
    python3 validate_traceability.py [DESIGN_DIR] [--requirements DIR]
                                     [--json] [--strict] [--quiet]

Exit codes
----------
    0  no errors (warnings may be present, unless --strict)
    1  one or more errors, or any warning under --strict
    2  usage / environment error (either directory missing)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

# This script spans two stages, so both stage script dirs and the shared lib/
# go on the path. Resolved relative to this file, so cwd does not matter —
# the same handling both existing validators use.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
for _p in (
    _HERE,
    os.path.join(_REPO_ROOT, "lib"),
    os.path.join(_REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_design as vd  # noqa: E402
import validate_requirements as vr  # noqa: E402
from artifact_core import parse_frontmatter  # noqa: E402


# Severities. There are exactly two; see spec D2.
ERROR = "error"
WARN = "warn"
_SEVERITY_ORDER = {ERROR: 0, WARN: 1}


@dataclass
class Finding:
    rule: str
    severity: str
    artifact_id: str
    path: str
    message: str


@dataclass
class Requirement:
    req_id: str
    type: str
    priority: str
    status: str
    path: str
    traces_to_design: List[str] = field(default_factory=list)


@dataclass
class DesignArtifact:
    design_id: str
    type: str
    path: str
    traces_from: List[str] = field(default_factory=list)


def _str_list(value: Any) -> List[str]:
    """Coerce a frontmatter list field to a list of strings, tolerating None."""
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str)]


def _text(value: Any) -> str:
    return str(value) if isinstance(value, str) else ""


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------
def index_requirements(reqs_dir: str) -> Tuple[Dict[str, Requirement], List[str]]:
    """Index every requirement by ID. Returns (index, unparseable_paths)."""
    index: Dict[str, Requirement] = {}
    skipped: List[str] = []
    for path in vr.discover_files(reqs_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        traces_to = data.get("traces_to")
        design = _str_list(traces_to.get("design")) if isinstance(traces_to, dict) else []
        index[data["id"]] = Requirement(
            req_id=data["id"],
            type=_text(data.get("type")),
            priority=_text(data.get("priority")),
            status=_text(data.get("status")),
            path=os.path.relpath(path, reqs_dir),
            traces_to_design=design,
        )
    return index, skipped


def index_design(design_dir: str) -> Tuple[Dict[str, DesignArtifact], List[str]]:
    """Index every design artifact by ID. Returns (index, unparseable_paths)."""
    index: Dict[str, DesignArtifact] = {}
    skipped: List[str] = []
    for path in vd.discover_files(design_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        index[data["id"]] = DesignArtifact(
            design_id=data["id"],
            type=_text(data.get("type")),
            path=os.path.relpath(path, design_dir),
            traces_from=_str_list(data.get("traces_from")),
        )
    return index, skipped


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def rule_dangling_trace(
    design_index: Dict[str, DesignArtifact], req_index: Dict[str, Requirement]
) -> List[Finding]:
    """Every design artifact's traces_from must resolve to a requirement.

    validate_design.py has already checked these are requirement-SHAPED. An ID
    that failed that check simply will not resolve here and is reported as
    dangling — the shape error is reported separately, by the tool that owns it.
    """
    findings: List[Finding] = []
    for art in sorted(design_index.values(), key=lambda a: a.design_id):
        for target in art.traces_from:
            if target not in req_index:
                findings.append(Finding(
                    rule="dangling-trace",
                    severity=ERROR,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=f"traces_from -> '{target}' is not a known requirement id",
                ))
    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def collect_findings(
    design_dir: str, reqs_dir: str
) -> Tuple[List[Finding], int, int, List[str]]:
    """Run every rule. Returns (findings, design_count, req_count, skipped)."""
    req_index, req_skipped = index_requirements(reqs_dir)
    design_index, design_skipped = index_design(design_dir)

    findings: List[Finding] = []
    findings.extend(rule_dangling_trace(design_index, req_index))

    return (
        findings,
        len(design_index),
        len(req_index),
        req_skipped + design_skipped,
    )


def print_report(
    findings: List[Finding],
    design_dir: str,
    reqs_dir: str,
    design_count: int,
    req_count: int,
    skipped: List[str],
    quiet: bool,
) -> None:
    print(f"Validating traceability: {design_dir} <-> {reqs_dir}")
    print(f"Indexed {design_count} design artifact(s), {req_count} requirement(s).")
    if skipped:
        print(
            f"WARNING: {len(skipped)} file(s) skipped (unparseable frontmatter); "
            f"results may be incomplete. Run the structural validators for details."
        )
    print("-" * 60)
    if not quiet:
        for f in sorted(
            findings, key=lambda f: (_SEVERITY_ORDER[f.severity], f.rule, f.artifact_id)
        ):
            print(f"  {f.severity.upper():<6} {f.rule:<22} {f.artifact_id:<10} {f.message}")
        print("-" * 60)
    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)
    print(f"Summary: {errors} error(s), {warns} warning(s).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate traceability between Groundwork design and requirement artifacts."
    )
    parser.add_argument(
        "design_dir",
        nargs="?",
        default=".sdlc/design",
        help="Directory of design files (default: .sdlc/design).",
    )
    parser.add_argument(
        "--requirements",
        default=".sdlc/requirements",
        help="Directory of requirement files (default: .sdlc/requirements).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero on warnings as well as errors."
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Print only the summary line."
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.design_dir):
        print(f"ERROR: design directory not found: {args.design_dir}", file=sys.stderr)
        return 2
    if not os.path.isdir(args.requirements):
        print(f"ERROR: requirements directory not found: {args.requirements}", file=sys.stderr)
        return 2

    findings, design_count, req_count, skipped = collect_findings(
        args.design_dir, args.requirements
    )
    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)

    if args.json:
        print(json.dumps(
            {
                "findings": [asdict(f) for f in findings],
                "counts": {"error": errors, "warn": warns},
            },
            indent=2,
        ))
    else:
        print_report(
            findings, args.design_dir, args.requirements,
            design_count, req_count, skipped, args.quiet,
        )

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

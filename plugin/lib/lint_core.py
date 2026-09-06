#!/usr/bin/env python3
"""Stage-agnostic core for Groundwork content-quality linters.

Groundwork runs an advisory content linter per stage: M1's
``lint_requirements_content.py`` (STO-136) and M2's ``lint_design_content.py``
(STO-208). They share the *finding record, prose helpers, report format and CLI*;
only the rules differ.

This module is that shared surface. It is the linter-tier analogue of
``artifact_core.py``, which STO-197 extracted from the validators for the same
reason, and it deliberately holds no requirement- or design-specific knowledge:
the vocabularies here are the ones both stages use, stage-only word lists stay
in the per-stage module, and the CLI is parameterized by the caller's
``lint_dir``.

The extraction is behavior-preserving: the M1 suite is its regression net.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable, List, Optional


@dataclass
class Finding:
    """One content-quality observation about one artifact.

    ``artifact_id`` is stage-agnostic on purpose: this record is emitted for
    requirements, components, interfaces and ADRs alike. It matches
    ``artifact_core.ArtifactFile.artifact_id`` and
    ``validate_traceability.Finding.artifact_id``.
    """

    rule: str
    severity: str  # "error" | "warn" | "info"
    artifact_id: str
    field: str
    excerpt: str
    message: str
    suggested_rewrite_hint: str


def flatten_text(value: Any) -> str:
    """Coerce a frontmatter value to a clean single-space-joined string."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[.;\n]+", text) if s.strip()]


# Qualifiers that promise a property without committing to a measurement.
# Shared: a vague requirement and a vague component responsibility fail the
# same way.
VAGUE_TERMS = {
    "fast", "rapid", "quick", "user-friendly", "easy", "intuitive", "seamless",
    "efficient", "robust", "flexible", "scalable", "secure", "reliable",
    "performant", "minimize", "maximize", "optimize", "approximately",
    "appropriate", "adequate", "sufficient", "state-of-the-art", "modern", "tbd",
}

# Verbs that denote a distinct action. Shared: M1's `compound` rule and M2's
# `god-component` rule both ask "does an and/or here join two actions?".
ACTION_VERBS = {
    "create", "update", "delete", "remove", "send", "display", "show", "store",
    "save", "validate", "verify", "notify", "alert", "log", "record", "generate",
    "transition", "publish", "return", "reject", "accept", "allow", "prevent",
    "block", "provide", "calculate", "compute", "export", "import", "retry",
    "cancel", "archive", "encrypt", "decrypt", "authenticate", "authorize",
    "render", "email", "persist", "enqueue", "dispatch", "present", "list",
    "filter", "sort", "redirect", "set", "mark", "flag", "assign",
}


def print_report(
    findings: List[Finding], root_dir: str, quiet: bool, noun: str = "requirement"
) -> None:
    """Print the shared per-artifact + summary report.

    ``noun`` labels the stage in the header line only, matching
    ``artifact_core.print_report``'s existing parameter of the same name.
    """
    by_artifact: dict = {}
    for f in findings:
        by_artifact.setdefault(f.artifact_id, []).append(f)

    print(f"Content-linting {noun}s in: {root_dir}")
    if not findings:
        print("No content anti-patterns found.")
        return
    for artifact_id in sorted(by_artifact):
        print(f"\n{artifact_id}")
        for f in by_artifact[artifact_id]:
            print(f"  [{f.severity}] {f.rule} ({f.field}): {f.message}")
            if not quiet:
                print(f"        excerpt: {f.excerpt}")
                print(f"        suggest: {f.suggested_rewrite_hint}")
    counts = {sev: sum(1 for f in findings if f.severity == sev)
              for sev in ("error", "warn", "info")}
    print(
        f"\nSummary: {len(findings)} finding(s) "
        f"({counts['error']} error, {counts['warn']} warn, {counts['info']} info)."
    )


def run_cli(
    argv: Optional[List[str]],
    *,
    default_dir: str,
    noun: str,
    lint_dir: Callable[[str], List[Finding]],
    description: str,
) -> int:
    """The shared linter CLI. Returns the process exit code.

    Advisory by contract: 0 unless ``--strict`` meets an error-severity finding
    (1) or the directory is missing (2).
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("root_dir", nargs="?", default=default_dir)
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any error-severity finding exists.")
    parser.add_argument("--quiet", action="store_true",
                        help="Print one line per finding (no excerpt/suggestion).")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.root_dir):
        print(f"ERROR: {noun} directory not found: {args.root_dir}", file=sys.stderr)
        return 2

    findings = lint_dir(args.root_dir)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print_report(findings, args.root_dir, args.quiet, noun)

    if args.strict and any(f.severity == "error" for f in findings):
        return 1
    return 0


def body_section(text: str, heading: str) -> str:
    """Return the raw text under a Markdown heading, or '' if it is absent.

    The section runs to the next heading of the same or higher level, so
    ``body_section(body, "## Decision Outcome")`` stops at the next ``##`` but
    contains its own ``### Consequences`` subsection.

    ``validate_traceability.decision_drivers_section`` is a near-equivalent,
    hard-coded to one heading. It is deliberately not reused: importing a
    hard-gate validator into an advisory linter to save fifteen lines couples
    the two tiers in the wrong direction (STO-208 spec D5).
    """
    level = len(heading) - len(heading.lstrip("#"))
    if level == 0:
        return ""
    start = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not start:
        return ""
    rest = text[start.end():]
    nxt = re.search(rf"^#{{1,{level}}}\s+\S", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest

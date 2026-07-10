#!/usr/bin/env python3
"""Content-quality linter for Groundwork atomic requirement artifacts.

Distinct from ``validate_requirements.py`` (which checks YAML schema + cross-file
structure). This tool reads the *prose* of each requirement and flags content
anti-patterns — vague qualifiers, compound requirements, EARS non-conformance,
passive voice with a nameless subject, and implementation bias at the
business/stakeholder tier.

It is ADVISORY: it prints a per-requirement diagnostic and, by default, exits 0.
Pass ``--strict`` to exit non-zero on any ``error``-severity finding. Pass
``--json`` for machine-readable findings (consumed by the requirements-critic).

Usage
-----
    python3 lint_requirements_content.py [REQUIREMENTS_DIR]
    python3 lint_requirements_content.py --json .sdlc/requirements
    python3 lint_requirements_content.py --strict --quiet reqs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Optional

import validate_requirements as vr


@dataclass
class Finding:
    rule: str
    severity: str  # "error" | "warn" | "info"
    req_id: str
    field: str
    excerpt: str
    message: str
    suggested_rewrite_hint: str


def _text(value: Any) -> str:
    """Coerce a frontmatter value to a clean single-space-joined string."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


VAGUE_TERMS = {
    "fast", "rapid", "quick", "user-friendly", "easy", "intuitive", "seamless",
    "efficient", "robust", "flexible", "scalable", "secure", "reliable",
    "performant", "minimize", "maximize", "optimize", "approximately",
    "appropriate", "adequate", "sufficient", "state-of-the-art", "modern", "tbd",
}


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"[.;\n]+", text) if s.strip()]


def check_vague_qualifiers(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    findings: List[Finding] = []
    for field in ("title", "description"):
        text = _text(fm.get(field))
        for sentence in _sentences(text):
            low = sentence.lower()
            quantified = bool(re.search(r"\d", sentence))
            for term in sorted(VAGUE_TERMS):
                if re.search(rf"\b{re.escape(term)}\b", low):
                    findings.append(Finding(
                        rule="vague-qualifier",
                        severity="info" if quantified else "warn",
                        req_id=req_id,
                        field=field,
                        excerpt=sentence.strip()[:120],
                        message=f"vague qualifier '{term}' without a concrete metric",
                        suggested_rewrite_hint=(
                            f"replace '{term}' with a measurable threshold "
                            f"(a time, count, or percentage)"
                        ),
                    ))
    return findings


# Registry of check functions, each (req_id, frontmatter) -> List[Finding].
# Populated in later tasks.
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
]


def lint_dir(reqs_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    for path in vr.discover_files(reqs_dir):
        fm, err = vr.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        req_id = fm.get("id") or os.path.basename(path)
        for check in CHECKS:
            findings.extend(check(req_id, fm))
    return findings


def _print_report(findings: List[Finding], reqs_dir: str, quiet: bool) -> None:
    by_req: Dict[str, List[Finding]] = {}
    for f in findings:
        by_req.setdefault(f.req_id, []).append(f)

    print(f"Content-linting requirements in: {reqs_dir}")
    if not findings:
        print("No content anti-patterns found.")
        return
    for req_id in sorted(by_req):
        print(f"\n{req_id}")
        for f in by_req[req_id]:
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Content-quality linter for Groundwork requirement artifacts."
    )
    parser.add_argument("requirements_dir", nargs="?", default=".sdlc/requirements")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any error-severity finding exists.")
    parser.add_argument("--quiet", action="store_true",
                        help="Print one line per finding (no excerpt/suggestion).")
    args = parser.parse_args(argv)

    reqs_dir = args.requirements_dir
    if not os.path.isdir(reqs_dir):
        print(f"ERROR: requirements directory not found: {reqs_dir}", file=sys.stderr)
        return 2

    findings = lint_dir(reqs_dir)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        _print_report(findings, reqs_dir, args.quiet)

    if args.strict and any(f.severity == "error" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

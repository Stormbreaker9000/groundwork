#!/usr/bin/env python3
"""Content-quality linter for Groundwork atomic design artifacts (STO-208).

The M2 analogue of ``lint_requirements_content.py``. Distinct from
``validate_design.py`` (schema + cross-file structure) and from
``validate_traceability.py`` (design <-> requirements edges): this tool reads
the *prose and the shape* of a design set and flags what neither structural
tier can see — a responsibility that promises without measuring, a component
doing two jobs, an interface nobody consumes, a hand-waved failure mode, an ADR
whose consequences are all upside, and a dependency cycle in a graph where
every individual edge resolves.

It is ADVISORY: it prints a per-artifact diagnostic and exits 0. Pass
``--strict`` to exit non-zero on any ``error``-severity finding (no rule emits
one today). Pass ``--json`` for machine-readable findings.

It runs from ``skills/design/SKILL.md`` Step 4, after the formatter's two hard
gates have passed — not from the critic, which runs before anything is on disk.

Usage
-----
    python3 lint_design_content.py [DESIGN_DIR]
    python3 lint_design_content.py --json .sdlc/design
    python3 lint_design_content.py --strict --quiet design
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Shared linter core lives at the repo root in ``lib/``. Resolved relative to
# this file, so cwd does not matter. Mirrors validate_design.py's bootstrap.
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import lint_core as core  # noqa: E402
from lint_core import Finding  # noqa: E402  (re-exported for tests)

import validate_design as vd  # noqa: E402


# Matches the whole frontmatter fence block, opening ``---`` through closing
# ``---`` inclusive. Mirrors artifact_core._FRONTMATTER_RE's shape (that
# regex is private to artifact_core, so this is a self-contained twin) but,
# unlike ``extract_frontmatter_block`` — whose capture group excludes both
# fence lines — this one is used for its match *span*, so ``match.end()``
# lands after the closing fence rather than after the YAML content.
_FRONTMATTER_FENCE_RE = re.compile(r"^---\s*\n.*?\n---\s*(?:\n|$)", re.DOTALL)


def _read_body(path: str) -> str:
    """Return a file's text with the frontmatter block stripped.

    The ADR rules read prose under MADR headings, which lives in the body. A
    read failure yields '' rather than raising: this tool is advisory, and an
    unreadable file is the structural validator's finding to make.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return ""
    match = _FRONTMATTER_FENCE_RE.match(text)
    if match is None:
        return text
    return text[match.end():]


# ---------------------------------------------------------------------------
# Component rules
# ---------------------------------------------------------------------------
def check_vague_responsibility(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a responsibility that promises a property without measuring it.

    The `vague-qualifier` analogue, including its severity demotion: a sentence
    carrying a digit has committed to a number somewhere, which is the failure
    this rule hunts, so it drops to `info`.
    """
    if fm.get("type") != "component":
        return []
    findings: List[Finding] = []
    text = core.flatten_text(fm.get("responsibility"))
    for sentence in core.sentences(text):
        low = sentence.lower()
        quantified = bool(re.search(r"\d", sentence))
        for term in sorted(core.VAGUE_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                findings.append(Finding(
                    rule="vague-responsibility",
                    severity="info" if quantified else "warn",
                    artifact_id=artifact_id,
                    field="responsibility",
                    excerpt=sentence.strip()[:120],
                    message=f"vague qualifier '{term}' without a concrete metric",
                    suggested_rewrite_hint=(
                        f"replace '{term}' with a measurable threshold, or move "
                        f"the property to an NFR the component traces to"
                    ),
                ))
    return findings


_GOD_COMPONENT_RE = re.compile(
    r"\b(and|or)\s+(" + "|".join(sorted(core.ACTION_VERBS)) + r")(?:s|es|d|ed|ing)?\b",
    re.IGNORECASE,
)


def check_god_component(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a responsibility gluing two purposes together.

    Ports M1's `compound` heuristic. M1 anchors its scan on 'shall' and searches
    the predicate after it; a responsibility has no such keyword, so the scan
    runs over the whole field. The verb anchoring is what keeps it quiet:
    'durably and atomically' does not fire, 'and sends notifications' does.
    """
    if fm.get("type") != "component":
        return []
    text = core.flatten_text(fm.get("responsibility"))
    match = _GOD_COMPONENT_RE.search(text)
    if not match:
        return []
    return [Finding(
        rule="god-component",
        severity="warn",
        artifact_id=artifact_id,
        field="responsibility",
        excerpt=text.strip()[:120],
        message=(
            f"two actions joined by '{match.group(1)}' ('{match.group(2)}') in "
            f"one responsibility"
        ),
        suggested_rewrite_hint=(
            "a component with two responsibilities is two components — split "
            "it, or name the single purpose that subsumes both"
        ),
    )]


# ---------------------------------------------------------------------------
# Interface rules
# ---------------------------------------------------------------------------
# Adverbs of intent: they describe an attitude toward failure rather than a
# failure. "Handled gracefully" tells a reader nothing they can design against.
_HANDWAVE_RE = re.compile(
    r"\b(gracefully|appropriately|properly|as needed|as appropriate)\b",
    re.IGNORECASE,
)


def check_error_modes_handwaved(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an error mode that names an attitude instead of a failure."""
    if fm.get("type") != "interface":
        return []
    findings: List[Finding] = []
    modes = fm.get("error_modes")
    if not isinstance(modes, list):
        return []
    for mode in modes:
        text = core.flatten_text(mode)
        match = _HANDWAVE_RE.search(text)
        if not match:
            continue
        findings.append(Finding(
            rule="error-modes-handwaved",
            severity="warn",
            artifact_id=artifact_id,
            field="error_modes",
            excerpt=text[:120],
            message=(
                f"error mode says '{match.group(1)}' rather than naming a "
                f"failure"
            ),
            suggested_rewrite_hint=(
                "name the condition and what the caller observes: 'the "
                "requested id does not exist', not 'errors are handled'"
            ),
        ))
    return findings


def check_orphan_interfaces(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> List[Finding]:
    """Flag an interface no component consumes.

    The `glossary-unused` analogue: defined-but-unused is a warning, not a gate.
    A contract nobody depends on is either dead or a missing `depends_on` edge,
    and the linter cannot tell which — so it reports rather than decides.
    """
    consumed: set = set()
    interfaces: List[Tuple[str, Dict[str, Any]]] = []
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") == "component":
            depends = fm.get("depends_on")
            if isinstance(depends, list):
                consumed.update(core.flatten_text(d) for d in depends)
        elif fm.get("type") == "interface":
            interfaces.append((artifact_id, fm))

    findings: List[Finding] = []
    for artifact_id, fm in interfaces:
        if artifact_id in consumed:
            continue
        findings.append(Finding(
            rule="orphan-interface",
            severity="warn",
            artifact_id=artifact_id,
            field="id",
            excerpt=core.flatten_text(fm.get("title")),
            message=f"interface '{artifact_id}' is consumed by no component",
            suggested_rewrite_hint=(
                "drop the contract, or add it to the depends_on of the "
                "component that should be consuming it"
            ),
        ))
    return findings


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
# Per-artifact checks: (artifact_id, frontmatter, body) -> [Finding].
# The body parameter is what M1's signature lacks: the ADR rules read prose
# under MADR headings, which is not in frontmatter.
CHECKS: List[Callable[[str, Dict[str, Any], str], List[Finding]]] = [
    check_vague_responsibility,
    check_god_component,
    check_error_modes_handwaved,
]

# Set-level checks: (artifacts) -> [Finding], where `artifacts` is the list of
# (artifact_id, frontmatter, body) triples. These need the whole set at once —
# "no component consumes this interface" is not decidable from one file, the
# same reason M1's glossary check needed SET_CHECKS.
SET_CHECKS: List[Callable[[List[Tuple[str, Dict[str, Any], str]]], List[Finding]]] = [
    check_orphan_interfaces,
]


def lint_dir(design_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    artifacts: List[Tuple[str, Dict[str, Any], str]] = []
    for path in vd.discover_files(design_dir):
        fm, err = vd.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        artifact_id = fm.get("id") or os.path.basename(path)
        body = _read_body(path)
        artifacts.append((artifact_id, fm, body))
        for check in CHECKS:
            findings.extend(check(artifact_id, fm, body))
    for set_check in SET_CHECKS:
        findings.extend(set_check(artifacts))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    return core.run_cli(
        argv,
        default_dir=".sdlc/design",
        noun="design artifact",
        lint_dir=lint_dir,
        description=(
            "Content-quality linter for Groundwork design artifacts."
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())

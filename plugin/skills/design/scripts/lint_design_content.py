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
# ADR rules
# ---------------------------------------------------------------------------
# MADR headings this stage writes. Gated for presence by validate_design.py;
# their prose is this linter's business.
DRIVERS_HEADING = "## Decision Drivers"
OPTIONS_HEADING = "## Considered Options"
CONSEQUENCES_HEADING = "### Consequences"

# `- Good: ...` / `- Bad: ...`, and MADR 4.0's `- Good, because ...`. Bold
# markers are tolerated because the formatter emits them in places.
_CONSEQUENCE_RE = re.compile(r"^\s*[-*]\s*(?:\*\*)?(Good|Bad)\b", re.MULTILINE)

# The formatter's honest placeholder for a section with nothing to record yet.
_PLACEHOLDER_RE = re.compile(r"^\s*[-*]\s*None\b", re.MULTILINE)


def _is_placeholder_section(section: str) -> bool:
    """True if a body section's only content is the formatter's placeholder.

    Distinct from ``_PLACEHOLDER_RE.search(section)``, which matches if a
    placeholder-shaped line appears *anywhere* in the section -- true of an
    unrelated bullet like "- None of the existing migrations need to
    change." sitting alongside real content. The placeholder means "nothing
    to record yet", which is only true when it is the section's only line.
    """
    lines = [line for line in section.splitlines() if line.strip()]
    return len(lines) == 1 and bool(_PLACEHOLDER_RE.match(lines[0]))


def check_adr_consequences_one_sided(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an accepted decision whose consequences are all upside.

    Every real decision costs something. A consequences section with Good
    bullets and no Bad bullet records a decision that was not weighed.

    Skipped for `proposed` decisions and for the placeholder: both are correct
    output for a decision that has not been taken.
    """
    if fm.get("type") != "adr" or fm.get("decision_status") == "proposed":
        return []
    section = core.body_section(body, CONSEQUENCES_HEADING)
    if not section.strip() or _is_placeholder_section(section):
        return []
    kinds = {m.group(1).lower() for m in _CONSEQUENCE_RE.finditer(section)}
    if "bad" in kinds or "good" not in kinds:
        return []
    return [Finding(
        rule="adr-consequences-one-sided",
        severity="warn",
        artifact_id=artifact_id,
        field="consequences",
        excerpt=core.flatten_text(section)[:120],
        message="consequences list only upsides; no cost is recorded",
        suggested_rewrite_hint=(
            "name what the decision costs — a decision with no downside was "
            "not a decision"
        ),
    )]


def check_adr_vague_driver(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag a vague qualifier in an ADR's decision drivers.

    The driver is what the decision claims to answer, so it is the most
    load-bearing place a vague qualifier can sit: 'must be scalable' names no
    threshold the chosen option can be checked against.

    Mirrors `check_vague_responsibility`'s severity demotion: a driver line
    carrying a digit has committed to a number somewhere, which is the
    failure this rule hunts, so it drops to `info`.
    """
    if fm.get("type") != "adr":
        return []
    section = core.body_section(body, DRIVERS_HEADING)
    findings: List[Finding] = []
    for line in section.splitlines():
        text = core.flatten_text(line)
        # Deliberately the per-line guard, not `_is_placeholder_section`: a
        # drivers section is a bullet list of distinct drivers, one per line,
        # not a single prose block the way `### Consequences` or
        # `## Considered Options` are. A placeholder bullet sitting next to
        # real drivers should not silence the real ones -- unlike those other
        # two sections, where the placeholder means "nothing here at all" and
        # only counts if it is the section's *only* content.
        if not text or _PLACEHOLDER_RE.match(line):
            continue
        low = text.lower()
        quantified = bool(re.search(r"\d", text))
        for term in sorted(core.VAGUE_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                findings.append(Finding(
                    rule="adr-vague-driver",
                    severity="info" if quantified else "warn",
                    artifact_id=artifact_id,
                    field="decision_drivers",
                    excerpt=text[:120],
                    message=(
                        f"decision driver '{term}' names no threshold the "
                        f"chosen option can be checked against"
                    ),
                    suggested_rewrite_hint=(
                        "cite the NFR that quantifies it, or state the "
                        "threshold in the driver"
                    ),
                ))
    return findings


def check_adr_option_unexamined(
    artifact_id: str, fm: Dict[str, Any], body: str
) -> List[Finding]:
    """Flag an option named in frontmatter but never discussed in the body.

    `info`, not `warn`: an option can legitimately be weighed under
    `## Decision Outcome` instead, so this reports a smell it cannot prove.
    The schema's `minItems: 2` is what makes the smell worth reporting — an
    option can be added to clear that gate without ever being considered.

    Skipped when the options section is the formatter's placeholder: a
    `proposed` decision can carry options in frontmatter (per the
    adr-generator contract) while the body honestly records that none have
    been examined yet, which is not this smell.
    """
    if fm.get("type") != "adr":
        return []
    options = fm.get("considered_options")
    if not isinstance(options, list):
        return []
    section = core.body_section(body, OPTIONS_HEADING)
    if not section.strip() or _is_placeholder_section(section):
        return []
    low = section.lower()
    findings: List[Finding] = []
    for option in options:
        text = core.flatten_text(option)
        if not text or text.lower() in low:
            continue
        findings.append(Finding(
            rule="adr-option-unexamined",
            severity="info",
            artifact_id=artifact_id,
            field="considered_options",
            excerpt=text[:120],
            message=(
                f"option '{text}' is listed in frontmatter but never appears "
                f"under '{OPTIONS_HEADING}'"
            ),
            suggested_rewrite_hint=(
                "weigh it in the body, or drop it — an option listed only to "
                "clear the two-option gate was not considered"
            ),
        ))
    return findings


# ---------------------------------------------------------------------------
# Set-level: the dependency graph
# ---------------------------------------------------------------------------
def _component_graph(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> Dict[str, Dict[str, str]]:
    """Build {component_id: {target_component_id: via_interface_id}}.

    One edge type: component A depends on component B when A lists an interface
    whose provider is B. Where two interfaces produce the same A->B edge, the
    lowest-sorting interface id is kept, so the reported path is deterministic.
    """
    providers: Dict[str, str] = {}
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") == "interface":
            provider = core.flatten_text(fm.get("provider"))
            if provider:
                providers[artifact_id] = provider

    graph: Dict[str, Dict[str, str]] = {}
    for artifact_id, fm, _body in artifacts:
        if fm.get("type") != "component":
            continue
        edges: Dict[str, str] = {}
        depends = fm.get("depends_on")
        if isinstance(depends, list):
            for raw in sorted(core.flatten_text(d) for d in depends):
                target = providers.get(raw)
                if target and target not in edges:
                    edges[target] = raw
        graph[artifact_id] = edges
    return graph


def _canonical(cycle: List[str]) -> Tuple[str, ...]:
    """Rotate a cycle to start at its lowest-sorting component id.

    Without this the same cycle is reported once per entry path — the shipped
    tamagotchi set yields its single CMP-003/CMP-004 cycle six times.
    """
    pivot = cycle.index(min(cycle))
    return tuple(cycle[pivot:] + cycle[:pivot])


def check_dependency_cycles(
    artifacts: List[Tuple[str, Dict[str, Any], str]]
) -> List[Finding]:
    """Flag cycles in the CMP.depends_on -> IF.provider -> CMP graph.

    Not a structural error: every edge resolves and every provider exists, so
    the structural validator is right to pass it. The *shape* is the defect,
    and shape is what the structural tier cannot see.
    """
    graph = _component_graph(artifacts)
    seen: set = set()
    cycles: List[List[str]] = []

    def walk(node: str, stack: List[str]) -> None:
        for target in sorted(graph.get(node, {})):
            if target in stack:
                cycle = stack[stack.index(target):]
                key = _canonical(cycle)
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(key))
                continue
            walk(target, stack + [target])

    for start in sorted(graph):
        walk(start, [start])

    findings: List[Finding] = []
    for cycle in sorted(cycles):
        # Render CMP-001 -> IF-002 -> CMP-002 -> IF-001 -> CMP-001, naming the
        # interfaces because the interfaces are where the fix is made.
        parts: List[str] = []
        for i, node in enumerate(cycle):
            nxt = cycle[(i + 1) % len(cycle)]
            parts.append(node)
            parts.append(graph[node][nxt])
        path = " -> ".join(parts + [cycle[0]])
        findings.append(Finding(
            rule="dependency-cycle",
            severity="warn",
            artifact_id=cycle[0],
            field="depends_on",
            excerpt=path[:120],
            message=f"dependency cycle: {path}",
            suggested_rewrite_hint=(
                "break the loop at one of the named interfaces — invert the "
                "dependency, or move the shared state into a component both "
                "can depend on"
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
    check_adr_consequences_one_sided,
    check_adr_vague_driver,
    check_adr_option_unexamined,
]

# Set-level checks: (artifacts) -> [Finding], where `artifacts` is the list of
# (artifact_id, frontmatter, body) triples. These need the whole set at once —
# "no component consumes this interface" is not decidable from one file, the
# same reason M1's glossary check needed SET_CHECKS.
SET_CHECKS: List[Callable[[List[Tuple[str, Dict[str, Any], str]]], List[Finding]]] = [
    check_orphan_interfaces,
    check_dependency_cycles,
]


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------
# Declarative description of every rule the checks above can emit, read by
# site/scripts/export_reference.py to build the published rule reference.
# ``test_rules_registry_matches_emitted_rules`` holds this equal, in both
# directions, to what the fixture corpus actually produces — so a new check
# with no entry here fails the suite before it can reach the documentation,
# and an entry no fixture exercises fails too.
#
# ``severities`` is a list because two rules demote to "info" when the text
# they flag carries a number. ``fields`` is a list because a check may flag
# more than one frontmatter field, and ``test_emitted_fields_are_declared``
# holds it honest.
RULES: List[Dict[str, Any]] = [
    {
        "id": "vague-responsibility",
        "severities": ["warn", "info"],
        "applies_to": "component",
        "fields": ["responsibility"],
        "summary": (
            "A component responsibility uses a vague qualifier with no "
            "concrete metric. Demoted to info when the sentence carries a "
            "number."
        ),
    },
    {
        "id": "god-component",
        "severities": ["warn"],
        "applies_to": "component",
        "fields": ["responsibility"],
        "summary": (
            "Two actions joined by a conjunction in one responsibility — "
            "the component is doing two jobs."
        ),
    },
    {
        "id": "error-modes-handwaved",
        "severities": ["warn"],
        "applies_to": "interface",
        "fields": ["error_modes"],
        "summary": (
            "An error mode gestures at failure rather than naming one."
        ),
    },
    {
        "id": "orphan-interface",
        "severities": ["warn"],
        "applies_to": "interface",
        "fields": ["id"],
        "summary": (
            "The contract is provided but consumed by no component. Set-level "
            "check: not decidable from a single file."
        ),
    },
    {
        "id": "adr-consequences-one-sided",
        "severities": ["warn"],
        "applies_to": "adr",
        "fields": ["consequences"],
        "summary": (
            "Consequences list only upsides; no cost is recorded. A decision "
            "with no downside was not a decision."
        ),
    },
    {
        "id": "adr-vague-driver",
        "severities": ["warn", "info"],
        "applies_to": "adr",
        "fields": ["decision_drivers"],
        "summary": (
            "A decision driver names no threshold the chosen option can be "
            "checked against. Demoted to info when the line carries a number."
        ),
    },
    {
        "id": "adr-option-unexamined",
        "severities": ["info"],
        "applies_to": "adr",
        "fields": ["considered_options"],
        "summary": (
            "An option listed in frontmatter never appears under the "
            "'Considered Options' heading, so it was named but not weighed."
        ),
    },
    {
        "id": "dependency-cycle",
        "severities": ["warn"],
        "applies_to": "component",
        "fields": ["depends_on"],
        "summary": (
            "A cycle in the component graph where every individual edge "
            "resolves. Set-level check: invisible one file at a time."
        ),
    },
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

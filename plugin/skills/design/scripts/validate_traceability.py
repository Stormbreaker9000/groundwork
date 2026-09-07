#!/usr/bin/env python3
"""Cross-artifact traceability validator for Groundwork (STO-102).

Groundwork's two structural validators each see one stage directory by design,
and each explicitly declines to resolve the edge that crosses between them:
``validate_design.py`` checks that ``traces_from`` is requirement-SHAPED but
not that the requirement exists, and ``validate_requirements.py`` excludes
every ``traces_to`` sub-list from its dangling-reference sweep. This tool is
the one that reads both directories at once and resolves that edge.

The rules it runs are declared in ``RULES`` below, which is also what the
documentation site renders. There is deliberately no second list here: a
restated table is a place for the same facts to drift.

The last two are index caveats rather than edge checks, and they are findings
for a reason: they travel the same channel every consumer already reads (the
warning count, --strict, --json, and the formatter's hand-off), so a sweep
that could not see the whole set cannot be reported downstream as a clean one.

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
from typing import Any, Dict, List, Optional, Tuple

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

import artifact_core as core  # noqa: E402
import generate_c4 as gc4  # noqa: E402
import validate_design as vd  # noqa: E402
import validate_requirements as vr  # noqa: E402
from artifact_core import parse_frontmatter  # noqa: E402


# Severities. There are exactly two; see spec D2.
ERROR = "error"
WARN = "warn"
_SEVERITY_ORDER = {ERROR: 0, WARN: 1}

# The published rule reference is generated from this list (STO-250 pass 2).
# It is the single declaration of what this tool checks: the module docstring
# used to restate it in prose, which was a second place for the same facts to
# drift. Keys match the two content linters' registries so one component
# renders all three. `fields` is empty by construction — a traceability
# Finding names an artifact and a path, never a frontmatter field.
RULES: List[Dict[str, Any]] = [
    {
        "id": "dangling-trace",
        "severities": [ERROR],
        "applies_to": "design artifact",
        "fields": [],
        "summary": (
            "A design artifact's traces_from names a requirement ID that "
            "does not exist in the requirements set."
        ),
    },
    {
        "id": "adr-driver-unresolved",
        "severities": [ERROR],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A requirement ID listed under '## Decision Drivers' does not "
            "resolve. A listed driver is the leading token of a list item."
        ),
    },
    {
        "id": "dangling-reverse-trace",
        "severities": [ERROR],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A requirement's non-empty traces_to.design names a design ID "
            "that does not exist. Fixed by hand in the requirements stage — "
            "there is no migration script and no bypass flag."
        ),
    },
    {
        "id": "misplaced-requirement-trace",
        "severities": [ERROR],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A requirement ID sits in traces_to.tests or traces_to.code, "
            "which hold test and code references. Fixed by hand in the "
            "requirements stage; the message names the exact edit."
        ),
    },
    {
        "id": "dangling-qa-trace",
        "severities": [ERROR],
        "applies_to": "qa artifact",
        "fields": [],
        "summary": (
            "A QA artifact's traces_from names an ID that exists in neither "
            "the requirements set nor the design set."
        ),
    },
    {
        "id": "uncovered-fr",
        "severities": [WARN],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "A functional requirement is cited by no component. Excludes "
            "priority: wont and status: obsolete."
        ),
    },
    {
        "id": "uncovered-asr",
        "severities": [WARN],
        "applies_to": "requirement",
        "fields": [],
        "summary": (
            "An architecturally significant requirement is covered by no test "
            "strategy item. Excludes priority: wont and status: obsolete."
        ),
    },
    {
        "id": "adr-driver-untraced",
        "severities": [WARN],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A listed decision driver resolves but is absent from that ADR's "
            "traces_from."
        ),
    },
    {
        "id": "adr-driver-unlisted",
        "severities": [WARN],
        "applies_to": "adr",
        "fields": [],
        "summary": (
            "A requirement ID appears in the drivers prose but not as a list "
            "item, so it was never checked as a driver. A warning rather than "
            "an error: ordinary English mentioning an ID is history, not a "
            "defect."
        ),
    },
    {
        "id": "index-unparseable",
        "severities": [WARN],
        "applies_to": "the index",
        "fields": [],
        "summary": (
            "A file's frontmatter did not parse, so it is missing from the "
            "index and the sweep was not complete."
        ),
    },
    {
        "id": "duplicate-id",
        "severities": [WARN],
        "applies_to": "the index",
        "fields": [],
        "summary": (
            "Two files claim the same ID; only the last one read was indexed."
        ),
    },
]


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
    traces_to_tests: List[str] = field(default_factory=list)
    traces_to_code: List[str] = field(default_factory=list)


@dataclass
class DesignArtifact:
    design_id: str
    type: str
    path: str
    traces_from: List[str] = field(default_factory=list)


@dataclass
class QAArtifact:
    qa_id: str
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
def index_requirements(
    reqs_dir: str,
) -> Tuple[Dict[str, Requirement], List[str], List[str]]:
    """Index every requirement by ID.

    Returns (index, unparseable_paths, duplicate_ids). A duplicate ID means the
    second file silently replaces the first in the index, so every result
    computed over it may be wrong in either direction; the caller reports it.
    """
    index: Dict[str, Requirement] = {}
    skipped: List[str] = []
    duplicates: List[str] = []
    for path in vr.discover_files(reqs_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        if data["id"] in index:
            duplicates.append(data["id"])
        traces_to = data.get("traces_to") if isinstance(data.get("traces_to"), dict) else {}
        index[data["id"]] = Requirement(
            req_id=data["id"],
            type=_text(data.get("type")),
            priority=_text(data.get("priority")),
            status=_text(data.get("status")),
            path=os.path.relpath(path, reqs_dir),
            traces_to_design=_str_list(traces_to.get("design")),
            traces_to_tests=_str_list(traces_to.get("tests")),
            traces_to_code=_str_list(traces_to.get("code")),
        )
    return index, skipped, duplicates


def index_design(
    design_dir: str,
) -> Tuple[Dict[str, DesignArtifact], List[str], List[str]]:
    """Index every design artifact by ID.

    Returns (index, unparseable_paths, duplicate_ids). See
    ``index_requirements`` for why duplicates are surfaced.
    """
    index: Dict[str, DesignArtifact] = {}
    skipped: List[str] = []
    duplicates: List[str] = []
    for path in vd.discover_files(design_dir):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        if data["id"] in index:
            duplicates.append(data["id"])
        index[data["id"]] = DesignArtifact(
            design_id=data["id"],
            type=_text(data.get("type")),
            path=os.path.relpath(path, design_dir),
            traces_from=_str_list(data.get("traces_from")),
        )
    return index, skipped, duplicates


# validate_qa.py's own SKIP_FILENAMES, restated rather than imported: this
# module already reaches into the requirements and design skills' scripts for
# discover_files, and pulling in the QA skill's structural validator as well
# would couple that script to this one for no reason — this tool only ever
# needs the skip set, not any of validate_qa.py's schema logic.
QA_SKIP_FILENAMES = {"qa-strategy.md", "index.yaml"}


def index_qa(
    qa_dir: str,
) -> Tuple[Dict[str, QAArtifact], List[str], List[str]]:
    """Index every QA artifact by ID.

    Returns (index, unparseable_paths, duplicate_ids). See
    ``index_requirements`` for why duplicates are surfaced.
    """
    index: Dict[str, QAArtifact] = {}
    skipped: List[str] = []
    duplicates: List[str] = []
    for path in core.discover_files(qa_dir, QA_SKIP_FILENAMES, set()):
        data, err = parse_frontmatter(path)
        if err or not isinstance(data, dict) or not isinstance(data.get("id"), str):
            skipped.append(path)
            continue
        if data["id"] in index:
            duplicates.append(data["id"])
        index[data["id"]] = QAArtifact(
            qa_id=data["id"],
            type=_text(data.get("type")),
            path=os.path.relpath(path, qa_dir),
            traces_from=_str_list(data.get("traces_from")),
        )
    return index, skipped, duplicates


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


def rule_dangling_qa_trace(
    qa_index: Dict[str, QAArtifact],
    req_index: Dict[str, Requirement],
    design_index: Dict[str, DesignArtifact],
) -> List[Finding]:
    """Every QA artifact's traces_from must resolve to a requirement or a
    design artifact.

    A TS covers either half of the pipeline — an FR/NFR straight out of the
    requirements set, or a component/interface/ADR it targets instead — so the
    resolution set is the union of both indexes, not either alone. Only
    traces_from is resolved: traces_to (tests, code) is future work the QA
    stage hands off to, not an edge this tool owns (spec D8).
    """
    findings: List[Finding] = []
    for art in sorted(qa_index.values(), key=lambda a: a.qa_id):
        for target in art.traces_from:
            if target in req_index or target in design_index:
                continue
            findings.append(Finding(
                rule="dangling-qa-trace",
                severity=ERROR,
                artifact_id=art.qa_id,
                path=art.path,
                message=(
                    f"traces_from -> '{target}' is not a known requirement or "
                    f"design artifact id"
                ),
            ))
    return findings


# A `wont` requirement having no component is the correct outcome, and an
# obsolete one is not part of the system. Both are excluded from the sweep
# entirely rather than warned about — warning trains the reader to ignore the
# rule (spec D4).
COVERAGE_EXCLUDED_PRIORITIES = {"wont"}
COVERAGE_EXCLUDED_STATUSES = {"obsolete"}


def rule_uncovered_fr(
    design_index: Dict[str, DesignArtifact], req_index: Dict[str, Requirement]
) -> List[Finding]:
    """Every functional requirement must be cited by at least one component.

    Components only. An FR is behaviour and behaviour is owned by a component,
    so an interface or ADR citing it is not coverage (spec D4).
    """
    covered: set = set()
    for art in design_index.values():
        if art.type == "component":
            covered.update(art.traces_from)

    findings: List[Finding] = []
    for req in sorted(req_index.values(), key=lambda r: r.req_id):
        if req.type != "functional":
            continue
        if req.priority in COVERAGE_EXCLUDED_PRIORITIES:
            continue
        if req.status in COVERAGE_EXCLUDED_STATUSES:
            continue
        if req.req_id in covered:
            continue
        findings.append(Finding(
            rule="uncovered-fr",
            severity=WARN,
            artifact_id=req.req_id,
            path=req.path,
            message="no component traces_from this functional requirement",
        ))
    return findings


def _read_asrs(design_dir: str) -> List[str]:
    """Every ASR ID in drivers.md's '## Architecturally Significant
    Requirements' section, or [] if the file, or the section, is absent.

    There is exactly one authoritative ASR list in this pipeline: drivers.md,
    written by the design formatter and already read by generate_c4.py
    (``DesignSet._read_asrs``) to seed each diagram's traces_from. This
    delegates to that same method rather than writing a second parser over
    the same section — two parsers of "what counts as an ASR" is precisely
    the drift this discipline exists to prevent, and ``ASR_HEADING`` /
    ``_ASR_LINE_RE`` live there, not here.

    A missing or unreadable drivers.md, or one lacking the heading, resolves
    to [] here exactly as it does in generate_c4.py (that method also prints
    a stderr warning distinguishing the two cases; this call inherits it).
    That is not re-reported as a finding of its own — a missing heading is
    validate_design.py's structural finding when drivers.md exists at all —
    but it does mean rule_uncovered_asr goes silent over a design set
    malformed in that specific way, which is accepted rather than duplicated
    as a second warning channel for the same underlying defect.
    """
    return gc4.DesignSet._read_asrs(design_dir)


def rule_uncovered_asr(
    req_index: Dict[str, Requirement],
    qa_index: Dict[str, QAArtifact],
    design_dir: str,
) -> List[Finding]:
    """Every architecturally significant requirement must be cited by at
    least one test strategy item.

    "Architecturally significant" means exactly what drivers.md's ASR list
    says it means (see ``_read_asrs``) — not a proxy such as "cited by some
    design artifact's traces_from". Those two sets differ in both
    directions: a design artifact may cite a requirement for reasons other
    than architectural significance, and an ASR may end up addressed by no
    single artifact's traces_from. The rule is named uncovered-*asr*, so it
    has to resolve against the actual ASR list or the name would lie.

    Reuses rule_uncovered_fr's exclusion filters rather than inventing a
    second definition of "excluded from coverage sweeps": a `wont` or
    `obsolete` requirement is excluded from this sweep for the same reason it
    is excluded from that one (spec D4).
    """
    asrs = _read_asrs(design_dir)

    covered: set = set()
    for ts in qa_index.values():
        covered.update(ts.traces_from)

    findings: List[Finding] = []
    for asr_id in sorted(set(asrs)):
        req = req_index.get(asr_id)
        if req is None:
            # Not a known requirement id (dangling, or an ASR line naming a
            # CMP-/IF- id by mistake). Resolving drivers.md's ASR list against
            # the requirements set is not this rule's job; it only asks
            # whether a *known* ASR requirement has test coverage.
            continue
        if req.priority in COVERAGE_EXCLUDED_PRIORITIES:
            continue
        if req.status in COVERAGE_EXCLUDED_STATUSES:
            continue
        if req.req_id in covered:
            continue
        findings.append(Finding(
            rule="uncovered-asr",
            severity=WARN,
            artifact_id=req.req_id,
            path=req.path,
            message="no test strategy item traces_from this architecturally significant requirement",
        ))
    return findings


# vd.REQUIREMENT_ID_RE is anchored with ^...$ and cannot scan a line, so the
# body scan needs its own pattern.
#
# What stops 'NFR-001' also matching as 'FR-001' is the alternation, not the
# guard: finditer is leftmost-first and 'NFR' precedes 'FR' in the group, so
# the whole token is consumed before 'FR' is ever tried. The (?<!\w) guard
# does something different — it rejects a *word-character* prefix, so
# 'SUBR-004' does not yield 'BR-004' and 'ANFR-003' does not yield 'NFR-003'.
# (Note 'ANFR-003' yields 'NFR-003', not 'FR-003', for the same leftmost-first
# reason: 'NFR' is tried and consumed before 'FR' is reached.)
#
# Known gap: the guard does not block a *hyphen* prefix, so prose such as
# 'non-FR-001' still scans as 'FR-001'. Documented, not fixed — a hyphen is a
# legal separator inside these IDs, so excluding it would break real ones.
# This is one of two reasons a bare scan of the section is not trustworthy
# enough to hard-fail a stage on; see DRIVER_ITEM_RE.
#
# 'ADR' is deliberately absent from the alternation: an ADR cross-reference in
# the prose is not a requirement.
REQUIREMENT_ID_SCAN_RE = re.compile(
    r"(?<!\w)(?:FR|NFR|CON|BR|UC)(?:-[A-Z0-9]+)*-[0-9]{3,}(?!\w)"
)

# A *declared* driver is the leading token of a list item, which is the only
# shape `agents/adr-generator.md` emits ('- NFR-001: keep p99 under 200ms').
# Anything else under the heading is prose, and prose must not hard-fail a
# stage: an architect writing '- NFR-001 (latency); supersedes the earlier
# FR-014 framing' is describing history, not declaring a driver on a
# requirement that no longer exists. Optional wrappers cover the ways a
# generator or a human marks the ID up: '- **FR-001**', '- `FR-001`',
# '- [FR-001](...)'.
DRIVER_ITEM_RE = re.compile(
    r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+[*_`\[\"']*"
    r"((?:FR|NFR|CON|BR|UC)(?:-[A-Z0-9]+)*-[0-9]{3,})(?!\w)"
)

DECISION_DRIVERS_HEADING = "## Decision Drivers"


def decision_drivers_section(path: str) -> str:
    """Return the raw text under '## Decision Drivers', or '' if absent.

    The section runs from the heading line to the next '## ' line or EOF. An
    H3 such as '### Consequences' does not terminate it, because '^## ' needs
    a space as the third character.

    Returns '' when the heading is absent: validate_design.py gates the five
    MADR headings, so a missing one is that tool's finding, not ours.

    Known limitation: the scan is not fence-aware, so a '## ' line inside a
    fenced code block terminates the section early. Noted, not handled.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return ""

    match = re.search(
        rf"^{re.escape(DECISION_DRIVERS_HEADING)}\s*$", text, re.MULTILINE
    )
    if not match:
        return ""
    rest = text[match.end():]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def _dedupe(ids: List[str]) -> List[str]:
    ordered: List[str] = []
    seen: set = set()
    for value in ids:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def extract_decision_drivers(path: str) -> Tuple[List[str], List[str]]:
    """Return (declared, mentioned_only) requirement IDs for an ADR's drivers.

    ``declared`` are the IDs in leading list-item position — the generated
    shape, and the only ones this tool is willing to hard-fail on.
    ``mentioned_only`` are IDs that appear somewhere in the section but never
    as a declared item; they are reported, never enforced, because the scan
    cannot tell a driver from a sentence.
    """
    section = decision_drivers_section(path)
    if not section:
        return [], []

    matches = (DRIVER_ITEM_RE.match(line) for line in section.splitlines())
    declared = _dedupe([m.group(1) for m in matches if m])
    everything = _dedupe([m.group(0) for m in REQUIREMENT_ID_SCAN_RE.finditer(section)])
    mentioned_only = [i for i in everything if i not in set(declared)]
    return declared, mentioned_only


def rule_adr_drivers(
    design_index: Dict[str, DesignArtifact],
    req_index: Dict[str, Requirement],
    design_dir: str,
) -> List[Finding]:
    """Check the IDs an ADR names under '## Decision Drivers'.

    agents/adr-generator.md derives body.decision_drivers as 'the traces_from
    IDs', so the two are the same list written twice. An unresolvable ID is an
    error; a resolving one absent from frontmatter means they have drifted.

    Deliberately one-directional: an ID in frontmatter but missing from the
    body is a rendering gap the formatter owns, not a traceability defect
    (spec D5).
    """
    findings: List[Finding] = []
    for art in sorted(design_index.values(), key=lambda a: a.design_id):
        if art.type != "adr":
            continue
        traced = set(art.traces_from)
        declared, mentioned_only = extract_decision_drivers(
            os.path.join(design_dir, art.path)
        )
        for driver in declared:
            if driver not in req_index:
                findings.append(Finding(
                    rule="adr-driver-unresolved",
                    severity=ERROR,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=(
                        f"'{DECISION_DRIVERS_HEADING}' lists '{driver}' as a "
                        f"driver, which is not a known requirement id"
                    ),
                ))
            elif driver not in traced:
                findings.append(Finding(
                    rule="adr-driver-untraced",
                    severity=WARN,
                    artifact_id=art.design_id,
                    path=art.path,
                    message=(
                        f"'{DECISION_DRIVERS_HEADING}' lists '{driver}' as a "
                        f"driver, which is absent from frontmatter traces_from"
                    ),
                ))
        # An ID that never appears in declared position is not enforced — but
        # staying silent about it would hide a real drivers list written as a
        # paragraph instead of bullets, which this rule would then never check.
        # Say so, at a severity that cannot block the stage.
        for mention in mentioned_only:
            if mention in req_index and mention in traced:
                continue
            findings.append(Finding(
                rule="adr-driver-unlisted",
                severity=WARN,
                artifact_id=art.design_id,
                path=art.path,
                message=(
                    f"'{DECISION_DRIVERS_HEADING}' mentions '{mention}' in prose "
                    f"but not as a list item, so it was not checked as a driver"
                    + ("" if mention in req_index else
                       " (and it does not resolve to a known requirement id)")
                ),
            ))
    return findings


def rule_dangling_reverse_trace(
    req_index: Dict[str, Requirement], design_index: Dict[str, DesignArtifact]
) -> List[Finding]:
    """A non-empty traces_to.design must resolve to a real design artifact.

    Presence is never required and asymmetry is never a finding: the
    requirement->design edge lives once, on design.traces_from (spec D3). This
    rule only says that if the slot is populated, its contents must be real.
    """
    findings: List[Finding] = []
    for req in sorted(req_index.values(), key=lambda r: r.req_id):
        for target in req.traces_to_design:
            if target in design_index:
                continue
            # A target that resolves as a *requirement* is not a typo, it is
            # the pre-STO-102 pattern the old constraint-specialist rule
            # mandated. Naming the exact remedy turns a stage-stopping error
            # the user cannot act on into a mechanical edit, which matters
            # because this rule has no re-dispatch loop behind it.
            if target in req_index:
                remedy = (
                    f"traces_to.design -> '{target}' is a requirement, not a "
                    f"design artifact. This slot holds CMP-/IF-/ADR- ids only. "
                    f"Move the edge: delete it here and add '{req.req_id}' to "
                    f"{target}'s own traces_from"
                )
            else:
                remedy = (
                    f"traces_to.design -> '{target}' is not a known design "
                    f"artifact id; clear it or correct it to a CMP-/IF-/ADR- id"
                )
            findings.append(Finding(
                rule="dangling-reverse-trace",
                severity=ERROR,
                artifact_id=req.req_id,
                path=req.path,
                message=remedy,
            ))
    return findings


def rule_misplaced_requirement_trace(
    req_index: Dict[str, Requirement]
) -> List[Finding]:
    """No requirement ID may sit in traces_to.tests or traces_to.code.

    Those slots hold test and source-file references. The same pre-STO-102
    instruction that put requirement IDs in ``traces_to.design`` also put FR
    IDs here, and enforcing one slot while ignoring the other lets a user fix
    the half that fails, re-run to a clean exit, and ship the other half —
    where a downstream test/code consumer will read a requirement ID as a
    path.

    Only an entry that resolves to a known requirement is flagged, so a real
    file path can never trip this.
    """
    findings: List[Finding] = []
    for req in sorted(req_index.values(), key=lambda r: r.req_id):
        for slot, targets in (("tests", req.traces_to_tests), ("code", req.traces_to_code)):
            for target in targets:
                if target not in req_index:
                    continue
                findings.append(Finding(
                    rule="misplaced-requirement-trace",
                    severity=ERROR,
                    artifact_id=req.req_id,
                    path=req.path,
                    message=(
                        f"traces_to.{slot} -> '{target}' is a requirement id; "
                        f"this slot holds {'test' if slot == 'tests' else 'source-file'} "
                        f"references only. Move the edge: delete it here and add "
                        f"'{req.req_id}' to {target}'s own traces_from"
                    ),
                ))
    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def index_caveat_findings(skipped: List[str], duplicates: List[str]) -> List[Finding]:
    """Turn the two index caveats into findings.

    They are findings and not header prose because every consumer of this tool
    reads findings: the warning count, ``--strict``, the ``--json`` payload and
    the formatter's ``traceability_rerun.warnings`` hand-off. A caveat carried
    outside that channel is a caveat that gets dropped at the first boundary,
    and the contract downstream reads an empty warnings list as proof the
    sweep was clean. A sweep over an index that is missing files or has
    collapsed two artifacts into one ID is not clean; it is unreliable in both
    directions, and it has to say so where it will be heard.
    """
    findings: List[Finding] = []
    for path in skipped:
        findings.append(Finding(
            rule="index-unparseable",
            severity=WARN,
            artifact_id="-",
            path=path,
            message=(
                "frontmatter did not parse, so this file is absent from the "
                "index and every result computed over it may be wrong in "
                "either direction. Run the structural validators for details"
            ),
        ))
    for dup in duplicates:
        findings.append(Finding(
            rule="duplicate-id",
            severity=WARN,
            artifact_id=dup,
            path="-",
            message=(
                "declared by more than one file; only the last was indexed, so "
                "results for this id may be wrong in either direction. Run the "
                "structural validators for details"
            ),
        ))
    return findings


def collect_findings(
    design_dir: str, reqs_dir: str, qa_dir: Optional[str] = None
) -> Tuple[List[Finding], int, int, List[str], List[str]]:
    """Run every rule.

    Returns (findings, design_count, req_count, skipped, duplicate_ids).

    ``qa_dir`` defaults to None — the design stage runs this tool at its own
    Step 4, long before any QA artifact exists, and a path default would make
    every M2 run report a missing directory. When it is None, the QA index is
    never built and neither QA rule runs; the caller does not merely see an
    empty QA set, which would report every architecturally significant
    requirement as uncovered.
    """
    req_index, req_skipped, req_dupes = index_requirements(reqs_dir)
    design_index, design_skipped, design_dupes = index_design(design_dir)

    skipped = req_skipped + design_skipped
    duplicates = req_dupes + design_dupes

    findings: List[Finding] = []
    findings.extend(rule_dangling_trace(design_index, req_index))
    findings.extend(rule_uncovered_fr(design_index, req_index))
    findings.extend(rule_adr_drivers(design_index, req_index, design_dir))
    findings.extend(rule_dangling_reverse_trace(req_index, design_index))
    findings.extend(rule_misplaced_requirement_trace(req_index))

    if qa_dir is not None:
        qa_index, qa_skipped, qa_dupes = index_qa(qa_dir)
        skipped = skipped + qa_skipped
        duplicates = duplicates + qa_dupes
        findings.extend(rule_dangling_qa_trace(qa_index, req_index, design_index))
        findings.extend(rule_uncovered_asr(req_index, qa_index, design_dir))

    duplicates = sorted(set(duplicates))
    findings.extend(index_caveat_findings(skipped, duplicates))

    return findings, len(design_index), len(req_index), skipped, duplicates


def print_report(
    findings: List[Finding],
    design_dir: str,
    reqs_dir: str,
    design_count: int,
    req_count: int,
    skipped: List[str],
    duplicates: List[str],
    quiet: bool,
) -> None:
    print(f"Validating traceability: {design_dir} <-> {reqs_dir}")
    print(f"Indexed {design_count} design artifact(s), {req_count} requirement(s).")
    if not core.HAVE_YAML:
        # The two structural validators announce this; so must this one. Its
        # whole job is reading list fields out of frontmatter, and the stdlib
        # fallback is the less faithful parser — a user who cannot see which
        # parser ran cannot judge a clean result.
        print(
            "WARNING: running in reduced (stdlib fallback) mode; "
            "install pyyaml for full-fidelity frontmatter parsing."
        )
    if skipped or duplicates:
        print(
            f"WARNING: index is incomplete — {len(skipped)} unparseable file(s), "
            f"{len(duplicates)} duplicate id(s); see the warning lines below."
        )
    print("-" * 60)
    # --quiet suppresses the warning listing only. Error lines always print:
    # this is a gate, and a gate that hides what failed is useless. Matches
    # validate_design.py and validate_requirements.py, whose --quiet drops
    # PASS lines and keeps failures.
    for f in sorted(
        findings, key=lambda f: (_SEVERITY_ORDER[f.severity], f.rule, f.artifact_id)
    ):
        if quiet and f.severity != ERROR:
            continue
        # The path is printed, not just carried in --json. Both agent contracts
        # require the stage to name the offending file, and the formatter runs
        # this tool without --json — so a path that only exists in the JSON
        # payload is a path the agent has to guess at.
        print(
            f"  {f.severity.upper():<6} {f.rule:<28} {f.artifact_id:<10} "
            f"{f.message} [{f.path}]"
        )
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
    parser.add_argument(
        "--qa",
        default=None,
        help="Directory of QA files (default: none — QA rules are skipped).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero on warnings as well as errors."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress warning lines; error lines and the summary always print.",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.design_dir):
        print(f"ERROR: design directory not found: {args.design_dir}", file=sys.stderr)
        return 2
    if not os.path.isdir(args.requirements):
        print(f"ERROR: requirements directory not found: {args.requirements}", file=sys.stderr)
        return 2
    if args.qa is not None and not os.path.isdir(args.qa):
        print(f"ERROR: qa directory not found: {args.qa}", file=sys.stderr)
        return 2

    findings, design_count, req_count, skipped, duplicates = collect_findings(
        args.design_dir, args.requirements, args.qa
    )
    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)

    if args.json:
        # `skipped` and `duplicate_ids` carry the same caveats the human report
        # prints in its header: without them a consumer cannot tell that
        # coverage was computed over an incomplete or collapsed index.
        print(json.dumps(
            {
                "findings": [asdict(f) for f in findings],
                "counts": {"error": errors, "warn": warns},
                "skipped": skipped,
                "duplicate_ids": duplicates,
            },
            indent=2,
        ))
    else:
        print_report(
            findings, args.design_dir, args.requirements,
            design_count, req_count, skipped, duplicates, args.quiet,
        )

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

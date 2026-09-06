#!/usr/bin/env python3
"""Export machine-readable reference data for the documentation site (STO-250).

Reads the repository's own sources of truth — the two content linters' RULES
registries, both artifact JSON Schemas, and the agent frontmatter — and writes
JSON into ``site/content/_generated/`` for the site to render.

Python rather than Node because it *imports* the linter modules and reads
their actual registries, instead of regexing Python source from JavaScript.

The outputs are committed and the site build does not run this script; CI
re-runs it and fails on any diff, so a change to a rule cannot land without
the published reference changing with it.

Stdlib only, like every other script in this repository.

Usage
-----
    python3 site/scripts/export_reference.py
    python3 site/scripts/export_reference.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "site", "content", "_generated")

# The linters bootstrap lib/ onto sys.path themselves when imported; this only
# has to make the linter modules findable.
for _scripts_dir in (
    os.path.join(REPO_ROOT, "skills", "design", "scripts"),
    os.path.join(REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)

import lint_design_content as ldc  # noqa: E402
import lint_requirements_content as lrc  # noqa: E402
import validate_traceability as vt  # noqa: E402


def export_rules() -> Dict[str, Any]:
    """All three linters' rule registries, verbatim.

    Deliberately does not restate or reformat rule text: the registry is the
    source, and any transformation here would be a place for drift to live.
    The design and requirements registries are advisory; the traceability
    registry is gating.
    """
    return {
        "design": {
            "linter": "lint_design_content.py",
            "rules": ldc.RULES,
        },
        "requirements": {
            "linter": "lint_requirements_content.py",
            "rules": lrc.RULES,
        },
        "traceability": {
            "linter": "validate_traceability.py",
            "rules": vt.RULES,
        },
    }


SCHEMAS = {
    "design": os.path.join(
        REPO_ROOT, "skills", "design", "schema", "design.schema.json"
    ),
    "requirements": os.path.join(
        REPO_ROOT, "skills", "requirements", "schema", "requirement.schema.json"
    ),
}

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_FENCED_BLOCK_RE = re.compile(r"^```.*?^```\s*$", re.DOTALL | re.MULTILINE)
_H1_RE = re.compile(r"^# (.+)$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(
    r"\A---\s*\n\s*description:\s*(.+?)\s*\n---\s*$", re.MULTILINE
)


def _field_entry(name: str, prop: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": name,
        "type": prop.get("type", ""),
        "enum": prop.get("enum", []),
        "required_for": [],
        "description": prop.get("description", ""),
    }


def _schema_fields(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten one artifact schema into a renderable field list.

    Both schemas share a shape: a base ``properties``/``required`` block, then
    an ``allOf`` of ``if type == <const>`` / ``then`` branches. A branch may
    add properties (design), or only mark an existing base property required
    for one type (requirements' ``ears_pattern``) — both are handled.

    Nested ``allOf`` inside a ``then`` is not descended into. Today that only
    affects two ADR/diagram sub-constraints, neither of which introduces a
    field name the base or branch blocks do not already declare.
    """
    fields: List[Dict[str, Any]] = []
    by_name: Dict[str, Dict[str, Any]] = {}

    for name, prop in schema.get("properties", {}).items():
        entry = _field_entry(name, prop)
        fields.append(entry)
        by_name[name] = entry

    for name in schema.get("required", []):
        if name in by_name:
            by_name[name]["required_for"] = ["*"]

    for branch in schema.get("allOf", []):
        const = (
            branch.get("if", {})
            .get("properties", {})
            .get("type", {})
            .get("const")
        )
        if const is None:
            continue
        then = branch.get("then", {})
        for name, prop in then.get("properties", {}).items():
            if name not in by_name:
                entry = _field_entry(name, prop)
                fields.append(entry)
                by_name[name] = entry
        for name in then.get("required", []):
            entry = by_name.get(name)
            if entry is None:
                continue
            if entry["required_for"] == ["*"]:
                continue
            if const not in entry["required_for"]:
                entry["required_for"].append(const)

    return fields


def export_fields() -> Dict[str, List[Dict[str, Any]]]:
    """Frontmatter field tables, read from the two canonical JSON Schemas."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    for stage, path in SCHEMAS.items():
        with open(path, "r", encoding="utf-8") as handle:
            out[stage] = _schema_fields(json.load(handle))
    return out


def _parse_agent_file(text: str, name: str) -> Dict[str, str]:
    """Parse one agent file's frontmatter description and body H1 title.

    The title is the first ``# `` heading in the file's BODY — after the
    closing frontmatter fence, and outside any fenced (``` ``` ```) code
    block — not the first ``# ``-shaped line anywhere in the file. Eight of
    the fifteen current agent files contain additional ``# ``-shaped lines
    later in the body, inside fenced blocks that show example artifacts the
    agent writes (e.g. ``# CMP-001 — Example Component``). A naive
    first-match-anywhere search happens to return the correct title today
    only because the real title always sits at line 5, before any example
    block. If a file's real title were ever preceded by an example block
    containing an H1-shaped line, first-match-anywhere — and even a search
    merely anchored past the frontmatter fence — would silently return the
    wrong title, since the fenced heading would still be the first ``# ``
    line encountered. Nothing would catch that: the drift gate only compares
    the committed JSON to what this function currently produces, so a
    consistently wrong extraction reads as "current" forever. Stripping
    fenced blocks from the body before searching removes that hazard
    regardless of where the example block sits relative to the real title.

    The description parser expects exactly the three-line frontmatter block
    every current agent file uses (``---`` / ``description: ...`` / ``---``).
    A second frontmatter key alongside ``description`` does not match this
    pattern and silently yields an empty description string rather than
    raising — there is no signal that the parse degraded. Whoever adds a
    second frontmatter key to an agent file next must re-verify
    ``export_agents()`` by hand; this function will not warn them.
    """
    frontmatter = _FRONTMATTER_RE.match(text)
    body = text[frontmatter.end():] if frontmatter else text
    heading = _H1_RE.search(_FENCED_BLOCK_RE.sub("", body))
    description = _DESCRIPTION_RE.search(text)
    raw = description.group(1).strip() if description else ""
    # Strips one matching outer quote pair only. A description that merely
    # begins and ends with quoted sub-phrases (no single pair wrapping the
    # whole string) would be corrupted by this — not reachable in any
    # current file, but a trap for whoever edits this next.
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1]
    return {
        "name": name,
        "title": heading.group(1).strip() if heading else "",
        "description": raw,
    }


def export_agents() -> List[Dict[str, str]]:
    """The agent roster, from each file's frontmatter description and H1.

    Every agent file carries a three-line frontmatter block whose single key
    is ``description``; the agent's name is its filename, not a frontmatter
    field. Per-file parsing is delegated to ``_parse_agent_file`` — see its
    docstring for what the extraction does and does not cover.
    """
    agents_dir = os.path.join(REPO_ROOT, "agents")
    out: List[Dict[str, str]] = []
    for filename in sorted(os.listdir(agents_dir)):
        if not filename.endswith(".md"):
            continue
        with open(
            os.path.join(agents_dir, filename), "r", encoding="utf-8"
        ) as handle:
            text = handle.read()
        out.append(_parse_agent_file(text, filename[:-3]))
    return out


# The two interviews' coverage areas, by the exact line each list follows.
# Anchors rather than heading names because the two skills phrase the
# introduction differently and neither is a heading.
STAGE_SOURCES = {
    "requirements": {
        "skill": "skills/requirements/SKILL.md",
        "heading": "**Coverage areas:**",
    },
    "design": {
        "skill": "skills/design/SKILL.md",
        "heading": (
            "Six coverage areas the requirement set cannot carry, "
            "by construction:"
        ),
    },
}

_AREA_ITEM_RE = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s+—\s+(.+)$")


def _coverage_areas(text: str, anchor: str) -> List[Dict[str, str]]:
    """Parse the numbered coverage-area list that follows ``anchor``.

    Raises rather than returning an empty list when the anchor moves or the
    list shape changes. A parser that degrades silently here would be worse
    than none: the drift gate only compares the committed JSON to what this
    function currently produces, so a consistently empty extraction reads as
    "current" forever and the published page quietly lists nothing.
    """
    index = text.find(anchor)
    if index == -1:
        raise ValueError(f"anchor not found: {anchor!r}")

    areas: List[Dict[str, str]] = []
    for line in text[index + len(anchor):].splitlines():
        stripped = line.strip()
        if not stripped:
            if areas:
                break
            continue
        match = _AREA_ITEM_RE.match(stripped)
        if not match:
            break
        areas.append(
            {"name": match.group(1).strip(), "detail": match.group(2).strip()}
        )

    if not areas:
        raise ValueError(f"no numbered areas found after anchor: {anchor!r}")
    return areas


def export_stages() -> Dict[str, Dict[str, Any]]:
    """The two interviews' coverage areas, read from the skill files.

    Deliberately narrow. Generating the area *names* means a page cannot list
    five areas when the skill has six. Generating the surrounding narrative
    would turn the two stage pages into tables, which is the opposite of what
    they are for.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for stage, source in STAGE_SOURCES.items():
        path = os.path.join(REPO_ROOT, source["skill"])
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out[stage] = {
            "skill": source["skill"],
            "heading": source["heading"],
            "areas": _coverage_areas(text, source["heading"]),
        }
    return out


# The two orchestrators are the only files that own hand-off contracts. Every
# other agent consumes or returns one; neither describes the pipeline.
PIPELINE_SOURCES = {
    "requirements": "agents/requirements-orchestrator.md",
    "design": "agents/design-orchestrator.md",
}

_STAGE_HEADING_RE = re.compile(r"^## Stage ([\d.]+) — (.+)$", re.M)
_YAML_BLOCK_RE = re.compile(r"^```yaml\n(.*?)^```", re.M | re.S)
_TOP_KEY_RE = re.compile(r"^([a-z_][a-z0-9_]*):", re.M)
_TRANSIENT_RE = re.compile(r"^\s*([a-z_][a-z0-9_]*):.*TRANSIENT", re.M)

# A heading names a contract when a backticked identifier follows the word
# "the": "Dispatch: the `generation_brief` hand-off", "Synthesise the
# `design_context_artifact`". Two shapes are deliberately NOT matched.
# "Back-fill `depends_on`" backticks a field and carries no YAML — keying on
# "the heading contains backticks" would raise on a stage that was never a
# contract. "Consume the clarification context" has the word but no backticks,
# so an intermediate shape is not promoted to a published contract. Keying on
# "the `x`" rather than on the verb is what lets the two orchestrators keep
# spelling Synthesi[sz]e differently without either one dropping out.
_CONTRACT_CLAUSE_RE = re.compile(r"\bthe ((?:`[a-z_][a-z0-9_]*`(?:\s*/\s*)?)+)")
_BACKTICKED_RE = re.compile(r"`([a-z_][a-z0-9_]*)`")


def _contract_names(label: str) -> List[str]:
    """The contract names a stage heading declares, in heading order."""
    clause = _CONTRACT_CLAUSE_RE.search(label)
    return _BACKTICKED_RE.findall(clause.group(1)) if clause else []


def _yaml_segments(section: str) -> Dict[str, str]:
    """Every top-level YAML key in a stage's section, mapped to its slice.

    A section may hold several fenced blocks, and one block may hold several
    top-level keys — design Stage 6 defines ``draft_components`` and
    ``draft_interfaces`` in a single fence, and design Stage 8 opens with a
    ``capability_map`` block before the ``critique_report`` its heading names.
    Slicing by top-level key rather than by block is what makes both come out
    right; taking "the first block after the heading" publishes Stage 8's
    wrong shape under the right name, and nothing downstream could tell.
    """
    segments: Dict[str, str] = {}
    for block in _YAML_BLOCK_RE.findall(section):
        keys = list(_TOP_KEY_RE.finditer(block))
        for index, key in enumerate(keys):
            end = keys[index + 1].start() if index + 1 < len(keys) else len(block)
            segments[key.group(1)] = block[key.start():end].rstrip() + "\n"
    return segments


def _parse_pipeline(text: str, source: str) -> List[Dict[str, Any]]:
    """One orchestrator's stages, in file order, with the contracts they own.

    Raises when a heading names a contract its own section does not define.
    That assertion is the reason this parser exists in this shape: the drift
    gate only compares committed JSON against current output, so a heading
    renamed without its YAML would quietly shrink the published table and CI
    would stay green on JSON that still matched itself. Failing loudly here is
    the same standard ``_coverage_areas`` holds for its anchor.
    """
    headings = list(_STAGE_HEADING_RE.finditer(text))
    if not headings:
        raise ValueError(f"no stage headings found in {source}")

    stages: List[Dict[str, Any]] = []
    for index, heading in enumerate(headings):
        end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(text)
        )
        section = text[heading.start():end]
        label = heading.group(2).strip()
        segments = _yaml_segments(section)

        contracts: List[Dict[str, Any]] = []
        for name in _contract_names(label):
            if name not in segments:
                found = ", ".join(sorted(segments)) or "none"
                raise ValueError(
                    f"{source} Stage {heading.group(1)} names `{name}` but its "
                    f"section defines no such top-level YAML key (found: {found})"
                )
            body = segments[name]
            contracts.append(
                {
                    "name": name,
                    "yaml": body,
                    "transients": sorted(set(_TRANSIENT_RE.findall(body))),
                }
            )

        stages.append(
            {
                "number": heading.group(1),
                "label": label,
                "retired": label == "(retired)",
                "contracts": contracts,
            }
        )
    return stages


def export_pipeline() -> Dict[str, Any]:
    """The two stages' agent order and hand-off contracts, from the source.

    Deliberately carries contract YAML as text rather than parsing it. These
    blocks are illustrative shapes with inline comments — the ``# ← TRANSIENT``
    markers among them — not loadable documents, and every script in this
    repository is stdlib-only. Rendering the text verbatim is also what makes
    the published contract and the agent's own contract the same bytes.
    """
    out: Dict[str, Any] = {}
    for stage, source in PIPELINE_SOURCES.items():
        path = os.path.join(REPO_ROOT, source)
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out[stage] = {
            "agent": os.path.basename(source)[:-len(".md")],
            "source": source,
            "stages": _parse_pipeline(text, source),
        }
    return out


def _serialize(payload: Any) -> str:
    """The single definition of what a committed reference file contains.

    Both write_json and --check go through this. If they ever computed the
    serialization separately, the gate could pass over a stale file.
    """
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_json(name: str, payload: Any) -> str:
    """Write ``payload`` to ``OUT_DIR/name``, stably and diff-cleanly."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(_serialize(payload))
    return path


OUTPUTS = {
    "rules.json": export_rules,
    "fields.json": export_fields,
    "agents.json": export_agents,
    "stages.json": export_stages,
    "pipeline.json": export_pipeline,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export reference data for the Groundwork docs site."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any committed output is stale, writing nothing",
    )
    args = parser.parse_args(argv)

    stale: List[str] = []
    for name, builder in sorted(OUTPUTS.items()):
        payload = builder()
        path = os.path.join(OUT_DIR, name)
        if args.check:
            expected = _serialize(payload)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    if handle.read() != expected:
                        stale.append(name)
            except (OSError, UnicodeDecodeError):
                stale.append(name)
        else:
            write_json(name, payload)

    if args.check and stale:
        for name in stale:
            print(f"stale: site/content/_generated/{name}", file=sys.stderr)
        print(
            "run: python3 site/scripts/export_reference.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

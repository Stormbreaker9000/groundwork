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

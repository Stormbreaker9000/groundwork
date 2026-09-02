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


def export_rules() -> Dict[str, Any]:
    """Both linters' rule registries, verbatim.

    Deliberately does not restate or reformat rule text: the registry is the
    source, and any transformation here would be a place for drift to live.
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
    }


SCHEMAS = {
    "design": os.path.join(
        REPO_ROOT, "skills", "design", "schema", "design.schema.json"
    ),
    "requirements": os.path.join(
        REPO_ROOT, "skills", "requirements", "schema", "requirement.schema.json"
    ),
}

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


def export_agents() -> List[Dict[str, str]]:
    """The agent roster, from each file's frontmatter description and H1.

    Every agent file carries a three-line frontmatter block whose single key
    is ``description``; the agent's name is its filename, not a frontmatter
    field. ``test_export_agents_reads_title_and_description`` fails if that
    stops being true.
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
        heading = _H1_RE.search(text)
        description = _DESCRIPTION_RE.search(text)
        raw = description.group(1).strip() if description else ""
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        out.append(
            {
                "name": filename[:-3],
                "title": heading.group(1).strip() if heading else "",
                "description": raw,
            }
        )
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

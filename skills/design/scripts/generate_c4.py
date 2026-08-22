#!/usr/bin/env python3
"""Deterministic C4 view generation for Groundwork design sets (STO-101).

The component graph is already fully described in frontmatter::

    CMP.depends_on -> IF.provider

so the three C4 views are a projection of the artifact set, not a new authored
document. This tool performs that projection. Everything it cannot derive —
which components group into which container, and who the external actors are —
arrives as a `draft_diagram_model` produced by the `c4-generator` agent at
pipeline Stage 9.6.

Run by the design formatter over the files it has just written, so the
formatter stays the single writer and `validate_design.py` runs once, over
everything. It re-runs standalone over any existing design set.

Usage
-----
    python3 generate_c4.py DESIGN_DIR --model model.json [--created-at DATE]

Prints a JSON summary on stdout: the diagrams written, and the
`traces_to.diagrams` back-fill the formatter applies.

Exit codes
----------
    0  diagrams written
    1  the model contradicts the design set
    2  usage / environment error (dir missing, model unreadable)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import artifact_core as core  # noqa: E402
from artifact_core import parse_frontmatter  # noqa: E402

SYSTEM_ALIAS = "sys"

# drivers.md's ASR section, written by the formatter at Stage 10 before this
# tool runs. One requirement per line: `- FR-001: high_impact_function (…)`.
ASR_HEADING = "## Architecturally Significant Requirements"
_ASR_LINE_RE = re.compile(r"^-\s+([A-Z]+(?:-[A-Z0-9]+)*-[0-9]{3,})\s*:")


def alias_for(artifact_id: str, boundary: Optional[str] = None) -> str:
    base = artifact_id.lower().replace("-", "_")
    return f"ext_{base}" if boundary == "external" else base


def container_alias(key: str) -> str:
    return "ctr_" + key.lower().replace("-", "_")


def actor_alias(key: str) -> str:
    return "actor_" + key.lower().replace("-", "_")


def q(text: Any) -> str:
    """A Mermaid string literal. Inner quotes become single quotes rather than
    escapes: Mermaid has no escape syntax inside these, and an unbalanced quote
    is exactly what validate_design.py rejects."""
    return '"' + str(text or "").replace('"', "'").replace("\n", " ").strip() + '"'


class DesignSet:
    """The components, interfaces and ASRs of one design directory."""

    def __init__(self, components, interfaces, asrs):
        self.components = components
        self.interfaces = interfaces
        self.asrs = asrs

    @classmethod
    def load(cls, design_dir: str) -> "DesignSet":
        components: Dict[str, dict] = {}
        interfaces: Dict[str, dict] = {}
        for path in core.discover_files(design_dir, {"assumptions.md", "drivers.md",
                                                     "index.yaml"}, {"diagrams"}):
            data, err = parse_frontmatter(path)
            if err or not isinstance(data, dict):
                continue
            artifact_id = data.get("id")
            if data.get("type") == "component" and artifact_id:
                components[artifact_id] = data
            elif data.get("type") == "interface" and artifact_id:
                interfaces[artifact_id] = data
        return cls(components, interfaces, cls._read_asrs(design_dir))

    @staticmethod
    def _read_asrs(design_dir: str) -> List[str]:
        path = os.path.join(design_dir, "drivers.md")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError:
            return []
        section = text.split(ASR_HEADING, 1)
        if len(section) < 2:
            return []
        out: List[str] = []
        for line in section[1].splitlines():
            if line.startswith("## "):
                break
            match = _ASR_LINE_RE.match(line.strip())
            if match and match.group(1) not in out:
                out.append(match.group(1))
        return out

    def boundary(self, cmp_id: str) -> str:
        return self.components.get(cmp_id, {}).get("boundary", "internal")

    def alias(self, cmp_id: str) -> str:
        return alias_for(cmp_id, self.boundary(cmp_id))

    def edges(self) -> List[Tuple[str, str, str]]:
        """``(consumer, provider, interface)`` for every CMP -> IF -> CMP edge."""
        out = []
        for cmp_id in sorted(self.components):
            for if_id in sorted(self.components[cmp_id].get("depends_on") or []):
                provider = (self.interfaces.get(if_id) or {}).get("provider")
                if provider:
                    out.append((cmp_id, provider, if_id))
        return sorted(set(out))

    def title(self, artifact_id: str) -> str:
        record = self.components.get(artifact_id) or self.interfaces.get(artifact_id)
        return (record or {}).get("title", artifact_id)

    def traces_for(self, cmp_ids) -> List[str]:
        out: Set[str] = set()
        for cmp_id in cmp_ids:
            out.update(self.components.get(cmp_id, {}).get("traces_from") or [])
        return sorted(out)


def validate_model(model: dict, dset: DesignSet) -> List[str]:
    """The Stage 9.6 invariant: every internal component in exactly one
    container, and nothing else placed in one."""
    errors: List[str] = []
    placement: Dict[str, List[str]] = {}
    for container in model.get("containers") or []:
        key = container.get("key")
        if not key:
            errors.append("a container has no 'key'")
            continue
        for cmp_id in container.get("components") or []:
            placement.setdefault(cmp_id, []).append(key)

    for cmp_id, keys in sorted(placement.items()):
        if cmp_id not in dset.components:
            errors.append(f"container '{keys[0]}' lists '{cmp_id}', which is not a "
                          f"component in this design set")
        elif dset.boundary(cmp_id) == "external":
            errors.append(f"'{cmp_id}' is boundary: external and cannot be placed in "
                          f"container '{keys[0]}' — externals sit outside every "
                          f"container by definition")
        elif len(keys) > 1:
            errors.append(f"'{cmp_id}' is placed in two containers "
                          f"({', '.join(sorted(keys))}) — it belongs to exactly one")

    for cmp_id in sorted(dset.components):
        if dset.boundary(cmp_id) == "internal" and cmp_id not in placement:
            errors.append(f"'{cmp_id}' is placed in no container")

    known = {c.get("key") for c in model.get("containers") or []}
    for actor in model.get("actors") or []:
        entrypoint = actor.get("entrypoint")
        if entrypoint and entrypoint not in known:
            errors.append(f"actor '{actor.get('key')}' enters at '{entrypoint}', "
                          f"which is not a container in this model")
    return errors


def render_context(model: dict, dset: DesignSet) -> str:
    """C4Context: actors, one system box, and the external systems it reaches."""
    lines = ["C4Context", f"  title System Context — {model['system_name']}"]
    for actor in sorted(model.get("actors") or [], key=lambda a: a["key"]):
        lines.append(
            f"  Person({actor_alias(actor['key'])}, {q(actor['name'])}, "
            f"{q(actor.get('description'))})"
        )
    lines.append(
        f"  System({SYSTEM_ALIAS}, {q(model['system_name'])}, "
        f"{q(model.get('system_description'))})"
    )
    externals = [c for c in sorted(dset.components) if dset.boundary(c) == "external"]
    for cmp_id in externals:
        record = dset.components[cmp_id]
        lines.append(
            f"  System_Ext({dset.alias(cmp_id)}, {q(record.get('title'))}, "
            f"{q(record.get('responsibility'))})"
        )
    for actor in sorted(model.get("actors") or [], key=lambda a: a["key"]):
        lines.append(
            f"  Rel({actor_alias(actor['key'])}, {SYSTEM_ALIAS}, "
            f"{q(actor.get('relationship', 'uses'))})"
        )
    for consumer, provider, if_id in dset.edges():
        c_ext = dset.boundary(consumer) == "external"
        p_ext = dset.boundary(provider) == "external"
        if c_ext == p_ext:
            continue  # wholly inside or wholly outside: not a context-level fact
        src = dset.alias(consumer) if c_ext else SYSTEM_ALIAS
        dst = dset.alias(provider) if p_ext else SYSTEM_ALIAS
        lines.append(f"  Rel({src}, {dst}, {q(dset.title(if_id))}, {q(if_id)})")
    return "\n".join(lines)


def write_diagram(out_dir, *, dia_id, title, level, container, description,
                  traces_from, confidence, created_at, block) -> str:
    """Write one diagram artifact. Frontmatter key order is fixed, so a
    regenerated set diffs only where the design actually changed."""
    os.makedirs(out_dir, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = os.path.join(out_dir, f"{dia_id}-{slug}.md")
    front = [
        "---",
        f"id: {dia_id}",
        "type: diagram",
        f"title: {title}",
        f"description: {description}",
        f"level: {level}",
    ]
    if container:
        front.append(f"container: {container}")
    front.extend([
        f"traces_from: [{', '.join(traces_from)}]",
        "traces_to: {}",
        "status: draft",
        f"confidence: {confidence}",
        f"created_at: {created_at}",
        "---",
    ])
    body = "\n".join(front) + f"\n\n# {title}\n\n```mermaid\n{block}\n```\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


def generate(design_dir: str, model: dict, created_at: str) -> dict:
    """Write every view and return the JSON summary."""
    dset = DesignSet.load(design_dir)
    out_dir = os.path.join(design_dir, "diagrams")
    confidence = model.get("confidence", "high")
    written = []

    externals = [c for c in sorted(dset.components) if dset.boundary(c) == "external"]
    path = write_diagram(
        out_dir,
        dia_id="DIA-001",
        title="System Context",
        level="context",
        container=None,
        description=(
            f"System context for {model['system_name']}: its actors, its "
            f"boundary, and the external systems it depends on."
        ),
        traces_from=dset.asrs,
        confidence=confidence,
        created_at=created_at,
        block=render_context(model, dset),
    )
    written.append({"id": "DIA-001", "path": path, "level": "context",
                    "depicts": externals})

    back_fill: Dict[str, List[str]] = {}
    for entry in written:
        for cmp_id in entry["depicts"]:
            back_fill.setdefault(cmp_id, []).append(entry["id"])
    return {"diagrams": written, "traces_to_diagrams":
            {k: sorted(v) for k, v in sorted(back_fill.items())}}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate C4 views for a design set.")
    parser.add_argument("design_dir", nargs="?", default=".sdlc/design")
    parser.add_argument("--model", required=True, help="draft_diagram_model JSON")
    parser.add_argument("--created-at", default=None,
                        help="YYYY-MM-DD stamped on every diagram")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.design_dir):
        print(f"error: no such design directory: {args.design_dir}", file=sys.stderr)
        return 2
    try:
        with open(args.model, "r", encoding="utf-8") as handle:
            model = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"error: could not read model: {exc}", file=sys.stderr)
        return 2

    dset = DesignSet.load(args.design_dir)
    errors = validate_model(model, dset)
    if errors:
        for err in errors:
            print(f"model: {err}", file=sys.stderr)
        return 1

    created_at = args.created_at or ""
    if not created_at:
        print("error: --created-at is required (diagrams must carry the same "
              "date as the rest of the set)", file=sys.stderr)
        return 2

    print(json.dumps(generate(args.design_dir, model, created_at), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

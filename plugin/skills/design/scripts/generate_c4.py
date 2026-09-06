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


# Bytes that corrupt one of the two downstream parsers if they survive into
# a quoted literal. C0 (0x00-0x1F — where a literal CR or LF live) and C1
# (0x80-0x9F — where NEL/U+0085 lives) control characters, DEL (0x7F), and
# the two multi-byte Unicode line-breaking characters (U+2028, U+2029) are
# every code point Python's ``str.splitlines()`` treats as a line break.
# `parse_frontmatter`'s stdlib fallback (`lib/artifact_core.py`) uses
# ``splitlines()`` to cut the frontmatter block into rows, so any one of
# these surviving into a value silently splits one field into two rows
# instead of raising — a title becomes a truncated value plus a stray
# sibling line. Folded to a space, not dropped, so word boundaries survive.
_HOSTILE_CONTROL_RE = re.compile("[\x00-\x1f\x7f\u0080-\u009f\u2028\u2029]")


def _sanitized(text: Any) -> str:
    """Baseline cleanup shared by every string literal this module emits:
    coerce to ``str``, fold an inner double quote to a single quote (both
    Mermaid and YAML use ``"`` as this module's literal delimiter, so a
    passed-through inner ``"`` would terminate the literal early), fold
    every control character and Unicode line/paragraph separator
    (`_HOSTILE_CONTROL_RE`, which includes an ordinary ``\\n``/``\\r``) to a
    space, and strip. Callers wrap the result in the delimiter quotes
    themselves; `q` and `yaml_q` each layer one more transform on top — see
    their docstrings for what and why."""
    value = str(text or "").replace('"', "'")
    value = _HOSTILE_CONTROL_RE.sub(" ", value)
    return value.strip()


def q(text: Any) -> str:
    """A Mermaid string literal. Consumed by exactly one parser (the Mermaid
    renderer embedded in `validate_design.py`'s body checks and in Mermaid
    itself), so there is no second parser to stay in agreement with — inner
    quotes become single quotes rather than escapes because Mermaid has no
    escape syntax inside these, and an unbalanced quote is exactly what
    validate_design.py rejects.

    A literal ``(`` or ``)`` is stripped, not preserved: `check_diagram_body`
    counts parens across the WHOLE rendered line — the surrounding
    ``Component(...)``/``Rel(...)`` call syntax included, not just this
    literal — so one stray paren in free-form source prose (a component's
    `responsibility`, an interface's title, ...) is enough to make an
    otherwise-correct line fail that check, and the error names the diagram
    rather than the prose that caused it. Mermaid does not require the
    character inside a label, and this generator is the only legitimate
    writer of a diagram body, so there is no hand-authored parenthesization
    in this text to preserve."""
    return '"' + _sanitized(text).replace("(", "").replace(")", "") + '"'


def yaml_q(text: Any) -> str:
    """A safe double-quoted YAML scalar for frontmatter values that may
    contain a colon (e.g. a generated description like "System context for
    Order System: its actors..."), which breaks YAML plain-scalar parsing.

    Unlike `q`, this string is read by TWO independent parsers that must
    agree byte-for-byte (pyyaml, and `lib/artifact_core.py`'s stdlib
    fallback — the determinism constraint requires a design set to validate
    identically whichever one is installed), and those two parsers disagree
    about backslash: pyyaml treats it as an escape introducer and unescapes
    it, while `_coerce_scalar` in the stdlib fallback strips only the
    surrounding quotes and does NOT unescape. The same source bytes would
    therefore decode to two different Python strings. Sanitize-then-quote,
    never escape, is the only way out of that: a backslash is folded to a
    forward slash — the same treatment already given to an inner double
    quote — rather than escaped, because the two parsers can only ever agree
    on bytes that need no escaping at all. Do not "fix" this back to
    `\\"` / `\\\\` — that reintroduces the exact divergence this exists
    to prevent.

    A literal `` #`` (space then hash) gets the same treatment for the same
    reason: `_strip_inline_comment` in the stdlib fallback truncates a value
    at the first `` #`` it finds, quoted or not, so an unfolded one would
    make pyyaml and the fallback read two different strings back — exactly
    the divergence this function exists to prevent. Folded to a single
    space rather than dropped, so a stray hash character alone (no leading
    space) is left untouched — only the two-character sequence is hostile."""
    value = _sanitized(text).replace("\\", "/")
    value = value.replace(" #", " ")
    return '"' + value + '"'


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
        """Every ASR ID in `drivers.md`'s ASR section, or ``[]``.

        An honest "no ASRs" `drivers.md` (the heading present, `- None
        identified.` under it) and a missing-or-unreadable `drivers.md` both
        legitimately return `[]` — but only the first is a legal outcome.
        The second is a malformed set silently shipping DIA-001 with an
        empty `traces_from`, so it gets a stderr warning distinguishing it
        from the honest case. This never changes the return value or this
        tool's exit code — `generate()` still runs on whatever ASRs it
        found, same as before; the warning is the only difference.
        """
        path = os.path.join(design_dir, "drivers.md")
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(f"warning: could not read {path} ({exc}) — diagram "
                  "traces_from will be empty", file=sys.stderr)
            return []
        section = text.split(ASR_HEADING, 1)
        if len(section) < 2:
            print(f"warning: {path} has no '{ASR_HEADING}' heading — "
                  "diagram traces_from will be empty", file=sys.stderr)
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
    seen_keys: Set[str] = set()
    for container in model.get("containers") or []:
        key = container.get("key")
        if not key:
            errors.append("a container has no 'key'")
            continue
        if key in seen_keys:
            errors.append(
                f"container key '{key}' is used by more than one container "
                f"— every container needs a distinct key"
            )
        else:
            seen_keys.add(key)
        if not container.get("components"):
            errors.append(
                f"container '{key}' has an empty 'components' list — a "
                f"container with nothing placed in it is not a deployable unit"
            )
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
    seen = set()
    for consumer, provider, if_id in dset.edges():
        c_ext = dset.boundary(consumer) == "external"
        p_ext = dset.boundary(provider) == "external"
        if c_ext == p_ext:
            continue  # wholly inside or wholly outside: not a context-level fact
        src = dset.alias(consumer) if c_ext else SYSTEM_ALIAS
        dst = dset.alias(provider) if p_ext else SYSTEM_ALIAS
        key = (src, dst, if_id)
        if key in seen:
            continue  # multiple internal components share this external fact
        seen.add(key)
        lines.append(f"  Rel({src}, {dst}, {q(dset.title(if_id))}, {q(if_id)})")
    return "\n".join(lines)


def container_of(model: dict) -> Dict[str, str]:
    """``{component id: container key}`` for every placed component."""
    out = {}
    for container in model.get("containers") or []:
        for cmp_id in container.get("components") or []:
            out[cmp_id] = container["key"]
    return out


def render_container(model: dict, dset: DesignSet) -> str:
    """C4Container: the deployable units, and every edge that leaves one."""
    placement = container_of(model)
    lines = ["C4Container", f"  title Container View — {model['system_name']}"]
    for actor in sorted(model.get("actors") or [], key=lambda a: a["key"]):
        lines.append(
            f"  Person({actor_alias(actor['key'])}, {q(actor['name'])}, "
            f"{q(actor.get('description'))})"
        )
    lines.append(f"  System_Boundary({SYSTEM_ALIAS}, {q(model['system_name'])}) {{")
    for container in sorted(model.get("containers") or [], key=lambda c: c["key"]):
        lines.append(
            f"    Container({container_alias(container['key'])}, "
            f"{q(container['name'])}, {q(container.get('technology'))}, "
            f"{q(container.get('description'))})"
        )
    lines.append("  }")
    for cmp_id in sorted(dset.components):
        if dset.boundary(cmp_id) != "external":
            continue
        record = dset.components[cmp_id]
        lines.append(
            f"  System_Ext({dset.alias(cmp_id)}, {q(record.get('title'))}, "
            f"{q(record.get('responsibility'))})"
        )
    for actor in sorted(model.get("actors") or [], key=lambda a: a["key"]):
        if actor.get("entrypoint"):
            lines.append(
                f"  Rel({actor_alias(actor['key'])}, "
                f"{container_alias(actor['entrypoint'])}, "
                f"{q(actor.get('relationship', 'uses'))})"
            )
    seen = set()
    for consumer, provider, if_id in dset.edges():
        src = (container_alias(placement[consumer]) if consumer in placement
               else dset.alias(consumer))
        dst = (container_alias(placement[provider]) if provider in placement
               else dset.alias(provider))
        if src == dst:
            continue  # intra-container: not a container-level fact
        key = (src, dst, if_id)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"  Rel({src}, {dst}, {q(dset.title(if_id))}, {q(if_id)})")
    return "\n".join(lines)


def render_component(model: dict, dset: DesignSet, container: dict) -> str:
    """C4Component: one container's internals, with every edge that touches it.

    An endpoint in another container renders as a ``Container()`` reference,
    never as a ``Component()`` — drawing it as a component would place it in
    two component views at once, which validate_design.py rejects.
    """
    placement = container_of(model)
    by_key = {c["key"]: c for c in model.get("containers") or []}
    members = sorted(container.get("components") or [])
    lines = ["C4Component", f"  title Component View — {container['name']}"]
    lines.append(
        f"  Container_Boundary({container_alias(container['key'])}, "
        f"{q(container['name'])}) {{"
    )
    for cmp_id in members:
        record = dset.components[cmp_id]
        lines.append(
            f"    Component({dset.alias(cmp_id)}, {q(record.get('title'))}, "
            f"{q(container.get('technology'))}, {q(record.get('responsibility'))})"
        )
    lines.append("  }")

    member_set = set(members)
    touching = [e for e in dset.edges() if e[0] in member_set or e[1] in member_set]

    for key in sorted({placement[c] for e in touching for c in (e[0], e[1])
                       if c in placement and placement[c] != container["key"]}):
        other = by_key[key]
        lines.append(
            f"  Container({container_alias(key)}, {q(other['name'])}, "
            f"{q(other.get('technology'))}, {q(other.get('description'))})"
        )
    for cmp_id in sorted({c for e in touching for c in (e[0], e[1])
                          if dset.boundary(c) == "external"}):
        record = dset.components[cmp_id]
        lines.append(
            f"  System_Ext({dset.alias(cmp_id)}, {q(record.get('title'))}, "
            f"{q(record.get('responsibility'))})"
        )

    def endpoint(cmp_id):
        if cmp_id in member_set or cmp_id not in placement:
            return dset.alias(cmp_id)
        return container_alias(placement[cmp_id])

    seen = set()
    for consumer, provider, if_id in touching:
        key = (endpoint(consumer), endpoint(provider), if_id)
        if key[0] == key[1] or key in seen:
            continue
        seen.add(key)
        lines.append(f"  Rel({key[0]}, {key[1]}, {q(dset.title(if_id))}, {q(if_id)})")
    return "\n".join(lines)


# A regenerated diagram file is named from the model's current `title` (see
# write_diagram), so any rename — a container's `name`, a component's
# `title` feeding a component-view title — leaves the OLD filename behind
# under a NEW one written alongside it. Both then sit in `out_dir`: one
# `DIA-004-...md` claiming an ID the other file also claims, and
# validate_design.py rejects the duplicate. Deliberately narrow: only files
# directly in `out_dir` (`os.listdir`, never a recursive walk) whose
# basename matches this pattern, and only when this run did not just write
# them. This script runs inside real user projects, so widening this glob —
# by pattern or by recursion — is not a refactor to make casually; if it
# ever needs to change, re-justify it here.
#
# "Did not just write" is decided by file identity, not by spelling. The
# run knows the names it chose; `os.listdir` reports the names the
# directory holds, and on a case-insensitive filesystem those differ: a
# diagram manually renamed to `DIA-004-Component-View-Worker.md` is
# reopened and rewritten by `open()` under the lower-cased name, yet still
# listed under the old casing. Matched by name it reads as stale, and
# deleting it would destroy the file this run had just written.
_STALE_DIAGRAM_RE = re.compile(r"^DIA-\d+.*\.md$")


def _file_identity(path: str) -> Optional[Tuple[int, int]]:
    """``(device, inode)`` — what makes two names the same file. ``None``
    when the path cannot be stat'd."""
    try:
        info = os.stat(path)
    except OSError:
        return None
    return (info.st_dev, info.st_ino)


def _remove_stale_diagrams(out_dir: str, written_paths: Set[str]) -> List[str]:
    """Delete a prior run's ``DIA-*.md`` files this run did not just write.

    See the module-level comment on `_STALE_DIAGRAM_RE` for the narrow
    deletion guard. Returns the removed paths, sorted, for the JSON summary.
    """
    removed: List[str] = []
    if not os.path.isdir(out_dir):
        return removed
    written_ids = {ident for ident in map(_file_identity, written_paths)
                   if ident is not None}
    for name in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, name)
        if not os.path.isfile(path):
            continue  # narrow to files; never descend into a subdirectory
        if not _STALE_DIAGRAM_RE.match(name):
            continue
        if _file_identity(path) in written_ids:
            continue  # this run's own file, under whatever name it is listed
        os.remove(path)
        removed.append(path)
    return removed


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
        f"title: {yaml_q(title)}",
        f"description: {yaml_q(description)}",
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


def generate(
    design_dir: str, model: dict, created_at: str, dset: Optional["DesignSet"] = None
) -> dict:
    """Write every view and return the JSON summary.

    ``dset`` lets a caller that already loaded the design set (``main`` does,
    to run `validate_model`) pass it through instead of re-reading every file
    a second time; a fresh caller may omit it and let this load its own.
    """
    if dset is None:
        dset = DesignSet.load(design_dir)
    out_dir = os.path.join(design_dir, "diagrams")
    confidence = model.get("confidence", "high")
    written = []

    # `depicts` drives the `traces_to.diagrams` back-fill below, and it is
    # deliberately asymmetric: every external component is recorded against
    # BOTH DIA-001 and DIA-002 (it is drawn as a `System_Ext` in each), but
    # an internal component is recorded only against its own component
    # view, never against DIA-001/DIA-002 too, even though it also appears
    # there (inside the `System`/`Container` box, not as its own node — it
    # has no alias of its own to point back at in those two views). The
    # asymmetry tracks what each view actually names as a distinct element,
    # not merely what it draws.
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

    path = write_diagram(
        out_dir,
        dia_id="DIA-002",
        title="Container View",
        level="container",
        container=None,
        description=(
            f"The deployable units of {model['system_name']} and the edges "
            f"that cross between them."
        ),
        traces_from=dset.traces_for(
            [c for c in dset.components if dset.boundary(c) == "internal"]
        ),
        confidence=confidence,
        created_at=created_at,
        block=render_container(model, dset),
    )
    written.append({"id": "DIA-002", "path": path, "level": "container",
                    "depicts": externals})

    for index, container in enumerate(
        sorted(model.get("containers") or [], key=lambda c: c["key"])
    ):
        dia_id = f"DIA-{index + 3:03d}"
        members = sorted(container.get("components") or [])
        path = write_diagram(
            out_dir,
            dia_id=dia_id,
            title=f"Component View — {container['name']}",
            level="component",
            container=container["key"],
            description=f"Internal structure of the {container['name']} container.",
            traces_from=dset.traces_for(members),
            confidence=confidence,
            created_at=created_at,
            block=render_component(model, dset, container),
        )
        written.append({"id": dia_id, "path": path, "level": "component",
                        "depicts": members})

    removed = _remove_stale_diagrams(out_dir, {entry["path"] for entry in written})

    back_fill: Dict[str, List[str]] = {}
    for entry in written:
        for cmp_id in entry["depicts"]:
            back_fill.setdefault(cmp_id, []).append(entry["id"])
    return {"diagrams": written, "removed": removed, "traces_to_diagrams":
            {k: sorted(v) for k, v in sorted(back_fill.items())}}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate C4 views for a design set.")
    parser.add_argument("design_dir", nargs="?", default=".sdlc/design")
    parser.add_argument("--model", required=True, help="draft_diagram_model JSON")
    parser.add_argument(
        "--created-at", required=True,
        help="YYYY-MM-DD stamped on every diagram (diagrams must carry the "
             "same date as the rest of the set)",
    )
    args = parser.parse_args(argv)
    if not args.created_at:
        parser.error("argument --created-at: must not be empty")

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

    print(json.dumps(generate(args.design_dir, model, args.created_at, dset), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

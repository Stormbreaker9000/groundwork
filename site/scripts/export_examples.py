#!/usr/bin/env python3
"""Publish the worked example artifact sets to the documentation site.

Reads ``docs/requirements/examples/`` and writes one Markdown page per
artifact type per set into ``site/content/guide/examples/``.

Consolidated by type rather than one page per artifact: the two sets hold 108
atomic artifacts between them, and 108 sidebar entries is a listing rather
than navigation. Each artifact keeps a stable anchor, so a link to a single
requirement still resolves.

Output is ``.md``, not ``.mdx``. Nextra compiles ``.md`` in markdown mode,
where ``<`` and ``{`` are literal text — so an artifact body cannot break the
site build by containing them. No example body currently does, and nothing
guarantees that stays true: these sets are regenerated deliberately.

Stdlib only, like every other script in this repository. The outputs are
committed and the site build does not run this script; CI re-runs it and
fails on any diff.

Usage
-----
    python3 site/scripts/export_examples.py
    python3 site/scripts/export_examples.py --check
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
EXAMPLES_DIR = os.path.join(REPO_ROOT, "docs", "requirements", "examples")
OUT_DIR = os.path.join(
    REPO_ROOT, "site", "content", "guide", "examples"
)

# Frontmatter is parsed with the validators' own parser, so this script sees
# exactly what the gates see. artifact_core lives in lib/ and is imported
# directly here rather than through a validator, so lib/ goes on the path
# explicitly — the validators bootstrap it for themselves, which does not
# help a module that never imports one.
for _dir in (
    os.path.join(REPO_ROOT, "lib"),
    os.path.join(REPO_ROOT, "skills", "design", "scripts"),
    os.path.join(REPO_ROOT, "skills", "requirements", "scripts"),
):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import artifact_core  # noqa: E402

# (stage, directory, page title). Order is page order in the sidebar.
GROUPS: List[Tuple[str, str, str]] = [
    ("requirements", "functional", "Functional requirements"),
    ("requirements", "non-functional", "Non-functional requirements"),
    ("requirements", "constraints", "Constraints"),
    ("requirements", "business-rules", "Business rules"),
    ("design", "components", "Components"),
    ("design", "interfaces", "Interfaces"),
    ("design", "adr", "Architecture decision records"),
    ("design", "diagrams", "C4 diagrams"),
]

# Project-level artifacts: prose files with no artifact ID, published together
# on one page per stage. Order is reading order, not alphabetical.
PROJECT_FILES: Dict[str, List[str]] = {
    "requirements": ["glossary.md", "assumptions.md", "definition-of-done.md"],
    "design": ["drivers.md", "assumptions.md"],
}

# Excluded on purpose. The critique report and dev log are pipeline internals;
# CONSOLIDATED.md is the hand-assembled artifact STO-264 exists to replace,
# and republishing it here would give a known-stale document a second and more
# authoritative home; the READMEs address a reader of the repository.
EXCLUDED = {
    "CONSOLIDATED.md",
    "README.md",
    "REGENERATION.md",
    "dev-log-followup.md",
}

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n\s*", re.DOTALL)


@dataclass
class Artifact:
    artifact_id: str
    title: str
    source: str
    meta: Dict[str, Any]
    body: str


def split_frontmatter(text: str) -> str:
    """Return the body after a leading frontmatter block, or the text as-is."""
    return _FRONTMATTER_RE.sub("", text, count=1)


def discover_sets() -> List[str]:
    """Every example set: a directory holding a ``requirements/`` subtree."""
    return sorted(
        name
        for name in os.listdir(EXAMPLES_DIR)
        if os.path.isdir(os.path.join(EXAMPLES_DIR, name, "requirements"))
    )


def _sort_key(artifact_id: str) -> Tuple[str, int]:
    """Sort IDs by prefix then numeric suffix, so FR-2 precedes FR-10."""
    prefix, _, number = artifact_id.rpartition("-")
    try:
        return (prefix, int(number))
    except ValueError:
        return (artifact_id, 0)


def load_group(set_name: str, stage: str, directory: str) -> List[Artifact]:
    """Load one artifact type's files, ID-sorted.

    A directory that does not exist yields an empty list. That is a legal
    shape, not an error: gdpr carries no design stage, and an absent ``adr/``
    or ``diagrams/`` means nothing qualified rather than something failed.
    """
    root = os.path.join(EXAMPLES_DIR, set_name, stage, directory)
    if not os.path.isdir(root):
        return []

    artifacts: List[Artifact] = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".md") or name in EXCLUDED:
            continue
        path = os.path.join(root, name)
        meta, error = artifact_core.parse_frontmatter(path)
        if error is not None or not isinstance(meta, dict):
            raise ValueError(f"{path}: {error or 'frontmatter is not a mapping'}")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        artifacts.append(
            Artifact(
                artifact_id=str(meta["id"]),
                title=str(meta.get("title", "")),
                source=os.path.relpath(path, REPO_ROOT),
                meta=meta,
                body=split_frontmatter(text),
            )
        )

    artifacts.sort(key=lambda a: _sort_key(a.artifact_id))
    return artifacts


_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^(#{1,5})(\s+)(.*)$")


def demote_headings(body: str) -> str:
    """Shift every heading down one level, outside fenced code blocks.

    An artifact body opens with ``# FR-001 — Title``; on a consolidated page
    that has to become an H2 under the page's own H1.

    A state machine rather than a regex over the whole document. Artifact
    bodies carry Gherkin and Mermaid fences whose lines can begin with ``#``,
    and a fence is closed only by a fence of at least the same length using
    the same character — the rule CommonMark actually specifies. An
    unterminated fence runs to the end of the file rather than silently
    re-enabling demotion, which is the residual STO-263 C1 records against
    the exporter's regex approach.
    """
    out: List[str] = []
    fence: Optional[Tuple[str, int]] = None

    for line in body.split("\n"):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            char = fence_match.group(2)[0]
            length = len(fence_match.group(2))
            info = fence_match.group(3).strip()
            if fence is None:
                # An opening fence may carry an info string; a closing one
                # may not.
                fence = (char, length)
            elif char == fence[0] and length >= fence[1] and not info:
                fence = None
            out.append(line)
            continue

        if fence is None:
            heading = _HEADING_RE.match(line)
            if heading:
                out.append(
                    "#" + heading.group(1) + heading.group(2) + heading.group(3)
                )
                continue

        out.append(line)

    return "\n".join(out)


def page_url(set_name: str, stage: str, directory: str) -> str:
    """Site-relative page URL, trailing slash, no basePath.

    The form ``site/content/index.mdx`` already uses and pass 1 confirmed
    resolves on the deployed project page.
    """
    return f"/guide/examples/{set_name}/{stage}/{directory}/"


def build_index(set_name: str) -> Dict[str, str]:
    """Map every artifact ID in a set to its anchored URL."""
    index: Dict[str, str] = {}
    for stage, directory, _title in GROUPS:
        url = page_url(set_name, stage, directory)
        for artifact in load_group(set_name, stage, directory):
            index[artifact.artifact_id] = f"{url}#{artifact.artifact_id.lower()}"
    return index


def _link_ids(ids: List[Any], index: Dict[str, str]) -> str:
    """Render an ID list as links, leaving unresolvable IDs as plain text.

    A generated page must not publish a dead cross-reference — least of all
    on pages about traceability.
    """
    if not ids:
        return "—"
    parts: List[str] = []
    for raw in ids:
        value = str(raw)
        target = index.get(value)
        parts.append(f"[{value}]({target})" if target else value)
    return ", ".join(parts)


# Frontmatter keys worth surfacing per artifact, in display order. Anything
# not listed stays in the source file; this is a reading view, not a dump.
META_ROWS = [
    ("type", "Type"),
    ("tier", "Tier"),
    ("priority", "Priority"),
    ("status", "Status"),
    ("confidence", "Confidence"),
    ("ears_pattern", "EARS pattern"),
    ("verification_method", "Verification"),
    ("boundary", "Boundary"),
    ("responsibility", "Responsibility"),
    ("provider", "Provider"),
    ("interaction", "Interaction"),
    ("level", "C4 level"),
]

LINK_ROWS = [
    ("traces_from", "Traces from"),
    ("depends_on", "Depends on"),
]


def _meta_table(artifact: Artifact, index: Dict[str, str]) -> str:
    rows: List[str] = []
    for key, label in META_ROWS:
        value = artifact.meta.get(key)
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        rows.append(f"| {label} | {value} |")
    for key, label in LINK_ROWS:
        value = artifact.meta.get(key)
        if not value:
            continue
        rows.append(f"| {label} | {_link_ids(list(value), index)} |")

    if not rows:
        return ""
    header = "| Field | Value |\n| --- | --- |"
    return header + "\n" + "\n".join(rows) + "\n"


def render_group(
    set_name: str,
    stage: str,
    directory: str,
    title: str,
    artifacts: List[Artifact],
    index: Dict[str, str],
) -> str:
    """Render one artifact type as a single consolidated page."""
    lines = [
        "<!--",
        "  GENERATED FILE — do not edit.",
        "  Source: docs/requirements/examples/"
        f"{set_name}/{stage}/{directory}/",
        "  Regenerate: python3 site/scripts/export_examples.py",
        "-->",
        "",
        f"# {title}",
        "",
        f"The {len(artifacts)} {title.lower()} from the "
        f"`{set_name}` worked example, exactly as the pipeline wrote them.",
        "",
    ]

    for artifact in artifacts:
        anchor = artifact.artifact_id.lower()
        heading = f"{artifact.artifact_id} — {artifact.title}".rstrip(" —")
        lines.append(f"## {heading} [#{anchor}]")
        lines.append("")
        table = _meta_table(artifact, index)
        if table:
            lines.append(table)
        body = demote_headings(artifact.body).strip()
        # The artifact's own H1 became an H2 identical to the heading above.
        body = re.sub(r"\A##\s+.*\n+", "", body)
        lines.append(body)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# Sidebar labels for the sets. A set with no entry here uses its directory
# name, so adding a set does not require touching this map.
SET_TITLES = {
    "tamagotchi": "Desktop tamagotchi",
    "gdpr": "GDPR compliance",
}

PROJECT_TITLES = {
    "glossary.md": "Glossary",
    "assumptions.md": "Assumptions",
    "definition-of-done.md": "Definition of done",
    "drivers.md": "Architecture drivers",
}


def render_project_artifacts(set_name: str, stage: str) -> str:
    """Render one stage's project-level prose files as a single page.

    These carry no artifact ID and no frontmatter — they are the stage's
    shared context, not atomic artifacts, and the structural validators skip
    them for the same reason.
    """
    root = os.path.join(EXAMPLES_DIR, set_name, stage)
    sections: List[str] = []
    for name in PROJECT_FILES[stage]:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        body = demote_headings(split_frontmatter(text)).strip()
        body = re.sub(r"\A##\s+.*\n+", "", body)
        anchor = os.path.splitext(name)[0]
        sections.append(
            f"## {PROJECT_TITLES[name]} [#{anchor}]\n\n{body}\n"
        )

    if not sections:
        return ""

    header = [
        "<!--",
        "  GENERATED FILE — do not edit.",
        f"  Source: docs/requirements/examples/{set_name}/{stage}/",
        "  Regenerate: python3 site/scripts/export_examples.py",
        "-->",
        "",
        "# Project artifacts",
        "",
        "The stage-level files that sit alongside the atomic artifacts: the "
        "vocabulary they are written in, what was assumed, and what is still "
        "open.",
        "",
    ]
    return "\n".join(header) + "\n".join(sections).rstrip("\n") + "\n"


def _meta_js(entries: List[Tuple[str, str]]) -> str:
    lines = ["export default {"]
    lines += [f"  '{key}': '{label}'," for key, label in entries]
    lines.append("}")
    return "\n".join(lines).replace(",\n}", "\n}") + "\n"


def build_pages() -> Dict[str, str]:
    """Every file this exporter owns: relative path to content."""
    pages: Dict[str, str] = {}
    set_entries: List[Tuple[str, str]] = []

    for set_name in discover_sets():
        index = build_index(set_name)
        stages_present: List[str] = []

        for stage in ("requirements", "design"):
            group_entries: List[Tuple[str, str]] = []
            for group_stage, directory, title in GROUPS:
                if group_stage != stage:
                    continue
                artifacts = load_group(set_name, stage, directory)
                if not artifacts:
                    continue
                pages[f"{set_name}/{stage}/{directory}.md"] = render_group(
                    set_name, stage, directory, title, artifacts, index
                )
                group_entries.append((directory, title))

            project = render_project_artifacts(set_name, stage)
            if project:
                pages[f"{set_name}/{stage}/project-artifacts.md"] = project
                group_entries.append(("project-artifacts", "Project artifacts"))

            if group_entries:
                pages[f"{set_name}/{stage}/_meta.js"] = _meta_js(group_entries)
                stages_present.append(stage)

        if stages_present:
            pages[f"{set_name}/_meta.js"] = _meta_js(
                [
                    (s, "Requirements" if s == "requirements" else "Design")
                    for s in stages_present
                ]
            )
            set_entries.append((set_name, SET_TITLES.get(set_name, set_name)))

    pages["_meta.js"] = _meta_js(set_entries)
    return pages


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish the worked example sets to the docs site."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any committed page is stale, writing nothing",
    )
    args = parser.parse_args(argv)

    pages = build_pages()
    stale: List[str] = []

    for relative, content in sorted(pages.items()):
        path = os.path.join(OUT_DIR, relative)
        if args.check:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    if handle.read() != content:
                        stale.append(relative)
            except (OSError, UnicodeDecodeError):
                stale.append(relative)
        else:
            _write(path, content)

    if args.check:
        # A page on disk that the exporter no longer produces is drift too.
        for root, _dirs, names in os.walk(OUT_DIR):
            for name in names:
                relative = os.path.relpath(
                    os.path.join(root, name), OUT_DIR
                ).replace(os.sep, "/")
                if relative not in pages:
                    stale.append(f"{relative} (orphaned)")

    if args.check and stale:
        for relative in sorted(stale):
            print(f"stale: site/content/guide/examples/{relative}", file=sys.stderr)
        print("run: python3 site/scripts/export_examples.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

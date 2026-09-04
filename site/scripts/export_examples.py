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

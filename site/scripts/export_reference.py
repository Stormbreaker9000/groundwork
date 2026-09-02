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

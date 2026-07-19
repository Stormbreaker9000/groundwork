#!/usr/bin/env python3
"""Stage-agnostic core for Groundwork atomic-artifact validators.

Groundwork emits one atomic artifact per Markdown file with YAML frontmatter.
The requirements stage (M1) and the design stage (M2) share the *parsing and
reporting* machinery: frontmatter extraction, the stdlib-fallback YAML-ish
parser, JSON-Schema validation, project-level artifact gating, file discovery,
and the report format. Only the domain-specific cross-file checks differ.

This module is that shared surface, extracted from ``validate_requirements.py``
(STO-197). It is deliberately free of any requirement- or design-specific
knowledge: discovery is parameterized by skip sets, the report noun is passed
in, and the per-artifact class exposes a generic ``artifact_id``. Domain logic
(cross-file checks, fallback required-field lists, artifact gates) stays in the
per-stage validators.

The extraction is behavior-preserving: the M1 suite is its regression net.

Dependencies
------------
Full validation requires two third-party packages::

    pip install pyyaml jsonschema

If they are missing, callers degrade to :func:`_stdlib_parse_frontmatter` and a
best-effort fallback validation the per-stage module supplies. ``HAVE_YAML`` and
``HAVE_JSONSCHEMA`` report which path is active.
"""
from __future__ import annotations

import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional dependencies. We degrade gracefully if they are not installed.
# ---------------------------------------------------------------------------
try:  # PyYAML
    import yaml  # type: ignore

    HAVE_YAML = True
except ImportError:  # pragma: no cover - exercised only without the dep
    yaml = None  # type: ignore
    HAVE_YAML = False

try:  # jsonschema
    import jsonschema  # type: ignore
    from jsonschema import Draft202012Validator  # type: ignore

    HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - exercised only without the dep
    jsonschema = None  # type: ignore
    Draft202012Validator = None  # type: ignore
    HAVE_JSONSCHEMA = False


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


class ArtifactFile:
    """A parsed artifact file and the errors found while validating it.

    Stage-agnostic: the id accessor reads frontmatter ``id`` without assuming a
    prefix. Per-stage subclasses may add domain-flavoured aliases.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self.frontmatter: Optional[Dict[str, Any]] = None
        self.errors: List[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def artifact_id(self) -> Optional[str]:
        if isinstance(self.frontmatter, dict):
            value = self.frontmatter.get("id")
            if isinstance(value, str):
                return value
        return None


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
def extract_frontmatter_block(text: str) -> Optional[str]:
    """Return the raw YAML frontmatter block, or None if absent."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None
    return match.group(1)


def _strip_inline_comment(value: str) -> str:
    # Remove a trailing ` # comment` (best effort, not quote-aware).
    hash_idx = value.find(" #")
    if hash_idx != -1:
        value = value[:hash_idx]
    return value.strip()


def _coerce_scalar(value: str) -> Any:
    value = _strip_inline_comment(value)
    if value == "" or value == "~" or value.lower() == "null":
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(part) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: Dict[str, Any] = {}
        for pair in inner.split(","):
            if ":" in pair:
                pk, _, pv = pair.partition(":")
                result[pk.strip()] = _coerce_scalar(pv.strip())
        return result
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _stdlib_parse_frontmatter(block: str) -> Dict[str, Any]:
    """A tiny, intentionally limited YAML-ish parser for the fallback path.

    Indentation-aware and recursive: supports flat scalars, inline ``[a, b]``
    and ``{k: v}`` collections, block lists (of scalars OR of mappings, e.g.
    ``operations: [{name, summary}]``), and nested block mappings whose values
    may themselves be block lists (e.g. ``traces_to.tests``). This is NOT a
    general YAML parser; install PyYAML for full fidelity.

    A block-mapping list item — ``- name: authorize`` followed by an indented
    ``summary: ...`` — is parsed into a dict, not flattened to a string. Getting
    this wrong silently corrupts the document: the continuation keys leak up
    into the enclosing mapping as phantom siblings.

    Known non-support (install PyYAML if you need it): block scalars (``>``/
    ``|``) are not folded — the value is left as the literal ``>`` marker. This
    is harmless for the fallback's job (required-field *presence*) but is why
    the fallback is never as faithful as the schema path.
    """
    # Keep only meaningful lines paired with their indentation.
    rows: List[Tuple[int, str]] = []
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        rows.append((indent, raw.strip()))

    def block_end(seg: List[Tuple[int, str]], i: int) -> int:
        """Index one past the rows more-indented than seg[i] (its children)."""
        base = seg[i][0]
        j = i + 1
        while j < len(seg) and seg[j][0] > base:
            j += 1
        return j

    def parse(seg: List[Tuple[int, str]]) -> Any:
        """Parse a segment of same-or-deeper rows into a list, mapping, or None."""
        if not seg:
            return None
        return parse_list(seg) if seg[0][1].startswith("- ") else parse_mapping(seg)

    def parse_mapping(seg: List[Tuple[int, str]]) -> Dict[str, Any]:
        mapping: Dict[str, Any] = {}
        i = 0
        while i < len(seg):
            _indent, text = seg[i]
            if ":" not in text:
                i += 1
                continue
            key, _, value = text.partition(":")
            key, value = key.strip(), value.strip()
            end = block_end(seg, i)
            if value == "":
                # Empty scalar, or a nested block in the deeper child rows.
                mapping[key] = parse(seg[i + 1:end]) if end > i + 1 else None
            else:
                mapping[key] = _coerce_scalar(value)
            i = end
        return mapping

    def parse_list(seg: List[Tuple[int, str]]) -> List[Any]:
        items: List[Any] = []
        i = 0
        while i < len(seg):
            indent, text = seg[i]
            if not text.startswith("- "):
                i += 1
                continue
            rest = text[2:]
            end = block_end(seg, i)
            children = seg[i + 1:end]
            if ":" in rest:
                # Block-mapping item: the dash line's `rest` is its first key,
                # sitting one level in from the dash; children are its siblings.
                items.append(parse_mapping([(indent + 2, rest)] + children))
            elif children:
                items.append(parse([(indent + 2, rest)] + children) if rest else parse(children))
            else:
                items.append(_coerce_scalar(rest))
            i = end
        return items

    value = parse(rows)
    return value if isinstance(value, dict) else {}


def parse_frontmatter(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse a file's frontmatter. Returns (data, error_message)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return None, f"could not read file: {exc}"

    block = extract_frontmatter_block(text)
    if block is None:
        return None, "missing YAML frontmatter (expected a leading '---' block)"

    if HAVE_YAML:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:  # type: ignore[union-attr]
            return None, f"invalid YAML frontmatter: {exc}"
    else:
        data = _stdlib_parse_frontmatter(block)

    if not isinstance(data, dict):
        return None, "frontmatter did not parse to a mapping/object"
    return _normalize_dates(data), None


def _normalize_dates(value: Any) -> Any:
    """Recursively convert YAML date/datetime objects to ISO-8601 strings.

    PyYAML deserializes unquoted ``YYYY-MM-DD`` scalars to ``datetime.date``.
    The schema models ``created_at`` as a string, so we coerce dates back to
    their canonical string form, accepting both quoted and unquoted authoring.
    """
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_dates(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
def load_schema(schema_path: str) -> Dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def make_validator(schema_path: str) -> Any:
    """Build a Draft 2020-12 validator, or None if jsonschema is unavailable.

    A FormatChecker enables ``format: date`` checks where supported; per-stage
    schemas also pin a ``created_at`` regex so the check holds without it.
    """
    if not HAVE_JSONSCHEMA:
        return None
    schema = load_schema(schema_path)
    Draft202012Validator.check_schema(schema)  # type: ignore[union-attr]
    return Draft202012Validator(  # type: ignore[union-attr]
        schema, format_checker=jsonschema.FormatChecker()  # type: ignore[union-attr]
    )


def validate_against_schema(data: Dict[str, Any], validator: Any) -> List[str]:
    """Return a list of human-readable schema errors (empty if valid)."""
    errors: List[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {location}: {err.message}")
    return errors


# ---------------------------------------------------------------------------
# Project-level artifact gate (shared: STO-134 assumptions, STO-135 glossary)
# ---------------------------------------------------------------------------
def _check_project_artifact(
    root_dir: str, filename: str, required_headings: List[str], label: str, hint: str
) -> List[str]:
    """Gate a project-level artifact's presence and its required H2 headings.

    Presence and headings only — content is never gated. A section reading
    'None identified' is legal and passes.
    """
    path = os.path.join(root_dir, filename)
    if not os.path.isfile(path):
        return [f"missing required {label} '{filename}' ({hint})"]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"could not read {label} '{filename}': {exc}"]

    errors: List[str] = []
    for heading in required_headings:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(
                f"{label} '{filename}' missing required heading '{heading}'"
            )
    return errors


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def discover_files(
    root_dir: str,
    skip_filenames: "frozenset[str] | set[str]",
    skip_dirnames: "frozenset[str] | set[str]" = frozenset(),
) -> List[str]:
    """Return every ``*.md`` under ``root_dir`` that is an atomic artifact.

    ``skip_filenames`` are project-level companions (assumptions, glossary,
    index) that live alongside artifacts but are not themselves atomic.
    ``skip_dirnames`` are whole subtrees a stage owns in another format (M2's
    ``adr/`` and ``diagrams/``); they are pruned in-place from the walk. A stray
    file that is neither skipped nor a valid artifact is surfaced by the caller,
    not silently ignored.
    """
    found: List[str] = []
    for root, dirs, names in os.walk(root_dir):
        if skip_dirnames:
            dirs[:] = [d for d in dirs if d not in skip_dirnames]
        for name in names:
            if not name.endswith(".md"):
                continue
            if name in skip_filenames:
                continue
            found.append(os.path.join(root, name))
    return sorted(found)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def print_report(
    files: List[ArtifactFile],
    global_errors: List[str],
    root_dir: str,
    quiet: bool,
    noun: str = "artifact",
) -> None:
    """Print the shared per-file + summary report. ``noun`` labels the stage
    ('requirement', 'design artifact') in the header line only."""
    total = len(files)
    failed = [f for f in files if not f.ok]
    passed = total - len(failed)

    if not (HAVE_YAML and HAVE_JSONSCHEMA):
        missing = []
        if not HAVE_YAML:
            missing.append("pyyaml")
        if not HAVE_JSONSCHEMA:
            missing.append("jsonschema")
        print(
            f"WARNING: running in reduced (stdlib fallback) mode; "
            f"missing {', '.join(missing)}. "
            f"For full schema validation: pip install {' '.join(missing)}"
        )
        print()

    print(f"Validating {noun}s in: {root_dir}")
    print(f"Discovered {total} {noun} file(s).")
    print("-" * 60)

    for f in files:
        if f.ok:
            if not quiet:
                rid = f.artifact_id or "(no id)"
                print(f"  PASS  {rid:<14} {os.path.relpath(f.path, root_dir)}")
        else:
            rid = f.artifact_id or "(no id)"
            print(f"  FAIL  {rid:<14} {os.path.relpath(f.path, root_dir)}")
            for e in f.errors:
                print(f"          - {e}")

    if global_errors:
        print("-" * 60)
        print("Set-level errors:")
        for e in global_errors:
            print(f"  - {e}")

    print("-" * 60)
    error_count = sum(len(f.errors) for f in files) + len(global_errors)
    print(
        f"Summary: {passed}/{total} file(s) passed, "
        f"{len(failed)} failed, {error_count} error(s) total."
    )

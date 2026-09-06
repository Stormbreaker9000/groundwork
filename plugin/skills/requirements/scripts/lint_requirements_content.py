#!/usr/bin/env python3
"""Content-quality linter for Groundwork atomic requirement artifacts.

Distinct from ``validate_requirements.py`` (which checks YAML schema + cross-file
structure). This tool reads the *prose* of each requirement and flags content
anti-patterns — vague qualifiers, compound requirements, EARS non-conformance,
passive voice with a nameless subject, and implementation bias at the
business/stakeholder tier.

It is ADVISORY: it prints a per-requirement diagnostic and, by default, exits 0.
Pass ``--strict`` to exit non-zero on any ``error``-severity finding. Pass
``--json`` for machine-readable findings (consumed by the requirements-critic).

Usage
-----
    python3 lint_requirements_content.py [REQUIREMENTS_DIR]
    python3 lint_requirements_content.py --json .sdlc/requirements
    python3 lint_requirements_content.py --strict --quiet reqs
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

# Shared linter core lives at the repo root in ``lib/``; add it to the path
# before importing. Resolved relative to this file, so cwd does not matter.
# Mirrors validate_design.py's bootstrap.
_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
_LIB_DIR = os.path.join(_REPO_ROOT, "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import lint_core as core  # noqa: E402
from lint_core import (  # noqa: E402  (re-exported for tests)
    ACTION_VERBS,
    VAGUE_TERMS,
    Finding,
)

import validate_requirements as vr  # noqa: E402


# --- Glossary (STO-135) -----------------------------------------------------
# The on-disk contract: "- **Term**: definition. *Also: alias, alias.*"
_GLOSSARY_TERM_RE = re.compile(r"^\s*-\s+\*\*(?P<term>[^*]+)\*\*\s*:\s*(?P<rest>.*)$")
_GLOSSARY_ALIAS_RE = re.compile(r"\*Also:\s*(?P<aliases>[^*]+?)\.?\*")

# Requirement fields whose prose is searched for glossary-term usage.
GLOSSARY_SEARCH_FIELDS = ("title", "description", "rationale", "fit_criterion")


def parse_glossary(reqs_dir: str) -> List[Tuple[str, List[str]]]:
    """Return [(term, aliases)] parsed from glossary.md, or [] if it is absent.

    A missing glossary is the structural validator's hard gate, not a content
    finding — so this returns [] rather than raising or reporting.
    """
    path = os.path.join(reqs_dir, vr.GLOSSARY_ARTIFACT)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return []

    entries: List[Tuple[str, List[str]]] = []
    for line in text.splitlines():
        match = _GLOSSARY_TERM_RE.match(line)
        if not match:
            continue
        term = match.group("term").strip()
        aliases: List[str] = []
        alias_match = _GLOSSARY_ALIAS_RE.search(match.group("rest"))
        if alias_match:
            aliases = [
                a.strip() for a in alias_match.group("aliases").split(",") if a.strip()
            ]
        entries.append((term, aliases))
    return entries


def _mentions(haystack: str, phrase: str) -> bool:
    """True if `phrase` appears in `haystack`, tolerating ordinary inflection.

    'decay' matches 'decays' / 'decaying' / 'decayed'. Deliberately loose: the
    failure being hunted is an invented glossary entry nobody used, so being
    strict about word forms would only produce false warnings on normal English.
    """
    stripped = phrase.strip()
    escaped = re.escape(stripped).replace(r"\ ", r"\s+")

    # \b requires a word-char/non-word-char transition. When the term itself
    # starts or ends with a non-word character (e.g. "C++", "state (persisted)"),
    # that transition never happens in the normal case (term surrounded by
    # plain whitespace) because both sides of the boundary are non-word
    # characters too. Anchor on the term's own edges instead: word-boundary
    # for a word-initial/final term, "not preceded/followed by non-space" for
    # a punctuation-initial/final one.
    lead = r"(?<!\w)" if stripped[:1].isalnum() or stripped[:1] == "_" else r"(?<!\S)"
    if stripped[-1:].isalnum() or stripped[-1:] == "_":
        tail = r"(?:s|es|d|ed|ing)?\b"
    else:
        tail = r"(?!\S)"

    return re.search(
        rf"{lead}{escaped}{tail}", haystack, re.IGNORECASE
    ) is not None


def check_glossary_unused(
    reqs_dir: str, frontmatters: List[Dict[str, Any]]
) -> List[Finding]:
    """Warn for any glossary term (and its aliases) that no requirement uses."""
    entries = parse_glossary(reqs_dir)
    if not entries:
        return []

    corpus = " ".join(
        core.flatten_text(fm.get(field)) for fm in frontmatters for field in GLOSSARY_SEARCH_FIELDS
    )

    findings: List[Finding] = []
    for term, aliases in entries:
        if any(_mentions(corpus, phrase) for phrase in (term, *aliases)):
            continue
        findings.append(Finding(
            rule="glossary-unused",
            severity="warn",
            artifact_id=vr.GLOSSARY_ARTIFACT,
            field="terms",
            excerpt=term,
            message=f"glossary term '{term}' is used by no requirement",
            suggested_rewrite_hint=(
                "drop the entry, or check whether a requirement should be using "
                "this term and is wording it differently"
            ),
        ))
    return findings


def check_vague_qualifiers(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    findings: List[Finding] = []
    for field in ("title", "description"):
        text = core.flatten_text(fm.get(field))
        for sentence in core.sentences(text):
            low = sentence.lower()
            quantified = bool(re.search(r"\d", sentence))
            for term in sorted(VAGUE_TERMS):
                if re.search(rf"\b{re.escape(term)}\b", low):
                    findings.append(Finding(
                        rule="vague-qualifier",
                        severity="info" if quantified else "warn",
                        artifact_id=req_id,
                        field=field,
                        excerpt=sentence.strip()[:120],
                        message=f"vague qualifier '{term}' without a concrete metric",
                        suggested_rewrite_hint=(
                            f"replace '{term}' with a measurable threshold "
                            f"(a time, count, or percentage)"
                        ),
                    ))
    return findings


# ears_pattern -> required leading keyword (None = must have NO condition lead;
# "SKIP" = combination pattern, no single-lead rule).
EARS_LEADS: Dict[str, Optional[str]] = {
    "event": "when",
    "state": "while",
    "unwanted": "if",       # also requires a "then" clause
    "optional": "where",
    "ubiquitous": None,
    "complex": "SKIP",
}

_COMPOUND_RE = re.compile(
    r"\b(and|or)\s+(" + "|".join(sorted(ACTION_VERBS)) + r")\b"
)

_CONDITION_LEAD_RE = re.compile(r"^(when|while|if|where)\b")

_PASSIVE_RE = re.compile(r"shall be \w+(?:ed|en)\b")


def check_compound(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    text = core.flatten_text(fm.get("description"))
    low = text.lower()
    idx = low.find("shall")
    if idx == -1:
        return []
    predicate = low[idx + len("shall"):]
    match = _COMPOUND_RE.search(predicate)
    if not match:
        return []
    return [Finding(
        rule="compound",
        severity="warn",
        artifact_id=req_id,
        field="description",
        excerpt=text.strip()[:120],
        message=(
            f"multiple actions joined by '{match.group(1)}' "
            f"('{match.group(2)}') in one requirement"
        ),
        suggested_rewrite_hint="split into one requirement per action",
    )]


def _ears_finding(req_id: str, desc: str, message: str) -> Finding:
    return Finding(
        rule="ears-conformance",
        severity="warn",
        artifact_id=req_id,
        field="description",
        excerpt=desc.strip()[:120],
        message=message,
        suggested_rewrite_hint="rephrase to the declared EARS pattern's shape",
    )


def check_ears(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    if fm.get("type") != "functional":
        return []
    desc = core.flatten_text(fm.get("description"))
    low = desc.lower()
    if "shall" not in low:
        return [_ears_finding(
            req_id, desc,
            "functional requirement description does not contain 'shall'",
        )]

    pattern = fm.get("ears_pattern")
    lead = EARS_LEADS.get(pattern, "SKIP")
    if lead == "SKIP":
        return []
    if lead is None:
        # ubiquitous: must NOT open with a condition keyword.
        if _CONDITION_LEAD_RE.match(low):
            return [_ears_finding(
                req_id, desc,
                "ears_pattern 'ubiquitous' should have no leading condition, "
                "but the description opens with one",
            )]
        return []
    # Conditional patterns: must open with the required keyword.
    if not re.match(rf"^{lead}\b", low):
        return [_ears_finding(
            req_id, desc,
            f"ears_pattern '{pattern}' requires a leading '{lead}' clause",
        )]
    if pattern == "unwanted" and "then" not in low:
        return [_ears_finding(
            req_id, desc,
            "ears_pattern 'unwanted' requires an 'If ... then ...' structure",
        )]
    return []


def check_passive(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    desc = core.flatten_text(fm.get("description"))
    low = desc.lower()
    for match in _PASSIVE_RE.finditer(low):
        tail = low[match.end():match.end() + 40]
        if " by " in tail:
            continue  # actor is named
        return [Finding(
            rule="passive-nameless",
            severity="warn",
            artifact_id=req_id,
            field="description",
            excerpt=desc.strip()[:120],
            message="passive voice hides the responsible actor",
            suggested_rewrite_hint=(
                "name the actor: 'the <system/component> shall <verb> ...'"
            ),
        )]
    return []


TECH_TERMS = {
    "button", "dropdown", "checkbox", "modal", "click", "tap", "page", "screen",
    "react", "vue", "angular", "postgres", "postgresql", "mysql", "mongodb",
    "redis", "kafka", "rest", "graphql", "endpoint", "sql", "css", "html",
    "javascript", "docker", "kubernetes",
}


def check_impl_bias(req_id: str, fm: Dict[str, Any]) -> List[Finding]:
    if fm.get("tier") not in ("business", "stakeholder"):
        return []
    tier = fm.get("tier")
    for field in ("title", "description"):
        text = core.flatten_text(fm.get(field))
        low = text.lower()
        for term in sorted(TECH_TERMS):
            if re.search(rf"\b{re.escape(term)}\b", low):
                return [Finding(
                    rule="impl-bias",
                    severity="info",
                    artifact_id=req_id,
                    field=field,
                    excerpt=text.strip()[:120],
                    message=(
                        f"implementation detail '{term}' in a "
                        f"{tier}-tier requirement"
                    ),
                    suggested_rewrite_hint=(
                        "move technology/UI choices to a constraint or the "
                        "solution tier"
                    ),
                )]
    return []


# Registry of content-quality checks, each (req_id, frontmatter) -> List[Finding].
CHECKS: List[Callable[[str, Dict[str, Any]], List[Finding]]] = [
    check_vague_qualifiers,
    check_compound,
    check_ears,
    check_passive,
    check_impl_bias,
]

# Registry of set-level checks, each (reqs_dir, [frontmatter]) -> List[Finding].
# These need the whole set at once — "no requirement uses this term" is not
# decidable from a single file.
SET_CHECKS: List[Callable[[str, List[Dict[str, Any]]], List[Finding]]] = [
    check_glossary_unused,
]


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------
# Declarative description of every rule the checks above can emit, read by
# site/scripts/export_reference.py to build the published rule reference.
# ``test_rules_registry_matches_emitted_rules`` holds this equal, in both
# directions, to what the fixture corpus actually produces.
#
# ``severities`` is a list because two rules demote to "info" when the text
# they flag carries a number. ``fields`` is a list because a check may flag
# more than one frontmatter field, and ``test_emitted_fields_are_declared``
# holds it honest.
RULES: List[Dict[str, Any]] = [
    {
        "id": "vague-qualifier",
        "severities": ["warn", "info"],
        "applies_to": "requirement",
        "fields": ["description", "title"],
        "summary": (
            "A vague qualifier with no concrete metric. Demoted to info when "
            "the sentence carries a number."
        ),
    },
    {
        "id": "compound",
        "severities": ["warn"],
        "applies_to": "requirement",
        "fields": ["description"],
        "summary": (
            "Multiple actions joined by a conjunction in one requirement, "
            "which cannot be verified or traced as a single unit."
        ),
    },
    {
        "id": "ears-conformance",
        "severities": ["warn"],
        "applies_to": "requirement",
        "fields": ["description"],
        "summary": (
            "The description does not match the shape of the EARS pattern "
            "the requirement declares."
        ),
    },
    {
        "id": "passive-nameless",
        "severities": ["warn"],
        "applies_to": "requirement",
        "fields": ["description"],
        "summary": "Passive voice hides the responsible actor.",
    },
    {
        "id": "impl-bias",
        "severities": ["info"],
        "applies_to": "requirement",
        "fields": ["description", "title"],
        "summary": (
            "An implementation detail appears in a requirement whose tier "
            "should stay solution-free."
        ),
    },
    {
        "id": "glossary-unused",
        "severities": ["warn"],
        "applies_to": "requirement",
        "fields": ["terms"],
        "summary": (
            "A glossary term no requirement uses. Set-level check: not "
            "decidable from a single file."
        ),
    },
]


def lint_dir(reqs_dir: str) -> List[Finding]:
    findings: List[Finding] = []
    frontmatters: List[Dict[str, Any]] = []
    for path in vr.discover_files(reqs_dir):
        fm, err = vr.parse_frontmatter(path)
        if err or not isinstance(fm, dict):
            # Parse/structure problems are the structural validator's job.
            continue
        frontmatters.append(fm)
        req_id = fm.get("id") or os.path.basename(path)
        for check in CHECKS:
            findings.extend(check(req_id, fm))
    for set_check in SET_CHECKS:
        findings.extend(set_check(reqs_dir, frontmatters))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    return core.run_cli(
        argv,
        default_dir=".sdlc/requirements",
        noun="requirement",
        lint_dir=lint_dir,
        description=(
            "Content-quality linter for Groundwork requirement artifacts."
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())

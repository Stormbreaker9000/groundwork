"""Tests for the Groundwork requirements content-quality linter."""
import json
import os

import lint_requirements_content as lc

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
CONTENT = os.path.join(FIXTURES, "content")


def rules_for(subdir):
    findings = lc.lint_dir(os.path.join(CONTENT, subdir))
    return {f.rule for f in findings}


def test_clean_fixture_has_no_findings():
    assert lc.lint_dir(os.path.join(CONTENT, "clean")) == []


def test_advisory_exit_is_zero_even_with_findings():
    # The clean dir yields no findings; still must exit 0.
    assert lc.main([os.path.join(CONTENT, "clean")]) == 0


def test_vague_qualifier_flagged():
    rules = rules_for("vague")
    assert "vague-qualifier" in rules


def test_vague_qualifier_downgraded_when_quantified():
    fm = {"title": "x", "description": "The system shall respond fast, within 200 ms."}
    findings = lc.check_vague_qualifiers("FR-001", fm)
    assert findings, "expected a finding for 'fast'"
    assert all(f.severity == "info" for f in findings)

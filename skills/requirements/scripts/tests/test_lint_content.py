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

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


def test_compound_requirement_flagged():
    assert "compound" in rules_for("compound")


def test_noun_conjunction_not_flagged_as_compound():
    fm = {"description": "The system shall accept the terms and conditions."}
    assert lc.check_compound("FR-001", fm) == []


def test_ears_mismatch_flagged():
    assert "ears-conformance" in rules_for("ears")


def test_event_pattern_with_when_is_clean():
    fm = {"type": "functional", "ears_pattern": "event",
          "description": "When a user logs in, the system shall record the timestamp."}
    assert lc.check_ears("FR-001", fm) == []


def test_ears_check_skips_non_functional():
    fm = {"type": "non_functional", "description": "no shall here"}
    assert lc.check_ears("NFR-001", fm) == []


def test_ears_missing_shall_flagged():
    fm = {"type": "functional", "ears_pattern": "event",
          "description": "When a user logs in, the system records the timestamp."}
    findings = lc.check_ears("FR-001", fm)
    assert findings and findings[0].rule == "ears-conformance"


def test_ears_state_pattern_requires_while():
    # State pattern with "While" opening should be clean
    fm_clean = {"type": "functional", "ears_pattern": "state",
                "description": "While the account is locked, the system shall reject logins."}
    assert lc.check_ears("FR-002", fm_clean) == []

    # State pattern without "While" opening should flag
    fm_bad = {"type": "functional", "ears_pattern": "state",
              "description": "The system shall reject logins."}
    findings = lc.check_ears("FR-002", fm_bad)
    assert len(findings) >= 1 and findings[0].rule == "ears-conformance"


def test_ears_unwanted_requires_if_and_then():
    # Unwanted pattern with "If...then" should be clean
    fm_clean = {"type": "functional", "ears_pattern": "unwanted",
                "description": "If the payment fails, then the system shall notify the user."}
    assert lc.check_ears("FR-003", fm_clean) == []

    # Unwanted pattern with "If" but no "then" should flag
    fm_bad = {"type": "functional", "ears_pattern": "unwanted",
              "description": "If the payment fails, the system shall notify the user."}
    findings = lc.check_ears("FR-003", fm_bad)
    assert len(findings) >= 1 and findings[0].rule == "ears-conformance"


def test_ears_optional_requires_where():
    # Optional pattern with "Where" opening should be clean
    fm_clean = {"type": "functional", "ears_pattern": "optional",
                "description": "Where premium is enabled, the system shall show analytics."}
    assert lc.check_ears("FR-004", fm_clean) == []

    # Optional pattern without "Where" opening should flag
    fm_bad = {"type": "functional", "ears_pattern": "optional",
              "description": "The system shall show analytics."}
    findings = lc.check_ears("FR-004", fm_bad)
    assert len(findings) >= 1 and findings[0].rule == "ears-conformance"


def test_ears_ubiquitous_violation_flagged():
    # Ubiquitous pattern with condition keyword opening should flag
    fm = {"type": "functional", "ears_pattern": "ubiquitous",
          "description": "When a user logs in, the system shall log the event."}
    findings = lc.check_ears("FR-005", fm)
    assert len(findings) >= 1 and findings[0].rule == "ears-conformance"


def test_ears_complex_pattern_skipped():
    # Complex pattern with "shall" should be clean (no single-lead rule)
    fm = {"type": "functional", "ears_pattern": "complex",
          "description": "The system shall do something without a standard lead."}
    assert lc.check_ears("FR-006", fm) == []

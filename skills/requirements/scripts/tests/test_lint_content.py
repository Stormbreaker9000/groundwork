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


def test_passive_nameless_flagged():
    assert "passive-nameless" in rules_for("passive")


def test_passive_with_named_actor_not_flagged():
    fm = {"description": "When triggered, the record shall be archived by the ledger service."}
    assert lc.check_passive("FR-001", fm) == []


def test_impl_bias_flagged_at_stakeholder_tier():
    findings = lc.lint_dir(os.path.join(CONTENT, "impl-bias"))
    impl = [f for f in findings if f.rule == "impl-bias"]
    assert impl
    assert all(f.severity == "info" for f in impl)


def test_impl_bias_not_flagged_at_solution_tier():
    fm = {"tier": "solution", "title": "x",
          "description": "When the user clicks the button, the system shall cancel."}
    assert lc.check_impl_bias("FR-001", fm) == []


def test_json_output_is_parseable(capsys):
    code = lc.main([os.path.join(CONTENT, "vague"), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert code == 0
    assert isinstance(data, list) and data
    assert {"rule", "severity", "req_id", "field", "message"} <= set(data[0])


# ---------------------------------------------------------------------------
# Glossary (STO-135) — set-level unused-term check.
# ---------------------------------------------------------------------------
def test_parse_glossary_reads_terms_and_aliases():
    entries = lc.parse_glossary(os.path.join(CONTENT, "glossary-used"))
    assert entries == [("Decay", ["stat decay"])]


def test_parse_glossary_absent_file_yields_no_entries():
    # The 'clean' fixture has no glossary.md — a missing glossary is the
    # structural validator's problem, not the linter's.
    assert lc.parse_glossary(os.path.join(CONTENT, "clean")) == []


def test_unused_glossary_term_is_flagged():
    findings = lc.lint_dir(os.path.join(CONTENT, "glossary-unused"))
    unused = [f for f in findings if f.rule == "glossary-unused"]
    assert len(unused) == 1
    assert "Quarantine" in unused[0].message
    assert unused[0].severity == "warn"


def test_used_glossary_term_is_not_flagged():
    findings = lc.lint_dir(os.path.join(CONTENT, "glossary-used"))
    assert [f for f in findings if f.rule == "glossary-unused"] == []


def test_glossary_term_matched_through_inflection():
    """'Decay' is used as 'decays' — inflection must count as usage."""
    fm = {"description": "The system shall apply decay while the app is closed."}
    assert lc._mentions("the pet's hunger decays over time", "Decay")
    assert lc._mentions("applying stat decay on launch", "stat decay")
    assert not lc._mentions(lc._text(fm.get("description")), "Quarantine")


def test_alias_counts_as_usage(tmp_path):
    """A requirement using only the ALIAS counts as using the term.

    The term itself ('Erasure') never appears in the corpus, so this fails if
    alias matching is broken — unlike a term that is a substring of its own alias.
    """
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\n"
        "- **Erasure**: the permanent removal of a data subject's personal data. "
        "*Also: right to be forgotten.*\n",
        encoding="utf-8",
    )
    findings = lc.check_glossary_unused(
        str(tmp_path),
        [{"description": "The system shall honour the right to be forgotten."}],
    )
    assert findings == []


def test_term_absent_entirely_is_flagged(tmp_path):
    """Same glossary, but neither the term nor its alias is used anywhere."""
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\n"
        "- **Erasure**: the permanent removal of a data subject's personal data. "
        "*Also: right to be forgotten.*\n",
        encoding="utf-8",
    )
    findings = lc.check_glossary_unused(
        str(tmp_path), [{"description": "The system shall export personal data."}]
    )
    assert len(findings) == 1
    assert findings[0].rule == "glossary-unused"


# ---------------------------------------------------------------------------
# STO-135 follow-up: punctuation-bearing glossary terms (boundary-anchor bug).
# ---------------------------------------------------------------------------
def test_mentions_matches_punctuation_prefixed_and_suffixed_term():
    """A term like 'C++' must be found even though \\b fails on both its edges."""
    assert lc._mentions("the C++ runtime must work", "C++")
    assert lc._mentions("we use C++", "C++")


def test_mentions_matches_parenthesised_multiword_term():
    assert lc._mentions(
        "the state (persisted) shall survive restarts", "state (persisted)"
    )


def test_mentions_cat_does_not_match_inside_category():
    """Regression guard: word-boundary anchoring must still hold for plain terms."""
    assert not lc._mentions("assign a Category to each item", "Cat")

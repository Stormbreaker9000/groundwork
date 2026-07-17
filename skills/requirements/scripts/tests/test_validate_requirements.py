"""Tests for the Groundwork requirements validator.

Run from anywhere::

    pytest skills/requirements/scripts/tests

The suite asserts the validator PASSES (exit 0) on the conformant fixture set
and FAILS (non-zero exit) with a targeted message on each invalid fixture case.
"""
import os

import pytest

import validate_requirements as vr

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
VALID_DIR = os.path.join(FIXTURES, "valid")
INVALID_DIR = os.path.join(FIXTURES, "invalid")
SCHEMA = vr.default_schema_path()


def run(reqs_dir):
    """Invoke the CLI entry point against a fixture dir; return (code, output)."""
    return vr.main([reqs_dir, "--schema", SCHEMA])


# ---------------------------------------------------------------------------
# Valid fixtures
# ---------------------------------------------------------------------------
def test_valid_set_passes(capsys):
    code = run(VALID_DIR)
    out = capsys.readouterr().out
    assert code == 0, f"expected exit 0 on valid fixtures, got {code}\n{out}"
    # Spans FR / NFR / CON at minimum.
    assert "FR-001" in out
    assert "NFR-001" in out
    assert "CON-001" in out


def test_skip_files_are_ignored(capsys):
    """definition-of-done.md and index.yaml must not be validated."""
    run(VALID_DIR)
    out = capsys.readouterr().out
    assert "definition-of-done.md" not in out
    assert "index.yaml" not in out
    assert "assumptions.md" not in out


# ---------------------------------------------------------------------------
# Invalid fixtures — each case must fail with a non-zero exit code.
# ---------------------------------------------------------------------------
INVALID_CASES = {
    "missing_required_field": "rationale",
    "bad_enum": "priority",
    "duplicate_id": "duplicate id",
    "dangling_trace": "dangling",
    "fr_missing_ears": "ears_pattern",
    "missing_context_artifact": "context artifact",
    "context_artifact_missing_heading": "missing required heading",
    "missing_glossary": "glossary artifact",
    "glossary_missing_heading": "missing required heading",
}


@pytest.mark.parametrize("case,needle", sorted(INVALID_CASES.items()))
def test_invalid_case_fails(case, needle, capsys):
    case_dir = os.path.join(INVALID_DIR, case)
    code = run(case_dir)
    out = capsys.readouterr().out
    assert code != 0, f"expected non-zero exit for case '{case}', got {code}\n{out}"
    assert needle.lower() in out.lower(), (
        f"case '{case}' did not report expected error containing '{needle}'\n{out}"
    )


# ---------------------------------------------------------------------------
# Unit-level checks of the building blocks.
# ---------------------------------------------------------------------------
def test_prefix_to_type_mapping():
    assert vr.PREFIX_TO_TYPE == {
        "FR": "functional",
        "NFR": "non_functional",
        "CON": "constraint",
        "BR": "business_rule",
        "UC": "use_case",
    }


def test_extract_frontmatter_block():
    text = "---\nid: FR-001\ntype: functional\n---\n# body\n"
    block = vr.extract_frontmatter_block(text)
    assert block is not None
    assert "id: FR-001" in block


def test_extract_frontmatter_block_absent():
    assert vr.extract_frontmatter_block("# no frontmatter here\n") is None


def test_missing_directory_returns_usage_error(capsys):
    code = vr.main([os.path.join(FIXTURES, "does-not-exist"), "--schema", SCHEMA])
    assert code == 2


def test_id_prefix_type_mismatch_is_flagged():
    rf = vr.RequirementFile("mem://x")
    rf.frontmatter = {"id": "FR-001", "type": "non_functional", "ears_pattern": "event"}
    vr.cross_file_checks([rf])
    assert any("implies type" in e for e in rf.errors)


def test_context_artifact_present_passes(tmp_path):
    (tmp_path / "assumptions.md").write_text(
        "## Assumptions\n- none\n## Dependencies\n- none\n## Open Questions\n- none\n",
        encoding="utf-8",
    )
    assert vr.check_context_artifact(str(tmp_path)) == []


def test_context_artifact_missing_file_is_flagged(tmp_path):
    errors = vr.check_context_artifact(str(tmp_path))
    assert any("context artifact" in e for e in errors)


def test_context_artifact_non_utf8_is_reported_not_raised(tmp_path):
    (tmp_path / "assumptions.md").write_bytes(b"\xff\xfe## Assumptions\n")
    errors = vr.check_context_artifact(str(tmp_path))
    assert errors and any("could not read" in e for e in errors)


# ---------------------------------------------------------------------------
# Glossary artifact (STO-135) — presence + heading gate.
# ---------------------------------------------------------------------------
def test_glossary_artifact_present_passes(tmp_path):
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\n- **Decay**: the reduction of stat values over time.\n",
        encoding="utf-8",
    )
    assert vr.check_glossary_artifact(str(tmp_path)) == []


def test_glossary_artifact_empty_section_passes(tmp_path):
    """An honest 'None identified' glossary is legal — content is never gated."""
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms\nNone identified\n", encoding="utf-8"
    )
    assert vr.check_glossary_artifact(str(tmp_path)) == []


def test_glossary_artifact_missing_file_is_flagged(tmp_path):
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("glossary artifact" in e for e in errors)


def test_glossary_artifact_missing_heading_is_flagged(tmp_path):
    (tmp_path / "glossary.md").write_text("# Glossary\n\n- **Decay**: x.\n", encoding="utf-8")
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("missing required heading" in e for e in errors)


def test_glossary_artifact_non_utf8_is_reported_not_raised(tmp_path):
    (tmp_path / "glossary.md").write_bytes(b"\xff\xfe## Terms\n")
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert errors and any("could not read" in e for e in errors)


def test_glossary_is_not_validated_as_a_requirement(capsys):
    run(VALID_DIR)
    out = capsys.readouterr().out
    assert "glossary.md" not in out


# ---------------------------------------------------------------------------
# Heading anchoring — the required heading must match a whole line, not just
# appear as a substring. A naive `heading in text` check would be fooled by a
# deeper heading level (### Terms) or a longer heading that merely starts with
# the required text (## Terms of Service). These pin that behavior against a
# future refactor of `_check_project_artifact`.
# ---------------------------------------------------------------------------
def test_glossary_artifact_h3_terms_is_rejected(tmp_path):
    """An H3 '### Terms' contains the substring '## Terms' but must not satisfy
    the '## Terms' H2 heading requirement."""
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n### Terms\n- **Decay**: x.\n", encoding="utf-8"
    )
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("missing required heading" in e for e in errors)


def test_glossary_artifact_terms_of_service_heading_is_rejected(tmp_path):
    """A longer heading that starts with '## Terms' must not satisfy the
    '## Terms' heading requirement."""
    (tmp_path / "glossary.md").write_text(
        "# Glossary\n\n## Terms of Service\n- **Decay**: x.\n", encoding="utf-8"
    )
    errors = vr.check_glossary_artifact(str(tmp_path))
    assert any("missing required heading" in e for e in errors)


def test_context_artifact_h3_assumptions_is_rejected(tmp_path):
    """An H3 '### Assumptions' contains the substring '## Assumptions' but must
    not satisfy the '## Assumptions' H2 heading requirement. Pins the same
    anchoring behavior for check_context_artifact, which shares
    _check_project_artifact with check_glossary_artifact."""
    (tmp_path / "assumptions.md").write_text(
        "### Assumptions\n- none\n## Dependencies\n- none\n## Open Questions\n- none\n",
        encoding="utf-8",
    )
    errors = vr.check_context_artifact(str(tmp_path))
    assert any("missing required heading" in e and "Assumptions" in e for e in errors)

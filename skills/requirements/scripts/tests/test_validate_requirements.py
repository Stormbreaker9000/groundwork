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


# ---------------------------------------------------------------------------
# Invalid fixtures — each case must fail with a non-zero exit code.
# ---------------------------------------------------------------------------
INVALID_CASES = {
    "missing_required_field": "rationale",
    "bad_enum": "priority",
    "duplicate_id": "duplicate id",
    "dangling_trace": "dangling",
    "fr_missing_ears": "ears_pattern",
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

"""Tests for the Groundwork cross-artifact traceability validator (STO-102).

Run from anywhere::

    pytest skills/design/scripts/tests

Each fixture case is a paired `design/` + `requirements/` tree, so every test
runs the real CLI end to end. Fixture artifacts carry only the fields this
tool reads — it never schema-validates, so they are deliberately not
schema-complete.
"""
import json
import os

import validate_traceability as vt

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "traceability")


def run(case, *extra):
    """Invoke the CLI against a fixture case; return the exit code."""
    root = os.path.join(FIXTURES, case)
    return vt.main(
        [os.path.join(root, "design"),
         "--requirements", os.path.join(root, "requirements"),
         *extra]
    )


# ---------------------------------------------------------------------------
# Clean set
# ---------------------------------------------------------------------------
def test_clean_set_has_no_findings(capsys):
    code = run("clean")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out


def test_clean_set_reports_both_index_sizes(capsys):
    run("clean")
    out = capsys.readouterr().out
    assert "Indexed 2 design artifact(s), 2 requirement(s)." in out


# ---------------------------------------------------------------------------
# dangling-trace (error)
# ---------------------------------------------------------------------------
def test_dangling_trace_is_an_error(capsys):
    code = run("dangling_trace")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "ERROR" in out
    assert "dangling-trace" in out
    assert "FR-404" in out


def test_dangling_trace_does_not_flag_the_resolving_id(capsys):
    """CMP-001 cites FR-001 and FR-404. Only FR-404 is a finding."""
    run("dangling_trace")
    out = capsys.readouterr().out
    assert "Summary: 1 error(s), 0 warning(s)." in out


# ---------------------------------------------------------------------------
# Usage / environment
# ---------------------------------------------------------------------------
def test_missing_design_dir_exits_2(capsys):
    code = vt.main([os.path.join(FIXTURES, "nope"),
                    "--requirements", os.path.join(FIXTURES, "clean", "requirements")])
    assert code == 2
    assert "design directory not found" in capsys.readouterr().err


def test_missing_requirements_dir_exits_2(capsys):
    code = vt.main([os.path.join(FIXTURES, "clean", "design"),
                    "--requirements", os.path.join(FIXTURES, "nope")])
    assert code == 2
    assert "requirements directory not found" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# --json / --quiet
# ---------------------------------------------------------------------------
def test_json_shape(capsys):
    run("dangling_trace", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"] == {"error": 1, "warn": 0}
    finding = payload["findings"][0]
    assert set(finding) == {"rule", "severity", "artifact_id", "path", "message"}
    assert finding["rule"] == "dangling-trace"
    assert finding["severity"] == "error"
    assert finding["artifact_id"] == "CMP-001"


def test_quiet_suppresses_the_listing_but_keeps_the_summary(capsys):
    run("dangling_trace", "--quiet")
    out = capsys.readouterr().out
    assert "dangling-trace" not in out
    assert "Summary: 1 error(s), 0 warning(s)." in out


# ---------------------------------------------------------------------------
# Unparseable frontmatter
# ---------------------------------------------------------------------------
def test_unparseable_file_is_skipped_with_a_header_note(capsys):
    """An unindexable component has an invisible traces_from, which would
    manufacture false coverage warnings. The run continues, but says so."""
    code = run("unparseable")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "1 file(s) skipped (unparseable frontmatter)" in out
    assert "Indexed 0 design artifact(s), 1 requirement(s)." in out

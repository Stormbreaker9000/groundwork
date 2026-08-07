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
# tests/ -> scripts/ -> design/ -> skills/ -> repo root. Resolved from this
# file so the suite runs from any cwd, the same handling the tool itself uses.
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))


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
    assert set(payload) == {"findings", "counts", "skipped", "duplicate_ids"}
    assert payload["counts"] == {"error": 1, "warn": 0}
    assert payload["skipped"] == []
    assert payload["duplicate_ids"] == []
    finding = payload["findings"][0]
    assert set(finding) == {"rule", "severity", "artifact_id", "path", "message"}
    assert finding["rule"] == "dangling-trace"
    assert finding["severity"] == "error"
    assert finding["artifact_id"] == "CMP-001"


def test_json_carries_the_skipped_paths(capsys):
    """The human report warns that results may be incomplete; --json exists so
    an agent need not parse prose to learn the same thing."""
    run("unparseable", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["skipped"]) == 1
    assert payload["skipped"][0].endswith(".md")


def test_quiet_keeps_error_lines_and_the_summary(capsys):
    """--quiet must match the flag's meaning in the two structural validators:
    it drops the routine listing and keeps failures. A gate that hides what
    failed is useless."""
    run("dangling_trace", "--quiet")
    out = capsys.readouterr().out
    assert "dangling-trace" in out
    assert "ERROR" in out
    assert "Summary: 1 error(s), 0 warning(s)." in out


def test_quiet_suppresses_warning_lines_but_still_counts_them(capsys):
    run("uncovered_fr", "--quiet")
    out = capsys.readouterr().out
    assert "uncovered-fr" not in out
    assert "WARN" not in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


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


# ---------------------------------------------------------------------------
# uncovered-fr (warn)
# ---------------------------------------------------------------------------
def test_uncovered_fr_is_a_warning_and_does_not_block(capsys):
    code = run("uncovered_fr")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "WARN" in out
    assert "uncovered-fr" in out
    assert "FR-002" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


def test_uncovered_fr_blocks_under_strict(capsys):
    code = run("uncovered_fr", "--strict")
    assert code == 1, capsys.readouterr().out


def test_covered_fr_is_not_flagged(capsys):
    run("uncovered_fr")
    out = capsys.readouterr().out
    assert "FR-001" not in out


def test_wont_and_obsolete_frs_are_excluded_entirely(capsys):
    """Not warned about, not counted. A `wont` requirement having no component
    is the correct outcome, and warning about it trains the reader to ignore
    the rule (spec D4)."""
    code = run("excluded_fr")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out
    assert "FR-002" not in out
    assert "FR-003" not in out


def test_interface_only_coverage_still_warns(capsys):
    """An FR is behaviour, and behaviour is owned by a component. An interface
    citing it is not coverage (spec D4)."""
    code = run("fr_covered_by_interface_only")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "uncovered-fr" in out
    assert "FR-001" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


# ---------------------------------------------------------------------------
# adr-driver-unresolved (error) / adr-driver-untraced (warn)
# ---------------------------------------------------------------------------
def test_unresolved_adr_driver_is_an_error(capsys):
    code = run("adr_driver_unresolved")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "adr-driver-unresolved" in out
    assert "NFR-404" in out
    assert "Summary: 1 error(s), 0 warning(s)." in out


def test_scan_pattern_consumes_a_whole_nfr_token():
    """'NFR-001' scans as one ID, not as a stray 'FR-001'. This is the
    alternation doing the work -- finditer is leftmost-first and 'NFR'
    precedes 'FR' -- so it holds with or without the (?<!\\w) guard."""
    assert vt.REQUIREMENT_ID_SCAN_RE.findall("NFR-001") == ["NFR-001"]


def test_scan_pattern_rejects_a_word_character_prefix():
    """This is what the (?<!\\w) guard buys. Without it 'SUBR-004' yields
    'BR-004' and 'ANFR-003' yields 'NFR-003' -- IDs nobody wrote."""
    assert vt.REQUIREMENT_ID_SCAN_RE.findall("SUBR-004") == []
    assert vt.REQUIREMENT_ID_SCAN_RE.findall("ANFR-003") == []


def test_untraced_adr_driver_is_a_warning(capsys):
    code = run("adr_driver_untraced")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "adr-driver-untraced" in out
    assert "CON-001" in out
    assert "Summary: 0 error(s), 1 warning(s)." in out


def test_adr_driver_check_accepts_any_requirement_type(capsys):
    """CON-001 resolves, so it is a warning about drift -- not an error about
    being the wrong type. agents/adr-generator.md emits [NFR-002, CON-001]
    (spec D5)."""
    run("adr_driver_untraced")
    out = capsys.readouterr().out
    assert "adr-driver-unresolved" not in out


def test_decision_drivers_section_stops_at_the_next_h2():
    """IDs under later headings are not decision drivers."""
    path = os.path.join(
        FIXTURES, "adr_driver_untraced", "design", "adr", "ADR-001-single-writer-db.md"
    )
    assert vt.extract_decision_drivers(path) == ["NFR-001", "CON-001"]


# ---------------------------------------------------------------------------
# dangling-reverse-trace (error)
# ---------------------------------------------------------------------------
def test_dangling_reverse_trace_is_an_error(capsys):
    code = run("dangling_reverse_trace")
    out = capsys.readouterr().out
    assert code == 1, out
    assert "dangling-reverse-trace" in out
    assert "CMP-999" in out
    assert "FR-001" in out


def test_empty_reverse_trace_and_asymmetry_are_never_findings(capsys):
    """The edge lives once, on design.traces_from. A requirement whose
    traces_to.design omits a component that traces to it is correct, not
    incomplete (spec D3)."""
    code = run("empty_reverse_trace")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out


# ---------------------------------------------------------------------------
# Duplicate IDs
# ---------------------------------------------------------------------------
def test_duplicate_ids_are_reported_in_the_header(capsys):
    """Both indexes are keyed by ID, so a repeat silently overwrites and the
    shadowed file becomes invisible to every rule -- a false-positive
    uncovered-fr in one file order, a missed dangling-trace in the other.
    Not a rule and not a severity: a header caveat, like the skipped note."""
    code = run("duplicate_ids")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "WARNING: duplicate id(s) across files: CMP-001, FR-001" in out
    assert "results may be unreliable" in out


def test_duplicate_ids_reach_the_json_payload(capsys):
    run("duplicate_ids", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["duplicate_ids"] == ["CMP-001", "FR-001"]


# ---------------------------------------------------------------------------
# Real-world regression: the shipped tamagotchi worked example
# ---------------------------------------------------------------------------
def test_shipped_tamagotchi_example_is_clean(capsys):
    """The one non-synthetic case: a set nobody wrote to satisfy these rules.

    It guards the D6 data fix in `docs/requirements/examples/tamagotchi/
    requirements/` -- requirement IDs wrongly parked in `traces_to.design`,
    which holds design-artifact IDs only. Re-introducing that data must fail
    CI; every other fixture here is synthetic and would not notice.
    """
    example = os.path.join(REPO_ROOT, "docs", "requirements", "examples", "tamagotchi")
    code = vt.main([
        os.path.join(example, "design"),
        "--requirements", os.path.join(example, "requirements"),
    ])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Summary: 0 error(s), 0 warning(s)." in out

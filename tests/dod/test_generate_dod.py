"""Tests for the Definition of Done generator (STO-104)."""
import os

import pytest

import generate_dod as gd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
REQS_ONLY = os.path.join(FIXTURES, "reqs_only")


def generate(fixture_dir, tmp_path, **kwargs):
    """Run the CLI over a fixture tree; return (exit_code, document_text)."""
    out = os.path.join(str(tmp_path), "definition-of-done.md")
    argv = ["--out", out]
    for stage in ("requirements", "design", "qa"):
        stage_dir = os.path.join(fixture_dir, stage)
        if os.path.isdir(stage_dir):
            argv += [f"--{stage}", stage_dir]
    for key, value in kwargs.items():
        argv += [f"--{key.replace('_', '-')}", value]
    code = gd.main(argv)
    text = ""
    if os.path.isfile(out):
        with open(out, encoding="utf-8") as handle:
            text = handle.read()
    return code, text


def test_requirements_only_set_generates(tmp_path):
    code, text = generate(REQS_ONLY, tmp_path)
    assert code == 0
    assert text.startswith("# Definition of Done")


def test_header_names_the_stages_that_fed_it(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "requirements ✓" in text
    assert "design —" in text
    assert "qa —" in text


def test_title_flag_appears_when_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path, title="Order Cancellation")
    assert "**Project / feature:** Order Cancellation" in text


def test_title_line_omitted_when_not_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Project / feature" not in text


def test_missing_requirements_dir_is_usage_error(tmp_path):
    code = gd.main(["--requirements", str(tmp_path / "nope"),
                    "--out", str(tmp_path / "dod.md")])
    assert code == 2


def test_no_stages_at_all_is_usage_error(tmp_path):
    code = gd.main(["--out", str(tmp_path / "dod.md")])
    assert code == 2


# ---------------------------------------------------------------------------
# NFR body parsing (spec E4, D8)
# ---------------------------------------------------------------------------
def _nfr(body):
    """An in-memory NFR artifact carrying only the body under test."""
    return gd.Artifact("NFR-999.md", {"id": "NFR-999", "type": "non_functional"}, body)


@pytest.mark.parametrize("line,expected", [
    ("Security → Confidentiality", "Security"),
    ("Reliability → Availability", "Reliability"),
    ("Performance Efficiency → Time behavior", "Performance Efficiency"),
    ("Functional Suitability → Functional completeness / correctness",
     "Functional Suitability"),
    ("Interaction Capability → Accessibility / Inclusivity",
     "Interaction Capability"),
    ("Compatibility → Interoperability", "Compatibility"),
    ("Flexibility → Adaptability", "Flexibility"),
    ("Maintainability → Analysability", "Maintainability"),
    ("Safety → Hazard warning", "Safety"),
    ("Extension: Observability", "Extension"),
    ("Extension: Deployability", "Extension"),
])
def test_iso_characteristic_head_token(line, expected):
    art = _nfr(f"\n## ISO 25010 Characteristic\n{line}\n\n## Quality Attribute Scenario\n")
    assert gd.parse_iso_characteristic(art) == expected


def test_iso_characteristic_tolerates_a_wrapped_line():
    art = _nfr(
        "\n## ISO 25010 Characteristic\n"
        "Extension: Observability (supporting Maintainability →\n"
        "Analysability)\n\n## Quality Attribute Scenario\n"
    )
    assert gd.parse_iso_characteristic(art) == "Extension"


def test_iso_characteristic_missing_heading_raises():
    with pytest.raises(gd.GenerationError):
        gd.parse_iso_characteristic(_nfr("\n# NFR-999\n\nNo heading here.\n"))


def test_iso_characteristic_unknown_head_raises():
    art = _nfr("\n## ISO 25010 Characteristic\nVibes → Good\n")
    with pytest.raises(gd.GenerationError):
        gd.parse_iso_characteristic(art)


def test_qas_response_measure_joins_continuation_lines():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Stimulus:** Submits an order\n"
        "- **Response measure:** End-to-end latency <= 200 ms at p95 over a\n"
        "  rolling 5-minute window; error rate <= 0.1%\n"
    )
    assert gd.parse_qas_field(art, "Response measure") == (
        "End-to-end latency <= 200 ms at p95 over a rolling 5-minute window; "
        "error rate <= 0.1%"
    )


def test_qas_field_stops_at_the_next_bullet():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Stimulus:** Submits an order\n"
        "- **Environment:** Normal operation\n"
    )
    assert gd.parse_qas_field(art, "Stimulus") == "Submits an order"


def test_qas_field_stops_at_the_next_heading():
    art = _nfr(
        "\n## Quality Attribute Scenario\n"
        "- **Response measure:** Zero defects\n"
        "\n## Rationale\nBecause.\n"
    )
    assert gd.parse_qas_field(art, "Response measure") == "Zero defects"


def test_qas_missing_field_raises():
    art = _nfr("\n## Quality Attribute Scenario\n- **Stimulus:** Something\n")
    with pytest.raises(gd.GenerationError):
        gd.parse_qas_field(art, "Response measure")


# A fixture directory nobody parametrizes is a case nobody tests. This list and
# the guard below are the same pattern tests/qa/test_validate_qa.py uses.
#
# Both cases xfail today: nothing calls parse_iso_characteristic or
# parse_qas_field yet (the NFR section is rendered starting in Task 4), so the
# CLI has no way to notice either fixture is malformed. They resolve on
# different tasks, though — nfr_missing_response_measure is reached by
# parse_qas_field, which Task 4 calls, so it un-xfails in Task 4. But
# nfr_missing_iso_heading is reached only by parse_iso_characteristic, which
# is not called until Task 7 — its marker must survive Tasks 4-6.
INVALID_CASES_WITH_MARKS = [
    pytest.param(
        "nfr_missing_iso_heading",
        marks=pytest.mark.xfail(
            reason="ISO parsing is first called in Task 7", strict=True
        ),
    ),
    pytest.param(
        "nfr_missing_response_measure",
        marks=pytest.mark.xfail(
            reason="NFR section lands in Task 4", strict=True
        ),
    ),
]
INVALID_CASE_NAMES = [case.values[0] for case in INVALID_CASES_WITH_MARKS]


@pytest.mark.parametrize("case", INVALID_CASES_WITH_MARKS)
def test_invalid_fixture_exits_one(case, tmp_path):
    code, _ = generate(os.path.join(FIXTURES, "invalid", case), tmp_path)
    assert code == 1, f"expected exit 1 for fixture {case}"


def test_every_invalid_fixture_is_exercised():
    on_disk = sorted(
        d for d in os.listdir(os.path.join(FIXTURES, "invalid"))
        if os.path.isdir(os.path.join(FIXTURES, "invalid", d))
    )
    assert on_disk == sorted(INVALID_CASE_NAMES)

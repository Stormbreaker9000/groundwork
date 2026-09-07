"""Tests for the Definition of Done generator (STO-104)."""
import os

import pytest

import generate_dod as gd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
REQS_ONLY = os.path.join(FIXTURES, "reqs_only")
FULL = os.path.join(FIXTURES, "full")


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
# nfr_missing_response_measure reaches parse_qas_field via render_nfr_gates
# (Task 4). nfr_missing_iso_heading reaches parse_iso_characteristic via
# nfrs_by_characteristic (Task 7). Both exit 1 like any other malformed
# artifact.
INVALID_CASES_WITH_MARKS = [
    pytest.param("nfr_missing_iso_heading"),
    pytest.param("nfr_missing_response_measure"),
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


# ---------------------------------------------------------------------------
# Functional acceptance + NFR fitness gates (spec D4)
# ---------------------------------------------------------------------------
def test_functional_section_has_one_gate_per_fr(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Functional Acceptance Gates" in text
    assert "**FR-001 — Cancel a pending order** (must)" in text


def test_functional_gate_carries_fit_criterion_and_source(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "100% of cancellation requests against pending orders succeed" in text
    assert "functional/FR-001-cancel-pending-order.md" in text


def test_functional_gate_does_not_inline_gherkin(tmp_path):
    """DoD is product-wide; acceptance criteria are item-specific and stay in
    the FR file. Referenced, never duplicated."""
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Given a pending order" not in text


def test_nfr_gate_uses_the_response_measure_as_the_oracle(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## NFR Fitness Gates" in text
    assert "Response measure: End-to-end latency <= 200 ms at p95" in text


def test_nfr_gate_names_the_scenario(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Submits an order via `POST /orders`" in text
    assert "Order API service" in text


def test_without_qa_gates_annotate_verification_method(tmp_path):
    """No QA set on disk means no evidence about CI, so the gate says what the
    requirement claims rather than asserting a pipeline nobody has seen."""
    _, text = generate(REQS_ONLY, tmp_path)
    assert "`[verification: test]`" in text
    assert "`[CI]`" not in text


# ---------------------------------------------------------------------------
# Architectural conformance (spec D6)
# ---------------------------------------------------------------------------
def test_accepted_adr_becomes_a_conformance_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Architectural Conformance Gates" in text
    assert "**ADR-001 — Oracle as the order store**" in text
    assert "Oracle 19c as the system of record" in text


def test_rejected_adr_is_not_a_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "ADR-002" not in text


def test_component_dependency_edges_become_a_gate(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "**CMP-001 — Order Service**" in text
    assert "IF-001" in text


def test_component_without_dependencies_has_no_gate(tmp_path):
    """Nothing to assert is not the same as an empty assertion."""
    _, text = generate(FULL, tmp_path)
    assert "CMP-002" not in text


def test_conformance_section_absent_without_a_design_set(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Architectural Conformance Gates" not in text


# ---------------------------------------------------------------------------
# Coverage + declared-unenforced register (spec D5, D7)
# ---------------------------------------------------------------------------
def test_coverage_lists_the_items_covering_each_requirement(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Test Coverage" in text
    assert "TS-001" in text
    assert "TS-002" in text


def test_uncovered_requirement_is_visible_as_a_gap(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "no test-strategy item cites this requirement" in text


def test_enforcement_tag_is_derived_from_covering_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "**FR-001 — Cancel a pending order** (must) `[CI]`" in text
    assert "**NFR-002 — Audit log integrity** (must) `[manual]`" in text


def test_unenforced_items_get_their_own_register(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "## Declared Unenforced" in text
    assert "TS-004" in text
    assert "The cut-off is a single conditional" in text


def test_unenforced_register_is_not_a_checklist(tmp_path):
    """A register records what is not gated; a checkbox would imply it is."""
    _, text = generate(FULL, tmp_path)
    register = text.split("## Declared Unenforced", 1)[1]
    assert "- [ ]" not in register.split("\n## ", 1)[0]


def test_unenforced_section_absent_when_nothing_is_unenforced(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Declared Unenforced" not in text


# ---------------------------------------------------------------------------
# Documentation + deployment readiness (spec D4)
# ---------------------------------------------------------------------------
def test_documentation_section_lists_must_frs(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Documentation Requirements" in text
    docs = text.split("## Documentation Requirements", 1)[1]
    assert "FR-001" in docs


def test_documentation_section_lists_operational_nfrs(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    docs = text.split("## Documentation Requirements", 1)[1]
    assert "NFR-002 (Security)" in docs


def test_deployment_section_lists_security_nfrs_and_rules(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "## Deployment / Operational Readiness" in text
    deploy = text.split("## Deployment / Operational Readiness", 1)[1]
    assert "NFR-002" in deploy
    assert "CON-001" in deploy
    assert "BR-001" in deploy


def test_non_operational_nfr_is_not_a_deployment_gate(tmp_path):
    """NFR-001 is Performance Efficiency — neither Security nor Reliability."""
    _, text = generate(REQS_ONLY, tmp_path)
    deploy = text.split("## Deployment / Operational Readiness", 1)[1]
    security_line = [
        line for line in deploy.splitlines() if "Security NFR gates" in line
    ][0]
    assert "NFR-001" not in security_line


# ---------------------------------------------------------------------------
# PR checklist (spec D4)
# ---------------------------------------------------------------------------
def _pr_section(text):
    body = text.split("## PR Checklist", 1)[1]
    return body.split("\n## ", 1)[0]


def test_pr_checklist_leads_the_document(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert text.index("## PR Checklist") < text.index("## Functional Acceptance Gates")


def test_pr_checklist_carries_manual_qa_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "TS-003" in _pr_section(text)


def test_pr_checklist_omits_ci_enforced_items(tmp_path):
    """A passing build is their evidence; a checkbox would ask for it twice."""
    _, text = generate(FULL, tmp_path)
    section = _pr_section(text)
    assert "TS-001" not in section
    assert "TS-002" not in section


def test_pr_checklist_omits_unenforced_items(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "TS-004" not in _pr_section(text)


def test_pr_checklist_carries_non_test_nfrs(tmp_path):
    """NFR-002 is verification_method: inspection — a human records evidence."""
    _, text = generate(REQS_ONLY, tmp_path)
    section = _pr_section(text)
    assert "NFR-002" in section
    assert "NFR-001" not in section


def test_pr_checklist_carries_accepted_adrs(tmp_path):
    _, text = generate(FULL, tmp_path)
    assert "ADR-001" in _pr_section(text)


def test_pr_checklist_carries_a_documentation_line(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Documentation updated" in _pr_section(text)


def test_gate_count_only_grows_as_stages_are_added(tmp_path):
    """Spec D3: each stage's run supersedes the last and adds gates. A stage
    that removed gates would mean a later run had less information, which
    cannot happen."""
    out_a = os.path.join(str(tmp_path), "a.md")
    out_b = os.path.join(str(tmp_path), "b.md")
    full_reqs = os.path.join(FULL, "requirements")

    assert gd.main(["--requirements", full_reqs, "--out", out_a]) == 0
    assert gd.main([
        "--requirements", full_reqs,
        "--design", os.path.join(FULL, "design"),
        "--qa", os.path.join(FULL, "qa"),
        "--out", out_b,
    ]) == 0

    def gates(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read().count("- [ ] ")

    assert gates(out_b) > gates(out_a)


# ---------------------------------------------------------------------------
# Wiring: every stage skill must invoke the generator, and the agent must be
# gone. A skill that stops calling it leaves a stale DoD on disk, which is the
# failure this ticket exists to end.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
PLUGIN = os.path.join(REPO_ROOT, "plugin")


@pytest.mark.parametrize("stage", ["requirements", "design", "qa"])
def test_every_stage_skill_invokes_the_generator(stage):
    path = os.path.join(PLUGIN, "skills", stage, "SKILL.md")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    assert "generate_dod.py" in text, f"{stage} SKILL.md does not run generate_dod.py"
    assert ".sdlc/definition-of-done.md" in text


def test_dod_generator_agent_is_gone():
    assert not os.path.exists(os.path.join(PLUGIN, "agents", "dod-generator.md"))


def test_dod_template_is_gone():
    assert not os.path.exists(
        os.path.join(PLUGIN, "skills", "requirements", "templates",
                     "definition-of-done.md")
    )

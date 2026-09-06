"""Tests for the documentation-site reference exporter (STO-250)."""
import json
import os

import pytest

import export_reference
import export_reference as er

ENTRY_KEYS = {"id", "severities", "applies_to", "fields", "summary"}


def test_export_rules_records_its_source_module():
    payload = er.export_rules()
    assert payload["design"]["linter"] == "lint_design_content.py"
    assert payload["requirements"]["linter"] == "lint_requirements_content.py"


def test_export_rules_carries_every_registry_entry():
    payload = er.export_rules()
    assert len(payload["design"]["rules"]) == 8
    assert len(payload["requirements"]["rules"]) == 6
    for section in payload.values():
        for rule in section["rules"]:
            assert set(rule) == ENTRY_KEYS


def test_export_rules_is_the_registry_not_a_copy():
    # The exporter must not restate rule text. If it drifts from the
    # registry, this fails.
    import lint_design_content as ldc
    payload = er.export_rules()
    assert [r["id"] for r in payload["design"]["rules"]] == [
        r["id"] for r in ldc.RULES
    ]


def test_written_json_is_stable_and_newline_terminated():
    target = os.path.join(er.OUT_DIR, "rules.json")
    with open(target, "r", encoding="utf-8") as handle:
        text = handle.read()
    assert text.endswith("\n")
    assert json.loads(text) == json.loads(
        json.dumps(er.export_rules(), indent=2, sort_keys=True)
    )


def test_check_mode_detects_clean_stale_and_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(er, "OUT_DIR", str(tmp_path))

    # Clean: freshly written output is current.
    assert er.main([]) == 0
    assert er.main(["--check"]) == 0

    # Stale: content that does not match what the registries produce.
    (tmp_path / "rules.json").write_text("garbage\n", encoding="utf-8")
    assert er.main(["--check"]) == 1
    assert "stale: " in capsys.readouterr().err

    # Missing: the file is not there at all.
    (tmp_path / "rules.json").unlink()
    assert er.main(["--check"]) == 1

    # Check mode must never write.
    assert not (tmp_path / "rules.json").exists()


def test_export_fields_covers_both_schemas():
    payload = er.export_fields()
    assert set(payload) == {"design", "requirements"}


def test_design_fields_include_base_and_conditional_properties():
    fields = {f["name"]: f for f in er.export_fields()["design"]}
    # Base property, required for every design artifact.
    assert fields["id"]["required_for"] == ["*"]
    # Conditional: only components must declare a responsibility.
    assert fields["responsibility"]["required_for"] == ["component"]
    # Conditional: only interfaces must declare a provider.
    assert fields["provider"]["required_for"] == ["interface"]
    # Enums survive.
    assert set(fields["type"]["enum"]) == {
        "component", "interface", "adr", "diagram"
    }


def test_requirement_conditional_required_without_added_properties():
    # requirement.schema.json's only allOf branch adds a `required` entry for
    # a property already declared in the base `properties` block. The
    # extractor must annotate the existing field rather than skip the branch.
    fields = {f["name"]: f for f in er.export_fields()["requirements"]}
    assert fields["ears_pattern"]["required_for"] == ["functional"]


def test_export_agents_covers_every_agent_file():
    agents = er.export_agents()
    on_disk = [
        n[:-3] for n in os.listdir(os.path.join(er.PLUGIN_ROOT, "agents"))
        if n.endswith(".md")
    ]
    assert len(agents) == len(on_disk) == 15
    assert {a["name"] for a in agents} == set(on_disk)


def test_export_agents_reads_title_and_description():
    by_name = {a["name"]: a for a in er.export_agents()}
    assert by_name["design-critic"]["title"] == "Design Critic"
    assert by_name["design-critic"]["description"].startswith(
        "Architecture quality critic."
    )
    for agent in er.export_agents():
        assert agent["title"], f"{agent['name']} has no H1"
        assert agent["description"], f"{agent['name']} has no description"


def test_parse_agent_file_title_skips_fenced_example_heading():
    # Regression test for the first-match-anywhere title bug: a `# `-shaped
    # line inside a fenced example block, appearing BEFORE the real title,
    # must not be picked up as the title. Against the old implementation
    # (er._H1_RE.search(text) with no offset) this returns "Example
    # Component" instead of "Real Title".
    text = (
        "---\n"
        "description: Test agent.\n"
        "---\n"
        "\n"
        "```markdown\n"
        "# CMP-001 — Example Component\n"
        "```\n"
        "\n"
        "# Real Title\n"
    )
    result = er._parse_agent_file(text, "test-agent")
    assert result["title"] == "Real Title"


def test_parse_agent_file_no_heading_returns_empty_title():
    text = "---\ndescription: Test agent.\n---\n\nNo heading in this body.\n"
    result = er._parse_agent_file(text, "test-agent")
    assert result["title"] == ""


def test_parse_agent_file_second_frontmatter_key_yields_empty_description():
    # today's _DESCRIPTION_RE anchors on exactly the three-line frontmatter
    # block; a second key breaks that shape and the description silently
    # comes back empty rather than raising.
    text = (
        "---\n"
        "description: Test agent.\n"
        "model: sonnet\n"
        "---\n"
        "\n"
        "# Title\n"
    )
    result = er._parse_agent_file(text, "test-agent")
    assert result["description"] == ""


def test_parse_agent_file_strips_quoted_description():
    text = (
        "---\n"
        'description: "Quoted agent description."\n'
        "---\n"
        "\n"
        "# Title\n"
    )
    result = er._parse_agent_file(text, "test-agent")
    assert result["description"] == "Quoted agent description."


def test_all_outputs_are_written_and_current():
    assert er.main(["--check"]) == 0


def test_rules_export_carries_the_traceability_registry():
    payload = export_reference.export_rules()
    assert set(payload) == {"design", "requirements", "traceability"}
    section = payload["traceability"]
    assert section["linter"] == "validate_traceability.py"
    assert {r["id"] for r in section["rules"]} == {
        "dangling-trace",
        "adr-driver-unresolved",
        "dangling-reverse-trace",
        "misplaced-requirement-trace",
        "uncovered-fr",
        "adr-driver-untraced",
        "adr-driver-unlisted",
        "index-unparseable",
        "duplicate-id",
    }


def test_traceability_rules_declare_no_fields():
    # The Fields column is meaningless for this tool; RuleTable drops it.
    for rule in export_reference.export_rules()["traceability"]["rules"]:
        assert rule["fields"] == []


def test_stages_export_carries_six_areas_each():
    payload = export_reference.export_stages()
    assert set(payload) == {"requirements", "design"}
    for stage in payload.values():
        assert len(stage["areas"]) == 6
        for area in stage["areas"]:
            assert set(area) == {"name", "detail"}
            assert area["name"] and area["detail"]


def test_stages_export_reads_the_real_skill_files():
    payload = export_reference.export_stages()
    req = [a["name"] for a in payload["requirements"]["areas"]]
    des = [a["name"] for a in payload["design"]["areas"]]
    assert req[0] == "Core functionality"
    assert req[-1] == "Out of scope"
    assert des[0] == "Runtime and stack"
    assert des[-1] == "Team constraints"


def test_stages_export_raises_when_the_anchor_moves():
    # A silent empty result is the failure mode this parser must not have:
    # the drift gate compares committed JSON to current output, so a
    # consistently empty extraction would read as "current" forever.
    with pytest.raises(ValueError, match="anchor not found"):
        export_reference._coverage_areas("no such anchor here", "## Missing")


# --- pipeline export (STO-220) ---------------------------------------------

PIPELINE_STAGE_KEYS = {"number", "label", "retired", "contracts"}
PIPELINE_CONTRACT_KEYS = {"name", "yaml", "transients"}


def test_pipeline_export_covers_both_orchestrators():
    payload = er.export_pipeline()
    assert set(payload) == {"requirements", "design"}
    assert payload["requirements"]["agent"] == "requirements-orchestrator"
    assert payload["design"]["agent"] == "design-orchestrator"
    for stage in payload.values():
        for entry in stage["stages"]:
            assert set(entry) == PIPELINE_STAGE_KEYS
            for contract in entry["contracts"]:
                assert set(contract) == PIPELINE_CONTRACT_KEYS


def test_pipeline_export_reads_the_real_stage_order():
    payload = er.export_pipeline()
    req = [s["number"] for s in payload["requirements"]["stages"]]
    des = [s["number"] for s in payload["design"]["stages"]]
    assert req == ["1", "2", "3", "4", "5", "6", "6.5", "7"]
    assert des == ["1", "2", "3", "4", "5", "6", "7", "8",
                   "9", "9.5", "9.6", "10", "11", "12"]


def test_pipeline_export_names_every_contract():
    payload = er.export_pipeline()

    def names(stage):
        return [c["name"] for s in payload[stage]["stages"] for c in s["contracts"]]

    assert names("requirements") == [
        "generation_brief", "draft_requirements", "critique_report",
        "context_artifact", "formatter_result",
    ]
    assert names("design") == [
        "generation_brief", "draft_components", "draft_interfaces",
        "critique_report", "design_context_artifact", "formatter_result",
    ]


def test_pipeline_export_splits_one_fence_holding_two_contracts():
    # Design Stage 6 defines draft_components and draft_interfaces as two
    # top-level keys inside a single ```yaml fence. Each contract must get
    # its own slice, not the whole block twice.
    payload = er.export_pipeline()
    stage6 = next(s for s in payload["design"]["stages"] if s["number"] == "6")
    assert [c["name"] for c in stage6["contracts"]] == [
        "draft_components", "draft_interfaces",
    ]
    components, interfaces = stage6["contracts"]
    assert components["yaml"].startswith("draft_components:")
    assert interfaces["yaml"].startswith("draft_interfaces:")
    assert "draft_interfaces:" not in components["yaml"]


def test_pipeline_export_skips_past_a_non_matching_first_block():
    # Design Stage 8's section opens with a `capability_map:` block; the
    # contract its heading names is the SECOND block. Taking the first block
    # after the heading would publish the wrong shape under the right name.
    payload = er.export_pipeline()
    stage8 = next(s for s in payload["design"]["stages"] if s["number"] == "8")
    assert [c["name"] for c in stage8["contracts"]] == ["critique_report"]
    assert stage8["contracts"][0]["yaml"].startswith("critique_report:")


def test_pipeline_export_ignores_a_backticked_field():
    # Design Stage 7 is "Back-fill `depends_on`" — a field, not a contract,
    # and it carries no YAML at all. A rule keyed on "the heading contains
    # backticks" would raise here.
    payload = er.export_pipeline()
    stage7 = next(s for s in payload["design"]["stages"] if s["number"] == "7")
    assert stage7["contracts"] == []


def test_pipeline_export_marks_retired_stages():
    payload = er.export_pipeline()
    retired = [s["number"] for s in payload["design"]["stages"] if s["retired"]]
    assert retired == ["11", "12"]
    assert all(not s["retired"] for s in payload["requirements"]["stages"])


def test_pipeline_export_carries_the_transient_markers():
    payload = er.export_pipeline()
    stage6 = next(s for s in payload["design"]["stages"] if s["number"] == "6")
    components, interfaces = stage6["contracts"]
    assert components["transients"] == ["required_capabilities"]
    assert interfaces["transients"] == ["consumed_by", "satisfies_capabilities"]

    # M1 has a fourth transient. STO-220's ticket lists three, all from M2;
    # `applies_to` is declared by constraint-specialist and appears in no
    # hand-written summary of the pipeline. Pinned here so the count cannot
    # quietly drop back to the three someone remembered.
    stage5 = next(s for s in payload["requirements"]["stages"] if s["number"] == "5")
    assert stage5["contracts"][0]["transients"] == ["applies_to"]


def test_pipeline_export_raises_when_a_named_contract_has_no_yaml():
    # The assert-the-join behaviour. Renaming a contract in the heading but
    # not in the YAML must fail loudly: a silent skip would shrink the
    # published table while CI stayed green off self-consistent JSON.
    text = (
        "## Stage 4 — Dispatch: the `renamed_brief` hand-off\n\n"
        "```yaml\ngeneration_brief:\n  scope: all\n```\n"
    )
    with pytest.raises(ValueError, match="renamed_brief"):
        er._parse_pipeline(text, "agents/fake.md")


def test_pipeline_export_raises_when_a_file_has_no_stages():
    with pytest.raises(ValueError, match="no stage headings"):
        er._parse_pipeline("# Some agent\n\nNo stages here.\n", "agents/fake.md")


def test_contract_names_reads_the_heading_not_the_verb():
    assert er._contract_names("Dispatch: the `generation_brief` hand-off") == [
        "generation_brief"
    ]
    assert er._contract_names(
        "Collect drafts: the `draft_components` / `draft_interfaces` hand-offs"
    ) == ["draft_components", "draft_interfaces"]
    assert er._contract_names("Synthesise the `design_context_artifact`") == [
        "design_context_artifact"
    ]
    assert er._contract_names("Synthesize the `context_artifact`") == [
        "context_artifact"
    ]
    # No "the" before the backticks: a field, not a contract.
    assert er._contract_names("Back-fill `depends_on`") == []
    # "the" not followed by backticks: prose, not a contract.
    assert er._contract_names("Consume the clarification context") == []


def test_pipeline_is_one_of_the_gated_outputs():
    assert "pipeline.json" in export_reference.OUTPUTS

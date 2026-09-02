"""Tests for the documentation-site reference exporter (STO-250)."""
import json
import os

import export_reference as er

ENTRY_KEYS = {"id", "severities", "applies_to", "fields", "summary"}


def test_export_rules_has_both_linters():
    payload = er.export_rules()
    assert set(payload) == {"design", "requirements"}


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
        n[:-3] for n in os.listdir(os.path.join(er.REPO_ROOT, "agents"))
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

"""Tests for the Groundwork design content-quality linter (STO-208)."""
import os

import lint_design_content as ldc

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "fixtures", "lint")


def rules_for(subdir):
    return {f.rule for f in ldc.lint_dir(os.path.join(LINT, subdir))}


def findings_for(subdir, rule):
    return [f for f in ldc.lint_dir(os.path.join(LINT, subdir)) if f.rule == rule]


def test_read_body_strips_frontmatter_fence():
    # Regression: _read_body must land on the real content, not on the
    # closing '---' fence line that extract_frontmatter_block's capture
    # group excludes but does not itself consume.
    path = os.path.join(LINT, "clean", "components", "CMP-001-order-service.md")
    body = ldc._read_body(path)
    assert body.lstrip().startswith("# order-service")
    assert "---" not in body.splitlines()[0]


def test_read_body_returns_empty_for_unreadable_file():
    assert ldc._read_body(os.path.join(LINT, "does-not-exist.md")) == ""


def test_read_body_returns_full_text_for_missing_frontmatter():
    path = os.path.join(LINT, "clean", "assumptions.md")
    with open(path, "r", encoding="utf-8") as handle:
        expected = handle.read()
    assert ldc._read_body(path) == expected


def test_clean_fixture_has_no_findings():
    assert ldc.lint_dir(os.path.join(LINT, "clean")) == []


def test_advisory_exit_is_zero():
    assert ldc.main([os.path.join(LINT, "vague-responsibility")]) == 0


def test_missing_directory_exits_two():
    assert ldc.main([os.path.join(LINT, "does-not-exist")]) == 2


def test_strict_is_a_noop_without_error_severity(capsys):
    # No rule in STO-208 emits `error`, so --strict must still exit 0 even
    # over a fixture with findings. This pins the advisory contract.
    code = ldc.main([os.path.join(LINT, "god-component"), "--strict"])
    capsys.readouterr()
    assert code == 0


def test_vague_responsibility_flagged():
    assert "vague-responsibility" in rules_for("vague-responsibility")


def test_vague_responsibility_is_warn_when_unquantified():
    found = findings_for("vague-responsibility", "vague-responsibility")
    assert found
    assert all(f.severity == "warn" for f in found)


def test_vague_responsibility_downgraded_when_quantified():
    fm = {"type": "component",
          "responsibility": "Serves reads fast, within 50 ms at p99."}
    found = ldc.check_vague_responsibility("CMP-001", fm, "")
    assert found, "expected a finding for 'fast'"
    assert all(f.severity == "info" for f in found)


def test_god_component_flagged():
    assert "god-component" in rules_for("god-component")


def test_god_component_ignores_adverb_conjunction():
    # The noise case the verb anchoring exists to suppress.
    fm = {"type": "component",
          "responsibility": "Persists pet state durably and atomically."}
    assert ldc.check_god_component("CMP-001", fm, "") == []


def test_god_component_ignores_noun_conjunction():
    fm = {"type": "component",
          "responsibility": "Owns the order aggregate and every transition of "
                            "its state."}
    assert ldc.check_god_component("CMP-001", fm, "") == []


def test_component_rules_skip_non_components():
    fm = {"type": "interface", "responsibility": "Provides fast and easy access."}
    assert ldc.check_vague_responsibility("IF-001", fm, "") == []
    assert ldc.check_god_component("IF-001", fm, "") == []


# ---------------------------------------------------------------------------
# Interface rules
# ---------------------------------------------------------------------------
def test_orphan_interface_flagged():
    found = findings_for("orphan-interface", "orphan-interface")
    assert len(found) == 1
    assert found[0].artifact_id == "IF-002"
    assert found[0].severity == "warn"


def test_consumed_interface_not_flagged():
    found = findings_for("orphan-interface", "orphan-interface")
    assert "IF-001" not in {f.artifact_id for f in found}


def test_error_modes_handwaved_flagged():
    found = findings_for("error-modes", "error-modes-handwaved")
    assert len(found) == 1
    assert "gracefully" in found[0].excerpt


def test_concrete_error_mode_not_flagged():
    fm = {"type": "interface",
          "error_modes": ["The requested order id does not exist."]}
    assert ldc.check_error_modes_handwaved("IF-001", fm, "") == []


def test_error_modes_rule_skips_non_interfaces():
    fm = {"type": "component", "error_modes": ["Handled gracefully."]}
    assert ldc.check_error_modes_handwaved("CMP-001", fm, "") == []


# ---------------------------------------------------------------------------
# body_section
# ---------------------------------------------------------------------------
def test_body_section_stops_at_same_level_heading():
    text = "## A\n\nalpha\n\n## B\n\nbeta\n"
    assert "alpha" in ldc.core.body_section(text, "## A")
    assert "beta" not in ldc.core.body_section(text, "## A")


def test_body_section_keeps_deeper_subsections():
    text = "## Decision Outcome\n\npicked\n\n### Consequences\n\n- Good: x\n\n## Next\n"
    section = ldc.core.body_section(text, "## Decision Outcome")
    assert "Consequences" in section and "Next" not in section


def test_body_section_absent_heading_is_empty():
    assert ldc.core.body_section("## A\n\nalpha\n", "## Missing") == ""


# ---------------------------------------------------------------------------
# ADR rules
# ---------------------------------------------------------------------------
def test_adr_consequences_one_sided_flagged():
    found = findings_for("adr-smells", "adr-consequences-one-sided")
    assert len(found) == 1
    assert found[0].artifact_id == "ADR-001"


def test_adr_vague_driver_flagged():
    found = findings_for("adr-smells", "adr-vague-driver")
    assert found
    assert any("scalable" in f.message for f in found)


def test_adr_option_unexamined_flagged():
    found = findings_for("adr-smells", "adr-option-unexamined")
    assert len(found) == 1
    assert "Snapshot table" in found[0].excerpt
    assert found[0].severity == "info"


def test_proposed_adr_with_placeholders_is_clean():
    # The formatter writes these placeholders on purpose for a decision that
    # has not been taken. Firing here would train the reader to ignore the rule.
    assert ldc.lint_dir(os.path.join(LINT, "adr-proposed")) == []


def test_balanced_consequences_not_flagged():
    body = ("## Decision Outcome\n\nx\n\n### Consequences\n\n"
            "- Good: fast reads.\n- Bad: writes fan out.\n")
    fm = {"type": "adr", "decision_status": "accepted"}
    assert ldc.check_adr_consequences_one_sided("ADR-001", fm, body) == []


def test_adr_rules_skip_non_adrs():
    body = "### Consequences\n\n- Good: only upside.\n"
    fm = {"type": "component", "decision_status": "accepted"}
    assert ldc.check_adr_consequences_one_sided("CMP-001", fm, body) == []


def test_adr_consequences_placeholder_only_is_clean():
    # The placeholder guard must mean "this section IS the placeholder", not
    # "a placeholder-shaped line appears somewhere in this section" -- this
    # is the case where that distinction doesn't yet matter (fix round 1).
    body = ("## Decision Outcome\n\nx\n\n### Consequences\n\n"
            "- None — the decision is pending.\n")
    fm = {"type": "adr", "decision_status": "accepted"}
    assert ldc.check_adr_consequences_one_sided("ADR-001", fm, body) == []


def test_adr_consequences_stray_none_bullet_still_flagged():
    # Regression for fix round 1: an unrelated "- None ..." bullet sitting
    # alongside real Good bullets must not silence the one-sided finding --
    # _PLACEHOLDER_RE.search over the whole section previously did exactly
    # that.
    body = ("## Decision Outcome\n\nx\n\n### Consequences\n\n"
            "- Good: fast reads.\n- Good: simple to reason about.\n"
            "- None of the existing migrations need to change.\n")
    fm = {"type": "adr", "decision_status": "accepted"}
    found = ldc.check_adr_consequences_one_sided("ADR-001", fm, body)
    assert len(found) == 1


def test_adr_option_unexamined_skips_placeholder_section():
    # Regression for fix round 1: a `proposed` ADR can carry options in
    # frontmatter (adr-generator contract) while the body honestly records
    # that none have been examined yet via the formatter's placeholder --
    # that must not be reported as an unexamined option.
    body = "## Considered Options\n\n- None — no alternatives are recorded yet.\n"
    fm = {
        "type": "adr",
        "decision_status": "proposed",
        "considered_options": ["Event sourcing", "Snapshot table"],
    }
    assert ldc.check_adr_option_unexamined("ADR-001", fm, body) == []

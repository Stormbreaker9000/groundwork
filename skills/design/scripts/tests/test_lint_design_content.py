"""Tests for the Groundwork design content-quality linter (STO-208)."""
import os

import lint_design_content as ldc

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "fixtures", "lint")


def rules_for(subdir):
    return {f.rule for f in ldc.lint_dir(os.path.join(LINT, subdir))}


def findings_for(subdir, rule):
    return [f for f in ldc.lint_dir(os.path.join(LINT, subdir)) if f.rule == rule]


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

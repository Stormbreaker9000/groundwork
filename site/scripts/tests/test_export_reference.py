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

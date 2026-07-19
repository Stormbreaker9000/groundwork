"""Tests for the Groundwork design-artifact validator.

Run from anywhere::

    pytest skills/design/scripts/tests

The suite asserts the validator PASSES (exit 0) on the conformant fixture set
and FAILS (non-zero exit) with a targeted message on each invalid fixture case,
mirroring the M1 requirements suite.
"""
import os

import pytest

import validate_design as vd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
VALID_DIR = os.path.join(FIXTURES, "valid")
INVALID_DIR = os.path.join(FIXTURES, "invalid")
SCHEMA = vd.default_schema_path()


def run(design_dir):
    """Invoke the CLI entry point against a fixture dir; return the exit code."""
    return vd.main([design_dir, "--schema", SCHEMA])


# ---------------------------------------------------------------------------
# Valid fixtures
# ---------------------------------------------------------------------------
def test_valid_set_passes(capsys):
    code = run(VALID_DIR)
    out = capsys.readouterr().out
    assert code == 0, f"expected exit 0 on valid fixtures, got {code}\n{out}"
    # The CMP -> IF -> CMP graph closes: both components and the interface pass.
    assert "CMP-001" in out
    assert "CMP-002" in out
    assert "IF-001" in out


def test_skip_files_and_subtrees_are_ignored(capsys):
    """assumptions.md, index.yaml, and the adr/ + diagrams/ subtrees must not be
    validated as artifacts."""
    run(VALID_DIR)
    out = capsys.readouterr().out
    assert "assumptions.md" not in out
    assert "index.yaml" not in out
    assert "ADR-001" not in out
    assert "c4-container" not in out


# ---------------------------------------------------------------------------
# Invalid fixtures — each case must fail with a non-zero exit code.
# ---------------------------------------------------------------------------
INVALID_CASES = {
    "missing_required_field": "responsibility",
    "bad_enum": "boundary",
    "duplicate_id": "duplicate id",
    "prefix_type_mismatch": "implies type",
    "dangling_depends_on": "depends_on",
    "dangling_provider": "provider",
    "traces_from_bad_format": "traces_from",
    "missing_assumptions": "assumptions",
    "assumptions_missing_heading": "missing required heading",
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
    assert vd.PREFIX_TO_TYPE == {"CMP": "component", "IF": "interface"}


def test_extract_frontmatter_block():
    text = "---\nid: CMP-001\ntype: component\n---\n# body\n"
    block = vd.extract_frontmatter_block(text)
    assert block is not None
    assert "id: CMP-001" in block


def test_id_prefix_type_mismatch_is_flagged():
    df = vd.DesignFile("mem://x")
    df.frontmatter = {"id": "IF-010", "type": "component"}
    vd.cross_file_checks([df])
    assert any("implies type" in e for e in df.errors)


def test_depends_on_resolves_to_known_interface():
    comp = vd.DesignFile("mem://c")
    comp.frontmatter = {"id": "CMP-001", "type": "component", "depends_on": ["IF-001"]}
    iface = vd.DesignFile("mem://i")
    iface.frontmatter = {"id": "IF-001", "type": "interface", "provider": "CMP-001"}
    vd.cross_file_checks([comp, iface])
    assert comp.ok, comp.errors
    assert iface.ok, iface.errors


def test_dangling_depends_on_is_flagged():
    comp = vd.DesignFile("mem://c")
    comp.frontmatter = {"id": "CMP-001", "type": "component", "depends_on": ["IF-404"]}
    vd.cross_file_checks([comp])
    assert any("depends_on" in e and "IF-404" in e for e in comp.errors)


def test_dangling_provider_is_flagged():
    iface = vd.DesignFile("mem://i")
    iface.frontmatter = {"id": "IF-001", "type": "interface", "provider": "CMP-404"}
    vd.cross_file_checks([iface])
    assert any("provider" in e and "CMP-404" in e for e in iface.errors)


def test_traces_from_bad_shape_is_flagged():
    comp = vd.DesignFile("mem://c")
    comp.frontmatter = {"id": "CMP-001", "type": "component", "traces_from": ["NOPE-1"]}
    vd.cross_file_checks([comp])
    assert any("traces_from" in e for e in comp.errors)


def test_traces_from_requirement_shape_is_accepted():
    comp = vd.DesignFile("mem://c")
    comp.frontmatter = {"id": "CMP-001", "type": "component", "traces_from": ["FR-001", "NFR-014"]}
    vd.cross_file_checks([comp])
    assert not any("traces_from" in e for e in comp.errors)


# ---------------------------------------------------------------------------
# Assumptions artifact — presence + heading gate (shares _check_project_artifact
# with M1; the heading-anchoring behavior is pinned there and re-pinned here).
# ---------------------------------------------------------------------------
def _write_assumptions(tmp_path, text):
    (tmp_path / "assumptions.md").write_text(text, encoding="utf-8")


def test_assumptions_present_passes(tmp_path):
    _write_assumptions(
        tmp_path,
        "## Assumptions\n- none\n## Dependencies\n- none\n## Open Questions\n- none\n",
    )
    assert vd.check_assumptions_artifact(str(tmp_path)) == []


def test_assumptions_missing_file_is_flagged(tmp_path):
    errors = vd.check_assumptions_artifact(str(tmp_path))
    assert any("assumptions artifact" in e for e in errors)


def test_assumptions_missing_heading_is_flagged(tmp_path):
    _write_assumptions(tmp_path, "## Assumptions\n- none\n## Dependencies\n- none\n")
    errors = vd.check_assumptions_artifact(str(tmp_path))
    assert any("missing required heading" in e for e in errors)


def test_assumptions_non_utf8_is_reported_not_raised(tmp_path):
    (tmp_path / "assumptions.md").write_bytes(b"\xff\xfe## Assumptions\n")
    errors = vd.check_assumptions_artifact(str(tmp_path))
    assert errors and any("could not read" in e for e in errors)


def test_assumptions_h3_heading_is_rejected(tmp_path):
    """An H3 '### Assumptions' contains the substring '## Assumptions' but must
    not satisfy the '## Assumptions' H2 requirement."""
    _write_assumptions(
        tmp_path,
        "### Assumptions\n- none\n## Dependencies\n- none\n## Open Questions\n- none\n",
    )
    errors = vd.check_assumptions_artifact(str(tmp_path))
    assert any("missing required heading" in e and "Assumptions" in e for e in errors)


# ---------------------------------------------------------------------------
# The two cases Part F singles out.
# ---------------------------------------------------------------------------
def _base_interface():
    return {
        "id": "IF-001", "type": "interface", "title": "x", "description": "x",
        "traces_from": [], "traces_to": {}, "status": "draft", "confidence": "high",
        "created_at": "2026-07-18", "provider": "CMP-001",
        "operations": [{"name": "a", "summary": "b"}], "interaction": "synchronous",
        "error_modes": ["boom"],
    }


def _base_component():
    return {
        "id": "CMP-001", "type": "component", "title": "x", "description": "x",
        "traces_from": [], "traces_to": {}, "status": "draft", "confidence": "high",
        "created_at": "2026-07-18", "responsibility": "does one thing",
        "boundary": "internal", "depends_on": [],
    }


def test_component_field_on_interface_is_rejected():
    """A component-only field on an interface must be rejected. This is the test
    that proves unevaluatedProperties actually composed — get the schema wrong
    and it silently accepts anything."""
    validator = core_validator()
    interface = _base_interface()
    interface["responsibility"] = "I do not belong on an interface"
    errors = _schema_errors(validator, interface)
    assert errors, "schema wrongly accepted a component field on an interface"


def test_interface_field_on_component_is_rejected():
    """The mirror direction, so neither branch leaks into the other."""
    validator = core_validator()
    component = _base_component()
    component["provider"] = "CMP-002"
    errors = _schema_errors(validator, component)
    assert errors, "schema wrongly accepted an interface field on a component"


# ---------------------------------------------------------------------------
# The stdlib fallback path (no jsonschema): per-type required-field lists.
# ---------------------------------------------------------------------------
def test_fallback_accepts_valid_per_type():
    assert vd._fallback_validate(_base_component()) == []
    assert vd._fallback_validate(_base_interface()) == []


def test_fallback_flags_missing_component_field():
    comp = _base_component()
    del comp["responsibility"]
    errors = vd._fallback_validate(comp)
    assert any("responsibility" in e for e in errors)


def test_fallback_flags_missing_interface_field():
    iface = _base_interface()
    del iface["provider"]
    errors = vd._fallback_validate(iface)
    assert any("provider" in e for e in errors)


def test_fallback_flags_bad_enum():
    comp = _base_component()
    comp["boundary"] = "sideways"
    errors = vd._fallback_validate(comp)
    assert any("boundary" in e for e in errors)


def test_valid_set_passes_in_fallback_mode(monkeypatch, capsys):
    """With pyyaml/jsonschema forced off, the stdlib parser + per-type fallback
    still pass the conformant set. Exercises the path that rots quietly on a
    machine without the deps."""
    monkeypatch.setattr(vd.core, "HAVE_YAML", False)
    monkeypatch.setattr(vd.core, "HAVE_JSONSCHEMA", False)
    code = run(VALID_DIR)
    out = capsys.readouterr().out
    assert code == 0, f"fallback mode failed the valid set\n{out}"
    assert "reduced (stdlib fallback) mode" in out


# ---------------------------------------------------------------------------
# Helpers that reach into the shared core for schema-level assertions.
# ---------------------------------------------------------------------------
def core_validator():
    return vd.core.make_validator(SCHEMA)


def _schema_errors(validator, data):
    return vd.core.validate_against_schema(data, validator)

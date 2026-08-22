"""Tests for the C4 view generator (STO-101).

Emission is asserted against committed golden files rather than regexes: a
golden file is what makes a layout change visible in review.
"""
import json
import os
import shutil

import pytest

import generate_c4 as g4

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "c4")


def case(name):
    root = os.path.join(FIXTURES, name)
    return (
        os.path.join(root, "design"),
        os.path.join(root, "model.json"),
        os.path.join(root, "expected"),
    )


def load_model(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_edges_resolve_through_the_provider():
    design_dir, _, _ = case("single-container")
    dset = g4.DesignSet.load(design_dir)
    assert dset.edges() == [
        ("CMP-001", "CMP-002", "IF-001"),
        ("CMP-001", "CMP-003", "IF-002"),
    ]


def test_asrs_are_read_from_drivers():
    design_dir, _, _ = case("single-container")
    dset = g4.DesignSet.load(design_dir)
    assert dset.asrs == ["FR-001", "NFR-001"]


def test_alias_rule_is_reversible():
    assert g4.alias_for("CMP-001", "internal") == "cmp_001"
    assert g4.alias_for("CMP-010", "external") == "ext_cmp_010"
    assert g4.alias_for("CMP-AUTH-004", "internal") == "cmp_auth_004"


def test_model_missing_a_component_is_rejected():
    design_dir, model_path, _ = case("single-container")
    dset = g4.DesignSet.load(design_dir)
    model = load_model(model_path)
    model["containers"][0]["components"] = ["CMP-001"]
    errors = g4.validate_model(model, dset)
    assert any("CMP-002" in e for e in errors)


def test_model_placing_a_component_twice_is_rejected():
    design_dir, model_path, _ = case("single-container")
    dset = g4.DesignSet.load(design_dir)
    model = load_model(model_path)
    model["containers"].append({
        "key": "second", "name": "Second", "technology": "Python",
        "description": "…", "components": ["CMP-002"],
    })
    errors = g4.validate_model(model, dset)
    assert any("CMP-002" in e and "two" in e.lower() for e in errors)


def test_model_placing_an_external_component_is_rejected():
    design_dir, model_path, _ = case("single-container")
    dset = g4.DesignSet.load(design_dir)
    model = load_model(model_path)
    model["containers"][0]["components"].append("CMP-003")
    errors = g4.validate_model(model, dset)
    assert any("CMP-003" in e for e in errors)


def test_context_view_matches_golden(tmp_path):
    design_dir, model_path, expected = case("single-container")
    out = tmp_path / "design"
    shutil.copytree(design_dir, out)
    code = g4.main([
        str(out), "--model", model_path, "--created-at", "2026-08-22",
    ])
    assert code == 0
    written = (out / "diagrams" / "DIA-001-system-context.md").read_text()
    golden = open(os.path.join(expected, "DIA-001-system-context.md")).read()
    assert written == golden


def test_generation_is_deterministic(tmp_path):
    design_dir, model_path, _ = case("single-container")
    runs = []
    for i in range(2):
        out = tmp_path / f"run{i}"
        shutil.copytree(design_dir, out)
        g4.main([str(out), "--model", model_path, "--created-at", "2026-08-22"])
        runs.append((out / "diagrams" / "DIA-001-system-context.md").read_text())
    assert runs[0] == runs[1]

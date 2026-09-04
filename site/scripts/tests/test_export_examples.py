"""Tests for the worked-example exporter (STO-250 pass 2).

These run against the real example sets under docs/requirements/examples/,
not fixtures. The sets are committed, regenerated deliberately by STO-219,
and are exactly what the site publishes — a fixture copy would be a second
thing to keep in step.
"""
import os

import export_examples as ee


def test_discovers_both_sets():
    assert ee.discover_sets() == ["gdpr", "tamagotchi"]


def test_loads_every_functional_requirement_in_id_order():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    assert len(artifacts) == 12
    assert [a.artifact_id for a in artifacts] == [
        f"FR-{n:03d}" for n in range(1, 13)
    ]


def test_artifact_carries_title_meta_and_body():
    first = ee.load_group("tamagotchi", "requirements", "functional")[0]
    assert first.artifact_id == "FR-001"
    assert first.title == "Persist pet state on stat change and app close"
    assert first.meta["type"] == "functional"
    assert first.meta["ears_pattern"] == "event"
    assert first.body.startswith("# FR-001")
    assert "## Acceptance Criteria" in first.body


def test_group_counts_match_the_committed_sets():
    expected = {
        ("tamagotchi", "requirements", "functional"): 12,
        ("tamagotchi", "requirements", "non-functional"): 9,
        ("tamagotchi", "requirements", "constraints"): 3,
        ("tamagotchi", "requirements", "business-rules"): 2,
        ("tamagotchi", "design", "components"): 19,
        ("tamagotchi", "design", "interfaces"): 31,
        ("tamagotchi", "design", "adr"): 7,
        ("tamagotchi", "design", "diagrams"): 4,
        ("gdpr", "requirements", "functional"): 3,
        ("gdpr", "requirements", "non-functional"): 15,
        ("gdpr", "requirements", "constraints"): 1,
        ("gdpr", "requirements", "business-rules"): 2,
    }
    for (set_name, stage, directory), count in expected.items():
        got = ee.load_group(set_name, stage, directory)
        assert len(got) == count, f"{set_name}/{stage}/{directory}"


def test_missing_group_is_empty_not_an_error():
    # gdpr has no design stage at all. That is a legal shape, not a failure.
    assert ee.load_group("gdpr", "design", "components") == []


def test_split_frontmatter_returns_the_body_only():
    text = "---\nid: FR-001\n---\n\n# FR-001 — Title\n\nProse.\n"
    assert ee.split_frontmatter(text) == "# FR-001 — Title\n\nProse.\n"


def test_split_frontmatter_leaves_a_file_without_frontmatter_alone():
    text = "# Assumptions\n\nProse.\n"
    assert ee.split_frontmatter(text) == text

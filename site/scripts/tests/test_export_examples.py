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


def test_demote_headings_shifts_every_level_by_one():
    body = "# Title\n\n## Section\n\n### Sub\n"
    assert ee.demote_headings(body) == "## Title\n\n### Section\n\n#### Sub\n"


def test_demote_headings_ignores_hashes_inside_fenced_blocks():
    # Gherkin and Mermaid blocks contain lines that start with '#'. Demoting
    # them would corrupt the fenced content, and a naive regex would.
    body = "# Title\n\n```gherkin\n# not a heading\n```\n\n## After\n"
    out = ee.demote_headings(body)
    assert "# not a heading" in out
    assert "## not a heading" not in out
    assert out.startswith("## Title")
    assert "### After" in out


def test_demote_headings_handles_an_unbalanced_fence():
    # An unterminated fence must not silently re-enable demotion below it.
    body = "# Title\n\n```\n# inside\n"
    out = ee.demote_headings(body)
    assert "# inside" in out
    assert "## inside" not in out


def test_index_maps_ids_to_anchored_urls():
    index = ee.build_index("tamagotchi")
    assert index["FR-001"] == (
        "/guide/examples/tamagotchi/requirements/functional/#fr-001"
    )
    assert index["CMP-001"] == (
        "/guide/examples/tamagotchi/design/components/#cmp-001"
    )


def test_rendered_page_anchors_every_artifact():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    index = ee.build_index("tamagotchi")
    page = ee.render_group(
        "tamagotchi", "requirements", "functional",
        "Functional requirements", artifacts, index,
    )
    assert "## FR-001 — Persist pet state on stat change and app close [#fr-001]" in page
    for artifact in artifacts:
        assert f"[#{artifact.artifact_id.lower()}]" in page


def test_rendered_page_links_resolvable_traces_and_leaves_the_rest_as_text():
    artifacts = ee.load_group("tamagotchi", "requirements", "functional")
    index = ee.build_index("tamagotchi")
    page = ee.render_group(
        "tamagotchi", "requirements", "functional",
        "Functional requirements", artifacts, index,
    )
    # FR-001 traces_from: [CON-002, BR-002] — both exist in this set.
    assert "[CON-002](/guide/examples/tamagotchi/requirements/constraints/#con-002)" in page
    # An ID absent from the set must render as plain text, never a dead link.
    assert "](/guide/examples/tamagotchi/requirements/functional/#fr-999)" not in page


def test_rendered_page_is_byte_identical_across_runs():
    args = ("tamagotchi", "design", "components", "Components")
    index = ee.build_index("tamagotchi")
    first = ee.render_group(*args, ee.load_group(*args[:3]), index)
    second = ee.render_group(*args, ee.load_group(*args[:3]), index)
    assert first == second


def test_check_passes_against_committed_output():
    # The gate's real contract: what is on disk equals what the exporter
    # produces right now.
    assert ee.main(["--check"]) == 0


def test_check_fails_when_a_page_is_stale(capsys):
    target = os.path.join(ee.OUT_DIR, "tamagotchi", "requirements", "functional.md")
    original = open(target, encoding="utf-8").read()
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original + "\nstale\n")
        assert ee.main(["--check"]) == 1
        assert "stale:" in capsys.readouterr().err
    finally:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original)
    assert ee.main(["--check"]) == 0


def test_check_orphan_guidance_is_specific_to_orphaned_pages(capsys):
    # An orphaned page needs a different remediation than ordinary drift:
    # regenerating does not delete anything, so the printed instruction must
    # say so — and must not show up for a page the generator still produces.
    orphan = os.path.join(ee.OUT_DIR, "tamagotchi", "requirements", "stray.md")
    try:
        with open(orphan, "w", encoding="utf-8") as handle:
            handle.write("stray\n")
        assert ee.main(["--check"]) == 1
        err = capsys.readouterr().err
        assert "(orphaned)" in err
        assert "delete any path marked (orphaned)" in err
    finally:
        if os.path.exists(orphan):
            os.remove(orphan)
    assert ee.main(["--check"]) == 0

    target = os.path.join(ee.OUT_DIR, "tamagotchi", "requirements", "functional.md")
    original = open(target, encoding="utf-8").read()
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original + "\nstale\n")
        assert ee.main(["--check"]) == 1
        err = capsys.readouterr().err
        assert "(orphaned)" not in err
        assert "delete any path marked (orphaned)" not in err
    finally:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original)
    assert ee.main(["--check"]) == 0


def test_project_artifact_pages_carry_the_prose_files():
    page = ee.render_project_artifacts("tamagotchi", "requirements")
    assert "## Glossary" in page
    assert "## Assumptions" in page
    assert "## Definition of done" in page


def test_gdpr_has_no_design_pages():
    assert not os.path.isdir(os.path.join(ee.OUT_DIR, "gdpr", "design"))


def test_link_ids_renders_unresolvable_ids_as_plain_text():
    index = {"FR-001": "/guide/examples/x/requirements/functional/#fr-001"}
    out = ee._link_ids(["FR-001", "FR-999"], index)
    assert out == "[FR-001](/guide/examples/x/requirements/functional/#fr-001), FR-999"

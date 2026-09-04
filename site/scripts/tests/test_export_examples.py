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


# ---------------------------------------------------------------------------
# Folder index pages (STO-250 pass 3)
# ---------------------------------------------------------------------------


def test_every_examples_subfolder_publishes_an_index_page():
    # Nextra resolves a folder's breadcrumb to that folder's own route, and
    # under examples/ every child of a set and of a stage is itself a folder.
    # Without an index page occupying the folder route the crumb points at a
    # directory with no page and 404s — which is exactly what shipped before
    # this test existed. Reordering _meta.js cannot substitute: there is no
    # child page to promote.
    pages = ee.build_pages()
    folders = set()
    for relative in pages:
        parts = relative.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            folders.add("/".join(parts[:depth]))
    assert folders  # the sweep below is meaningless if this is empty
    missing = sorted(f for f in folders if f"{f}/index.md" not in pages)
    assert missing == []


def test_index_pages_carry_the_generated_file_header():
    pages = ee.build_pages()
    index_pages = [p for p in pages if p.endswith("index.md")]
    assert len(index_pages) == 5  # 2 sets + 3 stages
    for relative in index_pages:
        assert pages[relative].startswith(
            "<!--\n  GENERATED FILE — do not edit.\n"
        ), relative
        assert "Regenerate: python3 site/scripts/export_examples.py" in (
            pages[relative]
        )


def test_meta_lists_the_index_first_so_the_breadcrumb_lands_on_it():
    pages = ee.build_pages()
    for relative in ("tamagotchi/_meta.js", "tamagotchi/design/_meta.js"):
        first = pages[relative].splitlines()[1]
        assert first == "  'index': 'Overview',", relative


def test_set_index_describes_the_set_and_links_every_stage():
    page = ee.build_pages()["tamagotchi/index.md"]
    assert "# Desktop tamagotchi" in page
    assert ee.SET_BLURBS["tamagotchi"] in page
    assert "](/guide/examples/tamagotchi/requirements/)" in page
    assert "](/guide/examples/tamagotchi/design/)" in page
    # gdpr has no design stage, so its index must not advertise one.
    gdpr = ee.build_pages()["gdpr/index.md"]
    assert "](/guide/examples/gdpr/requirements/)" in gdpr
    assert "/design/" not in gdpr


def test_set_index_counts_are_derived_from_the_loaded_artifacts():
    page = ee.build_pages()["tamagotchi/index.md"]
    design = [
        ee.load_group("tamagotchi", "design", d)
        for _s, d, _t in ee.GROUPS
        if _s == "design"
    ]
    total = sum(len(group) for group in design)
    assert f"{total} atomic artifacts" in page
    assert f"{len(design[0])} components" in page


def test_stage_index_lists_every_page_with_its_count():
    page = ee.build_pages()["gdpr/requirements/index.md"]
    assert "21 atomic artifacts published across 4 pages" in page
    assert (
        "- **[Constraints](/guide/examples/gdpr/requirements/constraints/)**"
        " — 1 constraint." in page
    )
    assert (
        "- **[Non-functional requirements]"
        "(/guide/examples/gdpr/requirements/non-functional/)**"
        " — 15 non-functional requirements." in page
    )
    # The project-artifacts page is advertised by the files actually present.
    assert "glossary, assumptions and definition of done" in page


def test_stage_index_project_gloss_follows_the_stage():
    page = ee.build_pages()["tamagotchi/design/index.md"]
    assert "architecture drivers and assumptions" in page


def test_check_detects_a_stale_index_page(capsys):
    target = os.path.join(ee.OUT_DIR, "tamagotchi", "design", "index.md")
    original = open(target, encoding="utf-8").read()
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original + "\nstale\n")
        assert ee.main(["--check"]) == 1
        assert "tamagotchi/design/index.md" in capsys.readouterr().err
    finally:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(original)
    assert ee.main(["--check"]) == 0


def test_check_sweeps_an_orphaned_index_page(capsys):
    # The orphan sweep is path-based, so it has to catch an index page the
    # generator does not produce just as it catches any other stray file.
    orphan = os.path.join(ee.OUT_DIR, "gdpr", "design")
    os.makedirs(orphan, exist_ok=True)
    path = os.path.join(orphan, "index.md")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("stray\n")
        assert ee.main(["--check"]) == 1
        err = capsys.readouterr().err
        assert "gdpr/design/index.md (orphaned)" in err
    finally:
        if os.path.exists(path):
            os.remove(path)
        if os.path.isdir(orphan):
            os.rmdir(orphan)
    assert ee.main(["--check"]) == 0


# ---------------------------------------------------------------------------
# Rendering details (STO-250 pass 3)
# ---------------------------------------------------------------------------


def test_count_phrase_singularises_only_a_count_of_one():
    assert ee.count_phrase(3, "Constraints") == "3 constraints"
    assert ee.count_phrase(1, "Constraints") == "1 constraint"
    assert ee.count_phrase(1, "Business rules") == "1 business rule"
    assert ee.count_phrase(0, "Constraints") == "0 constraints"


def test_count_phrase_keeps_an_acronym_capitalised():
    # The page's own H1 reads "C4 diagrams"; title.lower() two lines below it
    # produced "c4 diagrams".
    assert ee.count_phrase(4, "C4 diagrams") == "4 C4 diagrams"
    assert ee.count_phrase(1, "C4 diagrams") == "1 C4 diagram"


def test_rendered_group_intro_agrees_with_its_own_heading():
    artifacts = ee.load_group("tamagotchi", "design", "diagrams")
    page = ee.render_group(
        "tamagotchi", "design", "diagrams", "C4 diagrams", artifacts,
        ee.build_index("tamagotchi"),
    )
    assert "# C4 diagrams\n" in page
    assert "The 4 C4 diagrams from the `tamagotchi` worked example" in page
    assert "c4 diagrams" not in page


def test_meta_rows_declare_no_contract_level_interaction():
    # STO-216 moved interaction onto the operation; the design schema's
    # interface branch rejects a contract-level one through
    # unevaluatedProperties: false. A row for it could only ever render on a
    # schema-invalid artifact, publishing an illegal field as routine.
    assert "interaction" not in {key for key, _label in ee.META_ROWS}

"""Tests for the Definition of Done generator (STO-104)."""
import os

import pytest

import generate_dod as gd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
REQS_ONLY = os.path.join(FIXTURES, "reqs_only")


def generate(fixture_dir, tmp_path, **kwargs):
    """Run the CLI over a fixture tree; return (exit_code, document_text)."""
    out = os.path.join(str(tmp_path), "definition-of-done.md")
    argv = ["--out", out]
    for stage in ("requirements", "design", "qa"):
        stage_dir = os.path.join(fixture_dir, stage)
        if os.path.isdir(stage_dir):
            argv += [f"--{stage}", stage_dir]
    for key, value in kwargs.items():
        argv += [f"--{key.replace('_', '-')}", value]
    code = gd.main(argv)
    text = ""
    if os.path.isfile(out):
        with open(out, encoding="utf-8") as handle:
            text = handle.read()
    return code, text


def test_requirements_only_set_generates(tmp_path):
    code, text = generate(REQS_ONLY, tmp_path)
    assert code == 0
    assert text.startswith("# Definition of Done")


def test_header_names_the_stages_that_fed_it(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "requirements ✓" in text
    assert "design —" in text
    assert "qa —" in text


def test_title_flag_appears_when_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path, title="Order Cancellation")
    assert "**Project / feature:** Order Cancellation" in text


def test_title_line_omitted_when_not_given(tmp_path):
    _, text = generate(REQS_ONLY, tmp_path)
    assert "Project / feature" not in text


def test_missing_requirements_dir_is_usage_error(tmp_path):
    code = gd.main(["--requirements", str(tmp_path / "nope"),
                    "--out", str(tmp_path / "dod.md")])
    assert code == 2


def test_no_stages_at_all_is_usage_error(tmp_path):
    code = gd.main(["--out", str(tmp_path / "dod.md")])
    assert code == 2

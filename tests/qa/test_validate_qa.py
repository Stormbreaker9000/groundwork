"""Tests for the QA structural validator (STO-103)."""
import os

import pytest

import validate_qa as vq

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
SCHEMA = vq.default_schema_path()

INVALID_CASES = [
    "bad_id_pattern",
    "prefix_type_mismatch",
    "duplicate_id",
    "bad_test_level",
    "bad_enforcement",
    "missing_risk_rationale",
    "empty_traces_from",
    "unknown_field",
    "missing_strategy_artifact",
    "strategy_missing_heading",
]


def test_valid_fixture_passes():
    code = vq.main([os.path.join(FIXTURES, "valid")])
    assert code == 0


@pytest.mark.parametrize("case", INVALID_CASES)
def test_invalid_fixture_fails(case):
    code = vq.main([os.path.join(FIXTURES, "invalid", case)])
    assert code != 0, f"expected non-zero exit for fixture {case}"


def test_every_invalid_fixture_is_exercised():
    # A fixture directory nobody parametrizes is a rule nobody tests. This is
    # the guard that catches a fixture added without its case.
    on_disk = sorted(
        d for d in os.listdir(os.path.join(FIXTURES, "invalid"))
        if os.path.isdir(os.path.join(FIXTURES, "invalid", d))
    )
    assert on_disk == sorted(INVALID_CASES)


def test_strategy_companion_is_skipped_as_an_artifact():
    # qa-strategy.md and index.yaml sit beside the artifacts and are not
    # themselves artifacts; discovery must not try to parse them as one.
    found = vq.discover_files(os.path.join(FIXTURES, "valid"))
    assert all(os.path.basename(p).startswith("TS-") for p in found)
    assert found, "discovery returned nothing — the fixture set is not being read"


def test_prefix_to_type_is_the_single_id_authority():
    assert vq.PREFIX_TO_TYPE == {"TS": "test_strategy"}

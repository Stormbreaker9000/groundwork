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
    "bad_verification_mode",
    "missing_test_level_for_test_mode",
    "bad_enforcement",
    "missing_risk_rationale",
    "empty_traces_from",
    "unknown_field",
    "unknown_prefix",
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


def test_unknown_prefix_reports_the_cross_file_message():
    # Asserting the message, not the exit code: this artifact also violates the
    # schema's id pattern, so an exit-code assertion would pass without the
    # cross-file branch ever running. Only the message proves it ran.
    files, _ = vq.validate(
        os.path.join(FIXTURES, "invalid", "unknown_prefix"), SCHEMA
    )
    errors = [e for f in files for e in f.errors]
    assert any("is not one of" in e for e in errors), errors


def test_prefix_type_mismatch_reports_the_cross_file_message():
    # Same reasoning: type is a schema const, so a mismatched type is also a
    # schema violation. Only the message proves the cross-file branch ran.
    files, _ = vq.validate(
        os.path.join(FIXTURES, "invalid", "prefix_type_mismatch"), SCHEMA
    )
    errors = [e for f in files for e in f.errors]
    assert any("implies type" in e for e in errors), errors


# ---------------------------------------------------------------------------
# The stdlib fallback path (no jsonschema): verification_mode and the
# conditional test_level requirement (STO-307 D6, D7).
# ---------------------------------------------------------------------------
def _base_item():
    return {
        "id": "TS-001", "type": "test_strategy", "title": "x",
        "description": "x", "test_level": "unit", "risk_level": "medium",
        "risk_rationale": "x", "enforcement": "ci",
        "verification_mode": "test", "traces_from": ["FR-001"],
        "traces_to": {"tests": [], "code": []}, "status": "draft",
        "confidence": "high", "created_at": "2026-09-15",
    }


def test_fallback_accepts_a_valid_item():
    assert vq._fallback_validate(_base_item()) == []


def test_fallback_requires_verification_mode():
    item = _base_item()
    del item["verification_mode"]
    errors = vq._fallback_validate(item)
    assert any("verification_mode" in e for e in errors), errors


def test_fallback_flags_unknown_verification_mode():
    item = _base_item()
    item["verification_mode"] = "vibes"
    errors = vq._fallback_validate(item)
    assert any("verification_mode" in e for e in errors), errors


def test_fallback_requires_test_level_when_mode_is_test():
    item = _base_item()
    del item["test_level"]
    errors = vq._fallback_validate(item)
    assert any("test_level" in e for e in errors), errors


def test_fallback_allows_absent_test_level_for_a_non_test_mode():
    # A licence audit crosses no boundary and honestly has no level.
    item = _base_item()
    item["verification_mode"] = "inspection"
    del item["test_level"]
    assert vq._fallback_validate(item) == []


def test_fallback_allows_test_level_alongside_a_non_test_mode():
    # Optional, not forbidden (D7): an inspection that enumerates call sites
    # across two components is still about an integration boundary.
    item = _base_item()
    item["verification_mode"] = "inspection"
    item["test_level"] = "integration"
    assert vq._fallback_validate(item) == []

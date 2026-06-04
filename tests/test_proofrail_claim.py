"""Tests for ProofRail Bronze Claim Tool v0.1

Run with:
    python -m pytest tests/test_proofrail_claim.py
"""

import copy
import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Import the claim module from scripts/
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("proofrail_claim", SCRIPTS_DIR / "proofrail_claim.py")
proofrail_claim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proofrail_claim)

validate_claim = proofrail_claim.validate_claim
summarize_claim = proofrail_claim.summarize_claim
main = proofrail_claim.main

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "claims"


def _load_example(name):
    with open(EXAMPLES_DIR / name) as f:
        return yaml.safe_load(f)


@pytest.fixture
def composed_claim():
    return _load_example("bronze-composed-minimal.example.yaml")


@pytest.fixture
def native_claim():
    return _load_example("native-bronze-preview-minimal.example.yaml")


def _deep_delete(data, *keys):
    """Delete a key path from nested dicts.  keys are successive dict keys."""
    obj = data
    for k in keys[:-1]:
        obj = obj[k]
    del obj[keys[-1]]


# ---------------------------------------------------------------------------
# 1. Valid minimal composed claim passes
# ---------------------------------------------------------------------------

def test_valid_composed_claim_passes(composed_claim):
    errors, warnings, checks = validate_claim(composed_claim)
    assert not errors, f"Expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# 2. Valid native preview claim passes
# ---------------------------------------------------------------------------

def test_valid_native_claim_passes(native_claim):
    errors, warnings, checks = validate_claim(native_claim)
    assert not errors, f"Expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# 3. Missing proofrail_bronze_claim fails
# ---------------------------------------------------------------------------

def test_missing_root_key_fails():
    errors, warnings, checks = validate_claim({"some_other_key": {}})
    assert any("proofrail_bronze_claim" in e for e in errors)


def test_none_input_fails():
    errors, warnings, checks = validate_claim(None)
    assert any("proofrail_bronze_claim" in e for e in errors)


# ---------------------------------------------------------------------------
# 4. Missing protected_actuator_set fails
# ---------------------------------------------------------------------------

def test_missing_protected_actuator_set_fails(composed_claim):
    _deep_delete(composed_claim, "proofrail_bronze_claim", "protected_actuator_set")
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("protected_actuator_set" in e for e in errors)


# ---------------------------------------------------------------------------
# 5. Invalid claim_type fails
# ---------------------------------------------------------------------------

def test_invalid_claim_type_fails(composed_claim):
    composed_claim["proofrail_bronze_claim"]["claim_type"] = "gold_premium"
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("claim_type" in e for e in errors)


# ---------------------------------------------------------------------------
# 6. Missing declared_control_surfaces fails
# ---------------------------------------------------------------------------

def test_missing_declared_control_surfaces_fails(composed_claim):
    _deep_delete(composed_claim, "proofrail_bronze_claim", "declared_control_surfaces")
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("declared_control_surfaces" in e for e in errors)


def test_empty_declared_control_surfaces_fails(composed_claim):
    composed_claim["proofrail_bronze_claim"]["declared_control_surfaces"] = []
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("declared_control_surfaces" in e for e in errors)


# ---------------------------------------------------------------------------
# 7. Missing emergency_stop fails
# ---------------------------------------------------------------------------

def test_missing_emergency_stop_fails(composed_claim):
    _deep_delete(composed_claim, "proofrail_bronze_claim", "emergency_stop")
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("emergency_stop" in e for e in errors)


# ---------------------------------------------------------------------------
# 8. Missing bypass_prevention fails
# ---------------------------------------------------------------------------

def test_missing_bypass_prevention_fails(composed_claim):
    _deep_delete(composed_claim, "proofrail_bronze_claim", "bypass_prevention")
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("bypass_prevention" in e for e in errors)


# ---------------------------------------------------------------------------
# 9. Placeholder / invalid sha256 hash emits warning
# ---------------------------------------------------------------------------

def test_placeholder_hash_warns(composed_claim):
    # The example already uses "sha256:example" which is a placeholder
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("placeholder" in w for w in warnings)


def test_invalid_hash_prefix_warns(composed_claim):
    composed_claim["proofrail_bronze_claim"]["protected_actuator_set"]["hash"] = "md5:abc123"
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("sha256:" in w for w in warnings)
    # Should be a warning, not an error, in non-strict mode
    assert not any("sha256:" in e and "strict" not in e for e in errors)


def test_invalid_hash_prefix_fails_strict(composed_claim):
    composed_claim["proofrail_bronze_claim"]["protected_actuator_set"]["hash"] = "md5:abc123"
    errors, warnings, checks = validate_claim(composed_claim, strict=True)
    assert any("sha256:" in e for e in errors)


# ---------------------------------------------------------------------------
# 10. File existence checks warn when evidence files missing
# ---------------------------------------------------------------------------

def test_evidence_file_missing_warns(composed_claim, tmp_path):
    # Use an empty directory as evidence root; all referenced files will be missing
    errors, warnings, checks = validate_claim(
        composed_claim, evidence_root=str(tmp_path)
    )
    assert any("Evidence file not found" in w for w in warnings)
    # Should be warnings, not errors, in non-strict mode
    assert not any("Evidence file not found" in e for e in errors)


# ---------------------------------------------------------------------------
# 11. Strict mode promotes evidence-file warnings to failures
# ---------------------------------------------------------------------------

def test_strict_evidence_files_fail(composed_claim, tmp_path):
    errors, warnings, checks = validate_claim(
        composed_claim, strict=True, evidence_root=str(tmp_path)
    )
    assert any("Evidence file not found" in e for e in errors)


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------

def test_invalid_claim_status_fails(composed_claim):
    composed_claim["proofrail_bronze_claim"]["claim_status"] = "approved"
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("claim_status" in e for e in errors)


def test_invalid_validation_result_fails(composed_claim):
    composed_claim["proofrail_bronze_claim"]["validation"]["validation_result"] = "certified"
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("validation_result" in e for e in errors)


def test_bypass_design_level_warns(composed_claim):
    composed_claim["proofrail_bronze_claim"]["bypass_prevention"]["claim_level"] = "design"
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("design" in w for w in warnings)


def test_rate_limit_not_implemented_warns(composed_claim):
    composed_claim["proofrail_bronze_claim"]["rate_limit_or_circuit_breaker"]["implemented"] = False
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("rate_limit_or_circuit_breaker" in w and "not true" in w for w in warnings)


def test_emergency_stop_not_implemented_warns(composed_claim):
    composed_claim["proofrail_bronze_claim"]["emergency_stop"]["implemented"] = False
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("emergency_stop" in w and "not true" in w for w in warnings)


def test_summarize_produces_output(composed_claim):
    output = summarize_claim(composed_claim)
    assert "bronze-composed-demo-20260601-001" in output
    assert "composed_bronze" in output


def test_init_composed(tmp_path):
    out_file = str(tmp_path / "claim.yaml")
    rc = main(["init", "--profile", "bronze", "--type", "composed", "--out", out_file])
    assert rc == 0
    assert Path(out_file).exists()
    with open(out_file) as f:
        data = yaml.safe_load(f)
    assert data["proofrail_bronze_claim"]["claim_type"] == "composed_bronze"


def test_init_native(tmp_path):
    out_file = str(tmp_path / "claim.yaml")
    rc = main(["init", "--profile", "bronze", "--type", "native", "--out", out_file])
    assert rc == 0
    with open(out_file) as f:
        data = yaml.safe_load(f)
    assert data["proofrail_bronze_claim"]["claim_type"] == "native_bronze_preview"


def test_validate_cli_pass(tmp_path):
    """End-to-end: init -> validate should pass (with warnings)."""
    out_file = str(tmp_path / "claim.yaml")
    main(["init", "--profile", "bronze", "--type", "composed", "--out", out_file])
    rc = main(["validate", out_file])
    assert rc == 0


def test_validate_json_output(composed_claim, tmp_path):
    """Validate with --format json produces valid JSON."""
    claim_path = tmp_path / "claim.yaml"
    with open(claim_path, "w") as f:
        yaml.dump(composed_claim, f)

    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["validate", str(claim_path), "--format", "json"])
    output = buf.getvalue()
    data = __import__("json").loads(output)
    assert "result" in data
    assert "errors" in data
    assert "warnings" in data
    assert "checks" in data


def test_performance_fail_warns_normal(composed_claim):
    composed_claim["proofrail_bronze_claim"]["performance_evidence"]["results"] = {
        "p95_added_latency_ms": 150,
        "error_count": 0,
        "pass": False,
    }
    errors, warnings, checks = validate_claim(composed_claim)
    assert any("performance_evidence.results.pass is false" in w for w in warnings)
    assert not any("performance_evidence.results.pass" in e for e in errors)


def test_performance_fail_errors_strict(composed_claim):
    composed_claim["proofrail_bronze_claim"]["performance_evidence"]["results"] = {
        "p95_added_latency_ms": 150,
        "error_count": 0,
        "pass": False,
    }
    errors, warnings, checks = validate_claim(composed_claim, strict=True)
    assert any("performance_evidence.results.pass is false" in e for e in errors)

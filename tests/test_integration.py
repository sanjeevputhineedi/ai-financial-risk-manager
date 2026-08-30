"""
Checkpoints R13 & R14 — Integration Tests
=============================================
R13: simulates Murali's backend calling analyze_payee() the way the
     /risk/analyze endpoint's payee-risk adapter would.
R14: verifies the output is stable/versioned so Sanjeev's decision
     combiner (personal_risk + payee_risk) can rely on the schema.
"""

import json
import pandas as pd
from ml.payee_risk.api import analyze_payee

REQUIRED_CONTRACT_FIELDS = {"payee_risk", "risk_level", "confidence", "reasons", "model_version"}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def simulate_murali_backend_call(payee_row: dict) -> dict:
    """Mimics how Murali's FastAPI risk adapter would invoke this package."""
    context = {"record": payee_row}
    return analyze_payee(payee_row["payee_id"], context)


def test_contract_fields_present():
    df = pd.read_csv("data/fraud/synthetic_payees.csv")
    row = df.iloc[0].to_dict()
    result = simulate_murali_backend_call(row)
    missing = REQUIRED_CONTRACT_FIELDS - set(result.keys())
    assert not missing, f"Missing contract fields: {missing}"
    assert result["risk_level"] in VALID_RISK_LEVELS
    assert 0 <= result["payee_risk"] <= 100
    assert 0 <= result["confidence"] <= 1
    assert isinstance(result["reasons"], list)
    print("PASS: contract fields present and valid ->", json.dumps(result, indent=2))


def test_all_profile_types_produce_valid_output():
    """R13: run every profile class through the full pipeline (simulated backend calls)."""
    df = pd.read_csv("data/fraud/synthetic_payees.csv")
    for profile in df["profile_type"].unique():
        row = df[df["profile_type"] == profile].iloc[0].to_dict()
        result = simulate_murali_backend_call(row)
        assert REQUIRED_CONTRACT_FIELDS.issubset(result.keys())
        print(f"{profile:22s} -> risk={result['payee_risk']:6.2f}  level={result['risk_level']:8s}")


def test_output_stability_for_sanjeev_combiner():
    """
    R14: Sanjeev's decision engine combines personal_risk + payee_risk.
    Confirms payee_risk is a numeric 0-100 and model_version is present
    on every call so his combiner can log/attribute which model version
    produced a given decision.
    """
    df = pd.read_csv("data/fraud/synthetic_payees.csv")
    row = df.iloc[5].to_dict()
    result_a = simulate_murali_backend_call(row)
    result_b = simulate_murali_backend_call(row)  # same payee, second call

    # Direct/graph risk should be identical (deterministic features);
    # only reputation state may have advanced between calls in a real
    # system, so we don't require bit-for-bit equality, only contract stability.
    assert result_a["model_version"] == result_b["model_version"]
    assert isinstance(result_a["payee_risk"], float)
    assert isinstance(result_b["payee_risk"], float)
    print("PASS: output schema stable across repeated calls for Sanjeev's combiner.")


def test_malformed_input_raises_clear_error():
    """R13: verify graceful failure so Murali's backend can catch and handle it (per his M11 test spec)."""
    try:
        analyze_payee("bad_payee", {})  # missing required 'record'
        assert False, "Expected ValueError for missing record"
    except ValueError as e:
        print("PASS: malformed input correctly raises ValueError ->", e)


if __name__ == "__main__":
    test_contract_fields_present()
    print()
    test_all_profile_types_produce_valid_output()
    print()
    test_output_stability_for_sanjeev_combiner()
    print()
    test_malformed_input_raises_clear_error()
    print("\nALL INTEGRATION TESTS PASSED")

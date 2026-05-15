"""Step_5 — Acceptance test case generation.

Generates api_tests and e2e_tests from FEAT.AC + API endpoints + prototype.
Truth source: ADR-056 §7.3 step_5.
"""

from __future__ import annotations

from typing import Any


def generate_acceptance_tests(
    feats: list[Any],
    apis: list[Any],
    uis: list[Any],
    design_package: dict[str, Any],
) -> dict[str, Any]:
    """Generate acceptance test cases from frozen SSOT chain.

    Returns dict with keys:
      - api_tests: list of API-level test cases
      - e2e_tests: list of E2E test cases
      - coverage_map: dict mapping AC id → list of test ids
      - total_ac: int
      - covered_ac: int
    """
    api_tests: list[dict[str, Any]] = []
    e2e_tests: list[dict[str, Any]] = []
    coverage_map: dict[str, list[str]] = {}

    # Build endpoint lookup from API objects
    endpoints: list[dict[str, Any]] = []
    for api in apis:
        eps = getattr(api, "endpoints", [])
        if isinstance(eps, list):
            endpoints.extend(eps)

    # Generate API tests: each endpoint + matching AC
    for ep_idx, ep in enumerate(endpoints):
        method = ep.get("方法", ep.get("method", "GET"))
        path = ep.get("路径", ep.get("path", "")).strip("`")
        purpose = ep.get("说明", ep.get("purpose", ""))
        test_id = f"API-T{ep_idx + 1:03d}"
        api_tests.append({
            "test_id": test_id,
            "type": "api",
            "method": method,
            "path": path,
            "purpose": purpose,
            "assertions": [
                f"Status code matches expected for {method} {path}",
                "Response schema valid",
            ],
        })

    # Generate E2E tests from FEAT acceptance criteria
    ac_counter = 0
    for feat in feats:
        ac_list = getattr(feat, "acceptance_criteria", [])
        feat_id = getattr(feat, "feat_id", "UNKNOWN")
        for ac in ac_list:
            ac_counter += 1
            ac_key = f"AC-{ac_counter:03d}"
            test_id = f"E2E-T{ac_counter:03d}"
            e2e_tests.append({
                "test_id": test_id,
                "type": "e2e",
                "feat_ref": feat_id,
                "ac": ac,
                "assertions": [
                    "User can complete the full happy path",
                    "System state changes match AC expectation",
                ],
            })
            coverage_map[ac_key] = [test_id]

    # Map API tests to coverage_map for endpoints that match AC keywords
    for api_test in api_tests:
        matching_acs: list[str] = []
        path_lower = api_test["path"].lower()
        for ac_key, test_ids in coverage_map.items():
            ac_text = ""
            for e2e in e2e_tests:
                if e2e["test_id"] in test_ids:
                    ac_text = e2e.get("ac", "")
                    break
            if any(kw in ac_text.lower() for kw in path_lower.split("/") if len(kw) > 3):
                matching_acs.append(ac_key)
        if matching_acs:
            for ac_key in matching_acs:
                coverage_map.setdefault(ac_key, []).append(api_test["test_id"])

    total_ac = ac_counter
    covered_ac = total_ac  # Simplification: every AC gets at least one E2E test

    return {
        "api_tests": api_tests,
        "e2e_tests": e2e_tests,
        "coverage_map": coverage_map,
        "total_ac": total_ac,
        "covered_ac": covered_ac,
    }

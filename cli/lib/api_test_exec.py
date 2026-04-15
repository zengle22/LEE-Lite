"""API test execution module.

Runs generated pytest scripts via subprocess, parses junitxml results,
validates evidence YAML files against spec.evidence_required, and
atomically updates the coverage manifest.

Code-driven entry point for ll-qa-api-test-exec skill.
"""

from __future__ import annotations

import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.qa_manifest_backfill import backfill_manifest
from cli.lib.qa_schemas import validate_evidence, validate_spec


def run_api_test_exec(
    spec_path: str,
    test_dir: str,
    manifest_path: str,
    evidence_dir: str,
    run_id: str,
    base_url: str = "",
) -> dict[str, Any]:
    """Execute generated pytest tests, collect evidence, backfill manifest.

    Args:
        spec_path: Path to api-test-spec YAML (for evidence_required validation)
        test_dir: Directory containing generated pytest .py files
        manifest_path: Path to api-coverage-manifest.yaml
        evidence_dir: Directory for evidence output
        run_id: Unique execution run identifier
        base_url: API base URL for test execution (optional)

    Returns:
        Summary dict with total, passed, failed, error counts, evidence_dir,
        manifest_path, and per-case results.
    """
    spec_p = Path(spec_path)
    test_p = Path(test_dir)
    manifest_p = Path(manifest_path)
    evidence_p = Path(evidence_dir)

    # Step 1: Load spec YAML to get case_id, coverage_id, evidence_required
    with open(spec_p, encoding="utf-8") as f:
        raw_spec = yaml.safe_load(f) or {}

    spec = validate_spec(raw_spec.get("api_test_spec", raw_spec))
    coverage_id = spec.coverage_id
    evidence_required = list(spec.evidence_required)

    # Step 2: Set environment variables for generated tests
    env = os.environ.copy()
    env["EVIDENCE_DIR"] = str(evidence_p)
    env["EVIDENCE_RUN_ID"] = run_id
    if base_url:
        env["BASE_URL"] = base_url

    # Step 3: Run pytest via subprocess
    junitxml_path = evidence_p / "results.xml"
    result = subprocess.run(
        [
            "pytest",
            str(test_p),
            "--junitxml",
            str(junitxml_path),
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # pytest returns non-zero on test failures — this is expected, not an error
    # Only treat it as a real error if pytest itself crashed (returncode >= 4)
    if result.returncode >= 4:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "error": 1,
            "error_msg": result.stderr.strip(),
            "evidence_dir": str(evidence_p),
            "manifest_path": str(manifest_p),
            "manifest_updated": False,
            "run_id": run_id,
            "results": [],
        }

    # Step 4: Parse junitxml to get per-case results
    case_results = _parse_junitxml(junitxml_path)

    # Step 5: For each test case, validate evidence
    results: list[dict[str, Any]] = []
    total = 0
    passed = 0
    failed = 0
    error_count = 0

    for case_name, case_status in case_results:
        total += 1

        # Look for evidence file
        evidence_file = evidence_p / f"{coverage_id}.evidence.yaml"
        evidence_path = ""
        case_passed = case_status == "passed"

        if evidence_file.exists():
            evidence_path = str(evidence_file.relative_to(evidence_p))
            # Validate evidence file
            try:
                with open(evidence_file, encoding="utf-8") as f:
                    ev_data = yaml.safe_load(f) or {}
                record = ev_data.get("evidence_record", ev_data)
                validate_evidence(record)
                # Check all spec.evidence_required items are present
                ev_evidence = record.get("evidence", {})
                missing = [
                    item for item in evidence_required if item not in ev_evidence
                ]
                if missing:
                    case_passed = False
            except Exception:
                case_passed = False
        else:
            # No evidence file found — mark as failed
            case_passed = False

        if case_passed:
            passed += 1
        else:
            if case_status == "error":
                error_count += 1
            else:
                failed += 1

        results.append(
            {
                "coverage_id": coverage_id,
                "case_id": case_name,
                "passed": case_passed,
                "evidence_path": evidence_path,
            }
        )

    # Step 6: Call backfill_manifest
    manifest_updated = False
    try:
        backfill_result = backfill_manifest(manifest_p, results, run_id)
        manifest_updated = True
    except Exception as e:
        # Log error but don't crash — evidence was still collected
        results.append({"error": f"manifest backfill failed: {e}"})

    # Step 7: Return summary
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "error": error_count,
        "evidence_dir": str(evidence_p),
        "manifest_path": str(manifest_p),
        "manifest_updated": manifest_updated,
        "run_id": run_id,
        "results": results,
    }


def _parse_junitxml(junitxml_path: Path) -> list[tuple[str, str]]:
    """Parse junitxml results.xml and return list of (case_name, status).

    Status is one of: 'passed', 'failed', 'error'.
    """
    if not junitxml_path.exists():
        return []

    tree = ET.parse(str(junitxml_path))
    root = tree.getroot()

    cases: list[tuple[str, str]] = []

    for testsuite in root.findall(".//testsuite"):
        for testcase in testsuite.findall("testcase"):
            name = testcase.get("name", "unknown")
            classname = testcase.get("classname", "")
            full_name = f"{classname}.{name}" if classname else name

            # Check for failure or error child elements
            failure = testcase.find("failure")
            error = testcase.find("error")

            if failure is not None:
                status = "failed"
            elif error is not None:
                status = "error"
            else:
                status = "passed"

            cases.append((full_name, status))

    return cases

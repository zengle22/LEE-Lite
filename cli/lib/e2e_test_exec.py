"""E2E test execution module.

Runs generated Playwright .spec.ts scripts via subprocess, parses Playwright
JSON report results, validates evidence YAML files against spec.evidence_required,
and atomically updates the coverage manifest.

Code-driven entry point for ll-qa-e2e-test-exec skill.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.qa_manifest_backfill import backfill_manifest
from cli.lib.qa_schemas import validate_e2e_spec, validate_evidence
from cli.lib.test_exec_playwright import ensure_playwright_project


def run_e2e_test_exec(
    spec_path: str,
    test_dir: str,
    manifest_path: str,
    evidence_dir: str,
    run_id: str,
    target_url: str = "",
) -> dict[str, Any]:
    """Execute generated Playwright tests, collect evidence, backfill manifest.

    Args:
        spec_path: Path to e2e-journey-spec YAML (for evidence_required validation)
        test_dir: Directory containing generated Playwright .spec.ts files
        manifest_path: Path to api-coverage-manifest.yaml
        evidence_dir: Directory for evidence output
        run_id: Unique execution run identifier
        target_url: Browser target URL for test execution (optional)

    Returns:
        Summary dict with total, passed, failed, error counts, evidence_dir,
        manifest_path, and per-case results.
    """
    spec_p = Path(spec_path)
    test_p = Path(test_dir)
    manifest_p = Path(manifest_path)
    evidence_p = Path(evidence_dir)

    # Step 1: Load E2E spec YAML to get case_id, coverage_id, evidence_required
    with open(spec_p, encoding="utf-8") as f:
        raw_spec = yaml.safe_load(f) or {}

    spec = validate_e2e_spec(raw_spec.get("e2e_journey_spec", raw_spec))
    coverage_id = spec.coverage_id
    evidence_required = list(spec.evidence_required)

    # Step 2: Ensure Playwright project exists
    pw_root = evidence_p.parent
    ensure_playwright_project(pw_root, {"TARGET_URL": target_url, "npm_command": "npm install --no-fund --no-audit"})

    # Step 3: Copy generated .spec.ts files into Playwright testDir
    test_dir_path = Path(test_dir)
    pw_tests_dir = pw_root / "e2e"
    pw_tests_dir.mkdir(parents=True, exist_ok=True)
    for spec_file in test_dir_path.glob("*.spec.ts"):
        shutil.copy2(spec_file, pw_tests_dir / spec_file.name)

    # Step 4: Run npx playwright test via subprocess with JSON reporter
    report_path = evidence_p / "playwright-report.json"
    output_dir = evidence_p / "playwright-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "EVIDENCE_DIR": str(evidence_p),
        "EVIDENCE_RUN_ID": run_id,
    }
    if target_url:
        env["TARGET_URL"] = target_url

    result = subprocess.run(
        [
            "npx", "playwright", "test",
            "--reporter=json",
            f"--reporter-filename={report_path.name}",
            "--output", str(output_dir),
        ],
        cwd=str(pw_root),
        capture_output=True,
        text=True,
        env=env,
    )
    # Playwright returns 0 if all pass, 1 if any fail — both are expected outcomes

    # Step 5: Parse Playwright JSON report
    case_results = _parse_playwright_report(report_path)

    # Step 6: For each test case, validate evidence
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

    # Step 7: Call backfill_manifest
    manifest_updated = False
    try:
        backfill_result = backfill_manifest(manifest_p, results, run_id)
        manifest_updated = True
    except Exception as e:
        # Log error but don't crash — evidence was still collected
        results.append({"error": f"manifest backfill failed: {e}"})

    # Step 8: Return summary
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


def _parse_playwright_report(report_path: Path) -> list[tuple[str, str]]:
    """Parse Playwright JSON report and return list of (case_name, status).

    Status is one of: 'passed', 'failed', 'error'.
    """
    if not report_path.exists():
        return []

    with open(report_path, encoding="utf-8") as f:
        report = json.loads(f.read())

    cases: list[tuple[str, str]] = []

    for suite in report.get("suites", []):
        for spec in _flatten_specs(suite):
            title = spec.get("title", "")
            tests = spec.get("tests", [])
            test_item = tests[-1] if tests else {}
            pw_results = test_item.get("results", [])
            last_result = pw_results[-1] if pw_results else {}
            status = last_result.get("status", test_item.get("status", "failed"))

            # Map Playwright status to our status
            if status == "passed":
                case_status = "passed"
            elif status in ("failed", "timedOut"):
                case_status = "failed"
            elif status == "interrupted":
                case_status = "error"
            else:
                case_status = "failed"

            cases.append((title, case_status))

    return cases


def _flatten_specs(suite: dict[str, Any]) -> list[dict[str, Any]]:
    """Recursively flatten nested Playwright suites to extract all specs."""
    items = list(suite.get("specs", []))
    for nested in suite.get("suites", []):
        items.extend(_flatten_specs(nested))
    return items

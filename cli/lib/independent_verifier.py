"""independent_verifier — ADR-054 Phase 3 P0 module.

Truth source: ADR-054 §3 Phase 3 + locked decisions D-01 through D-05.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.gate_schema import GateVerdict


# ---------------------------------------------------------------------------
# Configuration (defaults, can be overridden per invocation)
# ---------------------------------------------------------------------------

MAIN_FLOW_COVERAGE_TARGET = 1.0      # 100% — D-01
MAIN_FLOW_FAILURE_TOLERANCE = 0       # D-01
NONCORE_FLOW_COVERAGE_TARGET = 0.80   # 80% — D-02
NONCORE_FLOW_FAILURE_TOLERANCE = 5    # D-02

MAIN_SCENARIO_TYPES = {"main"}
NONCORE_SCENARIO_TYPES = {"exception", "branch", "retry", "state"}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FlowMetrics:
    """Metrics for a single flow category (main or non-core)."""
    coverage: float  # ratio 0.0 to 1.0
    failures: int
    status: GateVerdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage": round(self.coverage * 100),  # store as percentage
            "failures": self.failures,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class VerdictReport:
    """Independent verification report — verdict + confidence for a test run."""
    run_id: str
    generated_at: str
    verdict: GateVerdict
    confidence: float  # 0.00 to 1.00
    details: dict[str, Any]  # serialized flow metrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "verdict": self.verdict.value,
            "confidence": round(self.confidence, 2),
            "details": self.details,
        }

    def to_yaml_dict(self) -> dict[str, Any]:
        return {
            "verification_report": self.to_dict()
        }


# ---------------------------------------------------------------------------
# Verdict determination
# ---------------------------------------------------------------------------

def _determine_flow_verdict(
    coverage: float,
    failures: int,
    is_main: bool,
) -> GateVerdict:
    """Determine flow verdict based on coverage + failure thresholds.

    Per D-01: main flow requires 100% coverage, 0 failures.
    Per D-02: non-core flow requires >=80% coverage, <=5 failures.
    """
    if is_main:
        target = MAIN_FLOW_COVERAGE_TARGET
        tolerance = MAIN_FLOW_FAILURE_TOLERANCE
    else:
        target = NONCORE_FLOW_COVERAGE_TARGET
        tolerance = NONCORE_FLOW_FAILURE_TOLERANCE

    if coverage >= target and failures <= tolerance:
        return GateVerdict.PASS
    return GateVerdict.FAIL


def _compute_confidence(manifest_items: list[dict]) -> float:
    """Compute confidence as ratio of executed items with evidence_refs.

    Per D-04: confidence = count(executed_items with evidence_refs) / count(executed_items)
    """
    executed = [
        item for item in manifest_items
        if item.get("lifecycle_status") in ("passed", "failed", "blocked")
    ]
    if not executed:
        return 0.0
    with_refs = sum(1 for item in executed if item.get("evidence_refs"))
    return with_refs / len(executed)


def _categorize_items(manifest_items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split manifest items into main_flow and non_core_flow based on scenario_type.

    Per D-03: scenario_type=main → main; exception/branch/retry/state → non-core
    Unknown scenario_type defaults to non-core with a log warning.
    """
    main: list[dict] = []
    non_core: list[dict] = []
    for item in manifest_items:
        stype = item.get("scenario_type", "main")
        if stype in MAIN_SCENARIO_TYPES:
            main.append(item)
        elif stype in NONCORE_SCENARIO_TYPES:
            non_core.append(item)
        else:
            # Unknown scenario_type defaults to non_core per safety
            non_core.append(item)
    return main, non_core


def _compute_flow_metrics(items: list[dict], is_main: bool) -> FlowMetrics:
    """Compute coverage and failures for a flow category.

    Empty item list is treated as 100% coverage (no items to execute).
    Only actual coverage failures or excessive failures count as flow fail.
    """
    total = len(items)
    if total == 0:
        # No items in this category — treat as fully covered (no gap)
        coverage = 1.0
    else:
        executed = [
            i for i in items
            if i.get("lifecycle_status") in ("passed", "failed", "blocked")
        ]
        coverage = len(executed) / total

    failures = sum(
        1 for i in items
        if i.get("lifecycle_status") == "failed"
    )

    status = _determine_flow_verdict(coverage, failures, is_main)
    return FlowMetrics(coverage=coverage, failures=failures, status=status)


# ---------------------------------------------------------------------------
# Main verify() function
# ---------------------------------------------------------------------------

def verify(
    manifest_items: list[dict],
    run_id: str | None = None,
) -> VerdictReport:
    """Produce a VerdictReport from executed manifest items.

    Args:
        manifest_items: List of manifest item dicts with lifecycle_status,
                       scenario_type, and evidence_refs fields.
        run_id: Optional run identifier. Auto-generated if not provided.

    Returns:
        VerdictReport with verdict, confidence, and flow-level details.

    Per D-05: verdict is determined by coverage+failures rules, NOT confidence.
    Confidence is computed per D-04 and included as a reference metric.
    """
    if run_id is None:
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    generated_at = datetime.now(timezone.utc).isoformat()

    main_items, non_core_items = _categorize_items(manifest_items)

    main_metrics = _compute_flow_metrics(main_items, is_main=True)
    non_core_metrics = _compute_flow_metrics(non_core_items, is_main=False)

    confidence = _compute_confidence(manifest_items)

    # Overall verdict: fail if ANY flow fails
    if main_metrics.status == GateVerdict.FAIL or non_core_metrics.status == GateVerdict.FAIL:
        overall_verdict = GateVerdict.FAIL
    else:
        overall_verdict = GateVerdict.PASS

    details = {
        "main_flow": main_metrics.to_dict(),
        "non_core_flow": non_core_metrics.to_dict(),
    }

    return VerdictReport(
        run_id=run_id,
        generated_at=generated_at,
        verdict=overall_verdict,
        confidence=confidence,
        details=details,
    )


def verify_from_manifest_file(manifest_path: str | Path) -> VerdictReport:
    """Load manifest from YAML and produce VerdictReport.

    Args:
        manifest_path: Path to api-coverage-manifest.yaml or similar.

    Returns:
        VerdictReport.
    """
    p = Path(manifest_path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    items = data.get("items", [])
    run_id = data.get("run_id")

    return verify(items, run_id=run_id)


def write_report(report: VerdictReport, output_path: str | Path) -> None:
    """Write VerdictReport to YAML file.

    Args:
        report: VerdictReport from verify()
        output_path: Destination path.
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(report.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for independent_verifier.

    Usage:
        python -m cli.lib.independent_verifier <manifest.yaml> [output.yaml]
        python -m cli.lib.independent_verifier --help
    """
    import sys
    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("Usage: python -m cli.lib.independent_verifier <manifest.yaml> [output.yaml]")
        sys.exit(0)

    manifest_path = Path(args[0])
    output_path = Path(args[1]) if len(args) > 1 else manifest_path.parent / "verification_report.yaml"

    report = verify_from_manifest_file(manifest_path)
    write_report(report, output_path)
    print(f"Verdict: {report.verdict.value}")
    print(f"Confidence: {report.confidence:.2f}")
    print(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
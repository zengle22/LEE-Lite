"""settlement_integration — bridge between independent_verifier and ll-qa-settlement.

Truth source: ADR-054 Phase 3 + D-06/D-07/D-08.
Integrates independent_verifier.verdict into settlement report generation.

Data flow: independent_verifier.verdict → ll-qa-settlement → settlement report
Settlement report contains verdict + confidence from independent_verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.gate_schema import GateVerdict
from cli.lib.independent_verifier import (
    VerdictReport,
    verify,
    verify_from_manifest_file,
)
from cli.lib.qa_schemas import (
    GapEntry,
    WaiverEntry,
)


@dataclass
class SettlementInput:
    """Input contract for settlement generation.

    Attributes:
        manifest_path: Path to api-coverage-manifest.yaml or e2e-coverage-manifest.yaml
        verdict_report: Optional VerdictReport from independent_verifier.
                       If not provided, computed from manifest.
        chain: "api" or "e2e"
    """
    manifest_path: str | Path
    verdict_report: VerdictReport | None = None
    chain: str = "api"  # "api" | "e2e"


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load manifest YAML and return parsed dict."""
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _compute_statistics(items: list[dict]) -> dict[str, Any]:
    """Compute settlement statistics from manifest items.

    Per ll-qa-settlement/SKILL.md:
    - total: all items
    - designed: items with lifecycle_status=designed (not yet executed)
    - executed: items with lifecycle_status in (passed, failed, blocked)
    - passed: items with lifecycle_status=passed
    - failed: items with lifecycle_status=failed
    - blocked: items with lifecycle_status=blocked
    - uncovered: designed items never executed
    - cut: items with lifecycle_status=cut
    - obsolete: items with obsolete=true
    - pass_rate: passed / executed
    """
    total = len(items)
    designed = sum(1 for i in items if i.get("lifecycle_status") == "designed")
    executed = sum(
        1 for i in items
        if i.get("lifecycle_status") in ("passed", "failed", "blocked")
    )
    passed = sum(1 for i in items if i.get("lifecycle_status") == "passed")
    failed = sum(1 for i in items if i.get("lifecycle_status") == "failed")
    blocked = sum(1 for i in items if i.get("lifecycle_status") == "blocked")
    uncovered = designed  # designed but never executed
    cut = sum(1 for i in items if i.get("lifecycle_status") == "cut")
    obsolete = sum(1 for i in items if i.get("obsolete", False))

    pass_rate = (passed / executed) if executed > 0 else 0.0

    return {
        "total": total,
        "designed": designed,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "uncovered": uncovered,
        "cut": cut,
        "obsolete": obsolete,
        "pass_rate": round(pass_rate, 3),
    }


def _build_gap_list(items: list[dict]) -> list[GapEntry]:
    """Build gap list from failed/blocked/uncovered items.

    Per ll-qa-settlement/SKILL.md:
    Gap list includes all items where lifecycle_status is failed, blocked, or uncovered.
    """
    gaps = []
    for item in items:
        status = item.get("lifecycle_status", "")
        if status in ("failed", "blocked", "designed"):
            gaps.append(GapEntry(
                coverage_id=item.get("coverage_id", ""),
                capability=item.get("capability", ""),
                lifecycle_status=status,
                failure_reason=item.get("failure_reason"),
                blocker_reason=item.get("blocker_reason"),
            ))
    return gaps


def _build_waiver_list(items: list[dict]) -> list[WaiverEntry]:
    """Build waiver list from items with non-none waiver_status.

    Per ll-qa-settlement/SKILL.md:
    Waiver list includes all items where waiver_status is not "none".
    """
    waivers = []
    for item in items:
        ws = item.get("waiver_status", "none")
        if ws and ws != "none":
            waivers.append(WaiverEntry(
                coverage_id=item.get("coverage_id", ""),
                waiver_status=ws,
                waiver_reason=item.get("waiver_reason"),
                approver=item.get("waiver_approver"),
                approved_at=item.get("waiver_approved_at"),
            ))
    return waivers


def generate_settlement(
    manifest_items: list[dict],
    verdict_report: VerdictReport | None = None,
    chain: str = "api",
    feature_id: str = "",
) -> dict[str, Any]:
    """Generate settlement report integrating independent_verifier verdict.

    Args:
        manifest_items: List of manifest item dicts from api-coverage-manifest.yaml
                       or e2e-coverage-manifest.yaml.
        verdict_report: Optional VerdictReport from independent_verifier.
                       If not provided, computed from manifest_items.
        chain: "api" or "e2e"
        feature_id: Feature identifier for the settlement report.

    Returns:
        Settlement report dict ready for YAML output.

    Per D-07: settlement report contains verdict and confidence from independent_verifier.

    Data flow: independent_verifier.verdict → ll-qa-settlement → settlement report
    """
    # Compute verdict if not provided
    if verdict_report is None:
        verdict_report = verify(manifest_items)

    # Compute statistics from manifest items
    statistics = _compute_statistics(manifest_items)
    gap_list = _build_gap_list(manifest_items)
    waiver_list = _build_waiver_list(manifest_items)

    # Build settlement key based on chain type
    settlement_key = f"{chain}_settlement"

    settlement = {
        settlement_key: {
            "feature_id": feature_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "statistics": statistics,
            # Per D-07: verdict and confidence from independent_verifier
            "verdict": verdict_report.verdict.value,
            "confidence": round(verdict_report.confidence, 2),
            "details": verdict_report.details,
            "gap_list": [
                {
                    "coverage_id": g.coverage_id,
                    "capability": g.capability,
                    "lifecycle_status": g.lifecycle_status,
                    "reason": g.failure_reason or g.blocker_reason or "",
                }
                for g in gap_list
            ],
            "waiver_list": [
                {
                    "coverage_id": w.coverage_id,
                    "waiver_status": w.waiver_status,
                    "waiver_reason": w.waiver_reason or "",
                }
                for w in waiver_list
            ],
        }
    }

    return settlement


def generate_settlement_from_manifest(
    manifest_path: str | Path,
    verdict_report: VerdictReport | None = None,
    output_path: str | Path | None = None,
    chain: str = "api",
) -> dict[str, Any]:
    """Load manifest, generate settlement, optionally write to file.

    Args:
        manifest_path: Path to coverage manifest YAML
        verdict_report: Optional VerdictReport from independent_verifier.
        output_path: Optional output path for settlement report.
        chain: "api" or "e2e"

    Returns:
        Settlement report dict.
    """
    p = Path(manifest_path)
    data = _load_manifest(p)
    items = data.get("items", [])
    feature_id = data.get("feature_id", "")

    # If no verdict_report provided, compute from manifest
    if verdict_report is None:
        verdict_report = verify(items, run_id=data.get("run_id"))

    report = generate_settlement(items, verdict_report, chain=chain, feature_id=feature_id)

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(report, f, default_flow_style=False, sort_keys=False)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for settlement_integration.

    Usage:
        python -m cli.lib.settlement_integration <manifest.yaml> [output.yaml] [api|e2e]
        python -m cli.lib.settlement_integration --help
    """
    import sys

    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("Usage: python -m cli.lib.settlement_integration <manifest.yaml> [output.yaml] [api|e2e]")
        print()
        print("Integrates independent_verifier output into ll-qa-settlement.")
        print("Generates settlement report with verdict + confidence.")
        sys.exit(0)

    manifest_path = Path(args[0])
    output_path = Path(args[1]) if len(args) > 1 else manifest_path.parent / "settlement_report.yaml"
    chain = args[2] if len(args) > 2 else "api"

    if chain not in ("api", "e2e"):
        print(f"Error: chain must be 'api' or 'e2e', got '{chain}'")
        sys.exit(1)

    report = generate_settlement_from_manifest(manifest_path, output_path=output_path, chain=chain)
    settlement_key = f"{chain}_settlement"

    print(f"Settlement report written to: {output_path}")
    print(f"Verdict: {report[settlement_key]['verdict']}")
    print(f"Confidence: {report[settlement_key]['confidence']:.2f}")
    print(f"Statistics: {report[settlement_key]['statistics']}")


if __name__ == "__main__":
    main()

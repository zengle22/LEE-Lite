"""impl-verify CLI entry point — Verify GSD delivery against frozen FRZ Package.

Usage:
    python impl_verify.py --frz <frz-package-path> --gsd <gsd-delivery-dir> [--output <report-path>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure workspace root is on sys.path for cli.lib imports
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

import yaml

from cli.lib.v2.convergence import compute_final_verdict, converge_and_gate
from cli.lib.v2.delivery_parser import parse_gsd_delivery
from cli.lib.v2.engineering_docs import check_engineering_docs
from cli.lib.v2.feedback import route_issues
from cli.lib.v2.scope_compliance import check_feature_scope
from cli.lib.v2.task_completion import check_task_completion
from cli.lib.v2.traceability import verify_traceability


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="impl-verify: Verify GSD delivery")
    parser.add_argument("--frz", required=True, help="Path to FRZ Package YAML")
    parser.add_argument("--gsd", required=True, help="Path to GSD delivery directory")
    parser.add_argument("--output", help="Output path for verification report")
    args = parser.parse_args(argv)

    frz_path = Path(args.frz)
    gsd_dir = Path(args.gsd)

    if not frz_path.exists():
        print(f"FRZ file not found: {frz_path}", file=sys.stderr)
        return 1

    with open(frz_path, encoding="utf-8") as f:
        frz_data = yaml.safe_load(f) or {}

    frz_pkg = frz_data.get("frz_package", frz_data)
    frozen_chain = frz_pkg.get("frozen_ssot_chain", {})
    api_refs = frozen_chain.get("api_refs", [])
    feat_refs = frozen_chain.get("feat_refs", [])

    # Parse GSD delivery
    gsd_delivery = parse_gsd_delivery(gsd_dir)

    # Build minimal IMPL from FRZ (MVP: use first IMPL ref)
    from cli.lib.v2.models import IMPL

    impl = IMPL(
        impl_id="IMPL-001",
        requirement_context={},
        tech_context={},
        arch_context={},
        api_context={},
        allowed_scope={"directories": ["src/"], "files": ["*.py"]},
        source_refs=[],
    )

    # Step 1: Task completion & scope
    task_result = check_task_completion(impl, gsd_delivery)

    # Step 2: Engineering docs
    eng_result = check_engineering_docs(gsd_delivery)

    # Step 3: Feature scope
    api_specs = [{"path": f"/api/{ref}"} for ref in api_refs] if api_refs else []
    scope_result = check_feature_scope(gsd_delivery, api_specs)

    # Step 4: Traceability
    from cli.lib.v2.models import FEAT

    feats = [FEAT(feat_id=ref, title=ref, user_value="", trigger="", main_flow=[ref], acceptance_criteria=[ref], source_refs=[]) for ref in feat_refs]
    trace_result = verify_traceability(gsd_delivery, feats)

    # Step 5: Final verdict
    verdict = compute_final_verdict(task_result, eng_result, scope_result, trace_result)

    # Dual-line convergence (MVP: line 1 mock = pass)
    line1 = {"verdict": "pass", "issues": []}
    line2 = {"verdict": verdict["final_verdict"], "issues": verdict["blocking_issues"], "conditions": verdict["conditions"]}
    convergence = converge_and_gate(line1, line2)

    # Build report
    report = {
        **verdict,
        "convergence": convergence,
        "task_completion_detail": task_result,
        "engineering_docs_detail": eng_result,
        "feature_scope_detail": scope_result,
        "traceability_detail": trace_result,
    }

    # Feedback routing
    findings = []
    if scope_result.get("unauthorized_features"):
        findings.extend(scope_result["unauthorized_features"])
    report["feedback_items"] = route_issues(findings, feats, [])

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(report, f, allow_unicode=True, sort_keys=False)
        print(f"Report written: {out_path}")

    print(f"Final verdict: {verdict['final_verdict']}")
    print(f"Release ready: {convergence['release_ready']}")

    return 0 if verdict["final_verdict"] == "pass" else 100


if __name__ == "__main__":
    sys.exit(main())

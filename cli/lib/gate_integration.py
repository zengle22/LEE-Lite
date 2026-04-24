"""gate_integration — bridge between settlement and ll-qa-gate-evaluate.

Truth source: ADR-054 Phase 3 + D-06/D-07/D-08.
Consumes settlement report (containing verdict + confidence) and produces final_decision.

Data flow: settlement → ll-qa-gate-evaluate.final_decision
Gate evaluation derives final_decision from settlement verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.gate_schema import Gate, GateVerdict
from cli.lib.settlement_integration import generate_settlement


@dataclass
class GateInput:
    """Input contract for gate evaluation.

    Attributes:
        api_settlement_path: Path to api-settlement-report.yaml
        e2e_settlement_path: Path to e2e-settlement-report.yaml (optional for API-only)
    """
    api_settlement_path: str | Path
    e2e_settlement_path: str | Path | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file and return parsed dict."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _derive_gate_decision(
    api_verdict: str | None,
    api_confidence: float | None,
    e2e_verdict: str | None,
    e2e_confidence: float | None,
) -> GateVerdict:
    """Derive gate final_decision from settlement verdicts.

    Per D-08: gate-evaluate based on settlement report, aligned with settlement verdict.

    Truth table for all verdict combinations:
    +-----------------+-------------------+------------------------+
    | API verdict     | E2E verdict       | Final decision         |
    +-----------------+-------------------+------------------------+
    | pass            | pass              | PASS                   |
    | pass            | conditional_pass  | CONDITIONAL_PASS       |
    | pass            | None (missing)    | PASS (API verdict)    |
    | conditional_pass| pass              | CONDITIONAL_PASS       |
    | conditional_pass| conditional_pass  | CONDITIONAL_PASS       |
    | conditional_pass| fail              | FAIL                   |
    | fail            | pass              | FAIL                   |
    | fail            | conditional_pass  | FAIL                   |
    | fail            | fail              | FAIL                   |
    | fail            | None (missing)    | FAIL                   |
    | None (missing)  | pass              | PASS (E2E verdict)    |
    | None (missing)  | conditional_pass  | CONDITIONAL_PASS       |
    | None (missing)  | fail              | FAIL                   |
    +-----------------+-------------------+------------------------+

    Logic:
    - If both API and E2E verdict = pass → PASS
    - If any verdict = fail → FAIL (fail-safe)
    - If verdicts are pass/conditional → CONDITIONAL_PASS
    - If only one chain present, use that verdict (fail-safe for missing E2E)
    """
    verdicts_with_conf = [
        (v, c) for v, c in [(api_verdict, api_confidence), (e2e_verdict, e2e_confidence)]
        if v is not None
    ]

    if not verdicts_with_conf:
        return GateVerdict.FAIL

    # Extract verdict strings only for logic
    verdict_strings = [v for v, _ in verdicts_with_conf]

    # If any chain fails → FAIL (fail-safe default)
    if any(v == "fail" for v in verdict_strings):
        return GateVerdict.FAIL

    # All verdicts are pass or conditional_pass
    if all(v == "pass" for v in verdict_strings):
        return GateVerdict.PASS

    # Mixed pass/conditional → CONDITIONAL_PASS
    return GateVerdict.CONDITIONAL_PASS


def evaluate_gate(
    api_settlement_path: str | Path,
    e2e_settlement_path: str | Path | None = None,
    feature_id: str = "",
) -> Gate:
    """Evaluate gate decision from settlement reports.

    Args:
        api_settlement_path: Path to api-settlement-report.yaml
        e2e_settlement_path: Path to e2e-settlement-report.yaml (optional for API-only)
        feature_id: Feature identifier

    Returns:
        Gate dataclass with final_decision and reasoning.

    Per D-08: gate-evaluate based on settlement report, aligned with settlement verdict.

    Data flow: settlement → ll-qa-gate-evaluate.final_decision
    """
    # Load API settlement
    api_path = Path(api_settlement_path)
    api_data = _load_yaml(api_path)
    api_settlement = api_data.get("api_settlement", api_data)
    api_verdict = api_settlement.get("verdict")
    api_confidence = api_settlement.get("confidence", 0.0)

    # Load E2E settlement if provided
    e2e_verdict = None
    e2e_confidence = None
    if e2e_settlement_path:
        e2e_path = Path(e2e_settlement_path)
        if e2e_path.exists():
            e2e_data = _load_yaml(e2e_path)
            e2e_settlement = e2e_data.get("e2e_settlement", e2e_data)
            e2e_verdict = e2e_settlement.get("verdict")
            e2e_confidence = e2e_settlement.get("confidence", 0.0)

    # Derive final decision using truth table
    final_decision = _derive_gate_decision(
        api_verdict, api_confidence,
        e2e_verdict, e2e_confidence
    )

    # Build reason string
    reason_parts = []
    if api_verdict:
        reason_parts.append(
            f"API chain verdict: {api_verdict} (confidence: {api_confidence:.2f})"
        )
    else:
        reason_parts.append("API chain verdict: MISSING")
    if e2e_verdict:
        reason_parts.append(
            f"E2E chain verdict: {e2e_verdict} (confidence: {e2e_confidence:.2f})"
        )
    elif e2e_settlement_path:
        reason_parts.append("E2E chain verdict: MISSING")
    else:
        reason_parts.append("E2E chain: not provided (API-only evaluation)")
    reason_parts.append(f"Final decision: {final_decision.value}")

    return Gate(
        artifact_type="gate",
        gate_id=f"GATE-{feature_id}" if feature_id else None,
        verdict=final_decision,
        feature_id=feature_id or api_settlement.get("feature_id", ""),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        reason="; ".join(reason_parts),
        notes=None,
    )


def write_gate_output(gate: Gate, output_path: str | Path) -> None:
    """Write Gate to release_gate_input.yaml format.

    Args:
        gate: Gate dataclass from evaluate_gate()
        output_path: Destination path for release_gate_input.yaml
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    gate_dict = {
        "gate": {
            "artifact_type": gate.artifact_type,
            "gate_id": gate.gate_id,
            "verdict": gate.verdict.value if gate.verdict else None,
            "feature_id": gate.feature_id,
            "evaluated_at": gate.evaluated_at,
            "reason": gate.reason,
            "notes": gate.notes,
        }
    }

    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(gate_dict, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for gate_integration.

    Usage:
        python -m cli.lib.gate_integration <api_settlement.yaml> [e2e_settlement.yaml] [output.yaml] [feature_id]
        python -m cli.lib.gate_integration --help
    """
    import sys

    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("Usage: python -m cli.lib.gate_integration <api_settlement.yaml> [e2e_settlement.yaml] [output.yaml] [feature_id]")
        print()
        print("Evaluates gate decision from settlement reports.")
        print("Derives final_decision from settlement verdicts per D-08.")
        sys.exit(0)

    api_path = Path(args[0])

    # Parse optional arguments
    e2e_path = None
    output_path = None
    feature_id = ""

    i = 1
    while i < len(args):
        arg = args[i]
        if arg.endswith(".yaml"):
            if e2e_path is None:
                e2e_path = Path(arg)
            else:
                output_path = Path(arg)
        else:
            feature_id = arg
        i += 1

    if output_path is None:
        output_path = api_path.parent / "release_gate_input.yaml"

    gate = evaluate_gate(api_path, e2e_path, feature_id)
    write_gate_output(gate, output_path)

    print(f"Gate decision: {gate.verdict.value if gate.verdict else 'unknown'}")
    print(f"Gate output written to: {output_path}")
    print(f"Reason: {gate.reason}")


if __name__ == "__main__":
    main()

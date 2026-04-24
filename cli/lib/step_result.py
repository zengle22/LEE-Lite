"""StepResult dataclass — data passing unit between orchestrator steps.

Truth source: ADR-054 §5.1 R-1 (Step 3 → Step 4 data passing contract).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    """test_orchestrator internal data passing unit between steps.

    Carries execution outputs from test_exec_skill (Step 3) to
    update_manifest (Step 4), enabling coverage_id → evidence_refs
    correlation.
    """
    run_id: str
    execution_refs: dict[str, str] = field(default_factory=dict)
    candidate_path: str = ""
    case_results: list[dict] = field(default_factory=list)
    manifest_items: list[dict] = field(default_factory=list)
    execution_output_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "execution_refs": self.execution_refs,
            "candidate_path": self.candidate_path,
            "case_results": self.case_results,
            "manifest_items": self.manifest_items,
            "execution_output_dir": self.execution_output_dir,
        }
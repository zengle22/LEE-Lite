"""Shared DTOs for test orchestration and bridge layer.

These dataclasses define the data transfer contracts between test_orchestrator steps.
They are used internally by test_orchestrator.py and are NOT exposed to AI agent
orchestrators (those use Skill tool calls, not Python dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    """Data transfer unit between test_orchestrator steps.

    Used internally by test_orchestrator.py to pass data from Step 3
    (execute_test_exec_skill) to Step 4 (update_manifest).

    Attributes:
        run_id: Unique identifier for this execution run
        execution_refs: Dict of execution output refs (e.g., candidate_artifact_ref)
        candidate_path: Path to artifacts/active/qa/candidates/{slug}.json
        case_results: List of dicts with coverage_id, case_id, status per case
        manifest_items: List of {coverage_id, status, evidence_ref} for manifest update
        execution_output_dir: Directory containing playwright output files
    """

    run_id: str
    execution_refs: dict[str, str] = field(default_factory=dict)
    candidate_path: str = ""
    case_results: list[dict[str, Any]] = field(default_factory=list)
    manifest_items: list[dict[str, Any]] = field(default_factory=list)
    execution_output_dir: str = ""


@dataclass
class EnvConfig:
    """Environment configuration produced by environment_provision.py.

    Attributes:
        feat_ref: Feature reference (API chain)
        proto_ref: Prototype reference (E2E chain)
        modality: Execution modality (api, web_e2e, cli)
        base_url: Primary base URL
        app_url: Frontend URL (E2E chain)
        api_url: Backend API URL (separated architecture)
        browser: Browser for web_e2e (chromium, firefox, webkit)
        timeout: Timeout in milliseconds
        feat_assumptions: List of environment assumptions from FEAT
    """

    feat_ref: str | None = None
    proto_ref: str | None = None
    modality: str = "api"
    base_url: str = "http://localhost:8000"
    app_url: str = "http://localhost:3000"
    api_url: str | None = None
    browser: str = "chromium"
    timeout: int = 30000
    feat_assumptions: list[str] = field(default_factory=list)

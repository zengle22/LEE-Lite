"""State machine executor for journey execution with per-step state persistence.

Implements the 5-state model (SETUP/EXECUTE/VERIFY/COLLECT/DONE) with state
persistence to {run_id}-state.yaml. Per D-05/D-06, state is persisted per-step.
Per D-07/D-08, step failure stops journey and enters COLLECT state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from cli.lib.job_state import utc_now
from cli.lib.run_manifest_gen import RUN_ARTIFACTS_DIR
from cli.lib.scenario_spec_compile import (
    ScenarioSpec,
    ScenarioStep,
    ALayerAssertion,
    BLayerAssertion,
    CLayerAssertion,
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class StepExecutionError(Exception):
    """Raised when a step execution fails."""

    pass


# ---------------------------------------------------------------------------
# State Enums and Dataclasses
# ---------------------------------------------------------------------------


class ExecutionState(str, Enum):
    """Execution states for the state machine.

    SETUP: Initial state, preparing environment
    EXECUTE: Executing test steps
    VERIFY: Verifying assertions
    COLLECT: Collecting evidence after failure
    DONE: All tests passed
    """

    SETUP = "SETUP"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    COLLECT = "COLLECT"
    DONE = "DONE"


@dataclass
class CompletedStep:
    """Represents a completed step in execution."""

    journey_id: str
    step_index: int
    step_name: str
    status: str  # "passed" | "failed"
    error: str | None = None
    completed_at: str | None = None


@dataclass
class ExecutionStateData:
    """State data persisted to {run_id}-state.yaml."""

    run_id: str
    current_state: ExecutionState
    current_journey: str | None = None
    current_step_index: int = 0
    completed_steps: list[CompletedStep] = field(default_factory=list)
    failed_journeys: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class ExecutionResult:
    """Result of a complete execution run."""

    run_id: str
    final_state: ExecutionState
    completed_steps: list[CompletedStep]
    failed_journeys: list[str]
    summary: dict[str, Any]


# ---------------------------------------------------------------------------
# State Machine Executor
# ---------------------------------------------------------------------------


class StateMachineExecutor:
    """Executes journey scenarios with state persistence.

    Implements a 5-state execution model:
    - SETUP: Initialize execution environment
    - EXECUTE: Execute journey steps atomically
    - VERIFY: Verify assertions per journey
    - COLLECT: Collect evidence on failure
    - DONE: All journeys completed

    Per D-05/D-06: State persisted per-step to {run_id}-state.yaml
    Per D-07/D-08: Step failure stops journey and enters COLLECT state
    """

    def __init__(
        self,
        workspace_root: Path,
        run_id: str,
        scenario_specs: list[ScenarioSpec],
        *,
        resume: bool = False,
    ) -> None:
        """Initialize the state machine executor.

        Args:
            workspace_root: Root of the workspace
            run_id: Unique identifier for this run
            scenario_specs: List of scenario specs to execute
            resume: If True, resume from saved state; if False, start fresh
        """
        self.workspace_root = Path(workspace_root)
        self.run_id = run_id
        self.scenario_specs = scenario_specs
        self.resume = resume
        self._state: ExecutionStateData | None = None
        self._state_file_path: Path | None = None

    def run(self) -> ExecutionResult:
        """Execute the state machine.

        Returns:
            ExecutionResult with final state and summary
        """
        # Initialize or load state
        if self.resume:
            self._state = self._load_state()
            self._state_file_path = self._get_state_file_path()

            # If already in DONE state, just return current state
            if self._state.current_state == ExecutionState.DONE:
                summary: dict[str, Any] = {
                    "total_journeys": len(self.scenario_specs),
                    "completed_steps": len(self._state.completed_steps),
                    "failed_journeys": len(self._state.failed_journeys),
                    "final_state": ExecutionState.DONE.value,
                    "resumed_from": "complete",
                }
                return ExecutionResult(
                    run_id=self.run_id,
                    final_state=ExecutionState.DONE,
                    completed_steps=list(self._state.completed_steps),
                    failed_journeys=list(self._state.failed_journeys),
                    summary=summary,
                )

            self._transition_state(self._state.current_state)
        else:
            self._initialize_state()

        # Execute state machine
        final_state = self._execute_with_state_machine()

        # Build summary
        summary = {
            "total_journeys": len(self.scenario_specs),
            "completed_steps": len(self._state.completed_steps),
            "failed_journeys": len(self._state.failed_journeys),
            "final_state": final_state.value,
        }

        return ExecutionResult(
            run_id=self.run_id,
            final_state=final_state,
            completed_steps=list(self._state.completed_steps),
            failed_journeys=list(self._state.failed_journeys),
            summary=summary,
        )

    def _initialize_state(self) -> None:
        """Initialize new execution state."""
        self._state = ExecutionStateData(
            run_id=self.run_id,
            current_state=ExecutionState.SETUP,
            current_journey=None,
            current_step_index=0,
            completed_steps=[],
            failed_journeys=[],
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self._state_file_path = self._get_state_file_path()
        self._save_state()

    def _load_state(self) -> ExecutionStateData:
        """Load state from {run_id}-state.yaml.

        Returns:
            Loaded ExecutionStateData

        Raises:
            FileNotFoundError: If state file does not exist
            ValueError: If state data is corrupted
        """
        state_path = self._get_state_file_path()
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {state_path}")

        try:
            raw = state_path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ValueError(f"Corrupted state file for {self.run_id!r}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"State file for {self.run_id!r} is not a valid YAML object")

        # Parse state
        try:
            current_state = ExecutionState(data["current_state"])
            completed_steps = [
                CompletedStep(
                    journey_id=cs["journey_id"],
                    step_index=cs["step_index"],
                    step_name=cs.get("step_name", ""),
                    status=cs["status"],
                    error=cs.get("error"),
                    completed_at=cs.get("completed_at"),
                )
                for cs in data.get("completed_steps", [])
            ]
            failed_journeys = list(data.get("failed_journeys", []))

            state = ExecutionStateData(
                run_id=data["run_id"],
                current_state=current_state,
                current_journey=data.get("current_journey"),
                current_step_index=data.get("current_step_index", 0),
                completed_steps=completed_steps,
                failed_journeys=failed_journeys,
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
            # Set state file path for future saves
            self._state_file_path = state_path
            return state
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Invalid state structure for {self.run_id!r}: {exc}") from exc

    def _save_state(self) -> None:
        """Save current state to {run_id}-state.yaml."""
        if self._state is None or self._state_file_path is None:
            raise RuntimeError("State not initialized")

        # Update timestamp
        self._state.updated_at = utc_now()

        # Convert to dict for serialization
        state_dict = {
            "run_id": self._state.run_id,
            "current_state": self._state.current_state.value,
            "current_journey": self._state.current_journey,
            "current_step_index": self._state.current_step_index,
            "completed_steps": [
                asdict(cs) for cs in self._state.completed_steps
            ],
            "failed_journeys": self._state.failed_journeys,
            "created_at": self._state.created_at,
            "updated_at": self._state.updated_at,
        }

        # Ensure directory exists
        self._state_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write state file
        with self._state_file_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(state_dict, fh, allow_unicode=True, sort_keys=False)

    def _get_state_file_path(self) -> Path:
        """Get the path to the state file.

        Returns:
            Path to ssot/tests/.artifacts/runs/{run_id}/{run_id}-state.yaml
        """
        return self.workspace_root / RUN_ARTIFACTS_DIR / self.run_id / f"{self.run_id}-state.yaml"

    def _transition_state(self, new_state: ExecutionState) -> None:
        """Transition to a new state and persist.

        Args:
            new_state: The new state to transition to
        """
        if self._state is None:
            raise RuntimeError("State not initialized")

        # Validate transition
        valid_transitions = self._get_valid_transitions(self._state.current_state)
        if new_state not in valid_transitions:
            raise ValueError(
                f"Invalid transition: {self._state.current_state.value} -> {new_state.value}"
            )

        # Update state
        self._state.current_state = new_state
        self._save_state()

    def _get_valid_transitions(self, state: ExecutionState) -> set[ExecutionState]:
        """Get valid next states from current state.

        Args:
            state: Current state

        Returns:
            Set of valid next states
        """
        # State machine transitions per plan:
        # SETUP -> EXECUTE -> VERIFY -> COLLECT/DONE
        # With shortcut: EXECUTE -> DONE (when all complete)
        transitions: dict[ExecutionState, set[ExecutionState]] = {
            ExecutionState.SETUP: {ExecutionState.EXECUTE},
            ExecutionState.EXECUTE: {ExecutionState.VERIFY, ExecutionState.COLLECT, ExecutionState.DONE},
            ExecutionState.VERIFY: {ExecutionState.COLLECT, ExecutionState.DONE},
            ExecutionState.COLLECT: {ExecutionState.EXECUTE, ExecutionState.DONE},
            ExecutionState.DONE: set(),
        }
        return transitions.get(state, set())

    def _execute_with_state_machine(self) -> ExecutionState:
        """Execute the state machine logic.

        Returns:
            Final execution state
        """
        if self._state is None:
            raise RuntimeError("State not initialized")

        # SETUP: Initialize environment
        if self._state.current_state == ExecutionState.SETUP:
            self._do_setup()
            self._transition_state(ExecutionState.EXECUTE)

        # EXECUTE: Iterate over scenario specs
        if self._state.current_state == ExecutionState.EXECUTE:
            all_complete = self._execute_journeys()
            if all_complete:
                self._transition_state(ExecutionState.DONE)
            else:
                # Some journeys failed - will enter COLLECT
                self._transition_state(ExecutionState.COLLECT)

        # VERIFY: Check assertions (currently merged with EXECUTE)
        if self._state.current_state == ExecutionState.VERIFY:
            self._do_verify()
            if self._state.failed_journeys:
                self._transition_state(ExecutionState.COLLECT)
            else:
                self._transition_state(ExecutionState.DONE)

        # COLLECT: Gather evidence for failed journeys
        if self._state.current_state == ExecutionState.COLLECT:
            self._do_collect()
            self._transition_state(ExecutionState.DONE)

        # DONE: Execution complete
        return self._state.current_state

    def _do_setup(self) -> None:
        """Perform SETUP phase initialization."""
        # Ensure run directory exists
        run_dir = self.workspace_root / RUN_ARTIFACTS_DIR / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

    def _execute_journeys(self) -> bool:
        """Execute all journeys.

        Per D-07: Each step is atomic unit
        Per D-08: On step failure, stop journey, enter COLLECT state

        Returns:
            True if all journeys completed successfully, False otherwise
        """
        if self._state is None:
            raise RuntimeError("State not initialized")

        all_passed = True

        for spec in self.scenario_specs:
            # Check if journey already failed
            if spec.journey_id in self._state.failed_journeys:
                continue

            self._state.current_journey = spec.journey_id
            self._save_state()

            # Execute steps for this journey
            journey_passed = self._execute_steps_for_journey(spec)
            if not journey_passed:
                all_passed = False

        return all_passed

    def _execute_steps_for_journey(self, spec: ScenarioSpec) -> bool:
        """Execute steps for a single journey.

        Args:
            spec: Scenario spec with steps to execute

        Returns:
            True if all steps passed, False if any failed
        """
        if self._state is None:
            raise RuntimeError("State not initialized")

        for step in spec.steps:
            # Check if step already completed
            if self._is_step_completed(spec.journey_id, step.step_index):
                continue

            # Update current step tracking
            self._state.current_step_index = step.step_index
            self._save_state()

            # Execute step (atomic unit per D-07)
            try:
                self._execute_step(step)
                # Mark step as completed
                completed = CompletedStep(
                    journey_id=spec.journey_id,
                    step_index=step.step_index,
                    step_name=self._get_step_name(step),
                    status="passed",
                    completed_at=utc_now(),
                )
                self._state.completed_steps.append(completed)
            except StepExecutionError as exc:
                # Per D-08: Step failure stops journey
                completed = CompletedStep(
                    journey_id=spec.journey_id,
                    step_index=step.step_index,
                    step_name=self._get_step_name(step),
                    status="failed",
                    error=str(exc),
                    completed_at=utc_now(),
                )
                self._state.completed_steps.append(completed)
                self._state.failed_journeys.append(spec.journey_id)
                self._save_state()
                return False

        return True

    def _execute_step(self, step: ScenarioStep) -> None:
        """Execute a single step.

        This is a placeholder for actual Playwright/step execution.
        Raises StepExecutionError on failure.

        Args:
            step: Step to execute

        Raises:
            StepExecutionError: If step execution fails
        """
        # Placeholder for actual step execution
        # In a real implementation, this would invoke Playwright or similar
        if not step.action:
            raise StepExecutionError(f"Step {step.step_index} has no action")

    def _do_verify(self) -> None:
        """Perform VERIFY phase - check assertions.

        Note: Currently assertions are checked inline during EXECUTE.
        This method provides a hook for more detailed verification logic.
        """
        pass

    def _do_collect(self) -> None:
        """Perform COLLECT phase - gather evidence for failed journeys.

        Per D-04: C_MISSING placeholders collect HAR + screenshot evidence.
        """
        if self._state is None:
            raise RuntimeError("State not initialized")

        for journey_id in self._state.failed_journeys:
            self._collect_evidence(journey_id)

    def _collect_evidence(self, journey_id: str) -> None:
        """Collect evidence for a failed journey.

        Creates evidence directory and placeholder files.

        Args:
            journey_id: ID of the failed journey
        """
        evidence_dir = (
            self.workspace_root
            / RUN_ARTIFACTS_DIR
            / self.run_id
            / "evidence"
            / journey_id
        )
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # Create placeholder evidence files
        # In a real implementation, these would be actual HAR and screenshot files
        har_file = evidence_dir / "network.har"
        screenshot_file = evidence_dir / "screenshot.png"

        if not har_file.exists():
            har_file.write_text("# HAR placeholder - to be captured by Playwright", encoding="utf-8")
        if not screenshot_file.exists():
            screenshot_file.write_text("# Screenshot placeholder - to be captured by Playwright", encoding="utf-8")

    def _is_step_completed(self, journey_id: str, step_index: int) -> bool:
        """Check if a step is already completed with passed status.

        Args:
            journey_id: Journey identifier
            step_index: Step index to check

        Returns:
            True if step completed successfully, False otherwise
        """
        if self._state is None:
            return False

        for completed in self._state.completed_steps:
            if (
                completed.journey_id == journey_id
                and completed.step_index == step_index
                and completed.status == "passed"
            ):
                return True
        return False

    def _get_step_name(self, step: ScenarioStep) -> str:
        """Get human-readable name for a step.

        Args:
            step: Step to get name for

        Returns:
            Step name string
        """
        parts = [step.action or "unknown"]
        if step.target:
            parts.append(f"@ {step.target}")
        return " ".join(parts)

    def get_next_uncompleted_step(self, journey_id: str) -> tuple[str, int] | None:
        """Get the next uncompleted step for a journey.

        Used for resume functionality.

        Args:
            journey_id: Journey to check

        Returns:
            Tuple of (journey_id, step_index) or None if all steps completed
        """
        if self._state is None:
            return None

        # Find scenario spec for this journey
        spec = None
        for s in self.scenario_specs:
            if s.journey_id == journey_id:
                spec = s
                break

        if spec is None:
            return None

        # Find first uncompleted step
        for step in spec.steps:
            if not self._is_step_completed(journey_id, step.step_index):
                return (journey_id, step.step_index)

        return None

    def get_current_state(self) -> ExecutionStateData | None:
        """Get the current execution state.

        Returns:
            Current ExecutionStateData or None if not initialized
        """
        return self._state


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def create_executor(
    workspace_root: Path,
    run_id: str,
    scenario_specs: list[ScenarioSpec],
    *,
    resume: bool = False,
) -> StateMachineExecutor:
    """Create a state machine executor.

    Args:
        workspace_root: Root of the workspace
        run_id: Unique identifier for this run
        scenario_specs: List of scenario specs to execute
        resume: If True, resume from saved state; if False, start fresh

    Returns:
        Configured StateMachineExecutor
    """
    return StateMachineExecutor(
        workspace_root=workspace_root,
        run_id=run_id,
        scenario_specs=scenario_specs,
        resume=resume,
    )


def load_state(workspace_root: Path, run_id: str) -> ExecutionStateData | None:
    """Load execution state from {run_id}-state.yaml.

    Args:
        workspace_root: Root of the workspace
        run_id: The run identifier

    Returns:
        ExecutionStateData if exists, None otherwise
    """
    state_path = workspace_root / RUN_ARTIFACTS_DIR / run_id / f"{run_id}-state.yaml"

    if not state_path.exists():
        return None

    try:
        raw = state_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)

        if not isinstance(data, dict):
            return None

        current_state = ExecutionState(data["current_state"])
        completed_steps = [
            CompletedStep(
                journey_id=cs["journey_id"],
                step_index=cs["step_index"],
                step_name=cs.get("step_name", ""),
                status=cs["status"],
                error=cs.get("error"),
                completed_at=cs.get("completed_at"),
            )
            for cs in data.get("completed_steps", [])
        ]

        return ExecutionStateData(
            run_id=data["run_id"],
            current_state=current_state,
            current_journey=data.get("current_journey"),
            current_step_index=data.get("current_step_index", 0),
            completed_steps=completed_steps,
            failed_journeys=list(data.get("failed_journeys", [])),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    except (yaml.YAMLError, KeyError, ValueError):
        return None
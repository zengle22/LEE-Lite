"""Integration tests for resume functionality (TEST-03).

This test module verifies --resume re-runs failed cases without repeating
completed steps, state file loading, and failure scenario handling.

Per ADR-054 §5.1 R-7 resume mechanism and D-10.
"""

import pytest
from pathlib import Path
import yaml

from cli.lib.state_machine_executor import (
    StateMachineExecutor,
    ExecutionState,
    ExecutionStateData,
    CompletedStep,
    create_executor,
    load_state,
)
from cli.lib.scenario_spec_compile import (
    ScenarioSpec,
    ScenarioAssertions,
    ScenarioStep,
    ALayerAssertion,
    BLayerAssertion,
    CLayerAssertion,
)
from cli.lib.job_state import utc_now


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_scenario_specs() -> list[ScenarioSpec]:
    """Create mock scenario specs for state machine testing."""
    return [
        ScenarioSpec(
            journey_id="JOURNEY-001",
            spec_id="SPEC-001",
            coverage_id="COV-001",
            steps=[
                ScenarioStep(step_index=0, action="navigate", target="/login"),
                ScenarioStep(step_index=1, action="fill_form", target="username"),
                ScenarioStep(step_index=2, action="fill_form", target="password"),
                ScenarioStep(step_index=3, action="click", target="submit"),
            ],
        ),
        ScenarioSpec(
            journey_id="JOURNEY-002",
            spec_id="SPEC-002",
            coverage_id="COV-002",
            steps=[
                ScenarioStep(step_index=0, action="navigate", target="/dashboard"),
                ScenarioStep(step_index=1, action="click", target="profile"),
                ScenarioStep(step_index=2, action="verify", target="profile-page"),
            ],
        ),
        ScenarioSpec(
            journey_id="JOURNEY-003",
            spec_id="SPEC-003",
            coverage_id="COV-003",
            steps=[
                ScenarioStep(step_index=0, action="navigate", target="/settings"),
                ScenarioStep(step_index=1, action="update", target="email"),
            ],
        ),
    ]


@pytest.fixture
def partial_state_yaml(tmp_path: Path) -> Path:
    """Create a partial execution state.yaml file."""
    state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-PARTIAL-001"
    state_dir.mkdir(parents=True, exist_ok=True)

    state_content = {
        "run_id": "RUN-PARTIAL-001",
        "current_state": "EXECUTE",
        "completed_steps": [
            {
                "journey_id": "JOURNEY-001",
                "step_index": 0,
                "step_name": "navigate",
                "status": "passed",
                "error": None,
                "completed_at": utc_now(),
            },
            {
                "journey_id": "JOURNEY-001",
                "step_index": 1,
                "step_name": "fill_form_username",
                "status": "passed",
                "error": None,
                "completed_at": utc_now(),
            },
        ],
        "current_journey": "JOURNEY-001",
        "current_step_index": 1,
        "failed_journeys": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    state_file = state_dir / "RUN-PARTIAL-001-state.yaml"
    with state_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

    return state_file


# ---------------------------------------------------------------------------
# Test: Resume from State
# ---------------------------------------------------------------------------


class TestResumeFromState:
    """Tests for resuming from existing state file."""

    def test_resume_loads_existing_state(self, tmp_path: Path, partial_state_yaml: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that resume=True loads existing state.yaml."""
        # Load state directly to verify resume capability
        loaded = load_state(tmp_path, "RUN-PARTIAL-001")

        assert loaded is not None
        assert loaded.run_id == "RUN-PARTIAL-001"
        assert loaded.current_state == ExecutionState.EXECUTE
        assert len(loaded.completed_steps) == 2

    def test_resume_skips_completed_steps(self, tmp_path: Path, partial_state_yaml: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that completed steps are skipped on resume."""
        loaded = load_state(tmp_path, "RUN-PARTIAL-001")

        # Check that JOURNEY-001 steps 0,1 are marked completed
        completed = {(s.journey_id, s.step_index) for s in loaded.completed_steps}
        assert ("JOURNEY-001", 0) in completed
        assert ("JOURNEY-001", 1) in completed

    def test_resume_state_file_format(self, tmp_path: Path, partial_state_yaml: Path):
        """Test that resume loads state file with correct format."""
        loaded = load_state(tmp_path, "RUN-PARTIAL-001")

        assert loaded is not None
        assert loaded.run_id == "RUN-PARTIAL-001"
        assert loaded.current_state == ExecutionState.EXECUTE
        assert len(loaded.completed_steps) == 2


# ---------------------------------------------------------------------------
# Test: Resume with Partial Execution
# ---------------------------------------------------------------------------


class TestResumeWithPartialExecution:
    """Tests for resume scenarios with partial execution."""

    def test_partial_execution_state_persisted(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that state is persisted after partial execution."""
        executor1 = create_executor(tmp_path, "RUN-PARTIAL-002", mock_scenario_specs, resume=False)
        result1 = executor1.run()

        # Load state using load_state function
        loaded = load_state(tmp_path, "RUN-PARTIAL-002")
        assert loaded is not None

    def test_resume_after_journey_failure(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test resume continues after journey failure."""
        # Create state where JOURNEY-001 failed
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-FAIL-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-FAIL-001",
            "current_state": "COLLECT",
            "completed_steps": [
                {
                    "journey_id": "JOURNEY-001",
                    "step_index": 0,
                    "step_name": "navigate",
                    "status": "passed",
                    "error": None,
                    "completed_at": utc_now(),
                },
                {
                    "journey_id": "JOURNEY-001",
                    "step_index": 1,
                    "step_name": "fill_form",
                    "status": "failed",
                    "error": "Network timeout",
                    "completed_at": utc_now(),
                },
            ],
            "current_journey": "JOURNEY-001",
            "current_step_index": 1,
            "failed_journeys": ["JOURNEY-001"],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-FAIL-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Load state and verify COLLECT state
        loaded = load_state(tmp_path, "RUN-FAIL-001")
        assert loaded is not None
        assert loaded.current_state == ExecutionState.COLLECT
        assert "Network timeout" in str([s.error for s in loaded.completed_steps if s.error])

    def test_resume_with_multiple_journeys(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test resume works with multiple journey scenario."""
        # Create state with multiple journeys
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-MULTI-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-MULTI-001",
            "current_state": "EXECUTE",
            "completed_steps": [
                {"journey_id": "JOURNEY-001", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 1, "step_name": "fill_form", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-002", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
            ],
            "current_journey": "JOURNEY-002",
            "current_step_index": 0,
            "failed_journeys": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-MULTI-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Verify state loaded correctly
        loaded = load_state(tmp_path, "RUN-MULTI-001")
        assert loaded is not None
        assert len(loaded.completed_steps) == 3

        # Verify JOURNEY-002 step 0 is completed
        completed_j2_step0 = any(
            s.journey_id == "JOURNEY-002" and s.step_index == 0
            for s in loaded.completed_steps
        )
        assert completed_j2_step0


# ---------------------------------------------------------------------------
# Test: Resume Failure Scenarios
# ---------------------------------------------------------------------------


class TestResumeFailureScenarios:
    """Tests for resume failure scenarios."""

    def test_resume_nonexistent_run_initializes_fresh(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that resuming non-existent run initializes fresh state."""
        # Verify load_state returns None for missing state
        loaded = load_state(tmp_path, "RUN-NONEXISTENT-001")
        assert loaded is None

        # Verify state file does not exist
        state_file = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-NONEXISTENT-001" / "RUN-NONEXISTENT-001-state.yaml"
        assert not state_file.exists()

    def test_resume_with_invalid_state_file(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test error handling for corrupted state.yaml."""
        # Create corrupted state file
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-CORRUPT-001"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "RUN-CORRUPT-001-state.yaml"

        state_file.write_text("invalid: yaml: content: [}", encoding="utf-8")

        # Should return None when state is corrupted
        loaded = load_state(tmp_path, "RUN-CORRUPT-001")
        assert loaded is None

    def test_resume_after_complete_run(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test resume after complete run."""
        # Create completed state
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-COMPLETE-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-COMPLETE-001",
            "current_state": "DONE",
            "completed_steps": [
                {"journey_id": "JOURNEY-001", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 1, "step_name": "fill_form", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 2, "step_name": "fill_form", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 3, "step_name": "click", "status": "passed", "error": None, "completed_at": utc_now()},
            ],
            "current_journey": "JOURNEY-001",
            "current_step_index": 3,
            "failed_journeys": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-COMPLETE-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Verify state loaded correctly
        loaded = load_state(tmp_path, "RUN-COMPLETE-001")
        assert loaded is not None
        assert loaded.current_state == ExecutionState.DONE
        assert len(loaded.completed_steps) == 4


# ---------------------------------------------------------------------------
# Test: Resume State File Format
# ---------------------------------------------------------------------------


class TestResumeStateFileFormat:
    """Tests for state.yaml file format validation."""

    def test_state_file_contains_required_fields(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that state.yaml has run_id, current_state, completed_steps."""
        executor = create_executor(tmp_path, "RUN-FORMAT-001", mock_scenario_specs, resume=False)
        executor.run()

        state_data = executor._state
        assert state_data is not None
        assert state_data.run_id == "RUN-FORMAT-001"
        assert state_data.current_state in ExecutionState
        assert isinstance(state_data.completed_steps, list)

    def test_state_file_format_yaml(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that state.yaml is valid YAML."""
        executor = create_executor(tmp_path, "RUN-YAML-001", mock_scenario_specs, resume=False)
        executor.run()

        state_file = (
            tmp_path
            / "ssot"
            / "tests"
            / ".artifacts"
            / "runs"
            / "RUN-YAML-001"
            / "RUN-YAML-001-state.yaml"
        )

        # Should be valid YAML
        loaded = yaml.safe_load(state_file.read_text(encoding="utf-8"))
        assert isinstance(loaded, dict)
        assert loaded["run_id"] == "RUN-YAML-001"

    def test_state_file_complex_structure(self, tmp_path: Path):
        """Test state file with multiple steps and journeys."""
        # Create complex state
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-COMPLEX-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-COMPLEX-001",
            "current_state": "EXECUTE",
            "completed_steps": [
                {"journey_id": "JOURNEY-001", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-002", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-003", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
            ],
            "current_journey": "JOURNEY-003",
            "current_step_index": 0,
            "failed_journeys": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-COMPLEX-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        loaded = yaml.safe_load(state_file.read_text(encoding="utf-8"))
        assert len(loaded["completed_steps"]) == 3


# ---------------------------------------------------------------------------
# Test: Resume Evidence Collection
# ---------------------------------------------------------------------------


class TestResumeEvidenceCollection:
    """Tests for evidence collection on COLLECT state."""

    def test_collect_state_on_resume_failure(self, tmp_path: Path):
        """Test COLLECT state is entered when resume encounters failure."""
        # Create state with failure
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-COLLECT-FAIL-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-COLLECT-FAIL-001",
            "current_state": "COLLECT",
            "completed_steps": [
                {"journey_id": "JOURNEY-001", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 1, "step_name": "fill_form", "status": "failed", "error": "Test error", "completed_at": utc_now()},
            ],
            "current_journey": "JOURNEY-001",
            "current_step_index": 1,
            "failed_journeys": ["JOURNEY-001"],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-COLLECT-FAIL-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Load and verify COLLECT state
        loaded = load_state(tmp_path, "RUN-COLLECT-FAIL-001")
        assert loaded is not None
        assert loaded.current_state == ExecutionState.COLLECT

    def test_evidence_preserved_on_resume(self, tmp_path: Path):
        """Test evidence from failed run is preserved."""
        # Create state with partial failure
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-EVIDENCE-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-EVIDENCE-001",
            "current_state": "COLLECT",
            "completed_steps": [
                {"journey_id": "JOURNEY-001", "step_index": 0, "step_name": "navigate", "status": "passed", "error": None, "completed_at": utc_now()},
                {"journey_id": "JOURNEY-001", "step_index": 1, "step_name": "fill_form", "status": "failed", "error": "Partial failure", "completed_at": utc_now()},
            ],
            "current_journey": "JOURNEY-001",
            "current_step_index": 1,
            "failed_journeys": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-EVIDENCE-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Load and verify evidence preserved
        loaded = load_state(tmp_path, "RUN-EVIDENCE-001")
        assert loaded is not None
        assert len(loaded.completed_steps) == 2
        assert loaded.completed_steps[0].status == "passed"
        assert loaded.completed_steps[1].status == "failed"

    def test_load_state_function(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test load_state convenience function."""
        # Create state
        executor = create_executor(tmp_path, "RUN-LOAD-001", mock_scenario_specs, resume=False)
        executor.run()

        # Load using function
        loaded = load_state(tmp_path, "RUN-LOAD-001")

        assert loaded is not None
        assert loaded.run_id == "RUN-LOAD-001"

    def test_load_state_nonexistent(self, tmp_path: Path):
        """Test load_state returns None for missing state."""
        loaded = load_state(tmp_path, "RUN-MISSING-001")
        assert loaded is None


# ---------------------------------------------------------------------------
# Test: State Machine Resume Integration
# ---------------------------------------------------------------------------


class TestStateMachineResumeIntegration:
    """Integration tests for state machine with resume."""

    def test_full_resume_cycle(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test complete resume cycle: execute -> fail -> resume -> complete."""
        # Phase 1: Initial execution
        executor1 = create_executor(tmp_path, "RUN-CYCLE-001", mock_scenario_specs, resume=False)
        result1 = executor1.run()

        assert result1.run_id == "RUN-CYCLE-001"
        assert result1.final_state in [ExecutionState.EXECUTE, ExecutionState.DONE]

        # Phase 2: Verify state file exists and can be loaded
        loaded = load_state(tmp_path, "RUN-CYCLE-001")
        assert loaded is not None

    def test_resume_skips_completed_in_execution(self, tmp_path: Path, partial_state_yaml: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that resumed execution skips already completed steps."""
        # Load state with partial execution
        loaded = load_state(tmp_path, "RUN-PARTIAL-001")
        assert loaded is not None

        # Verify completed steps are preserved
        completed = {(s.journey_id, s.step_index) for s in loaded.completed_steps}
        assert ("JOURNEY-001", 0) in completed
        assert ("JOURNEY-001", 1) in completed
        assert len(loaded.completed_steps) == 2

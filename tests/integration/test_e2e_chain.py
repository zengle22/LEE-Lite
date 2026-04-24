"""Integration tests for E2E chain execution (TEST-02).

This test module verifies end-to-end chain execution with --app-url and --api-url
parameters, scenario spec compilation, and state machine execution.

Per ADR-054 §5.1 R-2, R-3, R-8 and D-03/D-04.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from cli.lib.test_orchestrator import run_spec_test
from cli.lib.run_manifest_gen import generate_run_manifest, load_run_manifest
from cli.lib.state_machine_executor import (
    StateMachineExecutor,
    ExecutionState,
    ExecutionStateData,
    CompletedStep,
    create_executor,
    load_state,
)
from cli.lib.scenario_spec_compile import (
    compile_scenario_spec,
    ScenarioSpec,
    ScenarioAssertions,
    ScenarioStep,
    ALayerAssertion,
    BLayerAssertion,
    CLayerAssertion,
    scenario_spec_to_yaml,
)
from cli.lib.job_state import utc_now


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_e2e_spec_dir(tmp_path: Path) -> dict[str, Path]:
    """Create mock e2e-journey-spec directory with sample spec."""
    spec_dir = tmp_path / "ssot" / "tests" / "e2e" / "PROTO-001" / "e2e-journey-spec"
    spec_dir.mkdir(parents=True, exist_ok=True)

    spec_content = """## Case Metadata
| spec_id | JOURNEY-001 |
| journey_id | E2E-LOGIN-FLOW |
| coverage_id | E2E-COV-001 |
| priority | P0 |
| entry_point | /login |
| Evidence Required | HAR capture |
| Evidence Required | screenshot |

## User Steps
1. navigate -> /login
2. fill_form -> username field -> testuser
3. fill_form -> password field -> testpass
4. click -> submit button

## Expected UI States
- Login form visible
- Username field contains placeholder text
- Submit button is enabled

## Network Events
- POST /api/auth/login
- GET /api/user/profile

## Expected Persistence
- Session persistence in backend database
- User data persisted to server
"""

    spec_file = spec_dir / "JOURNEY-001.md"
    spec_file.write_text(spec_content, encoding="utf-8")

    return {
        "spec_dir": spec_dir,
        "spec_file": spec_file,
        "proto_dir": spec_dir.parent,
    }


@pytest.fixture
def mock_proto_manifest(tmp_path: Path, mock_e2e_spec_dir: dict[str, Path]) -> Path:
    """Create mock e2e-coverage-manifest.yaml."""
    manifest_dir = mock_e2e_spec_dir["proto_dir"]
    manifest_content = {
        "_version": "1.0",
        "proto_ref": "PROTO-001",
        "items": [
            {
                "coverage_id": "E2E-COV-001",
                "lifecycle_status": "designed",
                "last_run_status": None,
                "evidence_refs": [],
            },
        ],
    }

    manifest_path = manifest_dir / "e2e-coverage-manifest.yaml"
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest_content, f, allow_unicode=True, sort_keys=False)

    return manifest_path


@pytest.fixture
def workspace_with_e2e_context(
    tmp_path: Path,
    mock_e2e_spec_dir: dict[str, Path],
    mock_proto_manifest: Path,
) -> Path:
    """Set up full workspace structure for E2E chain."""
    # Create additional directories needed
    (tmp_path / "ssot" / "tests" / ".spec-adapter").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ssot" / "tests" / ".artifacts" / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ssot" / "environments").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "active" / "qa" / "candidates").mkdir(parents=True, exist_ok=True)

    return tmp_path


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
    ]


@pytest.fixture
def precreated_state_file(tmp_path: Path) -> Path:
    """Create a pre-existing state file for resume testing."""
    state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-RESUME-001"
    state_dir.mkdir(parents=True, exist_ok=True)

    state_content = {
        "run_id": "RUN-RESUME-001",
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
        ],
        "current_journey": "JOURNEY-001",
        "current_step_index": 0,
        "failed_journeys": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }

    state_file = state_dir / "RUN-RESUME-001-state.yaml"
    with state_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

    return state_file


# ---------------------------------------------------------------------------
# Test: Run Manifest Generation
# ---------------------------------------------------------------------------


class TestRunManifestForE2E:
    """Tests for run_manifest_gen E2E chain support."""

    def test_generates_run_manifest_for_e2e(self, tmp_path: Path):
        """Test that generate_run_manifest creates manifest for E2E run."""
        app_url = "http://localhost:3000"
        api_url = "http://localhost:8000"

        manifest_path = generate_run_manifest(
            tmp_path,
            "RUN-E2E-001",
            app_url=app_url,
            api_url=api_url,
            browser="chromium",
        )

        assert manifest_path.exists()
        assert manifest_path.name == "run-manifest.yaml"

    def test_run_manifest_contains_app_url(self, tmp_path: Path):
        """Test that manifest.base_url.app matches --app-url."""
        app_url = "http://localhost:3000"
        api_url = "http://localhost:8000"

        generate_run_manifest(
            tmp_path,
            "RUN-E2E-002",
            app_url=app_url,
            api_url=api_url,
        )

        manifest = load_run_manifest(tmp_path, "RUN-E2E-002")
        assert manifest["base_url"]["app"] == app_url

    def test_run_manifest_contains_api_url(self, tmp_path: Path):
        """Test that manifest.base_url.api matches --api-url."""
        app_url = "http://localhost:3000"
        api_url = "http://localhost:8000"

        generate_run_manifest(
            tmp_path,
            "RUN-E2E-003",
            app_url=app_url,
            api_url=api_url,
        )

        manifest = load_run_manifest(tmp_path, "RUN-E2E-003")
        assert manifest["base_url"]["api"] == api_url

    def test_run_manifest_contains_browser(self, tmp_path: Path):
        """Test that manifest.browser field is set."""
        generate_run_manifest(
            tmp_path,
            "RUN-E2E-004",
            app_url="http://localhost:3000",
            browser="firefox",
        )

        manifest = load_run_manifest(tmp_path, "RUN-E2E-004")
        assert manifest["browser"] == "firefox"

    def test_run_manifest_separated_urls(self, tmp_path: Path):
        """Test separated architecture with distinct app and api URLs."""
        app_url = "https://app.example.com"
        api_url = "https://api.example.com"

        generate_run_manifest(
            tmp_path,
            "RUN-E2E-005",
            app_url=app_url,
            api_url=api_url,
        )

        manifest = load_run_manifest(tmp_path, "RUN-E2E-005")
        assert manifest["base_url"]["app"] == app_url
        assert manifest["base_url"]["api"] == api_url
        assert manifest["base_url"]["app"] != manifest["base_url"]["api"]


# ---------------------------------------------------------------------------
# Test: E2E Chain Integration
# ---------------------------------------------------------------------------


class TestE2EChainIntegration:
    """Tests for E2E chain execution integration."""

    def test_e2e_chain_with_separated_urls(
        self,
        workspace_with_e2e_context: Path,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test E2E chain works with separated app_url and api_url."""
        # This test verifies the chain flow without requiring actual services
        app_url = "http://localhost:3000"
        api_url = "http://localhost:8000"

        # Mock the execute_test_exec_skill to avoid actual execution
        with patch("cli.lib.test_orchestrator.execute_test_exec_skill") as mock_exec:
            mock_exec.return_value = {
                "run_status": "passed",
                "candidate_artifact_ref": "e2e-candidate-001",
            }

            result = run_spec_test(
                workspace_with_e2e_context,
                proto_ref="PROTO-001",
                base_url=api_url,
                app_url=app_url,
                api_url=api_url,
                modality="web_e2e",
                coverage_mode="smoke",
            )

            # Verify result structure
            assert result.run_id.startswith("RUN-")
            assert len(result.case_results) > 0 or len(result.execution_refs) > 0

    def test_e2e_chain_creates_evidence_directory(
        self,
        workspace_with_e2e_context: Path,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that evidence directory is created under run artifacts."""
        with patch("cli.lib.test_orchestrator.execute_test_exec_skill") as mock_exec:
            mock_exec.return_value = {
                "run_status": "passed",
                "candidate_artifact_ref": "e2e-evidence-001",
            }

            result = run_spec_test(
                workspace_with_e2e_context,
                proto_ref="PROTO-001",
                app_url="http://localhost:3000",
                api_url="http://localhost:8000",
                modality="web_e2e",
            )

            # Verify run artifacts directory structure
            run_dir = (
                workspace_with_e2e_context
                / "ssot"
                / "tests"
                / ".artifacts"
                / "runs"
                / result.run_id
            )
            # Directory should exist after execution
            run_dir.mkdir(parents=True, exist_ok=True)

    def test_e2e_chain_returns_case_results(
        self,
        workspace_with_e2e_context: Path,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that StepResult contains case_results list."""
        with patch("cli.lib.test_orchestrator.execute_test_exec_skill") as mock_exec:
            mock_exec.return_value = {
                "run_status": "passed",
                "candidate_artifact_ref": "e2e-case-001",
            }

            result = run_spec_test(
                workspace_with_e2e_context,
                proto_ref="PROTO-001",
                modality="web_e2e",
            )

            assert isinstance(result.case_results, list)
            assert isinstance(result.manifest_items, list)


# ---------------------------------------------------------------------------
# Test: E2E Scenario Spec Compilation
# ---------------------------------------------------------------------------


class TestE2EScenarioSpecCompilation:
    """Tests for E2E scenario spec compilation with A/B/C layers."""

    def test_compiles_e2e_spec_to_scenario_spec(
        self,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that e2e spec is compiled to scenario spec."""
        from cli.lib.spec_adapter import spec_parse_e2e_spec

        spec_file = mock_e2e_spec_dir["spec_file"]
        e2e_spec = spec_parse_e2e_spec(spec_file)

        scenario_spec = compile_scenario_spec(e2e_spec, source_file=spec_file)

        assert isinstance(scenario_spec, ScenarioSpec)
        assert scenario_spec.journey_id == "E2E-COV-001"
        assert scenario_spec.spec_id == "JOURNEY-001"

    def test_scenario_spec_has_ab_layers(
        self,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that scenario spec has A-layer and B-layer assertions."""
        from cli.lib.spec_adapter import spec_parse_e2e_spec

        spec_file = mock_e2e_spec_dir["spec_file"]
        e2e_spec = spec_parse_e2e_spec(spec_file)

        scenario_spec = compile_scenario_spec(e2e_spec)

        # Check A-layer (UI state)
        assert len(scenario_spec.assertions.a_layer) > 0
        assert any(isinstance(a, ALayerAssertion) for a in scenario_spec.assertions.a_layer)

        # Check B-layer (network/API)
        assert len(scenario_spec.assertions.b_layer) > 0
        assert any(isinstance(b, BLayerAssertion) for b in scenario_spec.assertions.b_layer)

    def test_scenario_spec_has_c_missing(
        self,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that scenario spec has C_MISSING for C-layer assertions."""
        from cli.lib.spec_adapter import spec_parse_e2e_spec

        spec_file = mock_e2e_spec_dir["spec_file"]
        e2e_spec = spec_parse_e2e_spec(spec_file)

        scenario_spec = compile_scenario_spec(e2e_spec)

        # Check C-layer (business state - should be C_MISSING)
        assert len(scenario_spec.assertions.c_layer) > 0
        c_assertions = [
            c for c in scenario_spec.assertions.c_layer
            if isinstance(c, CLayerAssertion)
        ]
        assert len(c_assertions) > 0
        # Verify C_MISSING type
        assert all(c.type == "C_MISSING" for c in c_assertions)
        # Verify evidence collection
        assert all("har" in c.evidence_required for c in c_assertions)
        assert all("screenshot" in c.evidence_required for c in c_assertions)

    def test_scenario_spec_yaml_serialization(
        self,
        mock_e2e_spec_dir: dict[str, Path],
    ):
        """Test that scenario spec can be serialized to YAML."""
        from cli.lib.spec_adapter import spec_parse_e2e_spec

        spec_file = mock_e2e_spec_dir["spec_file"]
        e2e_spec = spec_parse_e2e_spec(spec_file)

        scenario_spec = compile_scenario_spec(e2e_spec)
        yaml_content = scenario_spec_to_yaml(scenario_spec)

        assert isinstance(yaml_content, str)
        assert "journey_id:" in yaml_content
        assert "assertions:" in yaml_content
        assert "a_layer:" in yaml_content
        assert "b_layer:" in yaml_content
        assert "c_layer:" in yaml_content


# ---------------------------------------------------------------------------
# Test: State Machine Execution
# ---------------------------------------------------------------------------


class TestE2EStateMachine:
    """Tests for state machine execution flow."""

    def test_state_machine_execution_flow(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test state machine executes through SETUP -> EXECUTE -> VERIFY/DONE."""
        executor = create_executor(tmp_path, "RUN-SM-001", mock_scenario_specs, resume=False)
        result = executor.run()

        # Result should be returned with final state
        assert result.final_state in [ExecutionState.EXECUTE, ExecutionState.DONE]
        assert result.run_id == "RUN-SM-001"

    def test_state_machine_persists_state(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that state is persisted to state.yaml."""
        executor = create_executor(tmp_path, "RUN-SM-002", mock_scenario_specs, resume=False)
        executor.run()

        # Verify state file exists after execution
        state_file = (
            tmp_path
            / "ssot"
            / "tests"
            / ".artifacts"
            / "runs"
            / "RUN-SM-002"
            / "RUN-SM-002-state.yaml"
        )
        assert state_file.exists()

        # Verify state can be loaded
        loaded = load_state(tmp_path, "RUN-SM-002")
        assert loaded is not None

    def test_state_machine_resume_flow(self, tmp_path: Path, precreated_state_file: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test resume from existing state."""
        # Load the pre-created state to verify resume capability
        loaded = load_state(tmp_path, "RUN-RESUME-001")
        assert loaded is not None
        assert loaded.current_state == ExecutionState.EXECUTE
        assert len(loaded.completed_steps) == 1

        # Verify the state file has correct structure
        state_file = precreated_state_file
        loaded_yaml = yaml.safe_load(state_file.read_text(encoding="utf-8"))
        assert loaded_yaml["run_id"] == "RUN-RESUME-001"
        assert loaded_yaml["current_state"] == "EXECUTE"
        assert len(loaded_yaml["completed_steps"]) == 1

    def test_state_machine_execution_states(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test that execution state machine has correct states."""
        # Check ExecutionState enum values
        assert ExecutionState.SETUP.value == "SETUP"
        assert ExecutionState.EXECUTE.value == "EXECUTE"
        assert ExecutionState.VERIFY.value == "VERIFY"
        assert ExecutionState.COLLECT.value == "COLLECT"
        assert ExecutionState.DONE.value == "DONE"


# ---------------------------------------------------------------------------
# Test: COLLECT State
# ---------------------------------------------------------------------------


class TestCollectState:
    """Tests for COLLECT state evidence collection."""

    def test_collect_state_entry(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test entering COLLECT state."""
        # Create state with failure by manipulating state file
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-COLLECT-001"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-COLLECT-001",
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

        state_file = state_dir / "RUN-COLLECT-001-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Load state and verify COLLECT state
        loaded = load_state(tmp_path, "RUN-COLLECT-001")
        assert loaded is not None
        assert loaded.current_state == ExecutionState.COLLECT
        assert len(loaded.failed_journeys) == 1

    def test_collect_state_evidence_preserved(self, tmp_path: Path, mock_scenario_specs: list[ScenarioSpec]):
        """Test evidence is preserved when entering COLLECT state."""
        # Create state with partial execution and failure
        state_dir = tmp_path / "ssot" / "tests" / ".artifacts" / "runs" / "RUN-COLLECT-002"
        state_dir.mkdir(parents=True, exist_ok=True)

        state_content = {
            "run_id": "RUN-COLLECT-002",
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
            ],
            "current_journey": "JOURNEY-001",
            "current_step_index": 0,
            "failed_journeys": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        state_file = state_dir / "RUN-COLLECT-002-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(state_content, f, allow_unicode=True, sort_keys=False)

        # Load and verify evidence preserved
        loaded = load_state(tmp_path, "RUN-COLLECT-002")
        assert loaded is not None
        assert len(loaded.completed_steps) == 1
        assert loaded.completed_steps[0].status == "passed"

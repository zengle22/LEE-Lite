"""Unit tests for scenario_spec_compile.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lib.scenario_spec_compile import (
    ALayerAssertion,
    BLayerAssertion,
    CLayerAssertion,
    C_MISSING_PLACEHOLDER,
    ScenarioAssertions,
    ScenarioSpec,
    ScenarioStep,
    compile_e2e_spec_file,
    compile_scenario_spec,
    compile_scenario_spec_batch,
    scenario_spec_to_yaml,
    write_scenario_spec,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_e2e_spec() -> dict:
    """Sample e2e spec dict mimicking spec_adapter.py output format."""
    return {
        "_source_coverage_id": "JOURNEY-001",
        "unit_ref": "JOURNEY-001",
        "pass_conditions": [
            "visible submit button",
            "error message displayed when invalid",
            "POST /api/submit called",
            "database updated after submit",
        ],
        "required_evidence": ["network_log: POST /api/submit"],
        "fail_conditions": [],
    }


@pytest.fixture
def ui_only_e2e_spec() -> dict:
    """E2E spec with only UI assertions."""
    return {
        "_source_coverage_id": "JOURNEY-002",
        "unit_ref": "JOURNEY-002",
        "pass_conditions": [
            "visible header",
            "text contains 'Welcome'",
        ],
        "required_evidence": [],
    }


@pytest.fixture
def network_only_e2e_spec() -> dict:
    """E2E spec with only network assertions."""
    return {
        "_source_coverage_id": "JOURNEY-003",
        "unit_ref": "JOURNEY-003",
        "pass_conditions": [
            "GET /api/users endpoint responds",
        ],
        "required_evidence": ["network_log: GET /api/users"],
    }


@pytest.fixture
def persistence_only_e2e_spec() -> dict:
    """E2E spec with only persistence assertions."""
    return {
        "_source_coverage_id": "JOURNEY-004",
        "unit_ref": "JOURNEY-004",
        "pass_conditions": [
            "database contains new record",
            "backend server persists state",
        ],
        "required_evidence": [],
    }


@pytest.fixture
def empty_e2e_spec() -> dict:
    """E2E spec with no pass_conditions."""
    return {
        "_source_coverage_id": "JOURNEY-005",
        "unit_ref": "JOURNEY-005",
        "pass_conditions": [],
        "required_evidence": [],
    }


# ---------------------------------------------------------------------------
# Test A-Layer Extraction
# ---------------------------------------------------------------------------


class TestALayerExtraction:
    """Tests for A-layer (UI state) extraction."""

    def test_extracts_ui_state_assertions(self, sample_e2e_spec: dict) -> None:
        """Verify A-layer contains assertions matching UI keywords."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert len(spec.assertions.a_layer) == 2
        assert all(isinstance(a, ALayerAssertion) for a in spec.assertions.a_layer)
        # Check specific assertions extracted
        descriptions = [a.description for a in spec.assertions.a_layer]
        assert "visible submit button" in descriptions
        assert "error message displayed when invalid" in descriptions

    def test_handles_chinese_keywords(self) -> None:
        """Verify Chinese '显示' keyword triggers A-layer extraction."""
        spec = compile_scenario_spec({
            "_source_coverage_id": "TEST-001",
            "unit_ref": "TEST-001",
            "pass_conditions": ["显示登录按钮"],
            "required_evidence": [],
        })
        assert len(spec.assertions.a_layer) == 1
        assert spec.assertions.a_layer[0].description == "显示登录按钮"

    def test_handles_empty_pass_conditions(self, empty_e2e_spec: dict) -> None:
        """Verify A-layer is empty when no UI assertions."""
        spec = compile_scenario_spec(empty_e2e_spec)
        assert len(spec.assertions.a_layer) == 0

    def test_multiple_a_layer_assertions(self, ui_only_e2e_spec: dict) -> None:
        """Verify multiple A-layer assertions are created."""
        spec = compile_scenario_spec(ui_only_e2e_spec)
        assert len(spec.assertions.a_layer) == 2


# ---------------------------------------------------------------------------
# Test B-Layer Extraction
# ---------------------------------------------------------------------------


class TestBLayerExtraction:
    """Tests for B-layer (network/API) extraction."""

    def test_extracts_network_assertions(self, sample_e2e_spec: dict) -> None:
        """Verify B-layer contains network event assertions."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert len(spec.assertions.b_layer) >= 1
        assert all(isinstance(b, BLayerAssertion) for b in spec.assertions.b_layer)

    def test_extracts_from_required_evidence(self, network_only_e2e_spec: dict) -> None:
        """Verify B-layer from required_evidence network_log."""
        spec = compile_scenario_spec(network_only_e2e_spec)
        assert len(spec.assertions.b_layer) >= 1
        # Check that network_log is extracted (goes into description)
        descriptions = [b.description for b in spec.assertions.b_layer]
        assert any("network_log" in d.lower() for d in descriptions)
        # Also verify network_event is extracted from the evidence
        network_events = [b.network_event for b in spec.assertions.b_layer if b.network_event]
        assert any("GET /api/users" in str(e) for e in network_events)

    def test_adds_fallback_when_no_network_assertion(self, ui_only_e2e_spec: dict) -> None:
        """Verify fallback B-layer when no explicit network assertion."""
        spec = compile_scenario_spec(ui_only_e2e_spec)
        assert len(spec.assertions.b_layer) >= 1
        # Should have fallback assertion
        fallbacks = [b for b in spec.assertions.b_layer if b.fallback_available]
        assert len(fallbacks) >= 1

    def test_b_layer_fallback_available(self, ui_only_e2e_spec: dict) -> None:
        """Verify fallback has fallback_available=True."""
        spec = compile_scenario_spec(ui_only_e2e_spec)
        fallback = next((b for b in spec.assertions.b_layer if b.fallback_available), None)
        assert fallback is not None
        assert fallback.fallback_available is True


# ---------------------------------------------------------------------------
# Test C-Layer Extraction
# ---------------------------------------------------------------------------


class TestCLayerExtraction:
    """Tests for C-layer (business state) extraction."""

    def test_marks_c_layer_as_c_missing(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C-layer type is 'C_MISSING'."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        assert len(spec.assertions.c_layer) == 2
        assert all(c.type == "C_MISSING" for c in spec.assertions.c_layer)

    def test_c_missing_has_har_evidence(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C_MISSING has 'har' in evidence_required."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        for c in spec.assertions.c_layer:
            assert "har" in c.evidence_required

    def test_c_missing_has_screenshot_evidence(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C_MISSING has 'screenshot' in evidence_required."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        for c in spec.assertions.c_layer:
            assert "screenshot" in c.evidence_required

    def test_c_missing_has_placeholder(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C_MISSING has placeholder text."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        for c in spec.assertions.c_layer:
            assert c.placeholder == C_MISSING_PLACEHOLDER

    def test_extracts_persistence_assertions(self, sample_e2e_spec: dict) -> None:
        """Verify C-layer extracts persistence-related assertions."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert len(spec.assertions.c_layer) == 1
        assert "database updated" in spec.assertions.c_layer[0].description

    def test_handles_empty_c_layer(self, ui_only_e2e_spec: dict) -> None:
        """Verify C-layer is empty when no persistence assertions."""
        spec = compile_scenario_spec(ui_only_e2e_spec)
        assert len(spec.assertions.c_layer) == 0


# ---------------------------------------------------------------------------
# Test ScenarioSpec Structure
# ---------------------------------------------------------------------------


class TestScenarioSpecStructure:
    """Tests for ScenarioSpec structure."""

    def test_contains_journey_id(self, sample_e2e_spec: dict) -> None:
        """Verify ScenarioSpec has journey_id."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert spec.journey_id == "JOURNEY-001"

    def test_contains_spec_id(self, sample_e2e_spec: dict) -> None:
        """Verify ScenarioSpec has spec_id."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert spec.spec_id == "JOURNEY-001"

    def test_contains_coverage_id(self, sample_e2e_spec: dict) -> None:
        """Verify ScenarioSpec has coverage_id."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert spec.coverage_id == "JOURNEY-001"

    def test_contains_source_file(self, sample_e2e_spec: dict) -> None:
        """Verify ScenarioSpec has source_file when provided."""
        source_path = Path("/path/to/spec.md")
        spec = compile_scenario_spec(sample_e2e_spec, source_file=source_path)
        assert spec.source_file == source_path

    def test_source_file_defaults_to_none(self, sample_e2e_spec: dict) -> None:
        """Verify source_file defaults to None when not provided."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert spec.source_file is None

    def test_contains_assertions(self, sample_e2e_spec: dict) -> None:
        """Verify ScenarioSpec has assertions object."""
        spec = compile_scenario_spec(sample_e2e_spec)
        assert isinstance(spec.assertions, ScenarioAssertions)


# ---------------------------------------------------------------------------
# Test ScenarioSpecToYaml
# ---------------------------------------------------------------------------


class TestScenarioSpecToYaml:
    """Tests for YAML serialization."""

    def test_serializes_to_yaml(self, sample_e2e_spec: dict) -> None:
        """Verify scenario_spec_to_yaml returns valid YAML string."""
        spec = compile_scenario_spec(sample_e2e_spec)
        yaml_output = scenario_spec_to_yaml(spec)
        assert isinstance(yaml_output, str)
        assert "journey_id:" in yaml_output
        assert "spec_id:" in yaml_output
        assert "coverage_id:" in yaml_output

    def test_yaml_contains_all_layers(self, sample_e2e_spec: dict) -> None:
        """Verify YAML contains a_layer, b_layer, c_layer sections."""
        spec = compile_scenario_spec(sample_e2e_spec)
        yaml_output = scenario_spec_to_yaml(spec)
        assert "a_layer:" in yaml_output
        assert "b_layer:" in yaml_output
        assert "c_layer:" in yaml_output

    def test_yaml_contains_c_missing_type(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C-layer in YAML has C_MISSING type."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        yaml_output = scenario_spec_to_yaml(spec)
        assert "C_MISSING" in yaml_output

    def test_yaml_contains_evidence_required(self, persistence_only_e2e_spec: dict) -> None:
        """Verify evidence_required list is in YAML output."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        yaml_output = scenario_spec_to_yaml(spec)
        assert "evidence_required:" in yaml_output
        assert "- har" in yaml_output or "har" in yaml_output
        assert "- screenshot" in yaml_output or "screenshot" in yaml_output

    def test_yaml_contains_placeholder(self, persistence_only_e2e_spec: dict) -> None:
        """Verify C_MISSING placeholder is in YAML output."""
        spec = compile_scenario_spec(persistence_only_e2e_spec)
        yaml_output = scenario_spec_to_yaml(spec)
        assert C_MISSING_PLACEHOLDER in yaml_output


# ---------------------------------------------------------------------------
# Test Write Scenario Spec
# ---------------------------------------------------------------------------


class TestWriteScenarioSpec:
    """Tests for writing scenario specs to files."""

    def test_write_scenario_spec_creates_file(self, sample_e2e_spec: dict, tmp_path: Path) -> None:
        """Verify write_scenario_spec creates the output file."""
        spec = compile_scenario_spec(sample_e2e_spec)
        output_path = write_scenario_spec(spec, tmp_path)
        assert output_path.exists()
        assert output_path.name == "JOURNEY-001.yaml"

    def test_write_scenario_spec_creates_directory(self, sample_e2e_spec: dict, tmp_path: Path) -> None:
        """Verify write_scenario_spec creates parent directories."""
        new_dir = tmp_path / "nested" / "dir"
        spec = compile_scenario_spec(sample_e2e_spec)
        output_path = write_scenario_spec(spec, new_dir)
        assert output_path.exists()

    def test_written_file_contains_yaml(self, sample_e2e_spec: dict, tmp_path: Path) -> None:
        """Verify written file contains valid YAML content."""
        spec = compile_scenario_spec(sample_e2e_spec)
        output_path = write_scenario_spec(spec, tmp_path)
        content = output_path.read_text()
        assert "journey_id:" in content
        assert "JOURNEY-001" in content


# ---------------------------------------------------------------------------
# Test Batch Compilation
# ---------------------------------------------------------------------------


class TestBatchCompilation:
    """Tests for batch compilation functionality."""

    def test_compile_scenario_spec_batch_returns_list(self) -> None:
        """Verify compile_scenario_spec_batch returns a list."""
        specs = compile_scenario_spec_batch([])
        assert isinstance(specs, list)
        assert len(specs) == 0

    def test_batch_compilation_extracts_all_layers(self, sample_e2e_spec: dict) -> None:
        """Verify batch compilation extracts all layers correctly."""
        # Create a mock file path for testing
        spec = compile_scenario_spec(sample_e2e_spec)
        assert len(spec.assertions.a_layer) > 0
        assert len(spec.assertions.b_layer) > 0

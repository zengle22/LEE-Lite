"""Scenario spec compiler: converts e2e-journey-spec markdown to scenario specs with A/B/C layer separation.

Per D-03/D-04, C-layer assertions are marked C_MISSING with placeholder + HAR + screenshot evidence collection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from cli.lib.spec_adapter import spec_parse_e2e_spec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_MISSING_PLACEHOLDER = "C_MISSING: Business state verification pending"

# Keywords for A-layer (UI state) extraction
A_LAYER_KEYWORDS = ["visible", "显示", "show", "display", "text", "contain", "have", "element"]

# Keywords for B-layer (network/API) extraction
B_LAYER_KEYWORDS = ["api", "network", "request", "response", "http", "/api/"]

# Keywords for C-layer (persistence/business state) extraction
C_LAYER_KEYWORDS = ["persistence", "persist", "database", "db", "backend", "server"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ALayerAssertion:
    """UI state assertions (visible elements, text, etc.)"""

    description: str
    source_step: str | None = None


@dataclass
class BLayerAssertion:
    """Network/API assertions with fallback handling"""

    description: str
    network_event: str | None = None
    fallback_available: bool = False
    fallback_description: str | None = None


@dataclass
class CLayerAssertion:
    """Business state assertions (marked C_MISSING)"""

    description: str
    type: Literal["C_MISSING"] = "C_MISSING"
    evidence_required: list[str] = field(default_factory=lambda: ["har", "screenshot"])
    placeholder: str = C_MISSING_PLACEHOLDER


@dataclass
class ScenarioStep:
    """Single step in a scenario"""

    step_index: int
    action: str
    target: str | None = None
    target_format: str | None = None
    value: str | None = None


@dataclass
class ScenarioAssertions:
    """All assertion layers for a scenario"""

    a_layer: list[ALayerAssertion] = field(default_factory=list)
    b_layer: list[BLayerAssertion] = field(default_factory=list)
    c_layer: list[CLayerAssertion] = field(default_factory=list)


@dataclass
class ScenarioSpec:
    """Compiled scenario spec with A/B/C layers"""

    journey_id: str
    spec_id: str
    coverage_id: str
    steps: list[ScenarioStep] = field(default_factory=list)
    assertions: ScenarioAssertions = field(default_factory=ScenarioAssertions)
    source_file: Path | None = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _matches_any_keyword(text: str, keywords: list[str]) -> bool:
    """Check if text matches any of the given keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def _extract_a_layer(pass_conditions: list[str]) -> list[ALayerAssertion]:
    """Extract A-layer assertions from pass_conditions based on UI keywords."""
    assertions: list[ALayerAssertion] = []
    for condition in pass_conditions:
        if _matches_any_keyword(condition, A_LAYER_KEYWORDS):
            assertions.append(ALayerAssertion(description=condition))
    return assertions


def _extract_b_layer(
    pass_conditions: list[str], required_evidence: list[str]
) -> list[BLayerAssertion]:
    """Extract B-layer assertions from pass_conditions and required_evidence.

    If no explicit network assertion is found, adds a fallback B-layer assertion.
    """
    assertions: list[BLayerAssertion] = []

    # Extract from pass_conditions with network keywords
    for condition in pass_conditions:
        if _matches_any_keyword(condition, B_LAYER_KEYWORDS):
            # Try to extract network event from the condition
            network_event = None
            if "/api/" in condition.lower():
                # Extract the API endpoint
                import re

                match = re.search(r"(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s,\]]+)", condition, re.I)
                if match:
                    network_event = f"{match.group(1)} {match.group(2)}"
                else:
                    # Try to find just the path
                    match = re.search(r"(/api/[^\s,\]]+)", condition, re.I)
                    if match:
                        network_event = match.group(1)

            assertions.append(BLayerAssertion(description=condition, network_event=network_event))

    # Extract from required_evidence containing network_log
    for evidence in required_evidence:
        if "network_log" in evidence.lower():
            assertions.append(
                BLayerAssertion(
                    description=f"Network: {evidence}",
                    network_event=evidence.replace("network_log:", "").strip(),
                )
            )

    # Add fallback if no network assertion found
    if not assertions:
        assertions.append(
            BLayerAssertion(
                description="Network verification required",
                fallback_available=True,
                fallback_description="Add explicit network/API assertion or rely on HAR capture",
            )
        )

    return assertions


def _extract_c_layer(pass_conditions: list[str]) -> list[CLayerAssertion]:
    """Extract C-layer assertions from pass_conditions based on persistence keywords.

    Per D-03: C-layer assertions MUST be marked C_MISSING.
    Per D-04: C_MISSING placeholders MUST collect HAR + screenshot evidence.
    """
    assertions: list[CLayerAssertion] = []
    for condition in pass_conditions:
        if _matches_any_keyword(condition, C_LAYER_KEYWORDS):
            assertions.append(
                CLayerAssertion(
                    type="C_MISSING",
                    description=condition,
                    evidence_required=["har", "screenshot"],
                    placeholder=C_MISSING_PLACEHOLDER,
                )
            )
    return assertions


def _scenario_spec_to_dict(spec: ScenarioSpec) -> dict[str, Any]:
    """Convert ScenarioSpec to a dictionary for YAML serialization."""
    result: dict[str, Any] = {
        "journey_id": spec.journey_id,
        "spec_id": spec.spec_id,
        "coverage_id": spec.coverage_id,
    }

    # Add steps if present
    if spec.steps:
        result["steps"] = [
            {
                "step_index": s.step_index,
                "action": s.action,
                "target": s.target,
                "target_format": s.target_format,
                "value": s.value,
            }
            for s in spec.steps
        ]

    # Add assertions with A/B/C layer separation
    result["assertions"] = {
        "a_layer": [
            {"description": a.description, "source_step": a.source_step}
            for a in spec.assertions.a_layer
        ],
        "b_layer": [
            {
                "description": b.description,
                "network_event": b.network_event,
                "fallback_available": b.fallback_available,
                "fallback_description": b.fallback_description,
            }
            for b in spec.assertions.b_layer
        ],
        "c_layer": [
            {
                "type": c.type,
                "description": c.description,
                "evidence_required": c.evidence_required,
                "placeholder": c.placeholder,
            }
            for c in spec.assertions.c_layer
        ],
    }

    # Add source_file if present
    if spec.source_file:
        result["source_file"] = str(spec.source_file)

    return result


# ---------------------------------------------------------------------------
# Main compilation functions
# ---------------------------------------------------------------------------


def compile_scenario_spec(
    e2e_spec: dict[str, Any], source_file: Path | None = None
) -> ScenarioSpec:
    """Compile an e2e spec dict into a ScenarioSpec with A/B/C layer separation.

    Args:
        e2e_spec: Parsed e2e spec dict from spec_parse_e2e_spec
        source_file: Optional source file path for traceability

    Returns:
        ScenarioSpec with extracted A/B/C layer assertions
    """
    # Extract identifiers
    journey_id = e2e_spec.get("_source_coverage_id", e2e_spec.get("unit_ref", ""))
    spec_id = e2e_spec.get("unit_ref", "")
    coverage_id = e2e_spec.get("_source_coverage_id", "")

    # Extract pass_conditions and required_evidence
    pass_conditions = e2e_spec.get("pass_conditions", [])
    required_evidence = e2e_spec.get("required_evidence", [])

    # Build assertion layers
    a_layer = _extract_a_layer(pass_conditions)
    b_layer = _extract_b_layer(pass_conditions, required_evidence)
    c_layer = _extract_c_layer(pass_conditions)

    assertions = ScenarioAssertions(a_layer=a_layer, b_layer=b_layer, c_layer=c_layer)

    return ScenarioSpec(
        journey_id=journey_id,
        spec_id=spec_id,
        coverage_id=coverage_id,
        assertions=assertions,
        source_file=source_file,
    )


def compile_e2e_spec_file(spec_path: Path) -> ScenarioSpec:
    """Compile a single e2e spec file into a ScenarioSpec.

    Args:
        spec_path: Path to the e2e-journey-spec markdown file

    Returns:
        ScenarioSpec with A/B/C layer separation
    """
    e2e_spec = spec_parse_e2e_spec(spec_path)
    return compile_scenario_spec(e2e_spec, source_file=spec_path)


def compile_scenario_spec_batch(spec_paths: list[Path]) -> list[ScenarioSpec]:
    """Compile multiple e2e spec files into ScenarioSpecs.

    Args:
        spec_paths: List of paths to e2e-journey-spec markdown files

    Returns:
        List of ScenarioSpecs
    """
    return [compile_e2e_spec_file(path) for path in spec_paths]


def scenario_spec_to_yaml(spec: ScenarioSpec) -> str:
    """Convert a ScenarioSpec to a YAML string.

    Args:
        spec: The ScenarioSpec to serialize

    Returns:
        YAML string representation
    """
    spec_dict = _scenario_spec_to_dict(spec)
    return yaml.safe_dump(spec_dict, allow_unicode=True, sort_keys=False, default_flow_style=False)


def write_scenario_spec(spec: ScenarioSpec, output_dir: Path) -> Path:
    """Write a ScenarioSpec to a YAML file.

    Args:
        spec: The ScenarioSpec to write
        output_dir: Directory to write the YAML file

    Returns:
        Path to the written file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{spec.journey_id}.yaml"
    yaml_content = scenario_spec_to_yaml(spec)

    with output_path.open("w", encoding="utf-8") as f:
        f.write(yaml_content)

    return output_path

"""Integration tests for FRZ→FEAT extraction logic.

Tests for Plan 08-04 Task 2: epic_to_feat_extract module.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

import sys

# Ensure the scripts directory is on the path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure workspace root is on the path for cli.lib imports
WORKSPACE_ROOT = SCRIPTS_DIR.parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from epic_to_feat_extract import (
    FeatExtractResult,
    build_feat_from_frz,
    extract_feat_from_frz_logic,
)
from cli.lib.errors import CommandError
from cli.lib.frz_schema import (
    FRZPackage,
    CoreJourney,
    DomainEntity,
    StateMachine,
    AcceptanceContract,
    KnownUnknown,
    FRZEvidence,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_minimal_frz() -> FRZPackage:
    """Create a minimal FRZPackage with one item per dimension."""
    return FRZPackage(
        artifact_type="frz_package",
        frz_id="FRZ-001",
        status="frozen",
        product_boundary=None,
        core_journeys=[
            CoreJourney(
                id="JRN-001",
                name="User Login",
                steps=["Navigate to login", "Enter credentials", "Submit form"],
            ),
        ],
        domain_model=[
            DomainEntity(
                id="ENT-001",
                name="User Account",
                contract={"fields": ["id", "email", "name"]},
            ),
        ],
        state_machine=[
            StateMachine(
                id="SM-001",
                name="Account Lifecycle",
                states=["draft", "active", "suspended", "closed"],
                transitions=[
                    {"from": "draft", "to": "active", "event": "activate"},
                    {"from": "active", "to": "suspended", "event": "suspend"},
                ],
            ),
        ],
        acceptance_contract=AcceptanceContract(
            expected_outcomes=["FC-001: User can log in successfully", "FC-002: Invalid credentials rejected"],
            acceptance_impact=["Login flow must be tested end-to-end"],
        ),
        constraints=["Must support OAuth2", "Session timeout 30 minutes"],
        derived_allowed=[
            "bundle_intent", "features", "product_objects_and_deliverables",
            "business_flow", "acceptance_criteria", "constraints", "non_decisions",
            "source_refs",
        ],
        known_unknowns=[
            KnownUnknown(
                id="UNK-001",
                topic="Password reset flow scope",
                status="open",
                owner="product-team",
                expires_in="3 cycles",
            ),
        ],
        evidence=FRZEvidence(
            source_refs=["prd::login-v2", "ux::wireframes-v3"],
        ),
    )


def _make_epic_package() -> dict[str, Any]:
    """Create a minimal EPIC package dict."""
    return {
        "epic_freeze_ref": "EPIC-001",
        "src_root_id": "SRC-001",
    }


def _make_multi_item_frz() -> FRZPackage:
    """FRZ with multiple items per dimension."""
    return FRZPackage(
        frz_id="FRZ-002",
        status="frozen",
        core_journeys=[
            CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"]),
            CoreJourney(id="JRN-002", name="Register", steps=["step1", "step2", "step3"]),
            CoreJourney(id="JRN-003", name="Logout", steps=["step1"]),
        ],
        domain_model=[
            DomainEntity(id="ENT-001", name="User", contract={"fields": ["id"]}),
            DomainEntity(id="ENT-002", name="Session", contract={"fields": ["token"]}),
        ],
        state_machine=[
            StateMachine(id="SM-001", name="Auth", states=["on", "off"], transitions=[]),
            StateMachine(id="SM-002", name="Session", states=["active", "expired"], transitions=[]),
        ],
        acceptance_contract=AcceptanceContract(
            expected_outcomes=["FC-001: Auth works", "FC-002: Session valid"],
            acceptance_impact=["Must pass E2E"],
        ),
        derived_allowed=["bundle_intent", "features", "source_refs"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFeatExtractResult:
    """Test FeatExtractResult dataclass."""

    def test_dataclass_is_frozen(self):
        result = FeatExtractResult(
            ok=True,
            frz_id="FRZ-001",
            feat_payload={},
            anchors_registered=[],
            drift_results=[],
            guard_verdict="pass",
        )
        with pytest.raises(Exception):
            result.ok = False


class TestBuildFeatFromFrz:
    """Test build_feat_from_frz rule-template mapping."""

    def test_mapping_correctness_single_item(self):
        """Features contain JRN-001 journey info, product_behavior_slices contain SM-001."""
        frz = _make_minimal_frz()
        epic = _make_epic_package()

        payload = build_feat_from_frz(frz, epic, "FRZ-001")

        # Features contain JRN-001
        features = payload["features"]
        assert len(features) >= 1
        assert any("JRN-001" in str(f) for f in features)

        # product_behavior_slices contain SM-001
        slices = payload["product_behavior_slices"]
        assert len(slices) >= 1
        assert any("SM-001" in str(s) for s in slices)

        # constraints_and_dependencies from FRZ constraints
        constraints = payload["constraints_and_dependencies"]
        assert "Must support OAuth2" in constraints
        assert "Session timeout 30 minutes" in constraints

        # source_refs contains "frz::FRZ-001" and epic_freeze_ref
        source_refs = payload["source_refs"]
        assert "frz::FRZ-001" in source_refs
        assert "EPIC-001" in source_refs

        # bundle_shared_non_goals from open known_unknowns
        non_decisions = payload["bundle_shared_non_goals"]
        assert any("UNK-001" in str(nd) or "Password reset" in str(nd) for nd in non_decisions)

    def test_mapping_multiple_items(self):
        """All items appear in FEAT payload."""
        frz = _make_multi_item_frz()
        epic = _make_epic_package()

        payload = build_feat_from_frz(frz, epic, "FRZ-002")

        # All 3 journeys appear
        features = payload["features"]
        assert any("JRN-001" in str(f) for f in features)
        assert any("JRN-002" in str(f) for f in features)
        assert any("JRN-003" in str(f) for f in features)

        # All 2 entities appear
        slices = payload.get("product_objects_and_deliverables", [])
        assert any("ENT-001" in str(s) for s in slices) or any("ENT-001" in str(features))

        # Both state machines appear
        behavior_slices = payload["product_behavior_slices"]
        assert any("SM-001" in str(s) for s in behavior_slices)
        assert any("SM-002" in str(s) for s in behavior_slices)

    def test_payload_structure(self):
        """FEAT payload has expected top-level keys."""
        frz = _make_minimal_frz()
        epic = _make_epic_package()

        payload = build_feat_from_frz(frz, epic, "FRZ-001")

        assert payload["artifact_type"] == "feat_freeze_package"
        assert payload["workflow_key"] == "product.epic-to-feat.extract"
        assert payload["workflow_run_id"] == "extract-FRZ-001"
        assert payload["status"] == "extracted"
        assert payload["schema_version"] == "1.0.0"
        assert payload["epic_freeze_ref"] == "EPIC-001"
        assert payload["src_root_id"] == "SRC-001"

    def test_source_refs_with_missing_epic_freeze_ref(self):
        """source_refs falls back to frz::{frz_id} when epic_package lacks epic_freeze_ref."""
        frz = _make_minimal_frz()
        epic: dict[str, Any] = {}

        payload = build_feat_from_frz(frz, epic, "FRZ-001")

        source_refs = payload["source_refs"]
        assert "frz::FRZ-001" in source_refs


class TestExtractFeatFromFrzLogic:
    """Test extract_feat_from_frz_logic with anchor registration."""

    def test_anchor_inheritance(self):
        """Anchors registered with projection_path=FEAT, registry YAML verified."""
        frz = _make_minimal_frz()
        epic = _make_epic_package()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            result = extract_feat_from_frz_logic(frz, epic, "FRZ-001", repo_root)

            # JRN-001, ENT-001, SM-001, FC-001, UNK-001 should be registered
            anchors = result.anchors_registered
            assert "JRN-001" in anchors
            assert "ENT-001" in anchors
            assert "SM-001" in anchors
            assert "UNK-001" in anchors

            # Verify registry YAML on disk has projection_path="FEAT"
            registry_path = repo_root / "ssot" / "registry" / "anchor_registry.yaml"
            assert registry_path.exists()
            content = registry_path.read_text()
            assert "FEAT" in content

    def test_empty_frz_dimensions(self):
        """FEAT payload has empty lists but is still valid; warnings non-empty."""
        from cli.lib.frz_schema import FRZPackage

        empty_frz = FRZPackage(
            frz_id="FRZ-EMPTY",
            status="frozen",
            core_journeys=[],
            domain_model=[],
            state_machine=[],
            acceptance_contract=None,
            derived_allowed=[
                "bundle_intent", "features", "product_objects_and_deliverables",
                "product_behavior_slices", "frozen_downstream_boundaries",
                "acceptance_criteria", "constraints_and_dependencies",
                "bundle_shared_non_goals", "source_refs",
            ],
        )
        epic = _make_epic_package()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            result = extract_feat_from_frz_logic(empty_frz, epic, "FRZ-EMPTY", repo_root)

            assert result.ok is True
            assert len(result.feat_payload["features"]) == 0
            assert len(result.feat_payload["product_behavior_slices"]) == 0
            assert len(result.warnings) > 0

    def test_result_fields(self):
        """FeatExtractResult has all required fields populated."""
        frz = _make_minimal_frz()
        epic = _make_epic_package()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            result = extract_feat_from_frz_logic(frz, epic, "FRZ-001", repo_root)

            assert isinstance(result, FeatExtractResult)
            assert result.frz_id == "FRZ-001"
            assert isinstance(result.feat_payload, dict)
            assert isinstance(result.anchors_registered, list)
            assert isinstance(result.drift_results, list)
            assert result.guard_verdict in ("pass", "block")


class TestGuardProjection:
    """Test that guard blocks non-derived fields."""

    def test_guard_blocks_non_derived(self):
        """Extra field not in derived_allowed causes block verdict."""
        frz = _make_minimal_frz()
        epic = _make_epic_package()

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Temporarily restrict derived_allowed to force guard block
            restricted_frz = FRZPackage(
                frz_id="FRZ-001",
                status="frozen",
                core_journeys=frz.core_journeys,
                domain_model=frz.domain_model,
                state_machine=frz.state_machine,
                acceptance_contract=frz.acceptance_contract,
                constraints=frz.constraints,
                known_unknowns=frz.known_unknowns,
                evidence=frz.evidence,
                # Only allow specific fields - everything else will be blocked
                derived_allowed=[],
            )

            result = extract_feat_from_frz_logic(restricted_frz, epic, "FRZ-001", repo_root)

            assert result.guard_verdict == "block"
            assert result.ok is False

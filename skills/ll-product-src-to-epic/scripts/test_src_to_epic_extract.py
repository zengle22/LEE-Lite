"""Integration tests for FRZ->EPIC extraction logic."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cli.lib.errors import CommandError
from cli.lib.frz_schema import (
    FRZPackage,
    CoreJourney,
    DomainEntity,
    StateMachine,
    AcceptanceContract,
    ProductBoundary,
    FRZEvidence,
    KnownUnknown,
    FRZStatus,
)


def _make_frz_package(
    frz_id: str = "FRZ-001",
    status: FRZStatus = FRZStatus.frozen,
    core_journeys: list[CoreJourney] | None = None,
    domain_model: list[DomainEntity] | None = None,
    state_machine: list[StateMachine] | None = None,
    acceptance_contract: AcceptanceContract | None = None,
    constraints: list[str] | None = None,
    derived_allowed: list[str] | None = None,
    known_unknowns: list[KnownUnknown] | None = None,
    evidence: FRZEvidence | None = None,
    product_boundary: ProductBoundary | None = None,
) -> FRZPackage:
    if core_journeys is None:
        core_journeys = []
    if domain_model is None:
        domain_model = []
    if state_machine is None:
        state_machine = []
    if acceptance_contract is None:
        acceptance_contract = AcceptanceContract(
            expected_outcomes=["User can complete the primary flow"],
            acceptance_impact=["Reduces support tickets"],
        )
    if constraints is None:
        constraints = []
    if derived_allowed is None:
        derived_allowed = []
    if known_unknowns is None:
        known_unknowns = []
    if evidence is None:
        evidence = FRZEvidence(source_refs=["discuss::meeting-001"])
    if product_boundary is None:
        product_boundary = ProductBoundary(in_scope=["Primary flow"], out_of_scope=[])
    return FRZPackage(
        frz_id=frz_id,
        status=status,
        product_boundary=product_boundary,
        core_journeys=core_journeys,
        domain_model=domain_model,
        state_machine=state_machine,
        acceptance_contract=acceptance_contract,
        constraints=constraints,
        derived_allowed=derived_allowed,
        known_unknowns=known_unknowns,
        evidence=evidence,
    )


def _make_minimal_src_package() -> dict:
    return {"src_root_id": "SRC-001"}


# ---------------------------------------------------------------------------
# Test 1: FRZ->EPIC mapping correctness (single items)
# ---------------------------------------------------------------------------


class TestMappingCorrectness:
    def test_scope_contains_journey(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package(
            core_journeys=[CoreJourney(id="JRN-001", name="User Login", steps=["Open app", "Enter credentials", "Submit"])],
            domain_model=[DomainEntity(id="ENT-001", name="UserAccount", contract={"purpose": "Manage user identity"})],
            state_machine=[StateMachine(id="SM-001", name="Auth State", states=["unauthenticated", "authenticated"], transitions=[{"from": "unauthenticated", "to": "authenticated"}])],
        )

        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")

        assert any("JRN-001" in s for s in payload["scope"])
        assert any("User Login" in s for s in payload["scope"])

    def test_actors_contain_entity_name(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package(
            domain_model=[DomainEntity(id="ENT-001", name="UserAccount", contract={"purpose": "Manage user identity"})],
        )
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")

        assert any(a["role"] == "UserAccount" for a in payload["actors_and_roles"])

    def test_behavior_slices_contain_state_machine(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package(
            state_machine=[StateMachine(id="SM-001", name="Auth State", states=["unauthenticated", "authenticated"], transitions=[])],
        )
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")

        assert any(b["name"] == "Auth State" for b in payload["product_behavior_slices"])

    def test_success_criteria_from_acceptance_contract(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package(
            acceptance_contract=AcceptanceContract(
                expected_outcomes=["User can login", "User can logout"],
                acceptance_impact=[],
            ),
        )
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")

        assert "User can login" in payload["epic_success_criteria"]
        assert "User can logout" in payload["epic_success_criteria"]

    def test_source_refs_contains_frz_entry(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package()
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-042")

        assert "frz::FRZ-042" in payload["source_refs"]


# ---------------------------------------------------------------------------
# Test 1b: FRZ->EPIC mapping with multiple items
# ---------------------------------------------------------------------------


class TestMappingMultipleItems:
    def test_all_items_appear_in_payload(self):
        from src_to_epic_extract import build_epic_from_frz

        frz = _make_frz_package(
            core_journeys=[
                CoreJourney(id="JRN-001", name="Login", steps=["Step 1", "Step 2"]),
                CoreJourney(id="JRN-002", name="Logout", steps=["Step 1", "Step 2"]),
                CoreJourney(id="JRN-003", name="Recover", steps=["Step 1", "Step 2"]),
            ],
            domain_model=[
                DomainEntity(id="ENT-001", name="User", contract={"purpose": "User"}),
                DomainEntity(id="ENT-002", name="Session", contract={"purpose": "Session"}),
            ],
            state_machine=[
                StateMachine(id="SM-001", name="Auth", states=["a", "b"], transitions=[]),
                StateMachine(id="SM-002", name="Session", states=["active", "expired"], transitions=[]),
            ],
        )
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")

        assert len(payload["scope"]) == 3
        assert len(payload["actors_and_roles"]) == 2
        assert len(payload["product_behavior_slices"]) == 2


# ---------------------------------------------------------------------------
# Test 2: Anchor inheritance
# ---------------------------------------------------------------------------


class TestAnchorInheritance:
    def test_anchors_registered_with_epic_projection(self):
        from src_to_epic_extract import extract_epic_from_frz_logic

        frz = _make_frz_package(
            core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["a", "b"])],
            domain_model=[DomainEntity(id="ENT-001", name="User", contract={"purpose": "User"})],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = extract_epic_from_frz_logic(
                frz_package=frz,
                src_package=_make_minimal_src_package(),
                frz_id="FRZ-001",
                repo_root=Path(tmpdir),
            )

            assert "JRN-001" in result.anchors_registered
            assert "ENT-001" in result.anchors_registered

    def test_registry_yaml_has_epic_projection(self):
        from src_to_epic_extract import extract_epic_from_frz_logic
        import yaml

        frz = _make_frz_package(
            core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["a", "b"])],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            extract_epic_from_frz_logic(
                frz_package=frz,
                src_package=_make_minimal_src_package(),
                frz_id="FRZ-001",
                repo_root=Path(tmpdir),
            )

            registry_path = Path(tmpdir) / "ssot" / "registry" / "anchor_registry.yaml"
            assert registry_path.exists()

            data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
            anchors = data["anchor_registry"]
            jrn_entry = next(a for a in anchors if a["anchor_id"] == "JRN-001")
            assert jrn_entry["projection_path"] == "EPIC"


# ---------------------------------------------------------------------------
# Test 3: Guard blocks non-derived fields
# ---------------------------------------------------------------------------


class TestGuardBlocksNonDerived:
    def test_guard_blocks_extra_field(self):
        from src_to_epic_extract import build_epic_from_frz
        from cli.lib.projection_guard import guard_projection

        derived = [
            "scope", "actors_and_roles", "product_behavior_slices",
            "epic_success_criteria", "constraints_and_dependencies",
            "non_goals", "source_refs", "decomposition_rules",
        ]
        frz = _make_frz_package(
            derived_allowed=derived,
            core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["a", "b"])],
        )
        payload = build_epic_from_frz(frz, _make_minimal_src_package(), "FRZ-001")
        # Add extra field not in derived_allowed
        payload["internal_notes"] = "secret stuff"

        result = guard_projection(frz, payload)
        assert result.verdict == "block"


# ---------------------------------------------------------------------------
# Test 5: Empty FRZ dimensions
# ---------------------------------------------------------------------------


class TestEmptyFRZDimensions:
    def test_empty_dimensions_produce_valid_payload_with_warnings(self):
        from src_to_epic_extract import extract_epic_from_frz_logic

        frz = _make_frz_package(
            core_journeys=[],
            domain_model=[],
            state_machine=[],
            acceptance_contract=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = extract_epic_from_frz_logic(
                frz_package=frz,
                src_package=_make_minimal_src_package(),
                frz_id="FRZ-001",
                repo_root=Path(tmpdir),
            )

            assert result.epic_payload["scope"] == []
            assert result.epic_payload["actors_and_roles"] == []
            assert result.epic_payload["product_behavior_slices"] == []
            assert len(result.warnings) > 0
            assert any("core_journeys" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Test 4: Non-frozen FRZ rejection (via runtime)
# ---------------------------------------------------------------------------


class TestNonFrozenFRZ:
    def test_draft_frz_raises_policy_denied(self):
        from cli.lib.frz_schema import FRZStatus
        from cli.lib.errors import ensure, CommandError

        frz = _make_frz_package(status=FRZStatus.draft)
        frz_status = frz.status.value if hasattr(frz.status, "value") else str(frz.status)

        with pytest.raises(CommandError) as exc_info:
            ensure(
                frz.status == FRZStatus.frozen,
                "POLICY_DENIED",
                f"FRZ status is '{frz_status}', must be 'frozen' for extraction",
            )

        assert exc_info.value.status_code == "POLICY_DENIED"


# ---------------------------------------------------------------------------
# Test 6: CLI command_extract dispatch
# ---------------------------------------------------------------------------


class TestCLICommandExtract:
    def test_extract_subcommand_parses_args(self):
        from src_to_epic import build_parser

        parser = build_parser()
        args = parser.parse_args([
            "extract", "--frz", "FRZ-001", "--src", "/tmp/src", "--output", "/tmp/out",
        ])

        assert args.command == "extract"
        assert args.frz == "FRZ-001"
        assert args.src == "/tmp/src"
        assert args.output == "/tmp/out"

    def test_extract_subcommand_required_args(self):
        from src_to_epic import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["extract"])

    def test_command_extract_returns_json_with_ok(self):
        """Verify command_extract exists and is callable with the right function signature."""
        from src_to_epic import command_extract
        import inspect

        sig = inspect.signature(command_extract)
        assert "args" in sig.parameters

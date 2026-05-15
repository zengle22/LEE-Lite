"""End-to-end tests for frz-ingest and impl-verify (tasks 12.1-12.3)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


def _load_module_by_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_workspace_root = Path(__file__).resolve().parent.parent.parent

_frz_ingest_module = _load_module_by_path(
    "frz_ingest_e2e",
    _workspace_root / "skills" / "ll-v2-frz-ingest" / "src" / "frz_ingest.py",
)
_impl_verify_module = _load_module_by_path(
    "impl_verify_e2e",
    _workspace_root / "skills" / "ll-v2-impl-verify" / "src" / "impl_verify.py",
)

frz_main = _frz_ingest_module.main
verify_main = _impl_verify_module.main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def _make_design_package_dir(base: Path) -> Path:
    """Create a minimal but complete design package directory."""
    dp = base / "design_package"

    _write_yaml(dp / "business_design" / "vision.yaml", {
        "product_vision": "Build a compiler",
        "scope_declaration": {"in_scope": ["freeze"], "out_of_scope": ["analysis"]},
        "target_users": ["devs"],
        "triggering_scenarios": [],
        "non_goals": ["no analysis"],
        "global_constraints": ["immutable"],
        "open_questions": [],
        "source_path": "biz/vision.yaml",
    })

    _write_yaml(dp / "product_design" / "prd.yaml", {
        "prd": "PRD content here",
        "user_journey_map": [
            {"name": "Compile journey", "steps": ["input", "check", "output"]},
        ],
        "acceptance_criteria": ["AC1: given x when y then z"],
        "source_path": "prd/prd.yaml",
    })

    _write_yaml(dp / "architecture_design" / "arch.yaml", {
        "tech_stack": {"language": "Python"},
        "api_contract": [{"path": "/api/v1"}],
        "layering": {"presentation": "API", "business": "Skill"},
        "data_flow": {"input": "Design Package", "output": "FRZ Package"},
        "storage_design": {"type": "file_system"},
        "integration_points": [{"service": "BMAD"}],
        "sync_async_strategy": {},
        "non_functional": {},
        "source_path": "arch/arch.yaml",
    })

    _write_yaml(dp / "engineering_design" / "eng.yaml", {
        "implementation_scope": {"directories": ["src/"]},
        "key_decisions": ["use dataclasses"],
        "source_path": "eng/eng.yaml",
    })

    _write_yaml(dp / "ux_design" / "ux.yaml", {
        "design_principles": ["consistency"],
        "interaction_flow": {},
        "state_expression": {},
        "design_tokens": {},
        "copy_style": {},
        "platform_strategy": {},
        "error_state_ux": {},
        "prototype": "proto.html",
    })

    _write_yaml(dp / "test_design" / "test.yaml", {
        "test_strategy": "unit + integration",
    })

    return dp


def _make_gsd_delivery_dir(base: Path) -> Path:
    """Create a minimal GSD delivery directory."""
    gsd = base / "gsd_delivery"
    code_dir = gsd / "code"
    docs_dir = gsd / "engineering_docs"
    code_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    (code_dir / "git.diff").write_text("+def existing(): pass\n", encoding="utf-8")
    (code_dir / "files_changed.list").write_text("src/main.py\n", encoding="utf-8")
    (code_dir / "files_added.list").write_text("", encoding="utf-8")

    (docs_dir / "change_description.md").write_text(
        "This is a detailed change description that is definitely longer than fifty characters.",
        encoding="utf-8",
    )
    (docs_dir / "key_decisions.md").write_text(
        "This is a key decision with rationale that exceeds twenty chars.",
        encoding="utf-8",
    )
    (docs_dir / "dependency_changes.md").write_text("Updated pytest", encoding="utf-8")
    (docs_dir / "known_issues.md").write_text("None", encoding="utf-8")
    (docs_dir / "rollback_strategy.md").write_text("Rollback by reverting commit", encoding="utf-8")

    return gsd


def _make_frz_package(path: Path) -> None:
    """Write a minimal FRZ package YAML."""
    pkg = {
        "frz_package": {
            "format_version": "2.0",
            "frz_ref": "FRZ-SRC-001-001",
            "version": "v1.0",
            "source_package_ref": "design_package",
            "frozen_ssot_chain": {
                "src_ref": "SRC-001",
                "epic_refs": ["EPIC-SRC-001-001"],
                "feat_refs": ["FEAT-SRC-001-001-001"],
                "tech_refs": ["TECH-SRC-001-001"],
                "arch_refs": ["ARCH-SRC-001-001"],
                "api_refs": ["API-SRC-001-001"],
                "ui_refs": ["UI-SRC-001-001"],
                "impl_refs": ["IMPL-SRC-001-001"],
            },
            "acceptance_test_cases": {},
            "completeness_check": {"verdict": "pass", "missing_items": [], "warnings": []},
            "alignment_check": {"verdict": "pass", "issues": []},
            "drift_check": {"verdict": "pass", "drift_items": []},
            "freeze_status": "frozen",
        }
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(pkg, f, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# E2E: frz-ingest
# ---------------------------------------------------------------------------


class TestFrzIngestEndToEnd:
    def test_full_pipeline_produces_frz_package(self, tmp_path: Path) -> None:
        """Task 12.1: Known design package -> golden FRZ package output."""
        dp = _make_design_package_dir(tmp_path)
        out_dir = tmp_path / "frz_output"

        rc = frz_main(["--input", str(dp), "--output", str(out_dir), "--src-id", "SRC-001"])
        assert rc == 0

        frz_files = list(out_dir.glob("*__frz.yaml"))
        assert len(frz_files) == 1

        with open(frz_files[0], encoding="utf-8") as f:
            data = yaml.safe_load(f)

        pkg = data["frz_package"]
        assert pkg["frz_ref"] == "FRZ-SRC-001-001"
        assert pkg["version"] == "v1.0"
        assert pkg["freeze_status"] == "frozen"
        assert pkg["frozen_ssot_chain"]["src_ref"] == "SRC-001"
        assert pkg["completeness_check"]["verdict"] == "pass"
        assert pkg["alignment_check"]["verdict"] == "pass"
        assert pkg["drift_check"]["verdict"] == "pass"

    def test_checkpoint_idempotency(self, tmp_path: Path) -> None:
        """Re-running with checkpoint should succeed without error."""
        dp = _make_design_package_dir(tmp_path)
        out_dir = tmp_path / "frz_output"
        checkpoint = tmp_path / "checkpoint.json"

        rc1 = frz_main([
            "--input", str(dp), "--output", str(out_dir),
            "--src-id", "SRC-001", "--checkpoint", str(checkpoint),
        ])
        assert rc1 == 0
        assert checkpoint.exists()

        rc2 = frz_main([
            "--input", str(dp), "--output", str(out_dir),
            "--src-id", "SRC-001", "--checkpoint", str(checkpoint),
        ])
        assert rc2 == 0


# ---------------------------------------------------------------------------
# E2E: impl-verify
# ---------------------------------------------------------------------------


class TestImplVerifyEndToEnd:
    def test_passing_delivery(self, tmp_path: Path) -> None:
        """Task 12.2: Static FRZ fixture + mock GSD -> expected pass verdict."""
        frz_path = tmp_path / "frz.yaml"
        _make_frz_package(frz_path)
        gsd_dir = _make_gsd_delivery_dir(tmp_path)
        report_path = tmp_path / "report.yaml"

        rc = verify_main([
            "--frz", str(frz_path),
            "--gsd", str(gsd_dir),
            "--output", str(report_path),
        ])
        assert rc == 0

        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)

        assert report["final_verdict"] == "pass"
        assert report["convergence"]["release_ready"] is True
        assert report["task_completion_detail"]["scope_compliance"] == "pass"
        assert report["engineering_docs_detail"]["engineering_docs"] == "pass"
        assert report["feature_scope_detail"]["scope_compliance"] == "pass"
        assert report["traceability_detail"]["traceability"] == "pass"

    def test_out_of_scope_fails(self, tmp_path: Path) -> None:
        """GSD touching forbidden files should produce fail verdict."""
        frz_path = tmp_path / "frz.yaml"
        _make_frz_package(frz_path)
        gsd_dir = _make_gsd_delivery_dir(tmp_path)

        # Inject out-of-scope file change (non-.py so it doesn't match allowed_files)
        code_dir = gsd_dir / "code"
        (code_dir / "files_changed.list").write_text("other/file.js\n", encoding="utf-8")

        report_path = tmp_path / "report.yaml"
        rc = verify_main([
            "--frz", str(frz_path),
            "--gsd", str(gsd_dir),
            "--output", str(report_path),
        ])
        assert rc == 100

        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)

        assert report["final_verdict"] == "fail"
        assert report["convergence"]["release_ready"] is False


# ---------------------------------------------------------------------------
# E2E: Dual-line convergence
# ---------------------------------------------------------------------------


class TestDualLineConvergenceEndToEnd:
    def test_and_gate_both_pass(self, tmp_path: Path) -> None:
        """Task 12.3: Line 1 pass + Line 2 pass -> release_ready."""
        frz_path = tmp_path / "frz.yaml"
        _make_frz_package(frz_path)
        gsd_dir = _make_gsd_delivery_dir(tmp_path)
        report_path = tmp_path / "report.yaml"

        rc = verify_main([
            "--frz", str(frz_path),
            "--gsd", str(gsd_dir),
            "--output", str(report_path),
        ])
        assert rc == 0

        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)

        # Line 1 in impl_verify.py is hardcoded pass for MVP
        assert report["convergence"]["convergence"] == "pass"
        assert report["convergence"]["release_ready"] is True

    def test_and_gate_line2_fail(self, tmp_path: Path) -> None:
        """Line 1 pass + Line 2 fail -> convergence fail, blocking_line = line_2."""
        frz_path = tmp_path / "frz.yaml"
        _make_frz_package(frz_path)
        gsd_dir = _make_gsd_delivery_dir(tmp_path)

        # Break engineering docs (missing rollback)
        docs_dir = gsd_dir / "engineering_docs"
        (docs_dir / "rollback_strategy.md").write_text("", encoding="utf-8")

        report_path = tmp_path / "report.yaml"
        rc = verify_main([
            "--frz", str(frz_path),
            "--gsd", str(gsd_dir),
            "--output", str(report_path),
        ])
        assert rc == 100

        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)

        assert report["convergence"]["convergence"] == "fail"
        assert report["convergence"]["blocking_line"] == "line_2"
        assert report["convergence"]["release_ready"] is False

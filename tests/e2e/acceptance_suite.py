#!/usr/bin/env python3
"""LL v2 Acceptance Test Suite — 8 end-to-end verification cases."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

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
_frz_mod = _load_module_by_path(
    "frz_ingest_acceptance",
    _workspace_root / "skills" / "ll-v2-frz-ingest" / "src" / "frz_ingest.py",
)
_verify_mod = _load_module_by_path(
    "impl_verify_acceptance",
    _workspace_root / "skills" / "ll-v2-impl-verify" / "src" / "impl_verify.py",
)
frz_main = _frz_mod.main
verify_main = _verify_mod.main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def make_design_package(base: Path, missing_dim: str | None = None) -> Path:
    dp = base / "design_package"
    dims = {
        "business_design": {
            "product_vision": "Build a compiler",
            "scope_declaration": {"in_scope": ["freeze"], "out_of_scope": ["analysis"]},
            "target_users": ["devs"],
            "triggering_scenarios": [],
            "non_goals": ["no analysis"],
            "global_constraints": ["immutable"],
            "open_questions": [],
            "source_path": "biz/vision.yaml",
        },
        "product_design": {
            "prd": "PRD content here",
            "user_journey_map": [
                {"name": "Compile journey", "steps": ["input", "check", "output"]},
            ],
            "acceptance_criteria": ["AC1: given x when y then z"],
            "source_path": "prd/prd.yaml",
        },
        "architecture_design": {
            "tech_stack": {"language": "Python"},
            "api_contract": [{"path": "/api/v1"}],
            "layering": {"presentation": "API", "business": "Skill"},
            "data_flow": {"input": "Design Package", "output": "FRZ Package"},
            "storage_design": {"type": "file_system"},
            "integration_points": [{"service": "BMAD"}],
            "sync_async_strategy": {},
            "non_functional": {},
            "source_path": "arch/arch.yaml",
        },
        "engineering_design": {
            "implementation_scope": {"directories": ["src/"]},
            "key_decisions": ["use dataclasses"],
            "source_path": "eng/eng.yaml",
        },
        "ux_design": {
            "design_principles": ["consistency"],
            "interaction_flow": {},
            "state_expression": {},
            "design_tokens": {},
            "copy_style": {},
            "platform_strategy": {},
            "error_state_ux": {},
            "prototype": "proto.html",
        },
        "test_design": {
            "test_strategy": "unit + integration",
        },
    }
    for dim, data in dims.items():
        if dim == missing_dim:
            continue
        write_yaml(dp / dim / "data.yaml", data)
    return dp


def make_gsd_delivery(base: Path, *, out_of_scope: bool = False, missing_rollback: bool = False) -> Path:
    gsd = base / "gsd_delivery"
    code_dir = gsd / "code"
    docs_dir = gsd / "engineering_docs"
    code_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    changed = "src/main.py\n" if not out_of_scope else "other/file.js\n"
    (code_dir / "files_changed.list").write_text(changed, encoding="utf-8")
    (code_dir / "files_added.list").write_text("", encoding="utf-8")
    (code_dir / "git.diff").write_text("+def existing(): pass\n", encoding="utf-8")

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
    rollback = "" if missing_rollback else "Rollback by reverting commit"
    (docs_dir / "rollback_strategy.md").write_text(rollback, encoding="utf-8")
    return gsd


def make_frz_package(path: Path) -> None:
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


def make_v1_frz_package(path: Path) -> None:
    """v1 style FRZ without format_version field."""
    pkg = {
        "frz_id": "FRZ-LEGACY-001",
        "version": "1.0",
        "product_boundary": {"scope": "core"},
        "core_journeys": [{"name": "j1"}],
        "domain_model": [],
        "state_machine": [],
        "acceptance_contract": {"ac1": "pass"},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(pkg, f, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------


class AcceptanceResult:
    def __init__(self, case_id: str, description: str, passed: bool, detail: str = "") -> None:
        self.case_id = case_id
        self.description = description
        self.passed = passed
        self.detail = detail


def run_case_1() -> AcceptanceResult:
    """frz-ingest 完整设计包 → FRZ Package"""
    with tempfile.TemporaryDirectory() as tmp:
        dp = make_design_package(Path(tmp))
        out_dir = Path(tmp) / "frz_out"
        rc = frz_main(["--input", str(dp), "--output", str(out_dir), "--src-id", "SRC-001"])
        if rc != 0:
            return AcceptanceResult("AC-1", "frz-ingest 完整设计包 → FRZ Package", False, f"exit code {rc}")
        files = list(out_dir.glob("*__frz.yaml"))
        if len(files) != 1:
            return AcceptanceResult("AC-1", "frz-ingest 完整设计包 → FRZ Package", False, "no FRZ file")
        with open(files[0], encoding="utf-8") as f:
            data = yaml.safe_load(f)
        pkg = data["frz_package"]
        checks = [
            pkg["frz_ref"] == "FRZ-SRC-001-001",
            pkg["version"] == "v1.0",
            pkg["freeze_status"] == "frozen",
            pkg["completeness_check"]["verdict"] == "pass",
            pkg["alignment_check"]["verdict"] == "pass",
            pkg["drift_check"]["verdict"] == "pass",
        ]
        if all(checks):
            return AcceptanceResult("AC-1", "frz-ingest 完整设计包 → FRZ Package", True)
        return AcceptanceResult("AC-1", "frz-ingest 完整设计包 → FRZ Package", False, str(pkg))


def run_case_2() -> AcceptanceResult:
    """frz-ingest 缺少必填维度 → 阻断"""
    with tempfile.TemporaryDirectory() as tmp:
        dp = make_design_package(Path(tmp), missing_dim="business_design")
        out_dir = Path(tmp) / "frz_out"
        rc = frz_main(["--input", str(dp), "--output", str(out_dir), "--src-id", "SRC-001"])
        if rc == 10:
            return AcceptanceResult("AC-2", "frz-ingest 缺少必填维度 → 阻断", True)
        return AcceptanceResult("AC-2", "frz-ingest 缺少必填维度 → 阻断", False, f"exit code {rc}, expected 10")


def run_case_3() -> AcceptanceResult:
    """impl-verify 合规 GSD 交付 → 通过"""
    with tempfile.TemporaryDirectory() as tmp:
        frz_path = Path(tmp) / "frz.yaml"
        make_frz_package(frz_path)
        gsd_dir = make_gsd_delivery(Path(tmp))
        report_path = Path(tmp) / "report.yaml"
        rc = verify_main(["--frz", str(frz_path), "--gsd", str(gsd_dir), "--output", str(report_path)])
        if rc != 0:
            return AcceptanceResult("AC-3", "impl-verify 合规 GSD → 通过", False, f"exit code {rc}")
        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)
        if report["final_verdict"] == "pass" and report["convergence"]["release_ready"] is True:
            return AcceptanceResult("AC-3", "impl-verify 合规 GSD → 通过", True)
        return AcceptanceResult("AC-3", "impl-verify 合规 GSD → 通过", False, str(report))


def run_case_4() -> AcceptanceResult:
    """impl-verify 越界文件 → 失败"""
    with tempfile.TemporaryDirectory() as tmp:
        frz_path = Path(tmp) / "frz.yaml"
        make_frz_package(frz_path)
        gsd_dir = make_gsd_delivery(Path(tmp), out_of_scope=True)
        report_path = Path(tmp) / "report.yaml"
        rc = verify_main(["--frz", str(frz_path), "--gsd", str(gsd_dir), "--output", str(report_path)])
        if rc != 100:
            return AcceptanceResult("AC-4", "impl-verify 越界文件 → 失败", False, f"exit code {rc}, expected 100")
        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)
        if report["final_verdict"] == "fail" and report["convergence"]["release_ready"] is False:
            return AcceptanceResult("AC-4", "impl-verify 越界文件 → 失败", True)
        return AcceptanceResult("AC-4", "impl-verify 越界文件 → 失败", False, str(report))


def run_case_5() -> AcceptanceResult:
    """impl-verify 缺少回滚方案 → 失败"""
    with tempfile.TemporaryDirectory() as tmp:
        frz_path = Path(tmp) / "frz.yaml"
        make_frz_package(frz_path)
        gsd_dir = make_gsd_delivery(Path(tmp), missing_rollback=True)
        report_path = Path(tmp) / "report.yaml"
        rc = verify_main(["--frz", str(frz_path), "--gsd", str(gsd_dir), "--output", str(report_path)])
        if rc != 100:
            return AcceptanceResult("AC-5", "impl-verify 缺少回滚 → 失败", False, f"exit code {rc}, expected 100")
        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)
        if report["final_verdict"] == "fail":
            return AcceptanceResult("AC-5", "impl-verify 缺少回滚 → 失败", True)
        return AcceptanceResult("AC-5", "impl-verify 缺少回滚 → 失败", False, str(report))


def run_case_6() -> AcceptanceResult:
    """双线路收敛 — Line 2 失败阻断发布"""
    with tempfile.TemporaryDirectory() as tmp:
        frz_path = Path(tmp) / "frz.yaml"
        make_frz_package(frz_path)
        gsd_dir = make_gsd_delivery(Path(tmp), out_of_scope=True)
        report_path = Path(tmp) / "report.yaml"
        rc = verify_main(["--frz", str(frz_path), "--gsd", str(gsd_dir), "--output", str(report_path)])
        if rc != 100:
            return AcceptanceResult("AC-6", "双线路收敛 Line 2 失败 → 阻断", False, f"exit code {rc}")
        with open(report_path, encoding="utf-8") as f:
            report = yaml.safe_load(f)
        conv = report["convergence"]
        if conv["convergence"] == "fail" and conv["blocking_line"] == "line_2" and conv["release_ready"] is False:
            return AcceptanceResult("AC-6", "双线路收敛 Line 2 失败 → 阻断", True)
        return AcceptanceResult("AC-6", "双线路收敛 Line 2 失败 → 阻断", False, str(conv))


def run_case_7() -> AcceptanceResult:
    """v1 FRZ Package 向后兼容读取"""
    with tempfile.TemporaryDirectory() as tmp:
        frz_path = Path(tmp) / "frz_v1.yaml"
        make_v1_frz_package(frz_path)
        gsd_dir = make_gsd_delivery(Path(tmp))
        report_path = Path(tmp) / "report.yaml"
        try:
            rc = verify_main(["--frz", str(frz_path), "--gsd", str(gsd_dir), "--output", str(report_path)])
            if rc in (0, 100):
                return AcceptanceResult("AC-7", "v1 FRZ 向后兼容读取", True, f"exit code {rc}")
            return AcceptanceResult("AC-7", "v1 FRZ 向后兼容读取", False, f"unexpected exit code {rc}")
        except Exception as exc:
            return AcceptanceResult("AC-7", "v1 FRZ 向后兼容读取", False, str(exc))


def run_case_8() -> AcceptanceResult:
    """幂等重试 — checkpoint 不重复生成"""
    with tempfile.TemporaryDirectory() as tmp:
        dp = make_design_package(Path(tmp))
        out_dir = Path(tmp) / "frz_out"
        checkpoint = Path(tmp) / "checkpoint.json"
        rc1 = frz_main([
            "--input", str(dp), "--output", str(out_dir),
            "--src-id", "SRC-001", "--checkpoint", str(checkpoint),
        ])
        if rc1 != 0:
            return AcceptanceResult("AC-8", "幂等重试 checkpoint", False, f"first run exit code {rc1}")
        if not checkpoint.exists():
            return AcceptanceResult("AC-8", "幂等重试 checkpoint", False, "checkpoint not created")
        rc2 = frz_main([
            "--input", str(dp), "--output", str(out_dir),
            "--src-id", "SRC-001", "--checkpoint", str(checkpoint),
        ])
        if rc2 == 0:
            return AcceptanceResult("AC-8", "幂等重试 checkpoint", True)
        return AcceptanceResult("AC-8", "幂等重试 checkpoint", False, f"second run exit code {rc2}")


def main() -> int:
    cases = [
        run_case_1,
        run_case_2,
        run_case_3,
        run_case_4,
        run_case_5,
        run_case_6,
        run_case_7,
        run_case_8,
    ]
    results: list[AcceptanceResult] = []
    for case_fn in cases:
        try:
            results.append(case_fn())
        except Exception as exc:
            results.append(AcceptanceResult(
                "???", case_fn.__doc__ or "", False, f"EXCEPTION: {exc}"
            ))

    print("=" * 70)
    print("LL v2 Acceptance Test Results")
    print("=" * 70)
    passed = 0
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"\n[{status}] {r.case_id}: {r.description}")
        if r.detail:
            print(f"       Detail: {r.detail}")
        if r.passed:
            passed += 1

    print("\n" + "=" * 70)
    print(f"Total: {passed}/{len(results)} passed")
    print("=" * 70)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import inspect
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from raw_to_src_bridge import semantic_review
from raw_to_src_common import load_raw_input, normalize_candidate
from raw_to_src_executor_phase import executor_run
from raw_to_src_high_fidelity import enrich_high_fidelity_candidate
from raw_to_src_records import (
    build_package_manifest,
    build_result_summary,
    build_run_state,
    build_supervision_evidence,
)
from raw_to_src_runtime import run_workflow


def _write_raw_input(tmp_path: Path, title: str, body: str) -> Path:
    path = tmp_path / "raw-input.md"
    path.write_text(
        "\n".join(
            [
                "---",
                "artifact_type: raw-input",
                "input_type: raw_requirement",
                f"title: {title}",
                "source_refs:",
                "  - docs/example.md",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_backward_compatible_revision_request_signatures() -> None:
    assert "revision_request_path" in inspect.signature(run_workflow).parameters
    assert "revision_request_path" in inspect.signature(executor_run).parameters
    assert "revision_request_ref" in inspect.signature(build_result_summary).parameters
    assert "revision_request_ref" in inspect.signature(build_run_state).parameters
    assert "revision_request_ref" in inspect.signature(build_supervision_evidence).parameters
    assert "revision_request_ref" in inspect.signature(build_package_manifest).parameters


def test_markdown_frontmatter_constraints_are_preserved(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw-input.md"
    raw_path.write_text(
        "\n".join(
            [
                "---",
                "artifact_type: raw-input",
                "input_type: raw_requirement",
                "title: Example Raw",
                "source_refs:",
                "  - docs/example.md",
                "constraints:",
                "  - first hard constraint",
                "  - second hard constraint",
                "---",
                "",
                "## 问题陈述",
                "",
                "需要验证 frontmatter constraints 会进入 key_constraints。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    document = load_raw_input(raw_path)

    assert document["key_constraints"] == ["first hard constraint", "second hard constraint"]


def test_smart_plan_input_does_not_trigger_onboarding_projection(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "智能训练计划生成模块 2.0 MVP 最小闭环重构",
        """## 问题陈述

当前训练计划链路过长，设备绑定与历史同步占据主流程，但 MVP 需要收敛为生成、执行、反馈、微调闭环。

## 目标用户

- 希望尽快拿到可执行计划的跑者

## 触发场景

- 用户极简建档后生成训练计划
- 用户完成训练后提交反馈并获得微调

## 业务动因

- 验证无伤优先的训练计划最小闭环

## 建议方向

- 设备绑定后置
- 使用 current_training_state
- 引入 body_checkin 与 session_feedback
""",
    )

    document = load_raw_input(raw_path)
    candidate = enrich_high_fidelity_candidate(normalize_candidate(document), document)

    object_names = {
        str(item.get("object", "")).strip()
        for item in candidate.get("structured_object_contracts", [])
        if isinstance(item, dict)
    }
    semantic_inventory = candidate.get("semantic_inventory") or {}

    assert "minimal_onboarding_page" not in object_names
    assert "first_ai_advice_output" not in object_names
    assert "minimal_onboarding_page" not in set(semantic_inventory.get("core_objects", []))


def test_smart_plan_input_projects_training_plan_contracts(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "智能训练计划生成模块 2.0 MVP 最小闭环重构",
        """## 问题陈述

训练计划 MVP 需要围绕生成、执行、反馈、微调闭环重构。

## 目标用户

- 希望尽快拿到可执行计划的跑者

## 建议方向

- 使用 current_training_state
- 风险评估改为 risk gate
- 输出 plan_draft 与 today_session
- 引入 body_checkin、session_feedback、micro_adjustment
""",
    )

    document = load_raw_input(raw_path)
    candidate = enrich_high_fidelity_candidate(normalize_candidate(document), document)

    object_names = {
        str(item.get("object", "")).strip()
        for item in candidate.get("structured_object_contracts", [])
        if isinstance(item, dict)
    }
    semantic_inventory = candidate.get("semantic_inventory") or {}
    enum_freezes = candidate.get("enum_freezes") or {}

    for expected in {
        "min_profile",
        "current_training_state",
        "risk_gate_result",
        "plan_draft",
        "today_session",
        "body_checkin",
        "session_feedback",
        "micro_adjustment",
        "plan_generation_guardrail",
        "plan_lifecycle",
    }:
        assert expected in object_names
        assert expected in set(semantic_inventory.get("core_objects", []))

    assert candidate.get("semantic_layer_declaration")
    assert "risk_gate_outcome" in enum_freezes
    assert "micro_adjustment_action" in enum_freezes
    assert "micro_adjustment_target_scope" in enum_freezes
    assert "readiness_to_train" in enum_freezes
    assert "pain_trend" in enum_freezes
    assert "deviation_reason" in enum_freezes
    assert semantic_inventory.get("product_surfaces")
    assert semantic_inventory.get("runtime_objects")
    assert semantic_inventory.get("states")
    body_checkin = next(item for item in candidate["structured_object_contracts"] if item.get("object") == "body_checkin")
    assert "readiness_to_train" in body_checkin.get("required_fields", [])
    assert "pain_trend" in body_checkin.get("required_fields", [])
    risk_gate = next(item for item in candidate["structured_object_contracts"] if item.get("object") == "risk_gate_result")
    assert "outcome" in risk_gate.get("required_fields", [])
    session_feedback = next(item for item in candidate["structured_object_contracts"] if item.get("object") == "session_feedback")
    assert "deviation_reason" in session_feedback.get("optional_fields", [])
    assert session_feedback.get("conditional_required_fields", {}).get("completed=false") == "deviation_reason"
    assert (candidate.get("bridge_context") or {}).get("recommended_min_profile_split")
    assert "runner_profile_min" not in candidate.get("target_capability_objects", [])
    assert not (candidate.get("semantic_inventory") or {}).get("commands")


def test_semantic_review_flags_onboarding_projection_mismatch(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "智能训练计划生成模块 2.0 MVP 最小闭环重构",
        """## 问题陈述

训练计划 MVP 需要围绕生成、执行、反馈、微调闭环重构。
""",
    )
    document = load_raw_input(raw_path)
    candidate = normalize_candidate(document)
    candidate["structured_object_contracts"] = [{"object": "minimal_onboarding_page"}]
    candidate["semantic_inventory"] = {"core_objects": ["minimal_onboarding_page"]}
    candidate["frozen_contracts"] = [{"applies_to": ["device_connect_entry"]}]

    review, findings = semantic_review(candidate, None, document=document)

    assert review["decision"] == "revise"
    assert any(item["type"] == "domain_projection_mismatch" for item in findings)


def test_semantic_review_flags_training_plan_empty_shell(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "智能训练计划生成模块 2.0 MVP 最小闭环重构",
        """## 问题陈述

训练计划 MVP 需要围绕生成、执行、反馈、微调闭环重构，并以 today_session 与 session_feedback 形成闭环。
""",
    )
    document = load_raw_input(raw_path)
    candidate = normalize_candidate(document)
    candidate["semantic_inventory"] = {
        "actors": ["跑者"],
        "product_surfaces": [],
        "operator_surfaces": [],
        "entry_points": [],
        "commands": [],
        "runtime_objects": [],
        "states": [],
        "observability_surfaces": [],
    }

    review, findings = semantic_review(candidate, None, document=document)

    assert review["decision"] == "revise"
    assert any(item["type"] == "machine_contracts_missing" for item in findings)
    assert any(item["type"] == "semantic_inventory_too_thin" for item in findings)

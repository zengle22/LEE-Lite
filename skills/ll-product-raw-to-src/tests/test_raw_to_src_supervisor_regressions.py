from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from raw_to_src_runtime import run_workflow
from raw_to_src_supervisor_phase import _apply_semantic_patch


def _write_adr_input(tmp_path: Path, title: str) -> Path:
    path = tmp_path / "raw-input.md"
    path.write_text(
        "\n".join(
            [
                "---",
                "artifact_type: raw-input",
                "input_type: adr",
                f"title: {title}",
                "source_refs:",
                "  - ADR-090",
                "---",
                "",
                "## 问题陈述",
                "",
                "当前主链已经具备 ADR 到 IMPL 的上游对象，但 implementation start 前仍缺独立的实施前文档压力测试边界。",
                "这个 workflow 需要检测跨文档冲突、失败路径缺口、测试不可观测性和修复目标，而不是直接下沉到实现设计。",
                "",
                "## 目标用户",
                "",
                "- reviewer",
                "- AI coder",
                "- implementation consumer",
                "",
                "## 触发场景",
                "",
                "- feature_impl_candidate_package 已生成，准备进入 implementation start",
                "- external gate 前需要确认 IMPL 是否具备稳定实施条件",
                "",
                "## 业务动因",
                "",
                "- 需要让 implementation readiness 形成可消费 verdict，而不是停留在摘要层",
                "- 需要在编码前发现跨文档冲突和失败路径缺口",
                "",
                "## 用户入口与控制面",
                "",
                "- 主入口 skill：`ll-qa-impl-spec-test`",
                "- workflow key：`qa.impl-spec-test`",
                "- 运行模式控制面：`quick_preflight`、`deep_spec_testing`",
                "- verdict 控制面：`pass`、`pass_with_revisions`、`block`",
                "",
                "## 运行时对象与状态",
                "",
                "- runtime objects：`feature_impl_candidate_package`、`impl_spec_test_report_package`、`implementation_readiness_gate_subject`",
                "- readiness states：`ready`、`partial`、`not_ready`",
                "- verdict states：`pass`、`pass_with_revisions`、`block`",
                "",
                "## 目标能力对象",
                "",
                "- `qa.impl-spec-test`",
                "- implementation-readiness verdict",
                "- score-to-verdict binding rules",
                "- repair-target routing rules",
                "",
                "## 成功结果",
                "",
                "- reviewer 可在不回读原始 ADR 的前提下判断 implementation start 是否允许继续",
                "- coder 可理解主测试对象、联动 authority、修复责任与阻断条件",
                "",
                "## 关键约束",
                "",
                "- `IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority",
                "- workflow 必须输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict",
                "- deep 模式必须覆盖失败路径推演与 counterexample family",
                "",
                "## 范围边界",
                "",
                "- In scope: 定义 implementation start 前的 implementation spec testing workflow 边界和 verdict 规则",
                "- Out of scope: 替代 external gate 或重写 FEAT / TECH / API / UI truth",
                "",
                "## 下游派生要求",
                "",
                "- 后续实现必须把 `pass / pass_with_revisions / block`、`quick_preflight / deep_spec_testing` 与 `repair_target_artifact` 做成正式 contract",
                "- implementation consumer 必须在不回读原始 ADR 的前提下理解何时 block、何时修复、何时进入 implementation start",
                "",
                "## 桥接摘要",
                "",
                "- 这不是新增第二层技术设计，而是为 implementation start 前补一层正式、可继承的 readiness testing 边界",
                "- workflow 只升级冲突，不改写上游 truth",
                "",
                "## 非目标",
                "",
                "- 不把该 workflow 定义为 external gate 的替代",
                "- 不要求该 workflow 直接运行代码或替代执行测试",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_apply_semantic_patch_repairs_governance_constraint_clarity() -> None:
    candidate = {
        "title": "ADR-090 Implementation Spec Testing Acceptance Repair",
        "semantic_lock": {"primary_object": "qa.impl-spec-test"},
        "target_capability_objects": ["qa.impl-spec-test", "implementation-readiness verdict"],
        "key_constraints": [
            "`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。",
            "workflow 必须输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict。",
        ],
        "out_of_scope": ["不把该 workflow 定义为 external gate 的替代。"],
        "governance_change_summary": [],
        "bridge_context": {},
    }

    patched, patches = _apply_semantic_patch(
        candidate,
        [{"type": "governance_constraint_clarity_insufficient"}],
        duplicate_path=None,
        document=None,
    )

    assert any(item["code"] == "bridge_context_repair" for item in patches)
    assert any("继承约束" in item for item in patched["key_constraints"])


def test_run_workflow_allow_update_repairs_acceptance_only_bridge_gap(tmp_path: Path) -> None:
    input_path = _write_adr_input(tmp_path, "ADR-090 Implementation Spec Testing Acceptance Repair")

    result = run_workflow(
        input_path=input_path,
        repo_root=tmp_path,
        run_id="adr090-acceptance-repair-r1",
        allow_update=True,
    )

    assert result["status"] == "freeze_ready"


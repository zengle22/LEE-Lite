from __future__ import annotations

from copy import deepcopy
from typing import Any

from src_to_epic_identity import is_governance_bridge_package, uses_adr005_prerequisite
from src_to_epic_common import unique_strings

GOVERNANCE_BRIDGE_BEHAVIOR_SLICES = [
    {
        "id": "collaboration-loop",
        "name": "主链候选提交与交接流",
        "track": "foundation",
        "goal": "冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。",
        "scope": [
            "定义 candidate package、proposal、evidence 在什么触发场景下被提交。",
            "定义提交后形成什么 authoritative handoff object。",
            "定义提交完成后对上游和 gate 分别暴露什么业务结果。",
        ],
        "product_surface": "候选提交流：governed skill 提交 candidate package 并形成 authoritative handoff submission",
        "completed_state": "上游 workflow 已明确看到一次正式提交完成，gate 已接管 handoff，待审批状态与回流边界都对上游可见。",
        "business_deliverable": "给 gate 使用的 authoritative handoff submission，以及给上游 workflow 可见的提交完成结果。",
        "capability_axes": ["主链协作闭环能力"],
        "overlay_families": [],
    },
    {
        "id": "handoff-formalization",
        "name": "主链 gate 审核与裁决流",
        "track": "foundation",
        "goal": "冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。",
        "scope": [
            "定义 approve / revise / retry / handoff / reject 的业务语义和输出物。",
            "定义每种裁决的返回去向和对上游的业务结果。",
            "定义 decision object 如何成为后续 formal 发布的唯一触发来源。",
        ],
        "product_surface": "审批裁决流：gate 审核 handoff 并输出 authoritative decision result",
        "completed_state": "一次 gate 审核已经结束，reviewer 给出单一 authoritative decision result，上游知道应回流、终止还是进入 formal 发布。",
        "business_deliverable": "给 execution 或 formal 发布链消费的 authoritative decision result，以及给 reviewer 可追溯的裁决结果。",
        "capability_axes": ["正式交接与物化能力", "主链协作闭环能力"],
        "overlay_families": [],
    },
    {
        "id": "object-layering",
        "name": "formal 发布与下游准入流",
        "track": "foundation",
        "goal": "冻结 approved decision 之后如何形成 formal output、formal ref 与 lineage，并让下游只通过正式准入链消费。",
        "scope": [
            "定义 approved decision 之后的 formal 发布动作和 formal output 完成态。",
            "定义 formal ref / lineage 如何成为 authoritative downstream input。",
            "定义 consumer admission 边界，阻止 candidate 或旁路对象被正式消费。",
        ],
        "product_surface": "formal 发布与准入流：approved decision 发布成 formal package 并供 consumer 准入",
        "completed_state": "formal publication package 已形成且被 admission 链认可，下游 consumer 只会拿到 formal input，不会再把 candidate 当成正式结果。",
        "business_deliverable": "给 downstream consumer 正式消费的 formal publication package，以及可验证的 admission result。",
        "capability_axes": ["对象分层与准入能力", "正式交接与物化能力"],
        "overlay_families": [],
    },
    {
        "id": "artifact-io-governance",
        "name": "主链受治理 IO 落盘与读取流",
        "track": "foundation",
        "goal": "冻结主链业务动作在什么时候必须 governed write/read，以及这些正式读写会为业务方留下什么 authoritative receipt 和 managed ref。",
        "scope": [
            "定义 handoff、decision、formal output、evidence 的正式读写动作。",
            "定义业务调用点、正式 receipt / registry record 和 managed ref。",
            "定义被拒绝读写时对业务方可见的失败表现。",
        ],
        "product_surface": "受治理落盘流：正式 write/read 生成 managed ref 与 authoritative receipt",
        "completed_state": "正式业务读写都留下 governed receipt / managed ref，调用方能知道对象写到哪里、为什么可读，失败不会静默旁路。",
        "business_deliverable": "给业务动作发起方返回的 governed write/read result，以及可审计的 managed ref / receipt。",
        "capability_axes": ["主链文件 IO 与路径治理能力"],
        "overlay_families": [],
    },
]


def derive_governance_bridge_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    slices = deepcopy(GOVERNANCE_BRIDGE_BEHAVIOR_SLICES)
    if rollout_requirement and rollout_requirement.get("required"):
        slices.append(
            {
                "id": "skill-adoption-e2e",
                "name": "governed skill 接入与 pilot 验证流",
                "track": "adoption_e2e",
                "goal": "冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。",
                "scope": [
                    "定义哪些 governed skill 先接入以及 scope 外对象如何处理。",
                    "定义 pilot 主链如何选定、扩围和形成真实 evidence。",
                    "定义 cutover / fallback 如何判断，以及 adoption 成立需要交付哪些真实 evidence。",
                ],
                "product_surface": "接入验证流：governed skill 通过 pilot / cutover / fallback 接入主链",
                "completed_state": "至少一条真实 pilot 链已完成验证，rollout owner 能看到 integration matrix、pilot evidence 和 cutover / fallback 决策结果。",
                "business_deliverable": "给 rollout owner 使用的 onboarding / pilot / cutover package，以及真实链路 evidence。",
                "capability_axes": ["技能接入与跨 skill 闭环验证能力"],
                "overlay_families": ["skill_onboarding", "migration_cutover", "cross_skill_e2e_validation"],
            }
        )
    return slices

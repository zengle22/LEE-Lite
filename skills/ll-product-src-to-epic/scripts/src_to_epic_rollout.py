from typing import Any

from src_to_epic_identity import (
    ROLLOUT_KEYWORD_GROUPS,
    is_engineering_bootstrap_baseline_package,
    is_execution_runner_package,
    is_governance_bridge_package,
    is_review_projection_package,
    semantic_lock,
    uses_adr005_prerequisite,
)
from src_to_epic_common import unique_strings, ensure_list, guess_repo_root_from_input


def _constraint_group(name: str, items: list[str]) -> dict[str, Any]:
    return {"name": name, "items": unique_strings(items)}


def _revision_constraint_note(package: Any) -> str:
    revision_context = package.src_candidate.get("revision_context")
    if not isinstance(revision_context, dict):
        return ""
    return str(revision_context.get("summary") or "").strip()


def _review_projection_constraint_groups(package: Any, key_constraints: list[str], source_refs: list[str]) -> list[dict[str, Any]]:
    lock = semantic_lock(package)
    revision_note = _revision_constraint_note(package)
    epic_level_items = [
        "本 EPIC 直接负责 gate 审核阶段的人类友好 Projection，而不是引入新的运行时治理闭环。",
        "Projection 必须是 derived-only、non-authoritative、non-inheritable；冻结与下游继承仍只回到 Machine SSOT。",
        "Projection 必须固定包含产品摘要、主流程、关键交付物、Authoritative Snapshot、Review Focus、Risks / Ambiguities 等审核模板块。",
    ]
    inherited_items = unique_strings(
        ([f"Semantic lock truth: {lock.get('one_sentence_truth')}"] if lock.get("one_sentence_truth") else [])
        + ([f"Allowed capabilities: {', '.join(lock.get('allowed_capabilities', []))}"] if lock.get("allowed_capabilities") else [])
        + ([f"Forbidden capabilities: {', '.join(lock.get('forbidden_capabilities', []))}"] if lock.get("forbidden_capabilities") else [])
        + key_constraints
        + ([revision_note] if revision_note else [])
        + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
        + [f"Upstream package: {package.artifacts_dir}"]
    )
    downstream_items = [
        "下游 FEAT 不得改写 src_root_id、epic_freeze_ref、source_refs 与 semantic_lock。",
        "下游 FEAT 不得把 Projection 当成新的 SSOT，也不得允许 TECH / TESTSET 直接继承 Projection。",
        "任何审核意见必须沉淀回 Machine SSOT，再重新生成 Projection。",
    ]
    return [
        _constraint_group("Epic-level constraints", epic_level_items),
        _constraint_group("Authoritative inherited constraints", inherited_items),
        _constraint_group("Downstream preservation rules", downstream_items),
    ]


def _execution_runner_constraint_groups(package: Any, key_constraints: list[str], source_refs: list[str]) -> list[dict[str, Any]]:
    lock = semantic_lock(package)
    revision_note = _revision_constraint_note(package)
    epic_level_items = [
        "本 EPIC 直接负责 gate approve 后的自动推进运行时，不把 approve 停在 formal publication 或人工接力。",
        "自动推进主链固定为：approve -> ready execution job -> runner claim -> next skill dispatch -> execution outcome。",
        "artifacts/jobs/ready 是正式 ready queue；runner claim 是唯一 intake；next skill dispatch 必须保留 authoritative refs 和目标 skill 边界。",
    ]
    inherited_items = unique_strings(
        ([f"Semantic lock truth: {lock.get('one_sentence_truth')}"] if lock.get("one_sentence_truth") else [])
        + ([f"Allowed capabilities: {', '.join(lock.get('allowed_capabilities', []))}"] if lock.get("allowed_capabilities") else [])
        + ([f"Forbidden capabilities: {', '.join(lock.get('forbidden_capabilities', []))}"] if lock.get("forbidden_capabilities") else [])
        + key_constraints
        + ([revision_note] if revision_note else [])
        + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
        + [f"Upstream package: {package.artifacts_dir}"]
    )
    downstream_items = [
        "下游 FEAT 不得把 automatic progression 重新解释成 formal publication / admission-only 链。",
        "下游 FEAT 不得跳过 ready queue 和 runner claim 直接以人工接力或路径猜测触发下一个 skill。",
        "执行结果、重试和失败证据必须继续保持 execution 语义可追溯。",
    ]
    return [
        _constraint_group("Epic-level constraints", epic_level_items),
        _constraint_group("Authoritative inherited constraints", inherited_items),
        _constraint_group("Downstream preservation rules", downstream_items),
    ]


def _governance_bridge_constraint_groups(package: Any, key_constraints: list[str], source_refs: list[str], rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    revision_note = _revision_constraint_note(package)
    filtered_constraints = [item for item in key_constraints if item not in {"QA test execution skill", "TestEnvironmentSpec", "TestCasePack 冻结", "ScriptPack 冻结", "合规与判定分层"}]
    epic_level_items = [
        "本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。",
        "主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。",
        "FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。",
        "主链文件 IO 与路径治理只覆盖交接对象的 IO 入口、出口、物化落点与引用稳定性，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。",
    ]
    if uses_adr005_prerequisite(package):
        epic_level_items.append("ADR-005 是主链文件 IO / 路径治理前置基础；本 EPIC 只消费其已交付能力，不重新实现 Gateway / Path Policy / Registry 模块。")
    if rollout_requirement and rollout_requirement.get("required"):
        epic_level_items.append("当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。")
    inherited_intro = "以下来源约束来自 authoritative SRC，downstream must preserve where applicable，但它们不重新定义本 EPIC 的 primary capability boundary。"
    inherited_items = unique_strings(
        [inherited_intro]
        + filtered_constraints
        + ([revision_note] if revision_note else [])
        + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
        + [f"Upstream package: {package.artifacts_dir}"]
    )
    downstream_items = [
        "下游 FEAT 不得改写 src_root_id、epic_freeze_ref 与 authoritative source_refs。",
        "下游 FEAT 不得把 EPIC 重新打平为上游 QA test execution 对象清单；source-level object constraints 只能附着到实际受其约束的 FEAT。",
        "candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。",
    ]
    return [
        _constraint_group("Epic-level constraints", epic_level_items),
        _constraint_group("Authoritative inherited constraints", inherited_items),
        _constraint_group("Downstream preservation rules", downstream_items),
    ]


def _default_constraint_groups(package: Any, key_constraints: list[str], source_refs: list[str]) -> list[dict[str, Any]]:
    revision_note = _revision_constraint_note(package)
    structure_items: list[str] = []
    layering_items: list[str] = []
    formalization_items: list[str] = []
    remaining_items: list[str] = []
    for item in key_constraints:
        if any(token in item for token in ["双会话双队列", "execution loop", "gate loop", "human loop"]):
            structure_items.append(item)
        elif any(token in item for token in ["approve", "revise", "retry", "handoff", "reject", "materialization", "物化"]):
            formalization_items.append(item)
        elif any(token in item for token in ["candidate", "formal", "分层", "proposal", "evidence", "裁决"]):
            layering_items.append(item)
        elif "handoff runtime" in item:
            structure_items.append(item)
        else:
            remaining_items.append(item)
    if is_governance_bridge_package(package):
        layering_items.append("路径与目录治理仅限主链 handoff、formal materialization 与 governed skill IO 边界，不得扩展为全局文件治理。")
    groups = [
        _constraint_group("主链结构约束", structure_items),
        _constraint_group("职责分层约束", layering_items),
        _constraint_group("Formalization 约束", formalization_items),
        _constraint_group(
            "来源与依赖约束",
            remaining_items
            + ([revision_note] if revision_note else [])
            + ([f"Authoritative source refs: {', '.join(source_refs)}"] if source_refs else [])
            + [f"Upstream package: {package.artifacts_dir}"],
        ),
    ]
    return [group for group in groups if group["items"]]


def derive_constraint_groups(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    key_constraints = ensure_list(package.src_candidate.get("key_constraints"))
    source_refs = ensure_list(package.src_candidate.get("source_refs"))
    if is_review_projection_package(package):
        return _review_projection_constraint_groups(package, key_constraints, source_refs)
    if is_execution_runner_package(package):
        return _execution_runner_constraint_groups(package, key_constraints, source_refs)
    if is_governance_bridge_package(package):
        return _governance_bridge_constraint_groups(package, key_constraints, source_refs, rollout_requirement)
    return _default_constraint_groups(package, key_constraints, source_refs)


def flatten_constraint_groups(groups: list[dict[str, Any]]) -> list[str]:
    flattened: list[str] = []
    for group in groups:
        for item in group["items"]:
            flattened.append(f"{group['name']}：{item}")
    return flattened[:14]


def derive_validation_findings(
    package: Any,
    constraint_groups: list[dict[str, Any]],
    decomposition_rules: list[str],
    success_metrics: list[str],
) -> list[dict[str, Any]]:
    if is_review_projection_package(package):
        return []
    if not is_governance_bridge_package(package):
        return []
    findings: list[dict[str, Any]] = []
    group_map = {group["name"]: group["items"] for group in constraint_groups}
    required_groups = {"Epic-level constraints", "Authoritative inherited constraints", "Downstream preservation rules"}
    if not required_groups.issubset(group_map):
        findings.append({"severity": "P1", "title": "Constraint layers are not separated", "detail": "Governance EPIC must separate epic-level constraints, inherited source constraints, and downstream preservation rules."})
    epic_items = " ".join(group_map.get("Epic-level constraints", []))
    inherited_items = " ".join(group_map.get("Authoritative inherited constraints", []))
    source_level_markers = ["TestEnvironmentSpec", "TestCasePack", "ScriptPack", "skill.qa.test_exec_web_e2e", "skill.runner.test_e2e", "invalid_run", "acceptance_status"]
    source_text = " ".join(ensure_list(package.src_candidate.get("key_constraints")) + ensure_list(package.src_candidate.get("source_refs")))
    qa_source_detected = any(marker in source_text for marker in source_level_markers)
    if any(marker in epic_items for marker in source_level_markers):
        findings.append({"severity": "P1", "title": "Epic-level constraints still carry source object detail", "detail": "EPIC-level constraints must stay at capability-boundary level instead of repeating QA execution object rules."})
    if qa_source_detected and not any(marker in inherited_items for marker in source_level_markers):
        findings.append({"severity": "P1", "title": "Inherited source constraints are too thin", "detail": "Authoritative inherited constraints should preserve the source-level object rules where applicable."})
    if (
        not any("产品行为切片" in rule for rule in decomposition_rules)
        or not any("cross-cutting constraints" in rule for rule in decomposition_rules)
        or not any("mandatory overlays" in rule or "mandatory cross-cutting overlays" in rule for rule in decomposition_rules)
    ):
        findings.append({"severity": "P1", "title": "FEAT decomposition axis is still ambiguous", "detail": "The EPIC must explicitly define product behavior slices as primary, capability axes as cross-cutting constraints, and rollout families as mandatory overlays."})
    metrics_text = " ".join(success_metrics)
    for token, title, detail in [
        ("producer -> consumer -> audit -> gate", "Missing pilot-chain completion signal", "Success metrics should require at least one real producer -> consumer -> audit -> gate pilot chain."),
        ("formal publish", "Missing materialization completion signal", "Success metrics should require at least one real approved decision -> formal publish -> admission path."),
        ("adoption / cutover / fallback", "Missing rollout verification signal", "Success metrics should define rollout verification for adoption / cutover / fallback."),
    ]:
        if token not in metrics_text:
            findings.append({"severity": "P1", "title": title, "detail": detail})
    return findings


def derive_traceability(package: Any, src_root_id: str) -> list[dict[str, Any]]:
    source_refs = unique_strings(ensure_list(package.src_candidate.get("source_refs")) + (["ADR-005"] if uses_adr005_prerequisite(package) else []))
    frz = package.frz_package if isinstance(getattr(package, "frz_package", None), dict) else {}
    frz_id = str(frz.get("frz_id") or "").strip()
    frz_anchor_ids: list[str] = []
    freeze_payload = frz.get("freeze") if isinstance(frz.get("freeze"), dict) else {}
    for collection_key in ("core_journeys", "domain_model", "state_machine", "known_unknowns"):
        for item in (freeze_payload.get(collection_key) or []) if isinstance(freeze_payload, dict) else []:
            if isinstance(item, dict) and str(item.get("id") or "").strip():
                frz_anchor_ids.append(str(item["id"]).strip())
    frz_refs = unique_strings([ref for ref in [frz_id, package.manifest.get("frz_registry_record_ref"), package.manifest.get("frz_package_ref")] if str(ref or "").strip()])
    anchor_refs = frz_anchor_ids[:12]
    return [
        {
            "epic_section": "Epic Intent",
            "input_fields": ["problem_statement", "trigger_scenarios", "business_drivers"],
            "source_refs": unique_strings(source_refs + frz_refs + anchor_refs),
        },
        {
            "epic_section": "Business Value and Problem",
            "input_fields": ["problem_statement", "business_drivers", "trigger_scenarios"],
            "source_refs": unique_strings(source_refs + frz_refs + anchor_refs),
        },
        {
            "epic_section": "Actors and Roles",
            "input_fields": ["target_users", "trigger_scenarios", "bridge_context.downstream_inheritance_requirements"],
            "source_refs": unique_strings([src_root_id] + source_refs + frz_refs + anchor_refs),
        },
        {
            "epic_section": "Capability Scope",
            "input_fields": ["in_scope", "governance_change_summary", "bridge_context.governance_objects"],
            "source_refs": unique_strings([src_root_id] + source_refs + frz_refs + anchor_refs),
        },
        {
            "epic_section": "Constraints and Dependencies",
            "input_fields": ["key_constraints", "bridge_context.downstream_inheritance_requirements"],
            "source_refs": unique_strings([f"product.raw-to-src::{package.run_id}"] + source_refs + frz_refs + anchor_refs),
        },
        {
            "epic_section": "Epic Success Criteria",
            "input_fields": ["business_drivers", "bridge_context.acceptance_impact", "trigger_scenarios"],
            "source_refs": unique_strings([f"product.raw-to-src::{package.run_id}"] + source_refs + frz_refs + anchor_refs),
        },
    ]


def derive_optional_architecture_refs(package: Any, src_root_id: str) -> list[str]:
    repo_root = guess_repo_root_from_input(package.artifacts_dir)
    architecture_dir = repo_root / "ssot" / "architecture"
    if not architecture_dir.exists():
        return []
    refs: list[str] = []
    for path in architecture_dir.glob(f"ARCH-{src_root_id}-*.md"):
        stem = path.stem
        if "__" in stem:
            refs.append(stem.split("__", 1)[0])
        else:
            refs.append(stem)
    return unique_strings(refs)


def multi_feat_score(package: Any) -> dict[str, Any]:
    if is_review_projection_package(package):
        return {
            "score": 8,
            "reasons": ["semantic_lock=review_projection_rule", "fixed_review_slices=4"],
            "is_multi_feat_ready": True,
        }
    scope_count = len(ensure_list(package.src_candidate.get("in_scope")))
    scenario_count = len(ensure_list(package.src_candidate.get("trigger_scenarios")))
    governance_object_count = len(ensure_list((package.src_candidate.get("bridge_context") or {}).get("governance_objects")))
    expected_downstream = ensure_list((package.src_candidate.get("bridge_context") or {}).get("expected_downstream_objects"))
    score = scope_count + scenario_count + governance_object_count + len(expected_downstream)
    reasons = [
        f"in_scope={scope_count}",
        f"trigger_scenarios={scenario_count}",
        f"governance_objects={governance_object_count}",
        f"expected_downstream_objects={len(expected_downstream)}",
    ]
    return {
        "score": score,
        "reasons": reasons,
        "is_multi_feat_ready": score >= 6 or (scope_count >= 2 and scenario_count >= 2),
    }


def _package_text_blob(package: Any) -> str:
    bridge = package.src_candidate.get("bridge_context") or {}
    fields = [
        package.src_candidate.get("title"),
        package.src_candidate.get("problem_statement"),
        *ensure_list(package.src_candidate.get("business_drivers")),
        *ensure_list(package.src_candidate.get("key_constraints")),
        *ensure_list(package.src_candidate.get("in_scope")),
        *ensure_list(package.src_candidate.get("governance_change_summary")),
        *ensure_list(package.src_candidate.get("trigger_scenarios")),
        *ensure_list(bridge.get("governance_objects")),
        *ensure_list(bridge.get("current_failure_modes")),
        *ensure_list(bridge.get("downstream_inheritance_requirements")),
        *ensure_list(bridge.get("acceptance_impact")),
    ]
    return " ".join(str(item).lower() for item in fields if item)


def assess_rollout_requirement(package: Any) -> dict[str, Any]:
    if is_review_projection_package(package):
        return {
            "required": False,
            "score": 0,
            "triggers": {name: False for name in ROLLOUT_KEYWORD_GROUPS},
            "rationale": ["该源只覆盖 gate 审核投影视图，不需要 adoption / rollout / cross-skill E2E 轨。"],
        }
    if is_engineering_bootstrap_baseline_package(package):
        return {
            "required": False,
            "score": 0,
            "triggers": {name: False for name in ROLLOUT_KEYWORD_GROUPS},
            "rationale": ["该源为工程骨架/本地开发环境基线：可包含治理约束，但不应强制引入 adoption / rollout / cross-skill E2E 作为主拆分轨。"],
        }
    text_blob = _package_text_blob(package)
    governance_bridge = is_governance_bridge_package(package)
    triggers = {
        name: governance_bridge or any(keyword in text_blob for keyword in keywords)
        for name, keywords in ROLLOUT_KEYWORD_GROUPS.items()
    }
    score = sum(1 for status in triggers.values() if status)
    required = score >= 2 and (triggers["shared_runtime_or_governance_change"] or governance_bridge)
    rationale = []
    if triggers["shared_runtime_or_governance_change"]:
        rationale.append("SRC 涉及共享治理底座或共用运行时能力，而不是单一业务功能。")
    if triggers["requires_existing_skill_migration"]:
        rationale.append("功能真正生效依赖现有 skill / workflow 接入，而不是只完成底座建设。")
    if triggers["effectiveness_depends_on_real_skill_integration"]:
        rationale.append("效果判定依赖真实 producer / consumer 接入，不能只靠组件内自测证明。")
    if triggers["requires_cross_skill_e2e_validation"]:
        rationale.append("需要跨 skill E2E 或 handoff/gate 闭环验证，才能证明治理主链真的成立。")
    return {
        "required": required,
        "score": score,
        "triggers": triggers,
        "rationale": rationale,
    }


def derive_rollout_plan(package: Any, rollout_requirement: dict[str, Any]) -> dict[str, Any]:
    if not rollout_requirement.get("required"):
        return {
            "required_feat_tracks": ["foundation"],
            "required_feat_families": [],
            "planning_notes": ["当前 SRC 不需要单独的 adoption / rollout / E2E FEAT 族。"],
        }
    return {
        "required_feat_tracks": ["foundation", "adoption_e2e"],
        "required_feat_families": [
            {
                "family": "skill_onboarding",
                "goal": "建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。",
            },
            {
                "family": "migration_cutover",
                "goal": "定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。",
            },
            {
                "family": "cross_skill_e2e_validation",
                "goal": "至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。",
            },
        ],
        "planning_notes": [
            "rollout / adoption / E2E 不另起第二个 EPIC，而是在当前主 EPIC 内显式保留，并在 epic-to-feat 阶段强制拆出独立 FEAT 族。",
            "foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 source_refs 和治理约束，不得形成并行真相。",
            "default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。",
        ],
    }

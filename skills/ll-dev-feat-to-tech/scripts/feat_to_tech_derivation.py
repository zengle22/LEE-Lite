#!/usr/bin/env python3
"""
Derivation helpers for the lite-native feat-to-tech runtime.
"""

from __future__ import annotations

from typing import Any

from feat_to_tech_axis_content import axis_content
from feat_to_tech_common import ensure_list, unique_strings
from feat_to_tech_contract_content import DEFAULT_API_COMMAND_SPECS, INTERFACE_CONTRACTS_BY_AXIS
from feat_to_tech_meta import (
    api_compatibility_rules as _meta_api_compatibility_rules,
    design_focus as _meta_design_focus,
    selected_feat_snapshot as _meta_selected_feat_snapshot,
    traceability_rows as _meta_traceability_rows,
)


ARCH_KEYWORDS = [
    "架构",
    "architecture",
    "boundary",
    "边界",
    "module",
    "模块",
    "subsystem",
    "topology",
    "调用链",
    "path",
    "registry",
    "external gate",
    "cross-skill",
]

STRONG_API_KEYWORDS = ["api", "接口", "contract", "schema", "request", "response", "webhook"]
WEAK_API_KEYWORDS = ["event", "message", "proposal", "decision", "consumer", "provider", "handoff", "queue"]
NEGATION_MARKERS = ["不", "无", "without", "no ", "not ", "do not"]

REVIEW_PROJECTION_AXIS_MAP = {
    "projection-generation": "projection_generation",
    "authoritative-snapshot": "authoritative_snapshot",
    "review-focus-risk": "review_focus_risk",
    "feedback-writeback": "feedback_writeback",
}

EXECUTION_RUNNER_AXIS_MAP = {
    "ready-job-emission": "runner_ready_job",
    "runner-operator-entry": "runner_operator_entry",
    "runner-control-surface": "runner_control_surface",
    "execution-runner-intake": "runner_intake",
    "next-skill-dispatch": "runner_dispatch",
    "execution-result-feedback": "runner_feedback",
    "runner-observability-surface": "runner_observability",
}

PRODUCT_FLOW_AXIS_MAP = {
    "first-ai-advice-release": "first_ai_advice",
    "extended-profile-progressive-completion": "extended_profile_completion",
    "device-connect-deferred-entry": "device_deferred_entry",
    "state-and-profile-boundary-alignment": "state_profile_boundary",
    "minimal-onboarding-flow": "minimal_onboarding",
}

MINIMAL_ONBOARDING_FIELD_MARKERS = [
    "gender",
    "birthdate",
    "height",
    "weight",
    "running_level",
    "recent_injury_status",
]

# Engineering baseline FEAT patterns - each FEAT owns exactly one engineering object
ENGINEERING_BASELINE_FEAT_MAP = {
    "repo-layout": "repo_layout_baseline",
    "apps-api-shell": "apps_api_shell",
    "apps-miniapp-shell": "apps_miniapp_shell",
    "local-env-baseline": "local_env_baseline",
    "db-migrations": "db_migrations_discipline",
    "healthz-readyz": "healthz_readyz_contract",
}

ENGINEERING_BASELINE_MODULE_MAP = {
    "repo_layout_baseline": [
        "Repository layout validator: 负责验证 src/, apps/, deploy/ 等顶层目录结构。",
        "Skeleton generator: 负责生成空壳文件和占位目录。",
        "AGENTS/README bootstrap: 负责写入项目级文档模板。",
    ],
    "apps_api_shell": [
        "API shell bootstrap: 负责生成 apps/api/ 最小可运行骨架。",
        "Health endpoint stub: 负责生成/healthz 占位端点。",
        "Build script placeholder: 负责生成 Makefile/scripts 占位。",
    ],
    "apps_miniapp_shell": [
        "MiniApp shell bootstrap: 负责生成 apps/miniapp/ 最小可运行骨架。",
        "UniApp config placeholder: 负责生成 manifest.json 等配置占位。",
        "Build target stub: 负责生成构建脚本占位。",
    ],
    "local_env_baseline": [
        "Docker Compose bootstrap: 负责生成 deploy/docker-compose.local.yml。",
        "Env var template: 负责生成.env.example 模板。",
        "Container network setup: 负责配置本地容器网络。",
    ],
    "db_migrations_discipline": [
        "Migration directory structure: 负责创建 db/migrations/ 目录。",
        "Migration naming convention: 负责定义迁移文件命名规则。",
        "Migration runner stub: 负责生成迁移执行脚本占位。",
    ],
    "healthz_readyz_contract": [
        "Healthz endpoint contract: 负责定义/healthz 响应格式。",
        "Readyz endpoint contract: 负责定义/readyz 响应格式。",
        "Health check integration: 负责定义容器健康检查配置。",
    ],
}

ENGINEERING_BASELINE_STRATEGY_MAP = {
    "repo_layout_baseline": [
        "先验证目录结构规范，再生成空壳文件。",
        "使用占位文件（.gitkeep）确保空目录被 git 追踪。",
        "最后验证生成结果与预期结构一致。",
    ],
    "apps_api_shell": [
        "先创建目录结构，再写入最小可运行代码。",
        "使用语言/框架的空壳模板（如 Go module、Python venv）。",
        "验证可运行性：确保能执行最简启动命令。",
    ],
    "apps_miniapp_shell": [
        "先创建 UniApp 项目结构，再写入配置文件。",
        "使用官方模板或手动创建 pages/, components/ 目录。",
        "验证构建工具可识别项目。",
    ],
    "local_env_baseline": [
        "先定义容器清单和服务依赖。",
        "编写 docker-compose.yml，配置网络和卷。",
        "验证 docker-compose up 可启动所有服务。",
    ],
    "db_migrations_discipline": [
        "先创建 migrations 目录和版本追踪表。",
        "定义迁移文件命名规则（如 V001__description.sql）。",
        "提供迁移执行和回滚脚本占位。",
    ],
    "healthz_readyz_contract": [
        "先定义健康检查响应格式（JSON/plain）。",
        "实现/healthz 和/readyz 端点。",
        "在 docker-compose 中配置 healthcheck。",
    ],
}

ENGINEERING_BASELINE_UNIT_MAP = {
    "repo_layout_baseline": [
        "`src/lee/__init__.py` (`new`): 标记 Python 包根目录。",
        "`apps/api/.gitkeep` (`new`): 占位 API 目录。",
        "`apps/miniapp/.gitkeep` (`new`): 占位 MiniApp 目录。",
        "`AGENTS.md` (`new`): 项目级 AI 助手说明。",
    ],
    "apps_api_shell": [
        "`apps/api/main.go` (`new`): Go API 入口（或对应语言）。",
        "`apps/api/go.mod` (`new`): Go 模块定义。",
        "`apps/api/healthz.go` (`new`): 健康检查端点。",
    ],
    "apps_miniapp_shell": [
        "`apps/miniapp/manifest.json` (`new`): UniApp 配置。",
        "`apps/miniapp/pages.json` (`new`): 页面路由。",
        "`apps/miniapp/App.vue` (`new`): 根组件。",
    ],
    "local_env_baseline": [
        "`deploy/docker-compose.local.yml` (`new`): 本地开发容器编排。",
        "`deploy/.env.example` (`new`): 环境变量模板。",
        "`deploy/networks.yaml` (`new`): 网络配置（可选）。",
    ],
    "db_migrations_discipline": [
        "`db/migrations/.gitkeep` (`new`): 迁移目录占位。",
        "`db/migrations/README.md` (`new`): 迁移规范说明。",
        "`db/migrations/V001__init.sql` (`new`): 初始迁移占位。",
    ],
    "healthz_readyz_contract": [
        "`src/lee/health/endpoints.py` (`new`): 健康检查端点实现。",
        "`src/lee/health/contracts.md` (`new`): 端点契约文档。",
        "`deploy/docker-compose.local.yml#healthcheck` (`modify`): 容器健康检查配置。",
    ],
}

ENGINEERING_BASELINE_SEQUENCE_MAP = {
    "repo_layout_baseline": [
        "1. validate target directory structure",
        "2. create top-level directories (src/, apps/, deploy/)",
        "3. create .gitkeep placeholders for empty directories",
        "4. write AGENTS.md and README templates",
        "5. verify structure matches expected layout",
    ],
    "apps_api_shell": [
        "1. create apps/api/ directory structure",
        "2. write language/framework bootstrap files",
        "3. add minimal health endpoint stub",
        "4. configure build scripts",
        "5. verify minimal runnable state",
    ],
    "apps_miniapp_shell": [
        "1. create apps/miniapp/ directory structure",
        "2. write UniApp configuration files",
        "3. create pages/App.vue root component",
        "4. configure build targets",
        "5. verify project recognized by build tools",
    ],
    "local_env_baseline": [
        "1. define container inventory and dependencies",
        "2. write docker-compose.local.yml",
        "3. configure networks and volumes",
        "4. create .env.example template",
        "5. verify docker-compose up starts all services",
    ],
    "db_migrations_discipline": [
        "1. create db/migrations/ directory",
        "2. define migration file naming convention",
        "3. create version tracking table schema",
        "4. write migration runner stub",
        "5. document migration workflow",
    ],
    "healthz_readyz_contract": [
        "1. define health check response format",
        "2. implement /healthz endpoint",
        "3. implement /readyz endpoint",
        "4. configure container healthcheck",
        "5. verify endpoints respond correctly",
    ],
}


def review_projection_axis(feature: dict[str, Any]) -> str:
    lock = feature.get("semantic_lock") or {}
    domain_type = str(lock.get("domain_type") or "").strip().lower()
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id in REVIEW_PROJECTION_AXIS_MAP:
        return REVIEW_PROJECTION_AXIS_MAP[axis_id]
    title = str(feature.get("title") or "").strip().lower()
    if "projection" in title and "生成" in title:
        return "projection_generation"
    if "snapshot" in title:
        return "authoritative_snapshot"
    if "review focus" in title or "风险提示" in title or "ambigu" in title:
        return "review_focus_risk"
    if "回写" in title or "writeback" in title or "批注" in title:
        return "feedback_writeback"
    if domain_type == "review_projection_rule":
        return "projection_generation"
    return ""


def execution_runner_axis(feature: dict[str, Any]) -> str:
    lock = feature.get("semantic_lock") or {}
    domain_type = str(lock.get("domain_type") or "").strip().lower()
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id in EXECUTION_RUNNER_AXIS_MAP:
        return EXECUTION_RUNNER_AXIS_MAP[axis_id]
    title = str(feature.get("title") or "").strip().lower()
    if "ready job" in title or "批准后" in title:
        return "runner_ready_job"
    if "用户入口" in title or "skill entry" in title:
        return "runner_operator_entry"
    if "控制面" in title or "control surface" in title:
        return "runner_control_surface"
    if "自动取件" in title or "runner intake" in title:
        return "runner_intake"
    if "自动派发" in title or "dispatch" in title:
        return "runner_dispatch"
    if "结果回写" in title or "feedback" in title:
        return "runner_feedback"
    if "监控" in title or "observability" in title:
        return "runner_observability"
    if domain_type == "execution_runner_rule":
        return "runner_ready_job"
    return ""


def product_flow_axis(feature: dict[str, Any]) -> str:
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id in PRODUCT_FLOW_AXIS_MAP:
        return PRODUCT_FLOW_AXIS_MAP[axis_id]
    text = feature_text(feature)
    if not any(marker in text for marker in ["最小建档", "minimal profile", "minimal onboarding", "profile_minimal_done"]):
        return ""
    if not any(marker in text for marker in ["首页", "homepage", "home page", "enter home", "首页放行"]):
        return ""
    field_hits = sum(1 for marker in MINIMAL_ONBOARDING_FIELD_MARKERS if marker in text)
    if field_hits >= 3:
        return "minimal_onboarding"
    return ""


def is_execution_runner_axis(axis: str) -> bool:
    return axis in set(EXECUTION_RUNNER_AXIS_MAP.values())


def is_review_projection_axis(axis: str) -> bool:
    return axis in set(REVIEW_PROJECTION_AXIS_MAP.values())


def feature_text(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
        parts.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            parts.extend([str(check.get("scenario") or ""), str(check.get("given") or ""), str(check.get("when") or ""), str(check.get("then") or "")])
    return "\n".join(parts).lower()


def feature_core_text(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ["scope", "constraints"]:
        parts.extend(ensure_list(feature.get(key)))
    return "\n".join(parts).lower()


def _axis_list(feature: dict[str, Any], section: str) -> list[str] | None:
    content = axis_content(feature_axis(feature), section)
    return content if isinstance(content, list) else None


def _axis_dict(feature: dict[str, Any], section: str) -> dict[str, str] | None:
    content = axis_content(feature_axis(feature), section)
    return content if isinstance(content, dict) else None


def _axis_text(feature: dict[str, Any], section: str) -> str | None:
    content = axis_content(feature_axis(feature), section)
    return content if isinstance(content, str) else None


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    segments: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
        segments.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            segments.extend([str(check.get("scenario") or ""), str(check.get("given") or ""), str(check.get("when") or ""), str(check.get("then") or "")])
    for segment in segments:
        lowered = segment.lower().strip()
        if not lowered or any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in lowered and keyword not in hits:
                hits.append(keyword)
    return hits


def build_refs(feature: dict[str, Any], package: Any) -> dict[str, str]:
    feat_ref = str(feature.get("feat_ref") or "").strip()
    feat_suffix = feat_ref.replace("FEAT-", "", 1) if feat_ref.startswith("FEAT-") else feat_ref
    tech_owner_ref = str(feature.get("tech_owner_ref") or feature.get("tech_ref") or "").strip()
    return {
        "feat_ref": feat_ref,
        "tech_ref": tech_owner_ref or (f"TECH-{feat_suffix}" if feat_suffix else ""),
        "surface_map_ref": str(feature.get("surface_map_ref") or "").strip(),
        "arch_ref": f"ARCH-{feat_suffix}" if feat_suffix else "",
        "api_ref": f"API-{feat_suffix}" if feat_suffix else "",
        "epic_ref": str(package.feat_json.get("epic_freeze_ref") or ""),
        "src_ref": str(package.feat_json.get("src_root_id") or ""),
    }


def explicit_axis(feature: dict[str, Any]) -> str:
    # Prefer the execution-runner axis when the semantic lock/title overlaps on
    # generic words like "回写"/"feedback". Otherwise execution FEATs can be
    # misclassified into review-projection writeback content.
    for axis in [execution_runner_axis(feature), review_projection_axis(feature), product_flow_axis(feature)]:
        if axis:
            return axis
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    mapping = {
        "collaboration-loop": "collaboration",
        "handoff-formalization": "formalization",
        "object-layering": "layering",
        "io-governance": "io_governance",
        "adoption-e2e": "adoption_e2e",
        "skill-adoption-e2e": "adoption_e2e",
    }
    return mapping.get(axis_id, "")


def looks_like_adoption_e2e(core_text: str, full_text: str) -> bool:
    rollout_tokens = ["migration", "cutover", "pilot", "wave", "rollout"]
    skill_tokens = [
        "skill",
        "skills",
        "技能接入",
        "cross skill",
        "cross-skill",
        "compat mode",
        "compat_mode",
        "pilot evidence",
        "onboarding matrix",
        "runtime binding",
        "producer -> gate",
        "consumer",
        "audit",
    ]
    has_rollout_signal = any(token in core_text for token in rollout_tokens)
    has_skill_signal = any(token in full_text for token in skill_tokens)
    return has_rollout_signal and has_skill_signal


def assess_optional_artifacts(feature: dict[str, Any], package: Any | None = None) -> dict[str, Any]:
    arch_hits = keyword_hits(feature, ARCH_KEYWORDS)
    api_hits = keyword_hits(feature, STRONG_API_KEYWORDS)
    weak_api_hits = keyword_hits(feature, WEAK_API_KEYWORDS)
    axis = feature_axis(feature)
    arch_required = bool(arch_hits) or axis in {
        "collaboration",
        "formalization",
        "layering",
        "io_governance",
        "first_ai_advice",
        "extended_profile_completion",
        "device_deferred_entry",
        "state_profile_boundary",
        "minimal_onboarding",
        "adoption_e2e",
        "runner_ready_job",
        "runner_operator_entry",
        "runner_control_surface",
        "runner_intake",
        "runner_dispatch",
        "runner_feedback",
        "runner_observability",
    }
    api_required = bool(api_hits) or axis in {
        "formalization",
        "layering",
        "io_governance",
        "first_ai_advice",
        "extended_profile_completion",
        "device_deferred_entry",
        "state_profile_boundary",
        "minimal_onboarding",
        "adoption_e2e",
        "runner_ready_job",
        "runner_operator_entry",
        "runner_control_surface",
        "runner_intake",
        "runner_dispatch",
        "runner_feedback",
        "runner_observability",
    } or (axis == "collaboration" and bool(weak_api_hits))
    arch_rationale = ["ARCH required by boundary/runtime placement."] if arch_required else ["ARCH omitted because the FEAT does not introduce a dedicated boundary/topology surface."]
    if arch_hits:
        arch_rationale.append(f"Keyword hits: {', '.join(arch_hits[:4])}.")
    api_rationale = ["API required by command-level contract surface."] if api_required else ["API omitted because no explicit command-level contract surface was detected."]
    if api_hits or weak_api_hits:
        api_rationale.append(f"Keyword hits: {', '.join((api_hits + weak_api_hits)[:4])}.")
    return {
        "arch_required": arch_required,
        "api_required": api_required,
        "arch_hits": arch_hits,
        "api_hits": api_hits + weak_api_hits,
        "arch_rationale": arch_rationale,
        "api_rationale": api_rationale,
        "reasons": arch_rationale + api_rationale,
    }


def selected_feat_snapshot(feature: dict[str, Any]) -> dict[str, Any]:
    return _meta_selected_feat_snapshot(feature, feature_axis(feature))


def design_focus(feature: dict[str, Any]) -> str:
    return _meta_design_focus(feature, feature_axis(feature))


def implementation_rules(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    rewritten_rules: list[str] = []
    for item in ensure_list(feature.get("constraints"))[:4]:
        text = str(item).strip()
        if text == "来源与依赖约束：保持与原始输入同题，不扩展到 EPIC、FEAT、TASK 或实现设计。":
            text = "来源与依赖约束：保持与原始输入同题，不扩展到相邻 FEAT、TASK 排期细节或超出本 FEAT 边界的实现域。"
        rewritten_rules.append(text)
    rules = rewritten_rules
    source_refs = ensure_list(feature.get("source_refs"))
    if "ADR-007" in source_refs and feature_axis(feature) == "adoption_e2e":
        rules.extend([
            "Authoritative inherited constraints：对外暴露一个宽 skill family：`skill.qa.test_exec_web_e2e` 与 `skill.qa.test_exec_cli`。",
            "Authoritative inherited constraints：内部保留一个窄 runner family：`skill.runner.test_e2e` 与 `skill.runner.test_cli`。",
        ])
    if axis == "state_profile_boundary":
        rules.append("Projection stores 只能作为只读 projection / read model，不得回写 canonical body facts，也不得覆盖 user_physical_profile 的唯一事实源地位。")
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            scenario = str(check.get("scenario") or "").strip()
            then = str(check.get("then") or "").strip()
            if scenario and then:
                rules.append(f"{scenario}: {then}")
    return unique_strings(rules)[:8]


def non_functional_requirements(feature: dict[str, Any], package: Any) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))
    axis = feature_axis(feature)
    requirements = [
        "Preserve FEAT, EPIC, and SRC traceability across every emitted design object.",
        "Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.",
    ]
    axis_specific_requirement = {
        "first_ai_advice": "Keep first-advice output, risk-gate decisions, and fallback-mode evidence traceable in freeze-ready artifacts.",
        "extended_profile_completion": "Keep patch-save results, profile-completion-percent updates, and retry-state evidence traceable in freeze-ready artifacts.",
        "device_deferred_entry": "Keep deferred-device-connection outcomes and homepage/first-advice preservation evidence traceable in freeze-ready artifacts.",
        "state_profile_boundary": "Keep canonical-ownership decisions, conflict-blocked outcomes, and unified-reader judgments traceable in freeze-ready artifacts.",
        "minimal_onboarding": "Keep minimal-profile submission results, homepage-entry decisions, and deferred-device-entry evidence traceable in freeze-ready artifacts.",
    }.get(axis)
    if axis_specific_requirement:
        requirements.append(axis_specific_requirement)
    else:
        requirements.append("Keep the package freeze-ready by recording execution evidence and supervision evidence.")
    if any(ref.startswith("ADR-") for ref in refs):
        requirements.append("Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.")
    return unique_strings(requirements)


def architecture_topics(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "architecture_topics") or unique_strings(ensure_list(feature.get("dependencies"))[:3] + ensure_list(feature.get("scope"))[:2])[:3]


def responsibility_splits(feature: dict[str, Any]) -> list[str]:
    canned = _axis_list(feature, "responsibility_splits")
    if canned is not None:
        return canned
    splits = [item for item in ensure_list(feature.get("constraints")) + ensure_list(feature.get("non_goals")) if any(marker in item.lower() for marker in ["不", "只", "不得", "only", "must not", "do not", "not ", "leave", "留给"])]
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("dependencies")))
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("scope")))
    return unique_strings(splits)[:3]


def api_surfaces(feature: dict[str, Any]) -> list[str]:
    canned = _axis_list(feature, "api_surfaces")
    if canned is not None:
        return canned
    surfaces: list[str] = []
    text = feature_text(feature)
    if "handoff" in text:
        surfaces.append("handoff object contract")
    if "decision" in text or "gate" in text:
        surfaces.append("gate decision contract")
    if "proposal" in text:
        surfaces.append("proposal exchange contract")
    if "consumer" in text or "provider" in text:
        surfaces.append("consumer/provider boundary contract")
    if "event" in text or "message" in text or "queue" in text:
        surfaces.append("event or message contract")
    return unique_strings(surfaces or ["feature-specific boundary contract"])[:4]


def api_cli_commands(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "api_cli_commands") or [
        "`ll gate submit-handoff --request <gate_submit_handoff.request.json> --response-out <gate_submit_handoff.response.json>` via `cli/commands/gate/command.py`",
        "`ll gate show-pending --request <gate_show_pending.request.json> --response-out <gate_show_pending.response.json>` via `cli/commands/gate/command.py`",
    ]


def api_command_specs(feature: dict[str, Any]) -> list[dict[str, Any]]:
    canned = axis_content(feature_axis(feature), "api_command_specs")
    if isinstance(canned, list):
        return canned
    return DEFAULT_API_COMMAND_SPECS


def api_request_response_contracts(feature: dict[str, Any]) -> list[str]:
    return [f"{spec['command']}: request={'; '.join(spec.get('request_schema') or [])}; response={'; '.join(spec.get('response_schema') or [])}" for spec in api_command_specs(feature)]


def api_error_and_idempotency(feature: dict[str, Any]) -> list[str]:
    return [f"{spec['command']}: idempotency={spec.get('idempotency')}; invariants={'; '.join(spec.get('invariants') or [])}" for spec in api_command_specs(feature)]


def api_compatibility_rules(feature: dict[str, Any]) -> list[str]:
    return _meta_api_compatibility_rules(feature_axis(feature))


def traceability_rows(feature: dict[str, Any], package: Any, refs: dict[str, str]) -> list[dict[str, Any]]:
    return _meta_traceability_rows(feature, package.run_id, refs)


def consistency_check(feature: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    minor_open_items: list[str] = []
    structural = []
    semantic = []

    def add_check(category: str, name: str, passed: bool, detail: str, issue: str | None = None) -> None:
        checks.append({"category": category, "name": name, "passed": passed, "detail": detail})
        (structural if category == "structural" else semantic).append(passed)
        if not passed and issue:
            issues.append(issue)

    add_check("structural", "TECH mandatory", True, "TECH is always emitted for the selected FEAT.")
    traceability_ok = bool(ensure_list(feature.get("source_refs")))
    add_check("structural", "Traceability present", traceability_ok, "Selected FEAT carries authoritative source refs for downstream design derivation.", "Selected FEAT did not carry enough source refs to support traceability.")
    add_check("structural", "ARCH coverage" if assessment["arch_required"] else "ARCH omission justified", (len(architecture_topics(feature)) >= 2) if assessment["arch_required"] else True, "ARCH coverage matches the selected FEAT boundary needs." if assessment["arch_required"] else "ARCH is omitted because the FEAT does not require boundary or topology redesign.", "ARCH was required but architecture topics could not be resolved clearly.")
    add_check("structural", "API coverage" if assessment["api_required"] else "API omission justified", bool(api_command_specs(feature)) if assessment["api_required"] else True, "API coverage includes concrete command-level contracts." if assessment["api_required"] else "API is omitted because no explicit cross-boundary contract surface was detected.", "API was required but no concrete command contract specs were derived.")
    arch_tech_separation = (architecture_diagram(feature) != tech_runtime_view(feature)) if assessment["arch_required"] else True
    add_check("semantic", "ARCH / TECH separation", arch_tech_separation, "ARCH keeps boundary placement while TECH keeps implementation carriers.", "ARCH and TECH still appear to share the same runtime topology.")
    if assessment["api_required"]:
        specs = api_command_specs(feature)
        api_complete = bool(specs) and all(spec.get("request_schema") and spec.get("response_schema") and spec.get("field_semantics") and spec.get("enum_domain") is not None and spec.get("invariants") and spec.get("canonical_refs") for spec in specs)
    else:
        api_complete = True
    add_check("semantic", "API contract completeness", api_complete, "API contracts carry schema, semantics, invariants, and canonical refs.", "API is still too thin; command specs are missing schema, invariants, or canonical ref semantics.")
    if feature_axis(feature) == "collaboration":
        scope = collaboration_reentry_scope(feature)
        add_check("semantic", "Collaboration re-entry boundary", scope != "ambiguous", "Collaboration FEATs keep decision-driven runtime routing in scope without claiming gate/publication ownership.", "The FEAT carries ambiguous or unresolved revise/retry re-entry ownership.")
    if assessment["api_required"]:
        minor_open_items.append("Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.")
    if assessment["arch_required"] or assessment["api_required"]:
        minor_open_items.append("Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.")
    return {"passed": all(structural) and all(semantic), "structural_passed": all(structural), "semantic_passed": all(semantic), "checks": checks, "issues": issues, "minor_open_items": minor_open_items}


def feature_axis(feature: dict[str, Any]) -> str:
    explicit = explicit_axis(feature)
    if explicit:
        return explicit
    title = str(feature.get("title") or "").strip().lower()
    core_text = feature_core_text(feature)
    full_text = feature_text(feature)
    if any(token in title for token in ["主链候选提交", "候选提交与交接", "交接流"]):
        return "collaboration"
    if any(token in title for token in ["对象分层", "准入"]):
        return "layering"
    if any(token in title for token in ["正式交接", "物化"]):
        return "formalization"
    if any(token in title for token in ["主链协作闭环", "协作闭环"]):
        return "collaboration"
    if any(token in title for token in ["文件 io", "路径治理"]):
        return "io_governance"
    if any(token in title for token in ["技能接入", "跨 skill", "cross skill", "cross-skill"]):
        return "adoption_e2e"
    if any(token in core_text for token in ["candidate package", "formal object", "formal refs", "lineage", "candidate layer", "formal layer", "authoritative layer", "准入", "对象分层"]):
        return "layering"
    if any(token in core_text for token in ["materialization", "external gate", "approve", "reject", "formalization", "正式交接", "物化"]):
        return "formalization"
    if any(token in core_text for token in ["execution loop", "gate loop", "human loop", "双会话双队列", "queue", "协作闭环", "re-entry", "reentry"]):
        return "collaboration"
    if any(token in core_text for token in ["path", "registry", "gateway", "artifact io", "路径", "落盘", "写入模式"]):
        return "io_governance"
    if looks_like_adoption_e2e(core_text, full_text):
        return "adoption_e2e"
    if any(token in full_text for token in ["candidate package", "formal object", "formal refs", "lineage"]):
        return "layering"
    return "generic"


def collaboration_reentry_scope(feature: dict[str, Any]) -> str:
    text = feature_text(feature)
    positive = any(token in text for token in ["回流条件", "回流", "re-entry", "reentry", "revise", "retry"])
    negative = any(token in text for token in ["re-entry semantics outside this feat", "keeping approval and re-entry semantics outside this feat", "回流语义留在", "回流语义不在本 feat"])
    structured = isinstance(feature.get("identity_and_scenario"), dict) and isinstance(feature.get("collaboration_and_timeline"), dict)
    pending = any(token in text for token in ["gate pending", "pending-intake", "pending visibility", "authoritative handoff", "待审批状态", "交接正式送入 gate"])
    if positive and negative:
        return "routing" if structured and pending else "ambiguous"
    if negative:
        return "downstream"
    if positive:
        return "routing"
    return "none"


def implementation_architecture(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "implementation_architecture") or ["Freeze one implementation carrier for the selected FEAT boundary and keep adjacent responsibilities out of scope."]


def implementation_modules(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "implementation_modules") or ["Runtime carrier module", "Contract/validator module", "Evidence or receipt module"]


def state_model(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "state_model") or ["`prepared` -> `executed` -> `recorded`"]


def architecture_diagram(feature: dict[str, Any]) -> str:
    return _axis_text(feature, "architecture_diagram") or "\n".join(["```text", "[Boundary Placement] -> [Implementation Carrier] -> [Authoritative Output]", "```"])


def is_engineering_baseline_feature(feature: dict[str, Any]) -> bool:
    """Check if this is an engineering baseline FEAT (SRC003-style code bootstrap)."""
    src_ref = str(feature.get("src_root_id") or feature.get("src_ref") or "")
    feat_ref = str(feature.get("feat_ref") or "")
    title = str(feature.get("title") or "").lower()

    # Check for SRC-003 style engineering baseline
    if "SRC-003" in src_ref or "SRC003" in src_ref:
        return True

    # Check for engineering baseline patterns in feat_ref or title
    for pattern in ENGINEERING_BASELINE_FEAT_MAP.keys():
        if pattern in feat_ref.lower() or pattern in title:
            return True

    # Check for explicit axis marking
    axis = str(feature.get("axis_id") or "").lower()
    if "engineering" in axis or "baseline" in axis:
        return True

    return False


def get_engineering_baseline_type(feature: dict[str, Any]) -> str | None:
    """Get the specific engineering baseline type for this FEAT."""
    if not is_engineering_baseline_feature(feature):
        return None

    feat_ref = str(feature.get("feat_ref") or "")
    title = str(feature.get("title") or "").lower()

    for pattern, baseline_type in ENGINEERING_BASELINE_FEAT_MAP.items():
        if pattern in feat_ref.lower() or pattern in title:
            return baseline_type

    return None


def tech_runtime_view(feature: dict[str, Any]) -> str:
    # For engineering baseline FEATs, return FEAT-specific runtime view
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type:
        return "\n".join(["```text", f"[{baseline_type}/runtime.py] -> [{baseline_type}/contracts.py] -> [{baseline_type}/receipts.py]", "```"])
    return _axis_text(feature, "tech_runtime_view") or "\n".join(["```text", "[runtime.py] -> [contracts.py] -> [receipts.py]", "```"])


def flow_diagram(feature: dict[str, Any]) -> str:
    # For engineering baseline FEATs, return FEAT-specific flow
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type:
        return "\n".join(["```text", f"bootstrap -> {baseline_type} -> verify runnable", "```"])
    return _axis_text(feature, "flow_diagram") or "\n".join(["```text", "caller -> runtime -> authoritative record", "```"])


def implementation_strategy(feature: dict[str, Any]) -> list[str]:
    # For engineering baseline FEATs, return FEAT-specific strategy
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type and baseline_type in ENGINEERING_BASELINE_STRATEGY_MAP:
        return ENGINEERING_BASELINE_STRATEGY_MAP[baseline_type]
    return _axis_list(feature, "implementation_strategy") or ["Freeze contracts first, implement one authoritative carrier, then validate traceability and replay safety."]


def implementation_modules(feature: dict[str, Any]) -> list[str]:
    # For engineering baseline FEATs, return FEAT-specific modules
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type and baseline_type in ENGINEERING_BASELINE_MODULE_MAP:
        return ENGINEERING_BASELINE_MODULE_MAP[baseline_type]
    return _axis_list(feature, "implementation_modules") or ["Runtime carrier module", "Contract/validator module", "Evidence or receipt module"]


def implementation_unit_mapping(feature: dict[str, Any]) -> list[str]:
    # For engineering baseline FEATs, return FEAT-specific unit mapping
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type and baseline_type in ENGINEERING_BASELINE_UNIT_MAP:
        return ENGINEERING_BASELINE_UNIT_MAP[baseline_type]
    return _axis_list(feature, "implementation_unit_mapping") or ["`runtime.py` (`new`): authoritative carrier", "`contracts.py` (`new`): request/response validation"]


def main_sequence(feature: dict[str, Any]) -> list[str]:
    # For engineering baseline FEATs, return FEAT-specific sequence
    baseline_type = get_engineering_baseline_type(feature)
    if baseline_type and baseline_type in ENGINEERING_BASELINE_SEQUENCE_MAP:
        return ENGINEERING_BASELINE_SEQUENCE_MAP[baseline_type]
    return _axis_list(feature, "main_sequence") or ["1. normalize request", "2. execute authoritative carrier", "3. persist evidence and refs", "4. return structured result"]


def interface_contracts(feature: dict[str, Any]) -> list[str]:
    axis = feature_axis(feature)
    return INTERFACE_CONTRACTS_BY_AXIS.get(axis, [f"`{feature_axis(feature)}Request`: freeze a machine-readable request/response contract before implementation."])


def main_sequence(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "main_sequence") or ["1. normalize request", "2. execute authoritative carrier", "3. persist evidence and refs", "4. return structured result"]


def exception_compensation(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "exception_compensation") or ["preserve authoritative partial state and return a repairable degraded status instead of fabricating success"]


def integration_points(feature: dict[str, Any]) -> list[str]:
    return _axis_list(feature, "integration_points") or ["Caller enters through the governed CLI/runtime surface.", "Downstream consumers read only authoritative refs emitted by this FEAT."]


def minimal_code_skeleton(feature: dict[str, Any]) -> dict[str, str]:
    return _axis_dict(feature, "minimal_code_skeleton") or {
        "happy_path": "\n".join(["```python", "def execute(request):", "    normalized = normalize(request)", "    result = run_authoritative_carrier(normalized)", "    return build_result(result)", "```"]),
        "failure_path": "\n".join(["```python", "def execute_or_fail(request):", "    normalized = normalize(request)", "    if not normalized:", "        raise ValueError('invalid_request')", "    return execute(request)", "```"]),
    }

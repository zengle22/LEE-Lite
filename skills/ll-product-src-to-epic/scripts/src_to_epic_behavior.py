from __future__ import annotations

from typing import Any

from src_to_epic_behavior_execution import derive_execution_runner_behavior_slices
from src_to_epic_behavior_governance import derive_governance_bridge_behavior_slices
from src_to_epic_behavior_review import derive_review_projection_behavior_slices
from src_to_epic_identity import (
    derive_capability_axes,
    is_engineering_bootstrap_baseline_package,
    is_execution_runner_package,
    is_governance_bridge_package,
    is_implementation_readiness_package,
    is_review_projection_package,
)


def _implementation_readiness_behavior_slices() -> list[dict[str, Any]]:
    return [
        {
            "id": "impl_readiness_intake",
            "name": "IMPL 主测试对象 intake 与 authority 绑定流",
            "track": "foundation",
            "goal": "冻结 IMPL 进入 implementation start 前如何作为主测试对象被 intake，并与 FEAT / TECH / ARCH / API / UI / TESTSET authority 绑定。",
            "scope": "主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。",
            "product_surface": "impl readiness intake surface",
            "completed_state": "reviewer 能明确知道当前测试对象、authority refs 和执行模式。",
            "business_deliverable": "implementation readiness intake result",
            "capability_axes": ["main_test_object_priority", "authority_binding"],
            "overlay_families": [],
        },
        {
            "id": "cross_artifact_consistency_review",
            "name": "跨文档一致性与产品行为边界评审流",
            "track": "foundation",
            "goal": "冻结 IMPL 与联动 authority 之间的功能逻辑、状态、API、UI、旅程和测试可观测性检查。",
            "scope": "functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。",
            "product_surface": "cross-artifact review report",
            "completed_state": "关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。",
            "business_deliverable": "cross-artifact issue inventory",
            "capability_axes": ["conflict_detection", "product_behavior_boundary"],
            "overlay_families": [],
        },
        {
            "id": "counterexample_and_failure_path_simulation",
            "name": "失败路径与反例推演流",
            "track": "foundation",
            "goal": "冻结 deep mode 下的失败路径推演、counterexample 覆盖和恢复动作校验。",
            "scope": "非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。",
            "product_surface": "failure-path simulation summary",
            "completed_state": "高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。",
            "business_deliverable": "counterexample coverage result",
            "capability_axes": ["failure_path_simulation", "counterexample_coverage"],
            "overlay_families": [],
        },
        {
            "id": "readiness_verdict_and_repair_routing",
            "name": "实施 readiness verdict 与修复路由流",
            "track": "foundation",
            "goal": "冻结 score-to-verdict、blocking/high-priority issue 和 repair_target_artifact 的输出语义。",
            "scope": "dimension score、pass/pass_with_revisions/block verdict、repair target、missing information、repair plan。",
            "product_surface": "implementation readiness report",
            "completed_state": "implementation consumer 无需回读 ADR 即可知道能否开工、哪里要修、由谁修。",
            "business_deliverable": "implementation-readiness verdict package",
            "capability_axes": ["score_to_verdict", "repair_target_routing"],
            "overlay_families": [],
        },
    ]


def _engineering_bootstrap_behavior_slices() -> list[dict[str, Any]]:
    """Engineering bootstrap baseline behavior slices - each slice maps to one engineering object.

    These slices ensure the EPIC focuses on engineering skeleton/code bootstrap objects
    (repo layout, app shells, local env, migrations, health checks) rather than
    governance semantics (handoff/gate/formal/IO).
    """
    return [
        {
            "id": "repo-layout-baseline",
            "name": "代码库目录与落点基线",
            "track": "foundation",
            "goal": "冻结 repo layout 与新代码落点：业务实现只进 apps/；legacy src 不再增量；治理/产物目录只放说明与工件。",
            "scope": "src/, apps/, deploy/, scripts/, db/ 目录落点冻结；AGENTS.md/README.md/.gitkeep 占位；模块边界声明。",
            "product_surface": "repo layout skeleton with authoritative directory layout and module boundaries",
            "completed_state": "新成员能根据目录结构和文档说明理解代码落点约束，且实际实现不违反模块边界。",
            "business_deliverable": "repo layout baseline package with directory validator and skeleton generator",
            "capability_axes": ["代码库目录与落点基线能力"],
            "overlay_families": [],
        },
        {
            "id": "api-shell-runnable",
            "name": "Go API 空壳可运行",
            "track": "foundation",
            "goal": "提供可启动的 apps/api 骨架（模块边界、依赖注入/分层约束、最小路由），并确保 handler 不直接跑 raw SQL。",
            "scope": "apps/api 目录结构、main.go 入口、分层架构（handler/service/repository）、/healthz+/readyz 端点。",
            "product_surface": "runnable Go API shell with health endpoints and layered architecture",
            "completed_state": "apps/api 可独立启动，/healthz 返回 200，/readyz 在 DB 可用时返回 200。",
            "business_deliverable": "可运行的 API shell package 与分层架构示例",
            "capability_axes": ["Go API 空壳可运行能力"],
            "overlay_families": [],
        },
        {
            "id": "miniapp-shell-runnable",
            "name": "UniApp 小程序空壳可运行",
            "track": "foundation",
            "goal": "提供可启动的 apps/miniapp 骨架（页面落点与最小导航），与后端健康检查打通最小联通性验证。",
            "scope": "apps/miniapp 目录结构、pages/index、uni-app 配置、API 调用示例。",
            "product_surface": "runnable UniApp miniapp shell with navigation and API integration",
            "completed_state": "apps/miniapp 可独立编译预览，能调用后端/healthz 并展示结果。",
            "business_deliverable": "可运行的小程序 shell package 与导航示例",
            "capability_axes": ["UniApp MiniApp 空壳可运行能力"],
            "overlay_families": [],
        },
        {
            "id": "local-env-baseline",
            "name": "本地开发环境与 Postgres 基线",
            "track": "foundation",
            "goal": "冻结本地运行方式（compose/postgres、env vars、.env.example），保证新成员可复现启动，不引入密钥到仓库。",
            "scope": "docker-compose.local.yml、postgres 服务配置、.env.example、网络与端口约定。",
            "product_surface": "local development environment baseline with docker-compose and postgres",
            "completed_state": "新成员执行 docker compose up 即可启动本地开发环境，无需手动配置。",
            "business_deliverable": "本地环境基线 package 与一键启动脚本",
            "capability_axes": ["本地开发环境与 Postgres 基线能力"],
            "overlay_families": [],
        },
        {
            "id": "db-migrations-discipline",
            "name": "Migration 机制与初始 Schema 基线",
            "track": "foundation",
            "goal": "建立 db/migrations 作为唯一 schema 演进通道，禁止手工改库作为默认协作方式，并提供最小初始化迁移路径。",
            "scope": "db/migrations/目录、0001_init.up.sql、迁移执行工具、迁移纪律约束。",
            "product_surface": "database migrations discipline with versioned SQL files",
            "completed_state": "空库上执行 migrations 可完成初始化，schema 与代码预期一致。",
            "business_deliverable": "migration 机制 package 与初始 schema 迁移文件",
            "capability_axes": ["Migration 机制与初始 Schema 基线能力"],
            "overlay_families": [],
        },
        {
            "id": "healthz-readyz-contract",
            "name": "Healthz/ReadyZ 合约与可验证就绪性",
            "track": "foundation",
            "goal": "提供 /healthz 与 /readyz contract 与依赖检查边界，作为后续业务链进入前的最小可观测与可验收基线。",
            "scope": "/healthz 基础健康检查、/readyz 依赖可用性检查（DB、外部服务）、探针配置。",
            "product_surface": "health check contract with liveness and readiness probes",
            "completed_state": "探针能正确反映应用状态，k8s 或 compose 可基于探针做流量调度。",
            "business_deliverable": "健康检查合约 package 与探针配置示例",
            "capability_axes": ["Healthz/ReadyZ 合约与可验证就绪性能力"],
            "overlay_families": [],
        },
    ]


def _default_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    axes = derive_capability_axes(package, rollout_requirement)
    derived: list[dict[str, Any]] = []
    for axis in axes:
        derived.append(
            {
                "id": str(axis.get("id") or ""),
                "name": str(axis.get("feat_axis") or axis.get("name") or ""),
                "track": "foundation",
                "goal": f"冻结 {axis.get('feat_axis') or axis.get('name')} 这一产品行为切片。",
                "scope": str(axis.get("scope") or axis.get("feat_axis") or axis.get("name") or ""),
                "product_surface": str(axis.get("feat_axis") or axis.get("name") or "产品切片"),
                "completed_state": "该切片对应的产品行为已形成可验收、可交接的业务结果。",
                "business_deliverable": str(axis.get("feat_axis") or axis.get("name") or "产品交付物"),
                "capability_axes": [str(axis.get("name") or axis.get("feat_axis") or "")],
                "overlay_families": [],
            }
        )
    return derived


def derive_product_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if is_review_projection_package(package):
        return derive_review_projection_behavior_slices()
    if is_execution_runner_package(package):
        return derive_execution_runner_behavior_slices(package)
    if is_implementation_readiness_package(package):
        return _implementation_readiness_behavior_slices()
    if is_engineering_bootstrap_baseline_package(package):
        return _engineering_bootstrap_behavior_slices()
    if is_governance_bridge_package(package):
        return derive_governance_bridge_behavior_slices(package, rollout_requirement)
    return _default_behavior_slices(package, rollout_requirement)

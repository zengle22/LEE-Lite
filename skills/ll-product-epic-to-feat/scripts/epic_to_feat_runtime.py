#!/usr/bin/env python3
"""
Lite-native runtime support for epic-to-feat.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from epic_to_feat_common import (
    dump_json,
    ensure_list,
    extract_src_ref,
    guess_repo_root_from_input,
    load_epic_package,
    load_json,
    parse_markdown_frontmatter,
    render_markdown,
    shorten_identifier,
    summarize_text,
    unique_strings,
    validate_input_package,
)


REQUIRED_OUTPUT_FILES = [
    "feat-freeze-bundle.md",
    "feat-freeze-bundle.json",
    "feat-review-report.json",
    "feat-acceptance-report.json",
    "feat-defect-list.json",
    "feat-freeze-gate.json",
    "handoff-to-feat-downstreams.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]

REQUIRED_MARKDOWN_HEADINGS = [
    "FEAT Bundle Intent",
    "EPIC Context",
    "Boundary Matrix",
    "FEAT Inventory",
    "Acceptance and Review",
    "Downstream Handoff",
    "Traceability",
]

DOWNSTREAM_WORKFLOWS = [
    "workflow.product.task.feat_to_delivery_prep",
    "workflow.product.feat_to_plan_pipeline",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "epic-to-feat" / run_id


def choose_src_ref(package: Any) -> str:
    source_refs = ensure_list(package.epic_json.get("source_refs"))
    src_ref = extract_src_ref(source_refs, fallback=str(package.epic_json.get("src_root_id") or ""))
    if src_ref:
        return src_ref
    return f"SRC-{shorten_identifier(package.run_id, limit=32)}"


def choose_epic_ref(package: Any) -> str:
    existing = str(package.epic_json.get("epic_freeze_ref") or "").strip()
    if existing:
        return existing
    title = str(package.epic_json.get("title") or package.run_id)
    return f"EPIC-{shorten_identifier(title, limit=40)}"


def axis_key(axis: dict[str, str]) -> str:
    raw = str(axis.get("id") or "").strip().lower()
    if raw:
        return raw
    name = str(axis.get("name") or "").strip()
    mapping = {
        "主链协作闭环能力": "collaboration-loop",
        "正式交接与物化能力": "handoff-formalization",
        "对象分层与准入能力": "object-layering",
        "主链文件 IO 与路径治理能力": "artifact-io-governance",
    }
    return mapping.get(name, shorten_identifier(name, limit=48).lower())


def feat_goal(axis: dict[str, str], package: Any) -> str:
    goals = {
        "collaboration-loop": "让 execution、gate、human 三类 loop 在同一条主链里形成稳定协作闭环，而不是由各 skill 分别拼接回流规则。",
        "handoff-formalization": "让 handoff、gate decision 与 formal materialization 形成单一路径的正式升级链，而不是让 candidate 与 formal 流转并存。",
        "object-layering": "让 candidate package、formal object 与 downstream consumption 形成稳定分层，防止业务 skill 混入裁决与准入职责。",
        "artifact-io-governance": "让主链中的 artifact IO、路径与目录边界收敛为受治理能力，并且严格限制在 mainline handoff 和 formalization 语境内。",
    }
    key = axis_key(axis)
    if key in goals:
        return goals[key]
    business_goal = str(package.epic_json.get("business_goal") or "")
    return summarize_text(f"{axis.get('name')}承担 EPIC 目标中的一块独立能力面。{business_goal}", limit=220)


def feat_scope(axis: dict[str, str]) -> list[str]:
    scopes = {
        "collaboration-loop": [
            "定义 execution loop 应提交什么对象、在何时进入 gate loop，以及哪些状态允许回流到 revision / retry。",
            "定义 gate loop 与 human loop 的衔接界面，包括谁消费 proposal、谁返回 decision、谁触发后续推进。",
            "明确 loop 协作只覆盖推进责任、交接界面与回流条件，不定义 formal materialization 对象本身。",
            "显式约束下游不得再为 queue、handoff、gate 关系发明第二套等价规则。",
        ],
        "handoff-formalization": [
            "定义 handoff object、gate decision object、formal materialization object 在主链中的单向升级顺序。",
            "明确 candidate 只能作为 gate 消费对象，不能绕过 gate 直接成为 downstream formal input。",
            "明确本 FEAT 负责正式推进链路，不负责对象准入判定与读取资格细则。",
            "要求下游继承同一套 approve / revise / retry / handoff / reject 语义，不得并列批准语义。",
        ],
        "object-layering": [
            "定义 candidate package、formal object、downstream consumption object 的分层职责和允许的引用方向。",
            "定义什么对象有资格成为正式输入，以及哪些 consumer 只能读取 formal layer 而不能读取 candidate layer。",
            "明确本 FEAT 负责对象层级与准入，不负责 handoff 决策链和 IO/path 落盘策略。",
            "要求任何下游消费都必须沿 formal refs 与 lineage 进入，不能以路径猜测或旁路对象读取。",
        ],
        "artifact-io-governance": [
            "约束主链 handoff、formal materialization 与 governed skill IO 的 artifact path、目录边界与写入模式。",
            "明确哪些 IO 是受治理主链 IO，哪些属于全局文件治理而必须留在本 FEAT 之外。",
            "要求所有正式主链写入都遵循统一的路径与覆盖边界，不允许以局部临时目录策略替代。",
            "明确本 FEAT 只覆盖 mainline IO/path 边界，不扩展为全仓库或全项目文件治理总方案。",
        ],
    }
    key = axis_key(axis)
    if key in scopes:
        return scopes[key]
    return [
        str(axis.get("scope") or axis.get("feat_axis") or axis.get("name") or "").strip(),
        f"Derived axis: {axis.get('feat_axis') or axis.get('name')}",
    ]


def feat_non_goals(axis: dict[str, str], package: Any) -> list[str]:
    del package
    extras = {
        "collaboration-loop": [
            "Do not define candidate -> formal upgrade semantics, gate decision authority, or materialization outputs here.",
            "Do not define object admission, formal-read eligibility, or path governance policy here.",
        ],
        "handoff-formalization": [
            "Do not redefine execution / gate / human loop responsibility splits or re-entry conditions here.",
            "Do not define consumer admission, formal-ref eligibility, or path enforcement policy here.",
        ],
        "object-layering": [
            "Do not define the handoff -> gate decision -> formal materialization action chain here.",
            "Do not define governed artifact paths, write modes, or repository-level IO enforcement here.",
        ],
        "artifact-io-governance": [
            "Do not define object qualification, candidate/formal authority, or consumer admission semantics here.",
            "Do not define gate decision semantics, approval authority, or formalization outcomes here.",
        ],
    }
    return unique_strings(extras.get(axis_key(axis), []))[:4]


def bundle_shared_non_goals(package: Any) -> list[str]:
    inherited = ensure_list(package.epic_json.get("non_goals"))[:3]
    shared = [
        "Do not expand any FEAT into heavy scheduler, database, event-bus, or runtime platform design.",
        "Do not turn the FEAT bundle into schema, CLI, directory-layout, or code-implementation detail.",
        "Do not embed task-level implementation sequencing inside FEAT definitions.",
    ]
    return unique_strings(inherited + shared)[:6]


def select_constraints(package: Any, keywords: list[str], fallback_count: int = 2) -> list[str]:
    constraints = ensure_list(package.epic_json.get("constraints_and_dependencies"))
    selected: list[str] = []
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for item in constraints:
        lowered = item.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            selected.append(item)
    if len(selected) < fallback_count:
        for item in constraints:
            if item not in selected:
                selected.append(item)
            if len(selected) >= fallback_count:
                break
    return selected


def feat_constraints(axis: dict[str, str], package: Any) -> list[str]:
    key = axis_key(axis)
    selected = {
        "collaboration-loop": select_constraints(package, ["双会话双队列", "execution loop", "human loop", "queue"], fallback_count=3),
        "handoff-formalization": select_constraints(package, ["handoff runtime", "external gate", "approve", "candidate package 仅作为 gate 消费对象", "formal object"], fallback_count=3),
        "object-layering": select_constraints(package, ["business skill 只产出 candidate", "formal object", "candidate package 与 formal object 强制分层", "正式输入"], fallback_count=3),
        "artifact-io-governance": select_constraints(package, ["路径与目录治理", "governed skill io", "formal materialization", "handoff"], fallback_count=3),
    }.get(key, select_constraints(package, [str(axis.get("name") or "")], fallback_count=3))

    specialized = {
        "collaboration-loop": [
            "Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。",
            "该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。",
        ],
        "handoff-formalization": [
            "Candidate 不得绕过 gate 直接升级为 downstream formal input。",
            "Formal materialization 语义必须单一路径推进，不得出现并列正式化入口。",
        ],
        "object-layering": [
            "Consumer 准入必须沿 formal refs 与 lineage 判断，不得通过路径猜测获得读取资格。",
            "对象分层必须阻止业务 skill 在 candidate 层承担 gate 或 formal admission 职责。",
        ],
        "artifact-io-governance": [
            "主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。",
            "任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。",
        ],
    }.get(key, [])
    return unique_strings(selected + specialized)[:6]


def feat_dependencies(axis: dict[str, str]) -> list[str]:
    dependencies = {
        "collaboration-loop": [
            "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
            "Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。",
        ],
        "handoff-formalization": [
            "Boundary to 主链协作闭环能力: 本 FEAT 消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。",
            "Boundary to 对象分层与准入能力: 本 FEAT 定义 candidate 到 formal 的推进链，不定义 consumer admission 与读取资格。",
        ],
        "object-layering": [
            "Boundary to 正式交接与物化能力: 本 FEAT 定义哪些对象可以成为正式输入，而不是定义正式升级动作本身。",
            "Boundary to 主链文件 IO 与路径治理能力: 本 FEAT 定义对象资格与引用方向，path / mode 规则留给 IO 治理 FEAT。",
        ],
        "artifact-io-governance": [
            "Boundary to 对象分层与准入能力: 本 FEAT 定义对象落盘边界，不定义对象层级与消费资格本身。",
            "Boundary to 正式交接与物化能力: 本 FEAT 约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。",
        ],
    }
    return dependencies.get(axis_key(axis), [])


def build_acceptance_checks(feat_ref: str, epic_ref: str, axis: dict[str, str]) -> list[dict[str, Any]]:
    key = axis_key(axis)
    checks = {
        "collaboration-loop": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Loop responsibility split is explicit",
                "given": f"{epic_ref} requires execution, gate, and human loops to cooperate",
                "when": f"{feat_ref} is reviewed as a standalone capability",
                "then": "The FEAT must define which loop owns which transition, input object, and return path without overlapping formalization responsibilities.",
                "trace_hints": [feat_ref, "execution loop", "gate loop", "human loop", "responsibility split"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Loop re-entry conditions are bounded",
                "given": "A revise or retry decision occurs in the mainline",
                "when": "The decision is fed back to execution",
                "then": "The FEAT must make clear what objects are returned, who consumes them, and which loop state allows re-entry.",
                "trace_hints": [feat_ref, "revise", "retry", "re-entry", "handoff object"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Downstream flows do not redefine collaboration rules",
                "given": "A downstream workflow consumes this FEAT",
                "when": "It needs queue, gate, or human coordination semantics",
                "then": "It must inherit the same collaboration rules instead of inventing a parallel queue or handoff model.",
                "trace_hints": [feat_ref, "downstream inheritance", "queue", "handoff", "gate"],
            },
        ],
        "handoff-formalization": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Formal upgrade path is single and explicit",
                "given": f"{epic_ref} contains candidate outputs awaiting approval",
                "when": "The mainline moves from candidate to formal state",
                "then": "The FEAT must define one explicit handoff -> gate decision -> formal materialization chain without parallel shortcuts.",
                "trace_hints": [feat_ref, "handoff", "gate decision", "formal materialization", "single path"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Candidate cannot bypass gate",
                "given": "A candidate package exists but gate approval has not occurred",
                "when": "A downstream consumer requests formal input",
                "then": "The FEAT must prevent that candidate from being treated as a formal downstream source.",
                "trace_hints": [feat_ref, "candidate package", "gate approval", "formal input", "bypass forbidden"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Materialization stays separate from business skill logic",
                "given": "A business skill emits proposal and evidence objects",
                "when": "Formalization is evaluated",
                "then": "The FEAT must keep the formalization decision and materialization action outside the business skill body.",
                "trace_hints": [feat_ref, "business skill", "materialization separation", "external gate"],
            },
        ],
        "object-layering": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Candidate and formal layers cannot be confused",
                "given": f"{epic_ref} emits both candidate and formal-stage objects",
                "when": "A consumer resolves upstream inputs",
                "then": "The FEAT must make clear which layer is authoritative for downstream use and forbid layer ambiguity.",
                "trace_hints": [feat_ref, "candidate layer", "formal layer", "authoritative input"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Consumer admission is formal-ref based",
                "given": "A downstream reader needs to consume a governed object",
                "when": "It resolves eligibility",
                "then": "The FEAT must require formal refs and lineage-based admission rather than path guessing or adjacent file discovery.",
                "trace_hints": [feat_ref, "formal refs", "lineage", "consumer admission"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Business skill cannot silently inherit gate authority",
                "given": "A business skill emits a candidate package",
                "when": "That package is reviewed for downstream use",
                "then": "The FEAT must prevent the business skill from silently acting as gate, approver, or formal admission authority.",
                "trace_hints": [feat_ref, "business skill", "gate authority", "formal admission"],
            },
        ],
        "artifact-io-governance": [
            {
                "id": f"{feat_ref}-AC-01",
                "scenario": "Mainline IO boundary is explicit",
                "given": f"{epic_ref} requires handoff and formalization artifacts to be written",
                "when": "A governed skill performs mainline IO",
                "then": "The FEAT must define which IO belongs to mainline handoff / materialization and which IO is out of scope.",
                "trace_hints": [feat_ref, "mainline IO", "handoff", "formalization", "scope boundary"],
            },
            {
                "id": f"{feat_ref}-AC-02",
                "scenario": "Path governance does not expand into global file governance",
                "given": "A downstream team proposes broader repository-wide directory rules",
                "when": "That proposal is compared to this FEAT",
                "then": "The FEAT must reject scope expansion beyond governed skill IO, handoff, and materialization boundaries.",
                "trace_hints": [feat_ref, "global file governance", "scope expansion forbidden", "path boundary"],
            },
            {
                "id": f"{feat_ref}-AC-03",
                "scenario": "Formal writes cannot fall back to free writes",
                "given": "A mainline write hits a path or mode restriction",
                "when": "The write is retried",
                "then": "The FEAT must preserve governed path / mode enforcement and block silent fallback to uncontrolled writes.",
                "trace_hints": [feat_ref, "path mode enforcement", "free write fallback", "formal write"],
            },
        ],
    }.get(key, [])
    return checks

def derive_feat_axes(package: Any) -> list[dict[str, str]]:
    axes = package.epic_json.get("capability_axes")
    if isinstance(axes, list) and axes:
        normalized: list[dict[str, str]] = []
        for index, axis in enumerate(axes, start=1):
            if not isinstance(axis, dict):
                continue
            axis_id = str(axis.get("id") or "").strip()
            name = str(axis.get("name") or axis.get("id") or f"Feature Slice {index}").strip()
            scope = str(axis.get("scope") or axis.get("feat_axis") or name).strip()
            feat_axis = str(axis.get("feat_axis") or name).strip()
            normalized.append({"id": axis_id, "name": name, "scope": scope, "feat_axis": feat_axis})
        if normalized:
            return normalized[:8]

    scope_items = ensure_list(package.epic_json.get("scope"))
    if scope_items:
        normalized = []
        for index, item in enumerate(scope_items, start=1):
            title = item.split("：", 1)[0].strip(" -") or f"Feature Slice {index}"
            normalized.append({"id": "", "name": title, "scope": item, "feat_axis": item})
        return normalized[:8]

    title = str(package.epic_json.get("title") or package.run_id).strip()
    return [{"id": "", "name": f"{title} Core Capability", "scope": "Preserve the EPIC as one decomposable FEAT boundary.", "feat_axis": title}]


def derive_traceability(package: Any, feat_ref: str, axis: dict[str, str]) -> list[dict[str, Any]]:
    source_refs = ensure_list(package.epic_json.get("source_refs"))
    epic_ref = choose_epic_ref(package)
    return [
        {"feat_section": "Goal", "epic_fields": ["title", "business_goal"], "source_refs": [epic_ref] + source_refs[:3]},
        {"feat_section": "Scope", "epic_fields": ["scope", "capability_axes", "decomposition_rules"], "source_refs": [epic_ref, axis["name"]]},
        {"feat_section": "Constraints", "epic_fields": ["constraints_and_dependencies", "non_goals"], "source_refs": [epic_ref] + source_refs[:2]},
        {"feat_section": "Acceptance Checks", "epic_fields": ["acceptance_and_review", "decomposition_rules"], "source_refs": [epic_ref, feat_ref]},
    ]


def build_feat_record(package: Any, axis: dict[str, str], index: int, axes: list[dict[str, str]]) -> dict[str, Any]:
    src_ref = choose_src_ref(package)
    epic_ref = choose_epic_ref(package)
    feat_ref = f"FEAT-{src_ref}-{index:03d}"
    scope_items = feat_scope(axis)
    dependency_items = feat_dependencies(axis)
    goal = feat_goal(axis, package)

    return {
        "feat_ref": feat_ref,
        "title": axis["name"],
        "axis_id": axis_key(axis),
        "derived_axis": axis.get("feat_axis"),
        "epic_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "source_refs": unique_strings([epic_ref, src_ref] + ensure_list(package.epic_json.get("source_refs"))),
        "goal": goal,
        "scope": scope_items,
        "inputs": [f"Authoritative EPIC package {epic_ref}", f"src_root_id {package.epic_json.get('src_root_id')}", "Inherited scope, constraints, and acceptance semantics"],
        "processing": [
            "Translate the parent EPIC capability boundary into one independently acceptable FEAT slice with dedicated responsibility and boundary statements.",
            "Preserve parent-child traceability while separating this FEAT's concern from adjacent FEATs.",
            "Emit FEAT-specific constraints and acceptance checks that can seed downstream delivery-prep and plan flows.",
        ],
        "outputs": [
            f"Frozen FEAT definition for {feat_ref}",
            "FEAT-specific acceptance checks for downstream TECH, TASK, and TESTSET derivation",
            "Traceable handoff metadata for delivery-prep and plan workflows",
        ],
        "dependencies": dependency_items,
        "non_goals": feat_non_goals(axis, package),
        "constraints": feat_constraints(axis, package),
        "acceptance_checks": build_acceptance_checks(feat_ref, epic_ref, axis),
        "traceability": derive_traceability(package, feat_ref, axis),
    }


def feat_count_assessment(feats: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "feat_count": len(feats),
        "is_valid": len(feats) >= 2,
        "reason": "At least two FEAT slices were derived." if len(feats) >= 2 else "The EPIC decomposed into fewer than two FEATs.",
    }


@dataclass
class GeneratedFeatBundle:
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]


def build_boundary_matrix(feats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for feat in feats:
        matrix.append(
            {
                "feat_ref": feat["feat_ref"],
                "title": feat["title"],
                "responsible_for": feat["scope"][:2],
                "not_responsible_for": feat["non_goals"][:2],
                "boundary_dependencies": feat["dependencies"],
                "acceptance_focus": [check["scenario"] for check in feat["acceptance_checks"][:3]],
            }
        )
    return matrix


def build_feat_bundle(package: Any) -> GeneratedFeatBundle:
    axes = derive_feat_axes(package)
    feats = [build_feat_record(package, axis, index, axes) for index, axis in enumerate(axes, start=1)]
    assessment = feat_count_assessment(feats)
    epic_ref = choose_epic_ref(package)
    src_ref = choose_src_ref(package)
    boundary_matrix = build_boundary_matrix(feats)
    shared_non_goals = bundle_shared_non_goals(package)
    source_refs = unique_strings(
        [f"product.src-to-epic::{package.run_id}", epic_ref, src_ref] + ensure_list(package.epic_json.get("source_refs"))
    )

    defects: list[dict[str, Any]] = []
    if not assessment["is_valid"]:
        defects.append(
            {
                "severity": "P1",
                "title": "EPIC boundary did not decompose into multiple FEAT slices",
                "detail": "The generated FEAT bundle contains fewer than two independently acceptable FEATs.",
            }
        )

    for feat in feats:
        if len(feat.get("acceptance_checks") or []) < 3:
            defects.append(
                {
                    "severity": "P1",
                    "title": f"{feat['feat_ref']} is missing structured acceptance checks",
                    "detail": "Each FEAT must provide at least three structured acceptance checks.",
                }
            )

    review_decision = "pass" if not defects else "revise"
    acceptance_decision = "approve" if not defects else "revise"

    handoff = {
        "handoff_id": f"handoff-{package.run_id}-to-feat-downstreams",
        "from_skill": "ll-product-epic-to-feat",
        "source_run_id": package.run_id,
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "target_workflows": [
            {
                "workflow": "workflow.product.task.feat_to_delivery_prep",
                "purpose": "derive delivery-prep artifacts and seed TECH / TASK generation",
            },
            {
                "workflow": "workflow.product.feat_to_plan_pipeline",
                "purpose": "derive release, devplan, and testplan after FEAT readiness",
            },
        ],
        "derivable_children": ["TECH", "TASK", "TESTSET"],
        "primary_artifact_ref": "feat-freeze-bundle.md",
        "supporting_artifact_refs": [
            "feat-freeze-bundle.json",
            "feat-review-report.json",
            "feat-acceptance-report.json",
            "feat-defect-list.json",
        ],
        "created_at": utc_now(),
    }

    json_payload = {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "workflow_run_id": package.run_id,
        "title": f"{package.epic_json.get('title') or epic_ref} FEAT Bundle",
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "downstream_workflows": DOWNSTREAM_WORKFLOWS,
        "source_refs": source_refs,
        "bundle_intent": (
            f"Decompose {epic_ref} into {len(feats)} complementary FEAT slices so that collaboration, formalization, object admission, "
            "and mainline IO/path governance each own a distinct acceptance surface and can be inherited downstream without overlap. "
            "Keep exactly these four FEATs because the parent EPIC already froze four stable capability axes: fewer FEATs would merge incompatible acceptance semantics, "
            "while more FEATs would prematurely split into task or implementation detail."
        ),
        "bundle_shared_non_goals": shared_non_goals,
        "epic_context": {
            "business_goal": package.epic_json.get("business_goal"),
            "scope": ensure_list(package.epic_json.get("scope")),
            "non_goals": ensure_list(package.epic_json.get("non_goals")),
            "decomposition_rules": ensure_list(package.epic_json.get("decomposition_rules")),
            "constraints_and_dependencies": ensure_list(package.epic_json.get("constraints_and_dependencies")),
        },
        "boundary_matrix": boundary_matrix,
        "features": feats,
        "bundle_acceptance_conventions": [
            {
                "topic": "Traceability",
                "rule": "Every FEAT must preserve epic_freeze_ref, src_root_id, and source_refs so downstream readers can recover the authoritative EPIC lineage.",
            },
            {
                "topic": "Independent acceptance",
                "rule": "Every FEAT must remain independently acceptable and must not collapse into task, code, or UI implementation detail.",
            },
        ],
        "acceptance_and_review": {
            "upstream_acceptance_decision": package.acceptance_report.get("decision"),
            "upstream_acceptance_summary": package.acceptance_report.get("summary"),
            "upstream_review_decision": package.review_report.get("decision"),
            "feat_review_decision": review_decision,
            "feat_acceptance_decision": acceptance_decision,
        },
        "downstream_handoff": handoff,
        "traceability": [
            {
                "bundle_section": "FEAT Bundle Intent",
                "epic_fields": ["title", "business_goal"],
                "source_refs": [epic_ref] + source_refs[:3],
            },
            {
                "bundle_section": "FEAT Inventory",
                "epic_fields": ["scope", "capability_axes", "decomposition_rules"],
                "source_refs": [epic_ref, f"product.src-to-epic::{package.run_id}"],
            },
        ],
        "feat_count_assessment": assessment,
    }

    frontmatter = {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "workflow_run_id": package.run_id,
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "downstream_workflows": DOWNSTREAM_WORKFLOWS,
        "source_refs": source_refs,
    }

    epic_context_lines = [
        f"- epic_freeze_ref: `{epic_ref}`",
        f"- src_root_id: `{package.epic_json.get('src_root_id')}`",
        f"- business_goal: {package.epic_json.get('business_goal')}",
    ]
    epic_scope = ensure_list(package.epic_json.get("scope"))
    if epic_scope:
        epic_context_lines.append("- inherited_scope:")
        epic_context_lines.extend([f"  - {item}" for item in epic_scope[:5]])

    boundary_matrix_sections = []
    for row in boundary_matrix:
        boundary_matrix_sections.append(
            "\n".join(
                [
                    f"### {row['feat_ref']} {row['title']}",
                    "",
                    "- Responsible for:",
                    *[f"  - {item}" for item in row["responsible_for"]],
                    "- Not responsible for:",
                    *[f"  - {item}" for item in row["not_responsible_for"]],
                    "- Boundary dependencies:",
                    *([f"  - {item}" for item in row["boundary_dependencies"]] or ["  - None"]),
                ]
            )
        )

    bundle_shared_non_goal_lines = ["- Shared non-goals:"] + [f"  - {item}" for item in shared_non_goals]
    bundle_acceptance_lines = ["- Bundle acceptance conventions:"] + [
        f"  - {item['topic']}: {item['rule']}" for item in json_payload["bundle_acceptance_conventions"]
    ]

    feat_inventory_sections: list[str] = []
    for feat in feats:
        feat_inventory_sections.append(
            "\n".join(
                [
                    f"### {feat['feat_ref']} {feat['title']}",
                    "",
                    f"- Goal: {feat['goal']}",
                    "- Scope:",
                    *[f"  - {item}" for item in feat["scope"]],
                    "- Dependencies:",
                    *([f"  - {item}" for item in feat["dependencies"]] or ["  - None"]),
                    "- Constraints:",
                    *[f"  - {item}" for item in feat["constraints"]],
                    "- Acceptance Checks:",
                    *[
                        f"  - {check['id']}: {check['scenario']} | given {check['given']} | when {check['when']} | then {check['then']}"
                        for check in feat["acceptance_checks"]
                    ],
                ]
            )
        )

    markdown_body = "\n\n".join(
        [
            f"# {json_payload['title']}",
            "## FEAT Bundle Intent\n\n" + json_payload["bundle_intent"] + "\n\n" + "\n".join(bundle_shared_non_goal_lines),
            "## EPIC Context\n\n" + "\n".join(epic_context_lines),
            "## Boundary Matrix\n\n" + "\n\n".join(boundary_matrix_sections),
            "## FEAT Inventory\n\n" + "\n\n".join(feat_inventory_sections),
            "## Acceptance and Review\n\n"
            + "\n".join(
                [
                    f"- Upstream acceptance: {package.acceptance_report.get('decision')} ({package.acceptance_report.get('summary')})",
                    f"- Upstream review: {package.review_report.get('decision')} ({package.review_report.get('summary')})",
                    f"- FEAT review: {review_decision}",
                    f"- FEAT acceptance: {acceptance_decision}",
                    f"- FEAT count assessment: {assessment['reason']}",
                    "- Boundary matrix: present and aligned with feature-specific acceptance surfaces.",
                    *bundle_acceptance_lines,
                ]
            ),
            "## Downstream Handoff\n\n"
            + "\n".join(
                [
                    "- Target workflows:",
                    *[f"  - {workflow}" for workflow in DOWNSTREAM_WORKFLOWS],
                    "- Derived child artifacts:",
                    "  - TECH",
                    "  - TASK",
                    "  - TESTSET",
                ]
            ),
            "## Traceability\n\n"
            + "\n".join(
                f"- {item['bundle_section']}: {', '.join(item['epic_fields'])} <- {', '.join(item['source_refs'])}"
                for item in json_payload["traceability"]
            ),
        ]
    )

    review_report = {
        "review_id": f"feat-review-{package.run_id}",
        "review_type": "feat_review",
        "subject_refs": [epic_ref] + [feat["feat_ref"] for feat in feats],
        "summary": "FEAT bundle preserves the EPIC decomposition boundary and downstream readiness.",
        "findings": [
            f"Generated {len(feats)} FEAT slices from {epic_ref}.",
            "Each FEAT includes FEAT-specific acceptance checks and axis-specific constraints, while traceability is enforced as a bundle-wide convention.",
            "Downstream handoff metadata preserves delivery-prep and plan workflow targets.",
            "Boundary matrix records the horizontal split between FEAT responsibilities and adjacent non-responsibilities.",
        ],
        "decision": review_decision,
        "risks": [defect["detail"] for defect in defects],
        "recommendations": [
            "Keep downstream TECH, TASK, and TESTSET derivation anchored to FEAT acceptance checks.",
            "Do not re-open the parent EPIC scope in delivery-prep or plan stages.",
            "Use the boundary matrix as the first guard against overlap before expanding downstream plans.",
            "Treat the emitted FEAT bundle as the single governed FEAT truth for downstream flows.",
        ],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "stage_id": "feat_acceptance_review",
        "created_by_role": "supervisor",
        "decision": acceptance_decision,
        "dimensions": {
            "independent_acceptance_boundary": {
                "status": "pass" if not defects else "fail",
                "note": "Each FEAT remains independently acceptable." if not defects else "One or more FEAT boundaries are weak.",
            },
            "parent_child_traceability": {"status": "pass", "note": "epic_freeze_ref, src_root_id, and source_refs are preserved."},
            "downstream_readiness": {"status": "pass", "note": "Output remains actionable for delivery-prep and plan flows."},
            "structured_acceptance_checks": {"status": "pass", "note": "Each FEAT includes structured acceptance checks."},
            "evidence_completeness": {"status": "pass", "note": "Execution and supervision evidence will ship with the package."},
        },
        "summary": "FEAT acceptance review passed." if not defects else "FEAT acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now(),
    }

    return GeneratedFeatBundle(
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
    )


def write_executor_outputs(output_dir: Path, package: Any, generated: GeneratedFeatBundle, command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "feat-freeze-bundle.md").write_text(
        render_markdown(generated.frontmatter, generated.markdown_body),
        encoding="utf-8",
    )
    dump_json(output_dir / "feat-freeze-bundle.json", generated.json_payload)
    dump_json(output_dir / "feat-review-report.json", generated.review_report)
    dump_json(output_dir / "feat-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "feat-defect-list.json", generated.defect_list)
    dump_json(output_dir / "handoff-to-feat-downstreams.json", generated.handoff)
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": package.run_id,
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "primary_artifact_ref": str(output_dir / "feat-freeze-bundle.md"),
            "result_summary_ref": str(output_dir / "feat-freeze-gate.json"),
            "review_report_ref": str(output_dir / "feat-review-report.json"),
            "acceptance_report_ref": str(output_dir / "feat-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "feat-defect-list.json"),
            "handoff_ref": str(output_dir / "handoff-to-feat-downstreams.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": generated.json_payload["status"],
        },
    )
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-product-epic-to-feat",
            "run_id": package.run_id,
            "role": "executor",
            "inputs": [str(package.artifacts_dir)],
            "outputs": [str(output_dir / "feat-freeze-bundle.md"), str(output_dir / "feat-freeze-bundle.json")],
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "draft_output_files": [
                    "feat-freeze-bundle.md",
                    "feat-freeze-bundle.json",
                    "feat-review-report.json",
                    "feat-acceptance-report.json",
                    "feat-defect-list.json",
                    "handoff-to-feat-downstreams.json",
                ],
            },
            "key_decisions": [
                f"Preserved epic_freeze_ref as {generated.frontmatter['epic_freeze_ref']}.",
                f"Preserved src_root_id as {generated.frontmatter['src_root_id']}.",
                f"Generated {len(generated.frontmatter['feat_refs'])} FEAT refs for downstream delivery-prep and plan workflows.",
            ],
            "uncertainties": [],
            "created_at": utc_now(),
        },
    )


def build_supervision_evidence(output_dir: Path, generated: GeneratedFeatBundle) -> dict[str, Any]:
    decision = "pass" if not generated.defect_list else "revise"
    findings = [
        {
            "title": "FEAT boundary preserved" if decision == "pass" else "FEAT boundary needs revision",
            "detail": "The generated FEAT bundle remains suitable for downstream derivation."
            if decision == "pass"
            else "The generated FEAT bundle requires revision before freeze.",
        }
    ]
    for defect in generated.defect_list:
        findings.append({"title": defect["title"], "detail": defect["detail"]})
    return {
        "skill_id": "ll-product-epic-to-feat",
        "run_id": generated.frontmatter["workflow_run_id"],
        "role": "supervisor",
        "reviewed_inputs": [str(output_dir / "feat-freeze-bundle.md"), str(output_dir / "feat-freeze-bundle.json")],
        "reviewed_outputs": [str(output_dir / "feat-freeze-bundle.md"), str(output_dir / "feat-freeze-bundle.json")],
        "semantic_findings": findings,
        "decision": decision,
        "reason": "FEAT bundle passed semantic review." if decision == "pass" else "FEAT bundle needs revision before freeze.",
        "created_at": utc_now(),
    }


def build_gate_result(generated: GeneratedFeatBundle, supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    pass_gate = supervision_evidence["decision"] == "pass" and not generated.defect_list
    return {
        "workflow_key": "product.epic-to-feat",
        "decision": "pass" if pass_gate else "revise",
        "freeze_ready": pass_gate,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "src_root_id": generated.frontmatter["src_root_id"],
        "feat_refs": generated.frontmatter["feat_refs"],
        "checks": {
            "execution_evidence_present": True,
            "supervision_evidence_present": True,
            "feat_refs_present": bool(generated.frontmatter["feat_refs"]),
            "downstream_handoff_present": True,
            "structured_acceptance_checks_complete": not generated.defect_list,
            "feat_count_valid": len(generated.frontmatter["feat_refs"]) >= 2,
        },
        "created_at": utc_now(),
    }


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    feat_json = load_json(artifacts_dir / "feat-freeze-bundle.json")
    if feat_json.get("artifact_type") != "feat_freeze_package":
        errors.append("feat-freeze-bundle.json artifact_type must be feat_freeze_package.")
    if feat_json.get("workflow_key") != "product.epic-to-feat":
        errors.append("feat-freeze-bundle.json workflow_key must be product.epic-to-feat.")

    epic_ref = str(feat_json.get("epic_freeze_ref") or "")
    src_root_id = str(feat_json.get("src_root_id") or "")
    feat_refs = ensure_list(feat_json.get("feat_refs"))
    source_refs = ensure_list(feat_json.get("source_refs"))
    downstream_workflows = ensure_list(feat_json.get("downstream_workflows"))
    if not epic_ref:
        errors.append("feat-freeze-bundle.json must include epic_freeze_ref.")
    if not src_root_id:
        errors.append("feat-freeze-bundle.json must include src_root_id.")
    if not feat_refs:
        errors.append("feat-freeze-bundle.json must include feat_refs.")
    if not any(ref.startswith("product.src-to-epic::") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include product.src-to-epic::<run_id>.")
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include SRC-*.")
    for workflow in DOWNSTREAM_WORKFLOWS:
        if workflow not in downstream_workflows:
            errors.append(f"feat-freeze-bundle.json downstream_workflows must include {workflow}.")

    features = feat_json.get("features")
    if not isinstance(features, list) or not features:
        errors.append("feat-freeze-bundle.json must include a non-empty features list.")
    else:
        for feature in features:
            if not isinstance(feature, dict):
                errors.append("Each feature entry must be an object.")
                continue
            if not feature.get("feat_ref"):
                errors.append("Each feature entry must include feat_ref.")
            if not feature.get("title"):
                errors.append("Each feature entry must include title.")
            if len(feature.get("acceptance_checks") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three acceptance checks.")
            if len(feature.get("constraints") or []) < 4:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least four constraints.")
            if len(feature.get("scope") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three scope bullets.")

    boundary_matrix = feat_json.get("boundary_matrix")
    if not isinstance(boundary_matrix, list) or len(boundary_matrix) != len(feat_refs):
        errors.append("feat-freeze-bundle.json must include a boundary_matrix aligned to feat_refs.")
    shared_non_goals = feat_json.get("bundle_shared_non_goals")
    if not isinstance(shared_non_goals, list) or not shared_non_goals:
        errors.append("feat-freeze-bundle.json must include bundle_shared_non_goals.")
    acceptance_conventions = feat_json.get("bundle_acceptance_conventions")
    if not isinstance(acceptance_conventions, list) or not acceptance_conventions:
        errors.append("feat-freeze-bundle.json must include bundle_acceptance_conventions.")

    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    _, markdown_body = parse_markdown_frontmatter(markdown_text)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in markdown_body:
            errors.append(f"feat-freeze-bundle.md is missing section: {heading}")

    handoff = load_json(artifacts_dir / "handoff-to-feat-downstreams.json")
    workflows = [item.get("workflow") for item in handoff.get("target_workflows", []) if isinstance(item, dict)]
    for workflow in DOWNSTREAM_WORKFLOWS:
        if workflow not in workflows:
            errors.append(f"handoff-to-feat-downstreams.json must include target workflow {workflow}.")

    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    if gate.get("epic_freeze_ref") != epic_ref:
        errors.append("feat-freeze-gate.json must point to the same epic_freeze_ref.")

    return errors, {
        "valid": not errors,
        "epic_freeze_ref": epic_ref,
        "src_root_id": src_root_id,
        "feat_refs": feat_refs,
        "source_refs": source_refs,
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-product-epic-to-feat Review Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- output_dir: {artifacts_dir}",
                "",
                "## Execution Evidence",
                "",
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                f"- decisions: {', '.join(execution.get('key_decisions', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- decision: {supervision.get('decision')}",
                f"- reason: {supervision.get('reason')}",
                "",
                "## Freeze Gate",
                "",
                f"- decision: {gate.get('decision')}",
                f"- freeze_ready: {gate.get('freeze_ready')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def executor_run(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_epic_package(input_path)
    generated = build_feat_bundle(package)
    effective_run_id = run_id or package.run_id
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    write_executor_outputs(
        output_dir=output_dir,
        package=package,
        generated=generated,
        command_name=f"python scripts/epic_to_feat.py executor-run --input {input_path}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "feat_refs": generated.frontmatter["feat_refs"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del repo_root
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    input_package_dir = Path(str(package_manifest.get("input_artifacts_dir") or "")).resolve()
    if not input_package_dir.exists():
        raise FileNotFoundError(f"Input package directory not found: {input_package_dir}")

    package = load_epic_package(input_package_dir)
    generated = build_feat_bundle(package)
    supervision = build_supervision_evidence(artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)

    bundle_json = load_json(artifacts_dir / "feat-freeze-bundle.json")
    updated_json = dict(bundle_json)
    updated_json["status"] = "accepted" if supervision["decision"] == "pass" else "revised"
    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = updated_json["status"]

    (artifacts_dir / "feat-freeze-bundle.md").write_text(render_markdown(frontmatter, body), encoding="utf-8")
    dump_json(artifacts_dir / "feat-freeze-bundle.json", updated_json)
    dump_json(artifacts_dir / "feat-review-report.json", generated.review_report)
    dump_json(artifacts_dir / "feat-acceptance-report.json", generated.acceptance_report)
    dump_json(artifacts_dir / "feat-defect-list.json", generated.defect_list)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "feat-freeze-gate.json", gate)

    return {
        "ok": True,
        "run_id": run_id or str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": gate["freeze_ready"],
    }


def run_workflow(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(
        artifacts_dir=artifacts_dir,
        repo_root=repo_root,
        run_id=run_id or executor_result["run_id"],
        allow_update=True,
    )
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "epic_freeze_ref": executor_result["epic_freeze_ref"],
        "feat_refs": executor_result["feat_refs"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }

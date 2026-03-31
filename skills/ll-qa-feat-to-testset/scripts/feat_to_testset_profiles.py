#!/usr/bin/env python3
"""Feature profile classification helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, normalize_semantic_lock

PRODUCT_PROFILE_AXIS_MAP = {
    "minimal-onboarding-flow": "minimal_onboarding",
    "first-ai-advice-release": "first_ai_advice",
    "extended-profile-progressive-completion": "extended_profile_completion",
    "device-connect-deferred-entry": "device_deferred_entry",
    "state-and-profile-boundary-alignment": "state_profile_boundary",
}


def derive_semantic_lock(feature: dict[str, Any]) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    if lock:
        return lock
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id == "minimal-onboarding-flow":
        return {
            "domain_type": "product_onboarding_test_rule",
            "one_sentence_truth": "TESTSET must validate the one-page minimal profile flow, profile_minimal_done completion, homepage entry, and deferred device connection boundary.",
            "primary_object": "最小建档 首页",
            "lifecycle_stage": "profile_minimal_done homepage",
            "allowed_capabilities": [
                "最小建档",
                "首页",
                "profile_minimal_done",
                "birthdate",
                "running_level",
                "recent_injury_status",
                "设备绑定",
            ],
            "forbidden_capabilities": [
                "authoritative decision object",
                "formal publication trigger",
                "cutover_guard_ref",
                "pilot evidence package",
                "compat_mode",
                "wave state",
            ],
            "inheritance_rule": "TESTSET must stay on onboarding completion semantics and must not drift into pilot/gate governance coverage.",
        }
    if axis_id == "first-ai-advice-release":
        return {
            "domain_type": "first_advice_release_test_rule",
            "one_sentence_truth": "TESTSET must validate first advice release, risk-gate blocking, minimum output fields, and the non-dependency on extended profile or device data.",
            "primary_object": "首轮 ai 建议",
            "lifecycle_stage": "advice_visible risk_gate",
            "allowed_capabilities": [
                "首轮 AI 建议",
                "training_advice_level",
                "first_week_action",
                "needs_more_info_prompt",
                "device_connect_prompt",
                "running_level",
                "recent_injury_status",
            ],
            "forbidden_capabilities": [
                "authoritative decision object",
                "formal publication trigger",
                "approve / revise / retry / handoff / reject",
                "candidate package",
            ],
            "inheritance_rule": "TESTSET must stay on first-advice/risk-gate semantics and must not drift into gate-decision testing.",
        }
    if axis_id == "extended-profile-progressive-completion":
        return {
            "domain_type": "extended_profile_completion_test_rule",
            "one_sentence_truth": "TESTSET must validate homepage task-card progressive completion, incremental save, completion updates, and retryable save failures that do not revoke homepage access.",
            "primary_object": "首页 任务卡 增量保存",
            "lifecycle_stage": "profile_extension homepage_entered",
            "allowed_capabilities": [
                "首页任务卡",
                "增量保存",
                "completion percent",
                "next_task_cards",
                "retry",
            ],
            "forbidden_capabilities": [
                "authoritative decision object",
                "formal publication trigger",
                "approve / revise / retry / handoff / reject",
                "candidate package",
            ],
            "inheritance_rule": "TESTSET must stay on progressive-completion semantics and must not drift into gate-decision testing.",
        }
    if axis_id == "device-connect-deferred-entry":
        return {
            "domain_type": "device_deferred_entry_test_rule",
            "one_sentence_truth": "TESTSET must validate deferred device entry, skip/non-blocking failure behavior, and the preservation of homepage and first-advice availability.",
            "primary_object": "设备连接 首页",
            "lifecycle_stage": "homepage_entered device_connection",
            "allowed_capabilities": [
                "设备连接",
                "首页",
                "首轮建议",
                "device_failed_nonblocking",
                "device_skipped",
            ],
            "forbidden_capabilities": [
                "authoritative decision object",
                "formal publication trigger",
                "approve / revise / retry / handoff / reject",
                "candidate package",
            ],
            "inheritance_rule": "TESTSET must stay on deferred-device-entry semantics and must not drift into gate-decision testing.",
        }
    if axis_id == "state-and-profile-boundary-alignment":
        return {
            "domain_type": "state_profile_boundary_test_rule",
            "one_sentence_truth": "TESTSET must validate primary_state / capability_flags separation, canonical ownership in user_physical_profile, conflict_blocked fail-closed behavior, and unified-reader judgments.",
            "primary_object": "primary_state capability_flags user_physical_profile",
            "lifecycle_stage": "canonical_profile_boundary conflict_blocked",
            "allowed_capabilities": [
                "primary_state",
                "capability_flags",
                "user_physical_profile",
                "runner_profiles",
                "conflict_blocked",
                "canonical_profile_boundary",
            ],
            "forbidden_capabilities": [
                "authoritative decision object",
                "formal publication trigger",
                "approve / revise / retry / handoff / reject",
                "candidate package",
            ],
            "inheritance_rule": "TESTSET must stay on state/profile-boundary semantics and must not drift into gate-decision testing.",
        }
    return {}


def feature_profile(feature: dict[str, Any]) -> str:
    lock = derive_semantic_lock(feature)
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id in PRODUCT_PROFILE_AXIS_MAP:
        return PRODUCT_PROFILE_AXIS_MAP[axis_id]
    if axis_id == "skill-adoption-e2e":
        return "pilot"
    if axis_id == "ready-job-emission":
        return "runner_ready_job"
    if axis_id == "runner-operator-entry":
        return "runner_operator_entry"
    if axis_id == "runner-control-surface":
        return "runner_control_surface"
    if axis_id == "execution-runner-intake":
        return "runner_intake"
    if axis_id == "next-skill-dispatch":
        return "runner_dispatch"
    if axis_id == "execution-result-feedback":
        return "runner_feedback"
    if axis_id == "runner-observability-surface":
        return "runner_observability"
    if axis_id == "projection-generation":
        return "projection_generation"
    if axis_id == "authoritative-snapshot":
        return "authoritative_snapshot"
    if axis_id == "review-focus-risk":
        return "review_focus_risk"
    if axis_id == "feedback-writeback":
        return "feedback_writeback"
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        title = str(feature.get("title") or "").lower()
        if "snapshot" in title:
            return "authoritative_snapshot"
        if "review focus" in title or "风险" in title or "ambigu" in title:
            return "review_focus_risk"
        if "writeback" in title or "回写" in title or "批注" in title:
            return "feedback_writeback"
        return "projection_generation"
    if str(lock.get("domain_type") or "").strip().lower() == "execution_runner_rule":
        title = str(feature.get("title") or "").lower()
        scope_text = " ".join(
            ensure_list(feature.get("scope"))
            + ensure_list(feature.get("constraints"))
            + ensure_list(feature.get("dependencies"))
            + ensure_list(feature.get("non_goals"))
        ).lower()
        pilot_text = f"{title} {scope_text}"
        if any(
            marker in pilot_text
            for marker in [
                "governed skill",
                "onboarding",
                "pilot",
                "cutover",
                "fallback",
                "migration wave",
                "接入",
                "验证流",
                "迁移波次",
            ]
        ):
            return "pilot"
        if "用户入口" in title or "skill entry" in title:
            return "runner_operator_entry"
        if "控制面" in title or "control surface" in title:
            return "runner_control_surface"
        if "自动取件" in title or "intake" in title or "claim" in title:
            return "runner_intake"
        if "自动派发" in title or "dispatch" in title:
            return "runner_dispatch"
        if "结果回写" in title or "feedback" in title or "retry" in title:
            return "runner_feedback"
        if "监控" in title or "observability" in title:
            return "runner_observability"
        return "runner_ready_job"
    title_text = " ".join(
        [
            str(feature.get("title") or ""),
            str(feature.get("authoritative_artifact") or ""),
            str(feature.get("axis_id") or ""),
            str(feature.get("derived_axis") or ""),
        ]
    ).lower()
    related_text = " ".join(ensure_list(feature.get("consumes")) + ensure_list(feature.get("produces"))).lower()
    fallback_text = " ".join(
        ensure_list(feature.get("scope"))
        + ensure_list(feature.get("constraints"))
        + ensure_list(feature.get("dependencies"))
        + [str(feature.get("gate_decision_dependency") or ""), str(feature.get("admission_dependency") or "")]
    ).lower()
    buckets = [
        ("io", ["governed write-read receipt", "managed ref", "receipt", "registry", "artifact-io-governance", "governed io", "落盘与读取流"]),
        ("formal", ["formal publication", "formal ref", "lineage", "admission", "formal object", "formal 发布", "准入流"]),
        ("gate", ["gate", "decision object", "gate-decision", "handoff-formalization", "审核与裁决流"]),
        ("collaboration", ["candidate", "handoff submission", "collaboration-loop", "候选提交与交接流"]),
        ("pilot", ["pilot", "onboarding", "cutover", "fallback", "wave", "compat mode", "skill-adoption-e2e", "接入与 pilot 验证流"]),
    ]
    for text in (title_text, related_text, f"{title_text} {related_text} {fallback_text}"):
        for profile, markers in buckets:
            if any(marker in text for marker in markers):
                return profile
    return "default"


def derive_priority(feature: dict[str, Any]) -> str:
    track = str(feature.get("track") or "").lower()
    profile = feature_profile(feature)
    text = " ".join(ensure_list(feature.get("scope")) + ensure_list(feature.get("constraints")) + [str(feature.get("title") or "")]).lower()
    if profile == "pilot" or profile.startswith("runner_") or "adoption" in track or "e2e" in track or "pilot" in text:
        return "P1"
    return "P0"


def derive_test_layers(feature: dict[str, Any]) -> list[str]:
    layers = ["integration"]
    profile = feature_profile(feature)
    joined_text = " ".join(ensure_list(feature.get("scope")) + [str(feature.get("axis_id") or ""), str(feature.get("track") or ""), profile]).lower()
    if any(marker in joined_text for marker in ["e2e", "pilot", "ui", "cross skill", "cross-skill"]):
        layers.append("e2e")
    if profile in {"minimal_onboarding", "extended_profile_completion", "device_deferred_entry"} and "e2e" not in layers:
        layers.append("e2e")
    return layers


def derive_recommended_coverage_scope_name(feature: dict[str, Any]) -> list[str]:
    profile = feature_profile(feature)
    title = str(feature.get("title") or "").strip()
    mapping = {
        "collaboration": "mainline collaboration feature",
        "gate": "gate decision feature",
        "formal": "formal publication feature",
        "io": "governed io feature",
        "pilot": "pilot rollout feature",
        "runner_ready_job": "execution runner ready-job feature",
        "runner_operator_entry": "execution runner operator-entry feature",
        "runner_control_surface": "execution runner control-surface feature",
        "runner_intake": "execution runner intake feature",
        "runner_dispatch": "execution runner dispatch feature",
        "runner_feedback": "execution runner feedback feature",
        "runner_observability": "execution runner observability feature",
        "minimal_onboarding": "minimal onboarding feature",
        "first_ai_advice": "first advice release feature",
        "extended_profile_completion": "extended profile completion feature",
        "device_deferred_entry": "deferred device connection feature",
        "state_profile_boundary": "state/profile boundary feature",
    }
    return [mapping.get(profile, f"{title or 'feature'} coverage")]


def derive_feature_owned_code_paths(feature: dict[str, Any]) -> list[str]:
    mapping = {
        "collaboration": [
            "cli/lib/mainline_runtime.py",
            "cli/lib/reentry.py",
            "cli/lib/gate_collaboration_actions.py",
        ],
        "gate": ["cli/commands/gate/command.py"],
        "formal": [
            "cli/lib/formalization.py",
            "cli/lib/lineage.py",
            "cli/lib/admission.py",
            "cli/commands/registry/command.py",
        ],
        "io": [
            "cli/lib/managed_gateway.py",
            "cli/commands/artifact/command.py",
        ],
        "pilot": [
            "cli/lib/rollout_state.py",
            "cli/lib/pilot_chain.py",
            "cli/commands/rollout/command.py",
            "cli/commands/audit/command.py",
        ],
        "runner_ready_job": [
            "cli/lib/ready_job_dispatch.py",
            "cli/lib/job_queue.py",
            "cli/commands/gate/command.py",
        ],
        "runner_operator_entry": [
            "cli/lib/runner_entry.py",
            "cli/lib/execution_runner.py",
            "cli/commands/loop/command.py",
        ],
        "runner_control_surface": [
            "cli/lib/runner_control.py",
            "cli/lib/job_state.py",
            "cli/commands/job/command.py",
        ],
        "runner_intake": [
            "cli/lib/job_queue.py",
            "cli/lib/job_state.py",
            "cli/commands/job/command.py",
        ],
        "runner_dispatch": [
            "cli/lib/skill_invoker.py",
            "cli/lib/execution_runner.py",
            "cli/commands/job/command.py",
        ],
        "runner_feedback": [
            "cli/lib/job_outcome.py",
            "cli/lib/execution_runner.py",
            "cli/commands/job/command.py",
        ],
        "runner_observability": [
            "cli/lib/runner_monitor.py",
            "cli/lib/job_queue.py",
            "cli/commands/loop/command.py",
        ],
        "minimal_onboarding": [
            "app/onboarding/minimal_profile_page.tsx",
            "app/onboarding/minimal_profile_submit.ts",
            "app/routing/homepage_entry_guard.ts",
        ],
        "first_ai_advice": [
            "app/home/first_advice_panel.tsx",
            "app/advice/first_advice_service.ts",
            "app/advice/risk_gate_evaluator.ts",
        ],
        "extended_profile_completion": [
            "app/home/profile_task_card_renderer.tsx",
            "app/profile/profile_extension_patch_service.ts",
            "app/profile/profile_completion_updater.ts",
        ],
        "device_deferred_entry": [
            "app/home/deferred_device_entry.tsx",
            "app/device_connection/deferred_connection_service.ts",
            "app/device_connection/result_handler.ts",
        ],
        "state_profile_boundary": [
            "app/state_boundary/primary_state_service.ts",
            "app/profile_boundary/physical_profile_store.ts",
            "app/state_boundary/unified_onboarding_state_reader.ts",
        ],
    }
    return mapping.get(feature_profile(feature), [])


def is_explicit_web_feature(feature: dict[str, Any]) -> bool:
    text_parts = [
        str(feature.get("title") or ""),
        str(feature.get("goal") or ""),
        str(feature.get("axis_id") or ""),
        str(feature.get("track") or ""),
    ]
    for key in ["scope", "constraints", "dependencies", "non_goals", "source_refs", "consumes", "produces"]:
        text_parts.extend(str(item) for item in ensure_list(feature.get(key)))
    text = " ".join(text_parts).lower()
    return any(marker in text for marker in ["web e2e", "playwright", "browser", "locator", "selector", "page flow", "ui flow", "frontend", "browser automation", "登录页", "浏览器"])

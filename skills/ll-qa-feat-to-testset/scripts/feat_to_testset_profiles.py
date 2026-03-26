#!/usr/bin/env python3
"""Feature profile classification helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, normalize_semantic_lock


def feature_profile(feature: dict[str, Any]) -> str:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    axis_id = str(feature.get("axis_id") or "").strip().lower()
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
    joined_text = " ".join(ensure_list(feature.get("scope")) + [str(feature.get("axis_id") or ""), str(feature.get("track") or ""), feature_profile(feature)]).lower()
    if any(marker in joined_text for marker in ["e2e", "pilot", "ui", "cross skill", "cross-skill"]):
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

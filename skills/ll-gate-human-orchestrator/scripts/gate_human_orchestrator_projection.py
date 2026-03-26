#!/usr/bin/env python3
"""Projection helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import dump_json, load_json, render_markdown, repo_relative, slugify


_BLOCK_TITLES = {
    "product_summary": "产品摘要",
    "roles": "关键角色",
    "main_flow": "主流程",
    "deliverables": "交付物",
    "authoritative_snapshot": "权威快照",
    "review_focus": "评审重点",
    "risks_ambiguities": "风险与歧义",
}

_STATUS_LABELS = {
    "complete": "完整",
    "missing_source": "缺少来源字段",
    "constraints_missing": "权威约束缺失",
    "insufficient_context": "上下文不足",
    "empty": "无附加项",
    "review_visible": "可供评审",
    "traceability_pending": "追溯待补齐",
}

_DECISION_LABELS = {
    "approve": "批准",
    "revise": "修订后重审",
    "retry": "重试",
    "handoff": "转交",
    "reject": "拒绝",
}

_DISPATCH_LABELS = {
    "formal_publication_trigger": "进入 formal publication",
    "execution_return": "回流 execution",
}

_CONTENT_TRANSLATIONS = {
    "Product summary is not yet frozen in Machine SSOT.": "产品摘要尚未在 Machine SSOT 中冻结。",
    "Roles are not yet frozen in Machine SSOT.": "关键角色尚未在 Machine SSOT 中冻结。",
    "Main flow is not yet frozen in Machine SSOT.": "主流程尚未在 Machine SSOT 中冻结。",
    "Deliverables are not yet frozen in Machine SSOT.": "交付物尚未在 Machine SSOT 中冻结。",
    "Authoritative constraints are incomplete; inspect Machine SSOT directly before approving.": "权威约束尚不完整；在批准前请直接检查 Machine SSOT。",
    "Review focus unavailable; inspect Machine SSOT directly.": "当前无法生成评审重点；请直接检查 Machine SSOT。",
    "No additional risks or ambiguities were derived from the current SSOT.": "当前 SSOT 未导出额外风险或歧义。",
    "Confirm the product shape in the summary matches the intended review scope.": "确认摘要中的产品形态与本轮评审范围一致。",
    "Check the frozen downstream boundary and make sure no out-of-scope work leaked into this round.": "检查冻结后的下游边界，确认没有超出范围的内容混入本轮。",
    "Verify there is one authoritative deliverable and downstream inheritance still points back to Machine SSOT.": "确认只有一个权威交付物，且 downstream inheritance 仍然回指 Machine SSOT。",
    "Check role ownership and responsibility placement before approving the projection.": "在批准 projection 前，确认角色归属和职责摆放清楚。",
    "Authoritative deliverable is not unique; confirm which output downstream should treat as canonical.": "权威交付物并不唯一；需要确认 downstream 应把哪个输出视为 canonical。",
    "Open technical decisions remain; check whether they block this review round or only downstream implementation.": "仍存在开放技术决策；需要确认它们阻塞当前评审轮次，还是只影响下游实现。",
}


def dispatch_handoff(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_runtime_action": result["dispatch_target"],
        "decision_ref": result["decision_ref"],
        "materialized_handoff_ref": result.get("materialized_handoff_ref", ""),
        "materialized_job_ref": result.get("materialized_job_ref", ""),
    }


def decision_display(decision: object) -> str:
    return _label_decision(decision)


def dispatch_target_display(dispatch_target: object) -> str:
    return _label_dispatch(dispatch_target)


def projection_status_display(status: object) -> str:
    return _label_status(status)


def projection_bundle_fields(repo_root: Path, brief_record_ref: str, machine_ssot_ref: str) -> dict[str, Any]:
    brief = load_json(_path_from_ref(repo_root, brief_record_ref))
    projection = brief.get("human_projection", {})
    if not isinstance(projection, dict):
        projection = {}
    return {
        "machine_ssot_ref": str(projection.get("ssot_ref") or machine_ssot_ref),
        "human_projection_ref": str(projection.get("projection_ref", "")),
        "projection_status": str(projection.get("status", "")),
        "projection_trace_refs": list(projection.get("trace_refs", [])),
        "projection_markers": dict(projection.get("derived_markers", {})),
        "snapshot_ref": str(projection.get("snapshot_ref", "")),
        "focus_ref": str(projection.get("focus_ref", "")),
        "human_projection": projection,
    }


def bundle_markdown(bundle: dict[str, Any]) -> str:
    refs = bundle["runtime_refs"]
    lines = [
        f"# Gate 裁决包 {bundle['workflow_run_id']}",
        "",
        "## 输入包",
        "",
        f"- input_ref: {bundle['input_ref']}",
        f"- machine_ssot_ref: {bundle.get('machine_ssot_ref', '')}",
        "",
        "## Brief 记录",
        "",
        f"- brief_record_ref: {refs['brief_record_ref']}",
        "",
        "## 人工评审简报",
        "",
        f"- human_projection_ref: {bundle.get('human_projection_ref', '')}",
        f"- projection_status: {_label_status(bundle.get('projection_status', ''))}",
        f"- snapshot_ref: {bundle.get('snapshot_ref', '')}",
        f"- focus_ref: {bundle.get('focus_ref', '')}",
    ]
    for block in bundle.get("human_projection", {}).get("review_blocks", []):
        lines.extend(
            [
                "",
                f"### {_label_block_title(block)}",
                "",
                f"- 状态: {_label_status(block.get('status', ''))}",
                *_format_block_content(block),
            ]
        )
    if bundle.get("projection_markers"):
        lines.extend(
            [
                "",
                "## Projection 标记",
                "",
                f"- derived_only: {bundle['projection_markers'].get('derived_only', '')}",
                f"- non_authoritative: {bundle['projection_markers'].get('non_authoritative', '')}",
                f"- non_inheritable: {bundle['projection_markers'].get('non_inheritable', '')}",
            ]
        )
    lines.extend(
        [
            "",
            "## 待处理人工裁决",
            "",
            f"- pending_human_decision_ref: {refs['pending_human_decision_ref']}",
            "",
            "## 裁决结果",
            "",
            f"- decision_ref: {bundle['decision_ref']}",
            f"- decision: {_label_decision(bundle['decision'])}",
            f"- decision_target: {bundle['decision_target']}",
            "",
            "## 分发结果",
            "",
            f"- dispatch_receipt_ref: {refs['dispatch_receipt_ref']}",
            f"- dispatch_target: {_label_dispatch(bundle['dispatch_target'])}",
            "",
            "## 物化结果",
            "",
            f"- materialized_handoff_ref: {bundle['materialized_handoff_ref']}",
            f"- materialized_job_ref: {bundle['materialized_job_ref']}",
            "",
            "## 追溯链",
            "",
            *[f"- {item}" for item in bundle["source_refs"]],
        ]
    )
    return "\n".join(lines)


def write_bundle_files(artifacts_dir: Path, bundle: dict[str, Any]) -> None:
    frontmatter = {
        "artifact_type": bundle["artifact_type"],
        "workflow_key": bundle["workflow_key"],
        "workflow_run_id": bundle["workflow_run_id"],
        "status": bundle["status"],
        "schema_version": bundle["schema_version"],
        "decision_ref": bundle["decision_ref"],
    }
    (artifacts_dir / "gate-decision-bundle.md").write_text(
        render_markdown(frontmatter, bundle_markdown(bundle)),
        encoding="utf-8",
    )
    dump_json(artifacts_dir / "gate-decision-bundle.json", bundle)


def human_projection_findings(bundle: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    allowed_statuses = {"review_visible", "traceability_pending"}
    if not bundle.get("machine_ssot_ref"):
        findings.append({"title": "Missing Machine SSOT ref", "detail": "machine_ssot_ref must be explicit in the gate package."})
    if not bundle.get("human_projection_ref"):
        findings.append({"title": "Missing human projection ref", "detail": "gate bundle must expose the rendered projection ref."})
    if bundle.get("projection_status") not in allowed_statuses:
        findings.append(
            {
                "title": "Projection not reviewer-ready",
                "detail": f"projection_status must be one of {sorted(allowed_statuses)}, got {bundle.get('projection_status', 'missing')}.",
            }
        )
    markers = bundle.get("projection_markers", {})
    for key in ("derived_only", "non_authoritative", "non_inheritable"):
        if markers.get(key) is not True:
            findings.append({"title": f"Missing projection marker: {key}", "detail": "projection markers must remain explicit and true."})
    if not bundle.get("snapshot_ref"):
        findings.append({"title": "Missing snapshot ref", "detail": "review bundle must expose snapshot_ref for authoritative constraints."})
    if not bundle.get("focus_ref"):
        findings.append({"title": "Missing focus ref", "detail": "review bundle must expose focus_ref for reviewer guidance."})
    return findings


def capture_projection_comment(
    artifacts_dir: Path,
    repo_root: Path,
    comment_ref: str,
    comment_text: str,
    comment_author: str,
    target_block: str = "",
) -> dict[str, Any]:
    _ensure_implementation_root()
    from cli.lib.review_projection.writeback import writeback_projection_comment

    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    projection_ref = str(bundle.get("human_projection_ref", ""))
    if not projection_ref:
        raise ValueError("gate decision bundle does not contain human_projection_ref")
    result = writeback_projection_comment(
        workspace_root=repo_root,
        projection_ref=projection_ref,
        comment_ref=comment_ref,
        comment_text=comment_text,
        comment_author=comment_author,
        target_block=target_block or None,
    )
    record_ref = artifacts_dir / f"projection-comment-{slugify(comment_ref)}.json"
    dump_json(record_ref, result)
    runtime_refs = load_json(artifacts_dir / "runtime-artifact-refs.json")
    runtime_refs["latest_projection_comment_ref"] = repo_relative(repo_root, record_ref)
    runtime_refs["latest_revision_request_ref"] = result["revision_request_ref"]
    dump_json(artifacts_dir / "runtime-artifact-refs.json", runtime_refs)
    return {
        "comment_record_ref": repo_relative(repo_root, record_ref),
        **result,
    }


def regenerate_projection_bundle(
    artifacts_dir: Path,
    repo_root: Path,
    updated_ssot_ref: str,
    revision_request_ref: str = "",
) -> dict[str, Any]:
    _ensure_implementation_root()
    from cli.lib.review_projection.regeneration import request_projection_regeneration

    runtime_refs = load_json(artifacts_dir / "runtime-artifact-refs.json")
    effective_revision_ref = revision_request_ref or str(runtime_refs.get("latest_revision_request_ref", ""))
    if not effective_revision_ref:
        raise ValueError("revision_request_ref is required")
    result = request_projection_regeneration(
        workspace_root=repo_root,
        revision_request_ref=effective_revision_ref,
        updated_ssot_ref=updated_ssot_ref,
    )
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    projection = load_json(_path_from_ref(repo_root, result["regenerated_projection_ref"]))
    bundle.update(
        {
            "machine_ssot_ref": updated_ssot_ref,
            "human_projection_ref": result["regenerated_projection_ref"],
            "projection_status": projection.get("status", ""),
            "projection_trace_refs": projection.get("trace_refs", []),
            "projection_markers": projection.get("derived_markers", {}),
            "snapshot_ref": projection.get("snapshot_ref", ""),
            "focus_ref": projection.get("focus_ref", ""),
            "human_projection": projection,
        }
    )
    for ref_value in (result["regenerated_projection_ref"], projection.get("snapshot_ref", ""), projection.get("focus_ref", ""), effective_revision_ref):
        if ref_value and ref_value not in bundle["source_refs"]:
            bundle["source_refs"].append(ref_value)
    write_bundle_files(artifacts_dir, bundle)
    runtime_refs["human_projection_ref"] = result["regenerated_projection_ref"]
    runtime_refs["snapshot_ref"] = projection.get("snapshot_ref", "")
    runtime_refs["focus_ref"] = projection.get("focus_ref", "")
    runtime_refs["latest_revision_request_ref"] = effective_revision_ref
    dump_json(artifacts_dir / "runtime-artifact-refs.json", runtime_refs)
    record_ref = artifacts_dir / "projection-regeneration.json"
    dump_json(record_ref, result)
    return {
        "regeneration_record_ref": repo_relative(repo_root, record_ref),
        **result,
    }


def write_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "gate-freeze-gate.json")
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-gate-human-orchestrator Review Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- decision: {bundle.get('decision')}",
                f"- projection_status: {bundle.get('projection_status', '')}",
                "",
                "## Execution Evidence",
                "",
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- supervisor_decision: {supervision.get('decision')}",
                "",
                "## Freeze Gate",
                "",
                f"- freeze_ready: {gate.get('freeze_ready')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def _label_block_title(block: dict[str, Any]) -> str:
    block_id = str(block.get("id", "")).strip()
    if block_id in _BLOCK_TITLES:
        return _BLOCK_TITLES[block_id]
    return str(block.get("title", block_id or "Projection Block"))


def _label_status(status: object) -> str:
    raw = str(status or "").strip()
    return _STATUS_LABELS.get(raw, raw)


def _translate_content(content: object) -> str:
    text = str(content)
    translated = _CONTENT_TRANSLATIONS.get(text)
    if translated:
        return translated
    if text.startswith("Completed state: "):
        return "完成态：" + text.removeprefix("Completed state: ")
    if text.startswith("Authoritative output: "):
        return "权威输出：" + text.removeprefix("Authoritative output: ")
    if text.startswith("Frozen downstream boundary: "):
        return "冻结下游边界：" + text.removeprefix("Frozen downstream boundary: ")
    if text.startswith("Open technical decisions: "):
        return "开放技术决策：" + text.removeprefix("Open technical decisions: ")
    if text.startswith("Missing fields: "):
        return "缺失字段：" + text.removeprefix("Missing fields: ")
    return text


def _format_block_content(block: dict[str, Any]) -> list[str]:
    block_id = str(block.get("id", "")).strip()
    content = [str(item) for item in block.get("content", [])]
    if block_id == "authoritative_snapshot":
        return _format_snapshot_content(content)
    if block_id == "risks_ambiguities":
        return _format_prefixed_lines("提示", [_translate_content(item) for item in content])
    if block_id == "review_focus":
        return _format_prefixed_lines("重点", [_translate_content(item) for item in content])
    return [f"- {_translate_content(item)}" for item in content]


def _format_snapshot_content(content: list[str]) -> list[str]:
    lines: list[str] = []
    for item in content:
        translated = _translate_content(item)
        if "：" not in translated:
            lines.append(f"- {translated}")
            continue
        label, value = translated.split("：", 1)
        parts = [part.strip() for part in value.split(";") if part.strip()]
        if not parts:
            lines.append(f"- {translated}")
            continue
        if len(parts) == 1:
            lines.append(f"- {label}：{parts[0]}")
            continue
        lines.append(f"- {label}：")
        lines.extend(f"  - {part}" for part in parts)
    return lines


def _format_prefixed_lines(prefix: str, items: list[str]) -> list[str]:
    if not items:
        return []
    if len(items) == 1:
        return [f"- {prefix}：{items[0]}"]
    return [f"- {prefix}{index}: {item}" for index, item in enumerate(items, start=1)]


def _label_decision(decision: object) -> str:
    raw = str(decision or "").strip()
    return _DECISION_LABELS.get(raw, raw)


def _label_dispatch(dispatch_target: object) -> str:
    raw = str(dispatch_target or "").strip()
    return _DISPATCH_LABELS.get(raw, raw)


def _path_from_ref(repo_root: Path, ref_value: str) -> Path:
    path = Path(ref_value)
    return path if path.is_absolute() else (repo_root / path)


def _ensure_implementation_root() -> None:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))

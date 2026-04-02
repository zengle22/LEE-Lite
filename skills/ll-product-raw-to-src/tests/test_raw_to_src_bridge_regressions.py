from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from raw_to_src_bridge import semantic_review, synthesize_adr_bridge_candidate
from raw_to_src_common import load_raw_input, normalize_candidate


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


def test_governance_object_extraction_ignores_generic_path_mentions(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线",
        """## 问题陈述

这份 IMPL 的重点是做实施前的文档压力测试，检查失败路径、恢复路径和 happy path 是否被充分定义，
但不应把这些普通表述投影成更高阶的治理对象。

## 目标用户

- 需要在开工前审查实施自洽性的 reviewer
""",
    )

    document = load_raw_input(raw_path)
    candidate = synthesize_adr_bridge_candidate(normalize_candidate(document), document)
    governance_objects = candidate.get("bridge_context", {}).get("governance_objects", [])

    assert "Path Policy" not in governance_objects
    assert "路径与目录治理" not in governance_objects
    assert "目录与 artifact 边界" not in governance_objects


def test_governance_object_extraction_keeps_explicit_path_policy_terms(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线",
        """## 问题陈述

这份 IMPL 明确需要定义 path policy、路径策略、目录边界与 artifact io gateway 的统一治理边界。

## 目标用户

- 需要在开工前审查实施自洽性的 reviewer
""",
    )

    document = load_raw_input(raw_path)
    candidate = synthesize_adr_bridge_candidate(normalize_candidate(document), document)
    governance_objects = candidate.get("bridge_context", {}).get("governance_objects", [])

    assert "Path Policy" in governance_objects
    assert "目录与 artifact 边界" in governance_objects
    assert "Artifact IO Gateway" in governance_objects


def test_layer_boundary_ignores_governance_boundary_mentions(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线",
        """## 问题陈述

这份 IMPL 是最后一道开工前文档压力测试，目标是把治理结论收敛成统一继承边界，
明确下游 EPIC / FEAT / TASK 的继承关系，而不是展开实现设计。
""",
    )

    document = load_raw_input(raw_path)
    candidate = normalize_candidate(document)
    candidate["problem_statement"] = (
        "这份 IMPL 是最后一道开工前文档压力测试，目标是把治理结论收敛成统一继承边界，"
        "明确下游 EPIC / FEAT / TASK 的继承关系，而不是展开实现设计。"
    )

    review, findings = semantic_review(candidate, None, document=document)

    assert review["decision"] in {"pass", "revise"}
    assert not any(item["type"] == "layer_boundary" for item in findings)


def test_layer_boundary_still_flags_actual_downstream_layer_drift(tmp_path: Path) -> None:
    raw_path = _write_raw_input(
        tmp_path,
        "ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线",
        """## 问题陈述

这份文档要把原型拆成 EPIC / FEAT / TASK 分解与实现设计，直接指导后续代码实现。
""",
    )

    document = load_raw_input(raw_path)
    candidate = normalize_candidate(document)
    candidate["problem_statement"] = "这份文档要把原型拆成 EPIC / FEAT / TASK 分解与实现设计，直接指导后续代码实现。"

    review, findings = semantic_review(candidate, None, document=document)

    assert review["decision"] == "revise"
    assert any(item["type"] == "layer_boundary" for item in findings)

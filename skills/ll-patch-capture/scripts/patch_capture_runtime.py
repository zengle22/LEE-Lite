"""Patch capture runtime with tri-classification (visual/interaction/semantic).

ADR-049 governed skill runtime for dual-path experience patch registration.
Classifies input changes and derives Minor/Major grade levels per ADR-050.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path for CLI execution
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from cli.lib.patch_schema import (
    ChangeClass,
    GradeLevel,
    derive_grade,
    validate_patch,
)

# ---------------------------------------------------------------------------
# Classification rules (ADR-049 §4.1-4.3 + ADR-050 §6.1)
# ---------------------------------------------------------------------------

CLASSIFICATION_RULES: dict[str, list[str]] = {
    "semantic_indicators": [
        "状态机", "业务规则", "数据流", "字段含义", "用户动作",
        "验收标准", "新增功能", "删除功能", "权限",
        "semantic", "state machine", "business rule", "data flow",
        "field meaning", "user action", "acceptance criteria",
    ],
    "interaction_indicators": [
        "跳转", "入口", "顺序", "流程", "确认步骤", "点击",
        "导航", "菜单", "按钮位置", "操作",
        "redirect", "entry", "order", "flow", "confirmation step",
        "click", "navigation", "menu", "button position",
    ],
    "visual_indicators": [
        "颜色", "尺寸", "间距", "图标", "文案", "样式",
        "布局", "排序", "默认", "字体",
        "color", "size", "spacing", "icon", "copy text", "style",
        "layout", "sort order", "default", "font",
    ],
}

# Negation keywords that invert semantic meaning
NEGATION_PATTERNS = [
    "不改", "不修改", "不变更", "保持", "不变",
    "no change", "not change", "keep", "stay the same",
]


def _has_negation(text: str) -> bool:
    """Check if text contains negation patterns."""
    lower = text.lower()
    return any(pat in lower for pat in NEGATION_PATTERNS)


def _scan_dimensions(text: str) -> list[str]:
    """Scan text against all indicator lists, return matched top-level dimensions."""
    lower = text.lower()
    matched: list[str] = []

    if any(ind in lower for ind in CLASSIFICATION_RULES["semantic_indicators"]):
        matched.append("semantic")
    if any(ind in lower for ind in CLASSIFICATION_RULES["interaction_indicators"]):
        matched.append("interaction")
    if any(ind in lower for ind in CLASSIFICATION_RULES["visual_indicators"]):
        matched.append("visual")

    return matched


def _fallback_classify_by_paths(paths: list[str]) -> ChangeClass:
    """Suggest a ChangeClass based on file path patterns.

    Replicates _suggest_change_class from patch_auto_register.py to avoid
    relative import issues when called from this module.
    """
    ui_patterns = (".html", ".jsx", ".tsx", ".vue", ".svelte", "ui/", "components/", "templates/")
    validation_patterns = ("validator", "validation", "schema", "constraint")
    nav_patterns = ("nav", "route", "router", "link", "breadcrumb")
    layout_patterns = ("layout", "grid", "flex", "style", ".css")
    error_patterns = ("error", "exception", "fallback", "boundary")

    joined = " ".join(paths).lower()

    if any(p in joined for p in ui_patterns):
        return ChangeClass.ui_flow
    if any(p in joined for p in validation_patterns):
        return ChangeClass.validation
    if any(p in joined for p in nav_patterns):
        return ChangeClass.navigation
    if any(p in joined for p in layout_patterns):
        return ChangeClass.layout
    if any(p in joined for p in error_patterns):
        return ChangeClass.error_handling

    return ChangeClass.other


def classify_change(text: str, paths: list[str] | None = None) -> dict:
    """Classify a change with dimensions_detected, confidence, needs_human_review.

    Scans ALL indicator lists, collects ALL matching dimensions.
    Applies "semantic dominates" rule: semantic indicator -> GradeLevel.MAJOR.

    Args:
        text: The change description text.
        paths: Optional file paths for fallback classification.

    Returns:
        Dict with change_class, grade_level, dimensions_detected, confidence,
        needs_human_review.
    """
    lower = text.lower()
    negated = _has_negation(lower)

    # If text explicitly negates semantic change, skip semantic scanning
    if negated:
        # Check if the negation targets semantic specifically
        semantic_negated = any(
            pat + "语义" in lower or pat + "业务" in lower or pat + "状态" in lower
            for pat in NEGATION_PATTERNS
        )
        if semantic_negated:
            matched_dimensions = [
                d for d in _scan_dimensions(text) if d != "semantic"
            ]
        else:
            matched_dimensions = _scan_dimensions(text)
    else:
        matched_dimensions = _scan_dimensions(text)

    fell_back = False
    if not matched_dimensions:
        # FALLBACK: replicate _suggest_change_class logic from patch_auto_register.py
        # (Cannot import directly due to relative imports in that module)
        fell_back = True
        if paths:
            fallback_class = _fallback_classify_by_paths(paths)
            matched_dimensions.append(fallback_class.value)
        else:
            matched_dimensions.append("other")

    # Determine change_class and grade_level
    has_semantic = "semantic" in matched_dimensions

    if has_semantic:
        change_class = ChangeClass.semantic
        grade_level = GradeLevel.MAJOR
    elif len(matched_dimensions) == 1:
        dim = matched_dimensions[0]
        if dim in [e.value for e in ChangeClass]:
            change_class = ChangeClass(dim)
        else:
            change_class = ChangeClass.other
        grade_level = derive_grade(change_class.value)
    else:
        # Multiple dimensions, no semantic -> prefer interaction over visual
        if "interaction" in matched_dimensions:
            change_class = ChangeClass.interaction
        elif "visual" in matched_dimensions:
            change_class = ChangeClass.visual
        else:
            change_class = ChangeClass.other
        grade_level = derive_grade(change_class.value)

    # Confidence calculation
    if fell_back:
        # Fallback cases always have low confidence — file patterns are imprecise
        confidence = "low"
    elif len(matched_dimensions) == 1:
        confidence = "high"
    else:
        confidence = "medium"

    needs_human_review = confidence == "low"

    return {
        "change_class": change_class.value,
        "grade_level": grade_level.value,
        "dimensions_detected": matched_dimensions,
        "confidence": confidence,
        "needs_human_review": needs_human_review,
    }


# ---------------------------------------------------------------------------
# Capture functions
# ---------------------------------------------------------------------------

def _find_workspace_root(start: Path | None = None) -> Path:
    """Walk up from start looking for workspace root (.planning or ssot dir)."""
    if start is None:
        start = Path.cwd()
    current = start
    while current != current.parent:
        if (current / ".planning").is_dir() or (current / "ssot").is_dir():
            return current
        current = current.parent
    return start


def _next_patch_number(patch_dir: Path) -> int:
    """Find the next sequential patch number from existing files."""
    existing = list(patch_dir.glob("UXPATCH-*.yaml"))
    if not existing:
        return 1
    max_num = 0
    for p in existing:
        stem = p.stem  # e.g., "UXPATCH-0001__foo"
        # Extract number: UXPATCH-NNNN
        parts = stem.split("-")
        if len(parts) >= 2:
            num_part = parts[1].split("_")[0]
            try:
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return max_num + 1


def capture_prompt(
    input_text: str,
    feat_ref: str,
    output_dir: Path | None = None,
) -> dict:
    """Capture a patch from a free-form prompt text.

    Args:
        input_text: The change description.
        feat_ref: Feature reference (e.g., "FEAT-001").
        output_dir: Optional output directory override.

    Returns:
        The full patch dict that was written.
    """
    result = classify_change(input_text)

    workspace_root = _find_workspace_root()
    patch_dir = output_dir or (workspace_root / "ssot" / "experience-patches" / feat_ref)
    patch_dir.mkdir(parents=True, exist_ok=True)

    patch_number = _next_patch_number(patch_dir)
    patch_id = f"UXPATCH-{patch_number:04d}"

    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    patch: dict[str, Any] = {
        "id": patch_id,
        "type": "experience_patch",
        "change_class": result["change_class"],
        "grade_level": result["grade_level"],
        "dimensions_detected": result["dimensions_detected"],
        "confidence": result["confidence"],
        "needs_human_review": result["needs_human_review"],
        "status": "draft",
        "created_at": created_at,
        "source": {
            "actor": "ll-patch-capture",
            "ai_suggested_class": result["change_class"],
            "human_confirmed_class": result["change_class"],
        },
        "scope": {
            "feat_ref": feat_ref,
            "page": None,
            "module": None,
        },
        "changed_files": [],
        "test_impact": "TODO: describe test impact",
        "backwrite_targets": [],
        "description": input_text,
    }

    # For semantic or interaction patches, add a placeholder test_impact structure
    if result["change_class"] in ("semantic", "interaction"):
        patch["test_impact"] = {
            "impacts_user_path": True,
            "impacts_acceptance": True,
            "affected_routes": ["TODO: identify affected routes"],
            "test_changes_required": ["TODO: describe test changes"],
        }

    # Validate before writing
    validate_patch(patch)

    slug = input_text[:30].replace(" ", "-").replace("/", "-") if input_text else "patch"
    yaml_path = patch_dir / f"{patch_id}__{slug}.yaml"

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {"experience_patch": patch},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return patch


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point with capture and classify subcommands."""
    parser = argparse.ArgumentParser(
        description="Patch capture runtime with tri-classification"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # classify subcommand
    classify_parser = subparsers.add_parser(
        "classify", help="Classify a change description"
    )
    classify_parser.add_argument(
        "--input", required=True, help="Change description text"
    )

    # capture subcommand
    capture_parser = subparsers.add_parser(
        "capture", help="Capture a patch from input"
    )
    capture_parser.add_argument(
        "--input", required=True, help="Change description text or file path"
    )
    capture_parser.add_argument(
        "--feat-ref", required=True, help="Feature reference (e.g., FEAT-001)"
    )
    capture_parser.add_argument(
        "--input-type",
        choices=["prompt", "document"],
        default="prompt",
        help="Input type: prompt or document",
    )
    capture_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory override",
    )

    args = parser.parse_args()

    if args.command == "classify":
        result = classify_change(args.input)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    elif args.command == "capture":
        if args.input_type == "document":
            doc_path = Path(args.input)
            if not doc_path.exists():
                print(f"Error: document path does not exist: {doc_path}", file=sys.stderr)
                sys.exit(1)
            with open(doc_path, encoding="utf-8") as f:
                input_text = f.read()
        else:
            input_text = args.input

        patch = capture_prompt(input_text, args.feat_ref, args.output_dir)
        print(json.dumps(patch, indent=2, ensure_ascii=False))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

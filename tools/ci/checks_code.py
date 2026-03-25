from __future__ import annotations

from pathlib import Path

from .common import (
    ROOT,
    Violation,
    build_report,
    collect_python_metrics,
    dump_json,
    git_show_file,
    read_text,
)


MAX_FILE_LINES = 500
MAX_FUNCTION_LINES = 80


def _function_map(metrics) -> dict[str, int]:
    return {item.qualname: item.length for item in metrics.functions}


def _compare_file_size(rel_path: str, current, previous, violations: list[Violation]) -> None:
    if previous is None:
        if current.line_count > MAX_FILE_LINES:
            violations.append(
                Violation(
                    "code-size-governance",
                    "new_file_too_large",
                    rel_path,
                    f"New Python file has {current.line_count} lines; max allowed is {MAX_FILE_LINES}.",
                )
            )
        return

    if previous.line_count > MAX_FILE_LINES and current.line_count >= previous.line_count:
        violations.append(
            Violation(
                "code-size-governance",
                "oversized_file_not_reduced",
                rel_path,
                f"File was already oversized at {previous.line_count} lines and must be reduced; current size is {current.line_count}.",
            )
        )
    elif previous.line_count <= MAX_FILE_LINES < current.line_count:
        violations.append(
            Violation(
                "code-size-governance",
                "file_grew_past_limit",
                rel_path,
                f"Python file grew from {previous.line_count} to {current.line_count} lines, exceeding the {MAX_FILE_LINES}-line limit.",
            )
        )


def _compare_function_sizes(rel_path: str, current, previous, violations: list[Violation]) -> None:
    previous_fn_map = _function_map(previous) if previous is not None else {}
    for fn in current.functions:
        old_len = previous_fn_map.get(fn.qualname)
        if old_len is None:
            if fn.length > MAX_FUNCTION_LINES:
                violations.append(
                    Violation(
                        "code-size-governance",
                        "new_function_too_large",
                        rel_path,
                        f"Function '{fn.qualname}' has {fn.length} lines; max allowed is {MAX_FUNCTION_LINES}.",
                    )
                )
            continue
        if old_len > MAX_FUNCTION_LINES and fn.length >= old_len:
            violations.append(
                Violation(
                    "code-size-governance",
                    "oversized_function_not_reduced",
                    rel_path,
                    f"Function '{fn.qualname}' was already oversized at {old_len} lines and must be reduced; current size is {fn.length}.",
                )
            )
        elif old_len <= MAX_FUNCTION_LINES < fn.length:
            violations.append(
                Violation(
                    "code-size-governance",
                    "function_grew_past_limit",
                    rel_path,
                    f"Function '{fn.qualname}' grew from {old_len} to {fn.length} lines, exceeding the {MAX_FUNCTION_LINES}-line limit.",
                )
            )


def _metrics_payload(rel_path: str, current, previous) -> dict[str, object]:
    return {
        "path": rel_path,
        "current_line_count": current.line_count,
        "baseline_line_count": previous.line_count if previous is not None else None,
        "current_functions": [{"qualname": item.qualname, "length": item.length} for item in current.functions],
        "baseline_functions": [{"qualname": item.qualname, "length": item.length} for item in previous.functions] if previous is not None else [],
    }


def check_code_size_governance(changed_files: list[str], output_dir: Path, base_ref: str) -> int:
    python_files = [path for path in changed_files if path.endswith(".py") and (ROOT / path).exists()]
    violations: list[Violation] = []
    metrics_payload: list[dict[str, object]] = []

    for rel_path in python_files:
        current_text = read_text(ROOT / rel_path)
        try:
            current = collect_python_metrics(rel_path, current_text)
        except Exception as exc:
            violations.append(Violation("code-size-governance", "python_parse_error", rel_path, f"Failed to parse Python file: {exc}"))
            continue

        previous_text = git_show_file(base_ref, rel_path)
        previous = None
        if previous_text is not None:
            try:
                previous = collect_python_metrics(rel_path, previous_text)
            except Exception as exc:
                violations.append(Violation("code-size-governance", "baseline_parse_error", rel_path, f"Failed to parse baseline Python file: {exc}"))
                continue

        _compare_file_size(rel_path, current, previous, violations)
        _compare_function_sizes(rel_path, current, previous, violations)
        metrics_payload.append(_metrics_payload(rel_path, current, previous))

    dump_json(output_dir / "code-size-metrics.json", {"base_ref": base_ref, "files": metrics_payload})
    dump_json(
        output_dir / "code-size-governance-report.json",
        build_report("code-size-governance", violations, {"base_ref": base_ref, "checked_files": python_files}),
    )
    return 1 if violations else 0

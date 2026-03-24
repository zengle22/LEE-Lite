#!/usr/bin/env python3
"""
Local loop helpers for input and intake stages.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from raw_to_src_common import first_paragraph, safe_stem


def split_patchable_issues(
    issues: list[dict[str, Any]],
    patchable_codes: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    patchable = [item for item in issues if item["code"] in patchable_codes]
    blocking = [item for item in issues if item["code"] not in patchable_codes]
    return patchable, blocking


def validate_intake_document(document: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if len(str(document.get("title", "")).strip()) < 3:
        issues.append({"code": "missing_title", "severity": "error", "message": "Intake title is missing or too short."})
    if not document.get("source_refs"):
        issues.append({"code": "missing_source_refs", "severity": "error", "message": "Intake source refs are required."})
    if not str(document.get("problem_statement", "")).strip():
        issues.append({"code": "missing_problem_statement", "severity": "error", "message": "Intake problem statement is required."})
    return issues, {"valid": not issues, "issue_count": len(issues), "issues": issues}


def apply_input_patch(document: dict[str, Any], issues: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = deepcopy(document)
    patches: list[dict[str, Any]] = []
    codes = {item["code"] for item in issues}
    if "missing_title" in codes and not str(working.get("title", "")).strip():
        working["title"] = safe_stem(Path(working["path"]))
        patches.append(
            {
                "code": "missing_title",
                "action": "Filled title from input filename.",
                "target_fields": ["title"],
            }
        )
    if "missing_body" in codes and not str(working.get("body", "")).strip() and str(working.get("problem_statement", "")).strip():
        working["body"] = str(working["problem_statement"]).strip()
        patches.append(
            {
                "code": "missing_body",
                "action": "Filled body from extracted problem statement.",
                "target_fields": ["body"],
            }
        )
    return working, patches


def apply_intake_patch(document: dict[str, Any], issues: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = deepcopy(document)
    patches: list[dict[str, Any]] = []
    codes = {item["code"] for item in issues}
    if "missing_problem_statement" in codes and not str(working.get("problem_statement", "")).strip():
        body = str(working.get("body", "")).strip()
        if body:
            working["problem_statement"] = first_paragraph(body)
            patches.append(
                {
                    "code": "missing_problem_statement",
                    "action": "Filled problem statement from intake body.",
                    "target_fields": ["problem_statement"],
                }
            )
    if "missing_source_refs" in codes and not working.get("source_refs"):
        working["source_refs"] = [Path(working["path"]).name]
        patches.append(
            {
                "code": "missing_source_refs",
                "action": "Filled source refs from input filename.",
                "target_fields": ["source_refs"],
            }
        )
    if "missing_title" in codes and not str(working.get("title", "")).strip():
        working["title"] = safe_stem(Path(working["path"]))
        patches.append(
            {
                "code": "missing_title",
                "action": "Filled intake title from input filename.",
                "target_fields": ["title"],
            }
        )
    return working, patches

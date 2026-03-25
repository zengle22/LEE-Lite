"""Static and runtime UI source collection for governed test execution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

from cli.lib.fs import canonical_to_path, to_canonical_path


DATA_TESTID_PATTERN = re.compile(r"data-testid\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
ID_PATTERN = re.compile(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
INPUT_NAME_PATTERN = re.compile(r"<input[^>]*name\s*=\s*['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
BUTTON_TEXT_PATTERN = re.compile(r"<button[^>]*>([^<]+)</button>", re.IGNORECASE)
PATH_PATTERN = re.compile(r"path\s*:\s*['\"](/[^'\"]+)['\"]", re.IGNORECASE)


def _normalize_local_ref(ref_value: str, workspace_root: Path) -> Path | None:
    if not ref_value or ref_value.startswith(("http://", "https://", "repo://", "runtime://", "proto://")):
        return None
    return canonical_to_path(ref_value, workspace_root)


def _text_candidates(text: str) -> dict[str, list[dict[str, str]]]:
    data_testids = [
        {"kind": "testid", "value": value, "selector": f"[data-testid='{value}']"}
        for value in sorted(set(DATA_TESTID_PATTERN.findall(text)))
    ]
    ids = [{"kind": "id", "value": value, "selector": f"#{value}"} for value in sorted(set(ID_PATTERN.findall(text)))]
    inputs = [{"kind": "name", "value": value, "selector": f"input[name='{value}']"} for value in sorted(set(INPUT_NAME_PATTERN.findall(text)))]
    buttons = [
        {"kind": "button", "value": value.strip(), "role": "button", "name": value.strip()}
        for value in sorted({item.strip() for item in BUTTON_TEXT_PATTERN.findall(text) if item.strip()})
    ]
    paths = [{"kind": "path", "value": value} for value in sorted(set(PATH_PATTERN.findall(text)))]
    return {"testids": data_testids, "ids": ids, "inputs": inputs, "buttons": buttons, "paths": paths}


def _scan_codebase(codebase_root: Path) -> dict[str, Any]:
    patterns = ("*.html", "*.htm", "*.tsx", "*.jsx", "*.ts", "*.js")
    files = []
    merged = {"testids": [], "ids": [], "inputs": [], "buttons": [], "paths": []}
    seen = {key: set() for key in merged}
    for pattern in patterns:
        for path in codebase_root.rglob(pattern):
            if path.is_file():
                files.append(path)
    for path in files[:200]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for key, items in _text_candidates(text).items():
            for item in items:
                marker = tuple(sorted(item.items()))
                if marker in seen[key]:
                    continue
                seen[key].add(marker)
                merged[key].append(item)
    return {"resolved": codebase_root.exists(), "root": str(codebase_root), "files_scanned": len(files[:200]), **merged}


def _runtime_url(runtime_ref: str, base_url: str, page_path: str) -> str:
    root = runtime_ref or base_url
    if not root.startswith(("http://", "https://")):
        return root
    return urljoin(root, page_path or "")


def _read_runtime_source(runtime_ref: str, base_url: str, page_path: str, workspace_root: Path) -> tuple[str, str]:
    target = _runtime_url(runtime_ref, base_url, page_path)
    local_path = _normalize_local_ref(target, workspace_root)
    if local_path is not None:
        return local_path.read_text(encoding="utf-8", errors="ignore"), to_canonical_path(local_path, workspace_root)
    with urlopen(target, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore"), target


def _scan_runtime_pages(
    runtime_ref: str,
    base_url: str,
    page_paths: list[str],
    workspace_root: Path,
) -> list[dict[str, Any]]:
    pages = []
    for page_path in sorted(set(page_paths)):
        try:
            text, resolved_ref = _read_runtime_source(runtime_ref, base_url, page_path, workspace_root)
            pages.append({"page_path": page_path, "resolved_ref": resolved_ref, "fetch_status": "ok", **_text_candidates(text)})
        except Exception as exc:  # noqa: BLE001
            pages.append(
                {
                    "page_path": page_path,
                    "resolved_ref": runtime_ref or base_url,
                    "fetch_status": "error",
                    "error": str(exc),
                    "testids": [],
                    "ids": [],
                    "inputs": [],
                    "buttons": [],
                    "paths": [],
                }
            )
    return pages


def collect_ui_source_context(
    workspace_root: Path,
    ui_source_spec: dict[str, Any],
    environment: dict[str, Any],
    case_pack: dict[str, Any],
) -> dict[str, Any]:
    codebase_ref = str(ui_source_spec.get("codebase_ref", ""))
    runtime_ref = str(ui_source_spec.get("runtime_ref", ""))
    codebase_root = _normalize_local_ref(codebase_ref, workspace_root)
    codebase = {"resolved": False, "root": codebase_ref, "files_scanned": 0, "testids": [], "ids": [], "inputs": [], "buttons": [], "paths": []}
    if codebase_root is not None and codebase_root.exists():
        codebase = _scan_codebase(codebase_root)
    page_paths = [str(case.get("page_path", "")) for case in case_pack.get("cases", []) if case.get("page_path")]
    if (runtime_ref or environment.get("base_url")) and not page_paths:
        page_paths = [""]
    runtime_pages = _scan_runtime_pages(runtime_ref, str(environment.get("base_url", "")), page_paths, workspace_root)
    return {
        "artifact_type": "ui_source_context",
        "ui_source_spec": ui_source_spec,
        "codebase": codebase,
        "runtime": {
            "base_url": environment.get("base_url", ""),
            "runtime_ref": runtime_ref,
            "pages": runtime_pages,
        },
    }

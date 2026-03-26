"""Static and runtime UI source collection for governed test execution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

from cli.lib.test_exec_ui_ast import parse_code_file
from cli.lib.test_exec_ui_runtime_probe import run_runtime_probe
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


def _merge_unique(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for item in items:
        normalized = {str(k): str(v) for k, v in item.items() if v not in (None, "")}
        marker = tuple(sorted(normalized.items()))
        if marker in seen:
            continue
        seen.add(marker)
        merged.append({**item, "source_kind": item.get("source_kind", key)})
    return merged


def _ast_scan(path: Path) -> dict[str, list[dict[str, Any]]]:
    parsed = parse_code_file(path)
    testids = []
    ids = []
    inputs = []
    buttons = []
    paths = []
    for route in parsed.get("routes", []):
        paths.append({"kind": "path", "value": route.get("path", ""), "source_kind": route.get("source_kind", "ast_route")})
    for element in parsed.get("elements", []):
        common = {
            "source_kind": "ast_element",
            "label": str(element.get("label", "")).strip(),
            "selector": str(element.get("selector", "")).strip(),
        }
        if element.get("testid"):
            testids.append({"kind": "testid", "value": str(element["testid"]), "selector": f"[data-testid='{element['testid']}']", **common})
        if element.get("id"):
            ids.append({"kind": "id", "value": str(element["id"]), "selector": f"#{element['id']}", **common})
        if element.get("element") in {"input", "textarea", "select"}:
            inputs.append(
                {
                    "kind": "name",
                    "value": str(element.get("name", "") or element.get("id", "")),
                    "selector": str(element.get("selector", "")),
                    "label": str(element.get("label", "")),
                    "source_kind": "ast_input",
                }
            )
        if element.get("element") == "button":
            buttons.append(
                {
                    "kind": "button",
                    "value": str(element.get("text", "") or element.get("name", "")).strip(),
                    "role": str(element.get("role", "button")).strip() or "button",
                    "name": str(element.get("name", "") or element.get("text", "")).strip(),
                    "source_kind": "ast_button",
                }
            )
    return {
        "testids": _merge_unique(testids, "testid"),
        "ids": _merge_unique(ids, "id"),
        "inputs": _merge_unique(inputs, "input"),
        "buttons": _merge_unique(buttons, "button"),
        "paths": _merge_unique(paths, "path"),
        "route_count": len(paths),
        "element_count": len(parsed.get("elements", [])),
    }


def _scan_codebase(codebase_root: Path) -> dict[str, Any]:
    patterns = ("*.html", "*.htm", "*.tsx", "*.jsx", "*.ts", "*.js")
    files = []
    merged = {"testids": [], "ids": [], "inputs": [], "buttons": [], "paths": []}
    seen = {key: set() for key in merged}
    ast_route_count = 0
    ast_element_count = 0
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
        ast_items = _ast_scan(path)
        ast_route_count += int(ast_items.get("route_count", 0))
        ast_element_count += int(ast_items.get("element_count", 0))
        for key in merged:
            for item in ast_items.get(key, []):
                marker = tuple(sorted({k: str(v) for k, v in item.items() if v not in (None, "")}.items()))
                if marker in seen[key]:
                    continue
                seen[key].add(marker)
                merged[key].append(item)
    return {
        "resolved": codebase_root.exists(),
        "root": str(codebase_root),
        "files_scanned": len(files[:200]),
        "ast_routes_found": ast_route_count,
        "ast_elements_found": ast_element_count,
        **merged,
    }


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


def _runtime_probe_payload(page_path: str, resolved_ref: str, html: str, probe: dict[str, Any] | None) -> dict[str, Any]:
    if probe is None:
        return {
            "page_path": page_path,
            "resolved_ref": resolved_ref,
            "fetch_status": "ok",
            **_text_candidates(html),
            "probe_status": "not_run",
            "probe_mode": "html_fetch",
            "accessibility_catalog": [],
            "interactive_catalog": [],
        }
    dom_catalog = probe.get("dom_catalog", {})
    html_text = str(probe.get("html", html))
    fallback = _text_candidates(html_text)
    return {
        "page_path": page_path,
        "resolved_ref": resolved_ref,
        "fetch_status": "ok" if probe.get("probe_status") == "ok" else "error",
        "testids": dom_catalog.get("testids", fallback["testids"]),
        "ids": dom_catalog.get("ids", fallback["ids"]),
        "inputs": dom_catalog.get("inputs", fallback["inputs"]),
        "buttons": dom_catalog.get("buttons", fallback["buttons"]),
        "paths": fallback["paths"],
        "probe_status": str(probe.get("probe_status", "unknown")),
        "probe_mode": str(probe.get("probe_mode", "runtime_probe")),
        "accessibility_catalog": list(probe.get("accessibility_catalog", [])),
        "interactive_catalog": list(dom_catalog.get("interactive", [])),
        "title": str(probe.get("title", "")),
        "final_url": str(probe.get("final_url", "")),
    }


def _scan_runtime_pages(
    runtime_ref: str,
    base_url: str,
    page_paths: list[str],
    workspace_root: Path,
    project_root: Path | None = None,
    environment: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    pages = []
    for page_path in sorted(set(page_paths)):
        try:
            text, resolved_ref = _read_runtime_source(runtime_ref, base_url, page_path, workspace_root)
            probe = None
            if project_root is not None and environment is not None and (runtime_ref or base_url):
                probe = run_runtime_probe(workspace_root, project_root, environment, _runtime_url(runtime_ref, base_url, page_path), page_path)
            pages.append(_runtime_probe_payload(page_path, resolved_ref, text, probe))
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
                    "probe_status": "error",
                    "probe_mode": "runtime_probe",
                    "accessibility_catalog": [],
                    "interactive_catalog": [],
                }
            )
    return pages


def _route_catalog(codebase: dict[str, Any], runtime_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in codebase.get("paths", []):
        path = str(item.get("value", "")).strip()
        marker = ("codebase", path)
        if path and marker not in seen:
            seen.add(marker)
            catalog.append({"path": path, "source": "codebase"})
    for page in runtime_pages:
        path = str(page.get("page_path", "")).strip()
        marker = ("runtime", path)
        if path and marker not in seen:
            seen.add(marker)
            catalog.append({"path": path, "source": "runtime"})
    return catalog


def _append_catalog_entries(
    catalog: list[dict[str, Any]],
    seen: set[tuple[str, str, str, str]],
    items: list[dict[str, Any]],
    source: str,
    page_path: str,
    kind: str,
) -> None:
    for item in items:
        value = str(item.get("value", item.get("selector", item.get("name", "")))).strip()
        selector = str(item.get("selector", "")).strip()
        marker = (source, page_path, kind, value, selector)
        if marker in seen:
            continue
        seen.add(marker)
        catalog.append(
            {
                "source": source,
                "page_path": page_path,
                "kind": kind,
                "value": value,
                "selector": selector,
                "role": str(item.get("role", "")).strip(),
                "name": str(item.get("name", "")).strip(),
                "label": str(item.get("label", "")).strip(),
                "source_kind": str(item.get("source_kind", "")).strip(),
            }
        )


def _element_catalog(codebase: dict[str, Any], runtime_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for kind in ("testids", "ids", "inputs", "buttons"):
        _append_catalog_entries(catalog, seen, codebase.get(kind, []), "codebase", "", kind[:-1] if kind.endswith("s") else kind)
    for page in runtime_pages:
        page_path = str(page.get("page_path", "")).strip()
        for kind in ("testids", "ids", "inputs", "buttons"):
            _append_catalog_entries(catalog, seen, page.get(kind, []), "runtime", page_path, kind[:-1] if kind.endswith("s") else kind)
    return catalog


def _source_summary(codebase: dict[str, Any], runtime_pages: list[dict[str, Any]], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
    runtime_ok = [page for page in runtime_pages if page.get("fetch_status") == "ok"]
    runtime_errors = [page for page in runtime_pages if page.get("fetch_status") != "ok"]
    runtime_probe_ok = [page for page in runtime_pages if page.get("probe_status") == "ok"]
    return {
        "codebase_resolved": bool(codebase.get("resolved")),
        "codebase_files_scanned": int(codebase.get("files_scanned", 0)),
        "codebase_ast_routes_found": int(codebase.get("ast_routes_found", 0)),
        "codebase_ast_elements_found": int(codebase.get("ast_elements_found", 0)),
        "runtime_page_count": len(runtime_pages),
        "runtime_fetch_ok_count": len(runtime_ok),
        "runtime_fetch_error_count": len(runtime_errors),
        "runtime_probe_ok_count": len(runtime_probe_ok),
        "runtime_accessibility_nodes": sum(len(page.get("accessibility_catalog", [])) for page in runtime_pages),
        "prototype_ref_present": bool(ui_source_spec.get("prototype_ref")),
    }


def collect_ui_source_context(
    workspace_root: Path,
    ui_source_spec: dict[str, Any],
    environment: dict[str, Any],
    case_pack: dict[str, Any],
    project_root: Path | None = None,
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
    runtime_pages = _scan_runtime_pages(
        runtime_ref,
        str(environment.get("base_url", "")),
        page_paths,
        workspace_root,
        project_root=project_root,
        environment=environment,
    )
    route_catalog = _route_catalog(codebase, runtime_pages)
    element_catalog = _element_catalog(codebase, runtime_pages)
    return {
        "artifact_type": "ui_source_context",
        "ui_source_spec": ui_source_spec,
        "source_summary": _source_summary(codebase, runtime_pages, ui_source_spec),
        "route_catalog": route_catalog,
        "element_catalog": element_catalog,
        "codebase": codebase,
        "runtime": {
            "base_url": environment.get("base_url", ""),
            "runtime_ref": runtime_ref,
            "pages": runtime_pages,
        },
        "prototype": {
            "prototype_ref": ui_source_spec.get("prototype_ref", ""),
            "resolved": bool(ui_source_spec.get("prototype_ref")),
        },
    }

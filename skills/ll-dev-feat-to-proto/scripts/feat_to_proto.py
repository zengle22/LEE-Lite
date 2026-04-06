#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import threading
from contextlib import suppress
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.feat_input_resolver import resolve_feat_input_artifacts_dir
from cli.lib.prototype_review_contract import build_prototype_review, validate_prototype_review
from feat_to_ui_spec import build_units, d_list, first, page_type_family, slugify

INPUT_FILES = [
    "package-manifest.json",
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
OUTPUT_FILES = [
    "package-manifest.json",
    "prototype-bundle.md",
    "prototype-bundle.json",
    "journey-ux-ascii.md",
    "ui-shell-spec.md",
    "prototype-flow-map.md",
    "prototype-review-guide.md",
    "prototype-completeness-report.json",
    "prototype-fidelity-report.json",
    "prototype-route-map.json",
    "prototype-journey-reachability-report.json",
    "prototype-initial-view-report.json",
    "prototype-placeholder-lint.json",
    "prototype-runtime-smoke.json",
    "prototype-review-report.json",
    "prototype-defect-list.json",
    "prototype-freeze-gate.json",
    "execution-evidence.json",
    "supervision-evidence.json",
    "prototype/index.html",
    "prototype/styles.css",
    "prototype/app.js",
    "prototype/mock-data.json",
    "prototype/mock-data.js",
]
RESOURCE_ROOT = Path(__file__).resolve().parents[1] / "resources"
JOURNEY_SPEC_REF = "journey-ux-ascii.md"
JOURNEY_SPEC_VERSION = "1.0.0"
UI_SHELL_SNAPSHOT_REF = "ui-shell-spec.md"
UI_SHELL_SOURCE_REF = "skills/ll-dev-feat-to-proto/resources/ui-shell/default-ui-shell-spec.md"
PROTOTYPE_TEMPLATE_ROOT = RESOURCE_ROOT / "prototype"
SRC002_HIFI_TEMPLATE_ROOT = RESOURCE_ROOT / "templates" / "src002-journey-hifi" / "prototype"
SHELL_REQUIRED_SECTIONS = (
    "## App Shell",
    "## Container Rules",
    "## CTA Placement",
    "## State Expression",
    "## Common Structural Components",
    "## Governance",
)
JOURNEY_REQUIRED_SECTIONS = (
    "## 1. Journey Main Chain",
    "## 2. Page Map",
    "## 3. Decision Points",
    "## 4. CTA Hierarchy",
    "## 5. Container Hints",
    "## 6. Error / Degraded / Retry Paths",
    "## 7. Open Questions / Frozen Assumptions",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def repo_root_from(repo_root: str | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path.cwd().resolve()


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_resource_text(*parts: str) -> str:
    return (RESOURCE_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def render_resource_text(parts: tuple[str, ...], replacements: dict[str, str] | None = None) -> str:
    content = read_resource_text(*parts)
    for key, value in (replacements or {}).items():
        content = content.replace(key, value)
    return content


def extract_shell_metadata(shell_source_text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key in ("ui_shell_source_id", "ui_shell_family", "ui_shell_version", "shell_change_policy"):
        match = re.search(rf"-\s*{re.escape(key)}:\s*(.+)", shell_source_text)
        metadata[key] = match.group(1).strip() if match else ""
    return metadata


def _collect_section_body(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            body.append(line.strip())
    return "\n".join(body).strip()


def validate_structured_sections(text: str, label: str, headings: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for heading in headings:
        if heading not in text:
            errors.append(f"{label} missing section: {heading}")
            continue
        if not _collect_section_body(text, heading):
            errors.append(f"{label} section has no content: {heading}")
    return errors


def validate_input_package(
    input_path: str | Path,
    feat_ref: str,
    repo_root: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    repo_root = repo_root or Path.cwd().resolve()
    try:
        input_dir, input_resolution = resolve_feat_input_artifacts_dir(input_path, repo_root, consumer_ref="dev.feat-to-proto")
    except Exception as exc:
        return [str(exc)], {}
    errors = [f"missing required input artifact: {name}" for name in INPUT_FILES if not (input_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(input_dir / "feat-freeze-bundle.json")
    gate = load_json(input_dir / "feat-freeze-gate.json")
    feature = next((item for item in d_list(bundle.get("features")) if str(item.get("feat_ref")) == feat_ref), None)
    if bundle.get("artifact_type") != "feat_freeze_package":
        errors.append("artifact_type must be feat_freeze_package")
    if not gate.get("freeze_ready"):
        errors.append("feat-freeze-gate.json freeze_ready must be true")
    if feature is None:
        errors.append(f"selected feat_ref not found in bundle: {feat_ref}")
    return errors, {
        "input_dir": input_dir,
        "input_mode": input_resolution.get("input_mode", "package_dir"),
        "bundle": bundle,
        "feature": feature,
        "feat_ref": feat_ref,
    }


def _feat_num_from_ref(feat_ref: str) -> str:
    match = re.search(r"-(\d{3})$", str(feat_ref or "").strip())
    return match.group(1) if match else ""


def _is_src002_hifi_required(context: dict[str, Any]) -> bool:
    feature = context.get("feature") if isinstance(context.get("feature"), dict) else {}
    contract = feature.get("journey_contract") if isinstance(feature.get("journey_contract"), dict) else {}
    if str(contract.get("journey_id") or "").strip() != "SRC002":
        return False
    return _feat_num_from_ref(str(context.get("feat_ref") or "")) in {"001", "002", "003", "004", "005", "006"}


def _copy_template_dir(from_dir: Path, to_dir: Path) -> None:
    required = [from_dir / "index.html", from_dir / "styles.css", from_dir / "app.js"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"template missing files: {', '.join(missing)}")
    if to_dir.exists():
        shutil.rmtree(to_dir)
    to_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(from_dir, to_dir)


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _find_chrome_executable() -> Path | None:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _serve_dir_for_smoke(prototype_dir: Path) -> tuple[ThreadingHTTPServer, str]:
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

    handler = partial(QuietHandler, directory=str(prototype_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, url


def _chrome_dump_dom(chrome: Path, url: str) -> tuple[bool, str]:
    args = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--disable-web-security",
        "--virtual-time-budget=3000",
        "--dump-dom",
        url,
    ]
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=25, check=False)
    except Exception as exc:
        return False, f"chrome invocation failed: {exc}"
    if proc.returncode != 0:
        args[1] = "--headless"
        with suppress(Exception):
            proc = subprocess.run(args, capture_output=True, text=True, timeout=25, check=False)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()
    return True, (proc.stdout or "").strip()


def _build_fidelity_report(bundle: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    required = _is_src002_hifi_required(context)
    proto_source = str(bundle.get("prototype_source") or "")
    expected = "hifi_interactive_html" if required else "interactive_html"
    ok = (not required) or proto_source == "src002_journey_hifi_template"
    return {
        "gate_name": "Prototype Fidelity Gate",
        "decision": "pass" if ok else "fail",
        "expected": expected,
        "prototype_source": proto_source,
        "checked_at": utc_now(),
        "notes": "" if ok else "SRC002 journey feats must use the SRC002 hi-fi template (not the UI spec viewer).",
    }


def _build_route_map(bundle: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    feat_ref = str(bundle.get("feat_ref") or "")
    routes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    entry = ""

    if _is_src002_hifi_required(context):
        input_dir = Path(context["input_dir"])
        handoff = load_json(input_dir / "handoff-to-feat-downstreams.json")
        surfaces = handoff.get("journey_surface_inventory") if isinstance(handoff.get("journey_surface_inventory"), list) else []
        main_path = handoff.get("journey_main_path") if isinstance(handoff.get("journey_main_path"), list) else []
        surface_ids = [str(item.get("surface_id") or "").strip() for item in surfaces if isinstance(item, dict) and str(item.get("surface_id") or "").strip()]
        surface_titles = {str(item.get("surface_id") or "").strip(): str(item.get("surface_title") or "").strip() for item in surfaces if isinstance(item, dict)}
        for sid in surface_ids:
            routes.append({"route_id": sid, "label": surface_titles.get(sid) or sid, "kind": "surface"})
        entry = next((sid for sid in surface_ids if sid.startswith("screen_")), (surface_ids[0] if surface_ids else ""))

        path_surface_seq: list[str] = []
        for step in main_path:
            found = re.findall(r"(screen_[a-z0-9_]+|drawer_[a-z0-9_]+|inline_[a-z0-9_]+)", str(step))
            if found:
                path_surface_seq.append(found[-1])
        for left, right in zip(path_surface_seq, path_surface_seq[1:]):
            edges.append({"from": left, "to": right, "trigger": "main_path"})

        return {
            "gate_name": "Prototype Route Map",
            "feat_ref": feat_ref,
            "entry_route_id": entry,
            "routes": routes,
            "edges": edges,
            "journey_surface_inventory_present": bool(surfaces),
            "journey_main_path_present": bool(main_path),
            "generated_at": utc_now(),
        }

    pages = bundle.get("pages") if isinstance(bundle.get("pages"), list) else []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        route_id = f"page-{index}"
        routes.append({"route_id": route_id, "label": str(page.get("title") or page.get("page_id") or route_id), "kind": "page"})
        if index + 1 < len(pages):
            edges.append({"from": route_id, "to": f"page-{index+1}", "trigger": "page_next"})
        if index - 1 >= 0:
            edges.append({"from": route_id, "to": f"page-{index-1}", "trigger": "page_back"})
    entry = routes[0]["route_id"] if routes else ""
    return {
        "gate_name": "Prototype Route Map",
        "feat_ref": feat_ref,
        "entry_route_id": entry,
        "routes": routes,
        "edges": edges,
        "generated_at": utc_now(),
    }


def _check_journey_reachability(route_map: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not _is_src002_hifi_required(context):
        return {"gate_name": "Journey Reachability", "decision": "pass", "checked_at": utc_now(), "notes": "not a journey-hifi required feat"}
    routes = route_map.get("routes") if isinstance(route_map.get("routes"), list) else []
    edges = route_map.get("edges") if isinstance(route_map.get("edges"), list) else []
    entry = str(route_map.get("entry_route_id") or "")
    route_ids = {str(item.get("route_id") or "") for item in routes if isinstance(item, dict) and str(item.get("route_id") or "")}
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        a = str(edge.get("from") or "")
        b = str(edge.get("to") or "")
        if not a or not b:
            continue
        adjacency.setdefault(a, set()).add(b)
    seen: set[str] = set()
    stack = [entry] if entry else []
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(sorted(adjacency.get(cur) or []))
    missing = sorted([rid for rid in route_ids if rid and rid not in seen])
    ignored: list[str] = []
    if missing and all(rid.startswith("inline_") for rid in missing):
        ignored = list(missing)
        missing = []
    ok = bool(entry) and not missing
    return {
        "gate_name": "Journey Reachability",
        "decision": "pass" if ok else "fail",
        "entry_route_id": entry,
        "reachable_count": len(seen),
        "route_count": len(route_ids),
        "unreachable_routes": missing,
        "ignored_unreachable_routes": ignored,
        "checked_at": utc_now(),
    }


def _check_initial_view_integrity(prototype_dir: Path) -> dict[str, Any]:
    css = _load_text(prototype_dir / "styles.css")
    html = _load_text(prototype_dir / "index.html")
    css_hidden_ok = "[hidden]" in css and "display:none" in css.replace(" ", "")
    overlays_declared_hidden = True
    for marker in ('id="sheet"', 'id="modal"', 'id="drawer"'):
        if marker in html and "hidden" not in html.split(marker, 1)[1][:140]:
            overlays_declared_hidden = False
    ok = css_hidden_ok and overlays_declared_hidden
    return {
        "gate_name": "Initial View Integrity",
        "decision": "pass" if ok else "fail",
        "css_hidden_rule": css_hidden_ok,
        "overlays_hidden_attr": overlays_declared_hidden,
        "checked_at": utc_now(),
    }


def _placeholder_lint(prototype_dir: Path) -> dict[str, Any]:
    hay = (_load_text(prototype_dir / "index.html") + "\n" + _load_text(prototype_dir / "app.js")).lower()
    markers = ["todo", "lorem", "ipsum", "占位", "placeholder", "来自 ui spec", "仅供说明", "原型说明"]
    hits = {m: hay.count(m) for m in markers if hay.count(m)}
    decision = "pass" if sum(hits.values()) <= 10 else "warn"
    return {"gate_name": "Placeholder Lint", "decision": decision, "hits": hits, "checked_at": utc_now()}


def _runtime_smoke(prototype_dir: Path, context: dict[str, Any]) -> dict[str, Any]:
    html = _load_text(prototype_dir / "index.html")
    css = _load_text(prototype_dir / "styles.css")
    js = _load_text(prototype_dir / "app.js")
    chrome = _find_chrome_executable()

    expected_kind = "src002-hifi" if _is_src002_hifi_required(context) else "spec-viewer"
    static_ok = bool(html.strip()) and bool(css.strip()) and bool(js.strip()) and 'src="app.js"' in html
    template_marker_ok = True if expected_kind != "src002-hifi" else 'name="lee-prototype-kind" content="hifi"' in html

    runtime_ok = False
    runtime_note = ""
    dom_excerpt = ""
    if chrome:
        server = None
        try:
            server, url = _serve_dir_for_smoke(prototype_dir)
            ok, dom = _chrome_dump_dom(chrome, url)
            if expected_kind == "src002-hifi":
                runtime_ok = ok and "生成训练计划" in dom
            else:
                runtime_ok = ok and ("Prototype Bundle" in dom or "Prototype" in dom)
            dom_excerpt = dom[:8000]
            runtime_note = "" if runtime_ok else "dom did not include expected render markers"
        finally:
            if server:
                with suppress(Exception):
                    server.shutdown()
                with suppress(Exception):
                    server.server_close()
    else:
        runtime_note = "chrome not found; runtime smoke skipped"

    decision = "pass"
    if not static_ok or not template_marker_ok:
        decision = "fail"
    if expected_kind == "src002-hifi" and (not chrome or not runtime_ok):
        decision = "fail"

    if dom_excerpt:
        write_text(prototype_dir / "runtime-smoke-dom.html", dom_excerpt)

    return {
        "gate_name": "Runtime Smoke",
        "decision": decision,
        "expected_kind": expected_kind,
        "static_ok": static_ok,
        "template_marker_ok": template_marker_ok,
        "runtime_ok": runtime_ok,
        "notes": runtime_note,
        "checked_at": utc_now(),
    }


def _parse_ui_spec_markdown(markdown: str) -> dict[str, Any]:
    lines = [line.rstrip("\n") for line in str(markdown or "").splitlines()]

    def humanize_field_name(field_name: str) -> str:
        return str(field_name or "").strip().replace("_", " ").title()

    def extract_field_options(note: str) -> list[str]:
        match = re.search(r"options\s*:\s*([^\n]+)", str(note or ""), flags=re.IGNORECASE)
        if not match:
            return []
        return [item.strip() for item in match.group(1).split(",") if item.strip()]

    def find_value(prefix: str) -> str:
        needle = f"- {prefix}:"
        for line in lines:
            if line.strip().startswith(needle):
                return line.split(":", 1)[1].strip()
        return ""

    def collect_bullets(after_line_prefix: str, stop_prefixes: tuple[str, ...]) -> list[str]:
        start = -1
        needle = after_line_prefix.strip()
        for idx, line in enumerate(lines):
            if line.strip() == needle:
                start = idx + 1
                break
        if start < 0:
            return []
        items: list[str] = []
        for line in lines[start:]:
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in stop_prefixes):
                break
            if stripped.startswith("- "):
                value = stripped[2:].strip()
                if value and value != "无":
                    items.append(value)
        return items

    def collect_numbered(after_heading: str) -> list[str]:
        start = -1
        for idx, line in enumerate(lines):
            if line.strip().startswith(after_heading):
                start = idx + 1
                break
        if start < 0:
            return []
        steps: list[str] = []
        for line in lines[start:]:
            stripped = line.strip()
            if not stripped:
                if steps:
                    break
                continue
            if stripped.startswith("#"):
                break
            if re.match(r"^\d+\.\s+", stripped):
                steps.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
                continue
            if stripped.startswith("### "):
                break
        return steps

    def collect_branch_paths() -> list[dict[str, Any]]:
        branches: list[dict[str, Any]] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("### Branch Path"):
                continue
            title = stripped.replace("###", "", 1).strip()
            steps: list[str] = []
            for line2 in lines[idx + 1 :]:
                s2 = line2.strip()
                if not s2:
                    if steps:
                        break
                    continue
                if s2.startswith("### "):
                    break
                if s2.startswith("## "):
                    break
                if re.match(r"^\d+\.\s+", s2):
                    steps.append(re.sub(r"^\d+\.\s+", "", s2).strip())
            if title and steps:
                branches.append({"title": title, "steps": steps})
        return branches

    def collect_states() -> list[dict[str, Any]]:
        states: list[dict[str, Any]] = []
        idx = 0
        while idx < len(lines):
            stripped = lines[idx].strip()
            if not stripped.startswith("### state:"):
                idx += 1
                continue
            name = stripped.split(":", 1)[1].strip()
            state: dict[str, Any] = {"name": name, "trigger": "", "ui_behavior": "", "user_options": ""}
            idx += 1
            while idx < len(lines):
                s2 = lines[idx].strip()
                if not s2:
                    idx += 1
                    continue
                if s2.startswith("### state:") or s2.startswith("## "):
                    break
                if s2.startswith("- trigger:"):
                    state["trigger"] = s2.split(":", 1)[1].strip()
                elif s2.startswith("- ui_behavior:"):
                    state["ui_behavior"] = s2.split(":", 1)[1].strip()
                elif s2.startswith("- user_options:"):
                    state["user_options"] = s2.split(":", 1)[1].strip()
                idx += 1
            states.append(state)
        return states

    def collect_codeblock(label: str) -> str:
        if label not in markdown:
            return ""
        in_block = False
        buffer: list[str] = []
        fence_start = "```text"
        fence_end = "```"
        for line in lines:
            if not in_block and line.strip() == fence_start:
                in_block = True
                continue
            if in_block and line.strip() == fence_end:
                break
            if in_block:
                buffer.append(line.rstrip())
        return "\n".join(buffer).strip()

    def collect_fields(section_heading: str, source: str) -> list[dict[str, Any]]:
        start = -1
        for idx, line in enumerate(lines):
            if line.strip() == section_heading:
                start = idx + 1
                break
        if start < 0:
            return []
        fields: list[dict[str, Any]] = []
        for line in lines[start:]:
            stripped = line.strip()
            if not stripped:
                if fields:
                    break
                continue
            if stripped.startswith("### ") or stripped.startswith("## "):
                break
            if not stripped.startswith("- "):
                continue
            body = stripped[2:].strip()
            if not body or body == "无":
                continue
            # examples:
            # - action (enum) - keep/downgrade/replace/skip
            # - micro_adjustment_id (string) - 微调建议 ID
            match = re.match(r"^(?P<name>[^()-]+?)\s*\((?P<typ>[^)]+)\)\s*(?:-\s*)?(?P<note>.*)$", body)
            if match:
                name = match.group("name").strip()
                typ = match.group("typ").strip()
                note = match.group("note").strip(" -")
            else:
                name = body.strip()
                typ = "string"
                note = ""
            fields.append(
                {
                    "field": name,
                    "label": humanize_field_name(name),
                    "type": typ,
                    "required": False,
                    "source": source,
                    "note": note,
                    "options": extract_field_options(note),
                }
            )
        return fields

    required_fields = collect_bullets("### Required Fields", ("###", "## "))
    display_fields = collect_fields("### Display Fields", "display")
    ui_visible_fields = collect_fields("### UI Visible Fields", "display")
    technical_payload_fields = collect_fields("### Technical Payload Fields", "system_payload")

    if len(ui_visible_fields) == 1 and str(ui_visible_fields[0].get("field") or "").strip() in {"所有 Display Fields", "All Display Fields"}:
        ui_visible_fields = list(display_fields)

    return {
        "ui_spec_id": find_value("ui_spec_id"),
        "linked_feat": find_value("linked_feat"),
        "page_name": find_value("page_name"),
        "page_type": find_value("page_type"),
        "platform": find_value("platform") or "web",
        "completeness_result": find_value("status") or "pass",
        "page_goal": find_value("page_goal"),
        "user_job": find_value("user_job"),
        "page_role_in_flow": find_value("page_role_in_flow"),
        "completion_definition": find_value("completion_definition"),
        "in_scope": collect_bullets("- in_scope:", ("- out_of_scope:", "## ")),
        "out_of_scope": collect_bullets("- out_of_scope:", ("## ",)),
        "entry_condition": find_value("entry_condition"),
        "exit_condition": find_value("exit_condition"),
        "upstream": find_value("upstream"),
        "downstream": find_value("downstream"),
        "main_user_path": collect_numbered("### Main Path"),
        "branch_paths": collect_branch_paths(),
        "ux_flow_notes": collect_bullets("## 6. UX Flow Notes", ("## 7.", "## 8.", "## 9.", "## 10.", "## 11.", "## 12.", "## 13.", "## 14.", "## 15.", "## 16.")),
        "page_sections": collect_bullets("- page_sections:", ("- information_priority:", "## ")),
        "information_priority": collect_bullets("- information_priority:", ("- action_priority:", "## ")),
        "action_priority": collect_bullets("- action_priority:", ("## ",)),
        "ascii_wireframe": collect_codeblock("## 8. ASCII Wireframe"),
        "states": collect_states(),
        "input_fields": collect_fields("### Input Fields", "user_input"),
        "display_fields": display_fields,
        "ui_visible_fields": ui_visible_fields,
        "technical_payload_fields": technical_payload_fields,
        "required_fields": required_fields,
        "derived_fields": collect_bullets("### Derived Fields", ("## ", "### ")),
        "user_actions": collect_bullets("### User Actions", ("### System Actions", "## ")),
        "system_actions": collect_bullets("### System Actions", ("## ",)),
        "frontend_validation_rules": collect_bullets("### Frontend Validation", ("### Backend Assumptions", "## ")),
        "backend_validation_assumptions": collect_bullets("### Backend Assumptions", ("## ",)),
        "data_dependencies": collect_bullets("- data_dependencies:", ("- api_touchpoints:", "## ")),
        "api_touchpoints": collect_bullets("- api_touchpoints:", ("- derived_logic:", "## ")),
        "derived_logic": collect_bullets("- derived_logic:", ("## ",)),
        "loading_feedback": find_value("loading_feedback"),
        "validation_feedback": find_value("validation_feedback"),
        "success_feedback": find_value("success_feedback"),
        "error_feedback": find_value("error_feedback"),
        "retry_behavior": find_value("retry_behavior"),
        "open_questions": collect_bullets("## 15. Open Questions", ("## 16.",)),
        "checklist": {},
        "slug": slugify(find_value("page_name") or find_value("ui_spec_id") or "page"),
    }


def resolve_ui_spec_bundle(repo_root: Path, feat_ref: str, feat_title: str = "") -> dict[str, Any] | None:
    base_dir = repo_root / "artifacts" / "feat-to-ui"
    if not base_dir.exists():
        return None
    candidates: list[tuple[float, Path, dict[str, Any]]] = []
    for candidate in base_dir.glob("*/ui-spec-bundle.json"):
        try:
            bundle = load_json(candidate)
        except Exception:
            continue
        manifest_path = candidate.parent / "package-manifest.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = load_json(manifest_path)
            except Exception:
                manifest = {}

        bundle_feat_ref = str(bundle.get("feat_ref") or manifest.get("feat_ref") or "").strip()
        bundle_feat_title = str(manifest.get("feat_title") or bundle.get("feat_title") or "").strip()

        matched = False
        if bundle_feat_ref and bundle_feat_ref == feat_ref:
            matched = True
        elif feat_title and bundle_feat_title and bundle_feat_title == feat_title:
            matched = True
        if not matched:
            continue

        ui_specs = d_list(bundle.get("ui_specs"))
        ui_spec_refs = [str(item).strip() for item in (bundle.get("ui_spec_refs") or []) if str(item).strip()]
        if not ui_specs and ui_spec_refs:
            parsed: list[dict[str, Any]] = []
            for ref in ui_spec_refs:
                ref_path = Path(ref)
                resolved = ref_path if ref_path.is_absolute() else (repo_root / ref_path)
                if not resolved.exists():
                    continue
                try:
                    parsed.append(_parse_ui_spec_markdown(resolved.read_text(encoding="utf-8")))
                except Exception:
                    continue
            ui_specs = d_list(parsed)
            if ui_specs:
                bundle = dict(bundle)
                bundle["ui_specs"] = ui_specs
                bundle["ui_spec_refs"] = ui_spec_refs

        if not ui_specs:
            continue
        candidates.append((candidate.stat().st_mtime, candidate, bundle))
    if not candidates:
        return None
    _, path, bundle = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
    return {"path": path.resolve(), "bundle": bundle}


def _extract_field_options(note: str) -> list[str]:
    match = re.search(r"options\s*:\s*([^\n]+)", str(note or ""), flags=re.IGNORECASE)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split(",") if item.strip()]


def _humanize_field_name(field_name: str) -> str:
    return str(field_name or "").strip().replace("_", " ").title()


def _field_view_model(field: dict[str, Any]) -> dict[str, Any]:
    note = str(field.get("note") or "").strip()
    return {
        "field": str(field.get("field") or "").strip(),
        "label": _humanize_field_name(str(field.get("field") or "").strip()),
        "type": str(field.get("type") or "string").strip(),
        "required": bool(field.get("required")),
        "source": str(field.get("source") or "").strip(),
        "note": note,
        "options": _extract_field_options(note),
    }


def _normalize_proto_field(field: dict[str, Any], linked_feat: str) -> dict[str, Any]:
    normalized = dict(field)
    if linked_feat.startswith("FEAT-SRC-001"):
        overrides = {
            "running_level": ["beginner", "intermediate", "experienced"],
            "recent_injury_status": ["none", "minor_but_runnable", "pain_or_recovering"],
        }
        if normalized.get("field") in overrides:
            options = overrides[normalized["field"]]
            normalized["options"] = options
            note = str(normalized.get("note") or "").strip()
            if re.search(r"options\s*:", note, flags=re.IGNORECASE):
                normalized["note"] = re.sub(
                    r"options\s*:\s*[^\n]+",
                    f"options: {', '.join(options)}",
                    note,
                    flags=re.IGNORECASE,
                )
    return normalized


def _required_ui_fields(unit: dict[str, Any]) -> list[str]:
    explicit = [str(item.get("field") if isinstance(item, dict) else item).strip() for item in unit.get("required_ui_fields") or [] if str(item.get("field") if isinstance(item, dict) else item).strip()]
    if explicit:
        return explicit
    required: list[str] = []
    for field in d_list(unit.get("input_fields")):
        source = str(field.get("source") or "").strip().lower()
        if field.get("required") and source in {"user_input", "user_choice", "display", "ui_state"}:
            name = str(field.get("field") or "").strip()
            if name:
                required.append(name)
    return required


def _buttons_for_family(family: str, index: int, total: int) -> list[dict[str, str]]:
    buttons: list[dict[str, str]] = []
    if index > 0:
        buttons.append({"label": "上一页", "action": "page_back", "tone": "ghost"})
    if index < total - 1:
        buttons.append({"label": "下一页", "action": "page_next", "tone": "ghost"})
    presets = {
        "form": [
            {"label": "提交建档", "action": "primary", "tone": "primary"},
            {"label": "查看校验失败", "action": "error", "tone": "danger"},
            {"label": "重置场景", "action": "reset", "tone": "ghost"},
        ],
        "panel": [
            {"label": "显示正常建议", "action": "primary", "tone": "primary"},
            {"label": "显示重试异常", "action": "error", "tone": "danger"},
            {"label": "查看补充信息", "action": "skip", "tone": "secondary"},
            {"label": "重置场景", "action": "reset", "tone": "ghost"},
        ],
        "card_list": [
            {"label": "保存当前卡", "action": "primary", "tone": "primary"},
            {"label": "显示保存失败", "action": "error", "tone": "danger"},
            {"label": "稍后再做", "action": "skip", "tone": "secondary"},
            {"label": "重置场景", "action": "reset", "tone": "ghost"},
        ],
        "entry": [
            {"label": "连接设备", "action": "primary", "tone": "primary"},
            {"label": "连接失败", "action": "error", "tone": "danger"},
            {"label": "跳过连接", "action": "skip", "tone": "secondary"},
            {"label": "重置场景", "action": "reset", "tone": "ghost"},
        ],
        "status": [
            {"label": "读取一致状态", "action": "primary", "tone": "primary"},
            {"label": "显示冲突阻断", "action": "error", "tone": "danger"},
            {"label": "恢复后重读", "action": "skip", "tone": "secondary"},
            {"label": "重置场景", "action": "reset", "tone": "ghost"},
        ],
    }
    buttons.extend(presets.get(family, [{"label": "继续", "action": "primary", "tone": "primary"}, {"label": "重置场景", "action": "reset", "tone": "ghost"}]))
    return buttons


def _page_model(unit: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    family = first(unit.get("page_type_family"), page_type_family(first(unit.get("page_type"), "")))
    linked_feat = first(unit.get("linked_feat"), unit.get("feat_ref"), "")
    input_fields = [_normalize_proto_field(_field_view_model(field), linked_feat) for field in d_list(unit.get("input_fields"))]
    display_fields = [_normalize_proto_field(_field_view_model(field), linked_feat) for field in d_list(unit.get("display_fields"))]
    editable_ui_fields = [_normalize_proto_field(_field_view_model(field), linked_feat) for field in d_list(unit.get("editable_ui_fields"))]
    ui_visible_fields = [_normalize_proto_field(_field_view_model(field), linked_feat) for field in d_list(unit.get("ui_visible_fields"))]
    technical_payload_fields = [_normalize_proto_field(_field_view_model(field), linked_feat) for field in d_list(unit.get("technical_payload_fields"))]
    return {
        "page_id": first(unit.get("slug"), slugify(first(unit.get("page_name"), "page"))),
        "title": first(unit.get("page_name"), "Page"),
        "page_goal": first(unit.get("page_goal"), ""),
        "page_type": first(unit.get("page_type"), ""),
        "page_type_family": family,
        "platform": first(unit.get("platform"), "web"),
        "completion_definition": first(unit.get("completion_definition"), ""),
        "entry_condition": first(unit.get("entry_condition"), ""),
        "exit_condition": first(unit.get("exit_condition"), ""),
        "main_path": unit.get("main_user_path") or [],
        "branch_paths": unit.get("branch_paths") or [],
        "states": unit.get("states") or [],
        "page_sections": unit.get("page_sections") or [],
        "information_priority": unit.get("information_priority") or [],
        "action_priority": unit.get("action_priority") or [],
        "input_fields": input_fields,
        "display_fields": display_fields,
        "editable_ui_fields": editable_ui_fields,
        "ui_visible_fields": ui_visible_fields,
        "technical_payload_fields": technical_payload_fields,
        "required_fields": [str(item.get("field") if isinstance(item, dict) else item).strip() for item in unit.get("required_fields") or [] if str(item.get("field") if isinstance(item, dict) else item).strip()],
        "required_ui_fields": _required_ui_fields(unit),
        "user_actions": unit.get("user_actions") or [],
        "system_actions": unit.get("system_actions") or [],
        "frontend_validation_rules": unit.get("frontend_validation_rules") or [],
        "data_dependencies": unit.get("data_dependencies") or [],
        "api_touchpoints": unit.get("api_touchpoints") or [],
        "loading_feedback": first(unit.get("loading_feedback"), ""),
        "validation_feedback": first(unit.get("validation_feedback"), ""),
        "success_feedback": first(unit.get("success_feedback"), ""),
        "error_feedback": first(unit.get("error_feedback"), ""),
        "retry_behavior": first(unit.get("retry_behavior"), ""),
        "ascii_wireframe": first(unit.get("ascii_wireframe"), ""),
        "buttons": _buttons_for_family(family, index, total),
        "open_questions": unit.get("open_questions") or [],
        "ui_spec_id": first(unit.get("ui_spec_id"), ""),
        "fidelity_class": "ui_spec_backed" if first(unit.get("ui_spec_id"), "").strip() else "feat_derived",
    }


def _render_index_html(feat_title: str) -> str:
    return render_resource_text(("prototype", "index.html"), {"__LEE_TITLE__": feat_title})


def _render_styles() -> str:
    return read_resource_text("prototype", "styles.css")


def _render_app_js() -> str:
    return read_resource_text("prototype", "app.js")

def _review_guide(bundle: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Prototype Review Guide",
            "",
            f"0. Read `{bundle['journey_structural_spec_ref']}` and `{bundle['ui_shell_snapshot_ref']}` first.",
            "1. Open `prototype/index.html` in a browser.",
            "2. Click through every page in the left journey navigation.",
            "3. Use the left state pills to inspect every named state.",
            "4. Trigger the bottom action buttons and confirm the preview surface responds coherently.",
            "5. Verify happy path plus error / skip flow stay aligned with the FEAT boundary.",
            "",
            "## Pages",
            *[f"- {page['title']}" for page in bundle["pages"]],
        ]
    )


def _container_hint(page: dict[str, Any]) -> str:
    return {
        "form": "page",
        "entry": "page",
        "status": "page",
        "panel": "bottom_sheet",
        "card_list": "page",
    }.get(str(page.get("page_type_family") or "").strip(), "page")


def _journey_structural_spec(bundle: dict[str, Any]) -> str:
    lines = [
        f"# Journey Structural Spec for {bundle['feat_ref']}",
        "",
        f"- journey_structural_spec_version: {JOURNEY_SPEC_VERSION}",
        f"- feat_ref: {bundle['feat_ref']}",
        f"- feat_title: {bundle['feat_title']}",
        "",
        "## 1. Journey Main Chain",
        *[f"{idx + 1}. {page['title']}" for idx, page in enumerate(bundle["pages"])],
        "",
        "## 2. Page Map",
        *[
            f"- {page['page_id']}: family={page['page_type_family']} goal={page['page_goal'] or 'n/a'}"
            for page in bundle["pages"]
        ],
        "",
        "## 3. Decision Points",
        *[
            f"- {page['title']}: {'; '.join(state['name'] for state in page.get('states', [])[:4]) or 'no named states'}"
            for page in bundle["pages"]
        ],
        "",
        "## 4. CTA Hierarchy",
        *[
            f"- {page['title']}: primary={next((button['label'] for button in page['buttons'] if button.get('tone') == 'primary'), 'TBD')} | secondary={', '.join(button['label'] for button in page['buttons'] if button.get('tone') != 'primary') or 'none'}"
            for page in bundle["pages"]
        ],
        "",
        "## 5. Container Hints",
        *[f"- {page['title']}: {_container_hint(page)}" for page in bundle["pages"]],
        "",
        "## 6. Error / Degraded / Retry Paths",
        *[
            f"- {page['title']}: {'; '.join(state['name'] for state in page.get('states', []) if any(token in state['name'].lower() for token in ('error', 'failed', 'blocked', 'degraded', 'retry', 'conflict', 'validation'))) or 'no explicit degraded/error path'}"
            for page in bundle["pages"]
        ],
        "",
        "## 7. Open Questions / Frozen Assumptions",
        "- Assumption: page family and container choice stay within the current UI Shell Source rules.",
        f"- Frozen source: {bundle['ui_shell_source_ref']} @ {bundle['ui_shell_version']}",
    ]
    return "\n".join(lines)


def _validate_journey_structural_spec(text: str) -> list[str]:
    errors = validate_structured_sections(text, "journey structural spec", JOURNEY_REQUIRED_SECTIONS)
    if "TBD" in text:
        errors.append("journey structural spec must not contain TBD placeholders")
    return errors


def _validate_ui_shell_snapshot(text: str) -> list[str]:
    errors = validate_structured_sections(text, "ui shell snapshot", SHELL_REQUIRED_SECTIONS)
    metadata = extract_shell_metadata(text)
    for key in ("ui_shell_source_id", "ui_shell_family", "ui_shell_version", "shell_change_policy"):
        if not metadata.get(key):
            errors.append(f"ui shell snapshot missing metadata: {key}")
    return errors


def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    feat_ref = context["feat_ref"]
    feature = context["feature"]
    output_dir = repo_root / "artifacts" / "feat-to-proto" / f"{slugify(run_id or feat_ref)}--{slugify(feat_ref)}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    ui_shell_source_text = Path(WORKSPACE_ROOT / UI_SHELL_SOURCE_REF).read_text(encoding="utf-8")
    ui_shell_metadata = extract_shell_metadata(ui_shell_source_text)
    ui_shell_snapshot_hash = sha256_text(ui_shell_source_text)
    feat_title = first(feature.get("title"), "").strip()
    ui_spec_context = resolve_ui_spec_bundle(repo_root, feat_ref, feat_title)
    units = d_list(ui_spec_context["bundle"].get("ui_specs")) if ui_spec_context else build_units(feature, feat_ref)
    pages = [_page_model(unit, index, len(units)) for index, unit in enumerate(units)]
    bundle = {
        "artifact_type": "prototype_package",
        "workflow_key": "dev.feat-to-proto",
        "feat_ref": feat_ref,
        "feat_title": feat_title or feat_ref,
        "prototype_entry_ref": "prototype/index.html",
        "journey_structural_spec_ref": JOURNEY_SPEC_REF,
        "journey_structural_spec_version": JOURNEY_SPEC_VERSION,
        "journey_ascii_ref": JOURNEY_SPEC_REF,
        "ui_shell_snapshot_ref": UI_SHELL_SNAPSHOT_REF,
        "ui_shell_ref": UI_SHELL_SNAPSHOT_REF,
        "ui_shell_source_ref": UI_SHELL_SOURCE_REF,
        "ui_shell_version": ui_shell_metadata.get("ui_shell_version", ""),
        "ui_shell_family": ui_shell_metadata.get("ui_shell_family", ""),
        "ui_shell_snapshot_hash": ui_shell_snapshot_hash,
        "shell_change_policy": ui_shell_metadata.get("shell_change_policy", ""),
        "prototype_source": "ui_spec_package" if ui_spec_context else "feat_freeze_package",
        "ui_spec_package_ref": rel(ui_spec_context["path"], repo_root) if ui_spec_context else "",
        "pages": pages,
        "source_refs": (ui_spec_context["bundle"].get("source_refs") if ui_spec_context else None) or feature.get("source_refs") or context["bundle"].get("source_refs") or [],
    }
    if _is_src002_hifi_required(context):
        bundle["prototype_source"] = "src002_journey_hifi_template"
        bundle["fidelity_target"] = "hifi_interactive_html"
    defects = [{"page_id": page["page_id"], "type": "human_review_pending"} for page in pages]
    fidelity_issues: list[str] = []
    blocking_points = [{"id": "human-review-required", "description": "Prototype must be reviewed by a human."}]
    if not ui_spec_context:
        fidelity_issues.append("ui_spec_package not resolved (by feat_ref or feat_title); output is feat-derived and can drift far from high-fidelity UI.")
        blocking_points.append(
            {
                "id": "ui-authority-missing",
                "description": "No ui_spec_package could be resolved; do not treat this output as a high-fidelity UI prototype.",
            }
        )
    review = build_prototype_review(
        verdict="revise",
        review_contract_ref="ssot/adr/ADR-039-Reviewer 能力提升采用分层 Review Contract 与 Coverage Gate 基线.MD",
        reviewer_identity="pending_human_review",
        reviewed_at=utc_now(),
        checks={
            "journey_check": {"passed": False, "issues": ["human review pending"]},
            "cta_hierarchy_check": {"passed": False, "issues": ["human review pending"]},
            "flow_consistency_check": {"passed": False, "issues": ["human review pending"]},
            "state_experience_check": {"passed": False, "issues": ["human review pending"]},
            "feat_alignment_check": {"passed": False, "issues": [*fidelity_issues, "human review pending"] if fidelity_issues else ["human review pending"]},
        },
        blocking_points=blocking_points,
    )
    completeness = {
        "gate_name": "Prototype Experience Completeness Check",
        "decision": "pass" if pages else "fail",
        "pages": [{"page_id": page["page_id"], "button_count": len(page["buttons"]), "state_count": len(page["states"])} for page in pages],
        "fidelity": {
            "ui_spec_resolved": bool(ui_spec_context),
            "ui_spec_page_count": len([page for page in pages if str(page.get("ui_spec_id") or "").strip()]),
            "page_count": len(pages),
        },
        "checked_at": utc_now(),
    }
    freeze_gate = {
        "workflow_key": "dev.feat-to-proto",
        "gate_name": "Prototype Human Review Gate",
        "freeze_ready": False,
        "checked_at": utc_now(),
        "checks": {
            "human_review_approved": False,
            "review_coverage_complete": True,
            "no_blocking_points": False,
            "journey_structural_spec_present": True,
            "journey_structural_spec_quality_pass": True,
            "ui_shell_snapshot_present": True,
            "ui_shell_snapshot_quality_pass": True,
        },
    }
    journey_structural_spec_text = _journey_structural_spec(bundle)
    journey_errors = _validate_journey_structural_spec(journey_structural_spec_text)
    shell_errors = _validate_ui_shell_snapshot(ui_shell_source_text)
    completeness["journey_structural_spec"] = {"decision": "pass" if not journey_errors else "fail", "errors": journey_errors}
    completeness["ui_shell_snapshot"] = {"decision": "pass" if not shell_errors else "fail", "errors": shell_errors}
    if journey_errors or shell_errors or not pages:
        completeness["decision"] = "fail"
        freeze_gate["checks"]["journey_structural_spec_quality_pass"] = not journey_errors
        freeze_gate["checks"]["ui_shell_snapshot_quality_pass"] = not shell_errors
    write_json(
        output_dir / "package-manifest.json",
        {
            "artifact_type": "prototype_package",
            "workflow_key": "dev.feat-to-proto",
            "run_id": run_id or feat_ref,
            "feat_ref": feat_ref,
            "journey_structural_spec_ref": JOURNEY_SPEC_REF,
            "ui_shell_snapshot_ref": UI_SHELL_SNAPSHOT_REF,
            "ui_shell_source_ref": UI_SHELL_SOURCE_REF,
            "ui_shell_version": bundle["ui_shell_version"],
            "ui_shell_snapshot_hash": ui_shell_snapshot_hash,
            "shell_change_policy": bundle["shell_change_policy"],
        },
    )
    write_json(output_dir / "prototype-bundle.json", bundle)
    write_text(output_dir / JOURNEY_SPEC_REF, journey_structural_spec_text)
    write_text(output_dir / UI_SHELL_SNAPSHOT_REF, ui_shell_source_text)
    write_text(
        output_dir / "prototype-bundle.md",
        "\n".join(
            [
                f"# Prototype Bundle for {feat_ref}",
                "",
                f"- feat_title: {bundle['feat_title']}",
                f"- page_count: {len(pages)}",
                f"- prototype_source: {bundle['prototype_source']}",
                f"- journey_structural_spec_ref: {bundle['journey_structural_spec_ref']}",
                f"- ui_shell_snapshot_ref: {bundle['ui_shell_snapshot_ref']}",
                f"- ui_shell_source_ref: {bundle['ui_shell_source_ref']}",
                f"- ui_shell_version: {bundle['ui_shell_version']}",
                *[f"- page: {page['title']} | family={page['page_type_family']} | states={len(page['states'])}" for page in pages],
            ]
        ),
    )
    write_text(output_dir / "prototype-flow-map.md", "\n".join(["# Prototype Flow Map", "", *[f"{index+1}. {page['title']}" for index, page in enumerate(pages)]]))
    prototype_dir = output_dir / "prototype"
    if _is_src002_hifi_required(context):
        _copy_template_dir(SRC002_HIFI_TEMPLATE_ROOT, prototype_dir)
    else:
        write_text(prototype_dir / "index.html", _render_index_html(bundle["feat_title"]))
        write_text(prototype_dir / "styles.css", _render_styles())
        write_text(prototype_dir / "app.js", _render_app_js())

    mock_payload = {
        "feat_ref": feat_ref,
        "feat_title": bundle["feat_title"],
        "source_refs": bundle["source_refs"],
        "journey_structural_spec_ref": JOURNEY_SPEC_REF,
        "ui_shell_snapshot_ref": UI_SHELL_SNAPSHOT_REF,
        "pages": pages,
    }
    write_json(prototype_dir / "mock-data.json", mock_payload)
    write_text(prototype_dir / "mock-data.js", "window.__LEE_PROTO_DATA__ = " + json.dumps(mock_payload, ensure_ascii=False, indent=2) + ";\n")

    if _is_src002_hifi_required(context):
        handoff = load_json(Path(context["input_dir"]) / "handoff-to-feat-downstreams.json")
        journey_model = {
            "feat_ref": "SRC002-JOURNEY",
            "journey_surface_inventory": handoff.get("journey_surface_inventory") or [],
            "journey_main_path": handoff.get("journey_main_path") or [],
            "feat_dependency_order": [item.get("feat_ref") for item in (handoff.get("feature_dependency_map") or []) if isinstance(item, dict) and item.get("feat_ref")],
            "checked_at": utc_now(),
        }
        write_json(prototype_dir / "journey-model.json", journey_model)
        write_text(prototype_dir / "journey-model.js", "window.__LEE_JOURNEY_MODEL__ = " + json.dumps(journey_model, ensure_ascii=False, indent=2) + ";\n")

    fidelity_report = _build_fidelity_report(bundle, context)
    route_map = _build_route_map(bundle, context)
    route_map["decision"] = "pass" if str(route_map.get("entry_route_id") or "").strip() and route_map.get("routes") else "fail"
    route_map["checked_at"] = utc_now()
    reachability_report = _check_journey_reachability(route_map, context)
    initial_view_report = _check_initial_view_integrity(prototype_dir)
    placeholder_report = _placeholder_lint(prototype_dir)
    runtime_smoke_report = _runtime_smoke(prototype_dir, context)

    write_json(output_dir / "prototype-fidelity-report.json", fidelity_report)
    write_json(output_dir / "prototype-route-map.json", route_map)
    write_json(output_dir / "prototype-journey-reachability-report.json", reachability_report)
    write_json(output_dir / "prototype-initial-view-report.json", initial_view_report)
    write_json(output_dir / "prototype-placeholder-lint.json", placeholder_report)
    write_json(output_dir / "prototype-runtime-smoke.json", runtime_smoke_report)

    completeness["fidelity_gate"] = fidelity_report
    completeness["route_map"] = {"decision": route_map["decision"], "entry_route_id": route_map.get("entry_route_id"), "route_count": len(route_map.get("routes") or [])}
    completeness["journey_reachability"] = reachability_report
    completeness["initial_view_integrity"] = initial_view_report
    completeness["placeholder_lint"] = placeholder_report
    completeness["runtime_smoke"] = runtime_smoke_report

    freeze_gate["checks"]["fidelity_gate_pass"] = fidelity_report.get("decision") == "pass"
    freeze_gate["checks"]["route_map_present"] = route_map.get("decision") == "pass"
    freeze_gate["checks"]["journey_reachability_pass"] = reachability_report.get("decision") == "pass"
    freeze_gate["checks"]["initial_view_integrity_pass"] = initial_view_report.get("decision") == "pass"
    freeze_gate["checks"]["placeholder_lint_pass"] = placeholder_report.get("decision") in {"pass", "warn"}
    freeze_gate["checks"]["runtime_smoke_pass"] = runtime_smoke_report.get("decision") == "pass"

    if (
        fidelity_report.get("decision") != "pass"
        or route_map.get("decision") != "pass"
        or reachability_report.get("decision") != "pass"
        or initial_view_report.get("decision") != "pass"
        or runtime_smoke_report.get("decision") != "pass"
        or journey_errors
        or shell_errors
        or not pages
    ):
        completeness["decision"] = "fail"

    write_text(output_dir / "prototype-review-guide.md", _review_guide(bundle))
    write_json(output_dir / "prototype-completeness-report.json", completeness)
    write_json(output_dir / "prototype-review-report.json", review)
    write_json(output_dir / "prototype-defect-list.json", defects)
    write_json(output_dir / "prototype-freeze-gate.json", freeze_gate)
    write_json(output_dir / "execution-evidence.json", {"workflow_key": "dev.feat-to-proto", "run_id": run_id or feat_ref, "generated_at": utc_now(), "artifacts_dir": str(output_dir)})
    write_json(output_dir / "supervision-evidence.json", {"workflow_key": "dev.feat-to-proto", "run_id": run_id or feat_ref, "review_completed_at": utc_now(), "decision": "review_required"})
    return {"ok": True, "artifacts_dir": str(output_dir), "freeze_ready": False}


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    review = load_json(artifacts_dir / "prototype-review-report.json")
    bundle = load_json(artifacts_dir / "prototype-bundle.json")
    journey_text = (artifacts_dir / JOURNEY_SPEC_REF).read_text(encoding="utf-8")
    shell_text = (artifacts_dir / UI_SHELL_SNAPSHOT_REF).read_text(encoding="utf-8")
    fidelity = load_json(artifacts_dir / "prototype-fidelity-report.json")
    route_map = load_json(artifacts_dir / "prototype-route-map.json")
    reachability = load_json(artifacts_dir / "prototype-journey-reachability-report.json")
    initial_view = load_json(artifacts_dir / "prototype-initial-view-report.json")
    placeholder = load_json(artifacts_dir / "prototype-placeholder-lint.json")
    runtime_smoke = load_json(artifacts_dir / "prototype-runtime-smoke.json")
    errors.extend(validate_prototype_review(review))
    errors.extend(_validate_journey_structural_spec(journey_text))
    errors.extend(_validate_ui_shell_snapshot(shell_text))
    for key in ("journey_structural_spec_ref", "ui_shell_snapshot_ref", "ui_shell_source_ref", "ui_shell_version", "ui_shell_snapshot_hash", "shell_change_policy"):
        if not str(bundle.get(key) or "").strip():
            errors.append(f"prototype bundle missing {key}")

    def _decision(label: str, payload: dict[str, Any]) -> str:
        decision = str((payload or {}).get("decision") or "").strip().lower()
        if decision not in {"pass", "fail", "warn"}:
            errors.append(f"{label} missing/invalid decision: {decision or '(empty)'}")
        return decision

    if _decision("prototype-fidelity-report.json", fidelity) != "pass":
        errors.append("prototype fidelity gate failed")
    if _decision("prototype-route-map.json", route_map) != "pass":
        errors.append("prototype route map gate failed")
    if _decision("prototype-journey-reachability-report.json", reachability) != "pass":
        errors.append("prototype journey reachability gate failed")
    if _decision("prototype-initial-view-report.json", initial_view) != "pass":
        errors.append("prototype initial view integrity gate failed")
    if _decision("prototype-runtime-smoke.json", runtime_smoke) != "pass":
        errors.append("prototype runtime smoke gate failed")
    if _decision("prototype-placeholder-lint.json", placeholder) == "fail":
        errors.append("prototype placeholder lint gate failed")
    return errors, {
        "review": review,
        "freeze_gate": load_json(artifacts_dir / "prototype-freeze-gate.json"),
        "bundle": bundle,
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, result = validate_output_package(artifacts_dir)
    if errors:
        return False, errors
    review = result["review"]
    if review.get("verdict") != "approved":
        return False, ["prototype review must be approved before freeze-ready handoff"]
    if review.get("blocking_points"):
        return False, ["prototype review must not contain blocking_points"]
    if review.get("coverage_declaration", {}).get("not_checked"):
        return False, ["prototype review coverage must not contain not_checked items"]
    if not str(review.get("reviewer_identity") or "").strip() or str(review.get("reviewer_identity")) == "pending_human_review":
        return False, ["prototype review must record a real human reviewer identity"]
    return True, []


def collect_evidence_report(artifacts_dir: Path) -> Path:
    report_path = artifacts_dir / "evidence-report.md"
    if not report_path.exists():
        write_text(report_path, "# Prototype Evidence Report\n")
    return report_path


def supervisor_review(artifacts_dir: Path, run_id: str) -> dict[str, Any]:
    ok, errors = validate_package_readiness(artifacts_dir)
    gate = load_json(artifacts_dir / "prototype-freeze-gate.json")
    gate["freeze_ready"] = ok
    gate["checked_at"] = utc_now()
    checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
    checks.update(
        {
            "human_review_approved": ok,
            "review_coverage_complete": not errors,
            "no_blocking_points": ok,
        }
    )
    gate["checks"] = checks
    write_json(artifacts_dir / "prototype-freeze-gate.json", gate)
    write_json(
        artifacts_dir / "supervision-evidence.json",
        {"workflow_key": "dev.feat-to-proto", "run_id": run_id, "review_completed_at": utc_now(), "decision": "approved" if ok else "revise", "errors": errors},
    )
    return {"ok": ok, "errors": errors, "freeze_ready": ok}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the feat-to-proto workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--feat-ref", required=True)
    run.add_argument("--repo-root")
    run.add_argument("--run-id")
    run.add_argument("--allow-update", action="store_true")
    run.set_defaults(func=command_run)
    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.add_argument("--feat-ref", required=True)
    vin.add_argument("--repo-root")
    vin.set_defaults(func=command_validate_input)
    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=command_validate_output)
    review = sub.add_parser("supervisor-review")
    review.add_argument("--artifacts-dir", required=True)
    review.add_argument("--run-id", default="")
    review.set_defaults(func=command_supervisor_review)
    ready = sub.add_parser("validate-package-readiness")
    ready.add_argument("--artifacts-dir", required=True)
    ready.set_defaults(func=command_validate_package_readiness)
    ev = sub.add_parser("collect-evidence")
    ev.add_argument("--artifacts-dir", required=True)
    ev.set_defaults(func=command_collect_evidence)
    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=command_validate_package_readiness)
    return parser


def command_run(args: argparse.Namespace) -> int:
    errors, context = validate_input_package(args.input, args.feat_ref, repo_root_from(args.repo_root))
    result = {"ok": False, "errors": errors}
    if not errors:
        result = build_package(context, repo_root_from(args.repo_root), args.run_id or "", args.allow_update)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(args.input, args.feat_ref, repo_root_from(getattr(args, "repo_root", None)))
    print(json.dumps({"ok": not errors, "result": str(result.get("input_dir") or ""), "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


def command_validate_output(args: argparse.Namespace) -> int:
    errors, _ = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(Path(args.artifacts_dir).resolve(), args.run_id or "")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def command_collect_evidence(args: argparse.Namespace) -> int:
    print(json.dumps({"ok": True, "report_path": str(collect_evidence_report(Path(args.artifacts_dir).resolve()))}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

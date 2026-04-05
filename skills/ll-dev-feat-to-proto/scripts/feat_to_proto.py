#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
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
    "prototype-flow-map.md",
    "prototype-review-guide.md",
    "prototype-completeness-report.json",
    "prototype-review-report.json",
    "prototype-defect-list.json",
    "prototype-freeze-gate.json",
    "execution-evidence.json",
    "supervision-evidence.json",
    "prototype/index.html",
    "prototype/styles.css",
    "prototype/app.js",
    "prototype/mock-data.json",
]


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
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{feat_title} Prototype</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <main class="app">
    <aside class="sidebar">
      <p class="eyebrow">FEAT Prototype</p>
      <h1 id="feat-title"></h1>
      <p class="sidebar-ref" id="feat-ref"></p>
      <section class="sidebar-card">
        <h2>Journey</h2>
        <ol id="journey-nav"></ol>
      </section>
      <section class="sidebar-card">
        <h2>States</h2>
        <div class="state-pills" id="state-pills"></div>
      </section>
      <section class="sidebar-card">
        <h2>Trace</h2>
        <ul class="source-list" id="source-refs"></ul>
      </section>
    </aside>
    <section class="canvas">
      <header class="hero">
        <p class="eyebrow">Static HTML prototype</p>
        <h2 id="page-title"></h2>
        <p id="page-goal"></p>
        <div class="hero-meta" id="hero-meta"></div>
      </header>
      <section class="preview-grid">
        <article class="card surface-card">
          <div class="card-head">
            <h3>Interactive Surface</h3>
            <p id="state-caption"></p>
          </div>
          <div id="preview-surface"></div>
        </article>
        <div class="stack">
          <section class="card">
            <h3>Current State</h3>
            <div id="state-summary"></div>
          </section>
          <section class="card">
            <h3>Completion Boundary</h3>
            <div id="completion-summary"></div>
          </section>
        </div>
      </section>
      <section class="detail-grid">
        <article class="card">
          <h3>Main Journey</h3>
          <ol id="main-path"></ol>
        </article>
        <article class="card">
          <h3>Failure / Alternate Paths</h3>
          <div id="branch-paths"></div>
        </article>
        <article class="card">
          <h3>Field Boundary</h3>
          <div id="field-boundary"></div>
        </article>
        <article class="card">
          <h3>Validation & Integrations</h3>
          <div id="technical-boundary"></div>
        </article>
        <article class="card wireframe-card">
          <h3>Wireframe</h3>
          <pre id="wireframe"></pre>
        </article>
      </section>
      <footer class="card actions-card">
        <div class="actions-meta" id="action-hint"></div>
        <div class="button-row" id="actions"></div>
      </footer>
    </section>
  </main>
  <script src="app.js"></script>
</body>
</html>"""


def _render_styles() -> str:
    return """:root{
  --bg:#f4f1ea;
  --ink:#152126;
  --muted:#5c6a70;
  --panel:#fffdf8;
  --line:#d9d1c3;
  --primary:#1f6a5b;
  --primary-ink:#f4fffb;
  --danger:#b74a32;
  --danger-ink:#fff4ef;
  --secondary:#d8e4df;
  --secondary-ink:#16352e;
  --ghost:#ece7dc;
  --shadow:0 16px 40px rgba(21,33,38,.08);
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:"IBM Plex Sans","Segoe UI",sans-serif;
  background:
    radial-gradient(circle at top right, rgba(31,106,91,.16), transparent 28%),
    linear-gradient(180deg,#f7f4ee 0%,var(--bg) 100%);
  color:var(--ink);
}
.app{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.sidebar{
  background:linear-gradient(180deg,#132328 0%,#172d33 100%);
  color:#f7fbfc;
  padding:28px 24px;
  border-right:1px solid rgba(255,255,255,.08);
}
.sidebar-ref,.source-list,.sidebar-card{color:rgba(247,251,252,.76)}
.sidebar-card{
  margin-top:20px;
  padding:18px;
  border:1px solid rgba(255,255,255,.08);
  border-radius:20px;
  background:rgba(255,255,255,.04);
}
.sidebar-card h2{margin:0 0 12px;font-size:14px;letter-spacing:.04em;text-transform:uppercase}
.source-list,.state-pills,#journey-nav{display:grid;gap:10px;padding:0;margin:0;list-style:none}
#journey-nav a{
  display:block;
  padding:12px 14px;
  border-radius:14px;
  background:rgba(255,255,255,.04);
  color:inherit;
  text-decoration:none;
}
#journey-nav li.active a{background:rgba(255,255,255,.14);color:#fff;font-weight:600}
.canvas{padding:32px;display:grid;gap:18px}
.hero,.card{
  background:var(--panel);
  border:1px solid var(--line);
  border-radius:24px;
  box-shadow:var(--shadow);
}
.hero{padding:28px}
.hero h2{margin:8px 0 10px;font-size:32px;line-height:1.1}
.hero p{margin:0;color:var(--muted)}
.eyebrow{
  margin:0;
  font-size:11px;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:#7f8c92;
}
.hero-meta,.info-chip-row,.button-row,.preview-grid,.detail-grid,.stack,.field-grid,.metric-grid,.provider-grid,.task-grid,.task-list{display:flex;gap:12px;flex-wrap:wrap}
.hero-meta{margin-top:16px}
.preview-grid{display:grid;grid-template-columns:1.45fr .9fr;align-items:start}
.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.stack{display:grid;gap:18px}
.card{padding:22px}
.card h3{margin:0 0 14px;font-size:18px}
.card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px}
.card-head p{margin:0;color:var(--muted)}
.surface-card{padding-bottom:26px}
.state-pills button,.button-row button{
  border:0;
  border-radius:999px;
  padding:11px 16px;
  font:inherit;
  cursor:pointer;
}
.state-pills button{
  width:100%;
  text-align:left;
  background:rgba(255,255,255,.06);
  color:#eef7f9;
}
.state-pills button.active{background:#e5f4ef;color:#14352d;font-weight:700}
.button-row button[data-tone="primary"]{background:var(--primary);color:var(--primary-ink)}
.button-row button[data-tone="danger"]{background:var(--danger);color:var(--danger-ink)}
.button-row button[data-tone="secondary"]{background:var(--secondary);color:var(--secondary-ink)}
.button-row button[data-tone="ghost"]{background:var(--ghost);color:var(--ink)}
.chip,.pill,.tone-pill{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:7px 12px;
  border-radius:999px;
  border:1px solid var(--line);
  background:#f8f5ee;
  color:var(--ink);
  font-size:13px;
}
.tone-pill.good{background:#e0f0eb;color:#16463c}
.tone-pill.warn{background:#fff0d9;color:#7d5312}
.tone-pill.danger{background:#fde5de;color:#812f1f}
.surface{
  display:grid;
  gap:16px;
  background:linear-gradient(180deg,#fcfaf5 0%,#f2ece1 100%);
  border:1px solid var(--line);
  border-radius:22px;
  padding:22px;
}
.surface-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.surface-header h4{margin:0;font-size:22px}
.surface-header p,.muted{margin:0;color:var(--muted)}
.banner{
  border-radius:18px;
  padding:14px 16px;
  border:1px solid var(--line);
  background:#fff;
}
.banner.good{background:#ecf7f3}
.banner.warn{background:#fff5df}
.banner.danger{background:#feebe4}
.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.field-card,.metric-card,.provider-card,.task-list article,.task-stage,.mini-card{
  border:1px solid var(--line);
  border-radius:18px;
  background:#fff;
  padding:14px;
}
.field-card.has-error{border-color:#d46a50;background:#fff2ed}
.field-card header,.provider-card header{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:10px}
.field-card strong,.metric-card strong,.provider-card strong{font-size:15px}
.field-card small,.metric-card small,.provider-card small,.task-list small{color:var(--muted)}
.field-input,.field-select,.field-textarea{
  margin-top:10px;
  width:100%;
  padding:11px 12px;
  border-radius:14px;
  border:1px solid var(--line);
  background:#faf7f0;
  color:var(--ink);
}
.field-textarea{min-height:110px;resize:none}
.surface-footer{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.device{display:flex;justify-content:center}
.device-frame{
  width:360px;
  max-width:100%;
  background:linear-gradient(180deg,#ffffff 0%,#faf7f0 100%);
  border:1px solid var(--line);
  border-radius:34px;
  overflow:hidden;
  box-shadow:0 18px 44px rgba(21,33,38,.14);
}
.device-status{
  display:flex;
  justify-content:space-between;
  gap:10px;
  padding:12px 14px;
  background:rgba(216,228,223,.55);
}
.device-top{padding:16px 16px 10px}
.device-top strong{display:block;font-size:16px;margin-bottom:6px}
.device-body{padding:0 16px 16px;display:grid;gap:12px}
.device-header{
  border:1px solid var(--line);
  border-radius:18px;
  background:#fff;
  padding:12px;
}
.device-title{font-weight:800;font-size:15px;line-height:1.2}
.device-subtitle{margin-top:6px;color:var(--muted);font-size:13px;line-height:1.3}
.device-banner{
  border:1px solid var(--line);
  border-radius:18px;
  padding:12px;
  background:#fff;
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
}
.device-banner.good{background:#ecf7f3}
.device-banner.warn{background:#fff5df}
.device-banner.danger{background:#feebe4}
.device-dot{opacity:.6}
.device-pill-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.device-compare{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.device-card h6{margin:0 0 8px;font-size:13px}
.device-list{margin:0;padding-left:18px;color:var(--muted)}
.device-section h5{
  margin:0 0 8px;
  font-size:12px;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--muted);
}
.device-card{
  border:1px solid var(--line);
  border-radius:18px;
  background:#fff;
  padding:12px;
  display:grid;
  gap:8px;
}
.device-pre{
  margin:0;
  white-space:pre-wrap;
  line-height:1.35;
  font-family:"IBM Plex Mono","Cascadia Code",monospace;
  font-size:12px;
  color:#2b3a3f;
}
.device-row{
  display:flex;
  justify-content:space-between;
  gap:10px;
  padding-bottom:8px;
  border-bottom:1px dashed var(--line);
}
.device-row:last-child{border-bottom:0;padding-bottom:0}
.device-bottom{
  padding:14px 16px 18px;
  background:#fff;
  display:flex;
  gap:10px;
  border-top:1px solid var(--line);
}
.device-cta{
  flex:1;
  border:0;
  border-radius:999px;
  padding:11px 14px;
  font:inherit;
  opacity:.9;
}
.device-cta[data-tone="primary"]{background:var(--primary);color:var(--primary-ink)}
.device-cta[data-tone="danger"]{background:var(--danger);color:var(--danger-ink)}
.device-cta[data-tone="secondary"]{background:var(--secondary);color:var(--secondary-ink)}
.device-cta[data-tone="ghost"]{background:var(--ghost);color:var(--ink)}
.task-grid{display:grid;grid-template-columns:260px 1fr;gap:16px}
.task-list{display:grid;gap:12px}
.task-list article.active{border-color:var(--primary);box-shadow:inset 0 0 0 1px rgba(31,106,91,.18)}
.progress-track{height:10px;border-radius:999px;background:#e6dfd1;overflow:hidden}
.progress-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#1f6a5b 0%,#68a896 100%)}
.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.provider-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.provider-card.active{border-color:var(--primary);background:#eef7f3}
.kv-list{display:grid;gap:12px}
.kv-row{
  display:flex;
  justify-content:space-between;
  gap:12px;
  align-items:flex-start;
  padding-bottom:10px;
  border-bottom:1px dashed var(--line);
}
.kv-row:last-child{border-bottom:0;padding-bottom:0}
.kv-row code{font-family:"IBM Plex Mono","Cascadia Code",monospace}
.list-tight,pre{margin:0}
pre{
  white-space:pre-wrap;
  line-height:1.35;
  color:#2b3a3f;
  background:#f8f5ee;
  border:1px solid var(--line);
  border-radius:18px;
  padding:16px;
}
.actions-card{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.actions-meta{display:grid;gap:6px}
.actions-meta strong{font-size:15px}
.wireframe-card{grid-column:1 / -1}
.source-list li{word-break:break-word}
.empty{color:var(--muted)}
@media (max-width:1100px){
  .app{grid-template-columns:1fr}
  .preview-grid,.detail-grid,.task-grid,.provider-grid{grid-template-columns:1fr}
}
@media (max-width:720px){
  .canvas{padding:18px}
  .hero h2{font-size:26px}
  .field-grid,.metric-grid{grid-template-columns:1fr}
  .device-compare{grid-template-columns:1fr}
}"""


def _render_app_js() -> str:
    return """async function boot() {
  const response = await fetch('mock-data.json');
  const data = await response.json();
  let pageIndex = 0;
  let stateIndex = 0;

  const els = {
    featTitle: document.getElementById('feat-title'),
    featRef: document.getElementById('feat-ref'),
    journeyNav: document.getElementById('journey-nav'),
    statePills: document.getElementById('state-pills'),
    sourceRefs: document.getElementById('source-refs'),
    pageTitle: document.getElementById('page-title'),
    pageGoal: document.getElementById('page-goal'),
    heroMeta: document.getElementById('hero-meta'),
    stateCaption: document.getElementById('state-caption'),
    previewSurface: document.getElementById('preview-surface'),
    stateSummary: document.getElementById('state-summary'),
    completionSummary: document.getElementById('completion-summary'),
    mainPath: document.getElementById('main-path'),
    branchPaths: document.getElementById('branch-paths'),
    fieldBoundary: document.getElementById('field-boundary'),
    technicalBoundary: document.getElementById('technical-boundary'),
    wireframe: document.getElementById('wireframe'),
    actions: document.getElementById('actions'),
    actionHint: document.getElementById('action-hint'),
  };

  const stateGroups = {
    primary: ['success', 'saved', 'connected', 'consistent', 'visible', 'ready', 'offered'],
    error: ['error', 'failed', 'blocked', 'retryable', 'degraded', 'validation', 'conflict', 'illegal'],
    skip: ['skip', 'skipped', 'partial', 'conservative', 'recovery', 'provider_selected'],
  };

  function currentPage() { return data.pages[pageIndex]; }
  function currentState(page) { return page.states[stateIndex] || page.states[0] || { name: 'initial', ui_behavior: 'No state available', user_options: '' }; }
  function labelize(text) { return String(text || '').replace(/_/g, ' ').replace(/\\b\\w/g, (match) => match.toUpperCase()); }
  function renderList(items, emptyText) { return !items || !items.length ? `<p class="empty">${emptyText}</p>` : `<ul class="list-tight">${items.map((item) => `<li>${item}</li>`).join('')}</ul>`; }
  function renderFieldTag(field) { return `<div class="mini-card"><strong>${field.label || labelize(field.field)}</strong><p class="muted">${field.type} · ${field.source || 'ui'}</p></div>`; }
  function previewTone(page, state) {
    const name = String(state.name || '').toLowerCase();
    if (name.includes('error') || name.includes('failed') || name.includes('blocked') || name.includes('retryable') || name.includes('illegal')) return 'danger';
    if (name.includes('conservative') || name.includes('skip') || name.includes('partial') || name.includes('recover')) return 'warn';
    if (page.page_type_family === 'panel' && name.includes('evaluating')) return 'warn';
    return 'good';
  }
  function valueFromField(field, stateName = '') {
    const key = String(field.field || '').toLowerCase();
    if (key.includes('percent')) return '40%';
    if (key.includes('advice_level')) return '可执行保守建议';
    if (key.includes('first_week_action')) return '周二轻松跑 20 分钟 + 周末快走';
    if (key.includes('needs_more_info')) return '补充 injury 与训练基础可释放更稳定建议';
    if (key.includes('device_connect')) return '连接设备可增强后续建议精度';
    if (key.includes('connection_status')) return stateName.includes('connected') ? 'device_connected' : stateName.includes('failed') ? 'connect_failed' : 'not_connected';
    if (key.includes('conflict_blocked')) return stateName.includes('conflict') || stateName.includes('illegal') ? 'true' : 'false';
    if (key.includes('status')) return 'non-blocking';
    if (key.includes('primary_state')) return 'profile_minimal_done';
    if (key.includes('capability_flags')) return 'device_connected=false, initial_plan_ready=false';
    if (key.includes('blocking_reason')) return 'runner_profiles.birthdate 与 user_physical_profile.birthdate 冲突';
    if (key.includes('recovery_hint')) return '以 user_physical_profile 为 canonical source 重写后重读';
    if (key.includes('canonical_profile_boundary')) return 'user_physical_profile 是唯一身体事实源';
    if (key.includes('resolved_profile_refs')) return 'users/basic, user_physical_profile/canonical';
    if (key.includes('task_cards')) return '基础习惯、周跑量、恢复备注';
    if (key.includes('next_task_cards')) return '睡眠习惯、训练天数';
    if (key.includes('experience_enhancement_ready')) return '后续建议可增强';
    if (key.includes('homepage_access_preserved')) return 'true';
    if (key.includes('first_advice_access_preserved')) return 'true';
    return field.note || labelize(field.field);
  }
  function renderFieldInput(field, state, idx) {
    const stateName = String(state.name || '').toLowerCase();
    const hasError = stateName.includes('validation') || stateName.includes('error');
    const fieldClass = hasError && idx < 2 ? 'field-card has-error' : 'field-card';
    const options = field.options && field.options.length ? `<div class="info-chip-row">${field.options.slice(0, 4).map((item) => `<span class="chip">${item}</span>`).join('')}</div>` : '';
    const control = field.type === 'text' ? `<textarea class="field-textarea" aria-label="${field.label}" placeholder="${field.note || field.label}">${field.note || ''}</textarea>` : `<input class="field-input" aria-label="${field.label}" placeholder="${field.note || field.label}" value="" />`;
    return `<article class="${fieldClass}"><header><strong>${field.label}</strong><span class="pill">${field.required ? 'Required' : 'Optional'}</span></header><small>${field.note || field.type}</small>${options}${field.options && field.options.length ? `<div class="field-select">${field.options[0]}</div>` : control}</article>`;
  }
  function renderFormSurface(page, state) {
    const tone = previewTone(page, state);
    const fields = (page.editable_ui_fields || page.input_fields || []).map((field, idx) => renderFieldInput(field, state, idx)).join('');
    const errorSummary = String(state.name).toLowerCase().includes('error') || String(state.name).toLowerCase().includes('validation') ? `<div class="banner danger"><strong>字段校验阻断</strong><p>${page.validation_feedback}</p></div>` : '';
    const successBanner = String(state.name).toLowerCase().includes('success') ? `<div class="banner good"><strong>建档完成，首页已放行</strong><p>${page.success_feedback}</p></div>` : '';
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.entry_condition}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner ${tone}"><strong>One-screen onboarding</strong><p>${page.completion_definition}</p></div>${errorSummary}${successBanner}<div class="field-grid">${fields}</div><div class="surface-footer"><div class="info-chip-row">${(page.required_fields || []).map((item) => `<span class="chip">${item}</span>`).join('')}</div></div></section>`;
  }
  function renderPanelSurface(page, state) {
    const tone = previewTone(page, state);
    const stateName = String(state.name || '').toLowerCase();
    const visibleKeys = stateName.includes('degraded')
      ? ['needs_more_info_prompt', 'device_connect_prompt', 'advice_mode']
      : stateName.includes('conservative')
        ? ['needs_more_info_prompt', 'device_connect_prompt', 'advice_mode']
        : stateName.includes('loading') || stateName.includes('evaluating')
          ? ['advice_mode']
          : ['training_advice_level', 'first_week_action', 'needs_more_info_prompt', 'device_connect_prompt'];
    const fields = (page.display_fields || [])
      .filter((field) => visibleKeys.includes(field.field))
      .map((field) => `<article class="metric-card"><strong>${field.label}</strong><p class="muted">${valueFromField(field, stateName)}</p></article>`)
      .join('');
    const guidance = tone === 'good' ? page.success_feedback : tone === 'warn' ? (page.validation_feedback || page.error_feedback) : page.error_feedback;
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.page_goal}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner ${tone}"><strong>${tone === 'good' ? '正常建议可见' : tone === 'warn' ? '保守提示 / 补充路径' : '建议生成异常'}</strong><p>${guidance}</p></div><div class="metric-grid">${fields}</div></section>`;
  }
  function renderCardListSurface(page, state) {
    const tone = previewTone(page, state);
    const tasks = ['基础习惯', '周跑量', '恢复备注', '训练频次'];
    const activeField = (page.editable_ui_fields || [])[0];
    const activeControl = activeField ? `<label class="field-card"><header><strong>${activeField.label}</strong><span class="pill">${activeField.required ? 'Required' : 'Optional'}</span></header><small>${activeField.note || activeField.type}</small><textarea class="field-textarea" placeholder="${activeField.note || activeField.label}"></textarea></label>` : '<p class="empty">No editable task-card field available.</p>';
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.page_goal}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner good"><strong>Profile completion 40%</strong><p>${page.success_feedback}</p><div class="progress-track"><div class="progress-fill" style="width:40%"></div></div></div><div class="task-grid"><aside class="task-list">${tasks.map((task, idx) => `<article class="${idx === 0 ? 'active' : ''}"><strong>${task}</strong><small>${idx === 0 ? '当前任务卡' : '待补全'}</small></article>`).join('')}</aside><div class="task-stage">${activeControl}</div></div></section>`;
  }
  function renderEntrySurface(page, state) {
    const tone = previewTone(page, state);
    const stateName = String(state.name || '').toLowerCase();
    const providers = ['Garmin', 'Apple Watch', 'Coros'];
    const showProviders = !(stateName.includes('skipped') || stateName.includes('failed') || stateName.includes('connected'));
    const metrics = (page.display_fields || [])
      .filter((field) => stateName.includes('connected') ? field.field !== 'connection_status' || true : !field.field.includes('experience_enhancement_ready') || stateName.includes('connected'))
      .map((field) => `<article class="metric-card"><strong>${field.label}</strong><p class="muted">${valueFromField(field, stateName)}</p></article>`)
      .join('');
    const summary = stateName.includes('skipped')
      ? '用户已跳过设备连接，首页和首轮建议继续可用。'
      : stateName.includes('connected')
        ? '设备已连接，后续增强体验已解锁。'
        : stateName.includes('failed')
          ? '连接失败被视为非阻塞事件，允许用户稍后重试。'
          : '连接设备只会增强体验，不会回退主链完成态。';
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.page_goal}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner ${tone === 'danger' ? 'danger' : 'good'}"><strong>设备连接是后置增强，不阻塞首页</strong><p>${summary}</p></div>${showProviders ? `<div class="provider-grid">${providers.map((name, idx) => `<article class="provider-card ${idx === 0 ? 'active' : ''}"><header><strong>${name}</strong><span class="pill">${idx === 0 ? 'selected' : 'available'}</span></header><small>连接后提升后续建议精度，不改变首页放行状态。</small></article>`).join('')}</div>` : ''}<div class="metric-grid">${metrics}</div></section>`;
  }
  function renderStatusSurface(page, state) {
    const tone = previewTone(page, state);
    const stateName = String(state.name || '').toLowerCase();
    const rows = (page.ui_visible_fields || [])
      .filter((field) => {
        if (stateName.includes('conflict') || stateName.includes('illegal')) {
          return ['blocking_reason', 'recovery_hint', 'canonical_profile_boundary'].includes(field.field);
        }
        return !['blocking_reason', 'recovery_hint'].includes(field.field);
      })
      .map((field) => `<div class="kv-row"><strong>${field.label}</strong><code>${valueFromField(field, stateName)}</code></div>`)
      .join('');
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.page_goal}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner ${tone}"><strong>${tone === 'danger' ? 'Conflict blocked' : 'Unified state available'}</strong><p>${tone === 'danger' ? page.error_feedback : page.success_feedback}</p></div><div class="kv-list">${rows}</div></section>`;
  }
  function renderGenericSurface(page, state) {
    const tone = previewTone(page, state);
    return `<section class="surface"><div class="surface-header"><div><h4>${page.title}</h4><p>${page.page_goal}</p></div><span class="tone-pill ${tone}">${labelize(state.name)}</span></div><div class="banner ${tone}"><strong>Preview</strong><p>${state.ui_behavior}</p></div>${renderList(page.main_path, 'No path defined.')}</section>`;
  }
  function renderUiSpecSurface(page, state) {
    const tone = previewTone(page, state);
    const wireframe = String(page.ascii_wireframe || '').trim();

    function escapeHtml(text) {
      return String(text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function wireframeButtons(text) {
      const matches = String(text || '').match(/\\[[^\\]]+\\]/g) || [];
      const normalized = matches.map((item) => item.replace(/^\\[|\\]$/g, '').trim()).filter(Boolean);
      return Array.from(new Set(normalized));
    }

    function wireframeBlocks(text) {
      const lines = String(text || '').split('\\n');
      const blocks = [];
      let current = [];
      for (const line of lines) {
        if (line.trim().startsWith('+')) {
          if (current.length) { blocks.push(current); current = []; }
          continue;
        }
        if (!line.includes('|')) continue;
        const inner = line.replace(/^\\|\\s?/, '').replace(/\\s?\\|\\s*$/, '').replace(/\\s+$/g, '');
        if (inner.trim()) current.push(inner);
      }
      if (current.length) blocks.push(current);
      return blocks.slice(0, 10);
    }

    function renderWireframeCards(text) {
      if (!text) return '<div class="device-card"><p class="muted">No ASCII wireframe provided.</p></div>';
      const blocks = wireframeBlocks(text);
      if (!blocks.length) return `<div class="device-card"><pre class="device-pre">${escapeHtml(text)}</pre></div>`;
      return blocks.map((block) => `<div class="device-card"><pre class="device-pre">${escapeHtml(block.join('\\n'))}</pre></div>`).join('');
    }

    const wireframeCtas = wireframeButtons(wireframe);
    const fallbackCtas = (page.buttons || []).filter((button) => button.action !== 'reset').slice(0, 2).map((button) => button.label);
    const ctas = (wireframeCtas.length ? wireframeCtas : fallbackCtas).slice(0, 2);
    const actionButtons = ctas.map((label, idx) => {
      const btnTone = idx === 0 ? 'primary' : 'ghost';
      return `<button class="device-cta" type="button" disabled data-tone="${btnTone}">${label}</button>`;
    }).join('');

    const header = `<div class="device-header"><div class="device-title">${page.title}</div><div class="device-subtitle">${page.page_goal || ''}</div></div>`;
    const meta = `<div class="device-banner ${tone}"><strong>${labelize(state.name)}</strong><span class="device-dot">·</span><span class="muted">${page.page_type || page.page_type_family}</span></div>`;
    const cards = renderWireframeCards(wireframe);

    return `<section class="device"><div class="device-frame"><div class="device-status"><span class="pill">${page.fidelity_class || 'ui'}</span><span class="pill">${tone}</span></div><div class="device-body">${header}${meta}${cards}</div><div class="device-bottom">${actionButtons}</div></div></section>`;
  }
  function renderSurface(page, state) {
    if (page.fidelity_class === 'ui_spec_backed') return renderUiSpecSurface(page, state);
    switch (page.page_type_family) {
      case 'form': return renderFormSurface(page, state);
      case 'panel': return renderPanelSurface(page, state);
      case 'card_list': return renderCardListSurface(page, state);
      case 'entry': return renderEntrySurface(page, state);
      case 'status': return renderStatusSurface(page, state);
      default: return renderGenericSurface(page, state);
    }
  }
  function findStateIndex(page, tokens) {
    const states = page.states || [];
    for (const token of tokens) {
      const idx = states.findIndex((state) => String(state.name || '').toLowerCase().includes(token));
      if (idx >= 0) return idx;
    }
    return -1;
  }
  function targetStateIndex(page, action) {
    if (action === 'reset') return 0;
    const tokens = stateGroups[action] || [];
    const idx = findStateIndex(page, tokens);
    if (idx >= 0) return idx;
    if (action === 'primary') return Math.min((page.states || []).length - 1, 1);
    if (action === 'error') return Math.min((page.states || []).length - 1, 2);
    if (action === 'skip') return Math.min((page.states || []).length - 1, 3);
    return 0;
  }
  function render() {
    const page = currentPage();
    const state = currentState(page);
    document.title = `${data.feat_title} Prototype`;
    els.featTitle.textContent = data.feat_title;
    els.featRef.textContent = data.feat_ref;
    els.journeyNav.innerHTML = data.pages.map((item, idx) => `<li class="${idx === pageIndex ? 'active' : ''}"><a href="#" data-page="${idx}">${item.title}</a></li>`).join('');
    els.statePills.innerHTML = (page.states || []).map((item, idx) => `<button type="button" class="${idx === stateIndex ? 'active' : ''}" data-state="${idx}">${labelize(item.name)}</button>`).join('');
    els.sourceRefs.innerHTML = (data.source_refs || []).map((item) => `<li>${item}</li>`).join('');
    els.pageTitle.textContent = page.title;
    els.pageGoal.textContent = page.page_goal;
    els.heroMeta.innerHTML = `<span class="chip">${page.page_type_family}</span><span class="chip">${page.platform}</span><span class="chip">${page.fidelity_class || 'unknown'}</span><span class="chip">${page.ui_spec_id || 'feat-derived'}</span>`;
    els.stateCaption.textContent = `${labelize(state.name)} · ${state.trigger || ''}`;
    els.previewSurface.innerHTML = renderSurface(page, state);
    els.stateSummary.innerHTML = `<p><strong>${labelize(state.name)}</strong></p><p class="muted">${state.ui_behavior || ''}</p><p class="muted">${state.user_options || ''}</p>`;
    els.completionSummary.innerHTML = `<p><strong>Entry</strong></p><p class="muted">${page.entry_condition}</p><p><strong>Completion</strong></p><p class="muted">${page.completion_definition}</p><p><strong>Exit</strong></p><p class="muted">${page.exit_condition}</p>`;
    els.mainPath.innerHTML = (page.main_path || []).map((step) => `<li>${step}</li>`).join('');
    els.branchPaths.innerHTML = (page.branch_paths || []).map((branch) => `<article class="mini-card"><strong>${branch.title}</strong>${renderList(branch.steps || [], 'No branch steps.')}</article>`).join('');
    els.fieldBoundary.innerHTML = `<p><strong>Required user-visible fields</strong></p>${renderList(page.required_ui_fields || [], 'No explicit required UI fields.')}<p><strong>UI-visible</strong></p><div class="info-chip-row">${(page.ui_visible_fields || []).map(renderFieldTag).join('') || '<p class="empty">No UI-visible fields.</p>'}</div><p><strong>Technical payload</strong></p><div class="info-chip-row">${(page.technical_payload_fields || []).map(renderFieldTag).join('') || '<p class="empty">No technical payload fields.</p>'}</div>`;
    els.technicalBoundary.innerHTML = `<p><strong>Validation rules</strong></p>${renderList(page.frontend_validation_rules || [], 'No validation rules.')}<p><strong>Data dependencies</strong></p>${renderList(page.data_dependencies || [], 'No dependencies listed.')}<p><strong>API touchpoints</strong></p>${renderList(page.api_touchpoints || [], 'No API touchpoints listed.')}<p><strong>Feedback</strong></p>${renderList([page.loading_feedback, page.validation_feedback, page.success_feedback, page.error_feedback, page.retry_behavior].filter(Boolean), 'No feedback guidance.')}`;
    els.wireframe.textContent = page.ascii_wireframe || 'No ASCII wireframe available.';
    els.actionHint.innerHTML = `<strong>${(page.action_priority || [page.title])[0] || page.title}</strong><span class="muted">${page.success_feedback || page.retry_behavior || page.validation_feedback || ''}</span>`;
    els.actions.innerHTML = (page.buttons || []).map((button) => `<button type="button" data-action="${button.action}" data-tone="${button.tone || 'primary'}">${button.label}</button>`).join('');
  }
  document.addEventListener('click', (event) => {
    const pageRef = event.target.getAttribute('data-page');
    if (pageRef !== null) { event.preventDefault(); pageIndex = Number(pageRef); stateIndex = 0; render(); return; }
    const stateRef = event.target.getAttribute('data-state');
    if (stateRef !== null) { stateIndex = Number(stateRef); render(); return; }
    const action = event.target.getAttribute('data-action');
    if (!action) return;
    if (action === 'page_next' && pageIndex < data.pages.length - 1) { pageIndex += 1; stateIndex = 0; render(); return; }
    if (action === 'page_back' && pageIndex > 0) { pageIndex -= 1; stateIndex = 0; render(); return; }
    stateIndex = targetStateIndex(currentPage(), action);
    render();
  });
  render();
}
boot();"""


def _review_guide(bundle: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Prototype Review Guide",
            "",
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


def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    feat_ref = context["feat_ref"]
    feature = context["feature"]
    output_dir = repo_root / "artifacts" / "feat-to-proto" / f"{slugify(run_id or feat_ref)}--{slugify(feat_ref)}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"]}
    output_dir.mkdir(parents=True, exist_ok=True)
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
        "prototype_source": "ui_spec_package" if ui_spec_context else "feat_freeze_package",
        "ui_spec_package_ref": rel(ui_spec_context["path"], repo_root) if ui_spec_context else "",
        "pages": pages,
        "source_refs": (ui_spec_context["bundle"].get("source_refs") if ui_spec_context else None) or feature.get("source_refs") or context["bundle"].get("source_refs") or [],
    }
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
        "checks": {"human_review_approved": False, "review_coverage_complete": True, "no_blocking_points": False},
    }
    write_json(output_dir / "package-manifest.json", {"artifact_type": "prototype_package", "workflow_key": "dev.feat-to-proto", "run_id": run_id or feat_ref, "feat_ref": feat_ref})
    write_json(output_dir / "prototype-bundle.json", bundle)
    write_text(
        output_dir / "prototype-bundle.md",
        "\n".join(
            [
                f"# Prototype Bundle for {feat_ref}",
                "",
                f"- feat_title: {bundle['feat_title']}",
                f"- page_count: {len(pages)}",
                f"- prototype_source: {bundle['prototype_source']}",
                *[f"- page: {page['title']} | family={page['page_type_family']} | states={len(page['states'])}" for page in pages],
            ]
        ),
    )
    write_text(output_dir / "prototype-flow-map.md", "\n".join(["# Prototype Flow Map", "", *[f"{index+1}. {page['title']}" for index, page in enumerate(pages)]]))
    write_text(output_dir / "prototype-review-guide.md", _review_guide(bundle))
    write_json(output_dir / "prototype-completeness-report.json", completeness)
    write_json(output_dir / "prototype-review-report.json", review)
    write_json(output_dir / "prototype-defect-list.json", defects)
    write_json(output_dir / "prototype-freeze-gate.json", freeze_gate)
    write_json(output_dir / "execution-evidence.json", {"workflow_key": "dev.feat-to-proto", "run_id": run_id or feat_ref, "generated_at": utc_now(), "artifacts_dir": str(output_dir)})
    write_json(output_dir / "supervision-evidence.json", {"workflow_key": "dev.feat-to-proto", "run_id": run_id or feat_ref, "review_completed_at": utc_now(), "decision": "review_required"})
    write_text(output_dir / "prototype" / "index.html", _render_index_html(bundle["feat_title"]))
    write_text(output_dir / "prototype" / "styles.css", _render_styles())
    write_text(output_dir / "prototype" / "app.js", _render_app_js())
    write_json(output_dir / "prototype" / "mock-data.json", {"feat_ref": feat_ref, "feat_title": bundle["feat_title"], "source_refs": bundle["source_refs"], "pages": pages})
    return {"ok": True, "artifacts_dir": str(output_dir), "freeze_ready": False}


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    review = load_json(artifacts_dir / "prototype-review-report.json")
    errors.extend(validate_prototype_review(review))
    return errors, {
        "review": review,
        "freeze_gate": load_json(artifacts_dir / "prototype-freeze-gate.json"),
        "bundle": load_json(artifacts_dir / "prototype-bundle.json"),
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
    gate["checks"] = {
        "human_review_approved": ok,
        "review_coverage_complete": not errors,
        "no_blocking_points": ok,
    }
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

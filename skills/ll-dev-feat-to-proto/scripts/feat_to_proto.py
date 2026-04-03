#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.feat_input_resolver import resolve_feat_input_artifacts_dir
from cli.lib.prototype_review_contract import build_prototype_review, validate_prototype_review
from feat_to_ui_spec import build_units, d_list, first, slugify

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


def _page_model(unit: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    buttons = []
    if index > 0:
        buttons.append({"label": "Back", "action": "back"})
    if index < total - 1:
        buttons.append({"label": "Continue", "action": "next"})
    else:
        buttons.append({"label": "Finish", "action": "finish"})
    buttons.extend(
        [
            {"label": "Retry", "action": "error"},
            {"label": "Skip", "action": "skip"},
            {"label": "Reset", "action": "reset"},
        ]
    )
    return {
        "page_id": unit["slug"],
        "title": unit["page_name"],
        "page_goal": unit["page_goal"],
        "main_path": unit["main_user_path"],
        "branch_paths": unit["branch_paths"],
        "states": unit["states"],
        "buttons": buttons,
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
      <h1>Prototype Journey</h1>
      <ol id="journey-nav"></ol>
    </aside>
    <section class="canvas">
      <header class="hero">
        <p class="eyebrow">Static HTML prototype</p>
        <h2 id="page-title"></h2>
        <p id="page-goal"></p>
      </header>
      <section class="card">
        <h3>State</h3>
        <p id="state-name"></p>
        <p id="state-description"></p>
      </section>
      <section class="card">
        <h3>Main Journey</h3>
        <ol id="main-path"></ol>
      </section>
      <section class="card">
        <h3>Failure / Alternate Paths</h3>
        <div id="branch-paths"></div>
      </section>
      <footer class="actions" id="actions"></footer>
    </section>
  </main>
  <script src="app.js"></script>
</body>
</html>"""


def _render_styles() -> str:
    return """body{margin:0;font-family:Arial,sans-serif;background:#f3f5f7;color:#16202a}
.app{display:grid;grid-template-columns:280px 1fr;min-height:100vh}
.sidebar{background:#0f1720;color:#f8fafc;padding:24px}
.canvas{padding:32px;display:grid;gap:16px}
.hero{background:linear-gradient(135deg,#fff 0%,#e8f0ff 100%);padding:24px;border-radius:16px}
.eyebrow{text-transform:uppercase;font-size:12px;letter-spacing:.12em;color:#5b6b7f}
.card{background:#fff;padding:20px;border-radius:16px;box-shadow:0 8px 24px rgba(15,23,32,.08)}
.actions{display:flex;flex-wrap:wrap;gap:12px}
button{border:0;border-radius:999px;padding:12px 18px;background:#1d4ed8;color:#fff;cursor:pointer}
button.secondary{background:#475569}
li.active a{font-weight:700}
a{color:inherit;text-decoration:none}
@media (max-width:900px){.app{grid-template-columns:1fr}.sidebar{padding-bottom:8px}}"""


def _render_app_js() -> str:
    return """async function boot(){const response=await fetch('mock-data.json');const data=await response.json();let pageIndex=0;let stateIndex=0;
const nav=document.getElementById('journey-nav');const title=document.getElementById('page-title');const goal=document.getElementById('page-goal');
const stateName=document.getElementById('state-name');const stateDescription=document.getElementById('state-description');const mainPath=document.getElementById('main-path');
const branchPaths=document.getElementById('branch-paths');const actions=document.getElementById('actions');
function render(){const page=data.pages[pageIndex];const state=page.states[stateIndex]||page.states[0];
nav.innerHTML=data.pages.map((item,idx)=>`<li class=\"${idx===pageIndex?'active':''}\"><a href=\"#\" data-page=\"${idx}\">${item.title}</a></li>`).join('');
title.textContent=page.title;goal.textContent=page.page_goal;stateName.textContent=state.name;stateDescription.textContent=state.ui_behavior;
mainPath.innerHTML=page.main_path.map(step=>`<li>${step}</li>`).join('');
branchPaths.innerHTML=page.branch_paths.map(branch=>`<article><h4>${branch.title}</h4><ol>${branch.steps.map(step=>`<li>${step}</li>`).join('')}</ol></article>`).join('');
actions.innerHTML=page.buttons.map(button=>`<button class=\"${button.action==='error'||button.action==='skip'?'secondary':''}\" data-action=\"${button.action}\">${button.label}</button>`).join('');}
document.addEventListener('click',event=>{const pageRef=event.target.getAttribute('data-page');if(pageRef!==null){event.preventDefault();pageIndex=Number(pageRef);stateIndex=0;render();return;}
const action=event.target.getAttribute('data-action');if(!action)return;
if(action==='next'&&pageIndex<data.pages.length-1){pageIndex+=1;stateIndex=0;}
else if(action==='back'&&pageIndex>0){pageIndex-=1;stateIndex=0;}
else if(action==='error'){stateIndex=Math.min(3,data.pages[pageIndex].states.length-1);}
else if(action==='skip'){stateIndex=Math.min(4,data.pages[pageIndex].states.length-1);}
else if(action==='finish'){stateIndex=data.pages[pageIndex].states.length-1;}
else if(action==='reset'){stateIndex=0;}
render();});
render();}
boot();"""


def _review_guide(bundle: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Prototype Review Guide",
            "",
            "1. Open `prototype/index.html` in a browser.",
            "2. Click through every page in the left journey navigation.",
            "3. Use `Continue`, `Back`, `Retry`, `Skip`, and `Reset` on each screen.",
            "4. Verify happy path plus error / skip flow feel coherent.",
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
    units = build_units(feature, feat_ref)
    pages = [_page_model(unit, index, len(units)) for index, unit in enumerate(units)]
    bundle = {
        "artifact_type": "prototype_package",
        "workflow_key": "dev.feat-to-proto",
        "feat_ref": feat_ref,
        "feat_title": first(feature.get("title"), feat_ref),
        "prototype_entry_ref": "prototype/index.html",
        "pages": pages,
        "source_refs": feature.get("source_refs") or context["bundle"].get("source_refs") or [],
    }
    defects = [{"page_id": page["page_id"], "type": "human_review_pending"} for page in pages]
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
            "feat_alignment_check": {"passed": False, "issues": ["human review pending"]},
        },
        blocking_points=[{"id": "human-review-required", "description": "Prototype must be reviewed by a human."}],
    )
    completeness = {
        "gate_name": "Prototype Experience Completeness Check",
        "decision": "pass" if pages else "fail",
        "pages": [{"page_id": page["page_id"], "button_count": len(page["buttons"]), "state_count": len(page["states"])} for page in pages],
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
    write_text(output_dir / "prototype-bundle.md", f"# Prototype Bundle for {feat_ref}\n\n- feat_title: {bundle['feat_title']}\n- page_count: {len(pages)}")
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
    write_json(output_dir / "prototype" / "mock-data.json", {"feat_ref": feat_ref, "pages": pages})
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

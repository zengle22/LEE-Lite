from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def slugify(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-") or "surface-map"


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def resolve_repo_root(repo_root: str | Path | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path.cwd().resolve()


def resolve_input_dir(input_value: str | Path, repo_root: Path) -> Path:
    candidate = Path(input_value)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    resolved = (repo_root / candidate).resolve()
    return resolved


def select_feature(bundle: dict[str, Any], feat_ref: str) -> dict[str, Any] | None:
    for feature in ensure_list(bundle.get("features")):
        if isinstance(feature, dict) and str(feature.get("feat_ref") or "").strip() == feat_ref:
            return dict(feature)
    return None


def normalize_scope(values: Any) -> list[str]:
    return [str(item).strip() for item in ensure_list(values) if str(item).strip()]


def normalize_surface_entries(raw_surface_map: Any) -> dict[str, list[dict[str, Any]]]:
    normalized = {key: [] for key in ("architecture", "api", "ui", "prototype", "tech")}
    if not isinstance(raw_surface_map, dict):
        return normalized
    for surface_name in normalized:
        raw_value = raw_surface_map.get(surface_name)
        entries = raw_value if isinstance(raw_value, list) else ensure_list(raw_value)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            normalized[surface_name].append(
                {
                    "owner": str(entry.get("owner") or "").strip(),
                    "action": str(entry.get("action") or "").strip(),
                    "scope": normalize_scope(entry.get("scope")),
                    "reason": str(entry.get("reason") or "").strip(),
                    "source_ref": str(entry.get("source_ref") or "").strip() or None,
                }
            )
    return normalized


def build_fallback_surface_map(feature: dict[str, Any], feat_ref: str, design_impact_required: bool) -> dict[str, list[dict[str, Any]]]:
    normalized = {key: [] for key in ("architecture", "api", "ui", "prototype", "tech")}
    base_scope = normalize_scope(feature.get("scope")) or normalize_scope(feature.get("acceptance_checks"))
    default_scope = base_scope or [str(feature.get("goal") or feature.get("title") or feat_ref).strip() or feat_ref]
    text = " ".join(
        str(part or "")
        for part in [
            feature.get("title"),
            feature.get("goal"),
            " ".join(normalize_scope(feature.get("scope"))),
            " ".join(normalize_scope(feature.get("constraints"))),
        ]
    ).lower()

    def add(surface: str, owner: str, action: str, reason: str, scope: list[str] | None = None) -> None:
        normalized[surface].append(
            {
                "owner": owner,
                "action": action,
                "scope": scope or default_scope,
                "reason": reason,
                "source_ref": None,
            }
        )

    explicit_refs = {
        "architecture": str(feature.get("arch_ref") or "").strip(),
        "api": str(feature.get("api_ref") or "").strip(),
        "ui": str(feature.get("ui_ref") or "").strip(),
        "prototype": str(feature.get("prototype_ref") or "").strip(),
        "tech": str(feature.get("tech_ref") or "").strip(),
    }
    for surface, ref in explicit_refs.items():
        if ref:
            add(surface, ref, "update", f"existing {surface} owner declared on selected FEAT")

    if not design_impact_required:
        return normalized

    if not normalized["ui"]:
        add("ui", f"UI-{feat_ref}", "create", "no explicit UI owner declared; create a routing placeholder for a user-facing FEAT")
    if not normalized["prototype"]:
        add("prototype", f"PROTO-{feat_ref}", "create", "no explicit prototype owner declared; create a placeholder for the main experience skeleton")
    if not normalized["tech"]:
        add("tech", f"TECH-{feat_ref}", "create", "no explicit technical owner declared; create a placeholder implementation strategy package")
    if not normalized["architecture"] and any(token in text for token in ("boundary", "module", "integration", "state", "workflow", "orchestration")):
        add("architecture", f"ARCH-{feat_ref}", "create", "architecture-impact inferred from FEAT scope and goal")
    if not normalized["api"] and any(token in text for token in ("api", "contract", "endpoint", "request", "response", "interface")):
        add("api", f"API-{feat_ref}", "create", "contract-impact inferred from FEAT scope and goal")
    return normalized


def build_surface_map_model(feature: dict[str, Any], feat_ref: str) -> tuple[bool, dict[str, list[dict[str, Any]]], str | None]:
    if "design_impact_required" in feature:
        design_impact_required = bool(feature.get("design_impact_required"))
    elif "ui_required" in feature:
        design_impact_required = bool(feature.get("ui_required"))
    elif any(feature.get(key) for key in ("design_surfaces", "arch_ref", "api_ref", "ui_ref", "prototype_ref", "tech_ref")):
        design_impact_required = True
    else:
        design_impact_required = True

    bypass_rationale = None
    if not design_impact_required:
        bypass_rationale = str(
            feature.get("surface_map_bypass_rationale")
            or feature.get("design_impact_rationale")
            or "FEAT does not require shared design asset derivation."
        ).strip()

    raw_design_surfaces = feature.get("design_surfaces")
    if isinstance(raw_design_surfaces, dict) and raw_design_surfaces:
        design_surfaces = normalize_surface_entries(raw_design_surfaces)
    else:
        design_surfaces = build_fallback_surface_map(feature, feat_ref, design_impact_required)

    return design_impact_required, design_surfaces, bypass_rationale


def validate_surface_entries(errors: list[str], design_surfaces: dict[str, list[dict[str, Any]]]) -> None:
    for surface_name, entries in design_surfaces.items():
        if not isinstance(entries, list):
            errors.append(f"surface_map.design_surfaces.{surface_name} must be a list.")
            continue
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"surface_map.design_surfaces.{surface_name}[{idx}] must be an object.")
                continue
            owner = str(entry.get("owner") or "").strip()
            action = str(entry.get("action") or "").strip()
            scope = normalize_scope(entry.get("scope"))
            reason = str(entry.get("reason") or "").strip()
            if not owner:
                errors.append(f"surface_map.design_surfaces.{surface_name}[{idx}] missing owner.")
            if action not in {"update", "create"}:
                errors.append(f"surface_map.design_surfaces.{surface_name}[{idx}] action must be update or create.")
            if not scope:
                errors.append(f"surface_map.design_surfaces.{surface_name}[{idx}] missing scope.")
            if not reason:
                errors.append(f"surface_map.design_surfaces.{surface_name}[{idx}] missing reason.")


def summary_lines(design_surfaces: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines: list[str] = []
    for surface_name in ("architecture", "api", "ui", "prototype", "tech"):
        for entry in design_surfaces.get(surface_name, []):
            lines.append(f"{surface_name}: {entry['owner']} ({entry['action']})")
    return lines


def create_justification_lines(design_surfaces: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines: list[str] = []
    for surface_name in ("architecture", "api", "ui", "prototype", "tech"):
        for entry in design_surfaces.get(surface_name, []):
            if str(entry.get("action") or "") == "create":
                lines.append(f"{surface_name}: {entry['owner']} -> {entry['reason']}")
    return lines


def stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def formal_surface_map_paths(repo_root: Path, bundle: dict[str, Any]) -> tuple[Path, Path]:
    mapping_dir = repo_root / "ssot" / "mapping"
    surface_map_ref = str(bundle.get("surface_map_ref") or "").strip() or "SURFACE-MAP"
    title = str((bundle.get("selected_feat") or {}).get("title") or bundle.get("feat_ref") or "surface-map").strip()
    base_name = f"{surface_map_ref}__{slugify(title)}-surface-map-package"
    return mapping_dir / f"{base_name}.md", mapping_dir / f"{base_name}.json"


def build_review_report(run_id: str, feat_ref: str, errors: list[str]) -> dict[str, Any]:
    return {
        "workflow_key": "dev.feat-to-surface-map",
        "run_id": run_id,
        "reviewed_at": utc_now(),
        "reviewer_identity": "system.surface-map-reviewer",
        "verdict": "approved" if not errors else "revise",
        "blocking_points": errors,
        "summary": "Surface map package is acceptable for freeze." if not errors else "Surface map package needs revision before freeze.",
        "coverage_declaration": {
            "selected_feat_ref": feat_ref,
            "issues_found": len(errors),
        },
    }


def build_freeze_gate(review_report: dict[str, Any], validation_errors: list[str]) -> dict[str, Any]:
    freeze_ready = not validation_errors and review_report.get("verdict") == "approved"
    return {
        "workflow_key": "dev.feat-to-surface-map",
        "freeze_ready": freeze_ready,
        "checked_at": utc_now(),
        "checks": {
            "validation_passed": not validation_errors,
            "review_approved": review_report.get("verdict") == "approved",
            "design_surface_consistency": not validation_errors,
        },
        "blocking_reasons": validation_errors if validation_errors else [],
    }


def build_package_payload(context: dict[str, Any], run_id: str) -> dict[str, Any]:
    bundle = context["bundle"]
    feature = context["feature"]
    feat_ref = str(context.get("feat_ref") or context.get("selected_feat_ref") or "").strip()
    design_impact_required, design_surfaces, bypass_rationale = build_surface_map_model(feature, feat_ref)
    ownership_summary = summary_lines(design_surfaces)
    create_justification_summary = create_justification_lines(design_surfaces)
    owner_binding_status = "bypassed" if not design_impact_required else ("proposed" if create_justification_summary else "bound")
    source_refs = [str(ref).strip() for ref in bundle.get("source_refs") or [] if str(ref).strip()]
    for ref in ensure_list(feature.get("source_refs")):
        ref = str(ref).strip()
        if ref and ref not in source_refs:
            source_refs.append(ref)
    surface_map_ref = f"SURFACE-MAP-{feat_ref}"
    selected_feat = {
        "feat_ref": feat_ref,
        "title": str(feature.get("title") or "").strip(),
        "goal": str(feature.get("goal") or "").strip(),
        "scope": normalize_scope(feature.get("scope")),
        "constraints": normalize_scope(feature.get("constraints")),
        "acceptance_checks": ensure_list(feature.get("acceptance_checks")),
        "source_refs": ensure_list(feature.get("source_refs")),
    }
    surface_map = {
        "design_surfaces": design_surfaces,
        "ownership_summary": ownership_summary,
        "create_justification_summary": create_justification_summary,
        "owner_binding_status": owner_binding_status,
        "bypass_rationale": bypass_rationale,
    }
    downstream_handoff = {
        "target_workflows": [
            "workflow.dev.feat_to_tech",
            "workflow.dev.feat_to_proto",
            "workflow.dev.proto_to_ui",
            "workflow.dev.tech_to_impl",
        ],
        "surface_map_ref": surface_map_ref,
        "feat_ref": feat_ref,
    }
    return {
        "artifact_type": "surface_map_package",
        "workflow_key": "dev.feat-to-surface-map",
        "workflow_run_id": run_id,
        "status": "accepted",
        "schema_version": str(bundle.get("schema_version") or "1.0.0"),
        "feat_ref": feat_ref,
        "surface_map_ref": surface_map_ref,
        "selected_feat": selected_feat,
        "design_impact_required": design_impact_required,
        "surface_map": surface_map,
        "source_refs": source_refs,
        "downstream_handoff": downstream_handoff,
        "surface_map_digest": stable_digest(
            {
                "feat_ref": feat_ref,
                "design_impact_required": design_impact_required,
                "design_surfaces": design_surfaces,
                "owner_binding_status": owner_binding_status,
            }
        ),
    }

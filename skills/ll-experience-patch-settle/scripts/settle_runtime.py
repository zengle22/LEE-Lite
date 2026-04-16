import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from cli.lib.patch_schema import validate_file, PatchSchemaError
from cli.lib.errors import ensure


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50]


def scan_pending_patches(feat_dir: Path) -> list[dict]:
    """Scan feat_dir for patches with status == pending_backwrite.

    Uses yaml.safe_load() for security. Validates each patch via
    patch_schema.py validate_file() before including.
    Adds _file key with absolute path string to each returned dict.
    Returns results sorted by patch ID ascending.
    """
    pending = []
    for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
        try:
            with open(patch_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            # Skip malformed YAML files
            continue

        if data is None:
            continue

        # Unwrap nested structure: YAML has experience_patch as root key
        patch = data.get("experience_patch", data)

        # Only include pending_backwrite
        if patch.get("status") != "pending_backwrite":
            continue

        # Validate via schema before including
        try:
            validate_file(patch_file, schema_type="patch")
        except (PatchSchemaError, Exception):
            # Skip patches that fail validation
            continue

        # Add _file key with absolute path
        patch["_file"] = str(patch_file.resolve())
        pending.append(patch)

    # Sort by patch ID ascending
    pending.sort(key=lambda p: p["id"])
    return pending


def group_by_class(patches: list[dict]) -> dict[str, list[dict]]:
    """Group patches by change_class using defaultdict."""
    groups = defaultdict(list)
    for p in patches:
        groups[p["change_class"]].append(p)
    return dict(groups)


def settle_patch(feat_dir: Path, patch: dict, new_status: str) -> dict:
    """Update a patch YAML file status to new_status.

    Sets resolution.backwrite_status for terminal states:
    - retain_in_code (D-02 visual terminal)
    - upgraded_to_src (D-04 semantic terminal)
    """
    patch_file = Path(patch["_file"])
    with open(patch_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Unwrap: find the root key
    root_key = "experience_patch" if "experience_patch" in data else None
    target = data[root_key] if root_key else data

    # Update status
    target["status"] = new_status
    target["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Set resolution for terminal states
    if new_status == "retain_in_code":
        if "resolution" not in target:
            target["resolution"] = {}
        target["resolution"]["backwrite_status"] = "retain_in_code"
    elif new_status == "upgraded_to_src":
        if "resolution" not in target:
            target["resolution"] = {}
        target["resolution"]["backwrite_status"] = "upgraded_to_src"

    # Write back
    with open(patch_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    return {
        "patch_id": target["id"],
        "new_status": new_status,
        "file_path": str(patch_file),
    }


def update_registry_statuses(feat_dir: Path, updated_patches: list[dict]) -> None:
    """Update registry entries after settlement.

    Atomic pattern: read entire registry, update in-memory, single write.
    """
    registry_path = feat_dir / "patch_registry.json"
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    status_map = {p["id"]: p["status"] for p in updated_patches}
    for entry in registry["patches"]:
        if entry["id"] in status_map:
            entry["status"] = status_map[entry["id"]]

    registry["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def generate_delta_files(feat_dir: Path, patches: list[dict], change_class: str) -> list[str]:
    """Generate delta/SRC files per change_class.

    D-02 visual: no delta files, only status update -> return []
    D-03 interaction: ui-spec-delta.yaml + flow-spec-delta.yaml + test-impact-draft.yaml
    D-04 semantic: SRC-XXXX__{slug}.yaml candidates
    """
    if change_class == "visual":
        return []

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    generated = []

    if change_class == "interaction":
        # D-03: ui-spec-delta.yaml
        ui_spec = {
            "ui_spec_delta": {
                "generated_at": timestamp,
                "source_patches": [p["id"] for p in patches],
                "changes": [
                    {
                        "patch_id": p["id"],
                        "original_text": p.get("summary", ""),
                        "proposed_change": p.get("description", p.get("summary", "")),
                        "rationale": p.get("problem", {}).get("user_issue", "") if p.get("problem") else "",
                        "affected_files": p.get("implementation", {}).get("changed_files", []),
                    }
                    for p in patches
                ],
            }
        }
        ui_path = feat_dir / "ui-spec-delta.yaml"
        with open(ui_path, "w", encoding="utf-8") as f:
            yaml.dump(ui_spec, f, default_flow_style=False, allow_unicode=True)
        generated.append(str(ui_path))

        # D-03: flow-spec-delta.yaml
        flow_spec = {
            "flow_spec_delta": {
                "generated_at": timestamp,
                "source_patches": [p["id"] for p in patches],
                "changes": [
                    {
                        "patch_id": p["id"],
                        "original_text": p.get("summary", ""),
                        "proposed_change": p.get("description", p.get("summary", "")),
                        "rationale": p.get("problem", {}).get("user_issue", "") if p.get("problem") else "",
                        "affected_files": p.get("implementation", {}).get("changed_files", []),
                    }
                    for p in patches
                ],
            }
        }
        flow_path = feat_dir / "flow-spec-delta.yaml"
        with open(flow_path, "w", encoding="utf-8") as f:
            yaml.dump(flow_spec, f, default_flow_style=False, allow_unicode=True)
        generated.append(str(flow_path))

        # D-03: test-impact-draft.yaml
        test_impact = {
            "test_impact_draft": {
                "generated_at": timestamp,
                "source_patches": [p["id"] for p in patches],
                "impacts": [
                    {
                        "patch_id": p["id"],
                        "test_impact": p.get("test_impact", {}),
                        "affected_files": p.get("implementation", {}).get("changed_files", []),
                    }
                    for p in patches
                ],
            }
        }
        test_path = feat_dir / "test-impact-draft.yaml"
        with open(test_path, "w", encoding="utf-8") as f:
            yaml.dump(test_impact, f, default_flow_style=False, allow_unicode=True)
        generated.append(str(test_path))

    elif change_class == "semantic":
        # D-04: SRC-XXXX__{slug}.yaml candidates
        for p in patches:
            slug = slugify(p.get("title", p["id"]))
            src_id = f"SRC-{p['id']}__{slug}"
            src_candidate = {
                "src_candidate": {
                    "patch_id": p["id"],
                    "generated_at": timestamp,
                    "title": p.get("title", ""),
                    "summary": p.get("summary", ""),
                    "proposed_changes": p.get("description", p.get("summary", "")),
                    "affected_files": p.get("implementation", {}).get("changed_files", []),
                    "requires_gate_approval": True,
                }
            }
            src_path = feat_dir / f"{src_id}.yaml"
            with open(src_path, "w", encoding="utf-8") as f:
                yaml.dump(src_candidate, f, default_flow_style=False, allow_unicode=True)
            generated.append(str(src_path))

    return generated


def generate_settlement_report(feat_dir: Path, results: list[dict]) -> str:
    """Write resolved_patches.yaml settlement report to feat_dir."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Determine feat_id from feat_dir
    feat_id = feat_dir.name

    # Count by change_class
    by_class = defaultdict(int)
    for r in results:
        by_class[r["change_class"]] += 1

    report = {
        "settlement_report": {
            "feat_id": feat_id,
            "generated_at": timestamp,
            "total_settled": len(results),
            "by_class": dict(by_class),
            "results": results,
        }
    }

    report_path = feat_dir / "resolved_patches.yaml"
    with open(report_path, "w", encoding="utf-8") as f:
        yaml.dump(report, f, default_flow_style=False, allow_unicode=True)

    return str(report_path)


def detect_settlement_conflicts(patches: list[dict]) -> list[dict]:
    """Detect same-file multi-patch conflicts within the same settlement batch.

    For each pair of patches, check if implementation.changed_files overlap.
    Returns list of conflict dicts: {patch_a, patch_b, overlapping_files}.
    """
    conflicts = []
    for i in range(len(patches)):
        for j in range(i + 1, len(patches)):
            files_a = set(patches[i].get("implementation", {}).get("changed_files", []))
            files_b = set(patches[j].get("implementation", {}).get("changed_files", []))
            overlap = files_a & files_b
            if overlap:
                conflicts.append({
                    "patch_a": patches[i]["id"],
                    "patch_b": patches[j]["id"],
                    "overlapping_files": sorted(overlap),
                })
    return conflicts


def run_skill(workspace_root: Path | str, payload: dict[str, Any]) -> dict:
    """Main entry point for settlement skill.

    Args:
        workspace_root: Project root directory
        payload: Request payload with feat_id

    Returns:
        dict with settled count, by_class, report_path, escalations, delta_files
    """
    workspace_root = Path(workspace_root) if isinstance(workspace_root, str) else workspace_root

    feat_id = str(payload.get("feat_id", "")).strip()
    ensure(feat_id, "INVALID_REQUEST", "feat_id is required")

    # Security: validate feat_id format (alphanumeric, hyphens, dots only)
    ensure(
        bool(re.match(r'^[a-zA-Z0-9][\w.\-]*$', feat_id)),
        "INVALID_REQUEST",
        "feat_id contains invalid characters",
    )
    ensure(len(feat_id) <= 128, "INVALID_REQUEST", "feat_id too long (max 128 chars)")

    # Resolve FEAT directory with path containment check
    base_dir = workspace_root / "ssot" / "experience-patches"
    feat_dir = (base_dir / feat_id).resolve()
    ensure(
        str(feat_dir).startswith(str(base_dir.resolve())),
        "INVALID_REQUEST",
        "feat_id contains path traversal",
    )

    # Scan pending patches
    pending = scan_pending_patches(feat_dir)
    if not pending:
        return {"settled": 0, "message": "no pending_backwrite patches"}

    # Detect conflicts
    conflicts = detect_settlement_conflicts(pending)
    escalations = []
    if conflicts:
        escalations = conflicts

    # Group by change_class
    groups = group_by_class(pending)

    # Status mapping per backwrite rules
    status_map = {
        "visual": "retain_in_code",
        "interaction": "backwritten",
        "semantic": "upgraded_to_src",
    }

    all_results = []
    all_updated_patches = []
    all_delta_files = []

    for change_class, group in groups.items():
        # Generate delta files
        delta_files = generate_delta_files(feat_dir, group, change_class)
        all_delta_files.extend(delta_files)

        # Settle each patch
        new_status = status_map.get(change_class, "backwritten")
        for patch in group:
            result = settle_patch(feat_dir, patch, new_status)
            result["change_class"] = change_class
            result["action"] = new_status
            result["files_generated"] = delta_files
            result["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            all_results.append(result)
            # Track patch dict with updated status for registry
            patch["status"] = new_status
            all_updated_patches.append(patch)

    # Update registry statuses
    update_registry_statuses(feat_dir, all_updated_patches)

    # Generate settlement report
    report_path = generate_settlement_report(feat_dir, all_results)

    # Count by_class
    by_class = defaultdict(int)
    for r in all_results:
        by_class[r["change_class"]] += 1

    return {
        "settled": len(all_results),
        "by_class": dict(by_class),
        "report_path": report_path,
        "escalations": escalations,
        "delta_files": all_delta_files,
    }


if __name__ == "__main__":
    import json as _json
    if len(sys.argv) < 3:
        print("Usage: python settle_runtime.py <workspace_root> <request_json_path>")
        sys.exit(1)
    ws = Path(sys.argv[1])
    with open(sys.argv[2], encoding="utf-8") as f:
        req = _json.load(f)
    result = run_skill(ws, req.get("payload", {}))
    print(_json.dumps(result, indent=2, ensure_ascii=False))

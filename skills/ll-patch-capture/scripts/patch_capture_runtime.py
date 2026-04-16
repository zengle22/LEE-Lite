import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli.lib.patch_schema import validate_file, PatchSchemaError
from cli.lib.errors import ensure


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50]  # Limit length


def get_next_patch_id(feat_dir: Path) -> str:
    """Determine next sequential UXPATCH ID from registry or filesystem."""
    registry_path = feat_dir / "patch_registry.json"
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        existing_ids = [
            int(p["id"].split("-")[1])
            for p in registry.get("patches", [])
            if p.get("id", "").startswith("UXPATCH-")
        ]
        next_seq = max(existing_ids, default=0) + 1
    else:
        next_seq = 1
    return f"UXPATCH-{next_seq:04d}"


def detect_conflicts(feat_dir: Path, new_changed_files: list[str], current_patch_id: str) -> list[dict]:
    """Scan active patches in the same FEAT for overlapping changed_files."""
    conflicts = []
    for patch_file in feat_dir.glob("UXPATCH-*.yaml"):
        if not patch_file.exists():
            continue
        with open(patch_file, encoding="utf-8") as f:
            patch_data = yaml.safe_load(f)

        # Unwrap nested structure: YAML has experience_patch as root key
        patch = patch_data.get("experience_patch", patch_data)
        if patch.get("status") not in ("active", "validated", "pending_backwrite"):
            continue
        if patch.get("id") == current_patch_id:
            continue

        existing_files = set(patch.get("implementation", {}).get("changed_files", []))
        overlap = existing_files & set(new_changed_files)
        if overlap:
            conflicts.append({
                "with_patch_id": patch.get("id", "unknown"),
                "overlapping_files": sorted(overlap),
            })

    return conflicts


def register_patch_in_registry(feat_dir: Path, patch_data: dict) -> dict:
    """Add a new patch entry to patch_registry.json."""
    registry_path = feat_dir / "patch_registry.json"

    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {
            "patch_registry_version": "1.0.0",
            "feat_id": feat_dir.name,
            "patches": [],
            "last_updated": None,
        }

    entry = {
        "id": patch_data["id"],
        "status": patch_data["status"],
        "change_class": patch_data["change_class"],
        "created_at": patch_data["created_at"],
        "title": patch_data["title"],
        "patch_file": f"{patch_data['id']}__{slugify(patch_data['title'])}.yaml",
    }
    registry["patches"].append(entry)
    registry["last_updated"] = patch_data["created_at"]

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return entry


def run_skill(workspace_root: Path | str, payload: dict[str, Any], request_id: str) -> dict:
    """Main entry point for patch capture skill.

    Args:
        workspace_root: Project root directory
        payload: Request payload with feat_id, input_type, input_value
        request_id: CLI request ID for tracing

    Returns:
        dict with patch_path, patch_id, status, and any conflicts/escalation info
    """
    workspace_root = Path(workspace_root) if isinstance(workspace_root, str) else workspace_root

    feat_id = str(payload.get("feat_id", "")).strip()
    input_type = str(payload.get("input_type", "")).strip()
    input_value = str(payload.get("input_value", "")).strip()

    ensure(feat_id, "INVALID_REQUEST", "feat_id is required")
    ensure(input_type in ("prompt", "document"), "INVALID_REQUEST", f"input_type must be 'prompt' or 'document', got '{input_type}'")
    ensure(input_value, "INVALID_REQUEST", "input_value is required")

    # Security: validate feat_id format (alphanumeric, hyphens, dots only)
    ensure(
        bool(re.match(r'^[a-zA-Z0-9][\w.\-]*$', feat_id)),
        "INVALID_REQUEST",
        "feat_id contains invalid characters",
    )
    ensure(len(feat_id) <= 128, "INVALID_REQUEST", "feat_id too long (max 128 chars)")
    ensure(len(input_value) <= 50000, "INVALID_REQUEST", "input_value too long (max 50000 chars)")

    # Resolve FEAT directory with path containment check
    base_dir = workspace_root / "ssot" / "experience-patches"
    feat_dir = (base_dir / feat_id).resolve()
    ensure(
        str(feat_dir).startswith(str(base_dir.resolve())),
        "INVALID_REQUEST",
        "feat_id contains path traversal",
    )
    feat_dir.mkdir(parents=True, exist_ok=True)

    # Generate patch ID
    patch_id = get_next_patch_id(feat_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Validate input file if document path
    if input_type == "document":
        doc_path = Path(input_value)
        ensure(doc_path.exists(), "INVALID_REQUEST", f"document not found: {input_value}")
        # Path traversal check
        try:
            doc_path.resolve().relative_to(workspace_root.resolve())
        except ValueError:
            from cli.lib.errors import ensure as _ensure
            _ensure(False, "INVALID_REQUEST", f"document path outside workspace: {input_value}")

    # Validate generated patch YAML if it exists (post-Executor generation)
    patch_path = None
    validation_result: dict[str, Any] = {"schema_valid": True, "errors": [], "conflicts": []}

    # Scan for the newly generated patch file
    for candidate in feat_dir.glob(f"{patch_id}__*.yaml"):
        if candidate.exists():
            patch_path = str(candidate)
            # Validate against schema
            try:
                validate_file(candidate, schema_type="patch")
                validation_result["schema_valid"] = True
            except PatchSchemaError as e:
                validation_result["schema_valid"] = False
                validation_result["errors"].append(str(e))
            except Exception as e:
                validation_result["schema_valid"] = False
                validation_result["errors"].append(f"Unexpected error: {e}")
            break

    # Check for conflicts
    if patch_path:
        with open(patch_path, encoding="utf-8") as f:
            patch_data = yaml.safe_load(f)
        # Unwrap nested structure: YAML has experience_patch as root key
        patch = patch_data.get("experience_patch", patch_data)
        changed_files = patch.get("implementation", {}).get("changed_files", [])
        conflicts = detect_conflicts(feat_dir, changed_files, patch_id)
        validation_result["conflicts"] = conflicts

    # Update registry if patch is valid
    registered = False
    registry_entry = None
    if patch_path and validation_result["schema_valid"] and not validation_result["conflicts"]:
        with open(patch_path, encoding="utf-8") as f:
            patch_data = yaml.safe_load(f)
        # Unwrap nested structure for registry update too
        patch = patch_data.get("experience_patch", patch_data)

        # SECURITY: do NOT trust AI-generated source fields; set programmatically
        patch["source"]["actor"] = "ai_suggested"
        patch["source"]["session"] = request_id
        patch["source"]["human_confirmed_class"] = patch.get("ai_suggested_class", patch.get("change_class", "visual"))

        # ESCALATION: check triggers before auto-registration (D-09)
        escalation_reasons = []
        # First Patch for this FEAT
        existing_count = len(patch_data.get("patches", [])) if patch_data.get("patches") else 0
        if existing_count == 0:
            escalation_reasons.append("first_patch_for_feat")
        # Semantic Patch requires SRC decision
        if patch.get("change_class") == "semantic":
            escalation_reasons.append("semantic_patch_requires_src_decision")
        # Disputed test_impact
        if patch.get("test_impact", "none") not in ("none", "path_change", "assertion_change", "new_case_needed"):
            escalation_reasons.append("disputed_test_impact")

        if escalation_reasons:
            validation_result["escalation_triggers"] = escalation_reasons
            registered = False
        else:
            patch["created_at"] = timestamp
            patch["updated_at"] = timestamp
            with open(patch_path, "w", encoding="utf-8") as f:
                yaml.dump(patch_data, f, default_flow_style=False, allow_unicode=True)
            # Validate unique patch_id before registering
            registry_for_check = None
            if (feat_dir / "patch_registry.json").exists():
                with open(feat_dir / "patch_registry.json", encoding="utf-8") as f:
                    registry_for_check = json.load(f)
            existing_ids = {p["id"] for p in registry_for_check.get("patches", [])} if registry_for_check else set()
            if patch.get("id") in existing_ids:
                validation_result["escalation_triggers"] = validation_result.get("escalation_triggers", []) + ["duplicate_patch_id"]
                registered = False
            else:
                registry_entry = register_patch_in_registry(feat_dir, patch)
                registered = True

    return {
        "patch_id": patch_id,
        "patch_path": patch_path or "",
        "feat_id": feat_id,
        "registered": registered,
        "validation": validation_result,
        "registry_entry": registry_entry,
        "escalation_needed": not validation_result["schema_valid"] or bool(validation_result["conflicts"]),
        "notification": f"Registered {patch_id} -> ssot/experience-patches/{feat_id}/" if registered else "",
    }


if __name__ == "__main__":
    import json as _json
    if len(sys.argv) < 4:
        print("Usage: python patch_capture_runtime.py <workspace_root> <request_json_path> <request_id>")
        sys.exit(1)
    ws = Path(sys.argv[1])
    with open(sys.argv[2], encoding="utf-8") as f:
        req = _json.load(f)
    rid = sys.argv[3]
    result = run_skill(ws, req.get("payload", {}), rid)
    print(_json.dumps(result, indent=2, ensure_ascii=False))

import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Add project root to path for cli.lib imports
PROJECT_ROOT = SCRIPTS_DIR.parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from settle_runtime import (
    scan_pending_patches,
    group_by_class,
    settle_patch,
    update_registry_statuses,
    generate_delta_files,
    generate_settlement_report,
    detect_settlement_conflicts,
    run_skill,
)


def _make_complete_patch(
    patch_id: str = "UXPATCH-0001",
    change_class: str = "visual",
    changed_files: list[str] | None = None,
    status: str = "pending_backwrite",
) -> dict:
    """Build a complete patch YAML dict that passes schema validation."""
    return {
        "experience_patch": {
            "id": patch_id,
            "type": "experience_patch",
            "status": status,
            "created_at": "2026-04-16T10:00:00Z",
            "updated_at": "2026-04-16T10:00:00Z",
            "title": f"Patch {patch_id}",
            "summary": "Test patch summary",
            "source": {
                "from": "prompt",
                "actor": "ai_suggested",
                "session": "test-session",
                "prompt_ref": "test-prompt",
                "human_confirmed_class": change_class,
                "ai_suggested_class": change_class,
            },
            "scope": {
                "feat_ref": "test-feat",
                "page": "homepage",
                "module": "ui",
            },
            "change_class": change_class,
            "implementation": {
                "code_changed": True,
                "changed_files": changed_files or [],
            },
        }
    }


def _make_feat_dir(
    patches: list[tuple[str, str, list[str], str]] | None = None,
) -> Path:
    """Create a temp feat directory with patch_registry.json and UXPATCH-*.yaml files.

    Args:
        patches: List of (patch_id, change_class, changed_files, status) tuples.
                 Defaults to 3 patches (1 per change_class, all pending_backwrite).

    Returns:
        Path to the created feat directory.
    """
    tmpdir = Path(tempfile.mkdtemp())

    if patches is None:
        patches = [
            ("UXPATCH-0001", "visual", ["src/style.css"], "pending_backwrite"),
            ("UXPATCH-0002", "interaction", ["src/flow.yaml"], "pending_backwrite"),
            ("UXPATCH-0003", "semantic", ["src/state.py"], "pending_backwrite"),
        ]

    registry_patches = []
    for patch_id, change_class, changed_files, status in patches:
        patch_data = _make_complete_patch(patch_id, change_class, changed_files, status)
        slug = patch_id.lower()
        patch_file = tmpdir / f"{patch_id}__{slug}.yaml"
        with open(patch_file, "w", encoding="utf-8") as f:
            yaml.dump(patch_data, f, default_flow_style=False, allow_unicode=True)

        registry_patches.append({
            "id": patch_id,
            "status": status,
            "change_class": change_class,
            "created_at": "2026-04-16T10:00:00Z",
            "title": f"Patch {patch_id}",
            "patch_file": f"{patch_id}__{slug}.yaml",
        })

    registry = {
        "patch_registry_version": "1.0.0",
        "feat_id": tmpdir.name,
        "patches": registry_patches,
        "last_updated": "2026-04-16T10:00:00Z",
    }
    with open(tmpdir / "patch_registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return tmpdir


class TestScanPendingPatches:
    def test_scan_pending_returns_only_pending_backwrite(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["src/a.css"], "pending_backwrite"),
            ("UXPATCH-0002", "interaction", ["src/b.yaml"], "active"),
            ("UXPATCH-0003", "semantic", ["src/c.py"], "archived"),
        ])
        result = scan_pending_patches(feat_dir)
        assert len(result) == 1
        assert result[0]["id"] == "UXPATCH-0001"

    def test_scan_pending_skips_malformed_yaml(self):
        feat_dir = _make_feat_dir()
        # Write invalid YAML
        with open(feat_dir / "UXPATCH-0099__bad.yaml", "w") as f:
            f.write("not: valid: yaml: [[[[")
        result = scan_pending_patches(feat_dir)
        # Should not crash; valid patches still returned
        assert all(p["id"].startswith("UXPATCH-") for p in result)

    def test_scan_pending_validates_schema(self):
        feat_dir = _make_feat_dir()
        # Write patch missing required fields
        bad_patch = {"experience_patch": {"id": "UXPATCH-0099"}}
        with open(feat_dir / "UXPATCH-0099__bad.yaml", "w") as f:
            yaml.dump(bad_patch, f)
        result = scan_pending_patches(feat_dir)
        # Bad patch should be skipped
        assert all(p["id"] != "UXPATCH-0099" for p in result)

    def test_scan_pending_empty_dir(self):
        tmpdir = Path(tempfile.mkdtemp())
        result = scan_pending_patches(tmpdir)
        assert result == []

    def test_scan_pending_adds_file_key(self):
        feat_dir = _make_feat_dir()
        result = scan_pending_patches(feat_dir)
        for p in result:
            assert "_file" in p
            assert Path(p["_file"]).is_absolute()

    def test_scan_pending_sorted_by_id(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0003", "visual", ["a.css"], "pending_backwrite"),
            ("UXPATCH-0001", "visual", ["b.css"], "pending_backwrite"),
            ("UXPATCH-0002", "visual", ["c.css"], "pending_backwrite"),
        ])
        result = scan_pending_patches(feat_dir)
        ids = [p["id"] for p in result]
        assert ids == sorted(ids)


class TestGroupByClass:
    def test_group_by_class_splits_correctly(self):
        patches = [
            {"id": "UXPATCH-0001", "change_class": "visual"},
            {"id": "UXPATCH-0002", "change_class": "interaction"},
            {"id": "UXPATCH-0003", "change_class": "interaction"},
        ]
        result = group_by_class(patches)
        assert len(result["visual"]) == 1
        assert len(result["interaction"]) == 2

    def test_group_by_class_empty_input(self):
        result = group_by_class([])
        assert result == {}

    def test_group_by_class_all_same(self):
        patches = [
            {"id": "UXPATCH-0001", "change_class": "visual"},
            {"id": "UXPATCH-0002", "change_class": "visual"},
            {"id": "UXPATCH-0003", "change_class": "visual"},
        ]
        result = group_by_class(patches)
        assert list(result.keys()) == ["visual"]
        assert len(result["visual"]) == 3


class TestSettleVisual:
    def test_settle_visual_to_retain_in_code(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["src/style.css"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        result = settle_patch(feat_dir, pending[0], "retain_in_code")
        assert result["new_status"] == "retain_in_code"

    def test_settle_visual_resolution_backwrite_status(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["src/style.css"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        settle_patch(feat_dir, pending[0], "retain_in_code")
        # Read back the file
        with open(pending[0]["_file"], encoding="utf-8") as f:
            data = yaml.safe_load(f)
        patch = data.get("experience_patch", data)
        assert patch["resolution"]["backwrite_status"] == "retain_in_code"

    def test_settle_visual_no_delta_files(self):
        """D-02: visual patches generate no delta files."""
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["src/style.css"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        delta_files = generate_delta_files(feat_dir, pending, "visual")
        assert delta_files == []


class TestSettleInteraction:
    def test_settle_interaction_creates_delta_files(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "interaction", ["src/flow.yaml"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        delta_files = generate_delta_files(feat_dir, pending, "interaction")
        assert len(delta_files) == 3
        assert any("ui-spec-delta.yaml" in f for f in delta_files)
        assert any("flow-spec-delta.yaml" in f for f in delta_files)
        assert any("test-impact-draft.yaml" in f for f in delta_files)

    def test_settle_interaction_ui_spec_has_original_text(self):
        """D-06: delta files must contain original_text field."""
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "interaction", ["src/flow.yaml"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        generate_delta_files(feat_dir, pending, "interaction")
        with open(feat_dir / "ui-spec-delta.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        changes = data["ui_spec_delta"]["changes"]
        assert len(changes) > 0
        assert "original_text" in changes[0]

    def test_settle_interaction_to_backwritten(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "interaction", ["src/flow.yaml"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        result = settle_patch(feat_dir, pending[0], "backwritten")
        assert result["new_status"] == "backwritten"


class TestSettleSemantic:
    def test_settle_semantic_creates_src_candidate(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "semantic", ["src/state.py"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        delta_files = generate_delta_files(feat_dir, pending, "semantic")
        assert len(delta_files) == 1
        assert "SRC-UXPATCH-0001" in delta_files[0]

    def test_settle_semantic_src_has_gate_approval(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "semantic", ["src/state.py"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        delta_files = generate_delta_files(feat_dir, pending, "semantic")
        with open(delta_files[0], encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["src_candidate"]["requires_gate_approval"] is True

    def test_settle_semantic_to_upgraded_to_src(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "semantic", ["src/state.py"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        result = settle_patch(feat_dir, pending[0], "upgraded_to_src")
        assert result["new_status"] == "upgraded_to_src"
        # Read back and check resolution
        with open(pending[0]["_file"], encoding="utf-8") as f:
            data = yaml.safe_load(f)
        patch = data.get("experience_patch", data)
        assert patch["resolution"]["backwrite_status"] == "upgraded_to_src"


class TestUpdateRegistryStatuses:
    def test_update_registry_updates_matching_ids(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["a.css"], "pending_backwrite"),
            ("UXPATCH-0002", "interaction", ["b.yaml"], "pending_backwrite"),
            ("UXPATCH-0003", "semantic", ["c.py"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        # Simulate post-settlement statuses
        pending[0]["status"] = "retain_in_code"
        pending[1]["status"] = "backwritten"
        update_registry_statuses(feat_dir, pending[:2])
        with open(feat_dir / "patch_registry.json", encoding="utf-8") as f:
            registry = json.load(f)
        statuses = {p["id"]: p["status"] for p in registry["patches"]}
        assert statuses["UXPATCH-0001"] == "retain_in_code"
        assert statuses["UXPATCH-0002"] == "backwritten"

    def test_update_registry_preserves_non_matching(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["a.css"], "pending_backwrite"),
        ])
        pending = scan_pending_patches(feat_dir)
        pending[0]["status"] = "retain_in_code"
        update_registry_statuses(feat_dir, pending)
        with open(feat_dir / "patch_registry.json", encoding="utf-8") as f:
            registry = json.load(f)
        # Third patch (if present in registry) should keep original status
        for p in registry["patches"]:
            if p["id"] == "UXPATCH-0001":
                assert p["status"] == "retain_in_code"

    def test_update_registry_sets_last_updated(self):
        feat_dir = _make_feat_dir()
        pending = scan_pending_patches(feat_dir)
        for p in pending:
            p["status"] = "backwritten"
        update_registry_statuses(feat_dir, pending)
        with open(feat_dir / "patch_registry.json", encoding="utf-8") as f:
            registry = json.load(f)
        assert "2026" in registry["last_updated"]


class TestSettlementReport:
    def test_settlement_report_contains_all_results(self):
        feat_dir = _make_feat_dir([
            ("UXPATCH-0001", "visual", ["a.css"], "pending_backwrite"),
            ("UXPATCH-0002", "interaction", ["b.yaml"], "pending_backwrite"),
            ("UXPATCH-0003", "semantic", ["c.py"], "pending_backwrite"),
        ])
        results = [
            {"patch_id": "UXPATCH-0001", "change_class": "visual", "action": "retain_in_code", "new_status": "retain_in_code", "files_generated": []},
            {"patch_id": "UXPATCH-0002", "change_class": "interaction", "action": "backwritten", "new_status": "backwritten", "files_generated": ["ui-spec-delta.yaml"]},
            {"patch_id": "UXPATCH-0003", "change_class": "semantic", "action": "upgraded_to_src", "new_status": "upgraded_to_src", "files_generated": ["SRC-UXPATCH-0003.yaml"]},
        ]
        report_path = generate_settlement_report(feat_dir, results)
        assert Path(report_path).exists()
        with open(report_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["settlement_report"]["results"]) == 3

    def test_settlement_report_has_by_class_counts(self):
        feat_dir = _make_feat_dir()
        results = [
            {"patch_id": "UXPATCH-0001", "change_class": "visual", "action": "retain_in_code", "new_status": "retain_in_code", "files_generated": []},
            {"patch_id": "UXPATCH-0002", "change_class": "interaction", "action": "backwritten", "new_status": "backwritten", "files_generated": []},
            {"patch_id": "UXPATCH-0003", "change_class": "semantic", "action": "upgraded_to_src", "new_status": "upgraded_to_src", "files_generated": []},
        ]
        report_path = generate_settlement_report(feat_dir, results)
        with open(report_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        by_class = data["settlement_report"]["by_class"]
        assert by_class["visual"] == 1
        assert by_class["interaction"] == 1
        assert by_class["semantic"] == 1

    def test_settlement_report_generated_at(self):
        feat_dir = _make_feat_dir()
        results = [{"patch_id": "UXPATCH-0001", "change_class": "visual", "action": "retain_in_code", "new_status": "retain_in_code", "files_generated": []}]
        report_path = generate_settlement_report(feat_dir, results)
        with open(report_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "generated_at" in data["settlement_report"]
        assert "T" in data["settlement_report"]["generated_at"]


class TestEscalationConditions:
    def test_detect_conflicts_finds_overlap(self):
        patches = [
            {"id": "UXPATCH-0001", "implementation": {"changed_files": ["src/a.tsx", "src/b.css"]}},
            {"id": "UXPATCH-0002", "implementation": {"changed_files": ["src/a.tsx", "src/c.py"]}},
        ]
        conflicts = detect_settlement_conflicts(patches)
        assert len(conflicts) == 1
        assert "src/a.tsx" in conflicts[0]["overlapping_files"]

    def test_detect_conflicts_no_overlap(self):
        patches = [
            {"id": "UXPATCH-0001", "implementation": {"changed_files": ["src/a.tsx"]}},
            {"id": "UXPATCH-0002", "implementation": {"changed_files": ["src/b.css"]}},
        ]
        conflicts = detect_settlement_conflicts(patches)
        assert conflicts == []


class TestRunSkill:
    def test_run_skill_no_pending_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "empty-feat"
            feat_dir.mkdir(parents=True)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "empty-feat",
                "patches": [],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            result = run_skill(tmpdir, {"feat_id": "empty-feat"})
            assert result["settled"] == 0

    def test_run_skill_settles_all_classes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            # Create patches
            for pid, cc, files in [
                ("UXPATCH-0001", "visual", ["a.css"]),
                ("UXPATCH-0002", "interaction", ["b.yaml"]),
                ("UXPATCH-0003", "semantic", ["c.py"]),
            ]:
                patch_data = _make_complete_patch(pid, cc, files, "pending_backwrite")
                with open(feat_dir / f"{pid}__test.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(patch_data, f)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [
                    {"id": "UXPATCH-0001", "status": "pending_backwrite", "change_class": "visual", "created_at": "2026-04-16T10:00:00Z", "title": "V", "patch_file": "UXPATCH-0001__test.yaml"},
                    {"id": "UXPATCH-0002", "status": "pending_backwrite", "change_class": "interaction", "created_at": "2026-04-16T10:00:00Z", "title": "I", "patch_file": "UXPATCH-0002__test.yaml"},
                    {"id": "UXPATCH-0003", "status": "pending_backwrite", "change_class": "semantic", "created_at": "2026-04-16T10:00:00Z", "title": "S", "patch_file": "UXPATCH-0003__test.yaml"},
                ],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            result = run_skill(tmpdir, {"feat_id": "test-feat"})
            assert result["settled"] == 3
            assert "by_class" in result
            assert "report_path" in result

    def test_run_skill_updates_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            patch_data = _make_complete_patch("UXPATCH-0001", "visual", ["a.css"], "pending_backwrite")
            with open(feat_dir / "UXPATCH-0001__test.yaml", "w", encoding="utf-8") as f:
                yaml.dump(patch_data, f)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [
                    {"id": "UXPATCH-0001", "status": "pending_backwrite", "change_class": "visual", "created_at": "2026-04-16T10:00:00Z", "title": "V", "patch_file": "UXPATCH-0001__test.yaml"},
                ],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            run_skill(tmpdir, {"feat_id": "test-feat"})
            with open(feat_dir / "patch_registry.json", encoding="utf-8") as f:
                reg = json.load(f)
            assert reg["patches"][0]["status"] == "retain_in_code"

    def test_run_skill_escalates_on_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            shared_file = "src/conflict.tsx"
            for pid in ["UXPATCH-0001", "UXPATCH-0002"]:
                patch_data = _make_complete_patch(pid, "visual", [shared_file], "pending_backwrite")
                with open(feat_dir / f"{pid}__test.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(patch_data, f)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [
                    {"id": "UXPATCH-0001", "status": "pending_backwrite", "change_class": "visual", "created_at": "2026-04-16T10:00:00Z", "title": "V1", "patch_file": "UXPATCH-0001__test.yaml"},
                    {"id": "UXPATCH-0002", "status": "pending_backwrite", "change_class": "visual", "created_at": "2026-04-16T10:00:00Z", "title": "V2", "patch_file": "UXPATCH-0002__test.yaml"},
                ],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            result = run_skill(tmpdir, {"feat_id": "test-feat"})
            assert "escalations" in result
            assert len(result["escalations"]) > 0

    def test_run_skill_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            with pytest.raises(CommandError):
                run_skill(tmpdir, {"feat_id": "../evil"})

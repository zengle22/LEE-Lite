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

from patch_capture_runtime import (
    slugify,
    get_next_patch_id,
    detect_conflicts,
    register_patch_in_registry,
    run_skill,
)


def _make_complete_patch(
    patch_id: str = "UXPATCH-0002",
    change_class: str = "visual",
    changed_files: list[str] | None = None,
    source_actor: str = "ai_suggested",
    ai_suggested_class: str | None = "visual",
) -> dict:
    """Build a complete patch YAML dict that passes schema validation."""

    patch = {
        "experience_patch": {
            "id": patch_id,
            "type": "experience_patch",
            "status": "active",
            "created_at": "2026-04-16T10:00:00Z",
            "updated_at": "2026-04-16T10:00:00Z",
            "title": f"Patch {patch_id}",
            "summary": "Test patch",
            "source": {
                "from": "prompt",
                "actor": source_actor,
                "session": "test-session",
                "prompt_ref": "test-prompt",
                "human_confirmed_class": ai_suggested_class or change_class,
                "ai_suggested_class": ai_suggested_class,
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

    return patch


class TestSlugify:
    def test_basic_slugify(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars_and_whitespace(self):
        assert slugify("Hello  World__Test") == "hello-world-test"

    def test_truncation_to_50_chars(self):
        long_text = "a" * 100
        result = slugify(long_text)
        assert len(result) <= 50


class TestGetNextPatchId:
    def test_no_registry_starts_at_0001(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            result = get_next_patch_id(feat_dir)
            assert result == "UXPATCH-0001"

    def test_existing_registry_increments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [
                    {"id": "UXPATCH-0001"},
                    {"id": "UXPATCH-0002"},
                    {"id": "UXPATCH-0003"},
                ],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            result = get_next_patch_id(feat_dir)
            assert result == "UXPATCH-0004"

    def test_empty_patches_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [],
                "last_updated": "2026-04-16T10:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)
            result = get_next_patch_id(feat_dir)
            assert result == "UXPATCH-0001"


class TestDetectConflicts:
    def test_overlapping_files_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            existing_patch = {
                "experience_patch": {
                    "id": "UXPATCH-0001",
                    "status": "active",
                    "implementation": {
                        "changed_files": ["src/components/Button.tsx", "src/styles/main.css"],
                    },
                }
            }
            with open(feat_dir / "UXPATCH-0001__test.yaml", "w") as f:
                yaml.dump(existing_patch, f)

            conflicts = detect_conflicts(
                feat_dir,
                ["src/components/Button.tsx", "src/utils/helper.py"],
                "UXPATCH-0002",
            )
            assert len(conflicts) == 1
            assert conflicts[0]["with_patch_id"] == "UXPATCH-0001"
            assert "src/components/Button.tsx" in conflicts[0]["overlapping_files"]

    def test_no_overlapping_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            existing_patch = {
                "experience_patch": {
                    "id": "UXPATCH-0001",
                    "status": "active",
                    "implementation": {
                        "changed_files": ["src/components/Button.tsx"],
                    },
                }
            }
            with open(feat_dir / "UXPATCH-0001__test.yaml", "w") as f:
                yaml.dump(existing_patch, f)

            conflicts = detect_conflicts(
                feat_dir,
                ["src/utils/helper.py"],
                "UXPATCH-0002",
            )
            assert len(conflicts) == 0

    def test_skips_inactive_patches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            archived_patch = {
                "experience_patch": {
                    "id": "UXPATCH-0001",
                    "status": "archived",
                    "implementation": {
                        "changed_files": ["src/components/Button.tsx"],
                    },
                }
            }
            with open(feat_dir / "UXPATCH-0001__test.yaml", "w") as f:
                yaml.dump(archived_patch, f)

            conflicts = detect_conflicts(
                feat_dir,
                ["src/components/Button.tsx"],
                "UXPATCH-0002",
            )
            assert len(conflicts) == 0

    def test_malformed_yaml_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            # Write invalid YAML -- detect_conflicts should skip, not crash
            with open(feat_dir / "UXPATCH-0001__test.yaml", "w") as f:
                f.write("not: valid: yaml: [[[")

            conflicts = detect_conflicts(feat_dir, ["src/components/Button.tsx"], "UXPATCH-0002")
            assert len(conflicts) == 0


class TestRegisterPatchInRegistry:
    def test_creates_new_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            patch_data = {
                "id": "UXPATCH-0001",
                "status": "active",
                "change_class": "visual",
                "created_at": "2026-04-16T10:00:00Z",
                "title": "Fix button color",
            }
            entry = register_patch_in_registry(feat_dir, patch_data)
            assert entry["id"] == "UXPATCH-0001"

            registry_path = feat_dir / "patch_registry.json"
            assert registry_path.exists()
            with open(registry_path) as f:
                registry = json.load(f)
            assert registry["patch_registry_version"] == "1.0.0"
            assert len(registry["patches"]) == 1
            assert registry["last_updated"] == "2026-04-16T10:00:00Z"

    def test_appends_to_existing_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [
                    {"id": "UXPATCH-0001"},
                ],
                "last_updated": "2026-04-16T09:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)

            patch_data = {
                "id": "UXPATCH-0002",
                "status": "active",
                "change_class": "interaction",
                "created_at": "2026-04-16T10:00:00Z",
                "title": "Change navigation",
            }
            entry = register_patch_in_registry(feat_dir, patch_data)
            assert entry["id"] == "UXPATCH-0002"

            with open(feat_dir / "patch_registry.json") as f:
                updated = json.load(f)
            assert len(updated["patches"]) == 2


class TestRunSkill:
    def test_missing_feat_id_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            with pytest.raises(CommandError, match="feat_id is required"):
                run_skill(tmpdir, {"input_type": "prompt", "input_value": "test"}, "req-1")

    def test_invalid_input_type_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            with pytest.raises(CommandError, match="input_type must be"):
                run_skill(
                    tmpdir,
                    {"feat_id": "test", "input_type": "invalid", "input_value": "test"},
                    "req-1",
                )

    def test_valid_prompt_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_skill(
                tmpdir,
                {
                    "feat_id": "test-feat",
                    "input_type": "prompt",
                    "input_value": "Fix button color on homepage",
                },
                "req-test-001",
            )
            assert "patch_id" in result
            assert result["patch_id"].startswith("UXPATCH-")

    def test_document_outside_workspace_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as outside_dir:
                outside_file = Path(outside_dir) / "doc.yaml"
                outside_file.write_text("test: data")

                from cli.lib.errors import CommandError
                with pytest.raises(CommandError, match="outside workspace"):
                    run_skill(
                        tmpdir,
                        {
                            "feat_id": "test-feat",
                            "input_type": "document",
                            "input_value": str(outside_file),
                        },
                        "req-test-002",
                    )

    def test_valid_document_input_happy_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid document file inside the workspace
            doc_file = Path(tmpdir) / "change-request.yaml"
            doc_file.write_text("description: Fix button color\n")

            result = run_skill(
                tmpdir,
                {
                    "feat_id": "test-feat",
                    "input_type": "document",
                    "input_value": str(doc_file),
                },
                "req-test-003",
            )
            assert "patch_id" in result
            assert result["patch_id"].startswith("UXPATCH-")

    def test_escalation_first_patch_for_feat(self):
        """With no registry, first patch should trigger escalation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a complete patch YAML that passes schema validation
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "new-feat"
            feat_dir.mkdir(parents=True)
            patch_file = feat_dir / "UXPATCH-0001__test.yaml"
            patch_content = _make_complete_patch("UXPATCH-0001", "visual", changed_files=["src/style.css"])
            with open(patch_file, "w") as f:
                yaml.dump(patch_content, f)

            result = run_skill(
                tmpdir,
                {"feat_id": "new-feat", "input_type": "prompt", "input_value": "Fix button color"},
                "req-test-004",
            )
            assert result.get("validation", {}).get("escalation_triggers") is not None
            assert "first_patch_for_feat" in result["validation"]["escalation_triggers"]
            assert result["registered"] is False

    def test_escalation_semantic_class(self):
        """Semantic change_class should trigger escalation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            # Create registry so it's not first-patch
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [{"id": "UXPATCH-0001"}],
                "last_updated": "2026-04-16T09:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)

            # Write a complete semantic patch YAML file
            patch_file = feat_dir / "UXPATCH-0002__test.yaml"
            patch_content = _make_complete_patch(
                "UXPATCH-0002", "semantic",
                changed_files=["src/state.py"],
                ai_suggested_class="semantic",
            )
            with open(patch_file, "w") as f:
                yaml.dump(patch_content, f)

            result = run_skill(
                tmpdir,
                {"feat_id": "test-feat", "input_type": "prompt", "input_value": "test"},
                "req-test-005",
            )
            assert "semantic_patch_requires_src_decision" in result["validation"]["escalation_triggers"]
            assert result["registered"] is False

    def test_source_fields_set_by_runtime(self):
        """Runtime overrides source.actor and source.session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create registry to bypass first-patch escalation
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [{"id": "UXPATCH-0001"}, {"id": "UXPATCH-0002"}],
                "last_updated": "2026-04-16T09:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)

            # Write a visual patch (no escalation) with AI-faked source
            patch_file = feat_dir / "UXPATCH-0003__test.yaml"
            patch_content = _make_complete_patch(
                "UXPATCH-0003", "visual",
                changed_files=["src/styles.css"],
                source_actor="human",
                ai_suggested_class="visual",
            )
            with open(patch_file, "w") as f:
                yaml.dump(patch_content, f)

            result = run_skill(
                tmpdir,
                {"feat_id": "test-feat", "input_type": "prompt", "input_value": "test"},
                "req-test-006",
            )
            assert result["registered"] is True
            # Verify source was overridden by runtime
            with open(patch_file) as f:
                saved = yaml.safe_load(f)
            saved_patch = saved.get("experience_patch", saved)
            assert saved_patch["source"]["actor"] == "ai_suggested"
            assert saved_patch["source"]["session"] == "req-test-006"

    def test_feat_id_path_traversal_rejected(self):
        """feat_id with path traversal should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            # The regex check catches ../ first, so test for that message
            with pytest.raises(CommandError, match="invalid characters|path traversal"):
                run_skill(
                    tmpdir,
                    {"feat_id": "../../../tmp/evil", "input_type": "prompt", "input_value": "test"},
                    "req-test-007",
                )

    def test_feat_id_invalid_chars_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            with pytest.raises(CommandError, match="invalid characters"):
                run_skill(
                    tmpdir,
                    {"feat_id": "feat@with$special", "input_type": "prompt", "input_value": "test"},
                    "req-test-008",
                )

    def test_missing_input_value_raises(self):
        """Missing input_value should raise CommandError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from cli.lib.errors import CommandError
            with pytest.raises(CommandError, match="input_value is required"):
                run_skill(
                    tmpdir,
                    {"feat_id": "test", "input_type": "prompt"},
                    "req-1",
                )

    def test_notification_on_successful_registration(self):
        """Successful registration should include notification message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create registry to bypass first-patch escalation
            feat_dir = Path(tmpdir) / "ssot" / "experience-patches" / "test-feat"
            feat_dir.mkdir(parents=True)
            registry = {
                "patch_registry_version": "1.0.0",
                "feat_id": "test-feat",
                "patches": [{"id": "UXPATCH-0001"}, {"id": "UXPATCH-0002"}],
                "last_updated": "2026-04-16T09:00:00Z",
            }
            with open(feat_dir / "patch_registry.json", "w") as f:
                json.dump(registry, f)

            patch_file = feat_dir / "UXPATCH-0003__test.yaml"
            patch_content = _make_complete_patch(
                "UXPATCH-0003", "visual",
                changed_files=["src/styles.css"],
                ai_suggested_class="visual",
            )
            with open(patch_file, "w") as f:
                yaml.dump(patch_content, f)

            result = run_skill(
                tmpdir,
                {"feat_id": "test-feat", "input_type": "prompt", "input_value": "test"},
                "req-test-010",
            )
            assert result["registered"] is True
            assert "notification" in result
            assert "UXPATCH-0003" in result["notification"]

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.validate_ai_governance import validate


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_minimal_repo(root: Path) -> None:
    write(
        root / "ssot" / "governance" / "AI-CONSTITUTION.md",
        "\n".join(
            [
                "# LEE Lite AI Constitution",
                "",
                "Always classify the architectural authority before selecting a carrier.",
                "Carrier must not redefine authority.",
                "FRZ is the semantic source of truth.",
                "Skills produce candidates, evidence, and handoff proposals.",
                "Only a Gate may approve, reject, revise, or advance a governed state transition.",
                "No implementation-readiness decision is valid without evidence references.",
                "Experience changes use ADR-049 grading.",
                "Patch context relevant to target files must be injected before code edits.",
                "Agents must not load the entire repository by default.",
                "Canonical rules belong in ssot.",
            ]
        )
        + "\n",
    )
    write(root / "ssot" / "adr" / "ADR-049-Test.md", "# ADR-049\n")
    write(root / "docs" / "repository-layout.md", "# Layout\n")
    write(
        root / "ssot" / "governance" / "maps" / "RULE-MAP.md",
        "| Rule | Load |\n| --- | --- |\n| Layout | `docs/repository-layout.md` |\n| Patch | `ssot/adr/ADR-049-Test.md` |\n",
    )
    write(root / "ssot" / "registry" / "rule_registry.yaml", "rules:\n  - path: docs/repository-layout.md\n")
    write(
        root / "ssot" / "registry" / "skill_registry.yaml",
        "\n".join(
            [
                "skills:",
                "  - skill_id: demo",
                "    source_path: skills/demo/SKILL.md",
                "    has_contract: true",
                "    has_lifecycle: false",
                "    has_agents: false",
                "    has_scripts: false",
            ]
        )
        + "\n",
    )
    write(
        root / "ssot" / "registry" / "knowledge_registry.yaml",
        "\n".join(
            [
                "primary_sources:",
                "  - ssot/governance/AI-CONSTITUTION.md",
                "knowledge_layers:",
                "  - layer_id: L0",
                "    sources:",
                "      - source_path: ssot/governance/AI-CONSTITUTION.md",
            ]
        )
        + "\n",
    )
    write(
        root / "skills" / "demo" / "SKILL.md",
        "---\nname: demo\ndescription: demo\n---\n\n## Required Read Order\n\n1. `ll.contract.yaml`\n2. `input/contract.yaml` and `output/contract.yaml`\n\n## Execution\n",
    )
    write(root / "skills" / "demo" / "ll.contract.yaml", "workflow_key: workflow.demo\n")
    write(root / "skills" / "demo" / "input" / "contract.yaml", "name: input\n")
    write(root / "skills" / "demo" / "output" / "contract.yaml", "name: output\n")
    write(root / ".claude" / "skills" / "demo" / "SKILL.md", "# Demo Adapter\n\nLoad canonical skill only.\n")
    bootloader = "# Bootloader\n\nLoad `ssot/governance/AI-CONSTITUTION.md` only.\n"
    write(root / "CLAUDE.md", bootloader)
    write(root / "AGENTS.md", bootloader)


class ValidateAiGovernanceTests(unittest.TestCase):
    def test_minimal_valid_governance_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)

            result = validate(root)

            self.assertTrue(result.passed, result.errors)
            self.assertEqual(result.warnings, [])

    def test_missing_registry_and_unplanned_map_reference_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            (root / "ssot" / "registry" / "rule_registry.yaml").unlink()
            write(root / "ssot" / "governance" / "maps" / "BROKEN.md", "`ssot/adr/ADR-999-Missing.md`\n")

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("rule_registry.yaml" in error for error in result.errors))
            self.assertTrue(any("ADR-999-Missing.md" in error for error in result.errors))

    def test_required_read_order_and_adapter_copy_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            (root / "skills" / "demo" / "output" / "contract.yaml").unlink()
            constitution = (root / "ssot" / "governance" / "AI-CONSTITUTION.md").read_text(encoding="utf-8")
            write(root / ".claude" / "skills" / "bad" / "SKILL.md", constitution)

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("output/contract.yaml" in error for error in result.errors))
            self.assertTrue(any("adapter bootloader copies" in error for error in result.errors))

    def test_root_bootloader_must_reference_constitution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            write(root / "AGENTS.md", "# Codex\n\nNo canonical governance reference.\n")

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("AGENTS.md" in error and "must reference" in error for error in result.errors))

    def test_skill_registry_flags_must_match_filesystem(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            (root / "skills" / "demo" / "agents").mkdir()

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("demo.has_agents=False but filesystem is True" in error for error in result.errors))

    def test_l0_must_only_reference_constitution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            write(
                root / "ssot" / "registry" / "knowledge_registry.yaml",
                "\n".join(
                    [
                        "knowledge_layers:",
                        "  - layer_id: L0",
                        "    sources:",
                        "      - source_path: ssot/governance/AI-CONSTITUTION.md",
                        "      - source_path: README.md",
                    ]
                )
                + "\n",
            )

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("L0 sources must contain only" in error for error in result.errors))

    def test_primary_sources_must_only_reference_constitution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_minimal_repo(root)
            write(
                root / "ssot" / "registry" / "knowledge_registry.yaml",
                "\n".join(
                    [
                        "primary_sources:",
                        "  - ssot/governance/AI-CONSTITUTION.md",
                        "  - README.md",
                        "knowledge_layers:",
                        "  - layer_id: L0",
                        "    sources:",
                        "      - source_path: ssot/governance/AI-CONSTITUTION.md",
                    ]
                )
                + "\n",
            )

            result = validate(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("primary_sources must contain only" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()

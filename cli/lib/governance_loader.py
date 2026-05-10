"""Shared loader for LEE Lite AI governance files.

The loader intentionally centralizes paths only. It does not encode a second
copy of the constitution or registry rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - callers receive a clear error.
    yaml = None  # type: ignore[assignment]


CONSTITUTION_PATH = Path("ssot/governance/AI-CONSTITUTION.md")
MAPS_DIR = Path("ssot/governance/maps")
RULE_REGISTRY_PATH = Path("ssot/registry/rule_registry.yaml")
SKILL_REGISTRY_PATH = Path("ssot/registry/skill_registry.yaml")
KNOWLEDGE_REGISTRY_PATH = Path("ssot/registry/knowledge_registry.yaml")


@dataclass(frozen=True)
class GovernancePaths:
    constitution: Path
    maps_dir: Path
    rule_registry: Path
    skill_registry: Path
    knowledge_registry: Path


def resolve_repo_root(start: Path | str | None = None) -> Path:
    """Resolve the repository root by walking up to a .git directory."""

    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def governance_paths(repo_root: Path | str | None = None) -> GovernancePaths:
    root = resolve_repo_root(repo_root)
    return GovernancePaths(
        constitution=root / CONSTITUTION_PATH,
        maps_dir=root / MAPS_DIR,
        rule_registry=root / RULE_REGISTRY_PATH,
        skill_registry=root / SKILL_REGISTRY_PATH,
        knowledge_registry=root / KNOWLEDGE_REGISTRY_PATH,
    )


def load_constitution(repo_root: Path | str | None = None) -> str:
    path = governance_paths(repo_root).constitution
    return path.read_text(encoding="utf-8")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load governance registries")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_rule_registry(repo_root: Path | str | None = None) -> Any:
    return load_yaml(governance_paths(repo_root).rule_registry)


def load_skill_registry(repo_root: Path | str | None = None) -> Any:
    return load_yaml(governance_paths(repo_root).skill_registry)


def load_knowledge_registry(repo_root: Path | str | None = None) -> Any:
    return load_yaml(governance_paths(repo_root).knowledge_registry)


def list_maps(repo_root: Path | str | None = None) -> list[Path]:
    maps_dir = governance_paths(repo_root).maps_dir
    if not maps_dir.exists():
        return []
    return sorted(path for path in maps_dir.glob("*.md") if path.is_file())


def resolve_governance_ref(ref: str, repo_root: Path | str | None = None) -> Path:
    """Resolve a repository-relative governance reference.

    Fragment identifiers are ignored for filesystem resolution.
    """

    root = resolve_repo_root(repo_root)
    clean_ref = ref.split("#", 1)[0]
    return (root / clean_ref).resolve()

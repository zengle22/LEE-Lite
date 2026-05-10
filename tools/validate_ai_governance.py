from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - reported as a validation error.
    yaml = None  # type: ignore[assignment]


CONSTITUTION = Path("ssot/governance/AI-CONSTITUTION.md")
MAPS_DIR = Path("ssot/governance/maps")
REGISTRIES = (
    Path("ssot/registry/rule_registry.yaml"),
    Path("ssot/registry/skill_registry.yaml"),
    Path("ssot/registry/knowledge_registry.yaml"),
)
CONSTITUTION_REF = CONSTITUTION.as_posix()
ROOT_BOOTLOADERS = (Path("CLAUDE.md"), Path("AGENTS.md"))
ADAPTER_ROOTS = (Path(".claude"), Path(".agents"), Path(".cursor"))

ROOT_PREFIXES = (
    ".claude",
    ".agents",
    ".cursor",
    ".github",
    "artifacts",
    "cli",
    "docs",
    "e2e",
    "examples",
    "knowledge",
    "scripts",
    "skills",
    "ssot",
    "tests",
    "tools",
)

CODE_SPAN_RE = re.compile(r"`([^`]+)`")
PATH_RE = re.compile(
    r"(?<![\w:/\\])((?:\./)?(?:"
    + "|".join(re.escape(prefix) for prefix in ROOT_PREFIXES)
    + r")/[^\s`),\]\"'，。；：]+)"
)
DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
ADR_049_RE = re.compile(r"\bADR-049\b")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def resolve_repo_root(start: Path | str | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def normalize_ref(raw: str) -> str:
    ref = raw.strip().strip("<>").replace("\\", "/")
    return ref.rstrip(".,;:，。；：")


def is_planned_marker(text: str) -> bool:
    lowered = text.lower()
    return "planned" in lowered or "计划" in text


def is_repo_relative_ref(ref: str) -> bool:
    if not ref or "://" in ref or DRIVE_RE.match(ref):
        return False
    if any(token in ref for token in ("<", ">", "*", "?")):
        return False
    if "/." in ref.replace("\\", "/"):
        return False
    first = ref[2:] if ref.startswith("./") else ref
    return any(first == prefix or first.startswith(prefix + "/") for prefix in ROOT_PREFIXES)


def extract_refs(text: str) -> list[str]:
    refs: list[str] = []
    whole = normalize_ref(text)
    if is_repo_relative_ref(whole):
        return [whole]
    for match in CODE_SPAN_RE.finditer(text):
        candidate = normalize_ref(match.group(1))
        if is_repo_relative_ref(candidate):
            refs.append(candidate)
    text_without_code_spans = CODE_SPAN_RE.sub(" ", text)
    for match in PATH_RE.finditer(text_without_code_spans):
        candidate = normalize_ref(match.group(1))
        if is_repo_relative_ref(candidate):
            refs.append(candidate)
    return sorted(set(refs))


def display_source(source: Path, root: Path, line_number: int | None = None) -> str:
    try:
        rel = source.resolve().relative_to(root)
    except ValueError:
        rel = source
    if line_number is None:
        return rel.as_posix()
    return f"{rel.as_posix()}:{line_number}"


def ref_exists(root: Path, ref: str) -> bool:
    clean = normalize_ref(ref).split("#", 1)[0]
    if not clean:
        return True
    return (root / clean).exists()


def validate_ref(
    result: ValidationResult,
    root: Path,
    ref: str,
    source: Path,
    *,
    line_number: int | None = None,
    planned: bool = False,
) -> None:
    if ref_exists(root, ref):
        return
    where = display_source(source, root, line_number)
    if planned:
        result.warn(f"{where}: planned reference does not exist yet: {ref}")
        return
    result.error(f"{where}: referenced path does not exist: {ref}")


def load_yaml_file(path: Path) -> tuple[Any | None, str | None]:
    if yaml is None:
        return None, "PyYAML is required to parse governance registries"
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 - report parser failures directly.
        return None, str(exc)


def iter_yaml_strings(value: Any, planned: bool = False) -> Iterable[tuple[str, bool]]:
    if isinstance(value, dict):
        local_planned = planned or any(
            str(key).lower() in {"planned", "status", "state"}
            and is_planned_marker(str(item))
            for key, item in value.items()
        )
        for item in value.values():
            yield from iter_yaml_strings(item, local_planned)
    elif isinstance(value, list):
        for item in value:
            yield from iter_yaml_strings(item, planned)
    elif isinstance(value, str):
        yield value, planned or is_planned_marker(value)


def check_required_files(result: ValidationResult, root: Path) -> None:
    constitution = root / CONSTITUTION
    if not constitution.is_file():
        result.error(f"missing required constitution: {CONSTITUTION.as_posix()}")

    maps_dir = root / MAPS_DIR
    if not maps_dir.is_dir():
        result.error(f"missing governance maps directory: {MAPS_DIR.as_posix()}")
    elif not any(maps_dir.glob("*.md")):
        result.error(f"no governance map markdown files found under {MAPS_DIR.as_posix()}")

    for registry in REGISTRIES:
        path = root / registry
        if not path.is_file():
            result.error(f"missing required registry: {registry.as_posix()}")
            continue
        _, error = load_yaml_file(path)
        if error:
            result.error(f"{registry.as_posix()}: YAML parse failed: {error}")


def check_map_refs(result: ValidationResult, root: Path) -> None:
    maps_dir = root / MAPS_DIR
    if not maps_dir.is_dir():
        return
    for map_file in sorted(maps_dir.glob("*.md")):
        for line_number, line in enumerate(map_file.read_text(encoding="utf-8").splitlines(), 1):
            for ref in extract_refs(line):
                validate_ref(
                    result,
                    root,
                    ref,
                    map_file,
                    line_number=line_number,
                    planned=is_planned_marker(line),
                )


def check_registry_refs(result: ValidationResult, root: Path) -> None:
    for registry in REGISTRIES:
        path = root / registry
        if not path.is_file():
            continue
        data, error = load_yaml_file(path)
        if error:
            continue
        for text, planned in iter_yaml_strings(data):
            for ref in extract_refs(text):
                validate_ref(result, root, ref, path, planned=planned)


def check_knowledge_registry_l0(result: ValidationResult, root: Path) -> None:
    registry = root / "ssot" / "registry" / "knowledge_registry.yaml"
    if not registry.is_file():
        return
    data, error = load_yaml_file(registry)
    if error or not isinstance(data, dict):
        return

    primary_sources = data.get("primary_sources")
    if primary_sources is not None and primary_sources != [CONSTITUTION_REF]:
        result.error(
            "ssot/registry/knowledge_registry.yaml: primary_sources must contain only "
            f"{CONSTITUTION_REF}; found {primary_sources}"
        )

    layers = data.get("knowledge_layers")
    if not isinstance(layers, list):
        return

    for layer in layers:
        if not isinstance(layer, dict) or layer.get("layer_id") != "L0":
            continue
        sources = layer.get("sources")
        if not isinstance(sources, list):
            result.error("ssot/registry/knowledge_registry.yaml: L0 must define a sources list")
            return
        source_paths = [
            item.get("source_path")
            for item in sources
            if isinstance(item, dict)
        ]
        if source_paths != [CONSTITUTION_REF]:
            result.error(
                "ssot/registry/knowledge_registry.yaml: L0 sources must contain only "
                f"{CONSTITUTION_REF}; found {source_paths}"
            )
        return

    result.error("ssot/registry/knowledge_registry.yaml: missing L0 knowledge layer")


def check_adr_049_refs(result: ValidationResult, root: Path) -> None:
    adr_049_exists = any((root / "ssot" / "adr").glob("ADR-049*"))
    sources: list[Path] = []
    maps_dir = root / MAPS_DIR
    if maps_dir.is_dir():
        sources.extend(sorted(maps_dir.glob("*.md")))
    sources.extend((root / registry) for registry in REGISTRIES if (root / registry).is_file())

    for source in sources:
        text = source.read_text(encoding="utf-8")
        if ADR_049_RE.search(text) and not adr_049_exists:
            result.error(f"{display_source(source, root)}: ADR-049 is referenced but no ssot/adr/ADR-049* file exists")


def parse_required_read_order(skill_md: Path) -> list[str]:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    in_section = False
    refs: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip().lower() == "## required read order"
            continue
        if not in_section:
            continue
        for ref in CODE_SPAN_RE.findall(line):
            clean = normalize_ref(ref)
            if clean and not is_repo_relative_ref(clean) and not DRIVE_RE.match(clean):
                refs.append(clean)
    return sorted(set(refs))


def check_skill_required_read_order(result: ValidationResult, root: Path) -> None:
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        skill_root = skill_md.parent
        for ref in parse_required_read_order(skill_md):
            ref_name = Path(ref).name
            if "/" not in ref and "\\" not in ref and ref_name not in {"ll.contract.yaml", "ll.lifecycle.yaml"}:
                continue
            if any(token in ref for token in ("<", ">", "*", "?")) or DRIVE_RE.match(ref):
                continue
            if not (skill_root / ref).exists():
                result.error(
                    f"{display_source(skill_md, root)}: Required Read Order file does not exist: {ref}"
                )


def check_skill_registry_matches_filesystem(result: ValidationResult, root: Path) -> None:
    registry = root / "ssot" / "registry" / "skill_registry.yaml"
    if not registry.is_file():
        return
    data, error = load_yaml_file(registry)
    if error or not isinstance(data, dict):
        return

    skills = data.get("skills")
    if not isinstance(skills, list):
        return

    for item in skills:
        if not isinstance(item, dict):
            continue
        skill_id = item.get("skill_id", "<unknown>")
        source_path = item.get("source_path")
        if not isinstance(source_path, str):
            continue
        skill_root = (root / source_path).parent
        checks = {
            "has_contract": (skill_root / "ll.contract.yaml").exists(),
            "has_lifecycle": (skill_root / "ll.lifecycle.yaml").exists(),
            "has_agents": (skill_root / "agents").is_dir(),
            "has_scripts": (skill_root / "scripts").is_dir(),
        }

        for key, actual in checks.items():
            declared = item.get(key)
            if declared is not None and declared != actual:
                result.error(
                    "ssot/registry/skill_registry.yaml: "
                    f"{skill_id}.{key}={declared} but filesystem is {actual}"
                )


def normalized_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        clean = " ".join(line.strip().split())
        if len(clean) >= 20:
            lines.append(clean)
    return lines


def longest_common_run(haystack: list[str], needle: list[str]) -> int:
    positions: dict[str, list[int]] = {}
    for index, line in enumerate(needle):
        positions.setdefault(line, []).append(index)

    longest = 0
    for hay_index, line in enumerate(haystack):
        for needle_index in positions.get(line, []):
            run = 0
            while (
                hay_index + run < len(haystack)
                and needle_index + run < len(needle)
                and haystack[hay_index + run] == needle[needle_index + run]
            ):
                run += 1
            longest = max(longest, run)
    return longest


def check_bootloader_file(
    result: ValidationResult,
    root: Path,
    markdown: Path,
    constitution_lines: list[str],
    *,
    require_constitution_ref: bool,
) -> None:
    text = markdown.read_text(encoding="utf-8", errors="ignore")
    if require_constitution_ref and CONSTITUTION_REF not in text.replace("\\", "/"):
        result.error(
            f"{display_source(markdown, root)}: bootloader must reference {CONSTITUTION_REF}"
        )

    bootloader_lines = normalized_lines(text)
    run = longest_common_run(bootloader_lines, constitution_lines)
    if run >= 6:
        result.error(
            f"{display_source(markdown, root)}: adapter bootloader copies {run} consecutive constitution lines"
        )


def check_adapter_bootloaders(result: ValidationResult, root: Path) -> None:
    constitution_path = root / CONSTITUTION
    if not constitution_path.is_file():
        return
    constitution_lines = normalized_lines(constitution_path.read_text(encoding="utf-8"))
    if not constitution_lines:
        return

    for bootloader in ROOT_BOOTLOADERS:
        path = root / bootloader
        if not path.is_file():
            result.error(f"missing root bootloader: {bootloader.as_posix()}")
            continue
        check_bootloader_file(
            result,
            root,
            path,
            constitution_lines,
            require_constitution_ref=True,
        )

    for adapter_root in ADAPTER_ROOTS:
        base = root / adapter_root
        if not base.is_dir():
            continue
        for markdown in sorted(base.rglob("*.md")):
            check_bootloader_file(
                result,
                root,
                markdown,
                constitution_lines,
                require_constitution_ref=False,
            )


def validate(repo_root: Path | str | None = None) -> ValidationResult:
    root = resolve_repo_root(repo_root)
    result = ValidationResult()
    check_required_files(result, root)
    check_map_refs(result, root)
    check_registry_refs(result, root)
    check_knowledge_registry_l0(result, root)
    check_adr_049_refs(result, root)
    check_skill_required_read_order(result, root)
    check_skill_registry_matches_filesystem(result, root)
    check_adapter_bootloaders(result, root)
    return result


def print_result(result: ValidationResult) -> None:
    print(f"AI governance validation: {'PASS' if result.passed else 'FAIL'}")
    print()
    print("Errors:")
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
    else:
        print("- none")
    print()
    print("Warnings:")
    if result.warnings:
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("- none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate LEE Lite AI governance references.")
    parser.add_argument("--repo-root", default=None, help="Repository root. Defaults to the current git root.")
    args = parser.parse_args(argv)
    result = validate(args.repo_root)
    print_result(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())

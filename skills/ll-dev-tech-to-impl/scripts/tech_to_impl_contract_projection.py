#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from tech_to_impl_common import ensure_list, guess_repo_root_from_input, unique_strings
from tech_to_impl_derivation import filtered_implementation_rules, implementation_units, tech_list

FRONTEND_UNIT_MARKERS = {
    "ui",
    "page",
    "screen",
    "view",
    "frontend",
    "front-end",
    "routing",
    "router",
    "navigation",
    "component",
    "components",
    "form",
    "homepage",
    "home",
}
BACKEND_UNIT_MARKERS = {
    "handler",
    "service",
    "store",
    "repository",
    "repo",
    "schema",
    "state",
    "runtime",
    "gate",
    "workflow",
    "job",
    "queue",
    "worker",
    "api",
    "contract",
    "persistence",
    "storage",
    "db",
    "database",
    "sync",
    "submit",
}
SHARED_UNIT_MARKERS = {"shared", "common", "types", "contracts", "models", "domain"}
FRONTEND_ROOT_CANDIDATES = ["src/fe", "src/frontend", "frontend", "web", "app", "apps/web"]
BACKEND_ROOT_CANDIDATES = ["src/be", "src/backend", "backend", "server", "api", "apps/api"]
SHARED_ROOT_CANDIDATES = ["src/shared", "src/common", "shared", "common", "lib", "pkg"]
WORKFLOW_GOVERNING_ADR_REFS = ["ADR-034"]

ENGINEERING_BASELINE_AXIS = "engineering_baseline"
ENGINEERING_BASELINE_ALLOWED_ROOTS = ("apps/", "db/", "deploy/", "scripts/")
ENGINEERING_BASELINE_ALLOWED_ROOT_FILES = {"README.md", "AGENTS.md", "Makefile", ".env.example"}
ENGINEERING_BASELINE_FORBIDDEN_PARTS = {"src", "ssot", "artifacts", ".tmp", "tmp"}
IGNORED_REPO_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
    ".ico",
    ".pdf",
    ".md",
    ".txt",
    ".out",
}
NON_RUNTIME_REPO_PARTS = {
    "docs",
    "doc",
    "test-cases",
    "screenshots",
    "output",
    "__tests__",
    "e2e",
    "e2e-archive",
}
GENERIC_MATCH_TOKENS = {
    "src",
    "app",
    "apps",
    "home",
    "profile",
    "module",
    "modules",
    "unit",
    "units",
    "component",
    "components",
    "service",
    "handler",
    "store",
    "repository",
    "repo",
    "model",
    "models",
    "view",
    "page",
    "screen",
    "form",
}
IGNORED_REPO_PARTS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
    ".local",
}


def _ref_list(values: list[str]) -> list[str]:
    return unique_strings([str(item).strip() for item in values if str(item).strip()])


def _provisional_refs(feature: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    raw_refs = feature.get("provisional_refs")
    items = raw_refs if isinstance(raw_refs, list) else ensure_list(raw_refs)
    for item in items:
        if isinstance(item, dict):
            ref = str(item.get("ref") or "").strip()
            impact_scope = str(item.get("impact_scope") or "unspecified").strip()
            follow_up_action = str(item.get("follow_up_action") or "freeze_or_revise_before_execution").strip()
        else:
            ref = str(item).strip()
            impact_scope = "unspecified"
            follow_up_action = "freeze_or_revise_before_execution"
        if not ref:
            continue
        refs.append(
            {
                "ref": ref,
                "status": "provisional",
                "impact_scope": impact_scope,
                "follow_up_action": follow_up_action,
            }
        )
    return refs


def _repo_root_for_package(package: Any) -> Path:
    return guess_repo_root_from_input(package.artifacts_dir.resolve())


def _existing_or_default_root(repo_root: Path, candidates: list[str]) -> Path:
    for candidate in candidates:
        candidate_path = repo_root / candidate
        if candidate_path.exists():
            return Path(candidate)
    return Path(candidates[0])


def _surface_for_unit(unit: dict[str, str]) -> str:
    lowered = f"{unit.get('path', '')} {unit.get('detail', '')}".lower()
    if any(marker in lowered for marker in SHARED_UNIT_MARKERS):
        return "shared"
    if any(marker in lowered for marker in FRONTEND_UNIT_MARKERS):
        return "frontend"
    if any(marker in lowered for marker in BACKEND_UNIT_MARKERS):
        return "backend"
    first_segment = str(unit.get("path") or "").strip().split("/", 1)[0].lower()
    if first_segment in FRONTEND_UNIT_MARKERS:
        return "frontend"
    if first_segment in SHARED_UNIT_MARKERS:
        return "shared"
    return "backend"


def _preferred_root_for_surface(repo_root: Path, surface: str) -> Path:
    if surface == "frontend":
        return _existing_or_default_root(repo_root, FRONTEND_ROOT_CANDIDATES)
    if surface == "shared":
        return _existing_or_default_root(repo_root, SHARED_ROOT_CANDIDATES)
    return _existing_or_default_root(repo_root, BACKEND_ROOT_CANDIDATES)


def _normalized_unit_path(unit_path: str) -> str:
    cleaned = str(unit_path or "").replace("`", "").replace("\\", "/").strip().strip("/")
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    return cleaned


def _is_engineering_baseline(feature: dict[str, Any]) -> bool:
    resolved_axis = str(feature.get("resolved_axis") or feature.get("derived_axis") or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", resolved_axis.replace("-", "_").replace(" ", "_"))
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized == ENGINEERING_BASELINE_AXIS


def _is_allowed_engineering_baseline_repo_path(path: str) -> bool:
    normalized = _normalized_unit_path(path)
    if not normalized:
        return False

    if normalized in ENGINEERING_BASELINE_ALLOWED_ROOT_FILES:
        return True

    lowered = normalized.lower()
    if any(lowered.startswith(prefix) for prefix in ["src/", "src/be/", "src/fe/", "ssot/", "artifacts/", ".tmp/", "tmp/"]):
        return False

    parts = [part for part in lowered.split("/") if part]
    if any(part in ENGINEERING_BASELINE_FORBIDDEN_PARTS for part in parts):
        return False

    return any(normalized.startswith(root) for root in ENGINEERING_BASELINE_ALLOWED_ROOTS)


def _split_ambiguous_repo_paths(path: str) -> list[str]:
    candidate = _normalized_unit_path(path)
    if not candidate:
        return []
    parts = re.split(r"\s+(?:or|OR|或|或者)\s+", candidate)
    return unique_strings([part.strip() for part in parts if part.strip()]) or [candidate]


def _expand_engineering_baseline_repo_paths(axis_id: str, path: str) -> list[str]:
    normalized = _normalized_unit_path(path)
    if not normalized:
        return []

    expanded: list[str] = []
    for variant in _split_ambiguous_repo_paths(normalized):
        if "*" not in variant:
            expanded.append(variant)
            continue

        if variant in {"scripts/doctor/*", "scripts/doctor/*.*"} or variant.startswith("scripts/doctor/"):
            expanded.extend(["scripts/dev/doctor.ps1", "scripts/dev/doctor.sh"])
            continue
        if variant in {"scripts/dev/*", "scripts/dev/*.*"}:
            expanded.extend(["scripts/dev/doctor.ps1", "scripts/dev/doctor.sh"])
            continue

        if axis_id == "local-env" and variant in {"scripts/dev/*.ps1", "scripts/dev/*ps1"}:
            expanded.extend(["scripts/dev/up.ps1", "scripts/dev/down.ps1"])
            continue
        if axis_id == "local-env" and variant in {"scripts/dev/*.sh", "scripts/dev/*sh"}:
            expanded.extend(["scripts/dev/up.sh", "scripts/dev/down.sh"])
            continue

        if axis_id == "db-migrations" and variant in {"scripts/db/*.ps1", "scripts/db/*ps1"}:
            expanded.extend(["scripts/db/migrate-up.ps1", "scripts/db/migrate-down-one.ps1"])
            continue
        if axis_id == "db-migrations" and variant in {"scripts/db/*.sh", "scripts/db/*sh"}:
            expanded.extend(["scripts/db/migrate-up.sh", "scripts/db/migrate-down-one.sh"])
            continue

        if axis_id == "api-shell" and variant == "apps/api/internal/config/*":
            expanded.extend(["apps/api/internal/config/config.go", "apps/api/internal/config/env.go"])
            continue
        if axis_id == "api-shell" and variant == "apps/api/internal/infra/db/*":
            expanded.extend(["apps/api/internal/infra/db/pool.go"])
            continue
        if axis_id == "api-shell" and variant == "apps/api/internal/transport/httpapi/*":
            expanded.extend(
                [
                    "apps/api/internal/transport/httpapi/router.go",
                    "apps/api/internal/transport/httpapi/handler.go",
                ]
            )
            continue

        raise ValueError(
            "engineering_baseline touch point may not use wildcard or ambiguous repo path "
            f"without an explicit expansion rule; axis_id={axis_id!r} path={path!r} normalized={variant!r}"
        )

    return unique_strings([item for item in expanded if item])


def _repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized_search_tokens(tokens: list[str]) -> list[str]:
    unique_tokens = unique_strings([str(token).strip().lower() for token in tokens if str(token).strip()])
    meaningful = [
        token
        for token in unique_tokens
        if len(token) > 2 and token not in FRONTEND_UNIT_MARKERS and token not in BACKEND_UNIT_MARKERS and token not in SHARED_UNIT_MARKERS
    ]
    if meaningful:
        return meaningful
    fallback = [token for token in unique_tokens if len(token) > 2]
    return fallback or unique_tokens


def _match_priority_tokens(tokens: list[str]) -> list[str]:
    priority = [token for token in tokens if token not in GENERIC_MATCH_TOKENS]
    return priority or tokens


def _candidate_match_score(lower_rel: str, tokens: list[str]) -> tuple[int, int]:
    matched = [token for token in tokens if token in lower_rel]
    priority_hits = sum(1 for token in _match_priority_tokens(tokens) if token in lower_rel)
    return (priority_hits, len(matched))


def _is_runtime_candidate(candidate: Path) -> bool:
    if candidate.suffix.lower() in IGNORED_REPO_SUFFIXES:
        return False
    if any(part.lower() in NON_RUNTIME_REPO_PARTS for part in candidate.parts):
        return False
    return True


def _search_repo_candidates(repo_root: Path, search_root: Path, tokens: list[str], limit: int = 3) -> list[str]:
    if not search_root.exists() or not tokens:
        return []
    lowered_tokens = _normalized_search_tokens(tokens)
    if not lowered_tokens:
        return []
    required_matches = 2 if len(lowered_tokens) >= 2 else 1
    ranked_matches: list[tuple[tuple[int, int], str]] = []
    for candidate in search_root.rglob("*"):
        if any(part in IGNORED_REPO_PARTS for part in candidate.parts):
            continue
        if candidate.is_dir():
            continue
        if not _is_runtime_candidate(candidate):
            continue
        rel = _repo_relative(repo_root, candidate)
        lower_rel = rel.lower()
        score = _candidate_match_score(lower_rel, lowered_tokens)
        if score[1] < required_matches or score[0] == 0:
            continue
        ranked_matches.append((score, rel))
    ranked_matches.sort(key=lambda item: (-item[0][0], -item[0][1], len(item[1]), item[1]))
    return unique_strings([rel for _, rel in ranked_matches[:limit]])


def _repo_touch_points(package: Any, feature: dict[str, Any]) -> list[dict[str, Any]]:
    repo_root = _repo_root_for_package(package)
    points: list[dict[str, Any]] = []
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    for index, unit in enumerate(implementation_units(package), start=1):
        surface = _surface_for_unit(unit)
        normalized_unit_path = _normalized_unit_path(unit["path"])
        if _is_engineering_baseline(feature):
            expanded_paths = _expand_engineering_baseline_repo_paths(axis_id, normalized_unit_path)
            if not expanded_paths:
                raise ValueError(
                    "engineering_baseline touch point must remain inside frozen allowlist roots "
                    f"{ENGINEERING_BASELINE_ALLOWED_ROOTS} or {sorted(ENGINEERING_BASELINE_ALLOWED_ROOT_FILES)}; "
                    f"got unit_path={unit['path']!r} normalized={normalized_unit_path!r}"
                )
            for path in expanded_paths:
                if not _is_allowed_engineering_baseline_repo_path(path):
                    raise ValueError(
                        "engineering_baseline touch point must remain inside frozen allowlist roots "
                        f"{ENGINEERING_BASELINE_ALLOWED_ROOTS} or {sorted(ENGINEERING_BASELINE_ALLOWED_ROOT_FILES)}; "
                        f"got unit_path={unit['path']!r} normalized={path!r}"
                    )
                points.append(
                    {
                        "touch_ref": f"TOUCH-{len(points)+1:03d}",
                        "unit_path": path,
                        "surface": surface,
                        "mode": unit["mode"],
                        "detail": unit["detail"],
                        "repo_paths": [path],
                        "primary_repo_path": path,
                        "placement_status": "authoritative_frozen_path",
                    }
                )
            continue
        else:
            preferred_root = _preferred_root_for_surface(repo_root, surface)
            default_repo_path = (preferred_root / normalized_unit_path).as_posix()
            search_root = repo_root / preferred_root if (repo_root / preferred_root).exists() else repo_root
            search_tokens = [token for token in re.split(r"[_/.\-]+", normalized_unit_path) if token]
            existing_matches = _search_repo_candidates(repo_root, search_root, search_tokens)
            repo_paths = existing_matches or [default_repo_path]
            placement_status = "existing_match" if existing_matches else "proposed_new_module"
        points.append(
            {
                "touch_ref": f"TOUCH-{index:03d}",
                "unit_path": unit["path"],
                "surface": surface,
                "mode": unit["mode"],
                "detail": unit["detail"],
                "repo_paths": repo_paths,
                "primary_repo_path": repo_paths[0],
                "placement_status": placement_status,
            }
        )
    return points


def _format_touch_point(point: dict[str, Any]) -> str:
    extra_paths = [path for path in point.get("repo_paths", []) if path != point.get("primary_repo_path")]
    extra_text = f"; nearby matches: {', '.join(extra_paths)}" if extra_paths else ""
    return (
        f"`{point['primary_repo_path']}` [{point['surface']} | {point['mode']} | {point['placement_status']}] "
        f"<- `{point['unit_path']}`: {point['detail']}{extra_text}"
    )


def _first_existing_ref(repo_root: Path, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if not pattern:
            continue
        for candidate in sorted(repo_root.glob(pattern)):
            if candidate.is_file():
                ref = candidate.stem.split("__", 1)[0].strip()
                if ref:
                    return ref
    return None


def _expected_ui_ref(feature: dict[str, Any]) -> str | None:
    feat_ref = str(feature.get("feat_ref") or "").strip()
    return f"UI-{feat_ref}" if feat_ref.startswith("FEAT-") else None


def _expected_testset_ref(feature: dict[str, Any]) -> str | None:
    feat_ref = str(feature.get("feat_ref") or "").strip()
    return feat_ref.replace("FEAT-", "TESTSET-", 1) if feat_ref.startswith("FEAT-") else None


def _discover_optional_authority_refs(repo_root: Path, feature: dict[str, Any]) -> dict[str, str | None]:
    expected_ui_ref = _expected_ui_ref(feature)
    expected_testset_ref = _expected_testset_ref(feature)
    ui_ref = _first_existing_ref(
        repo_root,
        [
            f"ssot/ui/**/*{expected_ui_ref}*.md" if expected_ui_ref else "",
            f"ssot/ui/**/*{feature.get('feat_ref') or ''}*.md",
        ],
    )
    testset_ref = _first_existing_ref(
        repo_root,
        [
            f"ssot/testset/{expected_testset_ref}__*" if expected_testset_ref else "",
            f"ssot/testset/*{feature.get('feat_ref') or ''}*",
        ],
    )
    return {"ui_ref": ui_ref, "testset_ref": testset_ref}


def resolve_selected_upstream_refs(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    source_refs: list[str],
    repo_root: Path,
) -> dict[str, Any]:
    discovered = _discover_optional_authority_refs(repo_root, feature)
    return {
        "adr_refs": _ref_list(list(WORKFLOW_GOVERNING_ADR_REFS) + [item for item in source_refs if item.startswith("ADR-")]),
        "src_ref": next((item for item in source_refs if item.startswith("SRC-")), ""),
        "epic_ref": next((item for item in source_refs if item.startswith("EPIC-")), ""),
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "ui_ref": str(feature.get("ui_ref") or "").strip() or discovered["ui_ref"],
        "testset_ref": str(feature.get("testset_ref") or "").strip() or discovered["testset_ref"],
    }


def build_selected_upstream_refs(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    source_refs: list[str],
    repo_root: Path,
) -> dict[str, Any]:
    return resolve_selected_upstream_refs(feature, refs, source_refs, repo_root)


def _testset_package_path(repo_root: Path, testset_ref: str, feat_ref: str) -> Path | None:
    patterns = [
        f"ssot/testset/{testset_ref}__*.yaml" if testset_ref else "",
        f"ssot/testset/{testset_ref}__*.yml" if testset_ref else "",
        f"ssot/testset/*{feat_ref}*.yaml" if feat_ref else "",
        f"ssot/testset/*{feat_ref}*.yml" if feat_ref else "",
    ]
    for pattern in patterns:
        if not pattern:
            continue
        matches = sorted(repo_root.glob(pattern))
        if matches:
            return matches[0]
    return None


def _testset_unit_refs_by_acceptance(repo_root: Path, selected_upstream_refs: dict[str, Any]) -> dict[str, list[str]]:
    testset_ref = str(selected_upstream_refs.get("testset_ref") or "").strip()
    feat_ref = str(selected_upstream_refs.get("feat_ref") or "").strip()
    package_path = _testset_package_path(repo_root, testset_ref, feat_ref)
    if package_path is None or not package_path.exists():
        return {}
    try:
        payload = yaml.safe_load(package_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(payload, dict):
        return {}

    mappings: dict[str, list[str]] = {}
    for row in payload.get("acceptance_traceability") or []:
        if not isinstance(row, dict):
            continue
        acceptance_ref = str(row.get("acceptance_ref") or "").strip()
        unit_refs = unique_strings(ensure_list(row.get("unit_refs")))
        if acceptance_ref and unit_refs:
            mappings[acceptance_ref] = unit_refs

    for row in payload.get("test_units") or []:
        if not isinstance(row, dict):
            continue
        acceptance_ref = str(row.get("acceptance_ref") or "").strip()
        unit_ref = str(row.get("unit_ref") or "").strip()
        if not acceptance_ref or not unit_ref:
            continue
        mappings.setdefault(acceptance_ref, [])
        if unit_ref not in mappings[acceptance_ref]:
            mappings[acceptance_ref].append(unit_ref)
    return mappings


def _acceptance_ref_aliases(acceptance_ref: str, feat_ref: str) -> list[str]:
    ref = str(acceptance_ref or "").strip()
    feature = str(feat_ref or "").strip()
    aliases = [ref]
    short_ref = ref
    if feature and ref.startswith(f"{feature}-"):
        short_ref = ref[len(feature) + 1 :]
        aliases.append(short_ref)
    match = re.search(r"AC-(\d+)$", short_ref)
    if match:
        number = int(match.group(1))
        short_variants = unique_strings([f"AC-{number:02d}", f"AC-{number:03d}"])
        aliases.extend(short_variants)
        if feature:
            aliases.extend([f"{feature}-{variant}" for variant in short_variants])
    elif feature and short_ref.startswith("AC-"):
        aliases.append(f"{feature}-{short_ref}")
    return unique_strings([item for item in aliases if item])


def _scope_boundary(feature: dict[str, Any], package: Any) -> dict[str, list[str]]:
    in_scope = unique_strings(
        ensure_list(feature.get("scope"))[:4]
        + [f"{unit['path']} ({unit['mode']})" for unit in implementation_units(package)[:4]]
    )
    out_of_scope = unique_strings(
        ensure_list(feature.get("non_goals"))[:4]
        + [
            "Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.",
            "Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.",
            "Do not expand touch set beyond declared modules without re-derive or revision review.",
        ]
    )
    return {"in_scope": in_scope[:6], "out_of_scope": out_of_scope[:6]}


def _upstream_impacts(
    feature: dict[str, Any],
    package: Any,
    selected_upstream_refs: dict[str, Any],
    checkpoints: list[dict[str, str]],
    provisional_refs: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    tech_focus = unique_strings(tech_list(package, "design_focus")[:2] + filtered_implementation_rules(package)[:2])
    interface_contracts = unique_strings(tech_list(package, "interface_contracts")[:2])
    expected_ui_ref = _expected_ui_ref(feature)
    expected_testset_ref = _expected_testset_ref(feature)
    engineering_baseline = _is_engineering_baseline(feature)
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    ui_ref = selected_upstream_refs["ui_ref"]
    if engineering_baseline and axis_id == "miniapp-shell" and not ui_ref:
        ui_ref = "embedded_execution_contract_sufficient"
    return {
        "adr": {
            "refs": selected_upstream_refs["adr_refs"],
            "impact": "Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.",
        },
        "src_epic_feat": {
            "src_ref": selected_upstream_refs["src_ref"],
            "epic_ref": selected_upstream_refs["epic_ref"],
            "feat_ref": selected_upstream_refs["feat_ref"],
            "impact": str(feature.get("goal") or "").strip(),
        },
        "tech": {
            "ref": selected_upstream_refs["tech_ref"],
            "impact_items": tech_focus,
        },
        "arch": {
            "ref": selected_upstream_refs["arch_ref"],
            "impact": "Architecture boundaries constrain layering, ownership, and runtime attachment points."
            if selected_upstream_refs["arch_ref"]
            else "No explicit ARCH ref selected for this run.",
        },
        "api": {
            "ref": selected_upstream_refs["api_ref"],
            "impact_items": interface_contracts if selected_upstream_refs["api_ref"] else [],
            "impact": "API contract changes remain governed by upstream API truth."
            if selected_upstream_refs["api_ref"]
            else "No explicit API ref selected for this run.",
        },
        "ui": {
            "ref": ui_ref,
            "impact": (
                "Engineering baseline miniapp shell is limited to minimal skeleton + healthz debug verification surface; "
                "embedded execution contract is sufficient and missing external UI authority must not block execution."
                if engineering_baseline and axis_id == "miniapp-shell" and ui_ref == "embedded_execution_contract_sufficient"
                else (
                    f"UI constraints remain inherited from {ui_ref} and cannot be redefined in IMPL."
                    if ui_ref
                    else f"No explicit UI ref selected and no accepted UI authority was discoverable for `{feature.get('feat_ref')}` (expected `{expected_ui_ref or 'UI ref'}`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised."
                )
            ),
            "provisional": any(item["ref"] == ui_ref for item in provisional_refs) if ui_ref else False,
        },
        "testset": {
            "ref": selected_upstream_refs["testset_ref"],
            "impact": (
                f"Acceptance and evidence must remain mapped to {selected_upstream_refs['testset_ref']}."
                + (
                    " This TESTSET is currently provisional and must be refreshed or re-frozen before final execution."
                    if any(item["ref"] == selected_upstream_refs["testset_ref"] for item in provisional_refs)
                    else ""
                )
                if selected_upstream_refs["testset_ref"]
                else f"No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `{feature.get('feat_ref')}` (expected `{expected_testset_ref or 'TESTSET ref'}`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff."
            ),
            "acceptance_refs": [item["ref"] for item in checkpoints],
        },
    }


def _authority_binding_entry(
    authority: str,
    *,
    ref: str | None = None,
    refs: list[str] | None = None,
    status: str,
    required_for: str,
    execution_effect: str,
    follow_up_action: str | None = None,
    expected_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "authority": authority,
        "ref": ref,
        "refs": refs or [],
        "status": status,
        "required_for": required_for,
        "execution_effect": execution_effect,
        "follow_up_action": follow_up_action or "none",
        "expected_ref": expected_ref,
    }


def _authority_binding_status(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    selected_upstream_refs: dict[str, Any],
    provisional_refs: list[dict[str, str]],
) -> list[dict[str, Any]]:
    provisional_index = {str(item.get("ref") or "").strip(): item for item in provisional_refs}
    engineering_baseline = _is_engineering_baseline(feature)
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    adr_refs = ensure_list(selected_upstream_refs.get("adr_refs"))
    entries = [
        _authority_binding_entry(
            "ADR",
            refs=adr_refs,
            status="bound" if adr_refs else "missing",
            required_for="execution-bundle governance and authority precedence",
            execution_effect="coder/tester inherit execution-bundle governance from frozen ADR refs",
            follow_up_action="attach governing ADR before execution" if not adr_refs else "none",
            expected_ref="ADR-034",
        ),
        _authority_binding_entry(
            "ARCH",
            ref=selected_upstream_refs.get("arch_ref"),
            status="bound" if selected_upstream_refs.get("arch_ref") else "not_selected",
            required_for="layering and ownership constraints when ARCH applies",
            execution_effect="IMPL inherits architecture boundaries only when ARCH was selected upstream",
        ),
        _authority_binding_entry(
            "API",
            ref=selected_upstream_refs.get("api_ref"),
            status="bound" if selected_upstream_refs.get("api_ref") else "not_selected",
            required_for="interface contract snapshots and response invariants when API applies",
            execution_effect="IMPL inherits API truth only when API was selected upstream",
        ),
    ]
    for authority, ref_key, expected_ref, required_for, execution_effect, missing_action in [
        (
            "UI",
            "ui_ref",
            _expected_ui_ref(feature),
            "UI entry/exit constraints and user-facing acceptance wording",
            "coder may rely on embedded UI contract only within the declared IMPL boundary",
            "freeze_or_revise_ui_before_final_execution",
        ),
        (
            "TESTSET",
            "testset_ref",
            _expected_testset_ref(feature),
            "acceptance truth, evidence collection, and tester alignment",
            "acceptance trace remains a proxy until TESTSET authority is frozen",
            "freeze_or_revise_testset_before_final_execution",
        ),
    ]:
        if authority == "UI" and engineering_baseline and axis_id != "miniapp-shell":
            ref = str(selected_upstream_refs.get(ref_key) or "").strip() or None
            entries.append(
                _authority_binding_entry(
                    authority,
                    ref=ref,
                    status="bound" if ref else "not_selected",
                    required_for="engineering baseline non-UI slice execution",
                    execution_effect="UI authority is not required for this slice; do not block execution on missing UI.",
                    follow_up_action="none",
                    expected_ref=expected_ref,
                )
            )
            continue
        if authority == "UI" and engineering_baseline and axis_id == "miniapp-shell":
            ref = str(selected_upstream_refs.get(ref_key) or "").strip() or None
            if ref:
                entries.append(
                    _authority_binding_entry(
                        authority,
                        ref=ref,
                        status="bound",
                        required_for=required_for,
                        execution_effect=execution_effect,
                        follow_up_action="none",
                        expected_ref=expected_ref,
                    )
                )
            else:
                entries.append(
                    _authority_binding_entry(
                        authority,
                        ref="embedded_execution_contract_sufficient",
                        status="not_selected",
                        required_for="engineering baseline miniapp shell (minimal skeleton + healthz debug verification)",
                        execution_effect="Embedded execution contract is sufficient for this slice; do not block execution on missing external UI SSOT.",
                        follow_up_action="none",
                        expected_ref=expected_ref,
                    )
                )
            continue
        ref = str(selected_upstream_refs.get(ref_key) or "").strip() or None
        provisional_item = provisional_index.get(ref or "")
        if provisional_item:
            status = "provisional"
            follow_up_action = provisional_item.get("follow_up_action") or missing_action
        elif ref:
            status = "bound"
            follow_up_action = "none"
        else:
            status = "missing"
            follow_up_action = missing_action
        entries.append(
            _authority_binding_entry(
                authority,
                ref=ref,
                status=status,
                required_for=required_for,
                execution_effect=execution_effect,
                follow_up_action=follow_up_action,
                expected_ref=expected_ref,
            )
        )
    return entries


def _authority_gap_register(authority_binding_status: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in authority_binding_status
        if str(item.get("status") or "") in {"missing", "provisional"}
    ]


def _boundary_items(package: Any, scope_boundary: dict[str, list[str]]) -> list[str]:
    optional_arch = package.tech_json.get("optional_arch") or {}
    optional_api = package.tech_json.get("optional_api") or {}
    return unique_strings(
        ensure_list(optional_arch.get("topics"))[:4]
        + ensure_list(optional_api.get("compatibility_rules"))[:3]
        + ensure_list(scope_boundary.get("out_of_scope"))[:3]
    )


def _embedded_execution_contract(
    feature: dict[str, Any],
    package: Any,
    refs: dict[str, str | None],
    scope_boundary: dict[str, list[str]],
    checkpoints: list[dict[str, str]],
) -> dict[str, Any]:
    integration_points = tech_list(package, "integration_points")
    exception_items = tech_list(package, "exception_and_compensation")
    main_sequence = tech_list(package, "main_sequence")
    return {
        "state_machine": tech_list(package, "state_model"),
        "api_contracts": tech_list(package, "interface_contracts")
        if refs.get("api_ref") or tech_list(package, "interface_contracts")
        else [],
        "ui_entry_exit": {
            "entry": integration_points[:2] or ensure_list(feature.get("scope"))[:2],
            "success_exit": ([main_sequence[-1]] if main_sequence else []) or [str(feature.get("goal") or "").strip()],
            "failure_exit": exception_items[:2]
            or ["Failure handling must stay inside the declared FEAT boundary and cannot bypass acceptance checks."],
        },
        "invariants": unique_strings(filtered_implementation_rules(package) + ensure_list(feature.get("constraints")))[:8],
        "boundaries": _boundary_items(package, scope_boundary)[:8],
        "acceptance_checks": [
            {
                "acceptance_ref": item["ref"],
                "scenario": item["scenario"],
                "expectation": item["expectation"],
            }
            for item in checkpoints
        ],
    }


def _change_controls(package: Any, repo_touch_points: list[dict[str, Any]], scope_boundary: dict[str, list[str]]) -> dict[str, list[str]]:
    touch_set = [_format_touch_point(point) for point in repo_touch_points]
    boundary_items = _boundary_items(package, scope_boundary)
    return {
        "touch_set": touch_set[:10],
        "allowed_changes": [
            "Implement only the declared repo touch points and governed evidence/handoff artifacts.",
            "Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.",
            "Create new modules only at the declared repo touch points when no existing match is available.",
        ],
        "forbidden_changes": unique_strings(
            [
                "Modify modules outside the declared repo touch points without re-derive or explicit revision approval.",
                "Invent new requirements or redefine design truth in IMPL.",
                "Use repo current shape as silent override of upstream frozen objects.",
            ]
            + [f"Boundary guardrail: {item}" for item in boundary_items[:3]]
        )[:6],
    }


def _task(
    step_id: str,
    title: str,
    objective: str,
    inputs: list[str],
    touch_points: list[str],
    outputs: list[str],
    depends_on: list[str],
    parallelizable_with: list[str],
    acceptance_refs: list[str],
    done_when: str,
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "title": title,
        "objective": objective,
        "inputs": unique_strings(inputs),
        "touch_points": unique_strings(touch_points),
        "outputs": unique_strings(outputs),
        "depends_on": unique_strings(depends_on),
        "parallelizable_with": unique_strings(parallelizable_with),
        "acceptance_refs": unique_strings(acceptance_refs),
        "done_when": done_when,
    }


def _implementation_task_breakdown(
    feature: dict[str, Any],
    package: Any,
    assessment: dict[str, Any],
    checkpoints: list[dict[str, str]],
    repo_touch_points: list[dict[str, Any]],
    execution_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    if _is_engineering_baseline(feature):
        del package, assessment, execution_contract
        acceptance_refs = [item["ref"] for item in checkpoints]
        axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()

        def _accepts(*refs: str) -> list[str]:
            selected = [ref for ref in refs if ref in acceptance_refs]
            return selected or (acceptance_refs[:1] if acceptance_refs else [])

        def _paths(prefixes: tuple[str, ...] | None = None) -> list[str]:
            if not prefixes:
                return [point["primary_repo_path"] for point in repo_touch_points]
            return [
                point["primary_repo_path"]
                for point in repo_touch_points
                if any(str(point["primary_repo_path"]).startswith(prefix) for prefix in prefixes)
            ]

        all_paths = _paths()

        if axis_id == "repo-layout-baseline":
            doc_paths = _paths(("README.md", "AGENTS.md")) or all_paths
            script_paths = _paths(("scripts/",)) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Freeze repo root rules and legacy src guard",
                    objective="Write/update root governance docs that freeze: allowed roots for new code, root allow/deny rules, and `src/` legacy no-growth constraint.",
                    inputs=["FEAT/TECH frozen scope", "repo root allow/deny rules"],
                    touch_points=doc_paths,
                    outputs=["README.md", "AGENTS.md"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="README/AGENTS explain where new code may land and explicitly forbid incremental development under `src/`.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Add repo doctor check for root violations",
                    objective="Add a deterministic check (script and/or Makefile target) that detects forbidden roots and disallowed new source placement.",
                    inputs=["README/AGENTS rules", "doctor check criteria"],
                    touch_points=script_paths,
                    outputs=["doctor check entrypoint", "violation output"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002"),
                    done_when="A contributor can run a single command to detect root layout violations (including `src/` growth).",
                ),
                _task(
                    step_id="TASK-003",
                    title="Verify repo layout enforcement evidence",
                    objective="Run the doctor check against a known-good tree (and at least one intentional violation) and capture evidence for review.",
                    inputs=["doctor command", "acceptance trace"],
                    touch_points=[],
                    outputs=["doctor evidence", "acceptance evidence"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence demonstrates the repo layout guardrails are enforceable and reproducible.",
                ),
            ]

        if axis_id == "api-shell":
            api_paths = _paths(("apps/api/", "Makefile", "scripts/")) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Create runnable Go API shell skeleton",
                    objective="Create the minimal Go module + server entrypoint and freeze the directory skeleton declared by TECH.",
                    inputs=["Go runtime constraints", "TECH implementation unit mapping"],
                    touch_points=api_paths,
                    outputs=["apps/api skeleton", "server entrypoint"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="`apps/api` can start a minimal server from a single entrypoint and directory boundaries are explicit.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Freeze API dev entrypoint command",
                    objective="Expose a stable local dev entrypoint (Makefile/script) to start the API shell and ensure it does not violate layering rules (handlers no raw SQL).",
                    inputs=["Makefile target contract", "layering constraints"],
                    touch_points=api_paths,
                    outputs=["api-dev entrypoint", "startup documentation"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002"),
                    done_when="A new contributor can run a single command to start the API shell without additional manual steps.",
                ),
                _task(
                    step_id="TASK-003",
                    title="Verify API shell starts and is probe-ready",
                    objective="Start the API via the frozen entrypoint and verify the declared probe routes are mounted (semantics remain owned by the health slice).",
                    inputs=["api-dev entrypoint", "curl/http client"],
                    touch_points=[],
                    outputs=["startup evidence", "route mount evidence"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence shows the API starts consistently and exposes the expected probe endpoints for downstream health contract wiring.",
                ),
            ]

        if axis_id == "miniapp-shell":
            miniapp_paths = _paths(("apps/miniapp/", "Makefile", "scripts/")) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Create minimal UniApp miniapp skeleton",
                    objective="Create `apps/miniapp` skeleton with frozen router/page layout so the project can start deterministically.",
                    inputs=["TECH implementation unit mapping", "miniapp scaffold constraints"],
                    touch_points=miniapp_paths,
                    outputs=["apps/miniapp skeleton", "minimal route/page"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="`apps/miniapp` exists with minimal runnable routing and a stable start command can be defined.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Add /healthz connectivity verification surface",
                    objective="Implement a debug verification page/button that calls backend `GET /healthz` and displays success/failure explicitly.",
                    inputs=["backend /healthz endpoint availability", "miniapp service wrapper"],
                    touch_points=miniapp_paths,
                    outputs=["debug healthz page", "verification UX"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-002"),
                    done_when="A deterministic, documented miniapp path exists to validate backend connectivity via `/healthz`.",
                ),
                _task(
                    step_id="TASK-003",
                    title="Freeze miniapp dev command and verification steps",
                    objective="Document and expose a stable miniapp dev entrypoint (e.g. `make miniapp-dev`) plus the verification steps for `/healthz`.",
                    inputs=["miniapp start command", "verification procedure"],
                    touch_points=miniapp_paths,
                    outputs=["miniapp README", "dev entrypoint"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002"),
                    done_when="Contributors can start the miniapp and reproduce the `/healthz` verification without tribal knowledge.",
                ),
                _task(
                    step_id="TASK-004",
                    title="Capture miniapp verification evidence",
                    objective="Run the documented verification path and capture evidence suitable for the TESTSET mapping (screenshot/log).",
                    inputs=["verification steps", "acceptance trace"],
                    touch_points=[],
                    outputs=["verification evidence"],
                    depends_on=["TASK-003"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence demonstrates the miniapp can reach backend `/healthz` via the debug verification surface.",
                ),
            ]

        if axis_id == "local-env":
            env_paths = _paths(("deploy/", ".env.example", "Makefile", "scripts/")) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Deliver docker-compose local Postgres entrypoint",
                    objective="Create `deploy/docker-compose.local.yml` that starts a local Postgres with durable volume and predictable ports.",
                    inputs=["Postgres config contract", "compose entrypoint constraints"],
                    touch_points=env_paths,
                    outputs=["deploy/docker-compose.local.yml"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="Compose file exists and can start Postgres via a stable entrypoint.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Freeze local env vars and dev up/down/doctor commands",
                    objective="Provide `.env.example` and stable entrypoints (`make dev-up/dev-down/doctor` or equivalent) without committing secrets.",
                    inputs=["env var contract", "Makefile/script targets"],
                    touch_points=env_paths,
                    outputs=[".env.example", "dev-up/dev-down/doctor entrypoints"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002"),
                    done_when="A new contributor can boot/stop local Postgres and run doctor checks with a single command.",
                ),
                _task(
                    step_id="TASK-003",
                    title="Verify local env up/down symmetry evidence",
                    objective="Run dev-up then dev-down and capture evidence that services start/stop predictably and ports/volumes behave as expected.",
                    inputs=["dev-up/dev-down entrypoints", "acceptance trace"],
                    touch_points=[],
                    outputs=["up/down evidence", "doctor evidence"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence shows local env can be started and stopped symmetrically on a fresh clone without manual fixes.",
                ),
            ]

        if axis_id == "db-migrations":
            mig_paths = _paths(("db/migrations/", "Makefile", "scripts/db/")) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Deliver migrations directory and initial 0001 init",
                    objective="Create `db/migrations` with the first executable init migration (up/down) as the only schema evolution channel.",
                    inputs=["migration naming rules", "initial schema requirements"],
                    touch_points=mig_paths,
                    outputs=["db/migrations/0001_init.up.sql", "db/migrations/0001_init.down.sql"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="A clean database can apply the initial migration and schema evolution is forced through `db/migrations`.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Freeze migrate up/down execution entrypoints",
                    objective="Expose stable commands (Makefile/scripts) for migrate up and rollback-one, and document the no-manual-DB-changes rule.",
                    inputs=["runner entrypoint contract", "rollback discipline"],
                    touch_points=mig_paths,
                    outputs=["db-migrate-up entrypoint", "db-migrate-down-one entrypoint"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002", "AC-003"),
                    done_when="Migration apply/rollback commands are frozen and do not require ad-hoc SQL in runtime handlers.",
                ),
                _task(
                    step_id="TASK-003",
                    title="Verify migration apply and rollback evidence",
                    objective="On an empty DB: run migrate up, validate expected objects exist, then run rollback-one and capture evidence.",
                    inputs=["migrate entrypoints", "acceptance trace"],
                    touch_points=[],
                    outputs=["migration evidence", "rollback evidence"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence shows migrations are the sole schema evolution channel and rollback works at the declared minimum granularity.",
                ),
            ]

        if axis_id == "health-readiness":
            health_paths = _paths(("apps/api/",)) or all_paths
            return [
                _task(
                    step_id="TASK-001",
                    title="Implement /healthz contract hook",
                    objective="Implement the `GET /healthz` handler contract: process liveness only (must not depend on DB).",
                    inputs=["TECH contract", "router mount point"],
                    touch_points=health_paths,
                    outputs=["healthz handler", "healthz route mount"],
                    depends_on=[],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001"),
                    done_when="`/healthz` returns deterministically and does not require DB connectivity.",
                ),
                _task(
                    step_id="TASK-002",
                    title="Implement /readyz contract hook with DB probe",
                    objective="Implement the `GET /readyz` handler contract: readiness depends on injected dependency probes (at least DB).",
                    inputs=["DB probe interface", "timeout/error mapping rules"],
                    touch_points=health_paths,
                    outputs=["readyz handler", "DB probe wiring"],
                    depends_on=["TASK-001"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts("AC-001", "AC-002"),
                    done_when="`/readyz` reflects dependency readiness and cleanly reports failures as 503 with a stable JSON envelope.",
                ),
                _task(
                    step_id="TASK-003",
                    title="Verify health/readiness behavior evidence",
                    objective="Use curl (or equivalent) to capture evidence for both healthy and unhealthy readiness scenarios (e.g., DB down).",
                    inputs=["api-dev entrypoint", "curl/http client"],
                    touch_points=[],
                    outputs=["health evidence", "ready evidence"],
                    depends_on=["TASK-002"],
                    parallelizable_with=[],
                    acceptance_refs=_accepts(*acceptance_refs),
                    done_when="Evidence shows `/healthz` and `/readyz` meet the frozen status code and JSON contract expectations.",
                ),
            ]

        return [
            _task(
                step_id="TASK-001",
                title="Implement declared engineering baseline touch set",
                objective="Implement only the frozen engineering baseline touch points for this slice (no `src/` growth, no `.tmp/`, no `ssot/` writes).",
                inputs=["TECH implementation units", "frozen allowlist roots"],
                touch_points=all_paths,
                outputs=["declared touch points"],
                depends_on=[],
                parallelizable_with=[],
                acceptance_refs=_accepts(*acceptance_refs),
                done_when="All declared touch points exist at their frozen repo-relative paths and can be verified independently.",
            )
        ]

    del feature, package, execution_contract
    acceptance_refs = [item["ref"] for item in checkpoints]
    frontend_paths = [point["primary_repo_path"] for point in repo_touch_points if point["surface"] == "frontend"]
    backend_paths = [point["primary_repo_path"] for point in repo_touch_points if point["surface"] == "backend"]
    shared_paths = [point["primary_repo_path"] for point in repo_touch_points if point["surface"] == "shared"]
    all_paths = [point["primary_repo_path"] for point in repo_touch_points]
    tasks: list[dict[str, Any]] = [
        _task(
            step_id="TASK-001",
            title="Freeze refs and repo touch points",
            objective="Lock selected FEAT / TECH / optional ARCH / API refs, freeze repo-aware placement, and forbid implementation drift before coding starts.",
            inputs=["selected_upstream_refs", "source_refs", "repo_root"],
            touch_points=all_paths,
            outputs=["frozen upstream refs", "repo-aware touch set", "execution boundary baseline"],
            depends_on=[],
            parallelizable_with=[],
            acceptance_refs=[],
            done_when="The implementation package states exactly where coding may occur and which upstream refs remain authoritative.",
        ),
        _task(
            step_id="TASK-002",
            title="Embed state, API, UI, and boundary contracts into implementation inputs",
            objective="Translate the frozen state machine, API surfaces, UI entry/exit, invariants, and boundary rules into coder-ready implementation inputs.",
            inputs=["state_machine", "api_contracts", "ui_entry_exit", "invariants", "boundaries"],
            touch_points=shared_paths + backend_paths[:1] + frontend_paths[:1],
            outputs=["embedded execution contract", "boundary-safe implementation baseline"],
            depends_on=["TASK-001"],
            parallelizable_with=[],
            acceptance_refs=acceptance_refs[:2],
            done_when="No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.",
        ),
    ]
    if assessment["frontend_required"]:
        tasks.append(
            _task(
                step_id="TASK-003",
                title="Implement frontend entry and exit surfaces",
                objective="Build the declared UI/page/component entry surface, validation feedback, and success/failure exits within the frozen boundary.",
                inputs=["embedded execution contract", "repo-aware frontend touch points"],
                touch_points=frontend_paths,
                outputs=["frontend surface", "entry/exit behavior", "field/error rendering"],
                depends_on=["TASK-001", "TASK-002"],
                parallelizable_with=["TASK-004"] if assessment["backend_required"] else [],
                acceptance_refs=[ref for ref in acceptance_refs if ref in {"AC-001", "AC-002"}],
                done_when="Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.",
            )
        )
    if assessment["backend_required"]:
        tasks.append(
            _task(
                step_id="TASK-004",
                title="Implement backend runtime, state, and persistence units",
                objective="Land the declared handlers / services / stores / runtime units so the frozen contracts and state transitions become executable.",
                inputs=["embedded execution contract", "repo-aware backend touch points"],
                touch_points=backend_paths or all_paths,
                outputs=["runtime units", "state readers/writers", "contract-aligned responses"],
                depends_on=["TASK-001", "TASK-002"],
                parallelizable_with=["TASK-003"] if assessment["frontend_required"] else [],
                acceptance_refs=[ref for ref in acceptance_refs if ref in {"AC-001", "AC-002"}],
                done_when="Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.",
            )
        )
    integration_dependencies = ["TASK-002"]
    if assessment["frontend_required"]:
        integration_dependencies.append("TASK-003")
    if assessment["backend_required"]:
        integration_dependencies.append("TASK-004")
    tasks.append(
        _task(
            step_id="TASK-005",
            title="Wire integration guards and downstream handoff",
            objective="Connect runtime entry/exit guards, boundary-safe integration hooks, and downstream delivery handoff without reinterpreting FEAT semantics.",
            inputs=["integration_points", "main_sequence", "handoff_artifacts"],
            touch_points=all_paths,
            outputs=["integration wiring", "guard behavior", "handoff-ready package"],
            depends_on=integration_dependencies,
            parallelizable_with=[],
            acceptance_refs=[ref for ref in acceptance_refs if ref in {"AC-002", "AC-003"}],
            done_when="The main sequence executes in order and downstream handoff remains boundary-safe.",
        )
    )
    if assessment["migration_required"]:
        tasks.append(
            _task(
                step_id="TASK-006",
                title="Make migration and cutover controls explicit",
                objective="Describe and implement the migration / rollback / compat behavior only where the frozen TECH package explicitly requires it.",
                inputs=["migration_required", "integration_points", "exception_and_compensation"],
                touch_points=backend_paths or all_paths,
                outputs=["migration plan", "rollback behavior", "compat controls"],
                depends_on=["TASK-005"],
                parallelizable_with=[],
                acceptance_refs=[ref for ref in acceptance_refs if ref == "AC-003"],
                done_when="Migration and fallback behavior is concrete enough to execute without keyword-based guesswork.",
            )
        )
    verify_dependencies = ["TASK-005"]
    if assessment["migration_required"]:
        verify_dependencies.append("TASK-006")
    tasks.append(
        _task(
            step_id="TASK-007",
            title="Collect acceptance evidence and close delivery handoff",
            objective="Run the acceptance-to-task mapping, collect evidence for every required acceptance check, and publish a downstream-ready handoff.",
            inputs=["acceptance_to_task_mapping", "dev_evidence_plan", "smoke_gate_subject"],
            touch_points=[],
            outputs=["acceptance evidence", "smoke gate inputs", "delivery handoff"],
            depends_on=verify_dependencies,
            parallelizable_with=[],
            acceptance_refs=acceptance_refs,
            done_when="Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.",
        )
    )
    return tasks


def _acceptance_to_task_mapping(
    checkpoints: list[dict[str, str]],
    task_breakdown: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        acceptance_ref = checkpoint["ref"]
        task_ids = [task["step_id"] for task in task_breakdown if acceptance_ref in ensure_list(task.get("acceptance_refs"))]
        mappings.append(
            {
                "acceptance_ref": acceptance_ref,
                "scenario": checkpoint["scenario"],
                "implemented_by": task_ids,
                "evidence_expectation": checkpoint["expectation"],
            }
        )
    return mappings


def _testset_mapping(
    selected_upstream_refs: dict[str, Any],
    checkpoints: list[dict[str, str]],
    repo_root: Path,
) -> dict[str, Any]:
    testset_ref = selected_upstream_refs["testset_ref"]
    unit_refs_by_acceptance = _testset_unit_refs_by_acceptance(repo_root, selected_upstream_refs)
    mappings = []
    feat_ref = str(selected_upstream_refs.get("feat_ref") or "").strip()
    for item in checkpoints:
        unit_refs: list[str] = []
        for alias in _acceptance_ref_aliases(item["ref"], feat_ref):
            unit_refs = unit_refs_by_acceptance.get(alias, [])
            if unit_refs:
                break
        mappings.append(
            {
                "acceptance_ref": item["ref"],
                "scenario": item["scenario"],
                "expectation": item["expectation"],
                "mapped_test_units": unit_refs,
                "mapping_status": (
                    "unit_bound"
                    if unit_refs
                    else ("package_bound_gap" if testset_ref else "missing_authority")
                ),
                "mapped_to": ", ".join(unit_refs) if unit_refs else testset_ref or "acceptance_trace_only_pending_testset_ref",
            }
        )
    return {
        "testset_ref": testset_ref,
        "mapping_policy": "TESTSET_over_IMPL_when_present",
        "mappings": mappings,
    }


def build_contract_projection(
    package: Any,
    feature: dict[str, Any],
    refs: dict[str, str | None],
    source_refs: list[str],
    assessment: dict[str, Any],
    steps: list[dict[str, str]],
    checkpoints: list[dict[str, str]],
    evidence_plan_rows: list[dict[str, Any]],
    deliverables: list[str],
    execution_contract_snapshot: dict[str, Any],
) -> dict[str, Any]:
    del steps, evidence_plan_rows, execution_contract_snapshot
    repo_root = _repo_root_for_package(package)
    selected_upstream_refs = build_selected_upstream_refs(feature, refs, source_refs, repo_root)
    provisional_refs = _provisional_refs(feature)
    authority_binding_status = _authority_binding_status(feature, refs, selected_upstream_refs, provisional_refs)
    scope_boundary = _scope_boundary(feature, package)
    repo_touch_points = _repo_touch_points(package, feature)
    normalized_assessment = {
        "frontend_required": bool(assessment.get("frontend_required")),
        "backend_required": bool(assessment.get("backend_required")),
        "migration_required": bool(assessment.get("migration_required")),
    }
    embedded_execution_contract = _embedded_execution_contract(feature, package, refs, scope_boundary, checkpoints)
    task_breakdown = _implementation_task_breakdown(
        feature,
        package,
        normalized_assessment,
        checkpoints,
        repo_touch_points,
        embedded_execution_contract,
    )
    acceptance_task_mapping = _acceptance_to_task_mapping(checkpoints, task_breakdown)
    change_controls = _change_controls(package, repo_touch_points, scope_boundary)
    return {
        "package_semantics": {
            "canonical_package": True,
            "execution_time_single_entrypoint": True,
            "domain_truth_source": False,
            "design_truth_source": False,
            "test_truth_source": False,
        },
        "authority_scope": {
            "upstream_truth_sources": [name for name, value in selected_upstream_refs.items() if value],
            "local_authority": [
                "execution_goal",
                "scope_boundary",
                "repo_touch_points",
                "embedded_execution_contract",
                "implementation_task_breakdown",
                "acceptance_to_task_mapping",
                "delivery_handoff",
                "evidence_requirements",
            ],
            "forbidden_authority": [
                "new_requirements",
                "design_redefinition",
                "test_truth_override",
                "repo_truth_override",
            ],
        },
        "selected_upstream_refs": selected_upstream_refs,
        "authority_binding_status": authority_binding_status,
        "authority_gap_register": _authority_gap_register(authority_binding_status),
        "provisional_refs": provisional_refs,
        "scope_boundary": scope_boundary,
        "upstream_impacts": _upstream_impacts(feature, package, selected_upstream_refs, checkpoints, provisional_refs),
        "normative_items": unique_strings(ensure_list(feature.get("constraints")) + filtered_implementation_rules(package)),
        "informative_items": unique_strings(ensure_list(feature.get("dependencies"))),
        "repo_touch_points": repo_touch_points,
        "embedded_execution_contract": embedded_execution_contract,
        "change_controls": change_controls,
        "required_steps": [
            {"title": task["title"], "work": task["objective"], "done_when": task["done_when"]}
            for task in task_breakdown
        ],
        "suggested_steps": (
            [{"title": "Resolve provisional refs", "reason": "Freeze or revise provisional upstream inputs before downstream execution."}]
            if provisional_refs
            else []
        ),
        "implementation_task_breakdown": task_breakdown,
        "acceptance_trace": checkpoints,
        "acceptance_to_task_mapping": acceptance_task_mapping,
        "testset_mapping": _testset_mapping(selected_upstream_refs, checkpoints, repo_root),
        "handoff_artifacts": deliverables,
        "conflict_policy": {
            "upstream_precedence": ["ADR", "SRC", "EPIC", "FEAT", "ARCH", "TECH", "API", "UI", "TESTSET"],
            "testset_precedence": "TESTSET_over_IMPL",
            "repo_discrepancy_policy": "explicit_discrepancy_handling_required",
        },
        "freshness_status": "fresh_on_generation",
        "rederive_triggers": [
            "selected_upstream_ref_version_changed",
            "testset_acceptance_changed",
            "api_or_ui_contract_changed",
            "tech_boundary_or_touch_set_changed",
            "touch_set_exceeded",
            "acceptance_or_delivery_changed",
            "provisional_ref_resolved_or_rejected",
        ],
        "self_contained_policy": {
            "principle": "strong_self_contained_execution_contract",
            "expand": [
                "repo_touch_points",
                "embedded_execution_contract",
                "implementation_task_breakdown",
                "acceptance_to_task_mapping",
                "acceptance_trace",
                "critical_interfaces_and_boundaries",
                "deliverables",
            ],
            "summary_only": [
                "historical_rationale",
                "full_adr_background",
                "full_upstream_markdown_bodies",
                "adjacent_feature_context",
            ],
            "forbidden": [
                "summary_only_execution_contract",
                "sidecar_only_execution_critical_facts",
                "abstract_touch_set_without_repo_placement",
                "keyword_only_migration_inference",
            ],
        },
        "repo_discrepancy_status": {
            "status": "placement_projected_from_repo_root",
            "policy": "do_not_promote_repo_to_truth",
        },
    }

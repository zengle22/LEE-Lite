#!/usr/bin/env python3
"""
Shared helpers for the lite-native feat-to-tech runtime.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_INPUT_FILES = [
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_markdown_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    end_marker = "\n---\n"
    end_index = markdown_text.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown_text
    frontmatter_text = markdown_text[4:end_index]
    body = markdown_text[end_index + len(end_marker) :]
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        return {}, body
    return data, body


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "unspecified"


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _string_list(values: Any) -> list[str]:
    items = values if isinstance(values, list) else ensure_list(values)
    return [str(item).strip() for item in items if str(item).strip()]


def discover_testset_binding(repo_root: Path, feat_ref: str) -> dict[str, Any] | None:
    testset_root = repo_root / "ssot" / "testset"
    if not testset_root.exists():
        return None

    matches: list[tuple[int, dict[str, Any]]] = []
    target = feat_ref.strip()
    for candidate in sorted(testset_root.glob("*.yaml")):
        try:
            payload = load_yaml(candidate) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(payload, dict):
            continue
        parent_id = str(payload.get("parent_id") or "").strip()
        feature_ids = _string_list((payload.get("traceability") or {}).get("feature_ids"))
        if parent_id != target and target not in feature_ids:
            continue
        ref = str(payload.get("id") or candidate.stem).strip()
        if not ref:
            continue
        lifecycle_state = str(payload.get("lifecycle_state") or "").strip().lower()
        higher_order_status = str(payload.get("higher_order_status") or "").strip().lower()
        status = str(payload.get("status") or "").strip().lower()
        historical_note = str(payload.get("historical_note") or "").strip()
        provisional_reasons = [
            reason
            for reason in [
                "lifecycle_state=historical_only" if lifecycle_state == "historical_only" else "",
                f"higher_order_status={higher_order_status}" if higher_order_status == "superseded" else "",
                "historical_note_present" if historical_note else "",
            ]
            if reason
        ]
        is_authoritative = not provisional_reasons and status in {"active", "accepted", "frozen"}
        score = 0
        if parent_id == target:
            score += 4
        if target in feature_ids:
            score += 2
        if is_authoritative:
            score += 4
        matches.append(
            (
                score,
                {
                    "ref": ref,
                    "path": candidate,
                    "status": status,
                    "lifecycle_state": lifecycle_state,
                    "higher_order_status": higher_order_status,
                    "historical_note": historical_note,
                    "is_authoritative": is_authoritative,
                    "provisional_reasons": provisional_reasons,
                },
            )
        )
    if not matches:
        return None
    matches.sort(key=lambda item: (-item[0], str(item[1]["path"])))
    return matches[0][1]


def enrich_feature_execution_metadata(repo_root: Path, feature: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(feature)
    feat_ref = str(enriched.get("feat_ref") or "").strip()
    if not feat_ref:
        return enriched

    testset_binding = discover_testset_binding(repo_root, feat_ref)
    if testset_binding and not str(enriched.get("testset_ref") or "").strip():
        enriched["testset_ref"] = testset_binding["ref"]
        enriched["source_refs"] = unique_strings(ensure_list(enriched.get("source_refs")) + [testset_binding["ref"]])
        if not testset_binding["is_authoritative"]:
            provisional_refs = enriched.get("provisional_refs")
            provisional_items = provisional_refs if isinstance(provisional_refs, list) else []
            if not any(isinstance(item, dict) and str(item.get("ref") or "").strip() == testset_binding["ref"] for item in provisional_items):
                note = testset_binding["historical_note"] or ", ".join(testset_binding["provisional_reasons"]) or "historical testset binding"
                provisional_items = provisional_items + [
                    {
                        "ref": testset_binding["ref"],
                        "impact_scope": "test acceptance mapping and execution evidence",
                        "follow_up_action": f"refresh_or_replace_testset_before_final_execution ({note})",
                    }
                ]
                enriched["provisional_refs"] = provisional_items
    return enriched


def normalize_semantic_lock(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    lock = {
        "domain_type": str(payload.get("domain_type") or "").strip(),
        "one_sentence_truth": str(payload.get("one_sentence_truth") or "").strip(),
        "primary_object": str(payload.get("primary_object") or "").strip(),
        "lifecycle_stage": str(payload.get("lifecycle_stage") or "").strip(),
        "allowed_capabilities": ensure_list(payload.get("allowed_capabilities")),
        "forbidden_capabilities": ensure_list(payload.get("forbidden_capabilities")),
        "inheritance_rule": str(payload.get("inheritance_rule") or "").strip(),
    }
    return {key: value for key, value in lock.items() if value not in ("", [], None)}


def derive_semantic_lock(feature: Any, inherited_payload: Any = None) -> dict[str, Any]:
    existing = normalize_semantic_lock(feature.get("semantic_lock") if isinstance(feature, dict) else None)
    if existing:
        return existing
    inherited = normalize_semantic_lock(inherited_payload)
    if inherited:
        return inherited
    if not isinstance(feature, dict):
        return {}

    identity = feature.get("identity_and_scenario") if isinstance(feature.get("identity_and_scenario"), dict) else {}
    completed_state = str(identity.get("completed_state") or "").strip()
    boundary = feature.get("frozen_downstream_boundary") if isinstance(feature.get("frozen_downstream_boundary"), dict) else {}
    inheritance_candidates = ensure_list(boundary.get("frozen_business_semantics"))
    inherited_rule = (
        str(inheritance_candidates[0]).strip()
        if inheritance_candidates
        else ""
    )
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    title = str(feature.get("title") or "").strip().lower()
    text_parts = [
        str(feature.get("goal") or ""),
        *ensure_list(feature.get("scope")),
        *ensure_list(feature.get("constraints")),
    ]
    text = "\n".join(part.lower() for part in text_parts if str(part).strip())

    def product_lock(
        *,
        domain_type: str,
        primary_object: str,
        lifecycle_stage: str,
        allowed_capabilities: list[str],
        forbidden_capabilities: list[str],
        default_truth: str,
        default_rule: str,
    ) -> dict[str, Any]:
        return normalize_semantic_lock(
            {
                "domain_type": domain_type,
                "one_sentence_truth": completed_state or default_truth,
                "primary_object": primary_object,
                "lifecycle_stage": lifecycle_stage,
                "allowed_capabilities": allowed_capabilities,
                "forbidden_capabilities": forbidden_capabilities,
                "inheritance_rule": inherited_rule or default_rule,
            }
        )

    if axis_id == "first-ai-advice-release":
        return product_lock(
            domain_type="first_advice_release_flow",
            primary_object="first advice",
            lifecycle_stage="advice visible",
            allowed_capabilities=[
                "training_advice_level",
                "first_week_action",
                "needs_more_info_prompt",
                "device_connect_prompt",
                "running_level",
                "recent_injury_status",
                "risk gate",
                "first advice",
            ],
            forbidden_capabilities=[
                "genericrequest",
                "ll rollout onboard-skill",
                "pilot chain",
                "cutover",
            ],
            default_truth="Minimal profile completion is enough to generate a safe first advice output without requiring expanded profile or device data first.",
            default_rule="Downstream TECH must preserve first-advice output and risk-gate semantics instead of collapsing into a generic runtime skeleton.",
        )
    if axis_id == "extended-profile-progressive-completion":
        return product_lock(
            domain_type="extended_profile_completion_flow",
            primary_object="extended profile task card",
            lifecycle_stage="incremental save",
            allowed_capabilities=[
                "task card",
                "incremental save",
                "profile completion",
                "extended profile patch",
                "homepage usable",
                "retry entry",
            ],
            forbidden_capabilities=[
                "genericrequest",
                "ll rollout onboard-skill",
                "pilot chain",
                "cutover",
            ],
            default_truth="Users can progressively complete extended profile fields from homepage task cards and each save stands alone.",
            default_rule="Downstream TECH must preserve task-card progressive completion and incremental-save semantics instead of collapsing into a generic runtime skeleton.",
        )
    if axis_id == "device-connect-deferred-entry":
        return product_lock(
            domain_type="device_deferred_entry_flow",
            primary_object="deferred device connection",
            lifecycle_stage="nonblocking enhancement",
            allowed_capabilities=[
                "device connection",
                "deferred entry",
                "device skipped",
                "device failed nonblocking",
                "homepage entered",
                "first advice available",
            ],
            forbidden_capabilities=[
                "genericrequest",
                "ll rollout onboard-skill",
                "pilot chain",
                "cutover",
            ],
            default_truth="Device connection stays a deferred enhancement path and must not block homepage entry or first-day advice.",
            default_rule="Downstream TECH must preserve deferred non-blocking device-entry semantics instead of collapsing into a generic runtime skeleton.",
        )
    if axis_id == "state-and-profile-boundary-alignment":
        return product_lock(
            domain_type="state_profile_boundary_rule",
            primary_object="canonical onboarding state",
            lifecycle_stage="boundary alignment",
            allowed_capabilities=[
                "primary_state",
                "capability_flags",
                "user_physical_profile",
                "runner_profiles",
                "canonical read",
                "conflict validator",
                "single source of truth",
            ],
            forbidden_capabilities=[
                "genericrequest",
                "ll rollout onboard-skill",
                "pilot chain",
                "cutover",
            ],
            default_truth="Page flow state and business completion state must not be mixed, and body-field conflicts must resolve to one canonical source of truth.",
            default_rule="Downstream TECH must preserve state-boundary and single-source-of-truth semantics instead of collapsing into a generic runtime skeleton.",
        )
    if axis_id == "minimal-onboarding-flow" or "最小建档" in title or "minimal onboarding" in text or "profile_minimal_done" in text:
        return product_lock(
            domain_type="product_onboarding_flow",
            primary_object="minimal profile",
            lifecycle_stage="homepage entry",
            allowed_capabilities=[
                "minimal profile",
                "birthdate",
                "running_level",
                "recent_injury_status",
                "profile_minimal_done",
                "homepage entry",
                "device connection deferred",
            ],
            forbidden_capabilities=[
                "ll rollout onboard-skill",
                "onboardingdirective",
                "pilotevidencesubmission",
                "pilot chain",
                "cutover",
                "compat mode",
                "migration wave",
                "rollout state",
            ],
            default_truth="User completes the minimal profile and can immediately enter homepage while device connection stays deferred.",
            default_rule="Downstream TECH must preserve minimal profile completion semantics and must not replace them with rollout or pilot governance semantics.",
        )
    return {}


def semantic_lock_errors(payload: Any) -> list[str]:
    lock = normalize_semantic_lock(payload)
    if not lock:
        return []
    required_fields = [
        "domain_type",
        "one_sentence_truth",
        "primary_object",
        "lifecycle_stage",
        "inheritance_rule",
    ]
    errors = [field for field in required_fields if not str(lock.get(field) or "").strip()]
    if not ensure_list(lock.get("allowed_capabilities")):
        errors.append("allowed_capabilities")
    if not ensure_list(lock.get("forbidden_capabilities")):
        errors.append("forbidden_capabilities")
    return [f"semantic_lock missing required field: {field}" for field in errors]


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


def resolve_input_artifacts_dir(input_value: str | Path, repo_root: Path) -> tuple[Path, dict[str, Any]]:
    candidate_path = Path(str(input_value))
    if candidate_path.exists() and candidate_path.is_dir():
        return candidate_path.resolve(), {"input_mode": "package_dir", "requested_ref": str(candidate_path.resolve())}

    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.lib.admission import validate_admission
    from cli.lib.fs import canonical_to_path
    from cli.lib.registry_store import resolve_registry_record

    requested_ref = str(input_value)
    admission = validate_admission(
        repo_root,
        consumer_ref="dev.feat-to-tech",
        requested_ref=requested_ref,
    )
    record = resolve_registry_record(repo_root, requested_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    if not source_package_ref:
        raise ValueError("formal feat record is missing metadata.source_package_ref")
    artifacts_dir = canonical_to_path(source_package_ref, repo_root)
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        raise FileNotFoundError(f"resolved feat package directory not found: {artifacts_dir}")
    return artifacts_dir.resolve(), {
        "input_mode": "formal_admission",
        "requested_ref": requested_ref,
        "resolved_formal_ref": admission["resolved_formal_ref"],
        "managed_artifact_ref": record.get("managed_artifact_ref", ""),
        "resolved_feat_ref": str(metadata.get("feat_ref") or metadata.get("assigned_id") or "").strip(),
    }


@dataclass
class FeatPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    feat_json: dict[str, Any]
    feat_frontmatter: dict[str, Any]
    feat_markdown_body: str
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    execution_evidence: dict[str, Any]
    supervision_evidence: dict[str, Any]
    gate: dict[str, Any]
    handoff: dict[str, Any]
    semantic_lock: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(
            self.feat_json.get("workflow_run_id")
            or self.manifest.get("run_id")
            or self.artifacts_dir.name
        )


def load_feat_package(artifacts_dir: Path) -> FeatPackage:
    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return FeatPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        feat_json=load_json(artifacts_dir / "feat-freeze-bundle.json"),
        feat_frontmatter=frontmatter,
        feat_markdown_body=body,
        review_report=load_json(artifacts_dir / "feat-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "feat-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "feat-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "feat-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-feat-downstreams.json"),
        semantic_lock=normalize_semantic_lock(load_json(artifacts_dir / "feat-freeze-bundle.json").get("semantic_lock")),
    )


def find_feature(package: FeatPackage, feat_ref: str) -> dict[str, Any] | None:
    target = feat_ref.strip()
    for feature in package.feat_json.get("features") or []:
        if isinstance(feature, dict) and str(feature.get("feat_ref") or "").strip() == target:
            return feature
    return None


def validate_input_package(input_value: str | Path, feat_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir, input_resolution = resolve_input_artifacts_dir(input_value, repo_root)
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    effective_feat_ref = feat_ref.strip() or str(input_resolution.get("resolved_feat_ref") or "").strip()
    if not effective_feat_ref:
        errors.append("feat_ref is required.")

    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_feat_package(artifacts_dir)
    errors.extend(semantic_lock_errors(package.feat_json.get("semantic_lock")))

    artifact_type = str(package.feat_json.get("artifact_type") or "")
    if artifact_type != "feat_freeze_package":
        errors.append(
            f"feat-freeze-bundle.json artifact_type must be feat_freeze_package, got: {artifact_type or '<missing>'}"
        )

    workflow_key = str(package.feat_json.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "product.epic-to-feat":
        errors.append(f"Upstream workflow must be product.epic-to-feat, got: {workflow_key or '<missing>'}")

    status = str(package.feat_json.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"feat-freeze status must be accepted or frozen, got: {status or '<missing>'}")

    if package.gate.get("freeze_ready") is not True:
        errors.append("feat-freeze-gate.json must mark the package as freeze_ready.")

    feature = find_feature(package, effective_feat_ref)
    if feature is None:
        errors.append(f"Selected feat_ref not found in feat-freeze-bundle.json: {effective_feat_ref}")
    else:
        for field in ["feat_ref", "title", "goal", "scope", "constraints", "acceptance_checks", "source_refs"]:
            if feature.get(field) in (None, "", []):
                errors.append(f"Selected feature is missing required field: {field}")
        if len(feature.get("acceptance_checks") or []) < 3:
            errors.append(f"{effective_feat_ref} must include at least three acceptance checks.")

    source_refs = ensure_list(package.feat_json.get("source_refs"))
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include SRC-*.")
    derivable_children = ensure_list(package.handoff.get("derivable_children"))
    if "TECH" not in derivable_children:
        errors.append("handoff-to-feat-downstreams.json must include TECH in derivable_children.")

    result = {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": workflow_key,
        "status": status,
        "input_mode": input_resolution.get("input_mode", "package_dir"),
        "feat_ref": effective_feat_ref,
        "feat_title": str((feature or {}).get("title") or ""),
        "epic_freeze_ref": package.feat_json.get("epic_freeze_ref"),
        "src_root_id": package.feat_json.get("src_root_id"),
        "source_refs": source_refs,
        "semantic_lock": package.semantic_lock,
    }
    return errors, result

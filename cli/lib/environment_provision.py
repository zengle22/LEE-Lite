"""Environment provision module: generates TEST_ENVIRONMENT_SPEC YAML files.

This module takes feat environment_assumptions and user parameters and generates
ENV files that test_exec_runtime.py can consume.

Per ADR-054 §2.3, §5.1 R-3.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Input DTO (also used by contracts.py EnvConfig)
# ---------------------------------------------------------------------------


@dataclass
class EnvProvisionInput:
    """Input for environment provision.

    Attributes:
        feat_ref: Feature reference (API chain)
        proto_ref: Prototype reference (E2E chain)
        base_url: Primary base URL (default: http://localhost:8000)
        modality: Execution modality (api, web_e2e, cli)
        browser: Browser for web_e2e (chromium, firefox, webkit)
        timeout: Timeout in milliseconds
        feat_assumptions: List of environment assumptions from FEAT
        app_url: Frontend URL (E2E chain, R-3)
        api_url: Backend API URL (separated architecture, R-3)
    """

    feat_ref: str | None = None
    proto_ref: str | None = None
    base_url: str = "http://localhost:8000"
    modality: str = "api"
    browser: str = "chromium"
    timeout: int = 30000
    feat_assumptions: list[str] = field(default_factory=list)
    app_url: str = "http://localhost:3000"
    api_url: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_env_id(feat_ref: str | None, proto_ref: str | None) -> str:
    """Generate a unique ENV identifier."""
    if feat_ref:
        return f"ENV-{feat_ref}"
    if proto_ref:
        return f"ENV-{proto_ref}"
    return f"ENV-{uuid.uuid4().hex[:8].upper()}"


def _timestamp() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _merge_assumptions(assumptions: list[str]) -> dict[str, Any]:
    """Parse feat_assumptions strings into structured config.

    Each assumption is expected to be in 'key=value' format (preferred) or 'key:value' format.
    URLs with ports (e.g., 'base_url=http://localhost:8000') use '=' delimiter.
    Returns a dict with parsed values.
    """
    result: dict[str, Any] = {}
    for assumption in assumptions:
        assumption = assumption.strip()
        if not assumption:
            continue
        # Check for '=' first since URLs contain ':' but not '='
        if "=" in assumption:
            key, _, value = assumption.partition("=")
            result[key.strip()] = value.strip()
        elif ":" in assumption:
            key, _, value = assumption.partition(":")
            result[key.strip()] = value.strip()
    return result


# ---------------------------------------------------------------------------
# Main provision function
# ---------------------------------------------------------------------------


def provision_environment(
    workspace_root: Path,
    *,
    feat_ref: str | None = None,
    proto_ref: str | None = None,
    base_url: str = "http://localhost:8000",
    app_url: str = "http://localhost:3000",
    api_url: str | None = None,
    modality: str = "api",
    browser: str = "chromium",
    timeout: int = 30000,
    feat_assumptions: list[str] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Generate TEST_ENVIRONMENT_SPEC YAML file.

    Priority: user CLI params > feat environment_assumptions > defaults.

    Args:
        workspace_root: Root of the workspace
        feat_ref: Feature reference (API chain)
        proto_ref: Prototype reference (E2E chain)
        base_url: User-provided base URL
        app_url: Frontend URL (E2E chain)
        api_url: Backend API URL (separated architecture)
        modality: Execution modality (api, web_e2e, cli)
        browser: Browser for web_e2e
        timeout: Timeout in milliseconds
        feat_assumptions: List of environment assumption strings from FEAT

    Returns:
        Tuple of (env_file_path, env_config dict)

    Raises:
        ValueError: If neither feat_ref nor proto_ref is provided
    """
    if feat_assumptions is None:
        feat_assumptions = []

    if not feat_ref and not proto_ref:
        raise ValueError("Either feat_ref or proto_ref must be provided")

    # Merge assumptions from feat
    merged_assumptions = _merge_assumptions(feat_assumptions)

    # Resolve URLs with priority: explicit params > assumptions > defaults
    resolved_base_url = merged_assumptions.get("base_url", base_url)
    resolved_app_url = merged_assumptions.get("app_url", app_url)
    resolved_api_url = merged_assumptions.get("api_url", api_url)

    # Generate ENV ID
    env_id = _generate_env_id(feat_ref, proto_ref)

    # Build the ENV document (ADR-054 §2.3.2)
    env_doc: dict[str, Any] = {
        "ssot_type": "TEST_ENVIRONMENT_SPEC",
        "test_environment_ref": f"ssot/environments/{env_id}.yaml",
        "execution_modality": modality,
        "base_url": resolved_base_url,
        "browser": browser if modality == "web_e2e" else None,
        "timeout": timeout,
        "required_fields": [],
        "feature_flags": merged_assumptions.get("feature_flags", {}),
        "test_data_config": merged_assumptions.get("test_data_config", {}),
        "source_feat_ref": feat_ref,
        "source_proto_ref": proto_ref,
        "generated_by": "environment_provision",
        "generated_at": _timestamp(),
    }

    # Add app_base_url and api_base_url for E2E chain (ADR-054 §5.1 R-3)
    if modality == "web_e2e":
        env_doc["app_base_url"] = resolved_app_url
        if resolved_api_url:
            env_doc["api_base_url"] = resolved_api_url

    # For API chain, also support api_base_url if provided
    if modality == "api" and resolved_api_url:
        env_doc["api_base_url"] = resolved_api_url

    # Remove None values
    env_doc = {k: v for k, v in env_doc.items() if v is not None}

    # Ensure output directory exists
    env_dir = workspace_root / "ssot" / "environments"
    env_dir.mkdir(parents=True, exist_ok=True)

    # Write .gitkeep if directory was just created (ENV-02)
    gitkeep_path = env_dir / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.write_text("", encoding="utf-8")

    # Write the ENV file
    env_path = env_dir / f"{env_id}.yaml"
    with env_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(env_doc, f, allow_unicode=True, sort_keys=False)

    # Build EnvConfig return value
    env_config: dict[str, Any] = {
        "feat_ref": feat_ref,
        "proto_ref": proto_ref,
        "modality": modality,
        "base_url": resolved_base_url,
        "app_url": resolved_app_url,
        "api_url": resolved_api_url,
        "browser": browser,
        "timeout": timeout,
        "feat_assumptions": feat_assumptions,
    }

    return env_path, env_config


# ---------------------------------------------------------------------------
# Convenience wrapper matching the contracts.py EnvConfig shape
# ---------------------------------------------------------------------------


def generate_env_file(workspace_root: Path, input: EnvProvisionInput) -> Path:
    """Generate a TEST_ENVIRONMENT_SPEC YAML file from EnvProvisionInput.

    This is a convenience wrapper around provision_environment.

    Args:
        workspace_root: Root of the workspace
        input: EnvProvisionInput dataclass

    Returns:
        Path to the generated ENV file
    """
    env_path, _ = provision_environment(
        workspace_root=workspace_root,
        feat_ref=input.feat_ref,
        proto_ref=input.proto_ref,
        base_url=input.base_url,
        app_url=input.app_url,
        api_url=input.api_url,
        modality=input.modality,
        browser=input.browser,
        timeout=input.timeout,
        feat_assumptions=input.feat_assumptions,
    )
    return env_path

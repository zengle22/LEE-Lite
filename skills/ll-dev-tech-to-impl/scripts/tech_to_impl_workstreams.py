#!/usr/bin/env python3
"""
Workstream helpers for tech-to-impl.
"""

from __future__ import annotations

import re
from typing import Any

from tech_to_impl_common import ensure_list
from tech_to_impl_workstream_analysis import assess_workstreams, is_execution_runner_package


def _classify_unit_surface(path: str, detail: str, assessment: dict[str, Any]) -> str:
    text = f"{path} {detail}".lower()
    if any(marker in text for marker in ["migration", "cutover", "rollout", "rollback", "fallback", "compat", "迁移", "切换", "回滚", "灰度"]):
        return "migration"
    if any(marker in text for marker in ["ui", "frontend", "front-end", "page", "screen", "view", "panel", "home/", "页面", "前端", "交互"]):
        return "frontend"
    if assessment.get("frontend_required") and not assessment.get("backend_required"):
        return "frontend"
    return "backend"


def _acceptance_refs(checkpoints: list[dict[str, str]] | None, fallback: list[str]) -> list[str]:
    refs = [str(item.get("ref") or "").strip() for item in checkpoints or [] if str(item.get("ref") or "").strip()]
    return [ref for ref in fallback if ref in refs] or refs[:1] or fallback[:1]


def implementation_steps(
    feature: dict[str, Any],
    assessment: dict[str, Any],
    package: Any,
    checkpoints: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    runner_package = is_execution_runner_package(feature, package)
    resolved_axis = str(feature.get("resolved_axis") or feature.get("derived_axis") or "").strip().lower()
    resolved_axis = re.sub(r"[^a-z0-9_]+", "_", resolved_axis.replace("-", "_").replace(" ", "_"))
    resolved_axis = re.sub(r"_+", "_", resolved_axis).strip("_")
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    units = package.tech_json.get("tech_design", {}).get("implementation_unit_mapping") or []
    unit_rows = []
    for raw in units:
        cleaned = str(raw).replace("`", "")
        if ":" in cleaned:
            left, detail = cleaned.split(":", 1)
        else:
            left, detail = cleaned, cleaned
        if "(" in left and ")" in left:
            path = left.split("(", 1)[0].strip()
        else:
            path = left.strip()
        unit_rows.append(
            {
                "path": path,
                "detail": detail.strip(),
                "surface": _classify_unit_surface(path, detail, assessment),
            }
        )
    unit_preview = ", ".join(units[:4]) or "the frozen TECH implementation units"
    interface_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("interface_contracts"))[:2])
    sequence_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("main_sequence"))[:3])
    integration_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("integration_points"))[:2])
    frontend_paths = [row["path"] for row in unit_rows if row["surface"] == "frontend"]
    backend_paths = [row["path"] for row in unit_rows if row["surface"] == "backend"]
    migration_paths = [row["path"] for row in unit_rows if row["surface"] == "migration"]

    steps: list[dict[str, Any]] = [
        {
            "task_id": "TASK-001",
            "title": "Freeze upstream refs, repo placement, and touch set",
            "workstream": "cross-cutting",
            "depends_on": [],
            "parallel_group": "setup",
            "outputs": ["frozen-upstream-refs", "touch-set-freeze", "execution-contract-snapshot"],
            "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
            "work": f"Lock feat_ref, tech_ref, optional arch/api refs, and the concrete touch set before coding: {unit_preview}.",
            "done_when": "The implementation entry references frozen upstream objects only, the concrete file/module touch set is explicit, and repo landing zones are frozen before coding starts.",
        }
    ]

    if resolved_axis == "engineering_baseline":
        def _outputs(prefixes: list[str], fallback: list[str]) -> list[str]:
            selected = [row["path"] for row in unit_rows if any(row["path"].startswith(prefix) for prefix in prefixes)]
            return selected[:6] or fallback

        if axis_id == "repo-layout-baseline":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Freeze root layout rules (allow/deny + legacy src guard)",
                        "workstream": "backend",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "repo-layout",
                        "outputs": ["README.md", "AGENTS.md"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Write/update `README.md` and `AGENTS.md` to freeze: new code landing zones (`apps/`, `db/`, `deploy/`, `scripts/`), "
                        "forbidden roots (`src/` is legacy), and root-level allow/deny rules so implementers cannot drift.",
                        "done_when": "`README.md` and `AGENTS.md` explicitly define allowed roots, forbidden roots, and the legacy `src/` no-increment rule.",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Implement repo doctor checks and entrypoint",
                        "workstream": "backend",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "repo-layout",
                        "outputs": _outputs(["scripts/doctor/", "scripts/dev/", "Makefile"], ["scripts/doctor/*", "Makefile"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Add a lightweight `doctor` check (Makefile target and/or scripts) that detects forbidden roots and layout violations. "
                        "Do not add business code; keep checks focused on repo layout compliance.",
                        "done_when": "`make doctor` (or equivalent script entrypoint) exists and fails loudly when forbidden roots (e.g. `src/`) receive new code.",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Run doctor and capture layout compliance evidence",
                        "workstream": "evidence",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "repo-layout",
                        "outputs": ["doctor-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002"]),
                        "work": "Run the frozen doctor entrypoint on a clean checkout and record the output as evidence. Ensure the check reports layout violations clearly.",
                        "done_when": "Doctor evidence exists and demonstrates that forbidden roots and layout drift are detectable before implementation begins.",
                    },
                ]
            )
            return steps

        if axis_id == "api-shell":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Scaffold apps/api module and server entrypoint",
                        "workstream": "backend",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "api-shell",
                        "outputs": _outputs(["apps/api/go.mod", "apps/api/cmd/server/main.go"], ["apps/api/go.mod", "apps/api/cmd/server/main.go"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Create the Go module baseline under `apps/api/` and a single runnable server entrypoint at `apps/api/cmd/server/main.go`.",
                        "done_when": "`apps/api` can be started locally via a single entrypoint without pulling in unrelated slices (compose/migrations/miniapp).",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Add minimal internal skeleton and HTTP router/handlers",
                        "workstream": "backend",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "api-shell",
                        "outputs": _outputs(
                            ["apps/api/internal/config/", "apps/api/internal/infra/", "apps/api/internal/transport/"],
                            ["apps/api/internal/transport/httpapi/*"],
                        ),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Freeze minimal directory boundaries (`internal/config`, `internal/infra/db`, `internal/transport/httpapi`) and mount the base routes. "
                        "HTTP handlers must not run raw SQL directly; DB access stays in infra/repository layers.",
                        "done_when": "Router + handlers compile and the service exposes the minimal HTTP surface expected by upstream FEAT/TECH.",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Freeze local dev start command and smoke endpoint existence",
                        "workstream": "backend",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "api-shell",
                        "outputs": ["Makefile"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Provide a stable dev entrypoint (e.g. `make api-dev`) and verify the server responds on `/healthz` and `/readyz` (existence + wiring only; semantics are owned by the health contract slice).",
                        "done_when": "`make api-dev` starts the server and `/healthz` + `/readyz` routes are mounted and reachable.",
                    },
                    {
                        "task_id": "TASK-005",
                        "title": "Capture runnable shell evidence (start + curl)",
                        "workstream": "evidence",
                        "depends_on": ["TASK-004"],
                        "parallel_group": "api-shell",
                        "outputs": ["api-shell-smoke-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002"]),
                        "work": "Start the API via the frozen entrypoint and capture minimal evidence (logs + curl results) proving the shell is runnable and endpoints exist.",
                        "done_when": "Evidence proves the API shell starts deterministically and `/healthz` + `/readyz` are reachable from the dev environment.",
                    },
                ]
            )
            return steps

        if axis_id == "miniapp-shell":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Scaffold UniApp miniapp skeleton (routes + manifest + index page)",
                        "workstream": "frontend",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "miniapp",
                        "outputs": _outputs(["apps/miniapp/pages.json", "apps/miniapp/manifest.json", "apps/miniapp/pages/index/"], ["apps/miniapp/pages.json", "apps/miniapp/manifest.json"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Create `apps/miniapp/` minimal runnable skeleton with `pages.json`, `manifest.json`, and a minimal landing page.",
                        "done_when": "`apps/miniapp` contains a minimal page/router structure and can be started via a frozen command.",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Add healthz connectivity verification page",
                        "workstream": "frontend",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "miniapp",
                        "outputs": _outputs(["apps/miniapp/pages/debug/"], ["apps/miniapp/pages/debug/healthz.vue"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002"]),
                        "work": "Implement `apps/miniapp/pages/debug/healthz.vue` (and any tiny helper module under `apps/miniapp`) to call backend `GET /healthz` and display success/failure clearly.",
                        "done_when": "A deterministic, reproducible verification path exists inside the miniapp to validate backend connectivity via `/healthz`.",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Freeze miniapp dev command and verification steps",
                        "workstream": "frontend",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "miniapp",
                        "outputs": _outputs(["apps/miniapp/README.md", "Makefile"], ["apps/miniapp/README.md", "Makefile"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Document the dev command + verification steps in `apps/miniapp/README.md` and expose a stable entrypoint (e.g. `make miniapp-dev`).",
                        "done_when": "New contributors can start the miniapp and follow a documented path to run the `/healthz` verification.",
                    },
                    {
                        "task_id": "TASK-005",
                        "title": "Capture miniapp verification evidence",
                        "workstream": "evidence",
                        "depends_on": ["TASK-004"],
                        "parallel_group": "miniapp",
                        "outputs": ["miniapp-healthz-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002"]),
                        "work": "Follow the documented verification path (start miniapp, open debug page, invoke `/healthz`) and capture evidence (screenshot/log).",
                        "done_when": "Evidence shows the miniapp can reach the backend `/healthz` endpoint via the debug verification page.",
                    },
                ]
            )
            return steps

        if axis_id == "local-env":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Deliver docker-compose local Postgres entrypoint",
                        "workstream": "backend",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "local-env",
                        "outputs": _outputs(["deploy/docker-compose.local.yml"], ["deploy/docker-compose.local.yml"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Create `deploy/docker-compose.local.yml` that starts a local Postgres with durable volume and predictable ports.",
                        "done_when": "`deploy/docker-compose.local.yml` exists and can boot Postgres via a stable entrypoint.",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Freeze local env vars entry (.env.example)",
                        "workstream": "backend",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "local-env",
                        "outputs": [".env.example"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Provide `.env.example` with the required DB connection variables. Do not commit secrets; `.env` remains ignored.",
                        "done_when": "Local DB connection inputs are standardized via `.env.example` (no secrets in repo).",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Freeze dev up/down/doctor commands",
                        "workstream": "backend",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "local-env",
                        "outputs": _outputs(["Makefile", "scripts/dev/"], ["Makefile", "scripts/dev/*.ps1"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-003"]),
                        "work": "Add Makefile targets (e.g. `dev-up`, `dev-down`, `doctor`) and optional helpers under `scripts/dev/` to standardize local env lifecycle.",
                        "done_when": "`make dev-up`/`make dev-down` are symmetric and `doctor` can validate basic prerequisites.",
                    },
                    {
                        "task_id": "TASK-005",
                        "title": "Verify local env lifecycle and capture evidence",
                        "workstream": "evidence",
                        "depends_on": ["TASK-004"],
                        "parallel_group": "local-env",
                        "outputs": ["local-env-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-003"]),
                        "work": "Run `make dev-up` and `make dev-down` and capture evidence (compose status/logs) proving the lifecycle is reproducible and symmetric.",
                        "done_when": "Evidence shows local Postgres starts/stops via frozen entrypoints and does not depend on undocumented personal setup.",
                    },
                ]
            )
            return steps

        if axis_id == "db-migrations":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Create initial migration (0001) with up/down scripts",
                        "workstream": "migration",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "migrations",
                        "outputs": _outputs(["db/migrations/0001_init."], ["db/migrations/0001_init.up.sql", "db/migrations/0001_init.down.sql"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Create `db/migrations/0001_init.up.sql` and `db/migrations/0001_init.down.sql` as the first executable migration pair.",
                        "done_when": "An empty DB can apply the initial migration cleanly and has a defined rollback script.",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Freeze migration runner entrypoints",
                        "workstream": "migration",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "migrations",
                        "outputs": _outputs(["Makefile", "scripts/db/"], ["Makefile", "scripts/db/*.ps1"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Add Makefile targets (e.g. `db-migrate-up`, `db-migrate-down-one`) and optional helpers under `scripts/db/` so schema changes can only flow through migrations.",
                        "done_when": "There is a single, documented migration execution path; hand-edited DB changes are treated as out-of-bounds.",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Verify migration apply/rollback and capture evidence",
                        "workstream": "evidence",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "migrations",
                        "outputs": ["migration-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "On an empty local DB, run the frozen migrate-up and migrate-down-one entrypoints and capture evidence (status/output).",
                        "done_when": "Evidence shows the initial migration applies cleanly and can rollback at the declared minimum granularity.",
                    },
                ]
            )
            return steps

        if axis_id == "health-readiness":
            steps.extend(
                [
                    {
                        "task_id": "TASK-002",
                        "title": "Implement /healthz and /readyz handlers and mount points",
                        "workstream": "backend",
                        "depends_on": ["TASK-001"],
                        "parallel_group": "health",
                        "outputs": _outputs(
                            ["apps/api/internal/transport/httpapi/handlers/", "apps/api/internal/transport/httpapi/router"],
                            ["apps/api/internal/transport/httpapi/handlers/healthz.go", "apps/api/internal/transport/httpapi/handlers/readyz.go"],
                        ),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
                        "work": "Implement `/healthz` (liveness) and `/readyz` (readiness) handlers and wire them into the HTTP router.",
                        "done_when": "Endpoints are implemented and mounted; contract semantics are stable and can be verified via curl.",
                    },
                    {
                        "task_id": "TASK-003",
                        "title": "Implement DB probe injection for readiness",
                        "workstream": "backend",
                        "depends_on": ["TASK-002"],
                        "parallel_group": "health",
                        "outputs": _outputs(["apps/api/internal/infra/db/"], ["apps/api/internal/infra/db/probe.go"]),
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002"]),
                        "work": "Add a DB probe helper with timeout; `/readyz` depends on the probe while `/healthz` must not.",
                        "done_when": "Readiness reflects DB connectivity (200 when ok, 503 when not) while liveness remains DB-independent.",
                    },
                    {
                        "task_id": "TASK-004",
                        "title": "Verify health/readiness responses and capture evidence",
                        "workstream": "evidence",
                        "depends_on": ["TASK-003"],
                        "parallel_group": "health",
                        "outputs": ["health-contract-evidence"],
                        "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                        "work": "Capture evidence via curl (or equivalent) for: `/healthz` returns 200 when process is up; `/readyz` returns 200 with DB up and 503 when DB is down/unreachable.",
                        "done_when": "Evidence demonstrates the frozen HTTP contract behavior and the DB-dependency boundary between liveness and readiness.",
                    },
                ]
            )
            return steps

        return steps

    if assessment["frontend_required"]:
        steps.append(
            {
                "task_id": "TASK-002",
                "title": "Implement frozen frontend entry/exit surface",
                "workstream": "frontend",
                "depends_on": ["TASK-001"],
                "parallel_group": "frontend",
                "outputs": frontend_paths[:4] or ["frontend-surface"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                "work": "Apply the selected UI/page/component changes, wire entry/exit behavior, and keep interaction behavior aligned to the frozen TECH/API boundary.",
                "done_when": "Frontend changes are wired, bounded to the selected scope, and preserve the frozen UI entry/exit contract without bypassing state or guard rules.",
            }
        )
    if assessment["backend_required"]:
        steps.append(
            {
                "task_id": "TASK-003" if assessment["frontend_required"] else "TASK-002",
                "title": "Implement frozen runtime, state, and interface units",
                "workstream": "backend",
                "depends_on": ["TASK-001"],
                "parallel_group": "backend",
                "outputs": backend_paths[:4] or ["runtime-units", "interface-hooks"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                "work": (
                    f"Update only the declared runtime units: {unit_preview}. "
                    f"Honor the frozen contracts and sequence: {interface_preview or 'use upstream interface contracts'}."
                ),
                "done_when": "The listed runtime/state/interface units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.",
            }
        )
    if assessment["migration_required"]:
        migration_task_id = f"TASK-{len(steps) + 1:03d}"
        steps.append(
            {
                "task_id": migration_task_id,
                "title": "Implement migration, compat, and rollback controls",
                "workstream": "migration",
                "depends_on": ["TASK-001"] + ([steps[-1]["task_id"]] if steps else []),
                "parallel_group": "migration",
                "outputs": migration_paths[:4] or ["migration-cutover-plan", "rollback-guardrails"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-003"]),
                "work": integration_preview or "Define compat-mode, rollout, rollback, or cutover sequencing needed to land the change safely.",
                "done_when": "Migration prerequisites, guardrails, fallback actions, and rollback sequencing are explicit enough for downstream execution and are tied to named touch points.",
            }
        )
    integration_task_id = f"TASK-{len(steps) + 1:03d}"
    steps.append(
        {
            "task_id": integration_task_id,
            "title": "Integrate flow boundaries and collect acceptance evidence",
            "workstream": "integration",
            "depends_on": [step["task_id"] for step in steps if step["task_id"] != "TASK-001"],
            "parallel_group": "integration",
            "outputs": ["integration-hooks-wired", "acceptance-evidence", "smoke-gate-ready-inputs"],
            "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002", "AC-003"]),
            "work": "Wire the concrete sequence, integration hooks, and acceptance evidence into the package handoff. " + (sequence_preview or "Follow the frozen upstream runtime sequence."),
            "done_when": (
                "The integrated flow preserves the frozen entry/exit sequence, exposes the required evidence for each acceptance check, and can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries."
                if not runner_package
                else "The package can enter template.dev.feature_delivery_l2 while preserving the frozen execution-runner lifecycle and operator/runtime boundary."
            ),
        }
    )
    handoff_task_id = f"TASK-{len(steps) + 1:03d}"
    steps.append(
        {
            "task_id": handoff_task_id,
            "title": "Assemble smoke gate input and downstream handoff",
            "workstream": "evidence",
            "depends_on": [integration_task_id],
            "parallel_group": "finalize",
            "outputs": ["dev-evidence-plan.json", "smoke-gate-subject.json", "handoff-to-feature-delivery.json"],
            "acceptance_refs": [str(item.get("ref") or "").strip() for item in checkpoints or [] if str(item.get("ref") or "").strip()],
            "work": "Finalize acceptance coverage, smoke-gate inputs, and downstream handoff artifacts without inventing new scope or rewriting upstream truth.",
            "done_when": "Each acceptance check maps to concrete task output and evidence, and downstream execution can start without reopening upstream FEAT/TECH docs.",
        }
    )
    return steps


def acceptance_checkpoints(
    feature: dict[str, Any],
    package: Any | None = None,
    assessment: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    if package is not None:
        runner_package = is_execution_runner_package(feature, package)
        units = package.tech_json.get("tech_design", {}).get("implementation_unit_mapping") or []
        unit_paths = ", ".join(units[:4]) or "the declared runtime units"
        contracts = ensure_list(package.tech_json.get("tech_design", {}).get("interface_contracts"))
        main_sequence = ensure_list(package.tech_json.get("tech_design", {}).get("main_sequence"))
        integration_points = ensure_list(package.tech_json.get("tech_design", {}).get("integration_points"))
        migration_required = bool((assessment or {}).get("migration_required"))
        observable_outcomes = ensure_list((feature.get("acceptance_and_testability") or {}).get("observable_outcomes"))

        checkpoints = [
            {
                "ref": "AC-001",
                "scenario": "Frozen touch set is implemented without design drift.",
                "expectation": f"The declared touch set is updated and evidence-backed: {unit_paths}.",
            },
            {
                "ref": "AC-002",
                "scenario": "Frozen contracts and runtime sequence execute through the implementation entry.",
                "expectation": "Implementation evidence proves the frozen contract hooks and state transitions are wired. "
                + (contracts[0] if contracts else "Use the upstream interface contracts without shadow redefinition."),
            },
            {
                "ref": "AC-003",
                "scenario": (
                    "Execution-runner lifecycle remains boundary-safe and ready for feature delivery."
                    if runner_package
                    else "Downstream handoff remains boundary-safe and ready for feature delivery."
                ),
                "expectation": (
                    "The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, "
                    "does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready."
                    if runner_package
                    else "The implementation package exposes only the frozen pending visibility / boundary handoff behavior, "
                    "keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready."
                ),
            },
        ]
        if main_sequence:
            checkpoints[1]["expectation"] += f" Main sequence evidence covers: {'; '.join(main_sequence[:3])}."
        if integration_points:
            checkpoints[2]["expectation"] += f" Integration evidence covers: {'; '.join(integration_points[:2])}."
        if observable_outcomes:
            checkpoints[2]["expectation"] += f" Observable outcomes remain externally visible: {'; '.join(observable_outcomes[:2])}."
        return checkpoints

    checkpoints: list[dict[str, str]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        if not isinstance(check, dict):
            continue
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": normalize_boundary_text(str(check.get("scenario") or "").strip()) or f"acceptance-{index}",
                "expectation": normalize_boundary_text(str(check.get("then") or "").strip()) or "Expectation must be confirmed during execution.",
            }
        )
    if checkpoints:
        return checkpoints

    acceptance = feature.get("acceptance_and_testability") or {}
    criteria = ensure_list(acceptance.get("acceptance_criteria"))
    outcomes = ensure_list(acceptance.get("observable_outcomes"))
    authoritative_artifact = str((feature.get("product_objects_and_deliverables") or {}).get("authoritative_output") or feature.get("authoritative_artifact") or "").strip()
    for index, criterion in enumerate(criteria, start=1):
        if outcomes:
            expectation = outcomes[min(index - 1, len(outcomes) - 1)]
        elif authoritative_artifact:
            expectation = f"{authoritative_artifact} 可被外部观察并作为唯一 authoritative result。"
        else:
            expectation = "该验收结果必须形成可外部观察的 authoritative outcome。"
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": normalize_boundary_text(criterion.strip()) or f"acceptance-{index}",
                "expectation": normalize_boundary_text(str(expectation).strip()) or "Expectation must be confirmed during execution.",
            }
        )
    return checkpoints


STALE_REENTRY_RULE = "keeping approval and re-entry semantics outside this feat"


def normalize_boundary_text(text: str) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return normalized
    if STALE_REENTRY_RULE in normalized.lower():
        return (
            "Submission completion only exposes authoritative handoff and pending visibility; "
            "decision-driven revise/retry routing stays in runtime while gate decision issuance and formal publication semantics remain outside this FEAT."
        )
    return normalized

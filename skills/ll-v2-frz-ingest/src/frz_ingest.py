"""frz-ingest CLI entry point — Compile and freeze a Complete Design Package.

Usage:
    python frz_ingest.py --input <design-package-dir> --output <output-dir> [--src-id SRC-001] [--slug my-feature] [--project-type generic]
"""

from __future__ import annotations

import argparse
import enum
import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path

# --- Logging initialization (earliest possible point) ---
_ingest_dir = Path(__file__).resolve().parent.parent
_log_dir = _ingest_dir / "logs"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=_log_dir / "frz-ingest.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("frz.ingest")
logger.info("frz_ingest.py starting up")

# --- Path resolution: environment-driven, decoupled from directory depth ---
# Priority: FRZ_CLI_LIB_PATH env var > upward search from __file__ > upward search from cwd > fallback

def _find_cli_lib(start: Path) -> Path | None:
    """Walk upward from start looking for cli/lib/frz_cli/."""
    for parent in [start, *start.parents]:
        candidate = parent / "cli" / "lib"
        if (candidate / "frz_cli").is_dir():
            return candidate
    return None


_cli_lib_path = os.environ.get("FRZ_CLI_LIB_PATH")
if _cli_lib_path:
    _lib_root = Path(_cli_lib_path).resolve()
    logger.info(f"Using CLI_LIB_PATH from env: {_lib_root}")
else:
    # Try auto-discovery without hard-coding directory depth
    # 1. Search upward from this script's resolved location (handles symlinks)
    _lib_root = _find_cli_lib(_ingest_dir)
    # 2. Search upward from current working directory (handles copied skills)
    if _lib_root is None:
        _lib_root = _find_cli_lib(Path.cwd())
    # 3. Final fallback: the original LEE-Lite project root
    if _lib_root is None:
        _fallback = Path("/Users/zengle/git/LEE-Lite/cli/lib")
        if (_fallback / "frz_cli").is_dir():
            _lib_root = _fallback
        else:
            logger.error("Could not auto-discover cli/lib. Set FRZ_CLI_LIB_PATH env var.")
            print("ERROR: Could not find cli/lib/frz_cli/. Set FRZ_CLI_LIB_PATH.", file=sys.stderr)
            sys.exit(1)
    logger.info(f"Auto-discovered CLI lib root: {_lib_root}")

if str(_lib_root) not in sys.path:
    sys.path.insert(0, str(_lib_root))
    logger.debug(f"Added to sys.path: {_lib_root}")

from frz_cli.alignment import check_alignment
from frz_cli.compiler import compile_ssot_chain
from frz_cli.completeness import check_completeness
from frz_cli.dimension_quality import check_dimension_quality, all_dimensions_grade_a, get_quality_report
from frz_cli.drift import detect_drift
from frz_cli.freezer import build_frz_package, save_checkpoint, _freeze_ssot_chain
from frz_cli.parser import parse_design_package
from frz_cli.test_generator import generate_acceptance_tests


def _derive_slug(text: str) -> str:
    """Convert arbitrary text to kebab-case slug for file naming."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "ssot"


def _discover_and_copy_prototype_artifacts(
    input_dir: Path, prototype_dir: Path, slug: str, src_id: str, module_filter: str | None = None
) -> list[Path]:
    """Discover HTML prototype files in input dir and copy to prototype_dir.

    Scans recursively for .html files (common prototype artifact format).
    Copies each to prototype_dir with a deterministic naming scheme.
    Filters by module_filter if provided (e.g. 'M12' matches 'proto-m12-*.html').
    Returns list of copied file paths (relative to prototype_dir's parent).
    """
    copied: list[Path] = []
    html_files = sorted(input_dir.rglob("*.html"))
    if not html_files:
        logger.info("No .html prototype files found in input directory")
        return copied

    idx = 0
    for src_path in html_files:
        # Skip non-matching module files
        if module_filter is not None:
            name_upper = src_path.name.upper()
            mf = module_filter.upper()
            if mf not in name_upper:
                logger.debug(f"Skipping prototype {src_path.name} (does not match module filter {module_filter})")
                continue
        idx += 1
        # Preserve subdirectory structure under prototype_dir
        rel_path = src_path.relative_to(input_dir)
        # Use deterministic naming: PROTO-{src_id}-{idx:03d}__{slug}-{original_name}
        dest_name = f"PROTO-{src_id}-{idx:03d}__{slug}-{rel_path.name}"
        dest_path = prototype_dir / dest_name
        try:
            shutil.copy2(src_path, dest_path)
            copied.append(dest_path)
            logger.info(f"Copied prototype: {src_path} -> {dest_path}")
        except Exception as e:
            logger.warning(f"Failed to copy prototype {src_path}: {e}")

    return copied


def _extract_source_gaps(dim_qualities: list, completeness: Any, alignment: Any) -> dict[str, Any]:
    """Extract source-document gaps from quality/comp/alignment checks for human traceability.

    Generates a structured gap list that maps each blocker back to the source
    document location and suggested fix.  Output is written as
    MISSING-SOURCE-{src_id}__{slug}.yaml alongside the quality report.
    """
    import datetime
    gaps: list[dict[str, Any]] = []
    gap_id = 0

    # --- API dimension blockers ---
    api_q = next((q for q in dim_qualities if q.dimension == "api"), None)
    if api_q:
        for blocker in api_q.blockers:
            # Parse "Endpoint METHOD PATH missing: FIELD1, FIELD2"
            m = re.search(r"Endpoint\s+(\S+)\s+(\S+)\s+missing:\s+(.+)", blocker)
            if m:
                gap_id += 1
                method, path, fields_str = m.groups()
                fields = [f.strip() for f in fields_str.split(",")]
                # Map endpoint to likely source doc
                doc_hint = "architecture_design/api_contract.md"
                if "training-state" in path:
                    doc_hint = "03_session_evaluation_training_state.md (API 表缺失)"
                elif "training-plan" in path:
                    doc_hint = "02_structured_training_plan.md 或 12_implementation_scope.md (API 表缺失)"
                elif "decisions" in path:
                    doc_hint = "04_decision_engine.md 或 09_user_stories_and_acceptance_criteria.md (AC 引用但无 schema)"
                elif "conversation" in path or "ai" in path:
                    doc_hint = "05_context_and_ai_coach.md (API 契约未定义)"
                elif "goal-feasibility" in path:
                    doc_hint = "02_structured_training_plan.md (API 表缺失)"
                elif "capability" in path:
                    doc_hint = "01_runner_knowledge_profile.md (API 表缺失)"
                gaps.append({
                    "gap_id": f"GAP-{gap_id:03d}",
                    "dimension": "api",
                    "severity": "P1",
                    "location": f"{method} {path}",
                    "missing": fields,
                    "root_cause": "源文档 API 表未定义该端点的完整 schema",
                    "suggested_fix": f"在 {doc_hint} 中补充 {', '.join(fields)}",
                    "source_doc_hint": doc_hint,
                    "blocker_text": blocker,
                })
            else:
                # Other API blockers (invalid path, mixed keys, etc.)
                gap_id += 1
                gaps.append({
                    "gap_id": f"GAP-{gap_id:03d}",
                    "dimension": "api",
                    "severity": "P1",
                    "location": "API endpoint",
                    "missing": [blocker],
                    "root_cause": "API 端点结构性问题",
                    "suggested_fix": "检查 API 表格式和字段定义",
                    "source_doc_hint": "architecture_design/api_contract.md",
                    "blocker_text": blocker,
                })

    # --- Other dimension blockers ---
    for q in dim_qualities:
        if q.dimension == "api":
            continue
        for blocker in q.blockers:
            gap_id += 1
            gaps.append({
                "gap_id": f"GAP-{gap_id:03d}",
                "dimension": q.dimension,
                "severity": "P1",
                "location": q.dimension,
                "missing": [blocker],
                "root_cause": f"{q.dimension} 维度核心内容缺失",
                "suggested_fix": f"补充 {q.dimension} 设计文档对应章节",
                "source_doc_hint": f"{q.dimension}_design/",
                "blocker_text": blocker,
            })

    # --- Completeness missing items ---
    for item in getattr(completeness, "missing_items", []) or []:
        gap_id += 1
        dim = item.get("dimension", "unknown")
        gaps.append({
            "gap_id": f"GAP-{gap_id:03d}",
            "dimension": dim,
            "severity": item.get("severity", "P2"),
            "location": item.get("field", "unknown"),
            "missing": [item.get("reason", "")],
            "root_cause": item.get("reason", ""),
            "suggested_fix": item.get("suggested_fix", ""),
            "source_doc_hint": f"{dim}_design/",
            "blocker_text": str(item),
        })

    # --- Alignment issues ---
    for issue in getattr(alignment, "issues", []) or []:
        gap_id += 1
        gaps.append({
            "gap_id": f"GAP-{gap_id:03d}",
            "dimension": "alignment",
            "severity": issue.get("severity", "medium").upper(),
            "location": issue.get("location", "unknown"),
            "missing": [issue.get("description", "")],
            "root_cause": "跨维度对齐缺失",
            "suggested_fix": issue.get("suggested_fix", ""),
            "source_doc_hint": "product_design/",
            "blocker_text": str(issue),
        })

    return {
        "source_gaps": {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_gaps": len(gaps),
            "gap_summary": {
                "p1_count": sum(1 for g in gaps if g.get("severity") == "P1"),
                "p2_count": sum(1 for g in gaps if g.get("severity") == "P2"),
                "by_dimension": _count_by(gaps, "dimension"),
            },
            "gaps": gaps,
        }
    }


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        k = item.get(key, "unknown")
        counts[k] = counts.get(k, 0) + 1
    return counts


def _build_required_sections(dim_qualities: list) -> list[str]:
    """Map failed quality dimensions to required design document sections."""
    section_map = {
        "src": [
            "business_design: product_vision (实质内容，非文档标题)",
            "business_design: triggering_scenarios",
            "business_design: non_goals / Out of Scope",
        ],
        "tech": [
            "architecture_design: sync_async_strategy (同步/异步策略)",
            "architecture_design: non_functional_requirements (性能/并发/降级)",
            "engineering_design: risks (已知风险)",
        ],
        "arch": [
            "architecture_design: layering / 模块结构 (Transport/Handler/Service/Repository)",
            "architecture_design: storage_design / 数据库表结构",
            "architecture_design: integration_points / 外部依赖",
        ],
        "api": [
            "architecture_design: API 端点参数定义 (request/response schema)",
            "architecture_design: error_codes (错误码定义)",
            "architecture_design: sequence_diagrams (Mermaid/PlantUML 时序图)",
        ],
        "ui": [
            "ux_design: prototype / 用户旅程原型 (HTML 或引用)",
        ],
        "impl": [
            "engineering_design: test_guidance / 边界条件 + 测试分层策略",
            "engineering_design: excluded_files (明确不碰的文件列表)",
            "product_design: AC 触发条件 (Given 子句)",
        ],
    }
    required: list[str] = []
    for q in dim_qualities:
        if q.grade != "A" and q.dimension in section_map:
            required.extend(section_map[q.dimension])
    return list(dict.fromkeys(required))


def _to_plain_dict(obj: object) -> object:
    if isinstance(obj, enum.Enum):
        return obj.value
    if hasattr(obj, "__dict__"):
        return {k: _to_plain_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, dict):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain_dict(v) for v in obj]
    return obj


def _run_parse(input_dir: Path, tmp_dir: Path, module_filter: str | None = None) -> tuple[dict[str, Any], str | None]:
    """Step 1: Parse design package and save to tmp dir.

    Returns (design_package, detected_module_filter).
    """
    logger.debug("Step 1: Parsing design package")
    design_package = parse_design_package(input_dir, module_filter=module_filter)
    dp_path = tmp_dir / "design_package.json"
    with open(dp_path, "w", encoding="utf-8") as f:
        json.dump(design_package, f, ensure_ascii=False, indent=2)
    logger.info(f"Design package written: {dp_path}")
    print(f"Design package written: {dp_path}")
    # Return the auto-detected module filter from parse_design_package
    # (it may have detected from directory name even if not passed explicitly)
    detected_filter = module_filter
    if detected_filter is None:
        # Replicate auto-detection logic from parse_design_package
        name = input_dir.name
        m = re.search(r'[Mm](\d+)', name)
        if m:
            detected_filter = f"M{m.group(1)}"
    return design_package, detected_filter


def _run_gap_report(design_package: dict[str, Any], tmp_dir: Path) -> dict[str, Any]:
    """Step 2: Generate gap report for agent-driven semantic extraction."""
    from frz_cli.parser import generate_gap_report
    logger.debug("Step 2: Generating gap report")
    gap_report = generate_gap_report(design_package)
    gaps_path = tmp_dir / "gaps.json"
    with open(gaps_path, "w", encoding="utf-8") as f:
        json.dump(gap_report, f, ensure_ascii=False, indent=2)
    logger.info(f"Gap report written: {gaps_path}")
    print(f"Gap report written: {gaps_path}")
    if gap_report["has_gaps"]:
        print(f"\nWARNING: {gap_report['total_gaps']} field(s) need agent semantic extraction.")
        for g in gap_report["gaps"]:
            print(f"  - {g['dimension']}.{g['field']}: {g['description']}")
        print("\nNext: Run skill agent semantic extraction step, then re-run with --step compile.")
    else:
        print("No gaps detected. Proceeding to compile.")
    return gap_report


def _run_compile(
    design_package: dict[str, Any],
    args: argparse.Namespace,
    output_dir: Path,
) -> int:
    """Step 3+: Compile SSOT chain, run checks, and freeze."""
    slug = _derive_slug(args.slug) if args.slug else _derive_slug(Path(args.input).name)
    logger.info(f"project_type={args.project_type}, compiling to {output_dir}")

    # When compiling a single module, skip cross-module semantic rules
    module_filter = getattr(args, "module_filter", None)
    check_project_type = "generic" if module_filter else args.project_type

    # Completeness check (input-side)
    logger.debug("Step 3: Running completeness check")
    completeness = check_completeness(
        design_package,
        project_type=check_project_type,
        rules_config_path=args.rules_config,
    )
    if completeness.verdict == "blocked":
        logger.error(f"BLOCKED: {completeness.missing_items}")
        print(f"BLOCKED: {completeness.missing_items}", file=sys.stderr)
        return 10

    # Compile
    logger.debug("Step 4: Compiling SSOT chain")
    chain = compile_ssot_chain(design_package, args.src_id)

    # Post-Compilation Validation (PCV)
    logger.debug("Step 4.5: Post-compilation validation")
    completeness = check_completeness(
        design_package,
        compiled_chain=chain,
        project_type=check_project_type,
        rules_config_path=args.rules_config,
    )
    if completeness.verdict == "blocked":
        logger.error(f"BLOCKED (PCV): {completeness.missing_items}")
        print(f"BLOCKED (PCV): {completeness.missing_items}", file=sys.stderr)
        return 10

    # Alignment check
    logger.debug("Step 5: Running alignment check")
    alignment = check_alignment(
        chain["src"], chain["epics"], chain["feats"],
        chain["techs"], chain["archs"], chain["apis"], chain["uis"],
    )

    # Drift detection
    logger.debug("Step 6: Running drift detection")
    drift = detect_drift(
        design_package, chain["src"], chain["feats"],
        chain["techs"], chain["archs"], chain["apis"], chain["uis"],
    )

    # Dimension Quality Gate (ADR-056 §step_4_5)
    logger.debug("Step 7: Running dimension quality gate")
    dim_qualities = check_dimension_quality(chain)
    quality_report = get_quality_report(dim_qualities)
    if not all_dimensions_grade_a(dim_qualities):
        failed = [q for q in dim_qualities if q.grade != "A"]
        logger.warning(f"QUALITY GATE BLOCKED: {len(failed)} dimensions below A-grade")
        print(f"QUALITY GATE BLOCKED: {len(failed)} dimensions below A-grade", file=sys.stderr)
        for q in failed:
            print(f"  {q.dimension}: score={q.score} grade={q.grade} blockers={q.blockers}", file=sys.stderr)

    # --- Prepare v2 directory structure per ADR-057 ---
    v2_base = output_dir / "ssot" / "v2"
    frz_dir = v2_base / "frz"
    src_dir = v2_base / "src"
    tech_dir = v2_base / "tech"
    arch_dir = v2_base / "arch"
    api_dir = v2_base / "api"
    ui_dir = v2_base / "ui"
    impl_dir = v2_base / "impl"
    prototype_dir = v2_base / "prototype"
    quality_dir = v2_base / "quality"

    for d in (frz_dir, src_dir, tech_dir, arch_dir, api_dir, ui_dir, impl_dir, prototype_dir, quality_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Generate acceptance tests
    logger.debug("Step 8: Generating acceptance tests")
    acceptance_test_cases = generate_acceptance_tests(
        chain["feats"], chain["apis"], chain["uis"], design_package
    )

    # --- Discover and copy prototype artifacts ---
    logger.debug("Step 8.5: Discovering prototype artifacts")
    _input_dir = Path(args.input)
    prototype_artifacts = _discover_and_copy_prototype_artifacts(
        _input_dir, prototype_dir, slug, args.src_id,
        module_filter=getattr(args, "module_filter", None)
    )

    import yaml

    frozen_chain = _freeze_ssot_chain(chain)

    # --- Save SSOT chain documents ---
    src_filename = f"SRC-{args.src_id}__{slug}.yaml"
    src_path = src_dir / src_filename
    with open(src_path, "w", encoding="utf-8") as f:
        yaml.dump({"src": _to_plain_dict(frozen_chain["src"])}, f, allow_unicode=True, sort_keys=False)

    tech_filename = f"TECH-{args.src_id}-001__{slug}.yaml"
    tech_path = tech_dir / tech_filename
    with open(tech_path, "w", encoding="utf-8") as f:
        yaml.dump({"tech": _to_plain_dict(frozen_chain["techs"])}, f, allow_unicode=True, sort_keys=False)

    arch_filename = f"ARCH-{args.src_id}-001__{slug}.yaml"
    arch_path = arch_dir / arch_filename
    with open(arch_path, "w", encoding="utf-8") as f:
        yaml.dump({"arch": _to_plain_dict(frozen_chain["archs"])}, f, allow_unicode=True, sort_keys=False)

    api_filename = f"API-{args.src_id}-001__{slug}.yaml"
    api_path = api_dir / api_filename
    with open(api_path, "w", encoding="utf-8") as f:
        yaml.dump({"api": _to_plain_dict(frozen_chain["apis"])}, f, allow_unicode=True, sort_keys=False)

    ui_filename = f"UI-{args.src_id}-001__{slug}.yaml"
    ui_path = ui_dir / ui_filename
    with open(ui_path, "w", encoding="utf-8") as f:
        yaml.dump({"ui": _to_plain_dict(frozen_chain["uis"])}, f, allow_unicode=True, sort_keys=False)

    impl_filenames: list[str] = []
    for idx, impl in enumerate(frozen_chain["impls"]):
        impl_filename = f"IMPL-{args.src_id}-{idx + 1:03d}__{slug}.yaml"
        impl_filenames.append(impl_filename)
        impl_path = impl_dir / impl_filename
        with open(impl_path, "w", encoding="utf-8") as f:
            yaml.dump({"impl": _to_plain_dict(impl)}, f, allow_unicode=True, sort_keys=False)

    common_impl_filename: str | None = None
    if frozen_chain.get("common_impl_context"):
        common_impl_filename = f"COMMON-IMPL-{args.src_id}__{slug}.yaml"
        common_impl_path = impl_dir / common_impl_filename
        with open(common_impl_path, "w", encoding="utf-8") as f:
            yaml.dump({"common_impl_context": _to_plain_dict(frozen_chain["common_impl_context"])}, f, allow_unicode=True, sort_keys=False)

    def _rel(path: Path) -> str:
        return str(path.relative_to(output_dir).as_posix())

    frozen_ssot_chain = {
        "src_ref": _rel(src_path),
        "tech_refs": [_rel(tech_path)],
        "arch_refs": [_rel(arch_path)],
        "api_refs": [_rel(api_path)],
        "ui_refs": [_rel(ui_path)] if chain["uis"] else [],
        "impl_refs": [_rel(impl_dir / fn) for fn in impl_filenames],
        "prototype_refs": [_rel(p) for p in prototype_artifacts],
    }
    if common_impl_filename:
        frozen_ssot_chain["common_impl_ref"] = _rel(impl_dir / common_impl_filename)

    evidence_refs = {
        "source_docs": sorted(str(p.relative_to(_input_dir)) for p in _input_dir.rglob("*") if p.is_file() and not p.name.startswith(".")),
        "compilation_log": _rel(frz_dir / f"FRZ-{args.src_id}-001__{slug}.compile.log"),
    }

    quality_filename = f"QUALITY-REPORT-{args.src_id}__{slug}.yaml"
    quality_path = quality_dir / quality_filename
    with open(quality_path, "w", encoding="utf-8") as f:
        yaml.dump({"quality_report": quality_report}, f, allow_unicode=True, sort_keys=False)

    source_gaps = _extract_source_gaps(dim_qualities, completeness, alignment)
    gaps_path = quality_dir / f"MISSING-SOURCE-{args.src_id}__{slug}.yaml"
    with open(gaps_path, "w", encoding="utf-8") as f:
        yaml.dump(source_gaps, f, allow_unicode=True, sort_keys=False)

    if not all_dimensions_grade_a(dim_qualities):
        human_review = {
            "human_review": {
                "blocked_dimensions": [
                    {"dimension": q.dimension, "score": q.score, "grade": q.grade, "blockers": q.blockers}
                    for q in dim_qualities if q.grade != "A"
                ],
                "action": "补充设计文档对应章节后重新运行 frz-ingest",
                "required_sections": _build_required_sections(dim_qualities),
            }
        }
        human_path = quality_dir / f"HUMAN-REVIEW-{args.src_id}__{slug}.yaml"
        with open(human_path, "w", encoding="utf-8") as f:
            yaml.dump(human_review, f, allow_unicode=True, sort_keys=False)

    logger.debug("Step 9: Building FRZ package")
    try:
        frz_pkg = build_frz_package(
            frz_ref=f"FRZ-{args.src_id}-001",
            version="v1.0",
            source_package_ref=str(Path(args.input)),
            chain=chain,
            acceptance_test_cases=acceptance_test_cases,
            completeness_check={"verdict": completeness.verdict, "missing_items": completeness.missing_items, "warnings": completeness.warnings},
            alignment_check={"verdict": alignment.verdict, "issues": alignment.issues},
            drift_check={"verdict": drift.verdict, "drift_items": drift.drift_items},
            dimension_quality_check=quality_report,
            frozen_ssot_chain=frozen_ssot_chain,
            evidence_refs=evidence_refs,
        )
    except Exception as e:
        logger.exception("Freeze step failed")
        print(f"FREEZE ERROR: {e}", file=sys.stderr)
        return 20

    if args.checkpoint:
        checkpoint = {
            "frz_ref": frz_pkg.frz_ref,
            "src_id": args.src_id,
            "steps": ["parse", "completeness", "compile", "alignment", "drift", "acceptance_tests", "freeze"],
            "completeness": completeness.verdict,
            "alignment": alignment.verdict,
            "drift": drift.verdict,
        }
        save_checkpoint(Path(args.checkpoint), checkpoint)

    frz_filename = f"{frz_pkg.frz_ref}__{slug}.yaml"
    frz_path = frz_dir / frz_filename
    with open(frz_path, "w", encoding="utf-8") as f:
        yaml.dump({"frz_package": _to_plain_dict(frz_pkg.__dict__)}, f, allow_unicode=True, sort_keys=False)

    logger.info(f"FRZ Package written: {frz_path}")
    logger.info(f"SSOT chain written: {v2_base}")
    logger.info(f"Quality report written: {quality_path}")
    print(f"FRZ Package written: {frz_path}")
    print(f"SSOT chain written: {v2_base}")
    print(f"Quality report written: {quality_path}")
    dim_summary = ", ".join(f"{q.dimension}={q.grade}({q.score})" for q in dim_qualities)
    logger.info(f"Verdict: completeness={completeness.verdict}, alignment={alignment.verdict}, drift={drift.verdict}, quality=[{dim_summary}]")
    print(f"Verdict: completeness={completeness.verdict}, alignment={alignment.verdict}, drift={drift.verdict}, quality=[{dim_summary}]")
    if not all_dimensions_grade_a(dim_qualities):
        logger.warning("Quality gate blocked — outputs written for human review")
        return 30
    logger.info("frz-ingest completed successfully")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="frz-ingest: Compile and freeze design packages")
    parser.add_argument("--input", required=True, help="Path to Complete Design Package directory")
    parser.add_argument("--output", required=True, help="Output directory for FRZ Package")
    parser.add_argument("--src-id", default="SRC-001", help="SRC identifier")
    parser.add_argument("--slug", help="Human-readable slug for file naming (kebab-case)")
    parser.add_argument("--checkpoint", help="Checkpoint file path for idempotent retry")
    parser.add_argument("--project-type", default="generic", help="Project type for rule selection (generic, lee-lite, ...)")
    parser.add_argument("--rules-config", help="Path to project-specific completeness rules YAML")
    parser.add_argument("--module-filter", help="Module identifier to filter input files (e.g., 'M12'). Only files whose names contain this identifier (or are cross-module generic docs) will be processed. Auto-detected from directory name if not provided.")
    parser.add_argument(
        "--step",
        choices=["parse", "gap-report", "compile", "full"],
        default="full",
        help=(
            "Execution step. "
            "parse = Tier 2 extraction only; "
            "gap-report = detect missing fields for agent; "
            "compile = compile SSOT after agent fixes; "
            "full = run everything (default)"
        ),
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Shared tmp dir for inter-step state
    tmp_dir = output_dir / ".frz-tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    module_filter = getattr(args, "module_filter", None)

    if args.step == "parse":
        _run_parse(input_dir, tmp_dir, module_filter=module_filter)
        return 0

    if args.step == "gap-report":
        dp_path = tmp_dir / "design_package.json"
        if not dp_path.exists():
            design_package, _ = _run_parse(input_dir, tmp_dir, module_filter=module_filter)
        else:
            with open(dp_path, encoding="utf-8") as f:
                design_package = json.load(f)
        _run_gap_report(design_package, tmp_dir)
        return 0

    if args.step == "compile":
        dp_path = tmp_dir / "design_package.json"
        if not dp_path.exists():
            print("ERROR: design_package.json not found. Run --step parse first.", file=sys.stderr)
            return 1
        with open(dp_path, encoding="utf-8") as f:
            design_package = json.load(f)
        return _run_compile(design_package, args, output_dir)

    # --step full (default)
    design_package, detected_filter = _run_parse(input_dir, tmp_dir, module_filter=module_filter)
    # Save detected filter to args for downstream use
    if detected_filter and not getattr(args, "module_filter", None):
        args.module_filter = detected_filter
    gap_report = _run_gap_report(design_package, tmp_dir)
    if gap_report.get("has_gaps"):
        print("\nGaps detected. In full mode, you should use --step parse + agent fix + --step compile.")
        print("Continuing with compile using Tier 2 extraction only...\n")
    return _run_compile(design_package, args, output_dir)


if __name__ == "__main__":
    sys.exit(main())

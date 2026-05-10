#!/usr/bin/env python3
"""Run full FRZ→SRC→EPIC→FEAT chain extraction for FRZ-055."""

from pathlib import Path
import json
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add skills to path
SKILLS_ROOT = PROJECT_ROOT / "skills"
for skill_dir in SKILLS_ROOT.iterdir():
    if skill_dir.is_dir() and (skill_dir / "scripts").exists():
        if str(skill_dir / "scripts") not in sys.path:
            sys.path.insert(0, str(skill_dir / "scripts"))

from cli.lib.frz_registry import get_frz
from cli.lib.frz_schema import FRZPackage, _parse_frz_dict
import yaml


def load_frz_from_registry(frz_id: str, repo_root: Path) -> FRZPackage:
    """Load FRZ package from registry."""
    frz_record = get_frz(repo_root, frz_id)
    if not frz_record:
        raise RuntimeError(f"FRZ {frz_id} not found in registry")

    package_ref = Path(frz_record["package_ref"])
    if not package_ref.is_absolute():
        package_ref = repo_root / package_ref

    data = yaml.safe_load(package_ref.read_text(encoding="utf-8"))
    inner = data.get("frz_package", data)
    return _parse_frz_dict(inner)


def run_epic_extraction(frz_package: FRZPackage, frz_id: str, repo_root: Path):
    """Run FRZ→EPIC extraction."""
    print(f"\n{'='*60}")
    print(f"Running EPIC extraction for {frz_id}")
    print(f"{'='*60}")

    # Import the extract module
    sys.path.insert(0, str(SKILLS_ROOT / "ll-product-src-to-epic" / "scripts"))
    from src_to_epic_extract import extract_epic_from_frz_logic

    # Create minimal src package dict
    src_package = {
        "src_root_id": f"SRC-from-{frz_id}"
    }

    # Run extraction
    result = extract_epic_from_frz_logic(frz_package, src_package, frz_id, repo_root)

    # Save output
    output_dir = repo_root / "artifacts" / "epic-extract" / frz_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save epic-freeze.json
    epic_json = output_dir / "epic-freeze.json"
    epic_json.write_text(json.dumps(result.epic_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ EPIC JSON saved to: {epic_json}")

    # Save epic-freeze.md
    epic_md = output_dir / "epic-freeze.md"
    md_content = [
        f"# {result.epic_payload.get('title', 'EPIC')}",
        "",
        "## Epic Intent",
        "",
        result.epic_payload.get("epic_intent", ""),
        "",
        "## Capability Scope",
        "",
    ]
    for item in result.epic_payload.get("scope", []):
        md_content.append(f"- {item}")
    md_content.extend([
        "",
        "## Actors and Roles",
        "",
    ])
    for actor in result.epic_payload.get("actors_and_roles", []):
        md_content.append(f"- {actor.get('role', '')}: {actor.get('responsibility', '')}")
    md_content.extend([
        "",
        "## Epic Success Criteria",
        "",
    ])
    for item in result.epic_payload.get("epic_success_criteria", []):
        md_content.append(f"- {item}")

    epic_md.write_text("\n".join(md_content), encoding="utf-8")
    print(f"✓ EPIC Markdown saved to: {epic_md}")

    # Save extraction report
    report = {
        "frz_id": frz_id,
        "ok": result.ok,
        "guard_verdict": result.guard_verdict,
        "anchors_registered": result.anchors_registered,
        "drift_results": result.drift_results,
        "warnings": result.warnings,
    }
    report_path = output_dir / "extraction-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Extraction report saved to: {report_path}")

    print(f"\nEPIC extraction: {'✓ SUCCESS' if result.ok else '✗ FAILED'}")
    print(f"  Guard verdict: {result.guard_verdict}")
    print(f"  Anchors registered: {len(result.anchors_registered)}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")

    return result, output_dir


def run_feat_extraction(frz_package: FRZPackage, frz_id: str, repo_root: Path, epic_payload: dict):
    """Run FRZ→FEAT extraction."""
    print(f"\n{'='*60}")
    print(f"Running FEAT extraction for {frz_id}")
    print(f"{'='*60}")

    # Import the extract module
    sys.path.insert(0, str(SKILLS_ROOT / "ll-product-epic-to-feat" / "scripts"))
    from epic_to_feat_extract import extract_feat_from_frz_logic

    # Create minimal epic package dict
    epic_package = {
        "epic_freeze_ref": epic_payload.get("epic_freeze_ref", frz_id),
        "src_root_id": epic_payload.get("src_root_id", ""),
    }

    # Run extraction
    result = extract_feat_from_frz_logic(frz_package, epic_package, frz_id, repo_root)

    # Save output
    output_dir = repo_root / "artifacts" / "feat-extract" / frz_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save feat-freeze.json
    feat_json = output_dir / "feat-freeze.json"
    feat_json.write_text(json.dumps(result.feat_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ FEAT JSON saved to: {feat_json}")

    # Save feat-freeze.md
    feat_md = output_dir / "feat-freeze.md"
    md_content = [
        f"# {result.feat_payload.get('title', 'FEAT')}",
        "",
        "## Bundle Intent",
        "",
        result.feat_payload.get("bundle_intent", ""),
        "",
        "## Features",
        "",
    ]
    for feat in result.feat_payload.get("features", []):
        md_content.append(f"### {feat.get('product_interface', 'Feature')}")
        md_content.append(f"- User Story: {feat.get('user_story', '')}")
        md_content.append(f"- Trigger: {feat.get('trigger', '')}")
        md_content.append("")

    feat_md.write_text("\n".join(md_content), encoding="utf-8")
    print(f"✓ FEAT Markdown saved to: {feat_md}")

    # Save extraction report
    report = {
        "frz_id": frz_id,
        "ok": result.ok,
        "guard_verdict": result.guard_verdict,
        "anchors_registered": result.anchors_registered,
        "drift_results": result.drift_results,
        "warnings": result.warnings,
    }
    report_path = output_dir / "extraction-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Extraction report saved to: {report_path}")

    print(f"\nFEAT extraction: {'✓ SUCCESS' if result.ok else '✗ FAILED'}")
    print(f"  Guard verdict: {result.guard_verdict}")
    print(f"  Anchors registered: {len(result.anchors_registered)}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")

    return result, output_dir


def main():
    frz_id = "FRZ-055"
    repo_root = PROJECT_ROOT

    print(f"\n{'='*60}")
    print(f"FRZ-055 Full SSOT Chain Extraction")
    print(f"{'='*60}")

    # Step 1: Load FRZ
    print(f"\n[1/4] Loading {frz_id} from registry...")
    frz_package = load_frz_from_registry(frz_id, repo_root)
    print(f"✓ {frz_id} loaded successfully")
    print(f"  - Journeys: {len(frz_package.core_journeys)}")
    print(f"  - Entities: {len(frz_package.domain_model)}")
    print(f"  - State Machines: {len(frz_package.state_machine)}")

    # Step 2: SRC already extracted
    print(f"\n[2/4] SRC already extracted to: artifacts/frz-extract/{frz_id}/src/")

    # Step 3: EPIC extraction
    epic_result, epic_dir = run_epic_extraction(frz_package, frz_id, repo_root)

    # Step 4: FEAT extraction
    feat_result, feat_dir = run_feat_extraction(frz_package, frz_id, repo_root, epic_result.epic_payload)

    # Summary
    print(f"\n{'='*60}")
    print(f"Chain extraction complete!")
    print(f"{'='*60}")
    print(f"  FRZ: {frz_id} ✓")
    print(f"  SRC: artifacts/frz-extract/{frz_id}/src/ ✓")
    print(f"  EPIC: {epic_dir}/ ✓")
    print(f"  FEAT: {feat_dir}/ ✓")
    print(f"\nNext steps available:")
    print(f"  - SURFACE: ll-dev-feat-to-surface-map")
    print(f"  - TECH: ll-dev-feat-to-tech")
    print(f"  - IMPL: ll-dev-tech-to-impl")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

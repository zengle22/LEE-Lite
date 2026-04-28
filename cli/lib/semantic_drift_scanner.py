"""Lightweight SSOT semantic drift scanner.

Detects:
- OVERLAY_ELEVATION: Overlay terms (governance/gate/handoff) as primary objects in EPIC/FEAT
- API_DUPLICATE: Same API endpoint declared in multiple API authority files

Usage:
- python -m cli.lib.semantic_drift_scanner --ssot-dir ./ssot
- python -m cli.lib.semantic_drift_scanner --ssot-dir ./ssot --output json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure


# ---------------------------------------------------------------------------
# Enums and dataclasses
# ---------------------------------------------------------------------------


class ViolationType(str, Enum):
    OVERLAY_ELEVATION = "overlay_elevation"
    API_DUPLICATE = "api_authority_duplicate"


@dataclass(frozen=True)
class Violation:
    """Structured violation of semantic drift constraints."""

    type: ViolationType
    severity: str
    file_path: str
    anchor_id: str | None = None
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.type.value}: {self.file_path} - {self.detail}"


@dataclass(frozen=True)
class ScanResult:
    """Result of a full SSOT scan."""

    total_violations: int
    blocker_count: int
    warning_count: int
    violations: list[Violation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_violations": self.total_violations,
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "violations": [
                {
                    "type": v.type.value,
                    "severity": v.severity,
                    "file_path": v.file_path,
                    "anchor_id": v.anchor_id,
                    "detail": v.detail,
                    "evidence": v.evidence,
                }
                for v in self.violations
            ],
        }


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OVERLAY_TERMS = frozenset([
    "governance",
    "gate",
    "handoff",
    "formal",
    "registry",
    "validation",
    "audit",
    "bypass",
    "settlement",
])

# Patterns for API endpoint extraction
API_ENDPOINT_PATTERNS = [
    # Match: "GET /api/v1/users"
    re.compile(r"([A-Z]+)\s+(/[^\s]+)"),
    # Match: "endpoint: /api/v1/users"
    re.compile(r"endpoint:\s*(/[^\s]+)"),
    # Match: "path: /api/v1/users"
    re.compile(r"path:\s*(/[^\s]+)"),
]

MAX_FILE_SIZE = 1024 * 1024  # 1MB


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _safe_read_file(file_path: Path) -> str:
    """Safely read a file, with size limit."""
    ensure(file_path.exists(), "INVALID_PATH", f"File not found: {file_path}")
    ensure(file_path.is_file(), "INVALID_PATH", f"Not a file: {file_path}")
    size = file_path.stat().st_size
    ensure(size <= MAX_FILE_SIZE, "FILE_TOO_LARGE", f"File too large: {file_path}")
    return file_path.read_text(encoding="utf-8", errors="replace")


def _extract_primary_topic(content: str) -> str | None:
    """Heuristic to extract the primary topic from a document.

    Looks for the first heading or prominent line that seems to declare
    what this document is about.
    """
    lines = content.splitlines()[:50]  # Only look at first 50 lines
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for headings
        if line.startswith("# "):
            return line[2:].strip().lower()
        if line.startswith("## "):
            return line[3:].strip().lower()
        if line.startswith("### "):
            return line[4:].strip().lower()
        # Look for "Primary Object" pattern
        if "primary object" in line.lower() or "primary_object" in line:
            if i + 1 < len(lines):
                return lines[i + 1].strip().lower()
            return line.lower()
    # Fallback: look at the first non-empty line
    for line in lines:
        line = line.strip()
        if line and len(line) < 200:
            return line.lower()
    return None


def _extract_endpoints(content: str) -> list[str]:
    """Extract API endpoints from file content."""
    endpoints: list[str] = []
    # Try all patterns
    for pattern in API_ENDPOINT_PATTERNS:
        matches = pattern.findall(content)
        for match in matches:
            if isinstance(match, tuple):
                # For "GET /path" pattern, combine method + path
                endpoint = f"{match[0]} {match[1]}"
            else:
                endpoint = match
            if endpoint and endpoint not in endpoints:
                endpoints.append(endpoint)
    return endpoints


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def scan_overlay_elevation(ssot_dir: Path) -> list[Violation]:
    """Scan for overlay terms being used as primary objects in EPIC/FEAT."""
    violations: list[Violation] = []

    epic_dir = ssot_dir / "epic"
    feat_dir = ssot_dir / "feat"

    for scan_dir in [epic_dir, feat_dir]:
        if not scan_dir.exists() or not scan_dir.is_dir():
            continue

        for file_path in sorted(scan_dir.glob("*.md")):
            try:
                content = _safe_read_file(file_path)
                topic = _extract_primary_topic(content)
                if not topic:
                    continue

                # Check if any overlay term appears in the topic
                found_terms = [term for term in OVERLAY_TERMS if term in topic]
                if found_terms:
                    violations.append(Violation(
                        type=ViolationType.OVERLAY_ELEVATION,
                        severity="blocker",
                        file_path=str(file_path),
                        detail=f"Primary topic appears to be overlay: '{topic}' contains {found_terms}",
                        evidence={"primary_topic": topic, "overlay_terms_found": found_terms},
                    ))
            except CommandError:
                # Skip unreadable files
                continue

    return violations


def scan_api_duplicates(ssot_dir: Path) -> list[Violation]:
    """Scan for duplicate API endpoints across multiple API authority files."""
    violations: list[Violation] = []
    endpoint_map: dict[str, list[str]] = {}

    api_dir = ssot_dir / "api"
    if not api_dir.exists() or not api_dir.is_dir():
        return violations

    for ext in ["*.md", "*.yaml", "*.yml"]:
        for file_path in sorted(api_dir.glob(ext)):
            try:
                content = _safe_read_file(file_path)
                endpoints = _extract_endpoints(content)
                for endpoint in endpoints:
                    if endpoint not in endpoint_map:
                        endpoint_map[endpoint] = []
                    endpoint_map[endpoint].append(str(file_path))
            except CommandError:
                # Skip unreadable files
                continue

    # Check for duplicates
    for endpoint, file_paths in endpoint_map.items():
        if len(file_paths) > 1:
            violations.append(Violation(
                type=ViolationType.API_DUPLICATE,
                severity="blocker",
                file_path=file_paths[0],
                detail=f"API endpoint declared in {len(file_paths)} files: {endpoint}",
                evidence={"endpoint": endpoint, "files": file_paths},
            ))

    return violations


def scan_ssot(ssot_dir: Path) -> ScanResult:
    """Scan SSOT directory for semantic drift."""
    ensure(ssot_dir.exists(), "INVALID_PATH", f"SSOT directory not found: {ssot_dir}")
    ensure(ssot_dir.is_dir(), "INVALID_PATH", f"Not a directory: {ssot_dir}")

    all_violations: list[Violation] = []
    all_violations.extend(scan_overlay_elevation(ssot_dir))
    all_violations.extend(scan_api_duplicates(ssot_dir))

    blocker_count = sum(1 for v in all_violations if v.severity == "blocker")
    warning_count = sum(1 for v in all_violations if v.severity == "warning")

    return ScanResult(
        total_violations=len(all_violations),
        blocker_count=blocker_count,
        warning_count=warning_count,
        violations=all_violations,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SSOT Semantic Drift Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ssot-dir",
        type=str,
        default="./ssot",
        help="SSOT root directory (default: ./ssot)",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    args = parser.parse_args()
    ssot_dir = Path(args.ssot_dir)

    try:
        result = scan_ssot(ssot_dir)
    except CommandError as e:
        print(f"ERROR: {e.status_code} - {e.message}", file=sys.stderr)
        if e.diagnostics:
            for diag in e.diagnostics:
                print(f"  {diag}", file=sys.stderr)
        sys.exit(1)

    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print("=" * 70)
        print("SSOT SEMANTIC DRIFT SCAN")
        print("=" * 70)
        print()
        print(f"Scan directory: {ssot_dir}")
        print()
        print(f"Total violations: {result.total_violations}")
        print(f"Blockers: {result.blocker_count}")
        print(f"Warnings: {result.warning_count}")
        print()

        if result.violations:
            print("Violations:")
            print("-" * 70)
            for i, v in enumerate(result.violations, 1):
                print(f"{i}. {v}")
                if v.evidence:
                    for key, value in v.evidence.items():
                        print(f"   {key}: {value}")
            print("-" * 70)
        else:
            print("No violations found.")

    sys.exit(1 if result.blocker_count > 0 else 0)


if __name__ == "__main__":
    main()

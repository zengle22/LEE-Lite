from __future__ import annotations

import json
import subprocess
import sys
import ast
from dataclasses import asdict, dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = Path(__file__).resolve().parent / "manifests"


@dataclass
class Violation:
    check: str
    code: str
    path: str
    message: str


@dataclass
class PythonFunctionMetric:
    qualname: str
    lineno: int
    end_lineno: int
    length: int


@dataclass
class PythonFileMetrics:
    path: str
    line_count: int
    functions: list[PythonFunctionMetric]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(read_text(path))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_manifest(name: str) -> Any:
    return load_json(MANIFEST_DIR / name)


def read_changed_files(path: Path | None) -> list[str]:
    if path is None:
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip().replace("\\", "/") for line in lines if line.strip()]


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def is_markdown(path: str) -> bool:
    return path.lower().endswith(".md")


def is_json(path: str) -> bool:
    return path.lower().endswith(".json")


def is_yaml(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".yaml") or lower.endswith(".yml")


def relative_to_root(path: Path) -> str:
    return normalize_path(path.relative_to(ROOT))


def list_repo_files() -> list[str]:
    files: list[str] = []
    for file_path in ROOT.rglob("*"):
        if file_path.is_file():
            files.append(relative_to_root(file_path))
    return sorted(files)


def match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def find_skill_roots(changed_files: list[str]) -> list[Path]:
    roots: set[Path] = set()
    for rel_path in changed_files:
        parts = Path(rel_path).parts
        if len(parts) >= 2 and parts[0] == "skills":
            candidate = ROOT / parts[0] / parts[1]
            if candidate.is_dir():
                roots.add(candidate)
    return sorted(roots)


def changed_with_prefix(changed_files: list[str], prefix: str) -> list[str]:
    normalized = prefix.rstrip("/") + "/"
    return [path for path in changed_files if path.startswith(normalized)]


def run_pytest(test_paths: list[str], report_path: Path) -> tuple[int, dict[str, Any]]:
    command = [sys.executable, "-m", "pytest", *test_paths]
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    payload = {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "tests": test_paths,
    }
    dump_json(report_path, payload)
    return result.returncode, payload


def git_show_file(revision: str, rel_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{rel_path}"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def collect_python_metrics(rel_path: str, text: str) -> PythonFileMetrics:
    tree = ast.parse(text)
    functions: list[PythonFunctionMetric] = []

    def visit(node: ast.AST, parents: list[str]) -> None:
        next_parents = parents
        if isinstance(node, ast.ClassDef):
            next_parents = parents + [node.name]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualname = ".".join(parents + [node.name])
            end_lineno = getattr(node, "end_lineno", None)
            if end_lineno is None:
                raise ValueError(f"Function {qualname} in {rel_path} is missing end_lineno metadata.")
            functions.append(
                PythonFunctionMetric(
                    qualname=qualname,
                    lineno=node.lineno,
                    end_lineno=end_lineno,
                    length=end_lineno - node.lineno + 1,
                )
            )
            next_parents = parents + [node.name]
        for child in ast.iter_child_nodes(node):
            visit(child, next_parents)

    visit(tree, [])
    return PythonFileMetrics(path=rel_path, line_count=len(text.splitlines()), functions=sorted(functions, key=lambda item: item.qualname))


def build_report(check: str, violations: list[Violation], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "check": check,
        "status": "failed" if violations else "passed",
        "violation_count": len(violations),
        "violations": [asdict(item) for item in violations],
    }
    if extra:
        report.update(extra)
    return report

#!/usr/bin/env python3
"""
Generate an evaluation report for a skill, including validation status and forward-test prompts.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml


SUPPORTED_RUNNERS = {"codex", "claude"}
RUNNER_DEFAULTS = {
    "codex": {
        "max_prompts": 1,
        "timeout_seconds": 90,
    },
    "claude": {
        "max_prompts": 1,
        "timeout_seconds": 60,
    },
}


def default_standard_validator() -> Path | None:
    codex_home = os.environ.get("CODEX_HOME")
    candidates = []
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py")
    candidates.append(Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def governed_validator_path() -> Path:
    return Path(__file__).resolve().parent / "validate_lee_workflow_skill.py"


def load_frontmatter(skill_md_path: Path) -> dict:
    content = skill_md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    data = yaml.safe_load(match.group(1))
    return data if isinstance(data, dict) else {}


def run_validator(name: str, validator_path: Path | None, skill_path: Path) -> tuple[str, str]:
    if validator_path is None:
        return "skipped", "validator not found"
    cmd = [sys.executable, str(validator_path), str(skill_path)]
    result = subprocess.run(cmd, text=True, capture_output=True)
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()
    status = "pass" if result.returncode == 0 else "fail"
    return status, output or f"{name} validator returned {result.returncode}"


def build_prompts(skill_path: Path, skill_name: str, contract: dict | None) -> list[str]:
    prompts = [
        f"Use ${skill_name} at {skill_path} to handle a realistic task that should trigger this skill."
    ]
    if contract:
        workflow_key = contract.get("workflow_key", skill_name)
        input_artifact = contract.get("input", {}).get("artifact_type", "input")
        output_artifact = contract.get("output", {}).get("artifact_type", "output")
        prompts.append(
            "Use "
            + f"${skill_name} at {skill_path} to transform a frozen {input_artifact.upper()} artifact into a governed "
            + f"{output_artifact.upper()} artifact for workflow {workflow_key}."
        )
        prompts.append(
            "Use "
            + f"${skill_name} at {skill_path} on an ambiguous or unfrozen {input_artifact.upper()} input and observe whether it requests clarification or blocks progress."
        )
    return prompts


def build_auto_forward_prompts(skill_path: Path, skill_name: str, contract: dict | None) -> list[str]:
    prompts = [
        (
            f"Use ${skill_name} at {skill_path}. Do not modify files. "
            "Decide whether the skill should trigger for this task, list the first files you would read, "
            "and state the first validation step. Keep the answer under 200 words."
        )
    ]
    if contract:
        workflow_key = contract.get("workflow_key", skill_name)
        input_artifact = contract.get("input", {}).get("artifact_type", "input").upper()
        output_artifact = contract.get("output", {}).get("artifact_type", "output").upper()
        prompts.append(
            (
                f"Use ${skill_name} at {skill_path} for workflow {workflow_key}. "
                f"Assume the user wants to transform a frozen {input_artifact} artifact into a governed {output_artifact} artifact. "
                "Do not edit files. Briefly say whether the input is actionable, what contract files you would inspect, "
                "and what could block progress."
            )
        )
    return prompts


def detect_repo_root(start: Path) -> Path:
    current = start
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return start
        current = current.parent


def runner_default(runner: str, key: str) -> int:
    return int(RUNNER_DEFAULTS[runner][key])


def build_runner_command(
    runner: str,
    workspace: Path,
    prompt: str,
    output_file: Path,
    timeout_seconds: int,
) -> list[str]:
    if runner == "codex":
        codex_binary = shutil.which("codex.cmd") or shutil.which("codex")
        if not codex_binary:
            raise FileNotFoundError("codex executable not found in PATH")
        return [
            codex_binary,
            "-a",
            "never",
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "-C",
            str(workspace),
            "--output-last-message",
            str(output_file),
            prompt,
        ]
    if runner == "claude":
        claude_binary = shutil.which("claude.exe") or shutil.which("claude")
        if not claude_binary:
            raise FileNotFoundError("claude executable not found in PATH")
        return [
            claude_binary,
            "-p",
            "--permission-mode",
            "bypassPermissions",
            "--allowedTools",
            "Read,Glob,Grep,Bash",
            "--output-format",
            "text",
            "--no-session-persistence",
            "--add-dir",
            str(workspace),
            "--",
            prompt,
        ]
    raise ValueError(f"Unsupported runner: {runner}")


def run_forward_tests(
    runner: str,
    workspace: Path,
    prompts: list[str],
    max_prompts: int,
    timeout_seconds: int,
) -> list[dict]:
    results: list[dict] = []
    for index, prompt in enumerate(prompts[:max_prompts], start=1):
        with tempfile.TemporaryDirectory(prefix="ll-meta-eval-") as tmp_dir:
            output_file = Path(tmp_dir) / f"forward-test-{index}.txt"
            cmd = build_runner_command(runner, workspace, prompt, output_file, timeout_seconds)
            started_at = time.time()
            try:
                result = subprocess.run(
                    cmd,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                )
                duration = round(time.time() - started_at, 2)
                if output_file.exists():
                    last_message = output_file.read_text(encoding="utf-8", errors="replace").strip()
                else:
                    last_message = ""
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()
                combined_output = "\n".join(part for part in [last_message, stdout, stderr] if part).strip()
                results.append(
                    {
                        "index": index,
                        "prompt": prompt,
                        "command": cmd,
                        "status": "pass" if result.returncode == 0 else "fail",
                        "exit_code": result.returncode,
                        "duration_seconds": duration,
                        "output": combined_output or "(no output captured)",
                    }
                )
            except subprocess.TimeoutExpired as exc:
                duration = round(time.time() - started_at, 2)
                timed_output = "\n".join(
                    part
                    for part in [
                        exc.stdout.strip() if isinstance(exc.stdout, str) else "",
                        exc.stderr.strip() if isinstance(exc.stderr, str) else "",
                    ]
                    if part
                ).strip()
                results.append(
                    {
                        "index": index,
                        "prompt": prompt,
                        "command": cmd,
                        "status": "fail",
                        "exit_code": "timeout",
                        "duration_seconds": duration,
                        "output": timed_output or f"forward-test timed out after {timeout_seconds} seconds",
                    }
                )
            except FileNotFoundError as exc:
                duration = round(time.time() - started_at, 2)
                results.append(
                    {
                        "index": index,
                        "prompt": prompt,
                        "command": cmd,
                        "status": "fail",
                        "exit_code": "missing-runner",
                        "duration_seconds": duration,
                        "output": str(exc),
                    }
                )
    return results


def render_forward_test_results(results: list[dict]) -> str:
    if not results:
        return "No automatic forward-tests were executed."
    blocks = []
    for result in results:
        command_text = " ".join(result["command"])
        blocks.append(
            f"""### Prompt {result['index']}

- status: {result['status']}
- exit_code: {result['exit_code']}
- duration_seconds: {result['duration_seconds']}
- command: `{command_text}`

Prompt:

```text
{result['prompt']}
```

Output:

```text
{result['output']}
```"""
        )
    return "\n\n".join(blocks)


def render_report(
    skill_path: Path,
    skill_name: str,
    standard_status: str,
    standard_output: str,
    governed_status: str,
    governed_output: str,
    prompts: list[str],
    forward_test_results: list[dict],
) -> str:
    prompt_lines = "\n".join(f"- {prompt}" for prompt in prompts)
    forward_test_block = render_forward_test_results(forward_test_results)
    return f"""# Skill Evaluation Report

## Target

- skill_path: {skill_path}
- skill_name: {skill_name}

## Validation Summary

- standard_validation: {standard_status}
- governed_validation: {governed_status}

## Standard Validator Output

```text
{standard_output}
```

## Governed Validator Output

```text
{governed_output}
```

## Forward-Test Prompt Suggestions

{prompt_lines}

## Automatic Forward-Test Results

{forward_test_block}

## Review Reminders

- Read `references/evaluation-checklist.md` before deciding the skill is ready.
- Read `references/forward-testing.md` before running independent passes.
- Treat validation pass as necessary but not sufficient for release.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an evaluation report for a skill.")
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument("--report-out", help="Optional path to write the report")
    parser.add_argument("--skip-standard", action="store_true")
    parser.add_argument("--skip-governed", action="store_true")
    parser.add_argument("--standard-validator", help="Optional path to quick_validate.py")
    parser.add_argument("--run-forward-tests", action="store_true", help="Execute prompt-based forward-tests via an external runner")
    parser.add_argument("--runner", choices=sorted(SUPPORTED_RUNNERS), default="codex", help="External runner to use for automatic forward-tests")
    parser.add_argument("--workspace", help="Workspace root for the runner; defaults to the nearest git root above the skill path")
    parser.add_argument("--max-prompts", type=int, help="Maximum number of generated prompts to run automatically")
    parser.add_argument("--timeout-seconds", type=int, help="Timeout per automatic forward-test")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    if not skill_path.exists():
        print(f"[ERROR] Skill directory not found: {skill_path}")
        return 1

    frontmatter = load_frontmatter(skill_path / "SKILL.md")
    skill_name = str(frontmatter.get("name", skill_path.name))

    standard_validator = None
    if not args.skip_standard:
        standard_validator = Path(args.standard_validator).resolve() if args.standard_validator else default_standard_validator()
    governed_validator = None if args.skip_governed else governed_validator_path()

    standard_status, standard_output = run_validator("standard", standard_validator, skill_path) if not args.skip_standard else ("skipped", "standard validation skipped")
    if not args.skip_governed and (skill_path / "ll.contract.yaml").exists():
        governed_status, governed_output = run_validator("governed", governed_validator, skill_path)
        contract = yaml.safe_load((skill_path / "ll.contract.yaml").read_text(encoding="utf-8"))
        contract = contract if isinstance(contract, dict) else None
    else:
        governed_status, governed_output = ("skipped", "governed validation skipped")
        contract = None

    prompts = build_prompts(skill_path, skill_name, contract)
    auto_prompts = build_auto_forward_prompts(skill_path, skill_name, contract)
    forward_test_results: list[dict] = []
    if args.run_forward_tests:
        workspace = Path(args.workspace).resolve() if args.workspace else detect_repo_root(skill_path)
        max_prompts = args.max_prompts if args.max_prompts is not None else runner_default(args.runner, "max_prompts")
        timeout_seconds = args.timeout_seconds if args.timeout_seconds is not None else runner_default(args.runner, "timeout_seconds")
        forward_test_results = run_forward_tests(
            runner=args.runner,
            workspace=workspace,
            prompts=auto_prompts,
            max_prompts=max_prompts,
            timeout_seconds=timeout_seconds,
        )
    report = render_report(
        skill_path,
        skill_name,
        standard_status,
        standard_output,
        governed_status,
        governed_output,
        prompts,
        forward_test_results,
    )

    if args.report_out:
        report_path = Path(args.report_out).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"[OK] Wrote evaluation report to {report_path}")
    else:
        print(report)

    statuses = {standard_status, governed_status}
    statuses.update(result["status"] for result in forward_test_results)
    if "fail" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

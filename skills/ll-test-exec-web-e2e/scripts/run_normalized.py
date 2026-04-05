#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--response-out", required=True)
    args = parser.parse_args(argv)

    request_path = Path(args.request).resolve()
    response_path = Path(args.response_out).resolve()
    normalize_script = Path(__file__).resolve().parent / "normalize_request.py"
    repo_root = Path(__file__).resolve().parents[3]

    with tempfile.TemporaryDirectory() as temp_dir:
        normalized_request = Path(temp_dir) / "request.normalized.json"
        subprocess.run(
            [sys.executable, str(normalize_script), "--input", str(request_path), "--output", str(normalized_request)],
            check=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli",
                "skill",
                "test-exec-web-e2e",
                "--request",
                str(normalized_request),
                "--response-out",
                str(response_path),
            ],
            check=False,
            cwd=repo_root,
        )
        return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

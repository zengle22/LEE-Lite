from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-gate-human-orchestrator" / "scripts" / "gate_human_orchestrator.py"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class GateUiSpecBriefTests(unittest.TestCase):
    def run_cmd(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    def make_ui_spec_gate_ready_package(self, root: Path) -> Path:
        artifacts_dir = root / "artifacts" / "feat-to-ui" / "ui-brief-demo"
        ui_spec_bundle = {
            "artifact_type": "ui_spec_package",
            "workflow_key": "dev.feat-to-ui",
            "workflow_run_id": "ui-brief-demo",
            "status": "pass",
            "feat_title": "最小建档主链能力",
            "ui_specs": [
                {
                    "page_name": "最小建档页",
                    "page_type": "single-page onboarding form",
                    "page_type_family": "form",
                    "page_goal": "在单页内完成首日必要建档，并在成功后立即放行首页。",
                    "page_role_in_flow": "登录/注册后的主链页面，承接首页放行前的最后一步。",
                    "completion_definition": "用户提交成功后立即进入首页，且设备连接保持后置。",
                    "main_user_path": [
                        "进入最小建档页并看到首日目标说明。",
                        "填写核心字段。",
                        "点击继续/完成建档。",
                    ],
                    "branch_paths": [
                        {
                            "title": "字段校验失败",
                            "steps": ["点击提交", "看到字段级错误", "修正并重试"],
                        }
                    ],
                    "page_sections": ["Goal Banner", "Six-Field Profile Form", "Footer Actions"],
                    "information_priority": ["六个必填字段及其原因", "风险提示"],
                    "action_priority": ["完成建档", "修正字段错误"],
                    "required_ui_fields": [
                        "gender",
                        "birthdate",
                        "height",
                        "weight",
                        "running_level",
                        "recent_injury_status",
                    ],
                    "ui_visible_fields": [
                        {"field": "running_level", "note": "options: beginner, intermediate, advanced, elite"},
                        {"field": "recent_injury_status", "note": "options: none, mild, recovering, active"},
                    ],
                    "states": [
                        {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示空表单"},
                        {"name": "submit_success", "trigger": "提交成功", "ui_behavior": "放行首页"},
                    ],
                    "frontend_validation_rules": [
                        "六个字段均为必填。",
                        "running_level 与 recent_injury_status 必须命中受支持枚举域。",
                    ],
                    "api_touchpoints": [
                        "POST /v1/onboarding/minimal-profile",
                        "GET /v1/onboarding/minimal-profile-state",
                    ],
                    "loading_feedback": "提交时主按钮 loading，并禁用重复点击。",
                    "success_feedback": "成功后立即跳转首页，并提示设备连接可稍后再做。",
                    "error_feedback": "失败时展示提交失败原因，不清空表单。",
                    "retry_behavior": "保留已填上下文并允许再次提交。",
                }
            ],
        }
        write_json(artifacts_dir / "ui-spec-bundle.json", ui_spec_bundle)
        write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})
        write_json(artifacts_dir / "acceptance-report.json", {"decision": "approve"})
        package_dir = artifacts_dir / "input"
        write_json(
            package_dir / "gate-ready-package.json",
            {
                "trace": {"run_ref": "ui-brief-demo", "workflow_key": "dev.feat-to-ui"},
                "payload": {
                    "candidate_ref": "feat-to-ui.ui-brief-demo.ui-spec-bundle",
                    "machine_ssot_ref": "artifacts/feat-to-ui/ui-brief-demo/ui-spec-bundle.json",
                    "acceptance_ref": "artifacts/feat-to-ui/ui-brief-demo/acceptance-report.json",
                    "evidence_bundle_ref": "artifacts/feat-to-ui/ui-brief-demo/supervision-evidence.json",
                },
            },
        )
        return package_dir

    def test_prepare_round_renders_full_ui_spec_brief(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_ui_spec_gate_ready_package(repo_root)

            prepare = self.run_cmd(
                "prepare-round",
                "--input",
                str(input_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "gate-ui-brief",
                cwd=ROOT,
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            payload = json.loads(prepare.stdout)
            markdown = payload["human_brief"]["markdown"]

            self.assertIn("### 页面定位", markdown)
            self.assertIn("### 主用户路径", markdown)
            self.assertIn("### 核心字段边界", markdown)
            self.assertIn("### 关键状态", markdown)
            self.assertIn("### 校验与接口触点", markdown)
            self.assertIn("### 反馈与恢复", markdown)
            self.assertIn("POST /v1/onboarding/minimal-profile", markdown)
            self.assertIn("running_level", markdown)


if __name__ == "__main__":
    unittest.main()

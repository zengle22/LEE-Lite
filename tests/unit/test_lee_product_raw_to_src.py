import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-product-raw-to-src" / "scripts" / "raw_to_src.py"
FIXTURES = ROOT / "tests" / "fixtures" / "raw-to-src"

sys.path.insert(0, str(ROOT / "skills" / "ll-product-raw-to-src" / "scripts"))

from raw_to_src_bridge import acceptance_review
from raw_to_src_common import heading_sections, parse_frontmatter


class RawToSrcWorkflowTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        (root / "ssot" / "src").mkdir(parents=True, exist_ok=True)
        (root / "artifacts" / "raw-to-src").mkdir(parents=True, exist_ok=True)

    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def write_existing_src(self, repo_root: Path, title: str) -> Path:
        path = repo_root / "ssot" / "src" / "SRC-001__duplicate.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    f"title: {title}",
                    "status: frozen",
                    "---",
                    "",
                    f"# {title}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path

    def test_run_creates_candidate_package_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            result = self.run_cmd("run", "--input", str(FIXTURES / "raw-requirement.md"), "--repo-root", str(repo_root), "--run-id", "test-run-basic")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "freeze_ready")
            self.assertEqual(payload["recommended_action"], "next_skill")

            artifacts_dir = Path(payload["artifacts_dir"])
            candidate_path = Path(payload["candidate_path"])
            self.assertTrue(artifacts_dir.exists())
            self.assertTrue(candidate_path.exists())
            self.assertFalse(any((repo_root / "ssot" / "src").glob("SRC-*.md")))

            content = candidate_path.read_text(encoding="utf-8")
            self.assertIn("artifact_type: src_candidate", content)
            self.assertIn("## 问题陈述", content)
            self.assertTrue((artifacts_dir / "execution-evidence.json").exists())
            self.assertTrue((artifacts_dir / "supervision-evidence.json").exists())
            self.assertTrue((artifacts_dir / "result-summary.json").exists())
            self.assertTrue((artifacts_dir / "run-state.json").exists())
            self.assertTrue((artifacts_dir / "patch-lineage.json").exists())
            self.assertTrue((artifacts_dir / "proposed-next-actions.json").exists())
            self.assertTrue((artifacts_dir / "package-manifest.json").exists())
            self.assertTrue((artifacts_dir / "source-semantic-findings.json").exists())
            self.assertTrue((artifacts_dir / "handoff-proposal.json").exists())
            self.assertTrue((artifacts_dir / "job-proposal.json").exists())
            self.assertTrue((artifacts_dir / "input" / "gate-ready-package.json").exists())
            self.assertTrue((artifacts_dir / "_cli" / "gate-submit-handoff.response.json").exists())
            self.assertTrue((artifacts_dir / "_cli" / "artifact-commit.response.json").exists())
            self.assertTrue((repo_root / "artifacts" / "registry" / "raw-to-src-test-run-basic-src-candidate.json").exists())
            self.assertEqual(
                payload["gate_ready_package_ref"],
                "artifacts/raw-to-src/test-run-basic/input/gate-ready-package.json",
            )
            self.assertTrue(payload["authoritative_handoff_ref"].startswith("artifacts/active/gates/handoffs/"))
            self.assertTrue(payload["gate_pending_ref"].startswith("artifacts/active/gates/pending/"))

            cli_response = json.loads((artifacts_dir / "_cli" / "artifact-commit.response.json").read_text(encoding="utf-8"))
            self.assertEqual(cli_response["status_code"], "OK")
            self.assertEqual(cli_response["data"]["canonical_path"], "artifacts/raw-to-src/test-run-basic/src-candidate.md")
            gate_submit = json.loads((artifacts_dir / "_cli" / "gate-submit-handoff.response.json").read_text(encoding="utf-8"))
            self.assertEqual(gate_submit["status_code"], "OK")
            self.assertEqual(gate_submit["data"]["gate_pending_ref"], payload["gate_pending_ref"])

            gate_ready_package = json.loads((artifacts_dir / "input" / "gate-ready-package.json").read_text(encoding="utf-8"))
            self.assertEqual(gate_ready_package["payload"]["candidate_ref"], "raw-to-src.test-run-basic.src-candidate")
            self.assertEqual(
                gate_ready_package["payload"]["machine_ssot_ref"],
                "artifacts/raw-to-src/test-run-basic/src-candidate.json",
            )

            pending_index = json.loads((repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(pending_index["handoffs"]), 1)
            self.assertTrue((repo_root / payload["authoritative_handoff_ref"]).exists())
            self.assertTrue((repo_root / payload["gate_pending_ref"]).exists())

            execution = json.loads((artifacts_dir / "execution-evidence.json").read_text(encoding="utf-8"))
            stage_ids = {item["stage_id"] for item in execution["stage_results"]}
            self.assertIn("input_revalidation", stage_ids)
            self.assertIn("intake_validation", stage_ids)
            self.assertIn("intake_revalidation", stage_ids)
            input_validation = json.loads((artifacts_dir / "input-validation.json").read_text(encoding="utf-8"))
            self.assertIn("initial_validation", input_validation)
            self.assertIn("revalidation", input_validation)

    def test_adr_input_emits_bridge_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            result = self.run_cmd("run", "--input", str(FIXTURES / "adr-bridge.yaml"), "--repo-root", str(repo_root), "--run-id", "test-run-adr")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            content = Path(payload["candidate_path"]).read_text(encoding="utf-8")
            self.assertIn("source_kind: governance_bridge_src", content)
            self.assertIn("## 治理变更摘要", content)
            self.assertIn("## Bridge Context", content)
            self.assertIn("ADR-021", content)
            self.assertIn("当前目录治理规则分散", content)
            self.assertIn("governance_objects:", content)
            self.assertNotIn("受该问题影响的业务角色", content)
            self.assertNotIn("当原始问题被触发并需要正式需求源时。", content)

    def test_semantic_lock_is_preserved_in_src_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "adr015.md"
            source.write_text(
                "\n".join(
                    [
                        "---",
                        "title: ADR-015 Projection Rule",
                        "semantic_lock:",
                        "  domain_type: review_projection_rule",
                        "  one_sentence_truth: 仅在 gate 审核阶段，从机器优先 SSOT 派生一份人类友好 Projection，帮助人类决策；冻结与继承仍回到 SSOT。",
                        "  primary_object: human_review_projection",
                        "  lifecycle_stage: gate_review_only",
                        "  allowed_capabilities:",
                        "    - projection_generation",
                        "    - authoritative_snapshot_rendering",
                        "    - review_focus_extraction",
                        "    - risk_ambiguity_extraction",
                        "    - review_feedback_writeback",
                        "  forbidden_capabilities:",
                        "    - mainline_runtime_governance",
                        "    - handoff_orchestration",
                        "    - formal_publication",
                        "    - governed_io_platform",
                        "  inheritance_rule: Projection is derived-only, non-authoritative, non-inheritable.",
                        "---",
                        "",
                        "# ADR-015 Projection Rule",
                        "",
                        "## 问题陈述",
                        "",
                        "SSOT 正文继续服务 AI 执行，但 gate 审核阶段需要一份人类友好 Projection，且 Projection 不能成为新的真相源。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cmd("run", "--input", str(source), "--repo-root", str(repo_root), "--run-id", "test-run-semantic-lock")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            candidate = json.loads((Path(payload["artifacts_dir"]) / "src-candidate.json").read_text(encoding="utf-8"))
            self.assertEqual(candidate["semantic_lock"]["domain_type"], "review_projection_rule")
            self.assertIn("projection_generation", candidate["semantic_lock"]["allowed_capabilities"])
            self.assertIn("mainline_runtime_governance", candidate["semantic_lock"]["forbidden_capabilities"])

    def test_adr018_bridge_synthesizes_execution_runner_semantic_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "ADR-018.md"
            source.write_text(
                "\n".join(
                    [
                        "# ADR-018 Execution Loop Job Runner 作为自动推进运行时",
                        "",
                        "## 问题陈述",
                        "",
                        "dispatch 已经可以产出 materialized-job，但当前仍缺少一个正式 consumer 去自动消费 artifacts/jobs/ready/ 中的 job，并把它推进到下游 workflow。",
                        "",
                        "- gate approve 后会停在 formal publication trigger，不能自动跑到下一个 skill。",
                        "- 当前仍依赖第三会话人工接力。", 
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cmd("run", "--input", str(source), "--repo-root", str(repo_root), "--run-id", "test-run-adr018")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            candidate = json.loads((Path(payload["artifacts_dir"]) / "src-candidate.json").read_text(encoding="utf-8"))
            semantic_lock = candidate["semantic_lock"]

            self.assertEqual(semantic_lock["domain_type"], "execution_runner_rule")
            self.assertEqual(semantic_lock["primary_object"], "execution_loop_job_runner")
            self.assertIn("ready_queue_consumption", semantic_lock["allowed_capabilities"])
            self.assertIn("formal_publication_substitution", semantic_lock["forbidden_capabilities"])

    def test_markdown_adr_bridge_does_not_inline_full_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "ADR-005.md"
            source.write_text(
                "\n".join(
                    [
                        "# ADR-005：Skill 文件读写采用 Artifact IO Gateway + Path Policy 统一治理",
                        "",
                        "* 状态：Draft",
                        "* 日期：2026-03-23",
                        "* 决策者：Le Zeng",
                        "",
                        "# 1. 背景",
                        "",
                        "随着 skill 数量增加，正式产物落点和消费路径越来越不稳定。",
                        "",
                        "# 2. 问题定义",
                        "",
                        "# **文件系统读写仍然是自由能力，而不是受控能力。**",
                        "",
                        "* 在不合规目录中落正式产物；",
                        "* 在没有注册、没有声明、没有审批的情况下覆盖已有文件；",
                        "* 通过路径猜测而不是 artifact 绑定来消费上下游文件。",
                        "",
                        "# 3. 决策",
                        "",
                        "将正式文件读写统一收口到 Artifact IO Gateway、Path Policy、Artifact Registry 与 Workspace Auditor。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_cmd("run", "--input", str(source), "--repo-root", str(repo_root), "--run-id", "test-run-markdown-adr")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "freeze_ready")
            self.assertEqual(payload["recommended_action"], "next_skill")

            content = Path(payload["candidate_path"]).read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)
            sections = heading_sections(body)
            self.assertIn("文件系统读写仍然是自由能力，而不是受控能力。", content)
            self.assertNotIn("状态：Draft", content)
            self.assertNotIn("## 2.1 正式产物落点不稳定", content)
            self.assertLess(len(content), 4000)
            self.assertIn("当前执行链已经出现", sections["问题陈述"])
            self.assertIn("这会直接造成", sections["问题陈述"])
            self.assertIn("正式文件读写统一纳入围绕", sections["问题陈述"])
            self.assertNotEqual(sections["问题陈述"], sections["业务动因"])
            self.assertIn("需要现在就把这类治理变化收敛成正式需求源", sections["业务动因"])
            self.assertIn("统一原则：", sections["治理变更摘要"])
            self.assertIn("下游必须继承的约束：", sections["治理变更摘要"])
            self.assertIn("workflow / orchestration 设计者", sections["目标用户"])
            self.assertIn("human gate / reviewer", sections["目标用户"])
            self.assertIn("定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。", sections["范围边界"])
            self.assertIn("结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。", sections["Bridge Context"])
            self.assertIn("下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。", sections["Bridge Context"])

    def test_merged_adr_bridge_preserves_explicit_structure_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            result = self.run_cmd(
                "run",
                "--input",
                str(FIXTURES / "adr-merged-bridge.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-merged-adr",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "freeze_ready")

            content = Path(payload["candidate_path"]).read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)
            sections = heading_sections(body)
            self.assertIn("因此需要一份 bridge SRC 作为统一继承源。", sections["问题陈述"])
            self.assertNotIn("受该治理规则约束的 skill 作者", sections["目标用户"])
            self.assertNotIn("当 skill 需要决定 artifact 目录、路径或落点策略时。", sections["触发场景"])
            self.assertIn("治理对象：双会话双队列闭环; 文件化 handoff runtime; external gate 独立裁决与物化", sections["治理变更摘要"])
            self.assertNotIn("现状失控：", sections["治理变更摘要"])
            self.assertIn("下游需求链必须将 双会话双队列闭环、文件化 handoff runtime、external gate 独立裁决与物化 视为同一治理闭环的组成部分统一继承", sections["治理变更摘要"])
            self.assertIn("approve、revise、retry、handoff、reject", sections["治理变更摘要"])
            self.assertIn("candidate package 是 gate 消费对象；formal object 是 gate 批准后供下游消费的正式输入。", sections["治理变更摘要"])
            self.assertIn("ADR-005 为主链文件 IO / 路径治理提供已交付治理基础", sections["治理变更摘要"])
            self.assertIn("external gate 必须以 approve、revise、retry、handoff、reject 形成唯一决策", sections["关键约束"])
            self.assertIn("candidate package 仅作为 gate 消费对象；经 gate 批准并物化后的 formal object 才能作为下游正式输入。", sections["关键约束"])
            self.assertIn("ADR-005 已提供的治理基础", sections["范围边界"])
            self.assertIn("不在本 SRC 中重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块", sections["范围边界"])
            self.assertIn("ADR-005", sections["来源追溯"])
            self.assertIn("结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。", sections["Bridge Context"])
            self.assertIn("审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。", sections["Bridge Context"])

    def test_qa_execution_adr_bridge_emits_objects_outcomes_and_derivation_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "ADR-007.md"
            source.write_text(
                "\n".join(
                    [
                        "---",
                        "title: ADR-007 QA Test Execution Governed Skill 标准方案",
                        "input_type: adr",
                        "source_refs:",
                        "  - ADR-007",
                        "  - ADR-001",
                        "  - ADR-004",
                        "  - ADR-005",
                        "  - ADR-006",
                        "---",
                        "",
                        "# ADR-007 QA Test Execution Governed Skill 标准方案",
                        "",
                        "## 问题陈述",
                        "",
                        "QA 测试执行链当前仍在 workflow、runner 和口头约定之间漂移。",
                        "",
                        "- TestSet、TestCasePack、ScriptPack、TSE 边界不稳定。",
                        "- test_environment_ref 如果不是结构化契约，后续会在 base_url、runner、mock、network 与 retry 上持续产生歧义。",
                        "- invalid_run、failed 与 completed_with_failures 的语义容易被混用。",
                        "",
                        "## 目标用户",
                        "",
                        "- QA workflow / orchestration 设计者",
                        "- skill.qa.test_exec_web_e2e 作者",
                        "- skill.runner.test_e2e 作者",
                        "- compliance checker / result judge / reviewer",
                        "",
                        "## 触发场景",
                        "",
                        "- 当 QA 测试执行链需要正式收敛为 governed skill，而不是分散的 workflow、runner 和自然语言约定时。",
                        "- 当后续实现需要定义 TestSet、ResolvedSSOTContext、TestCasePack、ScriptPack 与 TSE 的中间产物边界时。",
                        "",
                        "## 业务动因",
                        "",
                        "- 需要让 QA 测试执行链进入统一治理体系，而不是保留为孤立的脚本执行能力。",
                        "- 需要让 reviewer、report consumer 与 human gate 对同一 run 使用统一对象与状态语义。",
                        "",
                        "## 关键约束",
                        "",
                        "- QA test execution skill",
                        "- TestEnvironmentSpec",
                        "- TestCasePack 冻结",
                        "- ScriptPack 冻结",
                        "- 合规与判定分层",
                        "- run_status 与 acceptance_status 分层",
                        "- rerun mode 与 minimum evidence policy",
                        "",
                        "## 非目标",
                        "",
                        "- 不直接展开 QA runner、schema、CLI 实现细节。",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_cmd(
                "run",
                "--input",
                str(source),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-qa-adr",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn(payload["status"], {"freeze_ready", "retry_proposed"})

            content = Path(payload["candidate_path"]).read_text(encoding="utf-8")
            _, body = parse_frontmatter(content)
            sections = heading_sections(body)
            self.assertIn("skill.qa.test_exec_web_e2e", sections["目标能力对象"])
            self.assertIn("TestEnvironmentSpec contract/schema", sections["目标能力对象"])
            self.assertIn("rerun / repair lifecycle contract", sections["目标能力对象"])
            self.assertIn("reviewer 可独立判断 run 是否可采信", sections["成功结果"])
            self.assertIn("human gate 可稳定区分 execution complete 与 acceptance complete", sections["成功结果"])
            self.assertIn("宽 skill contract 与 lifecycle", sections["下游派生要求"])
            self.assertIn("EvidenceBundle minimum evidence policy", sections["下游派生要求"])
            self.assertIn("本 SRC 不重新论证上游 ADR 的正确性", sections["桥接摘要"])
            self.assertIn("下游不应再重新讨论核心边界", sections["桥接摘要"])
            self.assertIn("定义 QA test execution governed skill 的对象模型、状态语义、冻结链、证据规则与下游继承边界。", sections["范围边界"])
            self.assertNotIn("定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。", sections["范围边界"])

    def test_thin_adr_bridge_requires_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "thin-adr.yaml"
            source.write_text(
                "\n".join(
                    [
                        "input_type: adr",
                        "title: ADR-099 Artifact IO Gateway",
                        "source_refs:",
                        "  - ADR-099",
                        "requirement_overview:",
                        "  description: ADR-099 Artifact IO Gateway",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_cmd(
                "run",
                "--input",
                str(source),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-thin-adr",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "retry_proposed")
            self.assertEqual(payload["recommended_action"], "retry")

            artifacts_dir = Path(payload["artifacts_dir"])
            source_findings = json.loads((artifacts_dir / "source-semantic-findings.json").read_text(encoding="utf-8"))
            finding_types = {item["type"] for item in source_findings["findings"]}
            self.assertIn("downstream_actionability_insufficient", finding_types)

    def test_acceptance_review_has_independent_bridge_checks(self) -> None:
        candidate = {
            "source_kind": "governance_bridge_src",
            "governance_change_summary": ["治理对象：Artifact IO Gateway"],
            "key_constraints": ["统一接口"],
            "out_of_scope": [],
            "bridge_context": {
                "acceptance_impact": ["需要保留一致性"],
                "non_goals": [],
            },
        }
        report, findings = acceptance_review(candidate, {"findings": []})
        self.assertEqual(report["decision"], "revise")
        finding_types = {item["type"] for item in findings}
        self.assertIn("bridge_summary_insufficient", finding_types)
        self.assertIn("acceptance_impact_insufficient", finding_types)
        self.assertIn("governance_constraint_clarity_insufficient", finding_types)
        self.assertIn("non_goal_explicitness_insufficient", finding_types)

    def test_rejects_existing_ssot_input(self) -> None:
        result = self.run_cmd("validate-input", "--input", str(FIXTURES / "existing-ssot.md"))
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        codes = {item["code"] for item in payload["result"]["issues"]}
        self.assertIn("input_already_ssot", codes)
        self.assertEqual(payload["normalized"]["input_type"], "raw_requirement")

    def test_duplicate_title_produces_blocked_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            self.write_existing_src(repo_root, "Checkout Retry Messaging")

            result = self.run_cmd(
                "run",
                "--input",
                str(FIXTURES / "raw-requirement.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-duplicate",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["recommended_action"], "blocked")
            self.assertIsNone(payload["handoff_proposal_path"])
            self.assertIsNone(payload["gate_ready_package_ref"])
            self.assertIsNone(payload["authoritative_handoff_ref"])
            self.assertIsNone(payload["gate_pending_ref"])

            artifacts_dir = Path(payload["artifacts_dir"])
            result_summary = json.loads((artifacts_dir / "result-summary.json").read_text(encoding="utf-8"))
            defects = json.loads((artifacts_dir / "defect-list.json").read_text(encoding="utf-8"))
            self.assertEqual(result_summary["recommended_action"], "blocked")
            defect_types = {item["type"] for item in defects}
            self.assertIn("duplicate_title", defect_types)
            self.assertFalse((artifacts_dir / "handoff-proposal.json").exists())
            self.assertTrue((artifacts_dir / "job-proposal.json").exists())
            self.assertFalse((artifacts_dir / "input" / "gate-ready-package.json").exists())
            self.assertFalse((repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json").exists())

    def test_validate_output_checks_runtime_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            run = self.run_cmd(
                "run",
                "--input",
                str(FIXTURES / "raw-requirement.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-validate-output",
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            payload = json.loads(run.stdout)

            result = self.run_cmd("validate-output", "--artifacts-dir", payload["artifacts_dir"])
            self.assertEqual(result.returncode, 0, result.stderr)
            validation = json.loads(result.stdout)
            self.assertTrue(validation["ok"])

    def test_validate_package_readiness_and_freeze_guard_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            run = self.run_cmd(
                "run",
                "--input",
                str(FIXTURES / "raw-requirement.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-readiness",
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            payload = json.loads(run.stdout)

            readiness = self.run_cmd("validate-package-readiness", "--artifacts-dir", payload["artifacts_dir"])
            self.assertEqual(readiness.returncode, 0, readiness.stderr)
            readiness_payload = json.loads(readiness.stdout)
            self.assertTrue(readiness_payload["ok"])

            legacy_alias = self.run_cmd("freeze-guard", "--artifacts-dir", payload["artifacts_dir"])
            self.assertEqual(legacy_alias.returncode, 0, legacy_alias.stderr)
            alias_payload = json.loads(legacy_alias.stdout)
            self.assertTrue(alias_payload["ok"])

    def test_semantic_boundary_issue_proposes_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)
            source = repo_root / "semantic-retry.md"
            source.write_text(
                "\n".join(
                    [
                        "---",
                        "input_type: raw_requirement",
                        "title: Checkout Retry Messaging",
                        "---",
                        "",
                        "# Checkout Retry Messaging",
                        "",
                        "## 问题陈述",
                        "",
                        "需要把这次需求直接展开成 EPIC 和 FEAT 方案。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_cmd(
                "run",
                "--input",
                str(source),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-retry",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "retry_proposed")
            self.assertEqual(payload["recommended_action"], "retry")

            artifacts_dir = Path(payload["artifacts_dir"])
            source_findings = json.loads((artifacts_dir / "source-semantic-findings.json").read_text(encoding="utf-8"))
            acceptance = json.loads((artifacts_dir / "acceptance-report.json").read_text(encoding="utf-8"))
            run_state = json.loads((artifacts_dir / "run-state.json").read_text(encoding="utf-8"))
            job_proposal = json.loads((artifacts_dir / "job-proposal.json").read_text(encoding="utf-8"))
            self.assertTrue(source_findings["findings"])
            self.assertEqual(source_findings["stage_id"], "source_semantic_review")
            self.assertIn("acceptance_findings", acceptance)
            self.assertEqual(run_state["current_state"], "retry_recommended")
            self.assertEqual(job_proposal["retry_budget"], 2)
            defect_types = {item["type"] for item in json.loads((artifacts_dir / "defect-list.json").read_text(encoding="utf-8"))}
            self.assertIn("layer_boundary", defect_types)

    def test_executor_and_supervisor_commands_respect_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.make_repo(repo_root)

            executor = self.run_cmd(
                "executor-run",
                "--input",
                str(FIXTURES / "raw-requirement.md"),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-boundary",
            )
            self.assertEqual(executor.returncode, 0, executor.stderr)
            executor_payload = json.loads(executor.stdout)
            artifacts_dir = Path(executor_payload["artifacts_dir"])
            self.assertTrue((artifacts_dir / "execution-evidence.json").exists())
            self.assertFalse((artifacts_dir / "supervision-evidence.json").exists())
            self.assertFalse((artifacts_dir / "source-semantic-findings.json").exists())
            self.assertFalse((artifacts_dir / "acceptance-report.json").exists())

            supervisor = self.run_cmd(
                "supervisor-review",
                "--artifacts-dir",
                str(artifacts_dir),
                "--repo-root",
                str(repo_root),
                "--run-id",
                "test-run-boundary",
            )
            self.assertEqual(supervisor.returncode, 0, supervisor.stderr)
            supervisor_payload = json.loads(supervisor.stdout)
            self.assertEqual(supervisor_payload["recommended_action"], "next_skill")
            self.assertTrue((artifacts_dir / "supervision-evidence.json").exists())
            self.assertTrue((artifacts_dir / "source-semantic-findings.json").exists())
            self.assertTrue((artifacts_dir / "acceptance-report.json").exists())


if __name__ == "__main__":
    unittest.main()

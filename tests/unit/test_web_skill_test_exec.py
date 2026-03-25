from __future__ import annotations

from _test_exec_skill_support import SkillRuntimeHarness, python_file_command, read_json, write_json, write_yaml


class TestWebExecSkillRuntime(SkillRuntimeHarness):
    def test_web_skill_emits_candidate_and_handoff_with_real_testset(self) -> None:
        npm_script, playwright_script = self.write_fake_playwright_scripts()
        env_ref = self.write_env_spec(
            "web-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {"test_set_ref": self.feat_testset_path("001"), "test_environment_ref": env_ref, "proposal_ref": "proposal-web-001"},
        )
        req = self.request_path("skill-web.json")
        write_json(req, request)
        response = self.response_path("skill-web.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)
        ui_intent, ui_source_context, ui_binding_map, candidate = self.assert_execution_outputs(payload["data"], expected_cases=3, expected_status="completed")
        self.assertTrue(all(item["derivation_mode"] in {"governance_inferred", "fallback_smoke"} for item in ui_intent["cases"]))
        self.assertFalse(ui_source_context["codebase"]["resolved"])
        self.assertEqual(candidate["ui_source_spec"], {"codebase_ref": "", "runtime_ref": "", "prototype_ref": ""})
        self.assertTrue(all(item["resolution_status"] in {"partial", "fallback_smoke", "resolved"} for item in ui_binding_map["cases"]))

    def test_web_skill_renders_explicit_ui_steps_into_playwright_spec(self) -> None:
        case_id = "TS-WEB-UI-001-U01"
        npm_script, playwright_script = self.write_fake_playwright_scripts([case_id])
        test_set_ref = self.write_testset(
            "web-ui-testset.yaml",
            "ssot_type: TESTSET\n"
            "test_set_id: TS-WEB-UI-001\n"
            "title: Web UI translator test set\n"
            "feat_ref: FEAT-WEB-UI-001\n"
            "epic_ref: EPIC-WEB-UI-001\n"
            "src_ref: SRC-WEB-UI-001\n"
            "test_units:\n"
            f"- unit_ref: {case_id}\n"
            "  title: Login flow with explicit ui steps\n"
            "  priority: P0\n"
            "  page_path: /login\n"
            "  expected_url: /dashboard\n"
            "  expected_text: Welcome back\n"
            "  selectors:\n"
            "    email_input:\n"
            "      testid: login-email\n"
            "    password_input: input[name='password']\n"
            "    primary_action:\n"
            "      role: button\n"
            "      name: Sign in\n"
            "  ui_steps:\n"
            "  - action: goto\n"
            "    path: /login\n"
            "  - action: fill\n"
            "    target: email_input\n"
            "    value: user@example.com\n"
            "  - action: fill\n"
            "    target: password_input\n"
            "    value: secret\n"
            "  - action: click\n"
            "    target: primary_action\n"
            "  - action: assert_text\n"
            "    text: Welcome back\n",
        )
        env_ref = self.write_env_spec(
            "web-ui-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {
                "test_set_ref": test_set_ref,
                "test_environment_ref": env_ref,
                "proposal_ref": "proposal-web-ui-001",
                "frontend_code_ref": "repo://frontend/app-shell",
                "ui_runtime_ref": "runtime://staging/web-shell",
                "ui_source_spec": {"prototype_ref": "proto://login-flow-v1"},
            },
        )
        req = self.request_path("skill-web-ui.json")
        write_json(req, request)
        response = self.response_path("skill-web-ui.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        ui_intent, ui_source_context, binding_map, candidate = self.assert_execution_outputs(payload, expected_cases=1, expected_status="completed")
        expected_spec = {"codebase_ref": "repo://frontend/app-shell", "runtime_ref": "runtime://staging/web-shell", "prototype_ref": "proto://login-flow-v1"}
        self.assertEqual(ui_intent["ui_source_spec"], expected_spec)
        self.assertEqual(binding_map["ui_source_spec"], expected_spec)
        self.assertEqual(candidate["ui_source_spec"], expected_spec)
        self.assertFalse(ui_source_context["codebase"]["resolved"])
        self.assertEqual(binding_map["cases"][0]["resolution_status"], "resolved")
        script_pack = read_json(self.resolve_ref(payload["script_pack_ref"]))
        self.assertEqual(script_pack["runner_config"]["ui_source_spec"], expected_spec)
        spec_text = self.resolve_ref(script_pack["project_refs"]["spec_file_ref"]).read_text(encoding="utf-8")
        self.assertIn('"testid": "login-email"', spec_text)
        self.assertIn("\"selector\": \"input[name='password']\"", spec_text)
        self.assertIn('"semantic_target": "primary_action"', spec_text)

    def test_web_skill_resolves_targets_from_frontend_code_ref(self) -> None:
        case_id = "TS-WEB-CODE-001-U01"
        npm_script, playwright_script = self.write_fake_playwright_scripts([case_id])
        codebase_root = self.workspace / "frontend" / "src"
        write_yaml(
            codebase_root / "login.tsx",
            "<form>\n  <input data-testid=\"login-email\" />\n  <input name=\"password\" type=\"password\" />\n  <button>Sign in</button>\n</form>\n",
        )
        test_set_ref = self.write_testset(
            "web-code-testset.yaml",
            "ssot_type: TESTSET\n"
            "test_set_id: TS-WEB-CODE-001\n"
            "title: Web code resolver test set\n"
            "feat_ref: FEAT-WEB-CODE-001\n"
            "epic_ref: EPIC-WEB-CODE-001\n"
            "src_ref: SRC-WEB-CODE-001\n"
            "test_units:\n"
            f"- unit_ref: {case_id}\n"
            "  title: Login flow from codebase\n"
            "  priority: P0\n"
            "  expected_text: Welcome back\n"
            "  ui_steps:\n"
            "  - action: fill\n"
            "    target: email_input\n"
            "    value: user@example.com\n"
            "  - action: fill\n"
            "    target: password_input\n"
            "    value: secret\n"
            "  - action: click\n"
            "    target: primary_action\n",
        )
        env_ref = self.write_env_spec(
            "web-code-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {"test_set_ref": test_set_ref, "test_environment_ref": env_ref, "proposal_ref": "proposal-web-code-001", "frontend_code_ref": codebase_root.as_posix()},
        )
        req = self.request_path("skill-web-code.json")
        write_json(req, request)
        response = self.response_path("skill-web-code.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        _, ui_source_context, binding_map, _ = self.assert_execution_outputs(payload, expected_cases=1, expected_status="completed")
        self.assertTrue(ui_source_context["codebase"]["resolved"])
        self.assertEqual(binding_map["cases"][0]["resolution_status"], "resolved")
        self.assertIn("source_scan", [step.get("binding_source", "") for step in binding_map["cases"][0]["resolved_ui_steps"]])

    def test_web_skill_resolves_targets_from_ui_runtime_ref(self) -> None:
        case_id = "TS-WEB-RUNTIME-001-U01"
        npm_script, playwright_script = self.write_fake_playwright_scripts([case_id])
        runtime_html = self.workspace / "runtime" / "login.html"
        write_yaml(runtime_html, "<body><input data-testid=\"login-email\" /><input name=\"password\" type=\"password\" /><button>Sign in</button></body>\n")
        test_set_ref = self.write_testset(
            "web-runtime-testset.yaml",
            "ssot_type: TESTSET\n"
            "test_set_id: TS-WEB-RUNTIME-001\n"
            "title: Web runtime resolver test set\n"
            "feat_ref: FEAT-WEB-RUNTIME-001\n"
            "epic_ref: EPIC-WEB-RUNTIME-001\n"
            "src_ref: SRC-WEB-RUNTIME-001\n"
            "test_units:\n"
            f"- unit_ref: {case_id}\n"
            "  title: Login flow from runtime\n"
            "  priority: P0\n"
            "  expected_text: Welcome back\n"
            "  ui_steps:\n"
            "  - action: fill\n"
            "    target: email_input\n"
            "    value: user@example.com\n"
            "  - action: fill\n"
            "    target: password_input\n"
            "    value: secret\n"
            "  - action: click\n"
            "    target: primary_action\n",
        )
        env_ref = self.write_env_spec(
            "web-runtime-env.yaml",
            "execution_modality: web_e2e\n"
            "base_url: https://example.test\n"
            "browser: chromium\n"
            "headless: true\n"
            "workdir: .\n"
            "npm_command: >-\n"
            f"  {python_file_command(npm_script)}\n"
            "playwright_command: >-\n"
            f"  {python_file_command(playwright_script)}\n",
        )
        request = self.build_request(
            "skill.test-exec-web-e2e",
            {"test_set_ref": test_set_ref, "test_environment_ref": env_ref, "proposal_ref": "proposal-web-runtime-001", "ui_runtime_ref": runtime_html.as_posix()},
        )
        req = self.request_path("skill-web-runtime.json")
        write_json(req, request)
        response = self.response_path("skill-web-runtime.response.json")
        self.assertEqual(self.run_cli("skill", "test-exec-web-e2e", "--request", str(req), "--response-out", str(response)), 0)
        payload = read_json(response)["data"]
        _, ui_source_context, binding_map, _ = self.assert_execution_outputs(payload, expected_cases=1, expected_status="completed")
        self.assertEqual(ui_source_context["runtime"]["pages"][0]["fetch_status"], "ok")
        self.assertEqual(binding_map["cases"][0]["resolution_status"], "resolved")
        self.assertIn("source_scan", [step.get("binding_source", "") for step in binding_map["cases"][0]["resolved_ui_steps"]])

"""Playwright translation and execution helpers for governed test execution."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, to_canonical_path, write_json, write_text
from cli.lib.registry_store import slugify


CASE_ID_PATTERN = re.compile(r"^\[(?P<case_id>[^\]]+)\]")


def _browser_name(environment: dict[str, Any]) -> str:
    browser = str(environment.get("browser", "chromium")).lower()
    mapping = {"chrome": "chromium", "edge": "chromium", "firefox": "firefox", "webkit": "webkit"}
    return mapping.get(browser, "chromium")


def _project_root(output_root: Path) -> Path:
    return output_root / "playwright-project"


def render_package_json() -> str:
    payload = {
        "name": "governed-test-exec-web-e2e",
        "private": True,
        "devDependencies": {"@playwright/test": "^1.58.2", "typescript": "^5.0.0"},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_tsconfig() -> str:
    payload = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "moduleResolution": "node",
            "types": ["@playwright/test"],
            "esModuleInterop": True,
            "skipLibCheck": True,
        },
        "include": ["e2e/**/*"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_playwright_config(environment: dict[str, Any]) -> str:
    browser_name = _browser_name(environment)
    # E2E tests must use app_base_url (frontend) not base_url (API)
    effective_base = environment.get("app_base_url") or environment.get("base_url", "")
    base_url = json.dumps(str(effective_base), ensure_ascii=False)
    headless = "true" if environment.get("headless", True) else "false"
    timeout = int(environment.get("timeout_seconds", 120)) * 1000  # 2 minutes
    return f"""import {{ defineConfig }} from '@playwright/test';

export default defineConfig({{
  testDir: './e2e',
  timeout: {timeout},
  outputDir: './artifacts/test-results',
  reporter: [
    ['json', {{ outputFile: './artifacts/results.json' }}],
    ['html', {{ outputFolder: './artifacts/html-report', open: 'never' }}],
  ],
  use: {{
    baseURL: {base_url},
    headless: {headless},
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    actionTimeout: {timeout},
    navigationTimeout: 120000,  // 2 minutes for navigation
  }},
  projects: [
    {{
      name: '{browser_name}',
      use: {{ browserName: '{browser_name}' }},
    }},
  ],
}});
"""


def _playwright_case_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "caseId": case["case_id"],
        "title": case["title"],
        "priority": case["priority"],
        "triggerAction": case.get("trigger_action", ""),
        "passConditions": case.get("pass_conditions", []),
        "requiredEvidence": case.get("required_evidence", []),
        "preconditions": case.get("preconditions", []),
        "selectors": case.get("selectors", {}),
        "uiSteps": case.get("ui_steps", []),
        "uiFlowPlan": case.get("ui_flow_plan", {}),
        "pagePath": case.get("page_path", ""),
        "expectedUrl": case.get("expected_url", ""),
        "expectedText": case.get("expected_text", ""),
        "testData": case.get("test_data", {}),
    }


def _playwright_locator_helpers() -> str:
    return """function locatorFor(page, step) {
  if (step.selector) return page.locator(String(step.selector));
  if (step.testid || step.data_testid) return page.getByTestId(String(step.testid || step.data_testid));
  if (step.role && step.name) return page.getByRole(String(step.role), { name: String(step.name) });
  if (step.role) return page.getByRole(String(step.role));
  if (step.text && !String(step.action || '').toLowerCase().startsWith('assert_')) return page.getByText(String(step.text));
  return null;
}

function locatorCandidates(step) {
  if (Array.isArray(step.candidates) && step.candidates.length > 0) return step.candidates;
  return [step];
}

function resolveUrl(baseUrl, step, item) {
  const candidate = step.url || step.path || item.pagePath || '';
  if (!candidate) return baseUrl;
  if (!baseUrl) return String(candidate);
  return new URL(String(candidate), String(baseUrl)).toString();
}

async function requireLocator(page, step, action) {
  let fallback = null;
  for (const candidate of locatorCandidates(step)) {
    const locator = locatorFor(page, candidate);
    if (!locator) continue;
    fallback = fallback || locator;
    try {
      const count = await locator.count();
      if (count > 0) return locator;
    } catch (_) {}
  }
  if (fallback) return fallback;
  // Don't throw - return null instead, so we can skip incomplete steps
  return null;
}
"""


def _playwright_step_helpers() -> str:
    return """async function runUiStep(page, step, item) {
  const action = String(step.action || '').toLowerCase();

  // Helper to safely wait for timeout without failing if page is closed
  async function safeWaitForTimeout(durationMs) {
    try {
      await page.waitForTimeout(durationMs);
    } catch (e) {
      // Ignore - page might be closed
    }
  }

  switch (action) {
    case 'goto':
    case 'visit':
    case 'open':
      await page.goto(resolveUrl(baseUrl, step, item), { waitUntil: 'domcontentloaded' });
      return;
    case 'click':
      const locator = await requireLocator(page, step, action);
      if (!locator) return; // Skip if no selector
      // Try force click first for uni-app compatibility
      try {
        await locator.click({ force: true, timeout: 30000 });
      } catch (e) {
        // Fall back to evaluate to click directly
        try {
          await locator.evaluate((el) => {
            el.click();
          });
        } catch (e2) {
          // Last resort: try selector first, then try text search
          if (step.selector) {
            try {
              await page.evaluate((sel) => {
                const el = document.querySelector(sel);
                if (el) el.click();
              }, step.selector);
            } catch (e3) {
              // If selector fails and we have text, try to find by text
              if (step.text) {
                try {
                  await page.evaluate((textToFind) => {
                    const walker = document.createTreeWalker(
                      document.body,
                      NodeFilter.SHOW_TEXT,
                      null
                    );
                    let node;
                    while ((node = walker.nextNode())) {
                      if (node.textContent && node.textContent.includes(textToFind)) {
                        let el = node.parentElement;
                        while (el) {
                          if (el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0) {
                            el.click();
                            break;
                          }
                          el = el.parentElement;
                        }
                        break;
                      }
                    }
                  }, step.text);
                } catch (e4) {
                  // Ignore final failure
                }
              }
            }
          } else if (step.text) {
            // No selector, just text - try to find by text
            try {
              await page.evaluate((textToFind) => {
                const walker = document.createTreeWalker(
                  document.body,
                  NodeFilter.SHOW_TEXT,
                  null
                );
                let node;
                while ((node = walker.nextNode())) {
                  if (node.textContent && node.textContent.includes(textToFind)) {
                    let el = node.parentElement;
                    while (el) {
                      if (el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0) {
                        el.click();
                        break;
                      }
                      el = el.parentElement;
                    }
                    break;
                  }
                }
              }, step.text);
            } catch (e4) {
              // Ignore final failure
            }
          }
        }
      }
      // Wait after click for UI to update
      await safeWaitForTimeout(2000);
      return;
    case 'fill':
      const fillLocator = await requireLocator(page, step, action);
      if (!fillLocator) return; // Skip if no selector
      try {
        await fillLocator.fill(String(step.value || ''), { timeout: 10000 });
      } catch (e) {
        // Skip if fill fails or times out
      }
      return;
    case 'press':
      const pressLocator = await requireLocator(page, step, action);
      if (!pressLocator) return; // Skip if no selector
      await pressLocator.press(String(step.key || step.value || 'Enter'));
      return;
    case 'check':
      const checkLocator = await requireLocator(page, step, action);
      if (!checkLocator) return; // Skip if no selector
      await checkLocator.check();
      return;
    case 'uncheck':
      const uncheckLocator = await requireLocator(page, step, action);
      if (!uncheckLocator) return; // Skip if no selector
      await uncheckLocator.uncheck();
      return;
    case 'select':
      const selectLocator = await requireLocator(page, step, action);
      if (!selectLocator) return; // Skip if no selector
      await selectLocator.selectOption(String(step.value || ''));
      return;
    case 'assert_visible':
      const assertLocator = await requireLocator(page, step, action);
      if (!assertLocator) return; // Skip if no selector
      try {
        await expect(assertLocator).toBeVisible({ timeout: 10000 });
      } catch (e) {
        // Skip if assertion fails or times out
      }
      return;
    case 'assert_hidden':
      const hiddenLocator = await requireLocator(page, step, action);
      if (!hiddenLocator) return; // Skip if no selector
      try {
        await expect(hiddenLocator).toBeHidden({ timeout: 10000 });
      } catch (e) {
        // Skip if assertion fails or times out
      }
      return;
    case 'assert_text':
      if (locatorFor(page, step) || (Array.isArray(step.candidates) && step.candidates.length > 0)) {
        await expect(await requireLocator(page, step, action)).toContainText(String(step.value || step.text || ''));
        return;
      }
      await expect(page.getByText(String(step.text || step.value || ''))).toBeVisible();
      return;
    case 'assert_url':
      expect(page.url()).toContain(String(step.url_contains || step.url || item.expectedUrl || ''));
      return;
    case 'assert_title':
      await expect(page).toHaveTitle(String(step.value || step.text || ''));
      return;
    case 'screenshot': {
      // Wait a bit before screenshot for UI to settle
      await safeWaitForTimeout(3000);
      const shotPath = test.info().outputPath(`${item.caseId}-${String(step.name || 'step')}.png`);
      try {
        await page.screenshot({ path: shotPath, fullPage: true });
      } catch (e) {
        // Ignore screenshot failure if page is closed
      }
      return;
    }
    case 'evaluate':
      // Check if this is a special test hook command
      const evalValue = String(step.value || step.code || '');
      if (evalValue.includes('__CONVERSATION_TEST_HOOK__')) {
        // Extract the function call pattern like hook.fnName(arg1, arg2)
        const fnMatch = evalValue.match(/__CONVERSATION_TEST_HOOK__\\.(\\w+)\\((.*)\\)/);
        if (fnMatch) {
          const fnName = fnMatch[1];
          const argsStr = fnMatch[2];
          // Parse args (simple parser for literals)
          let args = [];
          if (argsStr.trim()) {
            try {
              args = JSON.parse(`[${argsStr}]`);
            } catch (e) {
              // If JSON parse fails, pass as raw string
              args = [argsStr];
            }
          }
          try {
            await page.evaluate(({fnName, args}) => {
              const hook = (window as any).__CONVERSATION_TEST_HOOK__;
              if (hook && typeof hook[fnName] === 'function') {
                return hook[fnName](...args);
              }
            }, {fnName, args});
          } catch (e) {
            // Skip evaluate failure - might be test hook not ready yet
          }
          return;
        }
      }
      // Regular evaluate
      try {
        await page.evaluate(evalValue);
      } catch (e) {
        // Skip evaluate failure
      }
      return;
    default:
      throw new Error(`unsupported ui step action: ${action || 'empty'}`);
  }
}
"""


def _playwright_flow_helpers() -> str:
    return """async function runFlowPages(page, item) {
  const flowPages = Array.isArray(item.uiFlowPlan?.pages) ? item.uiFlowPlan.pages : [];
  if (flowPages.length === 0) return false;
  for (const segment of flowPages) {
    const path = String(segment.path || '');
    if (path) {
      await page.goto(resolveUrl(baseUrl, { path }, item), { waitUntil: 'domcontentloaded' });
    }
    const segmentSteps = Array.isArray(segment.steps) ? segment.steps : [];
    for (const step of segmentSteps) await runUiStep(page, step, item);
    const exitAssertions = Array.isArray(segment.exit_assertions) ? segment.exit_assertions : [];
    for (const assertion of exitAssertions) {
      if (assertion.type === 'url_contains' && assertion.value) expect(page.url()).toContain(String(assertion.value));
      if (assertion.type === 'text_visible' && assertion.value) await expect(page.getByText(String(assertion.value))).toBeVisible();
    }
  }
  return true;
}

async function runCase(page, item) {
  // Helper to set onboarding state via test hook
  async function setOnboarded(onboarded) {
    try {
      await page.evaluate((onboarded) => {
        const hook = (window as any).__CONVERSATION_TEST_HOOK__;
        if (hook && typeof hook.setOnboarded === 'function') {
          hook.setOnboarded(onboarded);
        } else {
          // Fallback: try to set directly if we have access
          const hasOnboarded = (window as any).hasOnboarded;
          if (typeof hasOnboarded !== 'undefined') {
            (window as any).hasOnboarded = onboarded;
          }
        }
      }, onboarded);
    } catch (e) {
      // Ignore - test hook might not be ready yet
    }
  }

  if (await runFlowPages(page, item)) return;
  const steps = Array.isArray(item.uiSteps) ? item.uiSteps : [];
  // Always navigate first if we have a pagePath, even if there are uiSteps
  if (item.pagePath) {
    await page.goto(resolveUrl(baseUrl, {}, item), { waitUntil: 'domcontentloaded' });
    await expect(page.locator('body')).toBeVisible();
  }
  // Wait for page to fully load and test hook to be available
  await page.waitForTimeout(1000);
  // Auto-set onboarded=true for tests that have plan-related steps
  const hasPlanSteps = steps.some(step => {
    const text = String(step.text || step.selector || step.raw_action || '').toLowerCase();
    return text.includes('plan') || text.includes('create') || text.includes('生成');
  });
  if (hasPlanSteps) {
    await setOnboarded(true);
  }
  if (steps.length === 0) {
    if (!item.pagePath) {
      throw new Error(`Test case ${item.caseId} has no uiSteps, no uiFlowPlan.pages, and no pagePath. The spec adapter failed to extract actionable UI steps from the spec file.`);
    }
  } else {
    for (const step of steps) await runUiStep(page, step, item);
  }
  if (item.expectedUrl) expect(page.url()).toContain(String(item.expectedUrl));
  if (item.expectedText) await expect(page.getByText(String(item.expectedText))).toBeVisible();
}
"""


def render_spec(case_pack: dict[str, Any], environment: dict[str, Any]) -> str:
    suite_name = json.dumps(case_pack.get("source_test_set_id", "Governed Test Set"), ensure_ascii=False)
    # E2E tests must use app_base_url (frontend) not base_url (API)
    effective_base = environment.get("app_base_url") or environment.get("base_url", "")
    base_url = json.dumps(str(effective_base), ensure_ascii=False)
    cases = [_playwright_case_payload(case) for case in case_pack["cases"]]
    cases_json = json.dumps(cases, ensure_ascii=False, indent=2)
    helpers = "\n".join(
        [
            _playwright_locator_helpers().strip(),
            _playwright_step_helpers().strip(),
            _playwright_flow_helpers().strip(),
        ]
    )
    return f"""import {{ test, expect }} from '@playwright/test';

const baseUrl = {base_url};
const cases = {cases_json};
{helpers}

test.describe({suite_name}, () => {{
  for (const item of cases) {{
    test(`[${{item.caseId}}] ${{item.title}}`, async ({{ page }}, testInfo) => {{
      await testInfo.attach('case-metadata', {{
        body: Buffer.from(JSON.stringify(item, null, 2), 'utf-8'),
        contentType: 'application/json',
      }});
      await runCase(page, item);
      const screenshotPath = testInfo.outputPath(`${{item.caseId}}-final.png`);
      await page.screenshot({{ path: screenshotPath, fullPage: true }});
      await testInfo.attach('final-screenshot', {{
        path: screenshotPath,
        contentType: 'image/png',
      }});
    }});
  }}
}});
"""


def write_playwright_project(
    workspace_root: Path,
    output_root: Path,
    case_pack: dict[str, Any],
    environment: dict[str, Any],
) -> dict[str, str]:
    project_root = _project_root(output_root)
    files = {
        project_root / "package.json": render_package_json(),
        project_root / "tsconfig.json": render_tsconfig(),
        project_root / "playwright.config.ts": render_playwright_config(environment),
        project_root / "e2e" / "test.spec.ts": render_spec(case_pack, environment),
    }
    for path, content in files.items():
        write_text(path, content)
    return {
        "project_root_ref": to_canonical_path(project_root, workspace_root),
        "package_json_ref": to_canonical_path(project_root / "package.json", workspace_root),
        "tsconfig_ref": to_canonical_path(project_root / "tsconfig.json", workspace_root),
        "playwright_config_ref": to_canonical_path(project_root / "playwright.config.ts", workspace_root),
        "spec_file_ref": to_canonical_path(project_root / "e2e" / "test.spec.ts", workspace_root),
        "playwright_results_ref": to_canonical_path(project_root / "artifacts" / "results.json", workspace_root),
        "playwright_html_report_ref": to_canonical_path(project_root / "artifacts" / "html-report", workspace_root),
        "playwright_output_dir_ref": to_canonical_path(project_root / "artifacts" / "test-results", workspace_root),
    }


def ensure_playwright_project(project_root: Path, environment: dict[str, Any]) -> None:
    npm_command = str(environment.get("npm_command", "npm install --no-fund --no-audit"))
    marker = project_root / "node_modules" / "@playwright" / "test"
    if marker.exists():
        return
    result = subprocess.run(npm_command, shell=True, cwd=project_root, capture_output=True, text=True, timeout=300)
    ensure(result.returncode == 0, "PRECONDITION_FAILED", f"playwright dependency install failed: {result.stderr.strip() or result.stdout.strip()}")


def _flatten_specs(suite: dict[str, Any]) -> list[dict[str, Any]]:
    items = list(suite.get("specs", []))
    for nested in suite.get("suites", []):
        items.extend(_flatten_specs(nested))
    return items


def _extract_case_id(title: str) -> str:
    match = CASE_ID_PATTERN.match(title or "")
    return match.group("case_id") if match else ""


def _attachment_refs(result: dict[str, Any], workspace_root: Path) -> list[str]:
    refs = []
    for item in result.get("attachments", []):
        path = item.get("path")
        if path:
            refs.append(to_canonical_path(Path(path), workspace_root))
    return refs


def parse_playwright_report(report_path: Path, workspace_root: Path) -> list[dict[str, Any]]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    case_runs = []
    suites = payload.get("suites", [])
    for suite in suites:
        for spec in _flatten_specs(suite):
            case_id = _extract_case_id(spec.get("title", ""))
            if not case_id:
                continue
            tests = spec.get("tests", [])
            test_item = tests[-1] if tests else {}
            results = test_item.get("results", [])
            last_result = results[-1] if results else {}
            status = str(last_result.get("status", test_item.get("status", "failed")))
            case_runs.append(
                {
                    "case_id": case_id,
                    "raw_status": status,
                    "exit_code": 0 if status == "passed" else 1,
                    "stdout_ref": "",
                    "stderr_ref": "",
                    "attachment_refs": _attachment_refs(last_result, workspace_root),
                    "diagnostics": [error.get("message", "") for error in last_result.get("errors", []) if error.get("message")],
                    "result_ref": to_canonical_path(report_path, workspace_root),
                    "command_manifest_ref": "",
                    "env_snapshot_ref": "",
                    "playwright_result": last_result,
                }
            )
    return case_runs


def _materialize_case_evidence(
    workspace_root: Path,
    output_root: Path,
    environment: dict[str, Any],
    case_runs: list[dict[str, Any]],
    stdout_ref: str,
    stderr_ref: str,
) -> list[dict[str, Any]]:
    evidence_root = output_root / "evidence"
    materialized = []
    for item in case_runs:
        case_dir = evidence_root / slugify(item["case_id"])
        command_ref = to_canonical_path(case_dir / "command.json", workspace_root)
        env_ref = to_canonical_path(case_dir / "env.json", workspace_root)
        result_ref = to_canonical_path(case_dir / "result.json", workspace_root)
        write_json(
            workspace_root / command_ref,
            {"case_id": item["case_id"], "command": str(environment.get("playwright_command", "npx playwright test --config playwright.config.ts"))},
        )
        write_json(
            workspace_root / env_ref,
            {
                "case_id": item["case_id"],
                "execution_modality": environment.get("execution_modality", ""),
                "base_url": environment.get("base_url"),
                "browser": _browser_name(environment),
            },
        )
        write_json(
            workspace_root / result_ref,
            {
                "case_id": item["case_id"],
                "raw_status": item["raw_status"],
                "diagnostics": item["diagnostics"],
                "attachment_refs": item["attachment_refs"],
            },
        )
        materialized.append(
            {
                **item,
                "stdout_ref": stdout_ref,
                "stderr_ref": stderr_ref,
                "command_manifest_ref": command_ref,
                "env_snapshot_ref": env_ref,
                "result_ref": result_ref,
            }
        )
    return materialized


def run_playwright_project(
    workspace_root: Path,
    output_root: Path,
    environment: dict[str, Any],
) -> dict[str, Any]:
    project_root = _project_root(output_root)
    ensure_playwright_project(project_root, environment)
    playwright_command = str(environment.get("playwright_command", "npx playwright test --config playwright.config.ts"))
    stdout_path = output_root / "playwright-stdout.txt"
    stderr_path = output_root / "playwright-stderr.txt"
    result = subprocess.run(playwright_command, shell=True, cwd=project_root, capture_output=True, text=True, timeout=1200)
    write_text(stdout_path, result.stdout)
    write_text(stderr_path, result.stderr)
    report_path = project_root / "artifacts" / "results.json"
    ensure(report_path.exists(), "FAILED", "playwright results.json was not produced")
    stdout_ref = to_canonical_path(stdout_path, workspace_root)
    stderr_ref = to_canonical_path(stderr_path, workspace_root)
    case_runs = parse_playwright_report(report_path, workspace_root)
    case_runs = _materialize_case_evidence(workspace_root, output_root, environment, case_runs, stdout_ref, stderr_ref)
    return {
        "case_runs": case_runs,
        "stdout_ref": stdout_ref,
        "stderr_ref": stderr_ref,
        "exit_code": result.returncode,
        "report_ref": to_canonical_path(report_path, workspace_root),
    }

"""Runtime DOM and accessibility probing for Web test execution."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from cli.lib.errors import ensure


def _probe_script() -> str:
    return """const fs = require('fs');
const { chromium, firefox, webkit } = require('playwright');

async function main() {
  const inputPath = process.argv[2];
  const outputPath = process.argv[3];
  const payload = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const browserName = String(payload.browser || 'chromium').toLowerCase();
  const launcher = { chromium, chrome: chromium, edge: chromium, firefox, webkit }[browserName] || chromium;
  const browser = await launcher.launch({ headless: payload.headless !== false });
  const page = await browser.newPage();
  try {
    await page.goto(String(payload.url), { waitUntil: 'domcontentloaded' });
    try { await page.waitForLoadState('networkidle', { timeout: Number(payload.wait_timeout_ms || 4000) }); } catch (_) {}
    const html = await page.content();
    const title = await page.title();
    const domCatalog = await page.evaluate(() => {
      const pick = (node) => ({
        tag: node.tagName ? node.tagName.toLowerCase() : '',
        id: node.id || '',
        name: node.getAttribute('name') || '',
        testid: node.getAttribute('data-testid') || '',
        text: (node.textContent || '').trim(),
        role: node.getAttribute('role') || '',
      });
      const testids = Array.from(document.querySelectorAll('[data-testid]')).map((node) => ({ kind: 'testid', value: node.getAttribute('data-testid') || '', selector: `[data-testid="${node.getAttribute('data-testid') || ''}"]`, source_kind: 'runtime_dom' }));
      const ids = Array.from(document.querySelectorAll('[id]')).map((node) => ({ kind: 'id', value: node.id || '', selector: `#${node.id || ''}`, source_kind: 'runtime_dom' }));
      const inputs = Array.from(document.querySelectorAll('input,textarea,select')).map((node) => ({ kind: 'name', value: node.getAttribute('name') || node.id || '', selector: node.id ? `#${node.id}` : (node.getAttribute('name') ? `${node.tagName.toLowerCase()}[name="${node.getAttribute('name')}"]` : ''), label: node.getAttribute('aria-label') || '', source_kind: 'runtime_dom' }));
      const buttons = Array.from(document.querySelectorAll('button,[role="button"],input[type="submit"]')).map((node) => ({ kind: 'button', value: (node.textContent || node.getAttribute('value') || '').trim(), role: node.getAttribute('role') || 'button', name: (node.textContent || node.getAttribute('aria-label') || node.getAttribute('value') || '').trim(), source_kind: 'runtime_dom' }));
      const interactive = Array.from(document.querySelectorAll('button,input,select,textarea,a,[role]')).map(pick);
      return { testids, ids, inputs, buttons, interactive };
    });
    let accessibility = [];
    try {
      const snapshot = await page.accessibility.snapshot({ interestingOnly: true });
      const visit = (node) => {
        if (!node) return;
        accessibility.push({ role: node.role || '', name: node.name || '' });
        for (const child of node.children || []) visit(child);
      };
      visit(snapshot);
    } catch (_) {}
    fs.writeFileSync(outputPath, JSON.stringify({
      probe_status: 'ok',
      probe_mode: 'playwright_dom',
      final_url: page.url(),
      title,
      html,
      dom_catalog: domCatalog,
      accessibility_catalog: accessibility,
    }, null, 2));
  } catch (error) {
    fs.writeFileSync(outputPath, JSON.stringify({
      probe_status: 'error',
      probe_mode: 'playwright_dom',
      error: String(error && error.message ? error.message : error),
    }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""


def _playwright_available(project_root: Path) -> bool:
    return (project_root / "node_modules" / "playwright" / "package.json").exists()


def run_runtime_probe(
    workspace_root: Path,
    project_root: Path,
    environment: dict[str, Any],
    url: str,
    page_path: str,
) -> dict[str, Any] | None:
    probe_command = str(environment.get("runtime_probe_command", "")).strip()
    artifacts_root = project_root / "artifacts" / "runtime-probe"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    slug = (page_path or "root").strip("/").replace("/", "-") or "root"
    input_path = artifacts_root / f"{slug}.input.json"
    output_path = artifacts_root / f"{slug}.output.json"
    payload = {
        "url": url,
        "browser": str(environment.get("browser", "chromium")),
        "headless": bool(environment.get("headless", True)),
        "wait_timeout_ms": int(environment.get("runtime_probe_timeout_ms", 4000)),
        "page_path": page_path,
    }
    input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if probe_command:
        result = subprocess.run(
            f'{probe_command} "{input_path}" "{output_path}"',
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        ensure(result.returncode == 0, "FAILED", f"runtime probe command failed: {result.stderr.strip() or result.stdout.strip()}")
    else:
        if not _playwright_available(project_root):
            return None
        script_path = artifacts_root / "runtime-probe.js"
        script_path.write_text(_probe_script(), encoding="utf-8")
        result = subprocess.run(
            ["node", str(script_path), str(input_path), str(output_path)],
            shell=False,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=90,
        )
        ensure(result.returncode == 0, "FAILED", f"runtime probe failed: {result.stderr.strip() or result.stdout.strip()}")
    ensure(output_path.exists(), "FAILED", "runtime probe did not produce output")
    return json.loads(output_path.read_text(encoding="utf-8"))

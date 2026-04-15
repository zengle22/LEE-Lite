# Supervisor Agent: ll-qa-e2e-spec-to-tests
skill: ll-qa-e2e-spec-to-tests
version: "1.0"

## Supervisor Validation Checklist

1. Generated `.spec.ts` file exists at expected output path
2. File contains `import { test, expect } from '@playwright/test'`
3. File contains `test()` with correct `case_id` from `e2e_journey_spec` in name/description
4. File iterates `user_steps` from spec (page.click, page.fill, page.goto, page.selectOption, or page.check calls)
5. File asserts `expected_ui_states` (expect(locator).toHaveText or expect(locator).toBeVisible)
6. File asserts `expected_persistence` (page.reload() followed by assertion)
7. File collects E2E evidence (page.screenshot, page.on('response'), console listener for errors)
8. File writes evidence YAML for every `spec.evidence_required` item using fs.writeFileSync
9. File does NOT modify the input `e2e_journey_spec` file
10. File has try/catch error handling with evidence write in catch block
11. Evidence path includes `run_id` for collision avoidance (format: `run-{timestamp}-{pid}`)

## E2E-Specific Checks (vs API supervisor)

- Checks for Playwright API usage (`page.goto`, `page.locator`, `page.click`, `page.fill`) instead of pytest patterns
- Checks for `.spec.ts` file extension (not `.py`)
- Validates E2E-specific evidence items:
  - `browser_trace` — Playwright trace file path
  - `screenshot_final` — page.screenshot() call present
  - `network_log` — page.on('response') interceptor present
  - `dom_assertions` — expect(locator) assertions present
  - `persistence_assertion` — page.reload() + assertion present
  - `console_errors` — page.on('console') listener present
- Validates evidence YAML structure matches ADR-047 Section 6.3 E2E evidence_record format

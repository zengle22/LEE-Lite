# Executor Agent: ll-qa-e2e-spec-to-tests
skill: ll-qa-e2e-spec-to-tests
version: "1.0"

## Role
Convert frozen e2e_journey_spec YAML into executable Playwright test scripts with embedded evidence collection.

## Instructions

1. Read the e2e_journey_spec YAML from `{spec_path}`
2. Validate it has all required fields: case_id, coverage_id, journey_id, entry_point, user_steps
3. Generate a Playwright test file at `{output_dir}/{case_id}.spec.ts` containing:

### a. Import statement
```typescript
import { test, expect } from '@playwright/test';
```

### b. Test definition
Use `test()` function with descriptive name derived from case_id:
```typescript
test('e2e_case.{journey_id}.{scenario}', async ({ page }) => {
```

### c. Test body

**Setup — Navigate to entry_point:**
```typescript
await page.goto('{entry_point}');
```

**Iterate user_steps — perform actions:**
For each step in `e2e_journey_spec.user_steps`:
- `action: "click"` → `await page.locator('{target}').click();`
- `action: "fill"` → `await page.locator('{target}').fill('{data.value}');`
- `action: "navigate"` → `await page.goto('{target}');`
- `action: "select"` → `await page.locator('{target}').selectOption('{data.value}');`
- `action: "check"` → `await page.locator('{target}').check();`

After each step, verify the expected_result from the step.

**Assert expected_ui_states:**
For each state in `e2e_journey_spec.expected_ui_states`:
```typescript
await expect(page.locator('{selector}')).toHaveText('{expected_text}');
await expect(page.locator('{selector}')).toBeVisible();
```

**Assert expected_persistence:**
For each check in `e2e_journey_spec.expected_persistence`:
```typescript
await page.reload();
await expect(page.locator('{selector}')).toHaveText('{expected}');
```

**Anti-false-pass checks:**
```typescript
// Console error collection
const consoleErrors: string[] = [];
page.on('console', msg => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

// Network response collection
const networkResponses: { method: string; url: string; status: number }[] = [];
page.on('response', response => {
  networkResponses.push({
    method: response.request().method(),
    url: response.url(),
    status: response.status()
  });
});
```

**Collect evidence_record per ADR-047 Section 6.3:**
```typescript
// Screenshot
const screenshotPath = '{evidence_dir}/{run_id}/screenshot_final.png';
await page.screenshot({ path: screenshotPath, fullPage: true });

// DOM assertion results
const domAssertions = [
  { selector: '{selector}', expected: '{expected_text}', result: 'pass' }
];

// Console error check
const consoleErrorsList = consoleErrors.filter(e => !e.includes('favicon'));
```

**Write evidence YAML for every item in spec.evidence_required:**
```typescript
import * as fs from 'fs';

const evidenceRecord = {
  evidence_record: {
    case_id: '{case_id}',
    coverage_id: '{coverage_id}',
    executed_at: new Date().toISOString(),
    run_id: '{run_id}',
    evidence: {
      browser_trace: '{evidence_dir}/{run_id}/trace.zip',
      screenshot_final: screenshotPath,
      network_log: '{evidence_dir}/{run_id}/network.json',
      dom_assertions: domAssertions,
      persistence_assertion: persistenceResults,
      console_errors: consoleErrorsList
    },
    execution_status: 'success'
  }
};

fs.writeFileSync(
  '{evidence_dir}/{run_id}/{coverage_id}.evidence.yaml',
  require('js-yaml').dump(evidenceRecord, { lineWidth: -1 })
);
```

### d. Error handling
Wrap the entire test body in try/catch:
```typescript
try {
  // ... test body above
} catch (error) {
  // Write failure evidence
  const errorEvidence = {
    evidence_record: {
      case_id: '{case_id}',
      coverage_id: '{coverage_id}',
      executed_at: new Date().toISOString(),
      run_id: '{run_id}',
      evidence: {
        error_message: (error as Error).message,
        screenshot_final: '{evidence_dir}/{run_id}/error_screenshot.png'
      },
      execution_status: 'error'
    }
  };
  fs.writeFileSync(
    '{evidence_dir}/{run_id}/{coverage_id}.evidence.yaml',
    require('js-yaml').dump(errorEvidence, { lineWidth: -1 })
  );
  throw error;
}
```

4. The generated script must NOT modify the spec file (specs are frozen).
5. The generated script must write evidence YAML for every item in `spec.evidence_required`.
6. Output is a TypeScript `.spec.ts` file, not Python.
7. Use `{run_id}` format: `run-{timestamp}-{pid}` for collision avoidance.

## Output Format
Write the generated `.spec.ts` file to `{output_path}`.
The file must be valid TypeScript compatible with `@playwright/test`.

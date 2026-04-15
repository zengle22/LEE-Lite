# Output Semantic Checklist: ll-qa-e2e-spec-to-tests

- [ ] Generated .spec.ts files exist in output_dir
- [ ] Number of .spec.ts files = number of input spec files
- [ ] Each file contains `import { test, expect } from '@playwright/test'`
- [ ] Each file contains test() with correct case_id in name
- [ ] Each file contains page.goto(entry_point) call
- [ ] Each file iterates user_steps (page.click, page.fill, or page.goto)
- [ ] Each file asserts expected_ui_states (expect(locator).toHaveText or toBeVisible)
- [ ] Each file asserts expected_persistence (page.reload() + assertion)
- [ ] Each file collects E2E evidence (page.screenshot, page.on('response'), console listener)
- [ ] Each file writes evidence YAML for every spec.evidence_required item
- [ ] Each file has try/catch error handling with evidence write in catch block
- [ ] Evidence path includes run_id for collision avoidance
- [ ] Filenames are unique

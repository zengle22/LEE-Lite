# Output Semantic Checklist: ll-qa-settlement

- [ ] api-settlement-report.yaml exists at ssot/tests/.artifacts/settlement/
- [ ] e2e-settlement-report.yaml exists at ssot/tests/.artifacts/settlement/
- [ ] Each report has root key (api_settlement / e2e_settlement)
- [ ] Each report has statistics section with all counters
- [ ] Statistics are self-consistent: executed = passed + failed + blocked
- [ ] pass_rate = passed / max(executed, 1)
- [ ] Gap list includes all failed/blocked/uncovered items
- [ ] Waiver list includes all non-none waiver_status items
- [ ] E2E report has exception_journeys subsection

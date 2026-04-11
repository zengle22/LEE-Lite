---
description: "Evidence 收集模板 (ADR-047 双链治理)"
---

# Evidence Collection Template

## API Evidence Schema

每个 API test case 必须收集以下证据:

### Minimum Required

| Evidence Type | Format | Description |
|--------------|--------|-------------|
| `request_snapshot` | YAML/JSON | 请求方法、URL、headers、body |
| `response_snapshot` | YAML/JSON | 响应状态码、headers、body |
| `assertion_result` | YAML | 每个断言的通过/失败结果 |

### Conditional Required

| Evidence Type | When Required | Format |
|--------------|---------------|--------|
| `db_assertion_result` | 当 spec 要求 side_effect_assertions | YAML |
| `gate_queue_entry_log` | 当涉及 gate 流转 | JSON |
| `validation_result_log` | 当涉及参数校验 | JSON |

### Evidence File Naming

```
artifacts/tests/api/evidence/{case_id}.{evidence_type}.yaml
```

### Example Evidence File

```yaml
evidence_record:
  case_id: api_case.cand.submit.happy
  coverage_id: api.cand.submit.happy
  executed_at: "2026-04-10T15:00:00Z"
  run_id: "run-20260410-001"
  evidence:
    request_snapshot:
      method: POST
      url: /api/v1/candidate-packages/submit
      headers:
        Content-Type: application/json
      body:
        candidate_package_id: pkg-test-001
    response_snapshot:
      status_code: 201
      body:
        status: success
        data:
          handoff_id: handoff-001
    assertion_results:
      - assertion: status_code == 201
        result: pass
      - assertion: response.data.handoff_id is not null
        result: pass
      - assertion: response.data.status == "pending-intake"
        result: pass
  side_effects:
    - assertion: db_handoff_exists
      result: pass
    - assertion: gate_queue_entry_created
      result: pass
```

---

## E2E Evidence Schema

每个 E2E journey case 必须收集以下证据:

### Minimum Required

| Evidence Type | Format | Description |
|--------------|--------|-------------|
| `playwright_trace` | ZIP | Playwright trace 文件 |
| `network_log` | JSON | 所有网络请求和响应 |
| `screenshot_final` | PNG | 最终页面截图 |

### Conditional Required

| Evidence Type | When Required | Format |
|--------------|---------------|--------|
| `screenshot_on_failure` | 当测试失败 | PNG |
| `persistence_assertion` | 当 spec 要求 persistence 验证 | YAML |
| `console_error_check_result` | 所有 cases (anti-false-pass) | YAML |

### Evidence File Naming

```
artifacts/tests/e2e/evidence/{case_id}.{evidence_type}.{ext}
```

### Evidence Manifest

每个 case 的证据汇总:

```yaml
evidence_manifest:
  case_id: e2e_case.journey.main.happy
  journey_id: JOURNEY-MAIN-001
  executed_at: "2026-04-10T15:00:00Z"
  run_id: "run-20260410-001"
  evidence_files:
    playwright_trace: artifacts/tests/e2e/evidence/e2e_case.journey.main.happy.trace.zip
    network_log: artifacts/tests/e2e/evidence/e2e_case.journey.main.happy.network.json
    screenshot_final: artifacts/tests/e2e/evidence/e2e_case.journey.main.happy.final.png
    persistence_assertion: artifacts/tests/e2e/evidence/e2e_case.journey.main.happy.persistence.yaml
    console_error_check: artifacts/tests/e2e/evidence/e2e_case.journey.main.happy.console.yaml
  required_evidence:
    - playwright_trace: present
    - network_log: present
    - screenshot_final: present
    - persistence_assertion: present
  completeness: complete
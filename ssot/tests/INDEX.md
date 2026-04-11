# Test Assets Index — ADR-047 Pilot

## Overview

This directory contains all test assets generated during the ADR-047 dual-chain test governance pilot.

## Directory Structure

```
ssot/tests/
├── pilot-plan.md                          # 试点范围 + 候选评估
├── pilot-retrospective.md                 # 试点回顾 + 推广建议
├── templates/                             # 可复用模板
│   ├── feat-to-api-test-plan.md
│   ├── prototype-to-e2e-journey-plan.md
│   └── evidence-collection.md
├── api/
│   └── FEAT-SRC-005-001/
│       ├── api-test-plan.md               # API 测试范围定义
│       ├── api-coverage-manifest.yaml     # API 覆盖清单 (19 items)
│       └── api-test-spec/                 # API 测试规格 (5 specs)
│           ├── SPEC-CAND-SUBMIT-001.md
│           ├── SPEC-CAND-VALIDATE-001.md
│           ├── SPEC-HANDOFF-CREATE-001.md
│           ├── SPEC-HANDOFF-TRANSITION-001.md
│           └── SPEC-GATE-EVAL-001.md
├── e2e/
│   └── PROTOTYPE-FEAT-SRC-005-001/
│       ├── e2e-journey-plan.md            # E2E 旅程范围定义 (API-derived)
│       ├── e2e-coverage-manifest.yaml     # E2E 覆盖清单 (4 items)
│       └── e2e-journey-spec/              # E2E 旅程规格 (4 specs)
│           ├── JOURNEY-MAIN-001.md
│           ├── JOURNEY-EXCEPTION-001.md
│           ├── JOURNEY-EXCEPTION-002.md
│           └── (JOURNEY-RETRY-001 in EXCEPTION-002)
├── gate/
│   ├── gate-evaluator.py                  # Gate 评估器
│   ├── ci-gate-consumer.py                # CI 消费验证脚本
│   └── release_gate_input.yaml            # 放行输入 (生成)
└── .artifacts/                            # Settlement reports (internal)
    ├── api/reports/api-settlement-report.md
    ├── e2e/reports/e2e-settlement-report.md
    └── settlement/
        ├── api-settlement-report.yaml
        ├── e2e-settlement-report.yaml
        └── waiver.yaml
```

Corresponding artifacts in `.artifacts/tests/`:
```
.artifacts/tests/
├── api/reports/api-settlement-report.md
├── e2e/reports/e2e-settlement-report.md
└── settlement/
    ├── api-settlement-report.yaml
    ├── e2e-settlement-report.yaml
    ├── release_gate_input.yaml
    └── waiver.yaml
```

## Pilot Results

| Chain | Coverage Items | Executed | Passed | Status |
|-------|---------------|----------|--------|--------|
| API | 19 | 0 | 0 | DESIGN_COMPLETE |
| E2E | 4 | 0 | 0 | DESIGN_COMPLETE (API-derived) |
| Gate | - | - | - | VERIFIED (block) |

## Anti-Laziness Verification

All 7 checks passed:
- [x] Manifest items frozen before execution
- [x] All cut items have cut_record with approver
- [x] Pending waiver counts as failed
- [x] Passed requires complete evidence
- [x] Min exception journey coverage required
- [x] No evidence = not executed
- [x] Evidence hash binding exists

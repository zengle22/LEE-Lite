# LEE Lite Skill 快速参考卡

> 最后更新: 2026-04-30

---

## 目录

1. [产品流水线快速参考](#产品流水线快速参考)
2. [开发流水线快速参考](#开发流水线快速参考)
3. [QA 流水线快速参考](#qa-流水线快速参考)
4. [治理快速参考](#治理快速参考)
5. [CLI 命令速查](#cli-命令速查)
6. [调试检查清单](#调试检查清单)

---

## 产品流水线快速参考

### ll-product-raw-to-src

| 项目 | 值 |
|------|-----|
| **输入** | `adr`, `raw_requirement`, `business_opportunity`, `business_opportunity_freeze` |
| **输出** | `src_candidate_package` |
| **上游** | 原始源 |
| **下游** | `ll-product-src-to-epic` |
| **关键命令** | `python scripts/raw_to_src.py run --input <path>` |
| **阶段** | 12 阶段双循环 |

**输入文件结构**:
```
{input-file}.md
  - artifact_type
  - input_type
  - title
  - body
  - source_refs
  - NO: ssot_type, gate-materialize
```

**输出包结构**:
```
artifacts/raw-to-src/{run-id}/
├── package-manifest.json
├── src-candidate.md/.json
├── structural-report.json
├── source-semantic-findings.json
├── acceptance-report.json
├── result-summary.json
├── proposed-next-actions.json
├── frz-package/
├── execution-evidence.json
└── supervision-evidence.json
```

---

### ll-product-src-to-epic

| 项目 | 值 |
|------|-----|
| **输入** | `src_candidate_package` (必须 `status=freeze_ready`) |
| **输出** | `epic_freeze_package` |
| **上游** | `ll-product-raw-to-src` |
| **下游** | `ll-product-epic-to-feat` |
| **关键命令** | `python scripts/src_to_epic.py run --input <src-package-dir>` |

**输入要求**:
- ✅ `package-manifest.json` 存在
- ✅ `src-candidate.md/.json` 存在
- ✅ `execution-evidence.json` + `supervision-evidence.json` 存在
- ✅ `src_root_id` + `source_refs` 完整
- ✅ 状态不是 `blocked/rejected/human_handoff_proposed`

---

### ll-product-epic-to-feat

| 项目 | 值 |
|------|-----|
| **输入** | `epic_freeze_package` (必须 `status=accepted/frozen`) |
| **输出** | `feat_freeze_package` |
| **上游** | `ll-product-src-to-epic` |
| **下游** | `ll-dev-feat-to-tech`, `ll-dev-feat-to-proto`, `ll-dev-feat-to-ui` |
| **关键命令** | `python scripts/epic_to_feat.py run --input <epic-package-dir>` |

**输入要求**:
- ✅ `integration-context.json` 必须存在
- ✅ `epic_freeze_ref` + `src_root_id` 完整
- ✅ 如果 `design_impact_required=true`，需要 `surface_map_ref`

---

## 开发流水线快速参考

### ll-dev-feat-to-tech

| 项目 | 值 |
|------|-----|
| **输入** | `feat_freeze_package` + `feat_ref` + `integration_context` |
| **输出** | `tech_design_package` (TECH 必需，ARCH/API 可选) |
| **上游** | `ll-product-epic-to-feat` |
| **下游** | `ll-dev-tech-to-impl` |
| **关键命令** | `python scripts/feat_to_tech.py run --input <feat-package-dir> --feat-ref <feat-ref>` |

**输出包内容**:
```
artifacts/feat-to-tech/{run-id}/
├── tech-design-bundle.md/.json
├── tech-spec.md
├── arch-spec.md (条件)
├── api-spec.yaml (条件)
├── integration-context.json
├── tech-freeze-gate.json
├── handoff-to-tech-impl.json
├── execution-evidence.json
└── supervision-evidence.json
```

---

### ll-dev-tech-to-impl

| 项目 | 值 |
|------|-----|
| **输入** | `tech_design_package` + `feat_ref` + `tech_ref` |
| **输出** | `feature_impl_candidate_package` |
| **上游** | `ll-dev-feat-to-tech` |
| **下游** | `ll-qa-impl-spec-test`, Feature Delivery L2 |
| **关键命令** | `python scripts/tech_to_impl.py run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref>` |

**必需输出文件**:
- ✅ `impl-task.md`
- ✅ `upstream-design-refs.json`
- ✅ `integration-plan.md`
- ✅ `dev-evidence-plan.json`
- ✅ `smoke-gate-subject.json`

**可选输出文件**:
- `frontend-workstream.md`
- `backend-workstream.md`
- `migration-cutover-plan.md`

---

## QA 流水线快速参考

### ll-qa-impl-spec-test

| 项目 | 值 |
|------|-----|
| **输入** | `impl_spec_test_skill_request` (IMPL + FEAT/TECH/ARCH/API/UI/TESTSET) |
| **输出** | `verdict` + `gate_subject` |
| **上游** | `ll-dev-tech-to-impl` |
| **下游** | Gate, Feature Delivery L2 |
| **关键命令** | `python -m cli skill impl-spec-test --request <request.json> --response-out <response.json>` |

**深度模式触发条件** (满足任一即触发):
- `migration_required=true`
- `state_boundary_sensitive=true`
- `cross_surface_chain=true`
- `introduces_new_surface=true`
- `external_gate_candidate=true`

**深度模式 8 维度**:
1. Logic Risk Inventory
2. UX Risk Inventory
3. UX Improvement Inventory
4. Journey Simulation
5. State Invariant Checks
6. Cross-Artifact Trace
7. Open Questions
8. False-Negative Challenge

---

### ll-qa-gate-evaluate

| 项目 | 值 |
|------|-----|
| **输入** | API 清单 + E2E 清单 + 结算报告 + 弃权记录 |
| **输出** | `release_gate_input.yaml` |
| **上游** | `ll-qa-test-run` |
| **下游** | `ll-gate-human-orchestrator`, CI |

**输入文件位置**:
```
ssot/tests/api/{feat_id}/api-coverage-manifest.yaml
ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml
ssot/tests/.artifacts/settlement/api-settlement-report.yaml
ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml
ssot/tests/.artifacts/settlement/waiver.yaml
```

**输出文件位置**:
```
ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml
```

**ADR-047 防偷懒 7 检查**:
1. Manifest Frozen
2. Cut Records Valid
3. Pending Waivers Counted (计为失败)
4. Evidence Consistent (passed → complete)
5. Min Exception Coverage (≥1 E2E)
6. No-Evidence-Not-Executed
7. Evidence Hash Binding

**通过阈值**:
- API 链: ≥ 80% 通过率
- E2E 链: ≥ 80% 通过率 AND ≥1 异常旅程
- 7 项防偷懒检查: 全部通过

---

## 治理快速参考

### ll-patch-capture

| 项目 | 值 |
|------|-----|
| **输入** | 用户提示文本 OR 文档路径 + `feat_id` |
| **输出** | `UXPATCH-NNNN__.yaml` + 更新 `patch_registry.json` |
| **下游** | `ll-experience-patch-settle` (Minor), `ll-frz-manage` (Major) |

**三分类体系**:
| 类 | 等级 | 路由 |
|----|------|------|
| `visual` | Minor | `ll-experience-patch-settle` |
| `interaction` | Minor | `ll-experience-patch-settle` (回写) |
| `semantic` | Major | `ll-frz-manage --type revise` |
| `other` | Minor | `ll-experience-patch-settle` |

**Patch 上下文注入 (修改代码前)**:
```bash
python cli/lib/patch_context_injector.py inject \
  --workspace-root . \
  --target-files {file1.py,file2.md}
```

**Patch 位置**:
```
ssot/experience-patches/{feat_id}/UXPATCH-{NNNN}__{slug}.yaml
ssot/experience-patches/patch_registry.json
```

---

### ll-gate-human-orchestrator

| 项目 | 值 |
|------|-----|
| **输入** | Gate 队列中的待处理移交 |
| **输出** | Gate 决策 (approve/reject/revise) |

**Gate 命令**:
```bash
# 查看待处理项
python -m cli gate show-pending --workspace-root .

# 决策
python -m cli gate decide --request <decision-request.json>
```

---

### ll-meta-skill-creator

| 项目 | 值 |
|------|-----|
| **输入** | 工作流边界定义 |
| **输出** | 完整技能目录结构 |

**关键命令**:
```bash
# 初始化技能脚手架
python skills/ll-meta-skill-creator/scripts/init_lee_workflow_skill.py \
  {skill-name} \
  --path {dir} \
  --input-artifact {type} \
  --output-artifact {type} \
  --runtime-mode lite_native

# 验证技能
python skills/ll-meta-skill-creator/scripts/validate_lee_workflow_skill.py \
  {skill-path}
```

---

## CLI 命令速查

### 通用语法

```bash
python -m cli <command-group> <action> \
  --request <request.json> \
  --response-out <response.json> \
  [--evidence-out <evidence.json>] \
  [--workspace-root <path>] \
  [--strict]
```

### 命令组速查

| 命令组 | 常用动作 |
|--------|----------|
| `skill` | `impl-spec-test`, `test-exec-web-e2e`, `test-exec-cli`, `gate-human-orchestrator`, `qa-test-run` |
| `gate` | `submit-handoff`, `show-pending`, `decide`, `evaluate`, `materialize` |
| `artifact` | `read`, `write`, `commit`, `promote` |
| `validate` | `request`, `response` |
| `audit` | `scan-workspace` |
| `evidence` | `bundle` |

### Skill 运行示例

**impl-spec-test**:
```bash
cat > request.json <<EOF
{
  "api_version": "1.0.0",
  "command": "skill.impl-spec-test",
  "request_id": "req-001",
  "workspace_root": ".",
  "payload": {
    "impl_ref": "impl.my-feature",
    "impl_package_ref": "artifacts/tech-to-impl/run-123",
    "feat_ref": "feat.my-feature",
    "tech_ref": "tech.my-design",
    "execution_mode": "deep"
  }
}
EOF

python -m cli skill impl-spec-test \
  --request request.json \
  --response-out response.json
```

---

## 调试检查清单

### 任何技能失败时检查

- [ ] 输入文件存在且格式正确 (YAML/JSON 语法)
- [ ] 输入契约所有必需字段都存在
- [ ] 禁止的状态/标记不存在
- [ ] 上游 SSOT 对象存在且状态正确
- [ ] `source_refs` 谱系完整
- [ ] 工作区根目录正确
- [ ] 没有文件权限问题

### 执行器阶段失败检查

- [ ] 查看 `execution-evidence.json` 中的错误
- [ ] 检查 `agents/executor.md` 提示是否符合预期
- [ ] 验证输入包所有必需产物存在
- [ ] 尝试带 `--debug` 标志重新运行

### 监督器阶段拒绝检查

- [ ] 查看 `supervision-evidence.json` 中的缺陷列表
- [ ] 检查 `output/semantic-checklist.md` 哪些项未满足
- [ ] 确认执行器输出与上游权威一致
- [ ] 尝试用 `--revision-request` 重新运行

### 冻结守卫失败检查

- [ ] 确认执行证据和监督证据都存在
- [ ] 检查 `freeze-gate.json` 中的具体原因
- [ ] 验证所有语义检查都通过
- [ ] 运行 `validate-package-readiness`

### Gate 评估返回 fail 检查

- [ ] 检查 7 项防偷懒检查都通过
- [ ] 验证 API/E2E 通过率 ≥ 80%
- [ ] 确认所有 `lifecycle_status=passed` 项有 `evidence_status=complete`
- [ ] 确认 E2E 有 ≥1 异常旅程执行
- [ ] 检查 `waiver_status=pending` 项计为失败

---

## 快速流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        完整端到端流                             │
└─────────────────────────────────────────────────────────────────┘

原始需求
   │
   ▼
ll-product-raw-to-src → SRC候选包
   │
   ▼ (Gate)
ll-product-src-to-epic → EPIC冻结包
   │
   ▼ (Gate)
ll-product-epic-to-feat → FEAT冻结包 ──────────────────────────┐
   │                                                            │
   ▼ (可选)                                                     ▼
ll-dev-feat-to-surface-map → Surface Map包              ll-qa-feat-to-apiplan
   │                                                            │
   ▼                                                            ▼
ll-dev-feat-to-tech → TECH设计包 ────────────────┐      ll-qa-api-spec-gen
   │                                              │               │
   ▼                                              │               ▼
ll-dev-tech-to-impl → IMPL候选包                  │      ll-qa-api-manifest-init
   │                                              │               │
   ▼ (Gate)                                       │               ▼
ll-qa-impl-spec-test → Verdict                    │      ll-qa-test-run (API)
   │                                              │               │
   │ (如果 Verdict=pass)                          │               │
   │                                              │               ▼
   ├──────────────────────────────────────────────┘      ll-qa-settlement (API)
   │                                                      │
   │ (并行)                                               │
   ▼                                                      │
ll-dev-feat-to-proto → Prototype包                        │
   │                                                      │
   ▼                                                      │
ll-qa-prototype-to-e2eplan → E2E Test Plan                 │
   │                                                      │
   ▼                                                      │
ll-qa-e2e-spec-gen → E2E Spec                             │
   │                                                      │
   ▼                                                      │
ll-qa-e2e-manifest-init → E2E Manifest                    │
   │                                                      │
   ▼                                                      │
ll-qa-test-run (E2E)                                      │
   │                                                      │
   ▼                                                      │
ll-qa-settlement (E2E)                                    │
   │                                                      │
   ├──────────────────────────────────────────────────────┘
   ▼
ll-qa-gate-evaluate → release_gate_input.yaml
   │
   ▼ (Gate)
ll-gate-human-orchestrator → Decision
   │
   ▼
发布！
```

---

**快速参考卡结束**

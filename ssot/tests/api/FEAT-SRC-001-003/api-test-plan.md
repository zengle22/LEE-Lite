# API Test Plan — FEAT-SRC-001-003

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-001-003 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-001-003__object-layering-and-admission.md`
- Acceptance Checks: 3 条 (AC-01 candidate 与 formal 不能混层, AC-02 consumer 准入必须基于 formal refs, AC-03 业务 skill 不得静默继承 gate authority)

## Capabilities Extracted from FEAT

从 FEAT-SRC-001-003 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| object_layer | verify_separation, detect_layer_mixing |
| consumer_admission | verify_formal_refs, block_path_guessing |
| gate_authority | detect_silent_inheritance, block_unauthorized_approval |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | LAYER-SEPARATION-001 | 对象分层验证 | 验证 candidate 与 formal layer 的权威性分离，禁止 layer ambiguity | P0 |
| 2 | CONSUMER-ADMISSION-001 | Consumer 准入验证 | 确保 consumer 准入基于 formal refs 与 lineage，而非 path guessing | P0 |
| 3 | GATE-AUTHORITY-001 | Gate 权限防护 | 阻止业务 skill 静默充当 gate、approver 或 formal admission authority | P0 |
| 4 | LINEAGE-REF-001 | Lineage 引用验证 | 验证下游消费必须沿 formal refs 与 lineage 进入 | P1 |

## Test Dimension Matrix

| 维度 | 说明 |
|------|------|
| **正常路径** | 合法输入、正确响应、正确副作用 |
| **参数校验** | 必填缺失、类型错误、格式错误、非法枚举、越界值 |
| **边界值** | 最小值/最大值、空集合/空字符串 |
| **状态约束** | 合法状态迁移、非法状态迁移、重复提交 |
| **权限与身份** | 未授权访问、无权限操作 |
| **异常路径** | 资源不存在、冲突、上游依赖失败、业务拒绝 |
| **幂等/重试/并发** | 重复请求、并发提交 |
| **数据副作用** | DB 正确写入、关联对象同步变化 |

## Coverage Cut Records

| Capability | Dimension | Cut Reason | Source Ref |
|------------|-----------|------------|------------|
| LAYER-SEPARATION-001 | 边界值 | 分层判定为离散规则，无连续边界 | ADR-047 Section 4.1.3 |
| CONSUMER-ADMISSION-001 | 边界值 | 准入验证为二元判定，无边界概念 | ADR-047 Section 4.1.3 |
| GATE-AUTHORITY-001 | 边界值 | 权限防护为离散规则，无边界概念 | ADR-047 Section 4.1.3 |
| LINEAGE-REF-001 | 状态约束 | P1 能力，状态约束裁剪 | ADR-047 Section 4.1.3 |
| LINEAGE-REF-001 | 权限与身份 | 试点阶段无鉴权层 | ADR-047 Section 4.1.3 |
| LINEAGE-REF-001 | 幂等/重试/并发 | P1 能力，并发场景裁剪 | ADR-047 Section 4.1.3 |
| LINEAGE-REF-001 | 边界值 | 引用验证为离散检查 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | LAYER-SEPARATION-001, CONSUMER-ADMISSION-001, GATE-AUTHORITY-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | LINEAGE-REF-001 | 正常路径, 参数校验 (key), 异常路径 (key) |

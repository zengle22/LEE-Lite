# API Test Plan — FEAT-SRC-003-008

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-008 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-008__governed-skill-接入与-pilot-验证流.md`
- Acceptance Checks: 3 条 (Onboarding scope explicit, Real pilot chain required, Adoption scope limited)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-008 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| onboarding | define_scope, define_migration_waves, define_cutover_fallback |
| pilot_chain | execute_pilot, verify_full_chain, collect_evidence |
| adoption | generate_integration_matrix, make_cutover_decision |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | ONBOARD-SCOPE-001 | 定义接入范围 | 定义 governed skill 的 onboarding scope 和 migration waves | P0 |
| 2 | CUTOVER-DEFINE-001 | 定义 Cutover/Fallback | 定义围绕 runner 自动推进结果的 cutover 和 fallback 规则 | P0 |
| 3 | PILOT-EXEC-001 | 执行 Pilot 链 | 执行 producer -> consumer -> audit -> gate 真实链路 | P0 |
| 4 | PILOT-VERIFY-001 | 验证 Pilot 结果 | 验证 pilot 链覆盖真实协作而非组件级测试 | P0 |
| 5 | EVIDENCE-BIND-001 | 绑定 Pilot Evidence | 将 pilot evidence 绑定到真实 approve -> runner -> next skill 链路 | P0 |
| 6 | ADOPTION-MATRIX-001 | 生成集成矩阵 | 生成 adoption integration matrix 供业务方使用 | P1 |
| 7 | SCOPE-REJECT-001 | 越界接入拒绝 | 拒绝超出 governed skill 范围的 warehouse-wide 治理扩展 | P1 |

## Test Dimension Matrix

每个 capability 按以下维度评估覆盖范围：

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
| ADOPTION-MATRIX-001 | 边界值 | 集成矩阵生成为格式化验证，无连续边界 | ADR-047 Section 4.1.3 |
| ADOPTION-MATRIX-001 | 幂等/重试/并发 | 矩阵生成为只读计算，无并发副作用 | ADR-047 Section 4.1.3 |
| SCOPE-REJECT-001 | 边界值 | 范围拒绝为离散判断，无连续边界 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | ONBOARD-SCOPE-001, CUTOVER-DEFINE-001, PILOT-EXEC-001, PILOT-VERIFY-001, EVIDENCE-BIND-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | ADOPTION-MATRIX-001, SCOPE-REJECT-001 | 正常路径, 参数校验 (key), 异常路径 (key) |

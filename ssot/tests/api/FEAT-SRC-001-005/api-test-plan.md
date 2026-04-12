# API Test Plan — FEAT-SRC-001-005

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-001-005 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 dual-chain pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-001-005__governed-skill-adoption-and-cross-skill-e2e.md`
- Acceptance Checks: 3 条 (AC-01 onboarding 范围与迁移波次必须明确, AC-02 至少要有一条真实 pilot 主链, AC-03 adoption 不得膨胀成仓库级治理)

## Capabilities Extracted from FEAT

从 FEAT-SRC-001-005 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| skill_onboarding | register_skill, validate_onboarding_matrix |
| migration_management | define_wave, execute_cutover, execute_fallback |
| e2e_pilot | execute_pilot_chain, generate_e2e_evidence |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | SKILL-ONBOARD-001 | 技能接入验证 | 验证 governed skill 的 onboarding 边界、接入矩阵与分批纳入规则 | P0 |
| 2 | MIGRATION-CUTOVER-001 | 迁移切换控制 | 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界 | P0 |
| 3 | E2E-PILOT-001 | 跨 skill E2E 闭环 | 验证至少一条真实 producer -> consumer -> audit -> gate pilot 主链 | P0 |
| 4 | SCOPE-GUARD-001 | 作用域防护 | 阻止 adoption 膨胀成仓库级全局文件治理改造 | P1 |

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
| SKILL-ONBOARD-001 | 边界值 | 接入矩阵为离散技能列表，无连续边界 | ADR-047 Section 4.1.3 |
| MIGRATION-CUTOVER-001 | 边界值 | 迁移波次为离散阶段，无连续边界 | ADR-047 Section 4.1.3 |
| E2E-PILOT-001 | 边界值 | Pilot 链为离散步骤组合，无连续边界 | ADR-047 Section 4.1.3 |
| SCOPE-GUARD-001 | 状态约束 | P1 能力，状态约束裁剪 | ADR-047 Section 4.1.3 |
| SCOPE-GUARD-001 | 权限与身份 | 试点阶段无鉴权层 | ADR-047 Section 4.1.3 |
| SCOPE-GUARD-001 | 幂等/重试/并发 | P1 能力，并发场景裁剪 | ADR-047 Section 4.1.3 |
| SCOPE-GUARD-001 | 边界值 | 作用域防护为离散规则检查 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | SKILL-ONBOARD-001, MIGRATION-CUTOVER-001, E2E-PILOT-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 数据副作用 |
| P1 | SCOPE-GUARD-001 | 正常路径, 参数校验 (key), 异常路径 (key) |

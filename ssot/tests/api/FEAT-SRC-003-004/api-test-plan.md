# API Test Plan — FEAT-SRC-003-004

## Plan Metadata

| 字段 | 值 |
|------|-----|
| feature_id | FEAT-SRC-003-004 |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution |
| anchor_type | feat |

## Source References

- `ssot/feat/FEAT-SRC-003-004__execution-runner-自动取件流.md`
- Acceptance Checks: 3 条 (Auto-consume ready queue, Single-owner claim, Authoritative intake)

## Capabilities Extracted from FEAT

从 FEAT-SRC-003-004 的 Goal / Scope / Constraints / Acceptance Checks 中提取以下 API capabilities：

### API Objects

| Object | Capabilities |
|--------|-------------|
| ready_queue | scan, auto_consume |
| job_claim | claim_single_owner, transfer_ownership |
| runner_state | record_ownership, record_claim_evidence |

### Capability Detail

| # | Capability ID | Name | Description | Priority |
|---|--------------|------|-------------|----------|
| 1 | SCAN-QUEUE-001 | 扫描 Ready Queue | runner 自动扫描 `artifacts/jobs/ready` 中的待取件 job | P0 |
| 2 | CLAIM-JOB-001 | 抢占式 Claim Job | 对 ready job 进行 single-owner claim，确保仅一个 runner 成功 | P0 |
| 3 | OWNERSHIP-001 | 记录 Owner 状态 | 将 job 从 ready 转移到 running，记录 runner ownership | P0 |
| 4 | ANTI-REENTRY-001 | 防重入保护 | 防止同一 job 被多个 runner 同时 claim | P0 |
| 5 | LINEAGE-RECORD-001 | 记录 Claim Lineage | 保存 claim 证据、job lineage 和 ownership 转移记录 | P1 |

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
| LINEAGE-RECORD-001 | 边界值 | Lineage 记录为元数据追加，无连续边界 | ADR-047 Section 4.1.3 |
| LINEAGE-RECORD-001 | 状态约束 | 记录为只读追加操作，无状态机约束 | ADR-047 Section 4.1.3 |
| SCAN-QUEUE-001 | 边界值 | 空队列为正常边界，无需额外边界测试 | ADR-047 Section 4.1.3 |

## Test Priority Matrix

| Priority | Capabilities | Required Dimensions |
|----------|-------------|---------------------|
| P0 | SCAN-QUEUE-001, CLAIM-JOB-001, OWNERSHIP-001, ANTI-REENTRY-001 | 正常路径, 参数校验 (key), 状态约束, 异常路径 (key), 幂等/重试/并发, 数据副作用 |
| P1 | LINEAGE-RECORD-001 | 正常路径, 参数校验 (key), 异常路径 (key) |

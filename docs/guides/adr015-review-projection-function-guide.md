# ADR015 Gate Review Projection 功能说明

> 文档定位：说明文档 / 使用指南
>
> 管理方式：不属于 SSOT，不进入下游治理继承链
>
> 对应来源：`ADR-015 Machine SSOT + Human Review Projection`

## 1. 这是什么功能

这不是一个终端用户业务功能，也不是新的治理 runtime 平台。

它是一组专门服务 `gate review` 的审核辅助能力，目标是：

- 让 `Machine SSOT` 继续保持机器优先、结构稳定、可继承、可冻结
- 在进入 `gate` 审核时，从 `Machine SSOT` 自动派生一份给人看的 `Human Review Projection`
- 让 reviewer 在 Projection 上理解产品、判断问题、提出修订意见
- 但最终修改和冻结仍然回到 `Machine SSOT`

一句话概括：

> `SSOT` 负责执行与冻结，`Projection` 负责理解与审核；人可以在 `Projection` 上提意见，但最终权威修改永远回到 `SSOT`。

## 2. 它不是什么

这套能力明确不做下面这些事：

- 不把 `Projection` 变成新的真相源
- 不让下游直接继承 `Projection`
- 不定义 `handoff orchestration`
- 不定义 `formal publication`
- 不定义 `governed IO` 平台
- 不定义 `skill onboarding` runtime
- 不要求把 `Machine SSOT` 重写成人类友好的 narrative 正文

## 3. 功能拆分

当前功能被拆成 4 个互相配合的能力切片。

### 3.1 Human Review Projection 生成

作用：

- 从 `Machine SSOT` 渲染一份 reviewer 可读的审核视图
- 输出固定模板块，例如：
  - `Product Summary`
  - `Roles`
  - `Main Flow`
  - `Key Deliverables`
- 给视图打上：
  - `derived-only`
  - `non-authoritative`
  - `non-inheritable`

对应冻结实现：

- [TECH 001](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-tech/adr015-machine-ssot-human-review-projection-20260325-r3d-tech-001/tech-spec.md)

### 3.2 Authoritative Snapshot 生成

作用：

- 从 `Machine SSOT` 中提取 reviewer 必须看到的硬约束
- 避免 reviewer 只看 narrative，不看 authoritative boundary

固定抽取字段：

- `completed_state`
- `authoritative_output`
- `frozen_downstream_boundary`
- `open_technical_decisions`

对应冻结实现：

- [TECH 002](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-tech/adr015-machine-ssot-human-review-projection-20260325-r3d-tech-002/tech-spec.md)

### 3.3 Review Focus / Risks / Ambiguities

作用：

- 自动告诉 reviewer 这一轮最值得盯的点
- 自动提示风险和歧义，而不是让 reviewer 自己从字段里拼判断

典型提示内容：

- 产品形态是否清楚
- 边界是否遗漏
- 异常流是否缺失
- authoritative deliverable 是否唯一
- 术语是否重叠或含糊

对应冻结实现：

- [TECH 003](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-tech/adr015-machine-ssot-human-review-projection-20260325-r3d-tech-003/tech-spec.md)

### 3.4 Projection 批注回写

作用：

- reviewer 的意见不能只停在 Projection 上
- 所有修订都必须回写成 `Machine SSOT` 的修订请求
- `SSOT` 更新后，再重生成新 Projection

对应冻结实现：

- [TECH 004](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-tech/adr015-machine-ssot-human-review-projection-20260325-r3d-tech-004/tech-spec.md)

## 4. 整体实现逻辑

实现上是一个“只读派生面 + 回写闭环”。

### 4.1 渲染链路

1. 读取 freeze-ready 的 `Machine SSOT`
2. 渲染 `Human Review Projection`
3. 提取 `Authoritative Snapshot`
4. 生成 `Review Focus / Risks / Ambiguities`
5. 输出给 reviewer

### 4.2 回写链路

1. reviewer 基于 Projection 提 comment
2. 系统把 comment 映射回 SSOT field / boundary
3. 生成 `revision request`
4. 更新 `Machine SSOT`
5. 基于新 SSOT 重生成 Projection

可以用下面这条主线理解：

```text
Machine SSOT
  -> Projection Renderer
  -> Snapshot Extractor
  -> Focus/Risk Analyzer
  -> Gate Reviewer
  -> Comment Mapper
  -> SSOT Revision Request
  -> Machine SSOT Updated
  -> Projection Regenerated
```

## 5. 核心运行时模块

当前冻结设计里的实现模块是：

### Projection 生成

- `review_projection/template.py`
- `review_projection/renderer.py`
- `review_projection/markers.py`

职责：

- 选择模板
- 渲染 Projection
- 打 marker 和 trace refs

### Snapshot 生成

- `review_projection/field_selector.py`
- `review_projection/snapshot.py`
- `review_projection/traceability.py`

职责：

- 选出 authoritative fields
- 压缩成 Snapshot
- 绑定回 SSOT trace

### Focus / Risk 分析

- `review_projection/focus.py`
- `review_projection/risk_analyzer.py`
- `review_projection/prompt_blocks.py`

职责：

- 提取 reviewer 应优先关注的问题
- 生成风险与歧义提示
- 把提示插入 Projection

### Writeback 闭环

- `review_projection/writeback.py`
- `review_projection/revision_request.py`
- `review_projection/regeneration.py`

职责：

- comment 映射回 SSOT
- 生成修订请求
- 触发 Projection 重生成

## 6. 关键接口

当前冻结的主要对象接口如下。

### 6.1 Projection 渲染

- `ProjectionRenderRequest`
- `ProjectionRenderResult`

输入：

- `ssot_ref`
- `template_version`
- `review_stage`

输出：

- `projection_ref`
- `derived_markers`
- `trace_refs`
- `review_blocks`

### 6.2 Snapshot 提取

- `SnapshotExtractionRequest`
- `AuthoritativeSnapshot`

输入：

- `ssot_ref`
- `projection_ref`

输出：

- `snapshot_ref`
- `completed_state`
- `authoritative_output`
- `frozen_downstream_boundary`
- `open_technical_decisions`

### 6.3 Focus / Risk 分析

- `ReviewFocusRequest`
- `RiskSignal`

输入：

- `ssot_ref`
- `projection_ref`

输出：

- `focus_items`
- `risk_items`
- `ambiguity_items`
- `source_trace_refs`

### 6.4 Comment 回写

- `ProjectionComment`
- `ProjectionRegenerationRequest`

输入：

- `projection_ref`
- `comment_ref`
- `comment_text`
- `comment_author`

输出：

- `mapped_field_refs`
- `revision_request_ref`
- `regenerated_projection_ref`

## 7. 状态模型

### Projection 生成状态

```text
ssot_ready
  -> projection_requested
  -> projection_rendered
  -> review_visible
```

约束：

- `projection_rendered` 必须保留 `derived_only_marked`
- `projection_rendered` 必须保留 `traceable_to_ssot`

### Snapshot 状态

```text
projection_rendered
  -> snapshot_extracted
  -> snapshot_attached
  -> constraint_check_visible
```

### Focus / Risk 状态

```text
projection_rendered
  -> focus_extracted
  -> risk_flags_attached
  -> review_guidance_visible
```

### Writeback 状态

```text
review_comment_captured
  -> writeback_mapped
  -> ssot_revision_requested
  -> ssot_updated
  -> projection_regenerated
```

失败分支：

```text
writeback_mapped(fail)
  -> comment_mapping_pending
```

## 8. 如何使用

### 8.1 对系统调用方

标准调用顺序如下：

1. 确认 `Machine SSOT` 已 freeze-ready
2. 调 `Projection renderer`
3. 调 `Snapshot extractor`
4. 调 `Focus/Risk analyzer`
5. 把完整 Projection 提供给 reviewer
6. 如果 reviewer 有意见，提交 `ProjectionComment`
7. 走 writeback，更新 `Machine SSOT`
8. 重新生成 Projection

### 8.2 对 reviewer

标准审核顺序如下：

1. 先看 `Projection`
2. 再看 `Authoritative Snapshot`
3. 再看 `Review Focus / Risks / Ambiguities`
4. 如果有问题，提 comment，不直接改 Projection
5. 等 SSOT 更新后，看新生成的 Projection

### 8.3 对下游系统

下游只允许：

- 继续继承 `Machine SSOT`

下游不允许：

- 把 `Projection` 当 authoritative input
- 直接继承 `Projection`
- 直接 patch `Projection`

## 9. 用户故事

### 9.1 reviewer 视角

- 作为 reviewer，我希望看到一份从 SSOT 自动生成的人类友好 Projection，这样我不需要自己拼产品主线。
- 作为 reviewer，我希望看到一块短小但硬的 `Authoritative Snapshot`，这样我不会漏掉 completed state 和 frozen boundary。
- 作为 reviewer，我希望系统直接告诉我这轮该重点看什么，这样我能把注意力放在真正要判断的问题上。

### 9.2 SSOT owner 视角

- 作为 SSOT owner，我希望 reviewer 的意见最终回到 SSOT，而不是停在 Projection 上，这样系统始终只有一个真相源。

### 9.3 下游消费者视角

- 作为下游消费者，我希望继续只依赖 Machine SSOT，而不是处理另一份 narrative 文档，这样继承边界始终稳定。

## 10. 失败处理原则

### Projection 渲染失败

- 如果模板缺失，返回 `template_missing`
- 不允许自由发挥 narrative 补全

### Snapshot 提取失败

- 如果 authoritative field 缺失，返回 `authoritative_field_missing`
- 必须显式提示字段不足
- 不允许 silent omission

### Risk 信号不可追溯

- 丢弃该 signal
- 不允许把不可回链提示写进最终 Projection

### Comment 映射失败

- 标记 `comment_mapping_pending`
- 不允许直接编辑 Projection

### Projection 重生成失败

- 保留 `revision_request` 完成态
- 标记 `projection_regeneration_pending`
- 阻止旧 Projection 继续充当当前审核视图

## 11. 当前实现形态

当前仓库中，这套能力已经冻结到了：

- `TECH`
- `TESTSET candidate`
- `IMPL candidate`

对应目录：

- [feat-to-tech artifacts](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-tech)
- [feat-to-testset artifacts](/E:/ai/LEE-Lite-skill-first/artifacts/feat-to-testset)
- [tech-to-impl artifacts](/E:/ai/LEE-Lite-skill-first/artifacts/tech-to-impl)

当前实现形态是后端 / runtime 侧能力，不是页面功能。

代表性实现候选：

- [IMPL 003 impl-bundle.md](/E:/ai/LEE-Lite-skill-first/artifacts/tech-to-impl/adr015-machine-ssot-human-review-projection-20260325-r3d-impl-003/impl-bundle.md)

从当前 `IMPL` 看：

- `frontend_required: False`
- `backend_required: True`
- `migration_required: False`

也就是说，这套能力当前被当成一组审核投影视图 runtime 能力来实现。

## 12. 读者结论

如果只记住一件事，应当记住这句：

> `Projection` 是给人看的审核视图，不是新的真相源；真正会被修改、冻结、继承的仍然只有 `Machine SSOT`。

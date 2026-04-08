# ADR-045：引入 FRZ 冻结层与全链 Pre-SSOT 集成方案

* 状态：Draft
* 日期：2026-04-08
* 决策者：TBD
* 适用范围：`product.raw-to-src`（pre-ssot 冻结）、`ssot/` 主链（SRC/EPIC/FEAT…）、`skills/` governed workflows、`artifacts/`（trace/lineage/registry）、external gate 评审与 materialization
* 相关 ADR：ADR-002、ADR-008、ADR-019、ADR-022、ADR-043、ADR-044

---

# 1. 背景

当前 SSOT 主链为：

```text
raw → src → epic → feat → tech/ui/testset → impl
```

在真实工程运行中，已经出现并会持续出现以下结构性问题：

1. SSOT 层文档结构完整，但关键语义缺口（边界、状态机、规则、验收口径、主闭环）导致下游“猜意图”。
2. 关键设计信息长期散落在 PRD/原型/架构讨论/口头沟通/即时聊天中，未进入可继承链路，后续不可复用且不可审计。
3. 下游静默补义（尤其在 tech/ui/testset/impl）会在缺口处产生不一致语义，最终表现为 API 口径不一致、状态机分叉、验收漂移、UI 行为不统一。
4. 以“摘要压缩”方式做 freeze 时容易丢失决策依据、边界信息和未决项（known unknowns），导致下游误把“未定义”当“可自由补全”。
5. 单层继承模型（仅看直接上游）不足以抵抗缺口：缺口处不是补证据，而是补新真相，漂移不可避免。

仓库已有 ADR-019/022 让 `raw-to-src` 具备高保真与 facet 化能力，但仍缺少一个可治理、可审计、可作为真相锚点的 **pre-ssot 冻结层**，用于把“产品是什么”的不可漂移语义先冻结下来。

---

# 2. 决策

## 2.1 引入 FRZ（Freeze Package）层

将链路升级为：

```text
raw → frz → src → epic → feat → tech/ui/testset → impl
```

FRZ 的定义：

> FRZ 是面向 SSOT 的语义冻结包（Semantic Freeze Package），冻结“不可漂移的高阶真相”，并提供证据回溯、未决项挂牌与补义权限边界。

FRZ 的定位边界：

1. FRZ 不是 ADR：ADR 记录“决策点”，FRZ 冻结“任务级整体语义”。ADR 是 FRZ 的输入来源之一。
2. FRZ 不是 SRC：SRC 是面向下游拆解与派生的标准源规格；FRZ 是更高保真、带证据与未决项的冻结层，作为 SRC 的上游锚点。
3. FRZ 不进入 `ssot/` 主链：FRZ 作为 governed artifact 存放在 `artifacts/`，通过 manifest/registry 被引用与审计。

## 2.2 Pre-SSOT 与 SSOT 内补全边界

Pre-SSOT（FRZ 前/FRZ 内必须确定）原则：

> 决定“产品是什么”的内容必须前置冻结。

至少包括：

* 产品边界（in/out scope）
* 核心闭环与关键流程（core journeys）
* 领域模型最小骨架（core entities/relations）
* 主状态机（states/transitions/guards）
* 验收口径（success/failure definition）

SSOT 内允许 AI 补全的内容原则：

> 只允许补“派生性设计”，禁止改“方向性真相”。

允许项示例：

* epic/feat 拆解与组织
* 技术细化（模块/接口/数据结构）
* schema 展开与 UI 文案/状态细化
* 测试用例与实现任务拆分

禁止项（必须回写 FRZ）：

* 新业务规则或核心规则变更
* 核心对象定义变化
* 主状态机变化
* 主闭环流程变化
* UI 主交互模式变化
* 验收口径变化

## 2.3 FRZ 冻结最小集合约束（MSC）

为避免 FRZ 过轻或过胖，引入硬约束：

> FRZ 必须满足 Minimum Semantic Completeness（MSC）。

若以下任一维度缺失，则 FRZ 不得进入可冻结状态（frozen/freeze-ready）：

1. `product_boundary`
2. `core_journeys`
3. `domain_model`
4. `state_machine`
5. `acceptance_contract`

MSC 的作用：

* 把“建议性冻结”升级为“可校验冻结”
* 让下游缺口不再被静默补义，而是阻断或回写

## 2.4 FRZ → SRC 投影不变性（Projection Invariance）

定义 FRZ 与 SRC 的关系为：

* FRZ 负责冻结 canonical truth（锚点）
* SRC 负责组织、展开、细化（投影）

规则：FRZ → SRC 投影必须满足语义不变性。

SRC 不得：

* 重命名 FRZ 中的 canonical entities / states / terms
* 改变 state machine 的结构语义
* 改写 acceptance contract 的判定逻辑

SRC 仅允许：

* 结构重排（re-organization）
* 维度展开（decomposition）
* 表达细化（refinement）

所有投影必须具备 trace：

```text
src_element → frz_anchor_id
```

一句话：

> SRC 可以“展开”，不能“改口径”。

## 2.5 语义锚点（Anchor ID）

FRZ 内所有冻结对象必须具备稳定锚点 ID，以支持：

* 下游引用（`derived_from: SM-001`）
* reconcile 精准对齐
* drift 检查可自动化

锚点最小规范：

* 领域实体：`ENT-xxx`
* 状态机：`SM-xxx`
* 冻结规则/合同：`FC-xxx`（或保留已有 ID）
* 未决项：`UNK-xxx`
* 枚举冻结：`ENUM-xxx`

## 2.6 语义来源标注（inherited / derived / proposed）与 proposed 过期机制

所有下游新增语义必须标记来源：

* `inherited`：来自 FRZ 或直接上游冻结真相（不可改）
* `derived`：从上游逻辑推导（可补但不可越界）
* `proposed`：无上游依据，仅为建议（必须回上游确认）

禁止：

* 将 `proposed` 伪装为 `inherited`

为避免 proposed 永久挂账，引入过期机制：

* `proposed`/`known_unknowns` 必须带 `expires_in`（默认 2 cycles）与 `owner`
* 到期未清算的项不得继续被下游当作稳定输入

## 2.7 多层回溯继承（单层主继承 + 多层只读回溯）

核心原则：

> 当前层以直接上游为主输入；允许多层只读回溯用于补证据与校准，但禁止跳层造义。

上溯优先级：

```text
feat → epic → src → frz → evidence → raw
```

规则：

* 允许：补证据、校准语义、校验边界、识别缺口
* 禁止：跳过中间层重构语义、把 evidence 当 frozen truth、直接引入新主语义

## 2.8 FRZ 瘦身原则（写死一句话）

> FRZ 不是信息收集层，而是语义约束层；未被 downstream 使用或不会影响多层决策的内容，不应进入 FRZ。

---

# 3. 机制（落在仓库实现面）

## 3.1 FRZ 如何产生（raw-to-src 中间产物）

FRZ 作为 `product.raw-to-src` 的 pre-ssot 产物生成：

* 输出目录：`artifacts/raw-to-src/<run_id>/frz-package/`
* 文件最小集：
  * `index.md`
  * `freeze.yaml`
  * `evidence.yaml`
  * `frz-package.json`
* 并写入引用：
  * `package-manifest.json.frz_package_ref`
  * `package-manifest.json.frz_registry_record_ref`
  * `result-summary.json.frz_package_ref`

FRZ 的管理方式：

* 归档在 `artifacts/`（与 evidence/manifest 同级治理）
* 可通过 artifact registry 追溯（同等审计强度）
* 不污染 `ssot/` 主链，但可以作为下游 workflow 的只读输入锚点

## 3.2 Skill 使用者旅程（透明性）

本 ADR 中的“用户旅程”指 **skill 使用者** 使用新版 `raw-to-src` 的操作路径。

默认行为：

* 使用者仍然只需要运行 `raw-to-src`（命令不变）
* FRZ 在运行中自动生成并提交 registry
* 使用者不需要显式创建 FRZ，也不需要理解 FRZ 的内部结构即可继续下游流程

可选行为（当需要追溯/复核）：

* 通过 `result-summary.json.frz_package_ref` 或 `package-manifest.json.frz_package_ref` 定位 FRZ
* 通过 FRZ anchor id 在下游工件中引用或对齐（projection trace / reconcile）

## 3.3 Semantic Preservation Check（拆解前检查）

每次进入下游拆解前，必须完成：

1. 术语是否有定义：无定义禁止使用
2. 新语义是否有上游依据：无依据只能标 `proposed`
3. 空白是否标 unknown：未标 unknown 视为风险缺口
4. 是否有 evidence 引用：无引用不可追溯

## 3.4 与 ADR-044（缺口回流）的关系

当下游发现 MSC 维度缺口、主状态机缺口、验收口径缺口时：

* 允许临时阻断下游 freeze/dispatch
* 必须触发 reconcile/backport，把长期定义回写到 FRZ/SSOT 真相域

---

# 4. 结果（Consequences）

正面影响：

* 专家知识与讨论成果进入可继承链路
* 下游补全行为被明确约束，语义漂移显著下降
* 语义从“可生成”转为“可控制、可审计、可回溯”
* 自动化 validator/gate 有了可校验的锚点（MSC + anchor ids）

成本：

* 新增 FRZ 产物类型、schema 与校验
* 增加 FRZ → SRC trace 与不变性约束的工程维护成本
* 对 author/reviewer 需要训练来源标注与回写流程

主要风险与应对：

* FRZ 变胖：用 MSC + 瘦身原则 + downstream 使用驱动约束
* FRZ 丢信息：强制 evidence/known_unknowns
* 下游越权补义：来源标注 + proposed 过期 + reconcile 回写门禁
* 跳层破坏：单层主继承 + 多层只读回溯写死规则

---

# 5. 后续行动（Next Steps）

1. 在下游 workflow（`src-to-epic` 起）引入对 `frz_package_ref` 的消费与投影 trace 校验。
2. 把 FRZ anchor ids 作为 reconcile/backport 的最小引用单元（对齐 ADR-044）。
3. 为 `proposed` 与 `known_unknowns` 引入周期性清算（过期阻断或自动升级为 spec_gap）。
4. 在外部 gate/validator 中补充 Projection Invariance 检查（重命名/状态机改口径/验收口径改写）。
5. 为 FRZ freeze.yaml 补齐严格 JSON schema（可静态校验）。


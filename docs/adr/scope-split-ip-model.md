<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# IP 双 Scope 分离模型

> **修订沿革**:本规范 2026-08-26 首版;2026-08-29 随 `schemas/` 转 CC0 1.0 修订;2026-10-23 修订(对齐 `_meta` v1.0 的 `metadata.license` 枚举、补 `knowledge` 双形态的内容 IP 归属、补第三方来源材料义务)。历史版本见 git 记录。

## 是什么

evorule 生态的知识产权分为两个 **互不传染** 的 scope,**格式约束**与**法律权利**是两条独立维度:

| Scope | 资产 | 协议 | 谁决定 |
|---|---|---|---|
| **Scope A** — evorule 框架 IP | **规范层**:本仓 `schemas/` 全部 JSON Schema;主仓 `evorule-tcb/core_eval.json`。**实现层**:本仓 `tools/` / `docs/` / ADR / 示例;主仓 `evorule-tcb` / `evorule-reactor` / `evorule-governance` / `evorule-cli` 等代码 | 分层:规范层 **CC0 1.0 公共领域**;实现层 **AGPL-3.0-or-later + 商业双模式** | EvoRule 团队 |
| **Scope B** — 项目方内容 IP | 项目方用本仓 schema 创作的所有 system JSON(`rule_set` / `agent_def` / `workflow_dag` / `service_registry` / `knowledge` / `migration`) | **项目方自选**(通过 `metadata.license` 字段) | 项目方本人 |

**关键规则**:

1. **格式层**:所有 evorule 生态的 system JSON 必须符合本仓 schema 定义的字段结构(5 顶层字段 + kind-specific body + 类型/必填/格式约束)。
2. **法律层**:项目方对其创作的 system JSON 拥有完整 IP 所有权,evorule 不主张、不传染、不要求署名/回馈/分润。
3. **AGPL-3.0 的 copyleft 范围**:仅附着在 Scope A **实现层**资产本身;Scope A 资产**不**对项目方创作的 Scope B 内容施加传染效力。规范层为 CC0,本身无传染力。
4. **项目方声明机制**:每个 system JSON 通过 `metadata.license` 字段声明其内容协议。合法枚举以 `_meta` v1.0 为准,共 9 值:`AGPL-3.0-or-later` / `AGPL-3.0` / `Apache-2.0` / `MIT` / `BSD-3-Clause` / `CC0-1.0` / `CC0-1.0 Universal (Public Domain)` / `Proprietary` / `Custom`。
5. **数据资产形态的 IP 归属**:`knowledge` 有两种条目形态——文档条目(`content`)与数据资产条目(`payload` + `schema_ref`)——其内容 IP **都归数据作者**。`schema_ref` 指向的领域 JSON Schema 归**领域仓**所有,本仓只定义引用契约(代管不代持);入库校验方按 `schema_ref` 取 schema 强校验 `payload`,resolver 未命中即拒绝。
6. **上游义务不在 Scope 分离中免除**:Scope 分离划的是 evorule 与项目方之间的界,**不**处理项目方与第三方之间的许可义务。Scope B 内容中引入的第三方材料,其许可义务由引入方承担;evorule 不主张 IP **不等于**免除上游许可义务。来源分级、事实与表达分离、上架门与 copyleft 边界的具体规则见 [LEGAL_NOTES.md §5](../../LEGAL_NOTES.md#5-第三方来源材料义务)。

**与"治理"措辞的关系**:README 中"所有 evorule 生态的系统 JSON 必须由 evorule-system-rules 治理"中的"治理"专指**格式层面**(必须符合 schema 字段结构),**不**指**法律层面**(许可证、所有权、商业权利)。两者在本规范中**显式分离**。

## 为什么

- **消除项目方顾虑**:企业项目方最常见的疑虑是"用了 evorule,我的内容会被 AGPL 锁死"。本规范把"框架归 evorule,内容归项目方"明文化,降低销售阻力。
- **支持商业项目方闭源 SaaS**:`metadata.license` 的 `Proprietary` / `Custom` 选项是给"完全闭源/完全自有"准备的,商业项目方可以买 evorule 商业许可覆盖 Scope A 框架,Scope B 内容仍归项目方所有且可任意处置。
- **鼓励生态扩张**:第三方做"兼容 evorule 的工具/平台"时,清楚知道他们读 schema 写的工具受 AGPL 约束,但工具处理的项目方内容**不受** AGPL 约束,不必担心传染。schema 自身以 CC0 奉献,更使这条路径上没有额外的许可阻力。
- **规范层与实现层分离**:格式规范应当自由被实现(HTTP 规范 vs 服务器的同一思路),实现代码才受 copyleft 保护。治理权威来自治理模型与流程约束,不来自许可证限制——这使"受 evorule-system-rules 治理"可以专注于格式,而不是许可。
- **与 evorule 商业模型一致**:evorule 通过"卖框架许可"(Scope A 商业许可)创收,而不是"控制项目方内容"——这与"JSON 是一等公民"(`DESIGN_PHILOSOPHY.md §1`)的透明/可审计/数据导向精神一致。
- **避免法律歧义**:AGPL-3.0 是强 copyleft,但其效力有明确边界(对 licensed work 本身,不自动传染 downstream creations)。本规范把这条边界显式说清,减少后续争议。

## 怎么用

- 本规范主文档:[README.md §项目方内容归属](../../README.md#项目方内容归属scope-b)
- 本仓特定补充声明:[LEGAL_NOTES.md](../../LEGAL_NOTES.md)
- 第三方来源材料的引入规则:[LEGAL_NOTES.md §5 第三方来源材料义务](../../LEGAL_NOTES.md#5-第三方来源材料义务)
- 设计规范总览:[README.md](./README.md)
- 字段细节:`metadata.license` 字段定义见 [../reference/schema-reference.md](../reference/schema-reference.md)(该参考页当前以 `v0.9` 为基线);**当前固化版的合法枚举以 [`schemas/_meta/v1.0.json`](../../schemas/_meta/v1.0.json) 为准**(9 值)
- 机器可读层:每个 schema 文件在顶层声明 `x_legal_authority_notice` 字段,任何读 schema 的工具都能获取本规范的元信息
- 项目方如何声明自己内容的协议:[../tutorial/02-write-first-system-json.md](../tutorial/02-write-first-system-json.md) 中的 `metadata.license` 字段示例

## 不接受的替代方案

- **强制所有 evorule 系统 JSON 走 AGPL**:会阻挡企业项目方(他们最在意自己内容的 IP 不被传染),与 evorule 商业模型冲突。schema 的 `metadata.license` 字段明确允许 `Proprietary` / `Custom`,即排斥此方案。
- **不区分 Scope A / Scope B,含糊统称"受 evorule-system-rules 治理"**:读者会把"治理"读成"许可证主张",产生误解。本规范的核心动作就是把"格式治理"和"法律治理"显式拆开。
- **让 schemas 留在 AGPL-3.0-or-later + 商业双模式**(本规范 2026-08-26 的原立场):已于 2026-08-29 被否决并实际改为 **CC0 1.0 公共领域**。schema 是"格式规范"而非"引擎自身读取的解释器规范",第三方应当零法律负担地实现校验器、IDE 插件与代码生成器;规范层 CC0 / 实现层 AGPL 的分层与 `core_eval.json` 先例衔接,改判后的完整理由见 [LEGAL_NOTES.md](../../LEGAL_NOTES.md)。
- **把"evorule 不主张 Scope B 的 IP"读成"Scope B 的材料天然没有义务"**:Scope 分离只划 evorule 与项目方的界,不替代项目方对第三方材料承担的许可义务。判据集与技能包若从外部来源引入材料,必须按来源逐项标注与隔离,见关键规则 6。

## 引用

- [README.md §许可](../../README.md#许可) — Scope A 协议入口
- [README.md §项目方内容归属(Scope B)](../../README.md#项目方内容归属scope-b) — Scope B 协议入口
- [LEGAL_NOTES.md](../../LEGAL_NOTES.md) — 本仓特定法律声明
- [schemas/LICENSE-SCHEMAS.md](../../schemas/LICENSE-SCHEMAS.md) — schemas 的 CC0 1.0 奉献全文
- [../reference/schema-reference.md](../reference/schema-reference.md) — `metadata.license` 字段定义
- `DESIGN_PHILOSOPHY.md §1 JSON 是一等公民` — 透明/可审计/数据导向的底层立场
- `evorule-tcb/core_eval.json` `metadata.public_domain_notice` — CC0 范围的现有先例

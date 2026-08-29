<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# IP 双 Scope 分离模型

## 是什么

evorule 生态的知识产权分为两个 **互不传染** 的 scope,**格式约束**与**法律权利**是两条独立维度:

| Scope | 资产 | 协议 | 谁决定 |
|---|---|---|---|
| **Scope A** — evorule 框架 IP | 本仓的 `schemas/` / `tools/` / `docs/` / ADR;主仓的 `evorule-tcb` / `evorule-reactor` / `evorule-governance` / `evorule-cli` 等代码;以及 `evorule-tcb/core_eval.json`(后者为 CC0 1.0 公共领域) | AGPL-3.0-or-later + 商业双模式 | EvoRule 团队 |
| **Scope B** — 用户内容 IP | 用户用本仓 schema 创作的所有 system JSON(`rule_set` / `agent_def` / `workflow_dag` / `service_registry` / `knowledge` / `migration`) | **用户自选**(通过 `metadata.license` 字段) | 用户本人 |

**关键规则**:

1. **格式层**:所有 evorule 生态的 system JSON 必须符合本仓 schema 定义的字段结构(5 顶层字段 + kind-specific body + 类型/必填/格式约束)。
2. **法律层**:用户对其创作的 system JSON 拥有完整 IP 所有权,evorule 不主张、不传染、不要求署名/回馈/分润。
3. **AGPL-3.0 的 copyleft 范围**:仅附着在 Scope A 资产本身,Scope A 资产**不**对用户创作的 Scope B 内容施加传染效力。
4. **用户声明机制**:每个 system JSON 通过 `metadata.license` 字段声明其内容协议,enum 为 `Apache-2.0` / `MIT` / `BSD-3-Clause` / `Proprietary` / `Custom`。

**与"治理"措辞的关系**:README 中"所有 evorule 生态的系统 JSON 必须由 evorule-system-rules 治理"中的"治理"专指**格式层面**(必须符合 schema 字段结构),**不**指**法律层面**(许可证、所有权、商业权利)。两者在本规范中**显式分离**。

## 为什么

- **消除用户顾虑**:企业用户最常见的疑虑是"用了 evorule,我的内容会被 AGPL 锁死"。本规范把"框架归 evorule,内容归用户"明文化,降低销售阻力。
- **支持商业用户闭源 SaaS**:`metadata.license` 的 `Proprietary` / `Custom` 选项是给"完全闭源/完全自有"准备的,商业用户可以买 evorule 商业许可覆盖 Scope A 框架,Scope B 内容仍归用户所有且可任意处置。
- **鼓励生态扩张**:第三方做"兼容 evorule 的工具/平台"时,清楚知道他们读 schema 写的工具受 AGPL 约束,但工具处理的用户内容**不受** AGPL 约束,不必担心传染。
- **与 evorule 商业模型一致**:evorule 通过"卖框架许可"(Scope A 商业许可)创收,而不是"控制用户内容"——这与"JSON 是一等公民"(`DESIGN_PHILOSOPHY.md §1`)的透明/可审计/数据导向精神一致。
- **避免法律歧义**:AGPL-3.0 是强 copyleft,但其效力有明确边界(对 licensed work 本身,不自动传染 downstream creations)。本规范把这条边界显式说清,减少后续争议。

## 怎么用

- 本规范主文档:[README.md §用户内容归属](../../README.md#用户内容归属scope-b)
- 本仓特定补充声明:[LEGAL_NOTES.md](../../LEGAL_NOTES.md)
- 设计规范总览:[README.md](./README.md)
- 字段细节:`metadata.license` 字段定义见 [../reference/schema-reference.md](../reference/schema-reference.md)
- 机器可读层:每个 schema 文件在顶层声明 `x_legal_authority_notice` 字段,任何读 schema 的工具都能获取本规范的元信息
- 用户如何声明自己内容的协议:[../tutorial/02-write-first-system-json.md](../tutorial/02-write-first-system-json.md) 中的 `metadata.license` 字段示例

## 不接受的替代方案

- **强制所有 evorule 系统 JSON 走 AGPL**:会阻挡企业用户(他们最在意自己内容的 IP 不被传染),与 evorule 商业模型冲突。schema 的 `metadata.license` 字段明确允许 `Proprietary` / `Custom`,即排斥此方案。
- **不区分 Scope A / Scope B,含糊统称"受 evorule-system-rules 治理"**:读者会把"治理"读成"许可证主张",产生误解。本规范的核心动作就是把"格式治理"和"法律治理"显式拆开。
- **借鉴 `core_eval.json` 的 CC0 把 schemas 也 CC0**:见 docs/explanation 与调研记录——`core_eval.json` 因其"解释器规范"角色才 CC0,schemas 是"元规范"(用于验证系统 JSON 格式,非引擎自身读取),协议立场不同。当前统一走 AGPL-3.0-or-later + 商业双模式,保留未来重新评估的余地。

## 引用

- [README.md §许可](../../README.md#许可) — Scope A 协议入口
- [README.md §用户内容归属(Scope B)](../../README.md#用户内容归属scope-b) — Scope B 协议入口
- [LEGAL_NOTES.md](../../LEGAL_NOTES.md) — 本仓特定法律声明
- [../reference/schema-reference.md](../reference/schema-reference.md) — `metadata.license` 字段定义
- `DESIGN_PHILOSOPHY.md §1 JSON 是一等公民` — 透明/可审计/数据导向的底层立场
- `evorule-tcb/core_eval.json` `metadata.public_domain_notice` — CC0 范围的现有先例

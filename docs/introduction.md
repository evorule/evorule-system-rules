<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# evorule-system-rules 文档导航

> 本目录是 `evorule-system-rules` 仓的**公开文档**,按 [Diátaxis](https://diataxis.fr/) 框架组织。
> 四类文档各司其职,不要混在一起写。
> 项目内部的草稿、未定稿、过程文档由维护者流转,确认后提炼为公开版,详见 [explanation/doc-boundaries.md](./explanation/doc-boundaries.md)。

## 这是什么

`evorule-system-rules` 是 evorule 生态的**系统元规则集**——定义所有 evorule 平台加载的"系统 JSON"应该长什么样,如何版本化,以及 schema 升级时旧 JSON 怎么迁移。

**所有 evorule 生态的系统 JSON 必须由 evorule-system-rules 治理,evorule-rule 是它的下游实现,所有 evorule 系统文件必须对齐并受其约束。**

## 四类文档,各取所需

| 你想做什么 | 看哪里 | 用途 |
|---|---|---|
| 第一次接触,想跑通 | [tutorial/](./tutorial/) | 手把手教学,一步一步带你完成 |
| 有具体问题要解决 | [how-to/](./how-to/) | 任务式指南,以问题为导向 |
| 查 schema / CLI / 版本协议 | [reference/](./reference/) | 字典式参考,准确但无解释 |
| 想理解为什么这么设计 | [explanation/](./explanation/) | 概念与原理,讨论式 |

**不知道该看哪类?** 先问自己:"我在学 / 我在解决 / 我在查 / 我在理解?" —— 对应到上面四类之一。

## 补充目录

- [adr/](./adr/) — 架构决策记录(ADR),记录重要技术决策与历史
- [operations/](./operations/) — 构建、部署、测试、运维

## 公开与内部的边界

按 evorule 公开边界约定:

- **根 `*.md`**(README、CHANGELOG 等)和**本目录 `docs/`** 是 L1 公开,推送到代码托管平台
- **项目内部草稿**(未定稿、过程文档)在内部协作区流转,由维护者提炼为公开版

**工作流**:
1. 内部草稿、调研记录 → 项目内部协作区
2. 确认后 → 提炼为公开 `docs/` 的相应类别(tutorial / how-to / reference / explanation)
3. 重大决策 → 沉淀为 ADR(不可变历史)

**为什么这样分**:避免在公开文档上反复改未定稿内容,保持公开文档的稳定性和专业度。

**详细贡献指南**:[explanation/doc-boundaries.md](./explanation/doc-boundaries.md)

## 6 个 kind 速览

| kind | 用途 | 现有例子 |
|------|------|----------|
| `rule_set` | 业务规则 / TCB 规则 | `core_eval.json` 等业务规则集 |
| `agent_def` | evorule agent 定义 | `evo-agent/agents/*.json` |
| `workflow_dag` | DAG 工作流 | `evo-agent/rules/workflows/*.json` |
| `service_registry` | 服务注册 | `evorule-server/service_registry.json` |
| `knowledge` | 知识库 | `examples/knowledge.example.json`（D5 未验证草案；注：server 的 `docs/PITFALLS.json` 为豁免参照物，带自造壳 `pitfalls-v1`，非本 kind 实例） |
| `migration` | $schema 升级规则 | (本仓自产) |

详细见 [reference/schema-reference.md](./reference/schema-reference.md)。

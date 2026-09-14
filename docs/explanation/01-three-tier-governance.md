<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 01 — 3 层治理模型:Tier 1 / Tier 2 / Tier 3

> **立场篇**——理解 evorule 生态的治理结构。

## 一图理解

```
evorule-system-rules  (Tier 1,系统宪法,evorule 团队维护,**最高权威**)
        │
        ├─→  evorule              (Tier 2,evorule 自家系统)
        ├─→  evorule-server       (Tier 2,服务运行时)
        ├─→  evo-agent            (Tier 2,evorule 自家应用)
        └─→  evorule-rule         (Tier 2,治理层实现,**受 Tier 1 约束**)
                                          │
                                          └─→  项目方业务规则  (Tier 3,通过 evorule-rule 多租户管理)
```

## Tier 1:系统元规则层

- **谁写**:evorule 团队(系统维护者)
- **谁用**:evorule 自己 + evorule-rule + 所有 evorule 生态组件
- **权威性**:**最高**——所有 Tier 2/3 系统 JSON 必须遵循
- **产出**:
  - `$schema` 文件(JSON Schema Draft 2020-12)
  - `migration` 规则(evorule transform 表达)
  - 配套 `CHANGELOG`
- **位置**:`evorule-system-rules/` 仓根目录

## Tier 2:evorule 团队应用层

- **谁写**:evorule 团队(应用开发者)
- **谁用**:evorule 平台运行时
- **权威性**:**受 Tier 1 约束**——所有 system JSON 必须用 Tier 1 定义的 kind
- **现有文件**(待对齐):
  - `evorule/evorule-tcb/core_eval.json` → `kind: rule_set`
  - `evorule-server/service_registry.json` → `kind: service_registry`
  - `evo-agent/agents/*.json` → `kind: agent_def`
  - `evo-agent/rules/workflows/*.json` → `kind: workflow_dag`
  - `evorule-server/docs/PITFALLS.json` → `kind: knowledge`

## Tier 3:项目方业务规则层

- **谁写**:项目方业务专家(evorule 项目方)
- **谁用**:项目方的私有化部署
- **权威性**:**受 Tier 1 约束**——所有业务规则必须用 Tier 1 定义的 `rule_set` 格式
- **管理机制**:**通过 evorule-rule 平台的多租户管理**——evorule-rule 提供 CRUD / 版本 / 治理能力
- **示例**:项目方业务规则集(任意 JSON 文件,通过 evorule-rule 平台管理)

## evorule-rule 的双重身份(关键)

evorule-rule 既是 **Tier 1 的下游**(自己 schema 必须对齐 Tier 1),
又是 **Tier 3 的管理者**(用 Tier 1 治理项目方业务)。

这意味着:
- evorule-rule 的字段(`RuleDataset` / `Entry` / `Governance` / `Provenance` / `Lifecycle` / `Dependency`)
  必须以 Tier 1 的 5 顶层字段表达
- evorule-rule 升级必须跟随 Tier 1 $schema 主版本
- evorule-rule 不允许"自定义"超出 Tier 1 的字段格式

详见 [03-与 evorule-rule 的关系](./03-evorule-rule-alignment.md) 和 [设计规范(evorule-rule 对齐)](../adr/evorule-rule-must-align.md)。

## 为什么是 3 层而不是 2 层或 4 层

### 为什么不 2 层(系统 + 业务)

如果只有 2 层,"evorule 团队"和"项目方"被合并。但 evorule 团队的 system JSON 和项目方的业务规则**管理方式不同**:

- system JSON 由 evorule 团队维护,跟 evorule 版本同步
- 业务规则由 evorule-rule 平台的多租户管理,跟 evorule 版本解耦

2 层会丢失这个差异。

### 为什么不 4 层(再加一层 evorule 团队业务规则)

evorule 团队**自己用 evorule 编写的应用**(例:演示性业务规则)是 Tier 2 还是 Tier 3?

- 如果是 Tier 2:它由 evorule 团队维护,但本质是"业务规则",不是"系统规则"
- 如果是 Tier 3:它被 evorule-rule 多租户管理,但元规则由 evorule 团队制定

实际是**两可**——演示性应用兼具"系统演示"属性与"业务规则"属性。3 层模型通过"Tier 2 是 evorule 自家系统"+"Tier 3 是项目方业务"的二分法,留出灰色地带(由 evorule 团队判定)。这是务实的妥协,体现模型对真实场景的兼容能力。

## 治理的实际动作

| 动作 | 谁做 | 用什么工具 |
|------|------|-----------|
| 起草新 kind schema | evorule 团队 | git + 评审 |
| 修改现有 kind schema | evorule 团队 | git + migration 链 |
| 添加 system JSON | evorule 团队 | `evorule-migrate` |
| 添加项目方业务规则 | 项目方业务专家 | evorule-rule 平台 |
| evorule-rule 升级 | evorule-rule 团队 | 跟随 Tier 1 主版本 |
| 运行 migration 规则 | evorule 启动期 | `evorule-migrate run-migration` |

## 边界争议处理

实际治理中会出现边界争议:
- evorule 团队自建的演示性应用是 Tier 2 还是 Tier 3?
- 项目方编写的高频复用规则是否应提升至 Tier 2?

**处理原则**:
- 与 evorule 平台紧耦合(启动时加载、影响系统行为)→ Tier 2
- 与 evorule 平台松耦合(仅以 evorule 为业务规则引擎)→ Tier 3
- 灰色地带由 evorule 团队评审决定

## 延伸阅读

- [00-evorule 解释 evorule](./00-evorule-explains-evorule.md) — 核心定位
- [03-与 evorule-rule 的关系](./03-evorule-rule-alignment.md) — 双重身份详解
- [设计规范(evorule-rule 对齐)](../adr/evorule-rule-must-align.md) — evorule-rule 必须对齐(设计规范)

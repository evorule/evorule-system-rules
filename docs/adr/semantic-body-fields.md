<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 顶层 body 字段语义化

## 是什么

5 顶层字段之外的 body 字段,按各 kind 的业务语义命名,统一不强制。

**当前各 kind 的 body 字段**:

| kind | body 字段 |
|------|-----------|
| `rule_set` | `rules: []` |
| `agent_def` | `capabilities: []` / `tools: []` / `prompt_ref` / `model_config` |
| `workflow_dag` | `nodes: []` / `edges: []` |
| `service_registry` | `services: []` |
| `knowledge` | `entries: []` |
| `migration` | `transforms: []` |

每个 kind 的 body 字段独立定义、独立维护。

## 为什么

- **业务可读性**:看 `nodes: []` 一眼知道是 DAG,看 `services: []` 一眼知道是服务注册
- **工具路由清晰**:工具根据 `kind` 字段路由到不同的 body 处理逻辑
- **可演进性**:新增 kind 不影响现有 kind 的字段名

## 怎么用

- 各 kind 字段定义:`schemas/<kind>/v0.9.json`
- 字段总览:[reference/schema-reference.md](../reference/schema-reference.md)

## 不接受的替代方案

- **统一容器 `rules: []` + metadata 区分**:嵌套极深,丧失语义
- **`body: {}` 自由字段**:无任何约束,与"不规定"无异

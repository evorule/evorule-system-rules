<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 五顶层字段规范

## 是什么

所有 evorule 系统 JSON 必须包含 5 个固定顶层字段,加 1 个 kind-specific body。

**5 顶层字段**:

| 字段 | 含义 | 必填 | 约束 |
|------|------|------|------|
| `$schema` | 协议版本 URL | 是 | 指向 evorule-system-rules 仓的 schema 文件 |
| `kind` | 系统 JSON 种类 | 是 | 6 选 1(rule_set / agent_def / workflow_dag / service_registry / knowledge / migration) |
| `id` | 命名空间唯一标识 | 是 | 格式 `<org>.<scope>.<name>`,跨版本稳定 |
| `version` | 内容版本 | 是 | semver |
| `metadata` | 人类可读元数据 | 是 | 必含 `title` / `created` / `updated` |

**kind-specific body** 示例:
- `rule_set` → `rules: []`
- `agent_def` → `capabilities: []` / `tools: []` / `prompt_ref`
- `workflow_dag` → `nodes: []` / `edges: []`
- `service_registry` → `services: []`
- `knowledge` → `entries: []`
- `migration` → `transforms: []`

**完整示例**:

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v0.9.json",
  "kind": "rule_set",
  "id": "com.example.sales.validation",
  "version": "1.2.3",
  "metadata": {
    "title": "销售验证规则集",
    "created": "2026-03-01",
    "updated": "2026-08-20"
  },
  "rules": [ /* ... */ ]
}
```

## 为什么

- **工具通用**:5 顶层字段统一,evorule 工具(校验器、迁移器、索引器)可通用处理
- **可校验性**:`$schema` 字段指向 JSON Schema 文件,启动期可自动校验
- **可追溯性**:`id` 跨版本稳定,`version` 跟踪内容迭代
- **元数据明确**:`metadata` 强制包含 title / created / updated,任何 system JSON 一眼能看出"它是什么、谁维护、何时更新"

## 怎么用

- 字段完整定义:[reference/schema-reference.md](../reference/schema-reference.md)
- 编写第一个 system JSON:[tutorial/02-write-first-system-json.md](../tutorial/02-write-first-system-json.md)
- 通用元模式实现:`schemas/_meta/v0.9.json`

## 不接受的替代方案

- **统一 `data: {}` 容器**:`rules: []` 比 `data: { rules: [] }` 更易读
- **不规定顶层字段**:工具无法通用处理,跨仓迁移无依据

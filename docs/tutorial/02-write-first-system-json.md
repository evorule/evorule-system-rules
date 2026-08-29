<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 02 — 写你的第一个 system JSON:rule_set 示例

> 10 分钟从零写一个合规的 `rule_set`,并用 `evorule-migrate validate` 验证。

## 目标

构造一个包含 3 条规则的 `rule_set` JSON,所有字段符合 `schemas/rule_set/v0.9.json` 约束。

## 准备

- 已读 [01-quickstart-validate.md](./01-quickstart-validate.md)
- 已掌握 `evorule-migrate validate` 的用法

## 第 1 步:复制 example 作为起点

```bash
cd <evorule-system-rules>
cp examples/rule_set.example.json examples/my_first_ruleset.json
```

打开 `examples/my_first_ruleset.json`,内容是:

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v0.9.json",
  "kind": "rule_set",
  "id": "com.example.minimal",
  "version": "1.0.0",
  "metadata": {
    "title": "最小规则集示例",
    ...
  },
  "rules": [
    {
      "id": "R001",
      "title": "正值翻倍",
      ...
    }
  ]
}
```

## 第 2 步:设置 `id`

将 `id` 改为目标命名空间:

```json
"id": "com.<your-org>.learning.first-ruleset"
```

**约束**(来自 `_meta` schema):
- 必须小写字母开头
- 每段用 `.` 分隔,每段匹配 `^[a-z][a-z0-9_]*$`
- 推荐格式 `<org>.<scope>.<name>`

## 第 3 步:填充 `metadata`

```json
"metadata": {
  "title": "我的第一个规则集",
  "description": "学习 evorule-system-rules 时构造的练习",
  "authors": ["<your-email>"],
  "created": "2026-08-23",
  "updated": "2026-08-23",
  "tags": ["learning", "first"]
}
```

**必填字段**:
- `title` — 1-200 字符
- `created` — YYYY-MM-DD
- `updated` — YYYY-MM-DD

**可选字段**:description、authors、tags、license、lifecycle、provenance、governance、dependencies

## 第 4 步:编写 3 条规则

```json
"rules": [
  {
    "id": "R001",
    "title": "成年判断",
    "when": { "expr": "input.age >= 18" },
    "then": { "set": "output.is_adult = true" }
  },
  {
    "id": "R002",
    "title": "未成年判断",
    "when": { "expr": "input.age < 18" },
    "then": { "set": "output.is_adult = false" }
  },
  {
    "id": "R003",
    "title": "默认拒绝",
    "when": { "expr": "true" },
    "then": { "set": "output.requires_review = true" }
  }
]
```

**约束**:
- `id` 格式 `^R\d{3,6}$`(如 R001、R999999)
- 至少 1 条规则
- `when` 和 `then` 是 evorule 表达式(本教程用伪语法,具体语法由 evorule 引擎定义)

## 第 5 步:完整文件

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v0.9.json",
  "kind": "rule_set",
  "id": "com.<your-org>.learning.first-ruleset",
  "version": "1.0.0",
  "metadata": {
    "title": "我的第一个规则集",
    "description": "学习 evorule-system-rules 时构造的练习",
    "authors": ["<your-email>"],
    "created": "2026-08-23",
    "updated": "2026-08-23",
    "tags": ["learning", "first"]
  },
  "rules": [
    {
      "id": "R001",
      "title": "成年判断",
      "when": { "expr": "input.age >= 18" },
      "then": { "set": "output.is_adult = true" }
    },
    {
      "id": "R002",
      "title": "未成年判断",
      "when": { "expr": "input.age < 18" },
      "then": { "set": "output.is_adult = false" }
    },
    {
      "id": "R003",
      "title": "默认拒绝",
      "when": { "expr": "true" },
      "then": { "set": "output.requires_review = true" }
    }
  ]
}
```

## 第 6 步:验证

```bash
python tools/evorule-migrate validate examples/my_first_ruleset.json
```

**预期输出**:
```
OK examples/my_first_ruleset.json (kind=rule_set, schema=v0.9)
```

**校验失败时**:查看错误信息并根据提示修复。常见错误包括 `id` 格式不符、`rules` 少于 1 条、`metadata` 缺必填字段。

## 第 7 步:尝试其他 kind

将 `kind` 替换为 `agent_def` / `workflow_dag` / `service_registry` / `knowledge`,按照各 kind 的字段定义构造自己的版本。

字段定义见 [reference/schema-reference.md](../reference/schema-reference.md)。

## 下一步

- 把已有的 evorule JSON 升级到 v0.9 → [tutorial/03-upgrade-v0-to-v0.9.md](./03-upgrade-v0-to-v0.9.md)
- 理解 5 顶层字段为什么这样设计 → [explanation/00-evorule-explains-evorule.md](../explanation/00-evorule-explains-evorule.md)

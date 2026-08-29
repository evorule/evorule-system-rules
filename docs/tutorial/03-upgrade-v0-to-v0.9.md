<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 03 — 把 v0 JSON 升级到 v0.9

> 10 分钟跑通 `evorule-migrate upgrade`,为旧 evorule JSON 添加 5 顶层字段。

## 目标

准备一个 v0 格式的 JSON(无 5 顶层字段),运行 `upgrade` 升级到 v0.9,产出符合 v0.9 schema 的新 JSON。

## 前置条件

- 已读 [01-quickstart-validate.md](./01-quickstart-validate.md) 和 [02-write-first-system-json.md](./02-write-first-system-json.md)
- 已理解 `$schema` 和 `version` 字段的作用

## 第 1 步:准备一个 v0 格式的 JSON

在 `examples/` 目录新建 `my_old.json`:

```json
{
  "name": "我的旧规则集",
  "description": "没有 5 顶层字段的 v0 格式",
  "rules": [
    {
      "id": "R001",
      "when": { "expr": "input.x > 0" },
      "then": { "set": "output.y = 1" }
    }
  ]
}
```

**v0 格式特征**:
- 缺少 `$schema` / `kind` / `id` / `version` / `metadata` 5 顶层字段
- 包含自定义旧字段(如 `name`)

## 第 2 步:验证 v0 格式无法通过 v0.9 schema 校验

```bash
python tools/evorule-migrate validate examples/my_old.json
```

**预期输出**:
```
校验失败(...):
  - /: 'my_old.json' is missing required properties: '$schema', 'kind', 'id', 'version', 'metadata'
```

说明:缺少 5 顶层字段,需要通过 migration 升级。

## 第 3 步:运行 upgrade

```bash
python tools/evorule-migrate upgrade examples/my_old.json \
  --from-schema v0.0 \
  --to-schema v0.9 \
  -o examples/my_new.json
```

**预期输出**:
```
[OK] 已写入 examples/my_new.json

应用的 migrations:
  [OK] add_five_top_fields.json: 6 transforms
```

## 第 4 步:查看升级后的 JSON

打开 `examples/my_new.json`,内容大致为:

```json
{
  "name": "我的旧规则集",
  "description": "没有 5 顶层字段的 v0 格式",
  "rules": [
    { "id": "R001", "when": {...}, "then": {...} }
  ],
  "$schema": "https://evorule.org/schemas/' + kind + '/v0.9.json",
  "kind": "<derived-by-tool>",
  "id": "<derived-by-tool>",
  "version": "0.1.0",
  "metadata": {
    "authors": "['<git-user-email>']"
  }
}
```

**说明**:
- 原字段(`name` / `description` / `rules`)被保留
- 5 顶层字段已添加(部分以占位符 `<derived-by-tool>` 形式呈现)

## 第 5 步:理解占位符

工具的当前版本用占位符标记需要人工或后续工具补全的字段:

| 占位符 | 含义 | 补全方式 |
|--------|------|----------|
| `<derived-by-tool>` | 从上下文推导(后续 transform 引擎补) | 工具(完整 transform 引擎) |
| `<git-user-email>` | 从 git config 推导 | 工具 |
| `$schema` 字段值 | 从 `kind` 字段拼接 | 工具 |

**已知限制**:完整 transform 引擎是阶段 1 周 2 的工作(见 [reference/cli-reference.md §已知限制](../reference/cli-reference.md))。

## 第 6 步:手工补全占位符

打开 `my_new.json`,将占位符替换为实际值:

```json
{
  "name": "我的旧规则集",
  "description": "没有 5 顶层字段的 v0 格式",
  "rules": [
    { "id": "R001", "when": {...}, "then": {...} }
  ],
  "$schema": "https://evorule.org/schemas/rule_set/v0.9.json",
  "kind": "rule_set",
  "id": "com.<your-org>.learning.upgraded-ruleset",
  "version": "0.1.0",
  "metadata": {
    "title": "升级后的规则集",
    "description": "从 v0 升级到 v0.9",
    "authors": ["<your-email>"],
    "created": "2026-08-23",
    "updated": "2026-08-23",
    "tags": ["upgraded"]
  }
}
```

## 第 7 步:验证升级结果

```bash
python tools/evorule-migrate validate examples/my_new.json
```

**预期输出**:
```
OK examples/my_new.json (kind=rule_set, schema=v0.9)
```

**校验失败时**:
- 字段缺失 → 检查 5 顶层字段是否完整
- `id` 格式错 → 遵循 `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` 格式
- `metadata` 缺必填 → `title` / `created` / `updated` 是必填

## 完整工作流

```
v0 格式 JSON
    │
    ▼
evorule-migrate upgrade
    │
    ▼
v0.9 格式 JSON(含占位符)
    │
    ▼
人工补全占位符
    │
    ▼
evorule-migrate validate ✓
```

## 下一步

- 跑多个 migration 自由组合 → [how-to/upgrade-existing-json.md](../how-to/upgrade-existing-json.md)
- 理解双版本协议 → [reference/version-protocol.md](../reference/version-protocol.md)

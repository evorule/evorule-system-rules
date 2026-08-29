<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 01 — 快速开始:校验你的第一个 system JSON

> 5 分钟完成首次 `evorule-migrate validate`。

## 前置条件

- Python 3.10+(3.12 已验证)
- 依赖包:`jsonschema` ≥ 4.18,`referencing` ≥ 0.30
- evorule-system-rules 仓(本仓根目录)

## 安装依赖

```bash
pip install jsonschema referencing
```

确认安装:
```bash
python -c "import jsonschema, referencing; print('OK')"
```

## 列出支持的 kind

```bash
cd <evorule-system-rules>
python tools/evorule-migrate list-kinds
```

**预期输出**:
```
支持的 kind:
  - agent_def: v0.9
  - knowledge: v0.9
  - migration: v0.9
  - rule_set: v0.9
  - service_registry: v0.9
  - workflow_dag: v0.9
```

## 校验单个 example

```bash
python tools/evorule-migrate validate examples/rule_set.example.json
```

**预期输出**:
```
OK examples/rule_set.example.json (kind=rule_set, schema=v0.9)
```

## 批量校验 examples

```bash
# PowerShell
foreach ($f in (Get-ChildItem examples -Filter '*.json')) {
    python tools/evorule-migrate validate $f.FullName
}
```

**预期输出**(6 行 OK):
```
OK .../agent_def.example.json (kind=agent_def, schema=v0.9)
OK .../knowledge.example.json (kind=knowledge, schema=v0.9)
OK .../migration.example.json (kind=migration, schema=v0.9)
OK .../rule_set.example.json (kind=rule_set, schema=v0.9)
OK .../service_registry.example.json (kind=service_registry, schema=v0.9)
OK .../workflow_dag.example.json (kind=workflow_dag, schema=v0.9)
```

## 构造错误示例,观察校验失败

在 `examples/` 目录建一个 `bad.example.json`:

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v0.9.json",
  "kind": "rule_set",
  "id": "BadID",  ← 错误:大写字母开头
  "version": "1.0.0",
  "metadata": {
    "title": "测试",
    "created": "2026-08-23",
    "updated": "2026-08-23"
  },
  "rules": []  ← 错误:至少 1 条
}
```

跑校验:
```bash
python tools/evorule-migrate validate examples/bad.example.json
```

**预期输出**:
```
校验失败(...):
  - /id: 'BadID' does not match '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'
  - /rules: [] is too short (minItems=1)
```

**说明**:
- 字段不符合 schema 约束时,工具明确指出错误位置
- 修复后重跑,直到输出 OK

## 校验已有的 system JSON

evorule 生态中未对齐 v0.9 的 system JSON,跑校验会失败——这是预期行为。

```bash
python tools/evorule-migrate validate <path-to-existing-system-json>
```

**预期输出**:
```
校验失败(...):
  - /: '<文件名>' is missing required properties: '$schema', 'kind', 'id', 'version', 'metadata'
```

迁移至 v0.9 的方法见 [tutorial/03-upgrade-v0-to-v0.9.md](./03-upgrade-v0-to-v0.9.md)。

## 下一步

- 写一个自己的 system JSON → [tutorial/02-write-first-system-json.md](./02-write-first-system-json.md)
- 跑 migration 升级旧 JSON → [tutorial/03-upgrade-v0-to-v0.9.md](./03-upgrade-v0-to-v0.9.md)
- 查 CLI 详细用法 → [reference/cli-reference.md](../reference/cli-reference.md)

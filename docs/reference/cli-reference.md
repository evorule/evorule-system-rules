<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# evorule-migrate CLI

> `tools/evorule-migrate` 的命令行参考。

## 安装

```bash
# 方式 1:直接使用(从仓根目录)
cd <evorule-system-rules>
python tools/evorule-migrate <subcommand> [args]

# 方式 2:pip 安装(待发布)
pip install evorule-migrate
evorule-migrate <subcommand> [args]
```

依赖:`jsonschema` ≥ 4.18,`referencing` ≥ 0.30

## 全局选项

```bash
evorule-migrate --help
evorule-migrate <subcommand> --help
```

## 子命令

### validate

校验一个 system JSON 符合指定 `$schema`。

```bash
evorule-migrate validate <input.json>
```

**参数**:
- `input` — 待校验的 JSON 文件路径

工具从 `$schema` 字段自动读取 kind 和 version。

**退出码**:
- 0 — 校验通过
- 1 — 校验失败(打印具体错误)
- 2 — JSON 解析失败或 schema 文件缺失

**示例**:
```bash
$ python tools/evorule-migrate validate examples/rule_set.example.json
OK examples/rule_set.example.json (kind=rule_set, schema=v0.9)
```

### upgrade

将旧版本 JSON 升级到新版本(运行 migration 规则)。

```bash
evorule-migrate upgrade <input.json> \
  --from-schema <from> \
  --to-schema <to> \
  [--output <output.json>]
```

**参数**:
- `input` — 输入 JSON
- `--from-schema` — 起始 `$schema` 版本(默认 `v0.0`)
- `--to-schema` — 目标 `$schema` 版本(默认 `v0.9`)
- `--output` / `-o` — 输出 JSON(默认 stdout)

**行为**:
1. 加载 `migrations/<from>-to-<to>/` 下所有 `*.json`
2. 按文件名顺序应用每个 migration
3. 输出新 JSON + 应用报告
4. 检测占位符(`<...>`),存在则警告(exit 2)

**示例**:
```bash
$ python tools/evorule-migrate upgrade old.json \
    --from-schema v0.0 --to-schema v0.9 \
    -o new.json

应用的 migrations:
  [OK] add_five_top_fields.json: 6 transforms
```

### run-migration

运行指定的 migration 规则(可自由组合)。

```bash
evorule-migrate run-migration <input.json> <migration1.json> [<migration2.json> ...] \
  [--output <output.json>]
```

**参数**:
- `input` — 输入 JSON
- `migration` — 1+ 个 migration JSON 文件
- `--output` / `-o` — 输出 JSON(默认 stdout)

**适用场景**:
- 不走标准 `v0.0 → v0.9` 链路,自由组合多个 migration
- 测试单个 migration 规则

**示例**:
```bash
$ python tools/evorule-migrate run-migration \
    old.json \
    migrations/v0.0-to-v0.9/add_five_top_fields.json \
    -o new.json
```

### list-kinds

列出所有支持的 kind + 版本。

```bash
evorule-migrate list-kinds
```

**输出**:
```
支持的 kind:
  - agent_def: v0.9
  - knowledge: v0.9
  - migration: v0.9
  - rule_set: v0.9
  - service_registry: v0.9
  - workflow_dag: v0.9
```

## 退出码总览

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 校验失败 |
| 2 | 工具内部错误(JSON 解析失败、schema 缺失、占位符未补) |

## 高级用法

### 批量校验一个目录

```bash
# PowerShell
Get-ChildItem examples,migrations -Recurse -Filter '*.json' | ForEach-Object {
    python tools/evorule-migrate validate $_.FullName
}
```

### 升级并校验

```bash
# 升级
python tools/evorule-migrate upgrade old.json --from-schema v0.0 --to-schema v0.9 -o new.json

# 校验新文件
python tools/evorule-migrate validate new.json
```

## 已知限制

- 字符串拼接 transform 暂不支持(仅支持字面量值和 `set` 字段)
- JSON 对象字面量 transform 暂不支持
- 占位符 `<derived-by-tool>` 等需人工或后续工具补全

完整 transform 引擎是后续阶段的工作。

## 延伸阅读

- [tutorial/01-quickstart-validate.md](../tutorial/01-quickstart-validate.md) — 第一次使用
- [how-to/validate-system-json.md](../how-to/validate-system-json.md) — 校验任务详解

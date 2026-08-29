<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 如何升级已有 JSON 到新 schema

> 任务:将 evorule 生态的旧 system JSON(无 5 顶层字段)升级到 v0.9。

## 适用场景

- 将 evorule 生态各仓的 system JSON 对齐 v0.9
- 团队成员接入 evorule-system-rules 时,迁移存量 JSON
- v0.9 → v1.0 等后续 schema 升级

## 标准升级链路

```bash
python tools/evorule-migrate upgrade <input.json> \
  --from-schema v0.0 \
  --to-schema v0.9 \
  -o <output.json>
```

工具行为:
1. 加载 `migrations/v0.0-to-v0.9/` 下所有 `*.json`
2. 按文件名顺序应用每个 migration 的 transforms
3. 输出新 JSON + 应用报告
4. 报告未补全的占位符(如 `<derived-by-tool>`)

## 跨多版本升级

如果 `migrations/v0.0-to-v1.0/` 不存在(仅存在分段 `v0.0-to-v0.9` + `v0.9-to-v1.0`),需要逐级升级:

```bash
# 先升到 v0.9
python tools/evorule-migrate upgrade old.json --from-schema v0.0 --to-schema v0.9 -o step1.json

# 再升到 v1.0
python tools/evorule-migrate upgrade step1.json --from-schema v0.9 --to-schema v1.0 -o step2.json
```

工具**不**自动串联。显式逐级升级可避免跳过关键 migration。

## 自定义 migration 组合

若不走标准链路,可自由组合多个 migration:

```bash
python tools/evorule-migrate run-migration \
  old.json \
  migrations/v0.0-to-v0.9/add_five_top_fields.json \
  migrations/v0.0-to-v0.9/special_handling.json \
  -o new.json
```

适用场景:
- 测试单个 migration 规则
- 项目特定的 migration 链(不走标准版本号)

## 升级后必须验证

```bash
python tools/evorule-migrate validate new.json
```

校验失败时,根据错误信息修复。

## 真实场景:批量升级 evorule 生态的 system JSON

evorule 生态的系统 JSON 分布在多个仓的固定位置。批量升级前:

1. 列出所有待升级的 system JSON 路径
2. 准备备份目录(如 `<evorule-system-rules>/_migration_backup/`)
3. 运行批量升级命令

**PowerShell 批量示例**:

```powershell
# 1. 列出待升级文件(根据实际项目位置调整)
$files = @(
    "<path-to-evorule-repo>/<path-to-tcb>/core_eval.json",
    "<path-to-evorule-server-repo>/service_registry.json",
    "<path-to-evorule-server-repo>/docs/PITFALLS.json",
    "<path-to-evo-agent-repo>/agents/general.json",
    "<path-to-evo-agent-repo>/agents/researcher.json",
    "<path-to-evo-agent-repo>/rules/workflows/research_and_write.json"
)

# 2. 运行升级
foreach ($f in $files) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($f)
    $out = "<evorule-system-rules>/_migration_backup/$base.v0.9.json"
    python tools/evorule-migrate upgrade $f --from-schema v0.0 --to-schema v0.9 -o $out
}
```

**重要**:升级前先备份原文件,确认无误后再覆盖。

## 处理占位符

工具当前版本会留下占位符(`<derived-by-tool>` / `<git-user-email>` / 部分字段拼接),需要人工或后续工具补全。

**推荐流程**:
1. 运行 `upgrade` 产出新 JSON
2. 运行 `evorule-migrate validate` 查看哪些字段未通过
3. 参照 `id` 命名规范与 `metadata` 必填字段手工补全
4. 再次运行 `validate` 直至通过

完整 transform 引擎(自动补占位符)是后续阶段的工作。

## 升级失败的常见原因

### migration 规则文件不存在

```
错误:找不到 migration v0.0 → v0.9
```

**修复**:确认 `migrations/v0.0-to-v0.9/` 目录存在 + 有 `*.json` 文件

### 占位符未补全

```
[WARN] 以下占位符需要人工或工具补全:
  - kind = <derived-by-tool>
```

**修复**:手动替换为实际值

### 升级后 validate 失败

**修复**:看 validate 错误,根据 [how-to/validate-system-json.md](./validate-system-json.md) 修复

## 进阶:编写自定义 migration 规则

项目特定的旧 JSON 需要特殊处理时,可编写自定义 migration:

```json
{
  "$schema": "https://evorule.org/schemas/migration/v0.9.json",
  "kind": "migration",
  "id": "com.<your-org>.migration.add_custom_field",
  "version": "0.9.0",
  "from_version": "v0.0",
  "to_version": "v0.9",
  "metadata": {
    "title": "添加项目特定字段",
    "created": "2026-08-23",
    "updated": "2026-08-23"
  },
  "transforms": [
    {
      "id": "M001",
      "title": "添加项目标记字段",
      "when": { "missing": "project" },
      "then": { "set": "project = '<your-org>'" }
    }
  ]
}
```

将文件放入 `migrations/v0.0-to-v0.9/` 目录,运行标准 `upgrade` 时会自动应用。

## 延伸阅读

- [tutorial/03-upgrade-v0-to-v0.9.md](../tutorial/03-upgrade-v0-to-v0.9.md) — 详细教学
- [reference/cli-reference.md](../reference/cli-reference.md) — CLI 用法
- [reference/version-protocol.md](../reference/version-protocol.md) — 双版本协议

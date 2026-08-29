<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 如何校验 system JSON

> 任务:验证 system JSON 符合 evorule-system-rules 的 schema。

## 适用场景

- evorule 启动前,检查所有 system JSON 都合规
- CI 流水线中,防止格式错误的 JSON 合并
- 第三方接入前,验证其 system JSON 格式

## 单文件校验

```bash
python tools/evorule-migrate validate path/to/your.json
```

工具自动从 `$schema` 字段读取 kind 和 version,加载对应 schema 校验。

## 批量校验一个目录

### PowerShell

```powershell
Get-ChildItem -Path path\to\dir -Recurse -Filter '*.json' | ForEach-Object {
    $result = python tools/evorule-migrate validate $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] $($_.FullName)" -ForegroundColor Red
        Write-Host $result
    } else {
        Write-Host "[OK]   $($_.FullName)"
    }
}
```

### bash / Linux

```bash
find path/to/dir -name '*.json' -type f | while read f; do
    python tools/evorule-migrate validate "$f" || echo "FAIL: $f"
done
```

## 在 CI 中集成

`.github/workflows/validate.yml`(或对应的代码托管平台 CI 配置):

```yaml
name: Validate System JSON
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install jsonschema referencing
      - run: |
          find . -name '*.json' -not -path './schemas/*' -not -path './book/*' | while read f; do
            python tools/evorule-migrate validate "$f" || exit 1
          done
```

## 常见错误与修复

### 错误:`missing required properties: '$schema', 'kind', 'id', 'version', 'metadata'`

**原因**:JSON 缺 5 顶层字段
**修复**:运行 `evorule-migrate upgrade` 升级到 v0.9,见 [upgrade-existing-json.md](./upgrade-existing-json.md)

### 错误:`'BadID' does not match '^[a-z][a-z0-9_]*...'`

**原因**:`id` 字段命名不符合规范
**修复**:改为 `<org>.<scope>.<name>` 格式,全小写,每段匹配 `^[a-z][a-z0-9_]*$`

### 错误:`'v0.9' does not match '^v\d+\.\d+$'`

**原因**:`from_version` / `to_version` 格式错误
**修复**:使用 `v0.0` / `v0.9` / `v1.0` 等格式(注意是 `v0.0` 而非 `v0`)

### 错误:`'v0.9' does not match '^[a-z0-9_-]+$'`

**原因**:`metadata.tags` 含特殊字符
**修复**:tag 仅允许小写字母、数字、下划线、连字符

## 高级:自定义校验规则

添加项目特定的校验规则(如"所有 rule 必须有 title"):

```python
# 自定义脚本
import json
import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

# 加载 schema(同 evorule-migrate)
# ...

# schema 校验通过后,运行项目特定规则
def check_rules_have_titles(data):
    errors = []
    for i, rule in enumerate(data.get('rules', [])):
        if 'title' not in rule:
            errors.append(f"rules[{i}] ({rule.get('id', '?')}) 缺 title")
    return errors
```

## 延伸阅读

- [tutorial/01-quickstart-validate.md](../tutorial/01-quickstart-validate.md) — 第一次使用
- [reference/cli-reference.md](../reference/cli-reference.md) — CLI 详细
- [reference/schema-reference.md](../reference/schema-reference.md) — 字段定义

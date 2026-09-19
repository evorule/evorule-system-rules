<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# CI 与校验流水线

> evorule-system-rules 仓的 CI 配置、校验流水线、自动化测试。

## 流水线目标

1. **PR 校验**:每个 PR 触发,验证 schema / examples / migrations 一致
2. **主分支保护**:`master` 分支必须通过所有校验才能合并
3. **版本发布**:打 tag 时自动跑全套测试

## 校验项

### 1. Schema 校验

所有 `schemas/**/*.json` 必须:
- 是合法 JSON
- 符合 JSON Schema 2020-12 元 schema
- `_meta` 被所有 kind 正确引用

### 2. Examples 校验

所有 `examples/**/*.example.json` 必须:
- 是合法 JSON
- 通过 `evorule-migrate validate`

### 3. Migrations 校验

所有 `migrations/**/*.json` 必须:
- 是合法 JSON
- 通过 `evorule-migrate validate`
- `from_version` / `to_version` 与目录名一致

### 4. 工具自检

- `evorule-migrate list-kinds` 输出 6 个 kind
- 工具能跑 `validate` / `upgrade` / `run-migration` 三个子命令

### 5. Docs 链接检查

- `docs/` 内 .md 文件的相对链接不指向 404
- `SUMMARY.md` 列出的所有文件存在

### 6. 白名单对齐闸（`check_whitelist_sync.py`）

- TCB dispatch（`evorule-tcb/src/executor.rs`）↔ schema enum ↔ governance/CLI 白名单 ↔ bundle 结构门禁（`evorule-bundle/src/structure.rs`）**对齐一致**（77 线1 / 70 F-01；bundle 第四向为存量豁免清零 L1，2026-09-15 接入）
- 防 P0-01 复发：TCB 新增/调整元指令即 FAIL
- 命令：`python tools/check_whitelist_sync.py`
- **依赖外部权威仓**：需 `EVORULE_REPO` 指向已检出的 evorule 仓、`EVORULE_BUNDLE_REPO` 指向已检出的 evorule-bundle 仓（缺文件 → FAIL）

### 7. Schema 闭环验收（`_verify_schemas.py`）

- 全部 `schemas/**/*.json` 合法且符合 JSON Schema 2020-12（即校验项 1 的自动化）
- 真实文件（core_eval / 10_role13_demo / yuanze / service_registry 合并视图）通过 v1.0 schema
- 负向用例（not.domain / 混层 / set 缺 value / 非 `__` 路径）全部被拒
- examples 按 `$schema` 闭环（`_meta` 引用一致性）
- 命令：`python _verify_schemas.py`（末尾自动并入 §4 白名单对齐闸）
- **依赖外部仓**：`EVORULE_REPO` / `EVORULE_SERVER_REPO`（必选，缺失 → FAIL）；`YUANZE_DEMOS`（可选，缺失 → SKIP 对应用例）

## Gitee Go 配置(`.gitee-ci/ci.yml`,如使用 Gitee)

```yaml
name: evorule-system-rules CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Checkout authority repos (白名单对齐闸 / schema 闭环依赖)
        # 70 F-01：白名单与真实文件以 evorule / evorule-server 为权威源。
        # 仓库地址与 secrets 名按实际配置；不可用 public clone 时用 PAT。
        uses: actions/checkout@v4
        with:
          repository: <org>/evorule
          path: evorule
          token: ${{ secrets.PAT_EVORULE }}
      - uses: actions/checkout@v4
        with:
          repository: <org>/evorule-server
          path: evorule-server
          token: ${{ secrets.PAT_EVORULE }}
      - name: Install dependencies
        run: pip install jsonschema referencing
      - name: Tool self-check
        run: |
          python tools/evorule-migrate list-kinds
          # 期望:6 个 kind
      - name: Validate examples
        run: |
          for f in examples/*.json; do
            python tools/evorule-migrate validate "$f" || exit 1
          done
      - name: Validate migrations
        run: |
          for f in migrations/**/*.json; do
            python tools/evorule-migrate validate "$f" || exit 1
          done
      - name: Schema closed-loop verify (校验项 7, 内含 1/6)
        env:
          EVORULE_REPO: ${{ github.workspace }}/evorule
          EVORULE_SERVER_REPO: ${{ github.workspace }}/evorule-server
          # YUANZE_DEMOS 可选：不提供时脚本自动 SKIP 对应用例
        run: python _verify_schemas.py
      - name: Whitelist alignment gate (校验项 6)
        env:
          EVORULE_REPO: ${{ github.workspace }}/evorule
        run: python tools/check_whitelist_sync.py
      - name: Docs link check
        run: |
          # 简易检查:SUMMARY.md 链接的文件存在
          python tools/check_docs_links.py
```

## 本地预检

发版前本地跑:

```bash
# PowerShell
$ErrorActionPreference = 'Stop'

# 1. 工具自检
python tools/evorule-migrate list-kinds

# 2. 校验 examples
foreach ($f in (Get-ChildItem examples -Filter '*.json')) {
    python tools/evorule-migrate validate $f.FullName
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# 3. 校验 migrations
foreach ($f in (Get-ChildItem migrations -Recurse -Filter '*.json')) {
    python tools/evorule-migrate validate $f.FullName
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# 4. Schema 元有效性
foreach ($f in (Get-ChildItem schemas -Recurse -Filter '*.json')) {
    python -c "import json, jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open(r'$($f.FullName)')))"
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# 5. Schema 闭环验收（真实文件 + 负向用例，末尾含白名单对齐闸）
#    YUANZE_DEMOS 可选：不提供则按兄弟仓布局自动推导（<检出根>/yuanze-demos），对应仓缺失时自动 SKIP 对应用例
python _verify_schemas.py
if ($LASTEXITCODE -ne 0) { exit 1 }

# 6. 白名单对齐闸（TCB dispatch ↔ schema ↔ governance/CLI）
python tools/check_whitelist_sync.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "All checks passed" -ForegroundColor Green
```

## 性能基线

- 7 个 schema 文件,总 ~13KB
- 6 个 examples + 1 个 migration,总 ~8KB
- 工具冷启动 < 1s
- 单文件 validate < 100ms
- 批量校验 100 个 JSON < 5s

## 采用度监控

发版后跟踪:
- evorule 生态各仓的 system JSON 是否在阶段 2 末全部对齐 v0.9
- 团队是否在用 `evorule-migrate` 跑日常校验
- issue / PR 数(反映采用度)

## 故障排查

### `jsonschema` 版本不匹配

```bash
pip install --upgrade jsonschema referencing
# 要求 jsonschema >= 4.18,referencing >= 0.30
```

### `Draft202012Validator` 不存在

`jsonschema` < 4.18 才有这个类,确保:
```bash
python -c "import jsonschema; print(jsonschema.__version__)"
# 期望 >= 4.18
```

### `referencing` 库缺失

`evorule-migrate` 用 `referencing` 库避免自动 fetch URL:
```bash
pip install referencing
```

### PowerShell 中文乱码

如果工具输出在 PowerShell 显示乱码,设:
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

或直接用 `python` 跑(用 UTF-8 写出文件)。

## 延伸阅读

- [release-process.md](./release-process.md) — 发版流程
- [reference/cli-reference.md](../reference/cli-reference.md) — CLI 详细

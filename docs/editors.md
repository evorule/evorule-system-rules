<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 编辑器 $schema 关联

> 条文 `[CON-L0-002]`：编辑器关联必须**生效**——配了不生效等于没配。
> 关联后,你的编辑器会在保存前实时标出违反宪法 schema 的字段,写规则时就能看到错误,
> 而不是等发布门禁（[CON-L1-001]）拒收。
>
> 所有宪法 schema 是 JSON Schema **draft 2020-12**,任何支持该草案的编辑器/语言服务都可关联。

## 方式一：文档内嵌 `$schema` 头（推荐,零配置）

宪法要求每份系统 JSON 首键就是 `$schema`（[CON-L0-001]）。VS Code 与 JetBrains
的 JSON 语言服务都会自动读取这个头并加载对应 schema,**无需任何额外配置**：

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
  "kind": "rule_set",
  ...
}
```

注意:URL 是 schema 的**规范标识**（`$id`）。若你的环境无法联网解析该 URL,
请改用下面两种方式指向本地文件。

## 方式二：VS Code（settings.json 映射）

在项目根建 `.vscode/settings.json`,把文件名模式映射到本仓 schema 文件：

```jsonc
{
  "json.schemas": [
    {
      "fileMatch": ["core_eval.json", "rules/*.ruleset.json"],
      "url": "./schemas/rule_set/v1.0.json"
    },
    {
      "fileMatch": ["*workflow*.json"],
      "url": "./schemas/workflow_dag/v1.3.json"
    },
    {
      "fileMatch": ["service_registry.json"],
      "url": "./schemas/service_registry/v1.0.json"
    }
  ]
}
```

- `url` 支持相对路径（相对工作区根）或 `file://` 绝对路径;也可直接填规范 URL（能联网时）。
- `fileMatch` 按你的仓库布局改;文档内嵌 `$schema` 头优先于映射。
- 验证生效：随便删掉一条指令的必填参数,右侧问题面板应立即报 `required` 类错误。

## 方式三：JetBrains IDE（JSON Schema Mappings）

以 IntelliJ IDEA / PyCharm / WebStorm / GoLand 等为例：

1. `Settings` → `Languages & Frameworks` → `Schemas and DTDs` → `JSON Schema Mappings`
2. 点 `+` 新建映射,名称如 `evorule rule_set`
3. Schema 文件指向本仓 `schemas/rule_set/v1.0.json`（或填规范 URL）
4. 添加文件模式,如 `core_eval.json` 或通配 `*.ruleset.json`
5. 保存后打开目标 JSON,底部状态栏应显示 schema 已关联;编辑时实时标红

映射持久化在 `.idea/jsonSchemas.xml`,可随仓库提交给团队共用。

## 其他编辑器

- **Sublime Text**：装 `LSP-json` 包,在其设置中把本仓 schema 文件路径加入
  `schema_urls`/本地映射即可。
- **Neovim / Emacs（LSP）**：经 `vscode-json-languageserver` 类语言服务,在
  `settings` 的 `json.schemas` 传入同样的 `fileMatch + url` 结构。
- **通用判据**（[CON-L0-002]）：配置完成后,向目标文件注入一处必知违规
  （例如删掉 `set` 指令的 `params.attr`）,编辑器**必须**当场标红——标红即生效,
  不标红即配置未生效,回查映射路径。

<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 6 个 kind 的 schema 字段

> 所有 system JSON 的权威字段定义。完整 JSON Schema 在 `schemas/<kind>/v0.9.json`。

## 通用 5 顶层字段

所有 kind 共享:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `$schema` | string | 是 | URL,指向 `https://evorule.org/schemas/<kind>/v<version>.json` |
| `kind` | enum | 是 | 6 选 1 |
| `id` | string | 是 | `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` |
| `version` | string | 是 | semver |
| `metadata` | object | 是 | 含 `title` / `created` / `updated` 必填 |

### `metadata` 子字段

| 子字段 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `title` | string | 是 | 人类可读标题,1-200 字符 |
| `description` | string | 否 | 详细描述,≤ 5000 字符 |
| `authors` | array\<email\> | 否 | 作者邮箱列表 |
| `created` | date | 是 | 创建日期,YYYY-MM-DD |
| `updated` | date | 是 | 最后更新日期,YYYY-MM-DD |
| `tags` | array\<string\> | 否 | 标签,`^[a-z0-9_-]+$` |
| `license` | enum | 否 | `Apache-2.0` / `MIT` / `BSD-3-Clause` / `Proprietary` / `Custom` |
| `lifecycle` | object | 否 | `{ state, since }`,`state` 是 `draft` / `review` / `active` / `deprecated` / `retired` |
| `provenance` | object | 否 | `{ source, derived_from }`,`source` 是 `manual` / `generated` / `derived` / `imported` |
| `governance` | object | 否 | `{ approvers, reviewers, approval_date }` |
| `dependencies` | array | 否 | `[{ id, version }]`,`version` 是 semver range |

## kind: rule_set

业务规则集合 / TCB 规则集合。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rules` | array\<rule\> | 是 | ≥1 条规则 |

**rule 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | 是 | `^R\d{3,6}$`,规则集内唯一 |
| `title` | string | 否 | ≤ 200 字符 |
| `description` | string | 否 | ≤ 2000 字符 |
| `when` | object | 是 | evorule when 表达式 |
| `then` | object | 是 | evorule then 表达式 |
| `transform` | object | 否 | evorule transform 表达式 |
| `metadata` | object | 否 | 规则级元数据 |

**完整例子**: `examples/rule_set.example.json`

## kind: agent_def

evorule agent 定义。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `capabilities` | array\<string\> | 是 | ≥1 个能力,如 `web_search` / `document_read` |
| `tools` | array\<string\> | 否 | 可调用的工具名,对应 `service_registry` |
| `prompt_ref` | string | 是 | system prompt 引用(文件路径或 URL) |
| `model_config` | object | 否 | `{ provider, model, temperature, max_tokens }` |

**完整例子**: `examples/agent_def.example.json`

## kind: workflow_dag

DAG workflow 定义（对齐 evo-agent Workflow 引擎；v1.0 与 v1.1 并存，v1.1 仅新增节点级可选 `run_when`）。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workflow_id` | string | 是 | 工作流 id（`^[A-Za-z0-9_-]+$`） |
| `description` | string | 否 | 人类可读描述 |
| `nodes` | array\<node\> | 是 | ≥1 个节点（`depends_on` 内联隐式边表） |
| `output_node` | string | 是 | 输出节点 id：其结果作为整个工作流的返回值 |

**node 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | 是 | `^[A-Za-z0-9_-]+$`（工作流内唯一） |
| `agent_type` | string | 是 | `^[A-Za-z0-9_-]+$`（对应 `agents/<type>.json`） |
| `task` | string | 否 | 静态任务描述（与 `task_template` 二选一，同时提供时后者优先） |
| `task_template` | string | 否 | 可含 `{node_id}` 占位符，执行期被上游结果替换 |
| `depends_on` | array\<string\> | 否 | 依赖节点 id 列表；环在拓扑排序期拒绝 |
| `run_when` | object | 否 | **v1.1** 条件分支：`{ node, op, value }`；求值为假 → 跳过本节点，直接依赖被跳过节点的下游级联跳过（豁免需下游显式声明自己的 `run_when`） |

**run_when 子字段（v1.1）**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `node` | string | 是 | 被观察节点 id（须位于本节点更早拓扑层；被跳过时视作空字符串） |
| `op` | enum | 是 | `contains` / `equals` / `not_contains` |
| `value` | string | 是 | 期望值（与上游结果字符串比较） |

**完整例子**: `examples/workflow_dag.example.json`（v1.0）、`examples/workflow_dag_v1.1.example.json`（v1.1）

## kind: service_registry

服务注册 / HTTP 路由。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `services` | array\<service\> | 是 | ≥1 个服务 |

**service 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `name` | string | 是 | `^[a-z][a-z0-9_]*$` |
| `endpoint` | string (uri) | 是 | 完整 URL |
| `method` | enum | 否 | `GET` / `POST` / `PUT` / `DELETE` / `PATCH` / `WS` |
| `auth` | enum | 否 | `none` / `api_key` / `oauth2` / `mtls` / `internal` |
| `rate_limit` | integer | 否 | 每秒请求数上限,0 = 无限 |
| `timeout_ms` | integer | 否 | 超时毫秒数 |

**完整例子**: `examples/service_registry.example.json`

### D2 sidecar 标注模式（service_registry 特有）

service_registry 允许"主体零改动"的标注方式：主体文件保持纯对象映射（不含 5 顶层字段），治理标注（`$schema` / `kind` / `id` / `version` / `metadata`）放在同名 `<主体>.meta.json` sidecar 中：

- `evorule-migrate validate <主体文件>` 自动探测并合并 sidecar 后校验，成功输出 `[sidecar merge: ...]` 标记；
- `.meta.json` 不能单独校验——它只是标注层，不是完整文档；
- sidecar 中 `body` / `body_format` / `body_note` 是说明性字段，不参与合并与校验；
- **禁止把标注字段直接写进主体**：engine 加载器会把它们当服务名解析。

## kind: knowledge

知识库条目(RAG 文档集合)。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `entries` | array\<entry\> | 是 | ≥1 个条目 |

**entry 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | 是 | `^[A-Za-z0-9_.-]+$` |
| `title` | string | 否 | ≤ 200 字符 |
| `content` | string | 是 | 知识内容 |
| `category` | string | 否 | 分类 |
| `severity` | enum | 否 | `info` / `warning` / `error` / `critical` |
| `related` | array\<string\> | 否 | 相关条目 ID |
| `embedding_ref` | string | 否 | embedding 存储引用 |

**完整例子**: `examples/knowledge.example.json`

## kind: migration

`$schema` 升级迁移规则(自举核心)。

**body 字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `from_version` | string | 是 | `^v\d+\.\d+$`,起始 $schema 版本 |
| `to_version` | string | 是 | `^v\d+\.\d+$`,目标 $schema 版本 |
| `transforms` | array\<transform\> | 是 | ≥1 个 transform |

**transform 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | 是 | `^M\d{3,6}$`,migration 内唯一 |
| `title` | string | 否 | ≤ 200 字符 |
| `description` | string | 否 | ≤ 2000 字符 |
| `when` | object | 是 | evorule when 表达式 |
| `then` | object | 是 | evorule then 表达式 |

**完整例子**: `examples/migration.example.json`

## 验证当前 schema 是否生效

```bash
python tools/evorule-migrate list-kinds
# 期望输出:6 个 kind + 各自的版本
```

## 延伸阅读

- [version-protocol.md](./version-protocol.md) — `$schema` 与 `version` 的关系
- [cli-reference.md](./cli-reference.md) — 怎么用工具校验 schema
- [设计规范(五顶层字段)](../adr/five-top-level-fields.md) — 5 顶层字段规范
- [设计规范(顶层 body)](../adr/semantic-body-fields.md) — 顶层 body 字段语义化

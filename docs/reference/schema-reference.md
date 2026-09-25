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

evorule agent 定义（v1.0/v1.1 并存；v1.0 真值 = `system_prompt` 内联、`model`/`temperature` 平铺顶层——原 D5 草案的 `capabilities`/`prompt_ref`/`model_config` 已被真实结构否决）。

**body 字段（v1.0）**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_type` | string | 是 | `^[A-Za-z0-9_-]+$`（文件名 `agents/<agent_type>.json`，防路径穿越） |
| `version` | string | 是 | 定义内容版本号 |
| `description` | string | 是 | ≥1 字符 |
| `system_prompt` | string | 是 | 内联 system prompt 全文 |
| `model` | string | 是 | 模型名 |
| `temperature` | number | 是 | ∈[0,2] |
| `max_steps` | integer | 是 | ≥1 |
| `step_timeout_secs` | integer | 是 | ≥1 |
| `tools` | array\<string\> | 是 | 可用工具清单 |
| `memory` | object | 否 | 内存配置（type: none\|persistent 等） |
| `output_format` | object\|null | 否 | 输出格式配置 |
| `context_window_tokens` | integer | 否 | 上下文窗口 token 数（≥1，默认 8192） |
| `max_parallel_tools` | integer | 否 | 单轮并行工具调用上限（≥1，默认 1 = 串行） |

**v1.1 增量字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `capability_boundary` | object | 否 | 能力边界声明：`{ mode: "read_only"\|"read_write", sandbox_root: string(绝对路径), tools: array\<string\> }`（三键必填）。声明是 file 类工具沙箱检查的唯一权威；会话建立时注入边界事实（agent 自知边界）。语义约束（加载侧门卫）：顶层 `tools` 中沙箱类工具必须列于 `capability_boundary.tools`；`mode=read_only` 时不得含 `file_write`。未声明 = 行为同 v1.0（启动配置合成缺省边界） |

**完整例子**: `examples/agent_def.example.json`（v1.0）/ `examples/agent_def_v1.1.example.json`（v1.1）

## kind: workflow_dag

DAG workflow 定义（对齐 evo-agent Workflow 引擎；v1.0/v1.1/v1.2 并存：v1.1 新增节点级 `run_when`，v1.2 新增顶层 `loops` 循环原语与节点级 `compute` 纯函数节点）。

**body 字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workflow_id` | string | 是 | 工作流 id（`^[A-Za-z0-9_-]+$`） |
| `description` | string | 否 | 人类可读描述 |
| `nodes` | array\<node\> | 是 | ≥1 个节点（`depends_on` 内联隐式边表） |
| `loops` | array\<loop\> | 否 | **v1.2** 有界循环原语（加载/物化阶段静态展开为线性副本链，命名 `{loop_id}_iter{k}_{node_id}`；不支持嵌套） |
| `output_node` | string | 是 | 输出节点 id：其结果作为整个工作流的返回值（可引用展开后副本名） |

**node 子字段**:

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `id` | string | 是 | `^[A-Za-z0-9_-]+$`（工作流内唯一；loop.id 占用同一命名空间） |
| `agent_type` | string | 条件 | `^[A-Za-z0-9_-]+$`（对应 `agents/<type>.json`）；**v1.2 起条件必填**：节点无 `compute` 时必填，含 `compute` 时禁止 |
| `task` | string | 否 | 静态任务描述（与 `task_template` 二选一，同时提供时后者优先）；含 `compute` 时禁止 |
| `task_template` | string | 否 | 可含 `{node_id}` 占位符，执行期被上游结果替换；循环体内可含 `{prev.X}`；含 `compute` 时禁止 |
| `depends_on` | array\<string\> | 否 | 依赖节点 id 列表；环在展开后拓扑排序期拒绝 |
| `run_when` | object | 否 | **v1.1** 条件分支：`{ node, op, value }`；求值为假 → 跳过本节点，直接依赖被跳过节点的下游级联跳过（豁免需下游显式声明自己的 `run_when`）；**v1.2** 起 `node` 允许 `prev.X`（仅循环体内，观察上一迭代副本） |
| `compute` | object | 否 | **v1.2** 纯函数节点声明（见下） |

**loop 子字段（v1.2）**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 循环 id（展开命名前缀；不得与节点 id 冲突） |
| `max_iterations` | integer | 是 | 静态迭代上界（1..=32，冻结限额） |
| `body` | array\<node\> | 是 | 循环体节点 1..=8 个（即 node 形态，可含 compute/run_when/prev. 引用） |

**compute 子字段（v1.2）**: 封闭函数目录（新增函数 = 新 schema 版本 + 治理评审）；不经 delegate、无 IO 无副作用。结果词表：`strcmp(equal)`→`equal\|different`、`strcmp(contains)`→`contained\|not_contained`、`numeric_cmp`→`true\|false`、`regex_match`→`match\|no_match`。收敛门控规范习语：后续迭代首节点 `run_when: { node: "prev.<check节点>", op: "not_contains", value: "equal" }`（iter0 空结果语义天然放行首轮）。

**run_when 子字段（v1.1）**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `node` | string | 是 | 被观察节点 id（须位于本节点更早拓扑层；被跳过时视作空字符串）；**v1.2** 允许 `prev.X` |
| `op` | enum | 是 | `contains` / `equals` / `not_contains`（自 v1.1 冻结） |
| `value` | string | 是 | 期望值（与上游结果字符串比较） |

**完整例子**: `examples/workflow_dag.example.json`（v1.0）、`examples/workflow_dag_v1.1.example.json`（v1.1）、`examples/workflow_dag_v1.2.example.json`（v1.2）

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

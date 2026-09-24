# 变更日志

所有 evorule-system-rules 的显著变更都记录在这里。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.2.0] - 2026-09-24

### 新增
- `workflow_dag/v1.2` schema（plan-execute 动态循环前置能力，双版本协议次版本增量，v1.0/v1.1 存量零迁移）：
  - 顶层可选 `loops`：有界循环原语（`max_iterations` 1..=32、循环体 1..=8 节点），加载/物化阶段静态展开为线性副本链（命名 `{loop_id}_iter{k}_{node_id}`），展开后仍是纯 DAG；不支持嵌套（本版本冻结）
  - 节点级可选 `compute`：纯函数节点（封闭函数目录首发 `strcmp`/`numeric_cmp`/`regex_match`；不经 delegate、无 IO、无副作用；结果词表 `equal|different`、`contained|not_contained`、`true|false`、`match|no_match`；收敛门控规范习语 `not_contains "equal"`）
  - 节点引用 pattern 扩展 `prev.` 前缀：循环体内跨迭代引用上一迭代副本（仅循环体内合法，iter0 空结果语义）
  - `node.agent_type` 由恒必填放宽为条件必填（含 `compute` 时禁止 `agent_type`/`task`/`task_template`）——唯一 required 语义修改
- 示例 `examples/workflow_dag_v1.2.example.json`（有界循环 + compute 收敛门控）
- `evorule-constitution` crate 0.3.0：内嵌 v1.2 schema（build.rs 清单 + EMBEDDED 表随动）

### 评审与修正
- v1.2 草案经项目方批准（含 agent_type 条件化放行、compute 结果词表冻结）；实施期修正：strcmp(equal) 输出 `not_equal` → `different`（原词表下 `not_contains` 无法区分收敛态，收敛提前退出不可表达；词表冻结承诺不变）
- schema 正反用例 13/13 通过（含 compute 与 agent_type/task 互斥封口）；v1.0/v1.1 示例在 v1.2 下仍合法（纯增量证明）

## [v1.1.0] - 2026-09-19

### 新增
- `workflow_dag/v1.1` schema：节点级可选条件分支字段 `run_when`（`{ node, op, value }`，谓词最小集 `contains`/`equals`/`not_contains`）。求值为假跳过本节点；直接依赖被跳过节点的下游级联跳过，豁免需下游显式声明自己的 `run_when`。依据双版本协议属次版本新增可选字段：v1.0 存量 JSON 零迁移可用
- 示例 `examples/workflow_dag_v1.1.example.json`（条件发布工作流）

### 修正
- `docs/reference/schema-reference.md` workflow_dag 段：移除残留的未采纳草案描述（独立 `edges[]` 数组 + `node.type` 枚举），对齐真实 body 模型（内联 `depends_on` 隐式边表）并补充 `run_when`

## [v1.0.0] - 2026-08-27

### 固化
- 6 个 kind 的 v1.0 schema 正式发布(rule_set / agent_def / workflow_dag / service_registry / knowledge / migration),与 v0.9 双版本并存,迁移线 `v0.0-to-v0.9`、`v0.9-to-v1.0`
- 新增共享定义包 `schemas/_shared/`(transform_rule / instruction 等 `$defs`,供各 kind 引用)

### 法律与 IP 分离模型
- 全部 schema 注入机器可读声明字段 `x_legal_authority_notice`(AGPL-3.0-or-later + 商业双许可;经 schema 校验或创作的内容 IP 归作者,evorule 不主张)
- 新增法律文件体系:LEGAL_NOTES / NOTICE / DUAL_LICENSE / COMMERCIAL_LICENSE / FREE_COMMERCIAL_LICENSE / TRADEMARK,设计依据见 `docs/adr/scope-split-ip-model.md`

### 规则格式统一改造
- yuanze_rules.json 等真实资产对齐 5 顶层字段 + v1.0(修复单数 `__io_result__` → 复数 `__io_results__`、非法元指令 save_memory 下线)
- examples 全部升级为 v1.0 形态;service_registry 采用主体+`.meta.json` sidecar 标注
- `_verify_schemas.py`:15 schema 合法性 + 门禁正负用例 + examples 闭环 + 白名单四向一致的全量验收基准

### 工具与守卫
- 新增 `tools/check_whitelist_sync.py`(6 元指令白名单四处同步守卫)与 `tools/check_docs_links.py`(docs 相对链接守卫)
- 新增 `_empirical_interception.py`(Opt1-4 拦截实证矩阵 × yuanze-demos)
- server 内嵌副本同步守卫 `check_schema_sync.py --sync`(双向:check / sync)
- 2026-08-27 收编:`_verify_schemas.py` → `tools/verify_schemas.py`(根目录保留薄 shim);`check_docs_links.py` 改为锚定仓根,不受 cwd 影响;新增一键预检 `verify-all.ps1`;CLI 支持 service_registry D2 sidecar 合并校验

### 文档
- Diátaxis 结构重整:theorem→tutorial / how-to / reference / explanation 四象限 + ADR 已定型规范格式


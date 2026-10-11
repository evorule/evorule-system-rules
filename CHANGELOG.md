# 变更日志

所有 evorule-system-rules 的显著变更都记录在这里。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.5.0] - 2026-10-11

### 新增
- `_shared/v1.0` 新增 `llm_verdict` $def（LLM 判定事实载荷 v1.0，向后兼容新增——存量 `$ref` 不受影响，无需迁移）：LLM 在 agent 层完成语义判定后的事实化结构（kind/key/verdict/value/confidence/evidence/prompt_hash/model/origin 九字段，`additionalProperties:false`，`verdict:"value"` 条件必填 `value`）。设计原则：`confidence`/`origin` 不参与确定性求值面（不确定性不得写成规则条件阈值假象）；`prompt_hash` 保溯源不承诺可复现；本 def 为校验层定义，不改变引擎已消费的机器语义（schema-evolution-sop 红线合规）。消费面：evorule-rule 事实条目 `schema_ref`、evo-agent 判定产出侧；规则面经 payload 注入以现有 `exists`/`eq` 原子消费，引擎零 LLM 依赖
- `docs/reference/schema-reference.md` 新增「共享定义（_shared/v1.0）」节（llm_verdict 字段表+消费面说明）

### 修正
- `tools/scan_repo_json.py` 豁免清单 + `docs/explanation/04-governance-scope.md` 豁免表补登记 `evorule-tcb/discipline/`（governance 内核 L2 shape gate 直接消费的裸数组纪律门禁，非系统 JSON 加载通路；入仓时漏同步豁免，verify-all 实测暴露）

### 随动
- `evorule-constitution` crate 0.3.3：`include_str!` 内嵌 `_shared/v1.0.json` 内容自动跟随（坏 JSON 编译期即失败，自带门禁），版本号随内容变更递增

## [v1.4.0] - 2026-10-07

### 新增
- `workflow_dag/v1.3` schema（compute 纯函数目录扩展，双版本协议次版本增量，v1.0/v1.1/v1.2 存量零迁移，四版本并存）：函数目录由 3 种扩展为 27 种，新增 24 种——算术 `add/sub/mul/div/abs/min/max`（i64 域，div 零=节点失败）、字符串 `concat/length/upper/lower/trim/replace/split_at/substr/join`（按 Unicode char 计数与索引，字面操作非正则）、日期 `epoch_to_date/date_diff_days/epoch_add_days`（仅 UTC、仅显式入参、日期域 0000-01-01..=9999-12-31，无本地时区无当前时间函数——确定性红线）、逻辑 `and/or/not/if_else/clamp`（条件值取封闭布尔词表 true|false，不隐式真值化）
- 错误语义总纲（全目录统一 fail-fast，沿用 numeric_cmp 既有口径）：数值解析失败/除零/整数溢出/索引越界/日期域外/条件值不在词表/分隔符或查找串为空 = 节点失败 = 工作流终止，无静默回退
- 示例 `examples/workflow_dag_v1.3.example.json`（事件台账解析：拆列/归一化/UTC 日期推导/布尔联检，7 个新函数与既有函数组合）
- `docs/reference/schema-reference.md` workflow_dag 段随动（v1.3 增量、词表总表、常量参数位置规范）
- `evorule-constitution` crate 0.3.2：内嵌 v1.3 schema（build.rs 清单 + EMBEDDED 表随动）

## [v1.3.0] - 2026-09-25

### 新增
- `agent_def/v1.1` schema：顶层可选 `capability_boundary`（能力边界声明：`{ mode: "read_only"|"read_write", sandbox_root, tools }` 三键必填）。声明是 file 类工具沙箱检查的唯一权威；会话建立时注入边界事实（agent 自知边界）。依据双版本协议属次版本增量：v1.0 存量 JSON 零迁移可用（未声明 = 行为同 v1.0）
- 示例 `examples/agent_def_v1.1.example.json`（read_only 边界声明）
- `evorule-constitution` crate 0.3.1：内嵌 v1.1 schema（build.rs 清单 + EMBEDDED 表随动）

### 修正
- `docs/reference/schema-reference.md` agent_def 段：移除残留的未采纳草案描述（`capabilities`/`prompt_ref`/`model_config`——2026-08-27 已被真实结构否决），对齐 v1.0 真值（`system_prompt` 内联、`model`/`temperature` 平铺）并补充 v1.1 增量字段

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


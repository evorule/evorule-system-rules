<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 宪法的管辖边界：什么受治、什么豁免

> 本文回答一个问题：是不是仓库里的每一个 `.json` 都必须过 6 个 kind 的门？
> 答案是否定的。边界不清，宪法就会变成形式主义——把工具内部状态文件强行
> 套上治理外壳，除了制造噪音什么也得不到。

## 管辖对象

宪法治理的对象是**evorule 平台加载执行的系统 JSON**：

- 由 evorule 引擎 / evorule-server / evorule-rule 等运行时在启动或运行期加载；
- 参与确定性执行的规则、路由、流程、知识注入等；
- 其形态错误会导致运行时故障（这正是提交期拦截存在的意义）。

这类文件必须携带 5 顶层字段 + 合法 `$schema`，并通过对应 kind schema 校验。

## 豁免判据

一个 JSON 文件**豁免**出宪法管辖，当且仅当它满足以下全部判据：

1. **不被引擎加载执行**——只被开发工具、CI 脚本、文档系统读取；
2. **不参与确定性执行链路**——它的内容出错不会导致引擎行为偏差；
3. **生命周期由其消费工具自管**——格式演进由该工具自己的测试守护，
   不需要跨仓版本协议协调。

豁免是**状态而非身份**：同一个路径的文件今天豁免，明天一旦被引擎加载
（例如 PITFALLS.json 未来作为 knowledge 注入 RAG），就必须立即入管辖、补壳。
反方向亦然——被移出执行链路的文件应退出治理而不是背着一具空壳。

## 当前已知豁免清单

| 文件 | 所属 | 定性 |
|------|------|------|
| `docs/PITFALLS.json`（evorule-server 仓） | server | 工具/文档内部资产（`$schema: pitfalls-v1` 为该工具自造标识），由坑位守卫脚本读取，不经引擎。若未来作为 knowledge 注入运行时，须改造为 knowledge kind 并入辖 |
| `acceptance/t6_e2e/*.bak` 等验收夹具 | 本仓 | 测试夹具随所属测试套演进,非系统 JSON |
| `evorule-cli/tests/fixtures/**/*.json`（8 文件） | 根仓 | 测试夹具（2026-08-27 判定）：仅被 CLI 测试进程加载（`io_util::load_rules→extract_transforms`），不进生产执行链路；全部为裸 `{"transform":[...]}` 原生体，其中 `invalid/`、`unknown-type/` 是**负向夹具**——无壳/非法正是其测试语义，补壳反而破坏用例。由扫描门禁白名单承载（tools/scan_repo_json.py EXEMPT_PATTERNS）。若未来 fixtures 被提升为示例资产则重新判定 |
| `core/rule_schema/schemas/**/*.json` | server | schema 权威文件自身（2026-09-15 存量清零判定）：自指问题（schema 不能引用自己），由 check_schema_sync + verify_schemas 守护，生命周期随宪法仓版本演进自管 |
| `signatures/version1/cla.json`（server / evo-agent） | server / evo-agent | CLA 签署台账（顶层签署条目数组）：法律记录，非系统 JSON；生命周期由合规流程自管 |
| `.markdownlint.json` / `sdk/nodejs/package.json` | server / evo-agent | 开发工具配置（lint / npm），仅被开发工具读取，不经任何加载执行路径 |
| `plugins/**`、`plugin_manifest.json`、`service_registry.json` | server | 插件系统自有契约资产（2026-09-15 存量清零判定）：plugin.json contract_version 体系 + pack 装载 6 项硬校验 + r2_gate 属地执法，加载门禁比 schema 壳更细；生命周期由插件契约演进自管 |
| `rules/bundles/*/bundle_manifest.json` | server | bundle 落盘溯源 manifest（2026-09-15 存量清零判定）：bundle_land.rs 明确「不参与 loader 加载路径」，仅溯源/运行配置元数据；**条目文件已于 2026-09-15 全部带壳**（rule_set v1.0）并补 批次F 逐条目 content_hash 基线；顶层 content_hash 保留为导入时溯源记录 |
| `agents/*.json`、`rules/workflows/*.json` | evo-agent | 属地执法形态（2026-09-15 存量清零判定）：运行时经 constitution.rs 用 agent_def/workflow_dag v1.0 schema 校验裸 body（见下文属地执法义务表 evo-agent 行）；带壳反而与裸 body 运行时契约冲突。若未来校验降级失效，立即重新入辖 |
| `evorule-wasm-demo/plan.json` | 根仓 | wasm 演示测试向量（bench/test 脚本夹具）：仅被演示 harness 读取；构建产物 `rules_merged.json` 已 gitignore 退出门禁面 |

新项目引入"长得像系统 JSON 但其实不是"的文件时，应在本表登记而非默认入辖。

## 属地执法义务：谁消费，谁校验

豁免表回答"什么不必带壳";本节回答它的孪生问题——**凡是消费受治 JSON 的应用,必须在自身的加载路径上挂接宪法校验**。这与豁免并不矛盾:豁免决定资产要不要治理,属地执法决定消费者有没有执法义务。

**为什么要多点位而不是 server 单点**:server 的校验点只覆盖流经其 API 与热载管线的文件;应用本地加载的资产(如 evo-agent 的 `agents/*.json`、workflow 文件)不经任何 server 路径。多点位的必要性已由实证确认——evo-agent 侧拦下的 `agent_type` 路径穿越(2026-08-27 M7)在纯 server 门禁下永远不可见。

**义务的构成**(三条同时成立才算落挂):

1. **使用共享校验实现**——判定逻辑来自统一组件(`evorule-constitution` crate(已落地:0.2.0 起 schema 编译期内嵌;crates.io 发布前以 git 依赖+rev 钉版消费)或既有 core/rule_schema),禁止各应用复制第二份判定代码;应用差异只允许出现在接入点与缺失时的业务策略;
2. **schema 数据走 SSOT**——优先经共享 crate 的编译期内嵌数据(include_str! 直读宪法仓 `schemas/` 母本,同仓 SSOT);跨仓内嵌副本(如 server core/rule_schema)须登记进 `check_schema_sync.py` 同步清单;
3. **降级语义合规**——统一组件以 `Policy` 双模式承载(2026-09-22 收编裁定,与约束总表 §H 并存):缺省 `Strict`=schema 不可得即 fail-fast 拒绝(门禁语义,对齐 §H);非门禁消费方显式选用 `Lenient`=`warn + 最小结构门卫兜底`放行,不许静默空窗。内嵌模式下数据恒可得,"不可得"仅发生于显式目录模式指错路径——此时按 policy 分派,缺省拒绝。

**例外及其依据**:

| 消费方 | 状态 |
|--------|------|
| evorule 核心仓(evorule/evorule-tcb/governance 等) | 豁免本义务——代偿机制更强:TCB 运行期严格拒绝(未知指令当场拒收)承诺执行语义正确性,资产级发布审批(core_eval 流程)承诺来源正确性;两者合起来比 schema 预检更硬。**core 内部件因此恪守最小化**:governance 只做元指令白名单检查(审计链本职),刻意不承担 schema 全量校验——把重依赖与外部数据资产挡在核心仓之外是设计而非欠缺 |
| evorule-server | ✅ 已达标(API 校验点 + hot_reload 逐文件门禁 + 副本同步守卫) |
| evo-agent | ✅ 已达标(`src/agent/constitution.rs` 薄封装委托统一 crate `evorule-constitution`;M7 落地,2026-09-22 收编后判定代码单一化) |
| evorule-governance | ✅ 设计如此(见上表核心仓行):仅做元指令白名单,不补 schema 校验——曾误列为"半位缺口",2026-08-27 经项目方澄清为刻意设计并更正 |
| 后续新应用(evorule-rule、白标实例) | 出生即带:项目模板内含共享 crate 依赖与最小接入 |
| 运行宪法的属地分发(T8,2026-08-27) | 确立模式:核心仓 `core_eval.json` 仅承载引擎自评最小集(v0.4.0,原子+控制流+兜底);ReAct 等**应用剧本由消费方自持**——evo-agent 自带 `assets/agent_constitution.json`(app.evoagent.agent),示例应用自带 assets 副本,部署侧经 `paths.core_eval`/`--core_eval` 指向自有宪法。消费方测试夹具同样遵守本义务(不跨仓引用他仓资产) |

## 常见误用

- ❌ "保险起见给所有 JSON 都加 5 顶层字段" ——工具内部状态文件加壳后，
  两套格式约束互相打架，且暗示了它并不具备的执行语义；
- ❌ "反正没人校验，先用自造 $schema 顶着" ——自造标识合法的前提是
  文件处于豁免区并有明确登记；一旦进入加载路径就是违宪；
- ✅ 正确姿势：先回答"谁加载它"，再决定壳的类型。

## 与三层治理模型的关系

见 [3 层治理模型](01-three-tier-governance.md)。管辖边界是三层的先行判据：
先判定文件是否属于平台层管辖对象，才谈得上它落在哪一层。

## 延伸阅读

- [五顶层字段规范](../adr/five-top-level-fields.md)
- [IP 分离模型](../adr/scope-split-ip-model.md)（法律维度的边界,本文是技术维度的边界）

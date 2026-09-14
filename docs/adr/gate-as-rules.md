<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# ADR: 门禁即规则(Gate-as-Rules)——格式门禁的热加载迁移设计

> 状态:草案 v0.1(2026-08-27),送评审,未批准前不得实施。
> 背景:立项计划 M8/G1 条目与 T3 台账条目(内部决策记录,随本仓公开版不发布)。

## 是什么

本规范定义**格式门禁(gate)的两层拆分**:判定内容(JSON 数据,热加载即时生效)与判定引擎(Rust 内核,编译期固化)。目标是让最常被调整的门禁规则——白名单、数值范围、必填集、注册表——脱离编译域,复用 evorule 既有的热加载与确定性执行基建;同时明确**表达力边界**:JSON 数据无法承载图灵完备判定,凡超出边界者必须留在内核,这不是缺陷而是确定性保证的一部分。

### 边界声明(本文档的根本约束)

| 层 | 内容 | 可否热加载 | 理由 |
|----|------|-----------|------|
| L0 内核 | 门禁求值器:比较运算、类型谓词、受限 pattern 匹配(见 Q1)、确定序遍历、"政策不可触及执行态"不变量 | 否(编译固化) | 这些是"校验器自身正确性"的一部分;校验器若可被数据改写语义,全部下游保证失效 |
| L1 政策 | 新增 `gate_policy` kind:版本/枚举白名单、数值区间、必填字段集、`io_type` 注册表、kind→schema 绑定表、豁免清单 | 是(磁盘文件,变更即时生效) | 高频调整项;调整它们不应触发任何仓库的重编译 |
| L2 参数化护栏 | 深度上限、指令数上限等执行器,**代码实现不变,阈值取自 L1** | 部分(参数热载) | 循环/递归检查算法属正确性机制;当前阈值(如 MAX_BRANCH_DEPTH=64)若需按部署调优,改数据即可 |
| L3 交互反馈 | 编辑期 dry-run CLI、提交期 lint(`evorule-migrate validate` 的政策化演进)、CI 抽检 | — | 把同一套 L1 政策喂给不同入口,实现"错误挡在编码前"的前移 |

### 必答四问

**Q1 内核最小集形式化清单**(哪些检查永远留在 Rust):

1. 值域运算:数值区间、枚举成员、等值比较;
2. 结构谓词:必填键存在性、JSON 类型判定、数组长度界;
3. 受限 pattern 匹配,仅三种且均为线性时间、零回溯、天然终止:字面前缀(`starts_with`)、字面后缀、字符类白名单(如 `^[A-Za-z0-9_-]+$`);
4. 遍历确定性:对文档树和政策表的一切遍历采用 `BTreeMap` 序;
5. 纯函数封闭性:求值函数的输入仅为(被检文档, 政策文档),禁止读取时钟、环境变量、网络或其他数据集——政策不可自适应、不可级联。

不在清单内的判定能力,**不支持**,包括:正则表达式(存在灾难性回溯风险)、任意字符串计算、政策内定义循环或递归、跨文档 join(v1 明确不做;引用其他数据集内容做判定会使"这份政策当次判定依赖哪个数据集版本"变得不可静态回答,破坏重放一致性)。确有需要时,升级为内核中经过审查的新原语,而不是放开政策语言。

**Q2 政策数据用什么 kind**:新增 `gate_policy`,不复用 `rule_set`。理由:`rule_set` 的 body 语义是给 TCB executor 执行的业务变换(5 元指令;`collect`/`merge` 已于 v0.6.0 退役),而门禁判定的对象是*文档形态*,生命周期也不同——rule_set 变更走发布审批,gate_policy 变更是运维调参,审批级别应当分离。body 采用声明式条目:

```json
{
  "policy_id": "com.example.gate.default",
  "entries": [
    {
      "id": "agent_def-temperature-range",
      "target": { "kind": "agent_def", "path": "/temperature" },
      "check": { "type": "number_range", "min": 0.0, "max": 2.0 },
      "severity": "error",
      "message": "temperature must be in [0, 2]"
    },
    {
      "id": "io-type-registry",
      "target": { "kind": "transform", "path": "/io_request/io_type" },
      "check": { "type": "enum", "values": ["http_get", "llm_call"] },
      "severity": "error"
    }
  ]
}
```

`check.type` 枚举由 L0 固化(v1 仅六种:`number_range` / `enum` / `required_keys` / `string_prefix` / `charset_whitelist` / `array_length`),新增类型须修订本 ADR。`gate_policy` 自身受固定 schema 校验(schema 由内核持有,不经政策改写——防自举陷阱)。纳入第四份同步清单([check_schema_sync.py](../../../evorule-server/scripts/check_schema_sync.py) 现管三份)。

**Q3 差分退出准则**(如何证明迁移没有改变行为):影子模式先行。新引擎与旧 Rust 门禁在每个检查点双跑,只记差异不拦截;观测指标 `gate_dual_run_total{verdict}` 区分四种组合。切换条件同时满足:连续 ≥7 个自然日、组合 `new_fail ∧ old_pass` 计数为 0(零漏报硬性要求)、总差异率 < 0.5%。满足后翻转拦截权,旧路径保留一个版本周期作为回退位,随后删除(不留双轨死代码)。

**Q4 冷启动顺序**:进程启动时 (a) 装载编译期内置的最小 fallback 政策(`include_str!` 打包,内容等同现有 Rust 门禁行为);(b) 扫描 `policies/*.json`,逐个过 gate_policy schema,合法者按文件名序合并覆盖;(c) 任一文件非法则拒载该文件并 `tracing::warn`,其余文件照常,全无可载时退回 fallback——任何时候都不允许"半个政策"生效或静默空窗。每次政策装载经 [shared_facts_log::append](../../../evorule/evorule-governance/src/shared_facts_log.rs) 写入事实流,purpose=`gate_policy_reload`,达成政策变更可审计。

### 落地挂点(均已核实存在,无需新建基建)

- server 热加载管线 [hot_reload/loader.rs](../../../evorule-server/core/hot_reload/src/loader.rs):已有逐文件解析→校验→fail-soft 过滤的模式,政策文件目录接入此管线即为即时生效;
- 提交期硬校验双路:bundle 导入 [api/server.rs](../../../evorule-server/evorule-server/src/api/server.rs)(fail-fast)与编辑期 CLI;
- evo-agent 侧的 `src/agent/constitution.rs`(见该仓库)已建立"schemas 缺失→warn 降级"先例,L1 缺失时的降级行为与其同构。

## 为什么

- 一致性:evorule 的核心主张是"规则即数据,改完即生效",门禁却是整个体系里唯一"改一次要重编译三个仓库"的逻辑——高频调整点恰好停在成本最高的位置;
- 安全:白名单、注册表、阈值恰恰是运营中最常被要求改的内容,留在数据层使每次改动产生一条可审计事实,优于散落在 git diff 里;
- 错误前置:同一份 L1 政策同时驱动 CI(提交后)与编辑期 dry-run(提交前),形成编码前拦截闭环;
- 风险可控:L0 清单把正确性敏感部分钉死在编译期,政策热载只交换"值",不交换"语义";影子模式的零漏报硬门槛防止迁移引入漏检。

## 怎么用

本 ADR 为设计规范,实施分三阶段(每阶段独立可验收,顺序固定):

1. P1 影子期:server 内并行装配 shadow 引擎与默认政策集(从现有 Rust 门禁逆向成 `gate_policy` 条目),双跑采 diff;
2. P2 切换期:达到 Q3 准则后翻转拦截权;同步输出编辑期 dry-run 子命令(`evorule-migrate lint`);
3. P3 收敛期:CI 由每 PR 全量校验降为抽检+夜审;各仓保留的内联检查(sysl-level 白名单等)逐一核对是否已入 L1,清点存余。

实施时遵循:政策条目必须有对应负向测试样例;每阶段完成后更新本文件的状态行并登记台账。

## 不接受的替代方案

- 政策语言图灵完备化(允许正则、自定义函数、跨文档 join):破坏"校验器自身正确性可静态证明"的前提,v1 明确拒绝,扩展途径只有内核新原语;
- 用 `rule_set` 兼容承载门禁(不新增 kind):混淆运维调参与发布审批两条治理线,且 body 语义会被 5 元指令执行器误解,增加不确定性而非消除;
- 无影子期直接切换、或以"测试通过"代替真实流量差分:零漏报要求只能靠生产流量证明,单测覆盖不了未知分布。

## 引用

- 计划与决策:立项计划 G1"表达力边界"四层裁决表、T3 台账及 S3(server 下发侧校验平移)条目(内部决策记录,随本仓公开版不发布)
- 相关 ADR:[bootstrap-termination.md](bootstrap-termination.md)(L0 终止性保证来源)、[double-version-protocol.md](double-version-protocol.md)(kind 版本策略)

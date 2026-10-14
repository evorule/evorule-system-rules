<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 受约束者一页导览

> 本页是宪法条文的**钥匙面**（[CON-K1-001]）：按你的角色分流,告诉你受哪些条文约束、
> 正本在哪、本地一敲即验的命令是什么、最常见的错误长什么样。
> 所有宪法相关报错的「→ 导览」尾段都指向本页（[CON-K1-002]）。

条文 ID（如 `[CON-L1-001]`）是宪法条文的稳定引用标识；条文正本由项目方维护,
公开面的**形态正本**就是本仓 `schemas/` 树与下列文档节。

---

## 规则作者

你写 `rule_set`（业务规则 / transform 规则）。报错撞到你身上的每一行,都对应一条钥匙条文。

**受约束条文**

- `[CON-L0-001]` $schema 头强制 —— 每份文档首键必须是 `$schema`
- `[CON-L1-001]` 写入门禁 —— 保存/发布前的 schema 校验门
- `[CON-L1-002]` 拒收即向导 —— 拒收报文必须是四段式（违什么/在哪/正本/正确形态）
- `[CON-K2-002]` 正确样例最小化 —— 报错第④段给最小可过样例
- `[CON-K3-002]` 脚手架命令 —— `new` 生成合法骨架起步
- `[CON-K4-001]` 本地一敲即验 —— CLI 三态退出码（0 绿 / 1 违规 / 2 工具错）

**正本**

- 形态正本：[schemas/rule_set/v1.0.json](../schemas/rule_set/v1.0.json) 与 [schemas/_shared/v1.0.json](../schemas/_shared/v1.0.json)
- 手册：[规则设计与非法限制手册](reference/illegal-restrictions-manual.md)、[6 个 kind 的 schema 字段](reference/schema-reference.md)

**本地校验**

```bash
# 单文件 / 目录 / 严格模式（警告即违规）
evorule-rule-tools validate --file your_rule.json
evorule-rule-tools validate --dir rules/ --strict

# 从骨架起步（生成物已过校验器）
evorule-rule-tools new --kind rule_set --out rules/my_rule.json

# 无 CLI 环境时,用本仓迁移工具校验
python tools/evorule-migrate validate your_rule.json
```

**三大常见错误**（金样例非法对,点击看违规形态）

1. `eq` 域缺必填 `value` —— [domain.invalid.json](../acceptance/golden/rule_set/domain.invalid.json)（`allOf` if/then required 拒绝）
2. `instructions` 空数组 —— [instruction.invalid.json](../acceptance/golden/rule_set/instruction.invalid.json)（`minItems` 拒绝）
3. `path` 尾点空段（`"x."`）—— [path.invalid.json](../acceptance/golden/rule_set/path.invalid.json)（pattern 拒绝）

---

## 板块开发者

你把系统 JSON（`workflow_dag` / `service_registry` / `knowledge` / `agent_def`）嵌进自己的应用或工作流。

**受约束条文**

- `[CON-L0-001]` $schema 头强制
- `[CON-L0-002]` 编辑器关联生效 —— 见 [编辑器 $schema 关联](editors.md)
- `[CON-R-004]` 金样例集 —— 你的 kind 有合法/非法样例对可对照
- `[CON-R-005]` conformance 环测试 —— 装载行为以宪法仓样例为准
- `[CON-R-007]` 行尾规范化 —— schema 与样例资产统一 LF

**正本**

- 形态正本：[schemas/workflow_dag/v1.3.json](../schemas/workflow_dag/v1.3.json)、[schemas/service_registry/v1.0.json](../schemas/service_registry/v1.0.json)、[schemas/knowledge/v1.0.json](../schemas/knowledge/v1.0.json)
- 指南：[如何校验 system JSON](how-to/validate-system-json.md)

**本地校验**

```bash
# 仓总入口（含 schema 校验、文件头自检、文档链接、金样例覆盖率）
powershell -File verify-all.ps1

# 只跑文件头自检（$schema 首键 / $id 与路径一致）
python tools/check_schema_headers.py

# 验证你的文档片段
python tools/evorule-migrate validate your_workflow.json
```

**三大常见错误**（金样例非法对）

1. DAG 节点缺必填字段 —— [node.invalid.json](../acceptance/golden/workflow_dag/node.invalid.json)（仅有 `id` 一行是典型残缺）
2. 服务条目缺必填字段 —— [service.invalid.json](../acceptance/golden/service_registry/service.invalid.json)
3. 知识条目形态违规 —— [entry.invalid.json](../acceptance/golden/knowledge/entry.invalid.json)

---

## schema 贡献者

你改 `schemas/` 树本身（结构、$defs、版本演进）。

**受约束条文**

- `[CON-R-003]` 固化义务 —— 语义变更必须同批升宪法（semver minor+）
- `[CON-R-004]` 金样例集 —— 每个唯一 $def 名至少一对合法/非法样例
- `[CON-R-008]` 文件头规范 —— 首键 `$schema`、`$id` 与路径一致
- `[CON-G-001]` 变更分级 —— 语义级走全流程,描述级走轻流程
- `[CON-G-002]` 语义级全流程 —— 五件齐（动机影响面/TCB 联动声明/金样例同步/conformance 全绿/breaking 附迁移器）
- `[CON-G-003]` 版本号纪律 —— 结构面变化而版本未动 = 无声版本,红灯
- `[CON-G-004]` tag 制 —— 每次宪法 schema 包版本发布打 `vX.Y.Z` tag
- `[CON-X-002]` 门-钥配对 —— 任何门无配套钥匙不得单独合入

**正本**

- [schema 演进 SOP](operations/schema-evolution-sop.md)、[发版流程](operations/release-process.md)、[双版本协议](adr/double-version-protocol.md)

**本地校验**

```bash
# schema registry 校验 + case 断言
python tools/verify_schemas.py

# 金样例覆盖率（每个唯一 $def 名至少一对,目标 100%）
python tools/check_golden_coverage.py

# 文件头自检
python tools/check_schema_headers.py

# 全量
powershell -File verify-all.ps1
```

**三大常见错误**

1. 结构面变化版本未动 —— [CON-G-003] 无声版本禁令,CI 红灯（对比 required/enum/properties 增删改）
2. 金样例未同步 —— 新增/修改 $def 后未补样例对,覆盖率脚本跌破 100%
3. 文件头漂移 —— `$id` 与文件路径不一致,`check_schema_headers.py` 红灯

---

## 新消费者

第一次接入 evorule 生态的平台方 / 应用方。

**受约束条文**

- `[CON-R-006]` 同步守护 —— 内嵌 schema 副本必须登记同步清单,防漂移
- `[CON-R-007]` 行尾规范化 —— 跨平台协作统一 LF
- `[CON-L4-003]` conformance 挂 CI —— 环测试与同步检查必须红灯阻断
- `[CON-R-003]` 固化义务 —— 平台语义变更须联动宪法升版
- `[CON-K4-001]` 本地一敲即验 —— 接入验收先跑三态 CLI

**正本**

- [文档导航](introduction.md)、[如何校验 system JSON](how-to/validate-system-json.md)、[如何接入 evorule-rule 对齐](how-to/integrate-with-evorule-rule.md)

**本地校验**

```bash
# 一步跑通全仓校验
powershell -File verify-all.ps1

# 逐文件验收
python tools/evorule-migrate validate your_file.json
```

**三大常见错误**

1. 内嵌副本漂移 —— 拷走 schema 后宪法仓演进,两侧分叉;同步检查报 `DRIFT`
2. 行尾假漂移 —— Windows 下 CRLF 导致字节级比对误报 `DRIFT`（[CON-R-007] 归一化后消除）
3. 裸错误串拒收 —— 消费方自建校验只抛一行错误;对齐 [CON-L1-002] 四段式与 [CON-K1-002] 导览引用

---

## 报错怎么读

宪法拒收报文是**四段式**（[CON-K2-001]）：

```text
[宪法校验失败 / <门名称>]
① 违什么：<违规原因>（schema: <关键字>）
② 在哪：<JSON 路径>（第 N 行附近）
③ 正本：<schema 权威链接>
④ 正确形态（最小可过）：<最小样例>
→ 导览：docs/guide.md（规则作者节）| https://gitee.com/evorule/evorule-system-rules#docs
```

- ①② 告诉你错在哪;③ 是权威定义;④ 是能直接抄的最小修复。
- 缺任一段视为实现缺陷（[CON-L4-004] 挂钩）。
- 编辑器还没配 `$schema` 关联?看[下一页](editors.md)。

<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# evorule 规则设计与非法限制手册

> **禁区手册**——面向设计者（含 LLM 辅助设计时）的"哪些合法、哪些非法、有哪些限制"权威清单。
> 语言坐标：双层语言框架（指令层 / 元指令层）；事实源：`schemas/_shared/v1.0.json` 与引擎源码（见 §3）。
> 原则：引擎（TCB）**不设防**——违反宪法必报错（只有错误、无 warning）；符合宪法但语义错误的规则照常执行，业务正确性由设计者负责（records/77 边界与防御）。

---

## 0. 一句话

> evorule 有两层语言，不是一层：**指令层**是项目方业务规则的语言，**元指令层**是引擎宪法（transform 规则）的语言。凡在这两层之外发明结构、或把一层当另一层，规则必然"跑不起来"。TCB 不设防：违反宪法→报错（Error）；符合宪法但语义错→照常执行（由上层负责）。

## 1. 双层语言坐标（必读）

| | 指令层（Instruction Layer） | 元指令层（Meta-Instruction Layer） |
|---|---|---|
| 别称 | 项目方业务指令 | transform 规则类型 |
| 语言 | `increment / decrement / set / sequence / conditional / while_loop / call_external / call_service / noop` | `branch / set / push / io_request / enforce`（仅 5 种；`collect`/`merge` 已于 v0.6.0 退役，多轮编排由应用层 runner 实现） |
| 权威源 | core_eval.json 的 `instruction` 域匹配目标 | `executor.rs` dispatch（F-01） |
| 运行形态 | 作为 `__exec__.instruction` 流经引擎 | 作为 `transform[]` 中的规则 |
| 作用 | 表达"业务要做什么" | 表达"引擎如何反应/执行" |

**桥接**：引擎用 `instruction` 域匹配指令类型，命中后执行 `on_true` 的元指令。指令层声明"做什么"，元指令层决定"怎么做"。

## 2. 非法限制清单（禁区）

### 2.1 禁止发明结构

| 禁区 | 正确写法 | 违禁后果 | 依据 |
|---|---|---|---|
| 域嵌套不得用 `domain`/`domains` | 嵌套一律用 `inner` | 引擎不认 `domain`/`domains`，规则跑不起来 | P0-03 |
| I/O 结果容器是 `__io_results__`（复数） | 引用 `__io_results__.<io_type>` | 单数 `__io_result__` 匹配不到，I/O 结果读不到 | P1-03 |
| `set` 的 `operation` 只有宪法语义 | 元指令层 `set` 支持 `set`（覆盖）/`add`/`sub`（checked 算术） | 未知操作（如 `multiply`）→ `UnknownOperation` 报错 | F-01 |
| 路径引用必须 `__` 前缀 | `branch.domain`、`push.instructions`、动态引用均以 `__exec__.…` 开头 | 非 `__` 字符串被当字面量，运行时报 `MissingField`/`PathResolutionFailed` | 引擎路径语义 |

### 2.2 禁止混层

| 禁区 | 正确写法 | 依据 |
|---|---|---|
| 指令层类型（`increment`/`noop`/`decrement`/`conditional`/`while_loop`/`sequence`）不得当作 transform 类型 | transform 只有 5 种元指令；指令层类型只能出现在指令序列 / `instruction` 域 | P0-01 |
| 元指令层类型不得当作指令层 | 算术更新走 `increment`/`decrement` 指令 + 元指令 `set operation=add/sub` | 双层语言 |

### 2.3 禁止语义假设

- TCB **不评判语义**：符合宪法即执行。
- 业务 set 指令（指令层）的 `operation` 被忽略（纯覆盖，A-1 分层设计）——不要写出"看起来对、实际被忽略"的规则；算术更新必须用 `increment`/`decrement`。
- 业务正确性由设计者保证，引擎不兜底。

### 2.4 边界声明

- TCB 报错 = **违反宪法**（`TcbError::*`，只有错误、无 warning，有错必报）。
- 语义错误**不报错**，由上层（server 拦截 / 设计者）负责。
- 非法规则在**进入引擎前**由 server 侧 Schema 门禁拦截并给出明确提示（records/77 线1）。

## 3. 事实源速查（权威源唯一，禁止复制）

| # | 事实 | 权威源（唯一） |
|---|---|---|
| F-01 | 元指令类型（5） | `evorule-tcb/src/executor.rs` dispatch（branch/set/push/io_request/enforce；collect/merge 已于 v0.6.0 退役） |
| F-02 | 域类型（7 基础） | `evorule-tcb/src/domain.rs`（eq/lt/exists/instruction/all/not/has_fields） |
| F-03 | I/O 结果路径 | reactor 注入 **`__io_results__`**（复数） |
| F-04 | 路径语法 | `evorule-tcb/src/path.rs` |
| F-05 | 终止性约束（64/64/64/1024） | `transition.rs` / `executor.rs` / `domain.rs` 常量 |
| F-06 | Fact 类型枚举 | `evorule-reactor/src/fact.rs` |
| F-08 | 审计链哈希算法 | `evorule-reactor/src/hash.rs`（BLAKE3） |
| F-09 | 服务注册结构 | `io_handlers/src/service_registry.rs`（对象映射） |
| F-10 | 指令层 ↔ 元指令映射 | core_eval.json（TCB 宪法 transform 规则） |

> schema 侧同义事实已固化在 `schemas/_shared/v1.0.json`（`transform_rule` / `domain` / `instruction` 三个 `$defs`），与上表同源；**禁止**在别处重写一份。

## 4. LLM 提示规范（设计 / 生成规则时注入系统提示）

```
你是 evorule 规则设计助手，必须遵守以下约束：
1. transform 类型只有 5 种：branch / set / push / io_request / enforce
   （collect / merge 已于 v0.6.0 退役，多轮编排由应用层 runner 实现，禁止再生成）。
   禁止把 increment / noop / decrement / conditional / while_loop / sequence 等
   指令层类型当作 transform 类型（它们只能出现在指令序列或 instruction 域）。
2. 域嵌套一律用 inner；禁止 domain / domains 字段。
3. I/O 结果容器是 __io_results__（复数），不是 __io_result__。
4. 路径引用必须 __ 前缀（如 __exec__.payload.…）；非 __ 字符串会被当字面量。
5. set 的 operation 只支持 set（覆盖）/ add / sub（checked 算术），未知操作会报错。
6. 引擎不评判业务语义：符合宪法就执行，业务正确性由你负责。
7. 生成完成后，必须用 evorule 的 schema 门禁校验；非法则修正后再返回。
```

## 5. 验收路径（可复现，72 闭环）

> 以下每条声明都可通过命令复现；**期望输出**为硬性断言，失败即文档与实现脱节。

| 声明 | 命令（工作目录） | 期望输出 |
|---|---|---|
| 元指令白名单对齐（TCB dispatch 5 种 = schema enum；governance 公开白名单 4 种 = dispatch − enforce；CLI 引用 SSOT；bundle 结构门禁 = dispatch） | `python tools/check_whitelist_sync.py`（`d:\evorule-system-rules`） | `[PASS] 白名单对齐（dispatch 5 种: branch, enforce, io_request, push, set；公开白名单 4 种；CLI 引用 SSOT；bundle 结构门禁一致）` |
| 禁区负向用例全部被 schema 拒（not.domain / increment 混层 / set 缺 value / 非 `__` 路径等） | `python _verify_schemas.py`（`d:\evorule-system-rules`） | 全部 `[PASS]` 且进程退出码 0（`ALL OK`） |
| 真实规则文件通过 schema（core_eval / 10_role13_demo / yuanze / service_registry 合并视图） | 同上 | 正向用例全部 `[PASS]` |
| rule_translate 输出闸拒绝非法产物 | `cargo test -p evorule-workspace`（`d:\evorule-server`） | `schema_gate_rejects_unknown_op`、`schema_gate_rejects_invalid_set_operation` 通过 |
| server 校验 API 对非法规则返回 422 + `schema_gate=failed` | `cargo test -p evorule-server --lib`（`d:\evorule-server`） | `test_validate_*_rejected` 系列通过 |

---

## 延伸阅读

- [schema-reference.md](./schema-reference.md) — 6 个 kind 的字段定义
- [cli-reference.md](./cli-reference.md) — `evorule-migrate` 命令行
- [version-protocol.md](./version-protocol.md) — 双版本协议细则
- [03-evorule-rule-alignment.md](../explanation/03-evorule-rule-alignment.md) — 与 evorule-rule 的上下级关系
- 背景裁定：[records/77 边界与防御原则]、[records/75 双层语言框架]、[records/70 SSOT]（内部留存）

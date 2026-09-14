<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 02 — 自举的边界:递归如何停

> **立场篇**——"evorule 解释 evorule"听起来很美,但递归必须有人工基座。

## 诱惑与陷阱

### 诱惑

evorule 能治理业务规则,就能治理系统规则(系统规则也是 JSON)。
既然 evorule 能治理系统规则,**应该**也能治理元规则(管理规则的规则)。
既然 evorule 能治理元规则,**应该**也能治理元元规则(管理元规则的规则)。
推到底:**evorule 应该完全自己管理自己**,零人工。

### 陷阱

- **哥德尔陷阱**:任何足够强的形式系统,都无法在自身内完全证明一致性
- **鸡生蛋问题**:evorule 第 1 次启动时,谁校验 evorule 自身?
- **抽象税**:把简单的人工流程抽象成 evorule 规则,可能增加 10x 维护成本
- **TLA Trap**:写一个"通用 migration 工具"所需的复杂度,可能超过"为每次升级写 1 个 migration"的复杂度

### 现实

evorule **不能**完全自举——必须有人工基座。
本设计的目标是:**最小化人工基座 + 最大化自举覆盖**。

## 递归层级与终止

evorule 生态的元层(从底到顶):

| 层 | 内容 | 是否自举 | 谁管 | 工具 |
|----|------|----------|------|------|
| L0 | 物理现实(机器 / OS / 网络) | ❌ | 硬件 / OS kernel | - |
| L1 | `$schema` v1.0 schema 文件本身 | ❌ | 人类冻结,patch only | git + CI |
| L2 | 6 个 kind 的 schema 文件 | ❌ | 人类 + 评审 | git + CI |
| L3 | 现有 system JSON | ✅ | evorule 启动期校验 | evorule-migrate |
| L4 | 项目方业务规则 | ✅ | evorule-rule 平台 | evorule-rule |
| L5 | migration 规则 | ✅ | evorule 启动期校验 | evorule-migrate |

### 终止条件

**L0/L1/L2 永远不递归**——必须由 evorule 之外的东西管:

- L0:OS / 硬件,人类维护
- L1:`$schema` v1.0 是冻结点,只允许 patch(不破坏),新增 = 新 v2.0
- L2:6 个 kind 的字段定义,人类 + 评审流程

**L3/L4/L5 全部走 evorule 治理**——这是自举的边界。

## 一图理解

```
┌────────────────────────────────────────────────┐
│ L0: 物理现实          人类 / 硬件              │  ← 不可自举
├────────────────────────────────────────────────┤
│ L1: $schema v1.0     人类冻结,patch only     │  ← 不可自举
├────────────────────────────────────────────────┤
│ L2: 6 个 kind schema 人类 + 评审              │  ← 不可自举
├────────────────────────────────────────────────┤
│ L3: system JSON      evorule 治理(L1 校验)    │  ← 可自举
├────────────────────────────────────────────────┤
│ L4: 业务规则          evorule-rule 治理(L3 校验)│  ← 可自举
├────────────────────────────────────────────────┤
│ L5: migration 规则    evorule 治理(L1 校验)    │  ← 可自举
└────────────────────────────────────────────────┘
```

**关键洞察**:L1 不可自举,但 L1 之上的一切都可以自举。
这意味着 evorule 团队的人工基座 = L1 的一次性冻结工作。

## 工程化方案

### L1 冻结:最小化 + 极简

- `$schema` v1.0 应该**极简**——只保留 6 个 kind 的骨架
- 不在 L1 加任何"业务逻辑"——业务逻辑归 L3/L4
- L1 的修改必须**很慢**(每 6 个月一次,严肃评审)

### L3 治理:启动期校验

- evorule 启动时,加载每个 system JSON
- 读 `$schema` 字段,用 L1 schema 校验
- 失败 = 启动拒绝
- **简单**、**确定**、**无需 evorule 自身的复杂逻辑**

### L5 migration:evorule transform 表达

- migration 规则用 `kind: migration` 表达
- 内容用 evorule transform 语法(when / then)
- 跑 migration 的工具 = 普通的 evorule 引擎调用
- 工具的源码 = 人工写的(不可自举)
- 工具跑的规则 = evorule 治理的(可自举)

### 工具的最小化

`evorule-migrate` 工具做且只做 3 件事:

1. **加载** system JSON
2. **找**匹配的 migration 规则
3. **跑** migration 规则(evorule 引擎调用)

工具不写业务逻辑,业务逻辑都在 migration 规则里(可自举)。

## 递归具体何时停止

### 时间维度

- L1 v1.0 冻结时(2026-11 估计)→ 递归停止
- 之后所有 L1 改动必须 = L1 v2.0 起草 + L1 v1.0 → v2.0 migration
- L1 v1.0 → v2.0 migration 本身用 evorule 表达(L5)
- 工具的源码**不变**(仍跑 v1.0 的引擎),只是跑一组新的 migration 规则

### 范围维度

- 跨 L1 边界的修改永远需要人类
- L1 内部修改:人类 + 评审
- L3+ 修改:evorule 自动化

### 一次具体递归实例:加一个新的 kind

假设 evorule v1.2 需要新增 `kind: prompt_template`:

1. **人类**:起草 `schemas/prompt_template/v1.json` (L1 改动,需 v1.0 → v1.2 migration)
2. **人类**:写 migration 规则 `migrations/v1.0-to-v1.2/add_prompt_template_kind.json` (L5)
3. **evorule-migrate**:跑 migration 链(L3 自动化)
4. **校验**:新 JSON 符合 v1.2 schema(L3 自动化)
5. **递归止于第 1 步**——L1 schema 起草必须人类

如果 `prompt_template` 内部规则再变,只需要写新的 migration,**不需要人类改 schema**(因为 `prompt_template` v1 内部字段在 schema 起草时已定义好)。

## 反模式(避免)

### 反模式 1:试图让 evorule 自己写 L1

- **症状**:写一个"evorule 设计器"自动生成 schema
- **为什么不行**:L1 涉及"系统应该是什么"——这是设计决策,不是计算
- **替代**:人类用 JSON Schema 起草 + 评审

### 反模式 2:migration 工具过度通用

- **症状**:写一个"通用 JSON 树操作 DSL"
- **为什么不行**:通用 DSL 的复杂度 > 写 1 个具体 migration 的复杂度
- **替代**:用 evorule transform 表达(已存在的能力),工具只是驱动器

### 反模式 3:L1 频繁小改

- **症状**:每周改一次 schema
- **为什么不行**:每次改都触发整套 migration,工程税太高
- **替代**:L1 主版本 = 6 个月一次,中间只 patch

### 反模式 4:把 L1 当 L5 治

- **症状**:试图用 evorule 规则管理 schema 文件本身
- **为什么不行**:schema 文件由 evorule 之外的工具管(编辑器、git、CI)
- **替代**:schema 文件归 git + CI 管,内容归 L5 migration 管

## 自举的"无限猴子"问题

### 问题

理论上,evorule 可以用它自己的规则**生成新的规则**——
例:"读取所有 R0XX 规则,聚类出 R100-R200 的派生规则"。

### 立场

- **不禁止**——这是项目方的业务能力(AI 生成规则)
- **不鼓励**——生成出来的规则没有经过人类治理,质量不可控
- **必须标记**——生成的规则必须标 `metadata.provenance.source = "generated"`
- **必须审核**——`lifecycle.state = "draft"`,等人类批准

### 边界

- evorule 可以**生成**规则(用 AI / 算法)
- evorule **不能批准**自己生成的规则(必须人类)
- 业务规则的合法性 = evorule 校验(可自举)
- 业务规则的价值 = 人类判断(不可自举)

## 结论

**evorule 的自举闭环**:

1. **L1 是底,不是顶**——`$schema` v1.0 是冻结点,evorule 不能动
2. **L3+ 全自举**——所有 system JSON / 业务规则 / migration 规则都由 evorule 治理
3. **人工基座小而稳**——L1 + L2 = 100-200 行 JSON Schema + 评审流程,6 个月改一次
4. **工具极简**——`evorule-migrate` 只做加载 / 路由 / 执行,业务逻辑全在规则里

**这不是"evorule 完全管理自己"**——是"evorule 在最小人工基座上管理自己的大部分"。
**这是务实的自举**——不是理想的自举。

## 延伸阅读

- [00-evorule 解释 evorule](./00-evorule-explains-evorule.md) — 核心定位
- [设计规范(自举终止)](../adr/bootstrap-termination.md) — 自举终止条件(设计规范)

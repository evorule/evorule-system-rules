<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 自举终止条件

## 是什么

evorule 自举("evorule 用 evorule 治理 evorule 的元层")有明确的递归终止边界:

| 层 | 是否自举 | 维护者 | 工具 |
|----|----------|--------|------|
| L0 物理(机器 / OS / 网络) | ❌ | 硬件 / OS kernel | — |
| L1 `$schema` v1.0 schema 文件 | ❌ | evorule 团队冻结,仅 patch | git + CI |
| L2 6 个 kind 的 schema 文件 | ❌ | evorule 团队 + 评审流程 | git + CI |
| L3 system JSON | ✅ | evorule 启动期校验 | evorule-migrate |
| L4 业务规则 | ✅ | evorule-rule 平台 | evorule-rule |
| L5 migration 规则 | ✅ | evorule 启动期校验 | evorule-migrate |

**人工基座** = L0/L1/L2(约 100-200 行 JSON Schema + 评审流程,6 个月改一次)。
**自举覆盖** = L3/L4/L5(evorule 生态的全部运行时配置)。

## 递归停止的位置

- **L1 一旦冻结**(`v1.0.0`),evorule 不能动
- 之后任何 L1 改动 = L1 v2.0 起草 + L1 v1.0 → v2.0 的 migration
- L1 v1.0 → v2.0 migration 本身用 evorule 表达(L5),由 evorule-migrate 执行
- 工具源码不变,仅运行新 migration 规则

## 跨 L1 边界修改

- 永远需要人类(起草新 schema + 写 migration)
- L1 内部修改走人类 + 评审
- L3+ 修改走 evorule 自动化

## 为什么

- **避免哥德尔陷阱**:任何足够强的形式系统都无法在自身内完全证明一致性
- **最小化人工基座**:人工维护部分应小而稳
- **明确责任**:每层由谁维护(人类 / evorule / 工具)清晰可分

## 怎么用

- 自举边界详解:[explanation/02-bootstrap-boundary.md](../explanation/02-bootstrap-boundary.md)
- 核心定位:[explanation/00-evorule-explains-evorule.md](../explanation/00-evorule-explains-evorule.md)

## 不接受的替代方案

- **全部自举,人工基座为 0**:第 1 次启动时谁校验 evorule?(鸡生蛋)
- **L0/L1 不可自举,L2+ 全自举**:L2 频繁改,失去稳定性

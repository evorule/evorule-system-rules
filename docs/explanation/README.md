<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# explanation/ — 原理与设计讨论

> **面向想理解"为什么"的开发者**:设计动机、概念讨论、权衡。

适合:用着没问题,但想理解背后想法的人;做新设计前的参考资料。

## 写什么

- 为什么这么设计 / 不那么设计
- 概念之间的关系、术语定义
- 历史演变、曾考虑过但放弃的方案
- **哲学/立场白皮书**(00-/01-/02-/03- 编号系列):项目对外的工程哲学、立场宣言

## 不要写在这里

- ❌ "怎么用" → 去 [tutorial/](../tutorial/) 或 [how-to/](../how-to/)
- ❌ API 字段说明 → 去 [reference/](../reference/)
- ❌ 重要决策的正式记录 → 去 [adr/](../adr/)(ADR 是**不可变历史**,explanation 是**讨论**)

## 目录

- [00-evorule 解释 evorule](./00-evorule-explains-evorule.md) — 核心定位:evorule 用 evorule 治理 evorule
- [01-3 层治理模型](./01-three-tier-governance.md) — Tier 1 / Tier 2 / Tier 3 的边界
- [02-自举的边界](./02-bootstrap-boundary.md) — 递归如何停
- [03-与 evorule-rule 的关系](./03-evorule-rule-alignment.md) — 上下级 vs 平级
- [doc-boundaries.md](./doc-boundaries.md) — 公开 / 私有 / 试行 的文档边界

## 命名规范

`NN-主题-副题.md`(如 `00-evorule-explains-evorule.md`),NN 从 00 起,保证阅读顺序。

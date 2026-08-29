<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# reference/ — 字典式参考

> **面向需要查阅确切信息的开发者**:schema 字段、CLI 命令、版本协议。

适合:用的时候翻一翻,看完就走,不需要从头读到尾。

## 写什么

- **准确、完整**:字段、类型、默认值、约束
- **简洁、无废话**:不解释为什么,只写"是什么"
- **尽量自动生成**:从 `schemas/*.json` 自动提取,**不**手抄

## 不要写在这里

- ❌ 教程式引导 → 去 [tutorial/](../tutorial/)
- ❌ 任务步骤 → 去 [how-to/](../how-to/)
- ❌ "为什么这么设计" → 去 [explanation/](../explanation/)

## 命名规范

按"对象"命名(schema 名 / CLI 子命令 / 配置项名),**不**按"任务"命名。

## 目录

- [schema-reference.md](./schema-reference.md) — 6 个 kind 的字段定义
- [cli-reference.md](./cli-reference.md) — `evorule-migrate` 命令行
- [version-protocol.md](./version-protocol.md) — 双版本协议细则
- [illegal-restrictions-manual.md](./illegal-restrictions-manual.md) — 规则设计与非法限制手册（禁区清单）

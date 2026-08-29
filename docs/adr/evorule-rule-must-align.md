<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# evorule-rule 必须对齐 evorule-system-rules

## 是什么

evorule-rule(治理层实现)受 evorule-system-rules(Tier 1 系统元规则)约束,所有字段格式以 Tier 1 为准。

**对齐的 3 个层面**:

| 层面 | 要求 | 保障手段 |
|------|------|----------|
| 字段对齐 | evorule-rule 字段命名/类型与 Tier 1 schema 一致 | CI 强制检查 |
| 行为对齐 | 校验、迁移逻辑遵循 Tier 1 定义 | 单元测试 |
| 版本对齐 | evorule-rule 主版本 = Tier 1 `$schema` 主版本 | release 流程约束 |

**字段映射示例**(`RuleDataset` → `kind: rule_set`):

| evorule-rule 字段 | Tier 1 表达 |
|-------------------|------------|
| `RuleDataset::governance` | `metadata.governance` |
| `RuleDataset::provenance` | `metadata.provenance` |
| `RuleDataset::lifecycle` | `metadata.lifecycle` |
| `RuleDataset::dependencies` | `metadata.dependencies` |
| `RuleEntry::id` | `rules[].id` |
| `RuleEntry::when/then/transform` | `rules[].when/then/transform` |

**启动期校验**(evorule-rule 启动时):

1. 读 Tier 1 当前版本
2. 比对 evorule-rule 主版本,主版本失对齐 = 启动拒绝
3. 字段对齐检查,失对齐 = 启动拒绝

## 为什么

- **跨平台兼容**:同一份业务规则在 evorule 引擎和 evorule-rule 平台表现一致
- **避免规则格式分裂**:evorule-rule 不允许"自定义"超出 Tier 1 的字段
- **升级节奏受控**:Tier 1 升级时 evorule-rule 同步升级,避免野升级

## 怎么用

- 双重身份详解:[explanation/03-evorule-rule-alignment.md](../explanation/03-evorule-rule-alignment.md)
- 集成指南:[how-to/integrate-with-evorule-rule.md](../how-to/integrate-with-evorule-rule.md)
- 3 层治理模型:[explanation/01-three-tier-governance.md](../explanation/01-three-tier-governance.md)

## 不接受的替代方案

- **两者并列,各自独立**:evorule-rule 可自由定义 schema,规则格式可能分裂
- **evorule-system-rules 作为 evorule-rule 的可选插件**:失去"系统元规则"的权威性

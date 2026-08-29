<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 00 — evorule 解释 evorule:自举的核心定位

> **立场总纲**——本系列解释文档(01/02/03)的出发点。

## 一句话定位

**evorule 是用 evorule 自己的 vocabulary 定义"系统 JSON 格式/版本/升级"、执行元规则自己保证一致性的系统。evorule 解释 evorule。**

## 为什么是"自举"

evorule 不只是"业务规则引擎",它的目标是**递归地治理自己的元层**——

- 第 1 层:evorule 治理用户的业务规则集
- 第 2 层:evorule 治理自己的 system JSON(例:`core_eval.json`)
- 第 3 层:evorule 治理 system JSON 的 schema 升级(例:`v0 → v0.9` 的 migration 规则)

每一层都"用 evorule 治理上一层",这就是自举。

## 自举的诱惑与陷阱

### 诱惑

听起来很美——evorule 能治理业务,就能治理元规则;能治理元规则,就能治理元元规则;推到底,evorule 应该完全自己管理自己,零人工。

### 陷阱

- **哥德尔陷阱**:任何足够强的形式系统,都无法在自身内完全证明一致性
- **鸡生蛋问题**:evorule 第 1 次启动时,谁校验 evorule 自身?
- **抽象税**:把简单的人工流程抽象成 evorule 规则,可能增加 10x 维护成本

## 务实的自举

**evorule 不能完全自举,必须有人工基座。** 目标是最小化人工基座 + 最大化自举覆盖:

- 人工基座 ≈ 100-200 行 JSON Schema 文件(L1/L2)+ 评审流程
- 自举覆盖 = evorule 生态的全部运行时配置(L3+)

详见 [02-自举的边界](./02-bootstrap-boundary.md)。

## "evorule 解释 evorule" 的工程意义

1. **统一表达**:业务规则 / 系统规则 / 升级规则 用同一种语言表达
2. **统一工具**:同一套工具(校验器、迁移器)处理所有规则
3. **统一治理**:用户业务规则和系统元规则在同一个平台上
4. **统一升级**:所有规则都走 migration 工具,所有升级都有迹可循

## 与 evorule-rule 的关系

evorule-rule 是 evorule 生态的"治理层",但它自身**也是 evorule 治理的对象**:

- evorule-rule 的字段格式必须遵循 evorule-system-rules(Tier 1)
- evorule-rule 的升级节奏受 Tier 1 约束
- 用户业务规则通过 evorule-rule 平台管理,evorule-rule 负责用 Tier 1 校验它们

详见 [03-与 evorule-rule 的关系](./03-evorule-rule-alignment.md)。

## 对外叙事

evorule 不是"另一个规则引擎",而是**用规则解释规则的元系统**。
这个定位决定了 evorule 的产品边界:

- ❌ 不是低代码平台
- ❌ 不是单纯的工作流引擎
- ❌ 不是单纯的业务规则管理系统(BRMS)
- ✅ 是"系统的系统"——evorule 是"治理 evorule 自己的规则"

## 延伸阅读

- [01-3 层治理模型](./01-three-tier-governance.md) — 治理结构
- [02-自举的边界](./02-bootstrap-boundary.md) — 递归如何停
- [03-与 evorule-rule 的关系](./03-evorule-rule-alignment.md) — 双重身份

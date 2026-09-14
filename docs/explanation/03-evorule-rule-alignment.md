<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 03 — 与 evorule-rule 的关系:上下级,不是平级

> **立场篇**——evorule-rule 在 3 层治理模型中的双重身份。

## 双重身份

evorule-rule 在 evorule 生态中扮演两个角色:

```
                    ┌─────────────────────────────┐
                    │  evorule-system-rules        │  (Tier 1)
                    │  系统元规则 / $schema 权威    │
                    └──────────────┬───────────────┘
                                   │ 约束
                    ┌──────────────┴───────────────┐
                    │  evorule-rule                 │  (Tier 2 / Tier 3 桥)
                    │  • Tier 1 的下游(自己 schema  │
                    │    必须对齐)                   │
                    │  • Tier 3 的管理者(用 Tier 1 │
                    │    治理项目方业务规则)          │
                    └──────────────┬───────────────┘
                                   │ 管理
                    ┌──────────────┴───────────────┐
                    │  项目方业务规则                │  (Tier 3)
                    └─────────────────────────────┘
```

**含义**:
- evorule-rule **不能自由发挥**自定义 schema
- evorule-rule 的所有字段格式必须以 Tier 1 `$schema` 为准
- evorule-rule 升级必须跟随 Tier 1 `$schema` 主版本
- 项目方通过 evorule-rule 提交的业务规则,evorule-rule 负责校验它们符合 Tier 1

## 字段如何用 Tier 1 表达

### RuleDataset 对应 `kind: rule_set`

evorule-rule 的 RuleDataset 本质上是一个 rule_set。
它的元数据应该用 Tier 1 的 5 顶层字段表达:

```json
{
  "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
  "kind": "rule_set",
  "id": "com.acme.sales.validation",
  "version": "2.3.1",
  "metadata": {
    "title": "销售验证规则集",
    "description": "...",
    "authors": ["alice@acme.com"],
    "created": "2026-03-01",
    "updated": "2026-08-20",
    "tags": ["sales", "validation"],
    "license": "Proprietary"
  },
  "rules": [
    {
      "id": "R001",
      "when": { ... },
      "then": { ... },
      "transform": { ... }
    }
  ]
}
```

### 治理字段用 `metadata` 子字段表达

evorule-rule 现有的治理字段(Governance / Provenance / Lifecycle / Dependency)
应该用 Tier 1 的 5 顶层字段的扩展表达,而不是另起一套:

- **Governance**(谁批准 / 谁审核)→ `metadata.governance` 字段
- **Provenance**(来源 / 派生链)→ `metadata.provenance` 字段
- **Lifecycle**(草稿 / 评审 / 生效 / 废弃)→ `metadata.lifecycle` 字段
- **Dependency**(依赖哪些其他 rule)→ `metadata.dependencies` 字段

## 对齐的 3 个层面

### 字段对齐(静态)

- evorule-rule 不能新增"未在 Tier 1 定义的"顶层字段
- evorule-rule 的字段命名必须以 Tier 1 为准
- 例:不能把 `id` 改名为 `rule_id`,不能把 `metadata` 改名为 `info`

### 行为对齐(动态)

- evorule-rule 校验项目方规则时,用 Tier 1 的 JSON Schema
- evorule-rule 触发迁移时,跑 Tier 1 的 migration 规则
- evorule-rule **不允许**"绕过" Tier 1 直接加载未校验的 JSON

### 版本对齐(时序)

- Tier 1 `$schema` 主版本升级 = evorule-rule 主版本升级
- evorule-rule 不能"领先" Tier 1 实现未定义的字段
- evorule-rule 也不能"落后"——如果 Tier 1 已 v2.0,evorule-rule 必须 v2.0

## 对齐验证机制

### 启动期校验

evorule-rule 启动时:

1. 读 Tier 1 当前版本(从 `evorule-system-rules/CHANGELOG.md`)
2. 检查自己的代码中所有"硬编码字段"是否都在 Tier 1 schema 中
3. 失败 = 启动拒绝 + 提示"evorule-rule 与 evorule-system-rules 失对齐,需升级"

### 运行期校验

evorule-rule 处理项目方规则时:

1. 读项目方规则的 `$schema` 字段
2. 与 Tier 1 当前 schema 比对
3. 不匹配 = 走 migration(自动)或拒绝(配置决定)
4. migration 失败 = 明确报错(指出哪个字段不兼容)

### 升级期校验

evorule-rule 升级时:

1. 同时升级 Tier 1 仓的依赖绑定
2. 跑完整的 migration 测试(从最低支持版本到当前)
3. 跑双向兼容测试(新 evorule-rule 处理旧规则,旧 evorule-rule 拒绝新规则)
4. 全部通过 = 发布;否则 = 拒绝发布

## 不对齐会怎样

### evorule-rule 失对齐 Tier 1 的后果

- 平台项目方写入的规则 evorule 引擎加载失败
- migration 工具链断裂
- 跨平台兼容性破坏(同一份规则在 evorule-rule 平台能跑,在 evorule 引擎跑不了)
- "正规化"失败,evorule 没法向产品化推进

### 现实风险点

- evorule-rule 团队(就是 evorule 团队)很容易"图方便"加字段
- 业务紧急时,evorule-rule 可能先实现,等 Tier 1 跟上
- **必须有人/有机制拦截**——这是治理问题,不是技术问题

### 缓解措施

1. **CI 强制**:evorule-rule PR 必须跑"对齐检查"(对比字段表)
2. **代码评审**:任何"硬编码字段"必须有 Tier 1 引用
3. **季度 review**:evorule 团队每季度 review Tier 1 是否有遗漏字段
4. **透明记录**:所有 evorule-rule 字段在 evorule-system-rules 仓有追踪表

## 升级节奏

| 阶段 | Tier 1 | evorule-rule | 项目方规则 |
|------|--------|--------------|----------|
| v0 草案 | 起草中 | 暂不引用 | 暂不要求 |
| v0.9 冻结 | 草稿冻结 | 接入 schema 校验 | 可选引用 |
| v1.0 发布 | 主版本 | **主版本同步升级** | **强制对齐** |
| v1.x 迭代 | 补丁 | 跟随补丁 | 平滑兼容 |
| v2.0 升级 | 起草新主版本 | **起草新主版本** | 走 migration 链 |

**关键点**:
- Tier 1 主版本 = evorule-rule 主版本(对齐)
- Tier 1 冻结 = 项目方规则强制对齐(失对齐拒绝加载)
- Tier 1 草稿期 = 双方可灵活(但 v0.9 之后收紧)

## 一句话总结

**evorule-rule 是 evorule-system-rules 在治理层的"实现",所有 evorule-rule 字段以 Tier 1 schema 为准,evorule-rule 升级跟随 Tier 1 `$schema` 主版本。**

## 延伸阅读

- [00-evorule 解释 evorule](./00-evorule-explains-evorule.md) — 核心定位
- [01-3 层治理模型](./01-three-tier-governance.md) — 治理结构
- [设计规范(evorule-rule 对齐)](../adr/evorule-rule-must-align.md) — evorule-rule 必须对齐(设计规范)

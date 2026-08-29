<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 双版本协议

## 是什么

所有 evorule 系统 JSON 同时承载两个版本字段,**正交独立**:

| 字段 | 角色 | 格式 | 何时变化 |
|------|------|------|----------|
| `$schema` | 协议版本(字段约束) | semver | schema 升级时变 |
| `version` | 内容版本(具体规则迭代) | semver | 内容迭代时变 |

**示例组合**:

| `$schema` | `version` | 含义 |
|-----------|-----------|------|
| v1.0 | 1.2.3 | 协议稳定,内容小步迭代 |
| v2.0 | 1.0.0 | 协议升级,内容从 1.0 重新计数 |
| v1.0 | 2.0.0 | 协议稳定,内容有 breaking change(由 evorule 团队评审) |

**`$schema` URL 格式**:`https://evorule.org/schemas/<kind>/v<X>.<Y>.json`

## 升级规则

### `$schema` 主版本变化(breaking)

- 删除字段、改字段类型、改 required → 必须升主版本
- 所有现有 JSON 必须走 migration,否则启动期校验失败

### `$schema` 次版本变化(兼容性新增)

- 新增可选字段、新增 kind、新增 enum 值 → 升次版本
- 旧 JSON 仍可用

### `$schema` 补丁版本(纯修正)

- 文档修正、约束放宽 → 升补丁版本
- 完全兼容,无需 migration

### `version` 字段

- 与 `$schema` 完全独立
- 由内容所有者按需变化

## 冻结

`$schema` v1.0 一旦发布即冻结。改动 = 新主版本 + migration 链。

## 为什么

- **协议与内容解耦**:协议升级和内容升级互不干扰
- **迁移链路清晰**:`$schema` 主版本变化触发 migration,内容版本独立递增
- **同一协议下内容可自由迭代**

## 怎么用

- 详细规范:[reference/version-protocol.md](../reference/version-protocol.md)
- 跨多版本升级:[how-to/upgrade-existing-json.md](../how-to/upgrade-existing-json.md)
- 双版本在 `metadata` 中的位置:`schemas/_meta/v0.9.json`

## 不接受的替代方案

- **单版本耦合**:协议升级和内容升级绑定,migration 触发条件模糊
- **仅 `$schema`**:内容变更无版本号,审计困难

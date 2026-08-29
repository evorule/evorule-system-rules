<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 双版本协议

> `$schema` 与 `version` 的关系、升级规则、冻结时机。

## 两个版本的角色

evorule-system-rules 治理的 system JSON 有两个版本字段:

| 字段 | 含义 | 格式 | 谁变 |
|------|------|------|------|
| `$schema` | 协议版本(字段约束) | semver | $schema 升级时变 |
| `version` | 内容版本(具体规则迭代) | semver | 内容迭代时变 |

两者**正交**——可以独立变化。

## `$schema` URL 格式

```
https://evorule.org/schemas/<kind>/v<X>.<Y>.json
```

例:
- `https://evorule.org/schemas/rule_set/v1.0.json`
- `https://evorule.org/schemas/agent_def/v0.9.json`

## 升级规则

### `$schema` 主版本变化(breaking change)

- **触发条件**:字段定义有破坏性修改(删除字段、改字段类型、改 required)
- **后果**:所有使用旧 `$schema` 的 system JSON 失对齐,evorule 启动期校验失败
- **必须动作**:
  1. 写 migration 规则 `migrations/<from>-to-<to>/*.json`
  2. 跑 migration 升级所有现有 JSON
  3. 更新 `$schema` 字段到新 URL
  4. 跑 `evorule-migrate validate` 全部通过

### `$schema` 次版本变化(兼容性新增)

- **触发条件**:新增可选字段、新增 kind、新增 enum 值
- **后果**:旧 JSON 仍可用(evorule 不强制新字段)
- **可选动作**:跑 migration 把新字段默认值补进去(可选)

### `$schema` 补丁版本变化(纯修正)

- **触发条件**:文档修正、example 修正、约束放宽(更宽松)
- **后果**:完全兼容,无需 migration

### `version` 主版本变化(内容破坏性)

- **触发条件**:业务规则有重大重构
- **后果**:使用该规则集的下游消费方需要升级引用
- **不触发** migration(只改 `version` 不改 `$schema`)

## 冻结时机

### v1.0 冻结(协议稳定)

- 一旦发布 `v1.0.0`,该版本的字段定义**不可再改**
- 改动 = 新 `v<X+1>.0.0` + 写 migration 链
- 这是 evorule-system-rules 走向"产品化"的承诺

### 冻结后允许的修改

- `v1.0.x`(补丁):文档修正、约束放宽
- `v1.x.0`(次版本):新增可选字段、enum 新值
- `v<X+1>.0`(主版本):任何破坏性改动

## `id` 稳定性

`id` 字段是 system JSON 的"身份证",跨 `$schema` 版本必须稳定:

- 改名 = 新 ID(不是改名)——保证 migration 链可追踪
- 例:`com.evorule.tcb.core_eval` 在 v0.9、v1.0、v2.0 都是同一个 ID

## migration 目录结构

```
migrations/
  v0.0-to-v0.9/                  起始 v0.0 → v0.9
    add_five_top_fields.json     第一个 migration
  v0.9-to-v1.0/                  v0.9 → v1.0
    tighten_required_fields.json
  v1.0-to-v2.0/                  v1.0 → v2.0(将来)
    restructure_ids.json
```

文件名 `v<X>.<Y>-to-v<X'>.<Y'>`,目录里放 1+ 个 migration JSON。

## 升级链执行

`evorule-migrate upgrade` 自动按目录顺序应用:

1. 加载 `migrations/<from>-to-<to>/` 下所有 `*.json`
2. 按文件名排序(字典序)
3. 每个 migration 的 `transforms` 顺序应用
4. 输出新 JSON

## 典型升级示例

```bash
# 升级 core_eval.json 从 v0.0 到 v0.9
$ python tools/evorule-migrate upgrade core_eval.json \
    --from-schema v0.0 --to-schema v0.9 \
    -o core_eval.v0.9.json

应用的 migrations:
  [OK] add_five_top_fields.json: 6 transforms

# 校验升级结果
$ python tools/evorule-migrate validate core_eval.v0.9.json
OK core_eval.v0.9.json (kind=rule_set, schema=v0.9)
```

## 与 semver 的关系

`$schema` 和 `version` 都用 semver 三段式 `X.Y.Z`:

- **X(主版本)**:不兼容的 API 变更(对 `$schema` 是字段定义变化,对 `version` 是规则重大重构)
- **Y(次版本)**:向后兼容的功能新增
- **Z(补丁版本)**:向后兼容的修正

支持 pre-release(`-alpha.1` / `-rc.1`)和 build metadata(`+20260823`),但目前工具不强制。

## 边缘情况

### 同一份 JSON 跨多个 `$schema`

不推荐。如果必须,evorule 启动期会取 `$schema` 字段对应的 schema 校验,其他版本不被加载。

### `$schema` 指向不存在的版本

- 启动期校验失败
- 明确报错:`找不到 rule_set 的 v0.5.json,可用版本:['v0.9']`

### migration 链断裂

- 例:有 `v0.0 → v0.9` 和 `v0.9 → v1.0`,但缺 `v0.0 → v1.0`
- 工具不会自动串联,要求显式逐级升级
- 这避免了"无意中跳过关键 migration"

## 延伸阅读

- [设计规范(双版本)](../adr/double-version-protocol.md) — 双版本协议
- [schema-reference.md](./schema-reference.md) — 字段定义
- [cli-reference.md](./cli-reference.md) — 工具用法

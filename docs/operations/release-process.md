<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 发版流程

> evorule-system-rules 的发版流程、版本号约定、release checklist。

## 版本号约定

采用 [语义化版本](https://semver.org/lang/zh-CN/) `X.Y.Z`:

| 段 | 含义 | 触发 |
|----|------|------|
| X(主版本) | 协议破坏性变更 | 字段定义有破坏性修改,需 migration |
| Y(次版本) | 兼容性新增 | 新增可选字段、enum 值、新 kind |
| Z(补丁) | 兼容性修正 | 文档修正、约束放宽、bug 修复 |

**冻结点**:`v1.0.0` 发布后,该版本字段定义不可再改。改动 = 新 `v<X+1>.0.0`。

## 4 阶段发版流程

### 阶段 1:v0.9 草案(2-4 周)

**目标**:发布 v0.9 草案,收集团队反馈。

**产出**:
- 6 个 kind 的 v0.9 schema
- 通用 `_meta/v0.9.json`
- 6 个 examples
- 1+ 个 migration 规则
- `evorule-migrate` 工具(初级版)

**发版动作**:
- [ ] 推代码托管平台(仓建议私有,与 evorule / evorule-rule 同组织)
- [ ] 打 tag `v0.9.0-draft`
- [ ] 在 evorule 团队群通知 review
- [ ] 收集反馈,记录在项目内部协作区

**不发布到 PyPI**(工具尚未稳定)。

### 阶段 2:v0.9 冻结(1-2 周)

**目标**:基于反馈修正,发布 v0.9 正式版。

**产出**:
- v0.9 schema 全部冻结
- 现有 4 仓的 6+ system JSON 全部跑 `evorule-migrate upgrade` 对齐
- 工具完善(transform 引擎支持嵌套路径、对象字面量)

**发版动作**:
- [ ] 修所有 review 反馈
- [ ] 跑 `validate` 全部 examples + migration 通过
- [ ] 推代码托管平台 `master` 分支
- [ ] 打 tag `v0.9.0`
- [ ] 在 `CHANGELOG.md` 记录变更
- [ ] 通知 evorule 团队:"v0.9 冻结,现有 system JSON 必须升级"

### 阶段 3:v1.0 准备(3-4 周)

**目标**:起草 v1.0,evorule-rule 同步升级。

**产出**:
- v1.0 schema(冻结点)
- migration `v0.9-to-v1.0/` 规则
- evorule-rule v1.0 同步发布(主版本对齐)
- 至少 1 个项目方业务规则接入 evorule-rule 平台

**发版动作**:
- [ ] 整合 v0.9 反馈,起草 v1.0
- [ ] evorule-rule 团队升级到 v1.0
- [ ] 跑完整 migration 测试
- [ ] 跑双向兼容测试
- [ ] 推代码托管平台 `master` 分支
- [ ] 打 tag `v1.0.0`
- [ ] 公告:"v1.0 冻结,所有 evorule 生态必须对齐"

### 阶段 4:v1.0 强制对齐(2-4 周)

**目标**:所有 evorule 生态项目强制对齐 v1.0。

**产出**:
- 迁移工具链发布(PyPI / crates.io)
- 旧 v0.x 停止支持
- 至少 3 个真实项目完成 v0.x → v1.0 迁移

**发版动作**:
- [ ] 发布 `evorule-migrate` 到 PyPI
- [ ] evorule / evorule-server / evo-agent / evorule-rule 全部拒绝 v0.x 加载
- [ ] 启动错误信息提示项目方用 `evorule-migrate` 升级到 v1.0
- [ ] 旧 v0.x tag 标记为 deprecated
- [ ] CHANGELOG 公告 v0.x EOL

## Release Checklist(通用)

每个发版前确认:

- [ ] 所有 examples 通过 `evorule-migrate validate`
- [ ] 所有 migrations 通过 `evorule-migrate validate`
- [ ] 工具自检 `evorule-migrate list-kinds` 正常
- [ ] CHANGELOG.md 更新
- [ ] README.md 的"快速开始"命令可跑
- [ ] docs/ 链接无 404
- [ ] git tag 与 version 一致
- [ ] commit message 干净(用 UTF-8 + commit -F 避免 PowerShell 编码问题)

## 避免的常见错误

### 改 `$schema` URL 不更新 `version`

如果只更新 URL(`v0.9` → `v1.0`)但不改 `version` 字段:
- 工具找不到对应的 schema 文件
- 启动期校验失败

### migration 漏掉破坏性变更

每次主版本升级,必须:
1. 列所有破坏性变更
2. 每个变更写 1 个 transform
3. 用真实 system JSON 跑 upgrade,确认所有字段都正确处理

### 跳过逐级升级

不允许从 `v0.0` 直接跳到 `v1.0`,即使技术上可行:
- 跳过关键 migration 可能丢字段
- 工具强制逐级(项目方显式串)

## 紧急 hotfix

如果是 critical bug(例:某个字段定义错导致所有 system JSON 加载失败):

1. 评估严重性:是否影响所有 evorule 项目方?
2. 是 → 走 hotfix 分支,直接打 `v0.9.1` patch 版本
3. 在 CHANGELOG 标 `[HOTFIX]`
4. 通知所有 evorule 团队 + 项目方

**不允许**绕过 v1.0 冻结承诺(冻结后任何破坏性改动 = v2.0)。

## 延伸阅读

- [reference/version-protocol.md](../reference/version-protocol.md) — 双版本协议
- [explanation/00-evorule-explains-evorule.md](../explanation/00-evorule-explains-evorule.md) — 自举定位
- [ci-pipeline.md](./ci-pipeline.md) — CI 配置

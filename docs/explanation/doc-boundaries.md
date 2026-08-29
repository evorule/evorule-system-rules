<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 文档贡献指南

> 说明 evorule-system-rules 仓的文档结构、贡献流程、写作规范。

## 文档分层

evorule-system-rules 的公开文档按 [Diátaxis](https://diataxis.fr/) 框架组织,分四类:

| 类别 | 位置 | 用途 | 适合 |
|------|------|------|------|
| tutorial | `tutorial/` | 教学,手把手带新人 | 第一次接触的开发者 |
| how-to | `how-to/` | 任务式指南 | 卡在具体任务的人 |
| reference | `reference/` | 字典式参考 | 查阅确切信息 |
| explanation | `explanation/` | 原理与设计 | 想理解"为什么" |

加上 `adr/`(架构决策记录)和 `operations/`(运维与发布)。

## 写作规范

- **tutorial**:从空环境开始,一步步带你完成。每一步都到"能照着做"的颗粒度。**不**假设任何前置知识。
- **how-to**:目标明确(标题就是"如何 XXX"),步骤紧凑。可以假设读者已懂基本概念。
- **reference**:准确、完整、简洁。不解释为什么,只写"是什么"。尽量自动生成。
- **explanation**:讨论式,讲"为什么这么设计 / 不那么设计"。包含哲学/立场白皮书。
- **adr**:不可变历史快照。决策若变更,写新 ADR 并 supersede 旧的,**不要回头改旧文件**。
- **operations**:流程文档(发版、CI)。流程变了改文件,不改文件名。

## 命名规范

- `tutorial/`: `NN-标题.md`(如 `01-quickstart-validate.md`),NN 从 01 起
- `how-to/`: `动词-对象.md`(如 `validate-system-json.md`)
- `reference/`: 按"对象"命名(API 名 / CLI 子命令),不按"任务"
- `explanation/`: `NN-主题-副题.md`,NN 从 00 起(哲学立场从 00 起)
- `adr/`: `NNNN-kebab-case-title.md`(如 `0001-five-top-level-fields.md`)

## 文档头部

每个 .md 文件头部加版权注释:

```markdown
<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->
```

## 文档与仓根的关系

- **根 `*.md`**(README、CHANGELOG 等)是 L1 公开
- **本目录 `docs/`** 是 L1 公开的结构化补充
- 项目内部草稿、未定稿、设计过程文档不进入 `docs/`,在内部协作区流转,确认后由维护者提炼为公开版

## 贡献流程

1. 提 PR(走 evorule 团队标准 review)
2. CI 自动跑校验(`tools/evorule-migrate validate` + `tools/check_docs_links.py`)
3. Reviewer 关注:
   - 类别是否正确(tutorial / how-to / reference / explanation)
   - 是否符合命名规范
   - 是否暴露了内部信息(项目内部路径、未公开数据)
   - 重大决策是否需要先写 ADR

## 公开边界

公开文档**不**包含:
- ❌ 项目内部的具体路径、文件位置
- ❌ 内部研究数据、未公开的 bug 数字
- ❌ 内部讨论的"之前哪里错"
- ❌ 团队内部代号、流程细节
- ❌ 任何与 AI 工具 / 自动化系统相关的角色痕迹

公开文档**只**包含:
- ✅ 设计选型与决策理由(ADR 是不可变历史)
- ✅ 接口规范、字段定义、版本协议
- ✅ 使用方法、任务指南、教学
- ✅ 通用原则与设计哲学

## 内部信息如何公开化

如果研究 / 讨论产生了值得公开的洞察,应:
1. 提炼核心结论,丢弃过程
2. 改写为通用设计语言,去除具体项目名 / 路径
3. 以"evorule 生态"为主体,不强调内部研究中的具体问题
4. ADR 记录"选了 X,因为 Y",不记录"之前错在 Z"

## 链接检查

每次提交前跑:

```bash
python tools/check_docs_links.py
```

CI 也会跑,死链会阻塞合并。

## 延伸阅读

- evorule 仓的 `docs/introduction.md` — evorule 项目的文档导航(参考模板)

<!--
  Copyright 2026 EvoRule 元则 Project

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-License-Identifier: AGPL-3.0-or-later
-->

# evorule-system-rules 法律声明(本仓特定)

> **本文件是 evorule-system-rules 仓的特定法律声明**。它**不替代** LICENSE / COMMERCIAL_LICENSE.md / DUAL_LICENSE.md / FREE_COMMERCIAL_LICENSE.md / TRADEMARK.md / NOTICE.md,只是在那些通用文件之上,说明**本仓的特定立场与同步策略**。
>
> 如果本文件与上述通用文件冲突,**以通用文件为准**;但本文件是本仓 Scope A vs Scope B 分离模型的**权威解释入口**。

---

## 1. 与 evorule 主仓 license 文件的同步关系

本仓根目录的下列 6 个文件**以 evorule 主仓为权威来源**。但 6 件的**实际同步形态并不相同**,下表按 2026-10-23 实测逐件列出——**不要默认"同步 = 字节级一致"**:

| 本仓文件 | 权威来源 | 实际同步形态(2026-10-23 实测) |
|---|---|---|
| `LICENSE` | 主仓 `LICENSE` | **三仓字节级一致**(AGPL-3.0 标准全文,FSF 发布) |
| `FREE_COMMERCIAL_LICENSE.md` | 主仓同名文件 | **三仓字节级一致** |
| `TRADEMARK.md` | 主仓同名文件 | 主仓与本仓一致;evorule-rule 仓另有仓特定行 |
| `COMMERCIAL_LICENSE.md` | 主仓同名文件 | 条款正文一致;仅"网站"行按仓不同 |
| `NOTICE.md` | 主仓同名文件 | 条款正文一致;仅仓库 URL 行按仓不同;主仓另有"通道 D"一行 |
| `DUAL_LICENSE.md` | 主仓同名文件 | **存在实质分歧**:主仓含"通道 D(社区贡献授权)"整节(文档版本 2.0,2026-09-08),本仓与 evorule-rule 仓尚未追平 |

**同步原则**:

- 这 6 个文件**不在本仓独立维护**。如需修订,先在主仓修订,再同步到本仓。
- **同步形态分三档**:字节级一致(2 件)· 条款正文一致但含仓特定行(3 件)· 尚待追平(1 件)。**把"正文一致"当成"字节级一致"会踩空**——下游仓据此判断能否直接覆盖,结果覆盖掉自己的仓库 URL 行。
- 本文件(`LEGAL_NOTES.md`)是本仓**唯一**独立维护的法律文件,专门承载"本仓特定"的补充声明。
- 本仓如发现同步文件落后于主仓,以**主仓**为准;本仓修复。
- **已知未追平项(2026-10-23)**:`DUAL_LICENSE.md` 的"通道 D(社区贡献授权)"整节在本仓与 evorule-rule 仓缺失。补齐涉及对外协议文本,以项目方裁定为准,不自行追平。

## 2. 本仓特定立场(Scope A vs Scope B 分离)

evorule-system-rules 是**生态治理层**(Tier 1),所有 evorule 生态的 system JSON 都必须符合本仓 schema 定义的格式。但**格式治理**不等于**法律治理**。本仓的特定立场:

### 2.1 Scope A(本仓及主仓的 evorule 框架 IP)

Scope A 内部按**规范层 / 实现层**再分一层,两者协议不同:

| 资产 | 协议 |
|---|---|
| 本仓 `schemas/`(全部 JSON Schema) | **CC0 1.0 公共领域**(2026-08-29 决策,全文见 [schemas/LICENSE-SCHEMAS.md](./schemas/LICENSE-SCHEMAS.md)) |
| 本仓 `tools/` / `docs/` / ADR / 示例 | **AGPL-3.0-or-later + 商业双模式** |
| 主仓 `evorule-tcb` / `evorule-reactor` / `evorule-governance` / `evorule-cli` 等代码 | **AGPL-3.0-or-later + 商业双模式** |
| 主仓 `evorule-tcb/core_eval.json` | **CC0 1.0 公共领域**(因其"解释器规范"角色独立处理,见 §4) |

- 决定权:EvoRule 团队
- 商业许可咨询:<evorulelab@gmail.com>

### 2.2 Scope B(项目方的 system JSON 内容 IP)

- 包含:项目方用本仓 schema 创作的所有 system JSON(规则集、agent 定义、知识库、工作流、迁移规则、服务注册)
- 协议:**项目方自选** —— 通过 `metadata.license` 字段声明。合法枚举以 `_meta` v1.0 为准,共 9 值:
  `AGPL-3.0-or-later` / `AGPL-3.0` / `Apache-2.0` / `MIT` / `BSD-3-Clause` / `CC0-1.0` / `CC0-1.0 Universal (Public Domain)` / `Proprietary` / `Custom`
- 决定权:**项目方本人**
- evorule 不对 Scope B 内容做任何 IP 主张:不要求署名、不要求回馈、不参与分润、不强制披露
- **上游义务不因 Scope 分离而免除**:Scope B 内容中引入的第三方材料,其许可义务由引入方承担,见 [§5](#5-第三方来源材料义务)

**`knowledge` 双形态与内容 IP 归属**:`knowledge` 条目分两种形态,两者的内容 IP **都归数据作者**:

| 形态 | 字段 | 内容 IP 归属 |
|---|---|---|
| 文档知识条目 | `content`(人类可读正文) | 数据作者 |
| 数据资产条目 | `payload`(领域结构化数据)+ `schema_ref`(领域 JSON Schema 引用) | 数据作者 |

`schema_ref` 指向的领域 JSON Schema 归**领域仓**所有,本仓只定义引用契约(代管不代持);入库校验方按 `schema_ref` 取 schema 强校验 `payload`,resolver 未命中即拒绝(fail-fast)。

### 2.3 Scope 分离的法律基础

- AGPL-3.0 的 copyleft 效力**仅**附着在 **AGPL 协议的作品本身**(本仓的 tools、docs;schemas 已 CC0 无传染力),**不**对**使用 schema 创作的下游作品**施加传染。
- 这与"用 Microsoft Word 模板写文档,文档是项目方的"的常识一致;与"用 SQL 语法写查询,查询是作者的"的法律实践一致。
- 详细论证见 [docs/adr/scope-split-ip-model.md](./docs/adr/scope-split-ip-model.md)

## 3. 商业项目方场景澄清

商业项目方购买 evorule 商业许可的**覆盖范围**仅是 Scope A(本仓 + 主仓的 evorule 框架)。**项目方创作的 Scope B 内容不通过本许可覆盖**,因为:

1. Scope B 内容**本就归项目方所有**,evorule 无需"许可"项目方使用自己的内容。
2. 商业项目方买 evorule 商业许可是为了**合法使用 evorule 框架**(不公开自家产品的源代码),不是为了**获取自己内容的 IP**。
3. 商业项目方可任意处置 Scope B 内容(开源、闭源、SaaS、出售、定制),只要其产品中"使用 evorule 框架"的部分遵守 Scope A 商业许可即可。

具体商业许可条款细节见 [COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md);FAQ 见 [DUAL_LICENSE.md](./DUAL_LICENSE.md)。

## 4. 与 `core_eval.json` CC0 声明的关系

`evorule-tcb/core_eval.json`(主仓)采用 **CC0 1.0 公共领域**,原因在其 `metadata.public_domain_notice` 字段明确说明:**"本解释器规范是公共领域——任何人都可以实现兼容的 EvoRule 引擎"**。

本仓 schemas **同样采用 CC0 1.0 公共领域**(2026-08-29 决策,全文见 [schemas/LICENSE-SCHEMAS.md](./schemas/LICENSE-SCHEMAS.md)),理由:

- `core_eval.json` 是"解释器规范"(引擎在运行时读取并按其执行),有"允许多种实现"的战略诉求
- 本仓 schemas 是"格式规范"(用于校验 system JSON 的结构合规)——格式规范应自由被第三方工具链实现(校验器、IDE 插件、代码生成器、CLI),CC0 使规范层的法律负担归零
- 与 `core_eval.json` 先例衔接:同属"规范层资产 CC0、实现层资产 AGPL"的分层 IP 模型
- CC0 亦无损"单一权威"治理地位:治理权威来自治理模型与流程约束,不来自许可证限制

> 历史注记:2026-08-29 之前本节曾以"单一权威无需 CC0"为由不采用 CC0;经推广策略评估后立场修订为上述内容,原理由保留于 git 历史。

当前所有 evorule 系统 JSON **必须**走 evorule-system-rules 的 schema 治理,这是 Tier 1 治理模型的硬约束。

## 5. 第三方来源材料义务

Scope 分离划的是 **evorule 与项目方之间**的界,**不**处理**项目方与第三方之间**的许可义务。项目方(或规则集 / 知识库 / 技能包的贡献者)把自己不拥有的材料放进 system JSON 时,义务随材料一起转移过来——**evorule 不主张 IP ≠ 免除上游许可义务**。

本节是 **evorule 的工程与协作规则**,不是法律意见;具体项目请咨询执业律师。本仓不承诺任何材料已被清权,只规定**如何引入、如何标注、如何上架**。

### 5.1 来源四类分级

引入任何外部材料前,先判定它属于哪一类;不同类别走不同的许可路径:

| 类别 | 判定特征 | 可用范围 | 必须做的事 |
|---|---|---|---|
| **A 公共领域 / 政府与标准机构公开文本** | CC0 或公有领域声明;政府出版物、公开指南 | 可直接使用 | `metadata.provenance.source` 记 `imported`;条目内留来源标识、版本与获取日期 |
| **B 明确开源许可** | 标注了 MIT / Apache-2.0 / BSD / LGPL / GPL 等 | 可用,但**逐个按其许可履行义务** | 宽松许可:保留版权与许可声明;copyleft:先评估传染边界再入库 |
| **C 付费标准** | IPC / UL / IEC / ISO / ASTM 等以订阅或购买方式获取的文本 | **只取事实与数值,不复制文本与表格编排** | 记标准编号、版本、条款出处;用自己的话重述判据 |
| **D 专有或来源不明** | 厂商专有资料;授权链路无法确认 | **不可用** | 不得入库 |

### 5.2 事实与表达要分开处理

判据类材料大量是**事实**(数值、物理常数、公式、阈值)。事实与承载它的**表达**(原文段落、表格编排、图示)不是一回事,工程上的处理原则是:

- **事实层**:可以重述为自己的判据表达,并记录出处与独立复核结论
- **表达层**:不逐字搬运原文段落与表格编排
- **拿不准时**:先取得授权再使用

### 5.3 上架门:三条硬性要求

任何进入本仓治理链的外部来源材料,必须满足:

1. **来源可追溯** —— `metadata.provenance.source` 取 `manual` / `generated` / `derived` / `imported` 之一,并在条目内保留来源标识、版本与获取日期
2. **许可可标注** —— `metadata.license` 取 §2.2 的 9 个合法枚举值之一;无法归入任一枚举时用 `Custom` 并写明实际条款
3. **事实经复核** —— 引入的数值 / 阈值须有独立复核记录(谁复核、怎么复核、复核结论)。evorule 引擎只做**形式**校验(量纲、单位、冲突、循环、收敛),**不能**替你确认数值正确、条款未被曲解或版本未过期

### 5.4 copyleft 的边界

宽松许可(MIT / Apache-2.0 / BSD)不产生额外义务;copyleft(LGPL / GPL 等)的义务可能**穿透聚合**——把 copyleft 材料放进整体分发的产物里,署名与源码提供义务可能存活到整体。

因此:

- 判据集与技能包**按来源逐项隔离**:不同来源分条目存放,各自标 `metadata.license`,不混进同一份聚合产物
- 面向第三方分发的产物发布前,**逐来源过一遍许可**,不要假定"只是数据"就不受 copyleft 影响
- 授权链路不明的来源按 **D 类**处理(不可用),不按"善意推定"放行

## 6. Schema 自声明(机器可读层)

为让任何读 schema 的工具(包括第三方 validator、SDK、IDE 插件)都能获取本仓的 Scope 分离立场,本仓 schema 家族在 JSON Schema 顶层声明 `x_legal_authority_notice` 字段。这是一个 vendor extension,JSON Schema 规范允许,不影响 schema 验证逻辑,工具可读取该字段获知:

- 本 schema 由 EvoRule 团队维护,以 **CC0 1.0 公共领域**奉献(schemas/LICENSE-SCHEMAS.md)
- 读本 schema 验证的 system JSON 内容 IP 归作者所有,schema 本身无任何许可证主张

**覆盖范围(截至 v1.2)**:`schemas/<kind>/` 下各 kind 的 schema 文件均带该声明;`schemas/_shared/`(跨文件 `$defs` 单一事实源,非独立 kind schema)与 `schemas/domain/domain_schema.meta.v1.json`(扩展域 schema 元 schema)当前不带。

**正本位置**:本文件与 `docs/adr/scope-split-ip-model.md` 的正本在 **evorule-system-rules 仓根**。schema 中的 `../../LEGAL_NOTES.md` 与 `../../docs/adr/scope-split-ip-model.md` 是相对 `schemas/<kind>/` 的路径,在本仓完全解析得通;镜像副本仓(evorule-server 的 `core/rule_schema/`)不包含这两份文件,该相对路径在镜像侧不成立——**以本仓为正本**。

## 7. 修订历史

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0 | 2026-08-26 | 初版,与 LICENSE 修复同步发布;确立 Scope A vs Scope B 分离模型 |
| 1.1 | 2026-08-29 | `schemas/` 以 CC0 1.0 公共领域奉献(格式规范分层,与 core_eval 先例衔接);`x_legal_authority_notice` 机器可读声明同步更新 |
| 1.2 | 2026-10-23 | `metadata.license` 枚举对齐 `_meta` v1.0 实际值(9 值,原文档仅列 5 值);补 `knowledge` 双形态的内容 IP 归属;新增 §5 第三方来源材料义务(来源四类分级 / 事实与表达分离 / 上架门 / copyleft 边界);修正 §6 "每个 schema 文件" 的过宽表述,并标明正本位置与镜像侧路径说明 |
| 1.3 | 2026-10-23 | §1 同步关系表由"6 件字节级同步"改为**实测事实**(2 件真字节一致 / 3 件正文一致含仓特定行 / 1 件实质分歧),并登记 `DUAL_LICENSE.md` 通道 D 未追平项;`NOTICE.md` 协议分离表补 `schemas/` 一行(2026-08-29 CC0 决策此前未同步到对外声明) |

---

**最后更新**: 2026-10-23
**文档版本**: 1.3

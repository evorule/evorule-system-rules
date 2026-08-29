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

本仓根目录的下列 5 个文件**与 evorule 主仓(`D:\evorule\`)对应文件保持字节级同步**:

| 本仓文件 | 来源 | 同步方式 |
|---|---|---|
| `LICENSE` | `D:\evorule\LICENSE` | AGPL-3.0 标准全文(FSF 发布,与主仓字节级一致) |
| `COMMERCIAL_LICENSE.md` | `D:\evorule\COMMERCIAL_LICENSE.md` | 主仓商业许可协议摘要 |
| `DUAL_LICENSE.md` | `D:\evorule\DUAL_LICENSE.md` | 主仓双重许可说明 + FAQ |
| `FREE_COMMERCIAL_LICENSE.md` | `D:\evorule\FREE_COMMERCIAL_LICENSE.md` | 主仓非营利免费商业许可 |
| `TRADEMARK.md` | `D:\evorule\TRADEMARK.md` | 主仓商标使用政策 |
| `NOTICE.md` | `D:\evorule\NOTICE.md` | 主仓第三方归属声明 |

**同步原则**:

- 这 6 个文件**不在本仓独立维护**。如需修订,先在主仓修订,再同步到本仓。
- 本文件(`LEGAL_NOTES.md`)是本仓**唯一**独立维护的法律文件,专门承载"本仓特定"的补充声明。
- 本仓如发现 6 个同步文件与主仓不一致,以**主仓**为准;本仓修复。

## 2. 本仓特定立场(Scope A vs Scope B 分离)

evorule-system-rules 是**生态治理层**(Tier 1),所有 evorule 生态的 system JSON 都必须符合本仓 schema 定义的格式。但**格式治理**不等于**法律治理**。本仓的特定立场:

### 2.1 Scope A(本仓及主仓的 evorule 框架 IP)

- 包含:本仓的 `tools/` / `docs/` / ADR;主仓的 `evorule-tcb` / `evorule-reactor` / `evorule-governance` / `evorule-cli` 等 Rust 代码;以及 `evorule-tcb/core_eval.json`(后者为 **CC0 1.0 公共领域**,因其"解释器规范"角色独立处理)
- 协议:**AGPL-3.0-or-later + 商业双模式**(例外:本仓 `schemas/` 自 2026-08-29 起以 **CC0 1.0 公共领域** 奉献,见 [schemas/LICENSE-SCHEMAS.md](./schemas/LICENSE-SCHEMAS.md))
- 决定权:EvoRule 团队
- 商业许可咨询:<evorulelab@gmail.com>

### 2.2 Scope B(用户的 system JSON 内容 IP)

- 包含:用户用本仓 schema 创作的所有 system JSON(规则集、agent 定义、知识库、工作流、迁移规则、服务注册)
- 协议:**用户自选** —— 通过 `metadata.license` 字段声明,enum 为 `Apache-2.0` / `MIT` / `BSD-3-Clause` / `Proprietary` / `Custom`
- 决定权:**用户本人**
- evorule 不对 Scope B 内容做任何 IP 主张:不要求署名、不要求回馈、不参与分润、不强制披露

### 2.3 Scope 分离的法律基础

- AGPL-3.0 的 copyleft 效力**仅**附着在 **AGPL 协议的作品本身**(本仓的 tools、docs;schemas 已 CC0 无传染力),**不**对**使用 schema 创作的下游作品**施加传染。
- 这与"用 Microsoft Word 模板写文档,文档是用户的"的常识一致;与"用 SQL 语法写查询,查询是作者的"的法律实践一致。
- 详细论证见 [docs/adr/scope-split-ip-model.md](./docs/adr/scope-split-ip-model.md)

## 3. 商业用户场景澄清

商业用户购买 evorule 商业许可的**覆盖范围**仅是 Scope A(本仓 + 主仓的 evorule 框架)。**用户创作的 Scope B 内容不通过本许可覆盖**,因为:

1. Scope B 内容**本就归用户所有**,evorule 无需"许可"用户使用自己的内容。
2. 商业用户买 evorule 商业许可是为了**合法使用 evorule 框架**(不公开自家产品的源代码),不是为了**获取自己内容的 IP**。
3. 商业用户可任意处置 Scope B 内容(开源、闭源、SaaS、出售、定制),只要其产品中"使用 evorule 框架"的部分遵守 Scope A 商业许可即可。

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

## 5. Schema 自声明(机器可读层)

为让任何读 schema 的工具(包括第三方 validator、SDK、IDE 插件)都能获取本仓的 Scope 分离立场,本仓**每个 schema 文件**在 JSON Schema 顶层声明 `x_legal_authority_notice` 字段。这是一个 vendor extension,JSON Schema 规范允许,不影响 schema 验证逻辑,工具可读取该字段获知:

- 本 schema 由 EvoRule 团队维护,以 **CC0 1.0 公共领域**奉献(schemas/LICENSE-SCHEMAS.md)
- 读本 schema 验证的 system JSON 内容 IP 归作者所有,schema 本身无任何许可证主张

## 6. 修订历史

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0 | 2026-08-26 | 初版,与 LICENSE 修复同步发布;确立 Scope A vs Scope B 分离模型 |
| 1.1 | 2026-08-29 | `schemas/` 以 CC0 1.0 公共领域奉献(格式规范分层,与 core_eval 先例衔接);`x_legal_authority_notice` 机器可读声明同步更新 |

---

**最后更新**: 2026-08-29
**文档版本**: 1.1

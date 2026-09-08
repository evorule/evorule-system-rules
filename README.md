# evorule-system-rules

> 定型:evorule 生态的"系统元规则集",所有 evorule 系统 JSON 的 schema / 版本 / 升级权威
> **现行版本:v1.0(2026-08-27 固化;v0.9 双版本并存,迁移线 `v0.9-to-v1.0`)**
> 公开文档:`docs/`(Diátaxis + 设计规范 + mdbook)

## 这是什么

`evorule-system-rules` 是 evorule 生态的**系统宪法**——

定义 evorule 平台加载的所有"系统 JSON"应该长什么样,如何版本化,
以及 schema 升级时旧 JSON 怎么迁移。

**所有 evorule 生态的系统 JSON 必须由 evorule-system-rules 治理,
evorule-rule 是它的下游实现,所有 evorule 系统文件必须对齐并受其约束。**

## 6 个 kind

| kind | 用途 | 现有例子 |
|------|------|----------|
| `rule_set` | 业务规则集合 / TCB 规则集合 | `core_eval.json`、`yuanze_rules.json` |
| `agent_def` | agent 定义 | `evo-agent/agents/*.json` |
| `workflow_dag` | DAG 工作流 | `evo-agent/rules/workflows/*.json` |
| `service_registry` | 服务注册 / HTTP 路由 | `service_registry.json` |
| `knowledge` | 知识库 | `examples/knowledge.example.json`(D5 未验证草案;注:server 的 `docs/PITFALLS.json` 为豁免参照物,带自造壳,非本 kind 实例) |
| `migration` | $schema 升级迁移规则 | (本仓自产) |

每个 system JSON 必须有 5 个固定顶层字段 + kind-specific body:

```json
{
  "$schema": "https://evorule.org/schemas/<kind>/<version>.json",
  "kind": "<kind>",
  "id": "<org>.<scope>.<name>",
  "version": "<semver>",
  "metadata": { "title": "...", "created": "...", "updated": "..." },
  "<body>": ...
}
```

## 仓布局

```
evorule-system-rules/
  schemas/
    _shared/v1.0.json         共享 $defs(transform_rule 等,SSOT)
    _meta/v1.0.json           通用 5 顶层字段(另有 v0.9 历史版本)
    rule_set/v1.0.json        kind: rule_set(固化版)
    agent_def/v1.0.json       kind: agent_def(未验证草案,见 D5)
    workflow_dag/v1.0.json    kind: workflow_dag
    service_registry/v1.0.json
    knowledge/v1.0.json
    migration/v1.0.json       (各 kind v0.9 与 v1.0 双版本并存)
  examples/                   6 个 kind 的最小例子(service_registry 为 D2 sidecar 模式)
  migrations/                 $schema 升级规则(v0.0-to-v0.9 / v0.9-to-v1.0)
  tools/
    evorule-migrate           工具入口(validate / upgrade)
    verify_schemas.py         schema 全量校验 + examples 闭环 + 白名单对齐闸
    scan_repo_json.py         仓级数据格式门禁($schema 扫描)
    check_docs_links.py       docs/ 死链检查
    check_evoagent_assets.py  evo-agent 资产校验(已并入 verify-all 第 6 步)
  docs/                       公开文档(Diátaxis + 设计规范 + mdbook)
    book.toml
    SUMMARY.md
    introduction.md
    tutorial/                 教学
    how-to/                   任务式指南
    reference/                字典式参考
    explanation/              原理与设计(含哲学立场)
    adr/                      设计规范(已定型,非过程记录)
    operations/               运维与发布
  CHANGELOG.md
  LICENSE                     AGPL-3.0-or-later + 商业双许可
  COMMERCIAL_LICENSE.md       商业许可协议摘要(中文)
  DUAL_LICENSE.md             双重许可说明 + FAQ
  FREE_COMMERCIAL_LICENSE.md  非营利 / 开源项目免费商业许可
  TRADEMARK.md                商标使用政策
  NOTICE.md                   第三方依赖与归属声明
  README.md
```

## 快速开始

### 一键全量预检（推荐入口）

```bash
cd D:\evorule-system-rules
powershell -File verify-all.ps1
```

依次执行 6 步：schema 闭环验收 / docs 链接检查 / 拦截实证矩阵 / server 内嵌副本一致性 / 根仓数据格式门禁 / evo-agent 资产 schema 校验（后三步在对应仓缺失时容错跳过），任一失败即非零退出。

### 校验一个 system JSON

```bash
cd D:\evorule-system-rules
python tools/evorule-migrate validate path/to/your.json
```

> service_registry 主体可无 `$schema`——存在同名 `.meta.json` sidecar 时自动合并校验。

### 把 v0.9 JSON 升级到 v1.0

```bash
python tools/evorule-migrate upgrade path/to/old.json \
  --from-schema v0.9 --to-schema v1.0 \
  -o path/to/new.json
```

注意：rule_set 的 `rules[] → transform[]` 是语义翻译（rule_translate 职责），upgrade 输出会以 `<derived-by-rule_translate>` 占位并提示人工确认。

### 阅读文档

- 公开文档:打开 `docs/` 下的任何 .md,或运行 `mdbook serve docs/` 启动本地服务
- 文档导航:[docs/introduction.md](./docs/introduction.md)
- vault 私有工作区:`D:\knowledge\2-Projects\evorule-system-rules\`

详细见 [docs/](./docs/)。

## 3 层治理模型

```
evorule-system-rules  (Tier 1,系统宪法,evorule 团队维护)
        │
        ├─→  evorule              (Tier 2,evorule 自家系统)
        ├─→  evorule-server       (Tier 2,服务运行时)
        ├─→  evo-agent            (Tier 2,evorule 自家应用)
        └─→  evorule-rule         (Tier 2,治理层实现,**受 Tier 1 约束**)
                                          │
                                          └─→  用户业务规则  (Tier 3,通过 evorule-rule 多租户管理)
```

详细见 [docs/explanation/01-three-tier-governance.md](./docs/explanation/01-three-tier-governance.md)。

## 工作流(公开 / 私有)

```
        想法 / 问题
            │
            ▼
    ┌─────────────────┐
    │ 6-Research/     │  跨项目研究(跨 ≥2 项目)
    └────────┬────────┘
             │ 收敛到单项目
             ▼
    ┌─────────────────┐
    │ 2-Projects/...  │  试行稿、未定稿(私有)
    │ /design/        │
    └────────┬────────┘
             │ 确认 / 决策
             ▼
    ┌─────────────────┐
    │ evorule-system- │  正式发布(公开)
    │ rules/docs/     │
    └─────────────────┘
             │
             ▼
       重要规范沉淀为 adr/ 设计规范(已定型,确定性内容)
```

详细见 [docs/explanation/doc-boundaries.md](./docs/explanation/doc-boundaries.md)。

## 贡献

evorule 团队 + 受邀贡献者。提 PR 走标准 review 流程。

## 许可

**分层许可模型**(2026-08-29 起):

| 资产 | 协议 |
|---|---|
| `schemas/`(全部 JSON Schema) | **CC0 1.0 公共领域** — 见 [schemas/LICENSE-SCHEMAS.md](./schemas/LICENSE-SCHEMAS.md) |
| 其余资产(`tools/` / `docs/` / `examples/` / ADR 等) | **AGPL-3.0-or-later + 商业双模式** |

- 开源:[LICENSE](./LICENSE)(AGPL-3.0 标准全文)
- schema 公共领域声明:[schemas/LICENSE-SCHEMAS.md](./schemas/LICENSE-SCHEMAS.md)
- 双重许可说明 + FAQ:[DUAL_LICENSE.md](./DUAL_LICENSE.md)
- 商业许可协议(摘要):[COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md)
- 非营利 / 开源免费商业许可:[FREE_COMMERCIAL_LICENSE.md](./FREE_COMMERCIAL_LICENSE.md)
- 商标使用政策:[TRADEMARK.md](./TRADEMARK.md)
- 第三方归属:[NOTICE.md](./NOTICE.md)
- 商业许可 / FCL 资格咨询: evorulelab@gmail.com
- 本仓特定补充(双 scope IP 分离):[LEGAL_NOTES.md](./LEGAL_NOTES.md)

> **与 `core_eval.json` 的关系**:主仓(evorule)内 `evorule-tcb` crate 的 `core_eval.json` 因其"解释器规范"角色采用 **CC0 1.0 公共领域**;本仓 `schemas/` 因其"格式规范"角色同理采用 CC0——**规范层资产 CC0、实现层资产 AGPL+商业**的分层 IP 模型。`evorule-system-rules` 仓定位为生态**治理层**(所有 evorule 系统 JSON 必须受其格式治理),治理权威来自治理模型与流程约束,不来自许可证限制。

商业咨询: <evorulelab@gmail.com>

## 用户内容归属(Scope B)

**用户用 evorule-system-rules 的 schema 创作的所有系统 JSON(rule_set / agent_def / workflow_dag / service_registry / knowledge / migration)的知识产权,完全归用户所有。**

evorule 生态的 IP 与用户的 IP 是两个独立 scope,互不传染:

| Scope | 包含 | 协议 | 决定权 |
|---|---|---|---|
| **Scope A** evorule 自己的 IP | 本仓的 `tools/`、`docs/`、ADR(AGPL+商业)与 `schemas/`(CC0);主仓的 `evorule-tcb` / `evorule-reactor` / `evorule-governance` 等代码(AGPL+商业)与 `core_eval.json`(CC0) | 分层:规范层 CC0 + 实现层 AGPL-3.0-or-later + 商业双模式 | EvoRule 团队 |
| **Scope B** 用户的 IP | 用户填入 schema 的所有 system JSON(规则集、agent 定义、知识库、工作流等) | **用户自选**(通过 `metadata.license` 字段) | 用户本人 |

具体含义:

- ✅ **许可证不传染用户内容**:用本仓的 schema 写自己的 rule_set,不会因为 schema 的协议而被强制任何协议(schema 已 CC0,且格式/作品分离是通用法律原则)。schema 是"格式",内容是"作品",作者拥有作品。
- ✅ **用户可完全闭源**:`metadata.license` 字段的 `Proprietary` / `Custom` 选项就是为完全自有/闭源准备的。
- ✅ **用户可自由分发 / 商用 / 卖许可**:这是用户的权利,与 evorule 无关。
- ✅ **第三方做兼容 SDK**:本仓 schema 以 CC0 奉献,第三方读取 schema 编写校验器、IDE 插件等工具**无任何许可证约束**(工具与用户内容均可自选协议);工具读的用户内容同样不受任何传染。
- ❌ **用户内容不受 evorule 主张**:evorule 不对用户创作的内容做任何 IP 主张,不要求署名,不要求回馈,不分润。

**"受 evorule-system-rules 治理"** 仅指 **格式层面**(系统 JSON 必须符合 schema 定义的字段结构、类型、必填项),**不**指 **法律层面**(许可证、所有权、商业权利)。

详细规范见 [docs/adr/scope-split-ip-model.md](./docs/adr/scope-split-ip-model.md)。Schema 自身在 `x_legal_authority_notice` 字段也机器可读地声明了此点。

# 变更日志

所有 evorule-system-rules 的显著变更都记录在这里。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.0.0] - 2026-08-27

### 固化
- 6 个 kind 的 v1.0 schema 正式发布(rule_set / agent_def / workflow_dag / service_registry / knowledge / migration),与 v0.9 双版本并存,迁移线 `v0.0-to-v0.9`、`v0.9-to-v1.0`
- 新增共享定义包 `schemas/_shared/`(transform_rule / instruction 等 `$defs`,供各 kind 引用)

### 法律与 IP 分离模型
- 全部 schema 注入机器可读声明字段 `x_legal_authority_notice`(AGPL-3.0-or-later + 商业双许可;经 schema 校验或创作的内容 IP 归作者,evorule 不主张)
- 新增法律文件体系:LEGAL_NOTES / NOTICE / DUAL_LICENSE / COMMERCIAL_LICENSE / FREE_COMMERCIAL_LICENSE / TRADEMARK,设计依据见 `docs/adr/scope-split-ip-model.md`

### 规则格式统一改造
- yuanze_rules.json 等真实资产对齐 5 顶层字段 + v1.0(修复单数 `__io_result__` → 复数 `__io_results__`、非法元指令 save_memory 下线)
- examples 全部升级为 v1.0 形态;service_registry 采用主体+`.meta.json` sidecar 标注
- `_verify_schemas.py`:15 schema 合法性 + 门禁正负用例 + examples 闭环 + 白名单四向一致的全量验收基准

### 工具与守卫
- 新增 `tools/check_whitelist_sync.py`(6 元指令白名单四处同步守卫)与 `tools/check_docs_links.py`(docs 相对链接守卫)
- 新增 `_empirical_interception.py`(Opt1-4 拦截实证矩阵 × yuanze-demos)
- server 内嵌副本同步守卫 `check_schema_sync.py --sync`(双向:check / sync)
- 2026-08-27 收编:`_verify_schemas.py` → `tools/verify_schemas.py`(根目录保留薄 shim);`check_docs_links.py` 改为锚定仓根,不受 cwd 影响;新增一键预检 `verify-all.ps1`;CLI 支持 service_registry D2 sidecar 合并校验

### 文档
- Diátaxis 结构重整:theorem→tutorial / how-to / reference / explanation 四象限 + ADR 已定型规范格式


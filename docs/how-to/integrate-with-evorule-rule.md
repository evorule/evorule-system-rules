<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
<!-- Copyright (C) 2026 EvoRule 元则 Project -->

# 如何接入 evorule-rule 对齐

> 任务:evorule-rule 升级时,与 evorule-system-rules 保持对齐。

## 适用场景

- evorule-rule 主版本升级(跟随 Tier 1 `$schema` 主版本)
- evorule-rule 平台接入 schema 校验
- 验证 evorule-rule 字段定义与 Tier 1 一致

## 3 个层面的对齐

| 层面 | 内容 | 工具 |
|------|------|------|
| 字段对齐 | evorule-rule 字段命名/类型符合 Tier 1 schema | CI 强制检查 |
| 行为对齐 | evorule-rule 校验/迁移逻辑遵循 Tier 1 | 单元测试 |
| 版本对齐 | evorule-rule 主版本 = Tier 1 `$schema` 主版本 | release 流程约束 |

详见 [explanation/03-evorule-rule-alignment.md](../explanation/03-evorule-rule-alignment.md) 和 [设计规范(evorule-rule 对齐)](../adr/evorule-rule-must-align.md)。

## 字段如何用 Tier 1 表达

### RuleDataset → `kind: rule_set`

```rust
// evorule-rule 内部表示
struct RuleDataset {
    id: String,
    version: String,
    metadata: DatasetMetadata,
    entries: Vec<RuleEntry>,
    governance: Governance,
    provenance: Provenance,
    lifecycle: Lifecycle,
    dependencies: Vec<Dependency>,
}

// 对应 Tier 1 JSON 表达
{
  "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
  "kind": "rule_set",
  "id": "com.example.sales.validation",
  "version": "2.3.1",
  "metadata": {
    "title": "...",
    "lifecycle": { ... },   // 治理字段嵌入 metadata
    "provenance": { ... },
    "governance": { ... },
    "dependencies": [ ... ]
  },
  "rules": [ ... ]           // 内部 entries 序列化时改名为 rules
}
```

### 治理字段映射

| evorule-rule 字段 | Tier 1 表达 |
|-------------------|------------|
| `RuleDataset::governance` | `metadata.governance` |
| `RuleDataset::provenance` | `metadata.provenance` |
| `RuleDataset::lifecycle` | `metadata.lifecycle` |
| `RuleDataset::dependencies` | `metadata.dependencies` |
| `RuleEntry::id` | `rules[].id`(沿用) |
| `RuleEntry::when/then/transform` | `rules[].when/then/transform`(沿用) |

## 启动期校验

evorule-rule 启动时:

```rust
// 伪代码
fn startup_check() {
    let tier1_version = read_tier1_version();  // 从 evorule-system-rules/CHANGELOG.md
    let current_version = env!("CARGO_PKG_VERSION");

    if tier1_version.major != current_version.major {
        panic!("evorule-rule v{} 与 evorule-system-rules v{} 主版本失对齐,需升级",
               current_version, tier1_version);
    }

    // 字段对齐检查
    let field_alignment = check_field_alignment();
    if !field_alignment.is_ok() {
        panic!("字段失对齐:{:?}", field_alignment.errors);
    }
}
```

## 升级流程

| 步骤 | 负责方 | 内容 |
|------|------|------|
| 1 | evorule 团队 | 起草 Tier 1 v1.0(冻结点) |
| 2 | evorule-rule 团队 | 同步升级 evorule-rule v1.0,字段对齐 |
| 3 | evorule-rule 团队 | 运行完整 migration 测试 + 双向兼容测试 |
| 4 | evorule-rule 团队 | 发布 evorule-rule v1.0 |
| 5 | 平台项目方 | 升级 evorule-rule + 运行业务规则 migration |

## CI 强制检查

evorule-rule 仓的 CI 包含字段对齐检查:

```yaml
# .github/workflows/tier1-alignment.yml
name: Tier 1 Alignment Check
on: [push, pull_request]
jobs:
  alignment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Clone evorule-system-rules
        run: git clone --depth 1 <evorule-system-rules-git-url>
      - name: Run alignment check
        run: |
          python evorule-system-rules/tools/check_alignment.py \
            --tier1-dir evorule-system-rules/schemas \
            --evorule-rule-dir src/
```

`check_alignment.py` 是项目特定脚本,扫描 evorule-rule 源码中所有硬编码字段,验证均在 Tier 1 schema 中。

## 紧急情况:补充 Tier 1 临时未定义字段

evorule-rule 升级时,若业务紧急需要 Tier 1 临时未定义的字段:

1. **临时方案**:evorule-rule 使用 `metadata.custom.<key>: value` 形式(允许的扩展点)
2. **正式方案**:在下一个 Tier 1 minor 版本(如 v1.1)加入该字段
3. **CI 检查**:提示"该字段是临时的,需纳入正式 schema"

## 验收清单

evorule-rule v1.0 发布前确认:

- [ ] 所有字段定义与 Tier 1 v1.0 schema 完全对齐
- [ ] 启动期校验:失对齐 = 启动拒绝
- [ ] 单元测试覆盖 100% 的字段映射
- [ ] migration 测试覆盖 `v0.x → v1.0` 完整链路
- [ ] 双向兼容测试通过(新 evorule-rule 处理旧规则 + 旧 evorule-rule 拒绝新规则)
- [ ] CHANGELOG 注明与 Tier 1 v1.0 对齐

## 延伸阅读

- [explanation/03-evorule-rule-alignment.md](../explanation/03-evorule-rule-alignment.md) — 双重身份详解
- [设计规范(evorule-rule 对齐)](../adr/evorule-rule-must-align.md) — evorule-rule 必须对齐(设计规范)
- [reference/version-protocol.md](../reference/version-protocol.md) — 双版本协议

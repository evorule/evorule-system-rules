# schema 演进 SOP（三步照单办事）

> 建立：2026-09-22（四缝处置批次落地，源自历史施工中母本漂移的教训）
> 适用：任何对本仓 `schemas/` 的变更——新增字段、收紧门禁、勘误描述。

## 为什么需要 SOP

本仓是全生态系统 JSON 的**唯一权威**（系统 JSON schema 权威约束），server 侧持有内嵌副本。历史教训：
执行侧防御先行落地、母本未回灌，造成「副本比母本更严格」的 SSOT 倒挂（`check_schema_sync` exit=1 才暴露）；
同一文件头注与正文枚举矛盾长期并存。以下三步把这类缝挡在提交前。

## 三步（照单办事，不得跳步）

### 第 1 步：改母本（仅本仓）

- 只改 `schemas/` 下文件；`transform` 协议词、`$schema` URI、`x_legal_authority_notice` 原样保留。
- **红线**：确定性/可回放/可审计不可触碰——schema 变更只许落在描述与校验层，
  不改变引擎已消费的机器语义（`instruction_type`/域函数/状态路径等标识符不动）。
- 收紧型变更（如 `additionalProperties:false`）必须在变更说明中附**存量零命中评估**
  （对全部消费仓规则文件全扫确认无存量违例，否则收紧即拒载存量资产）。

### 第 2 步：verify-all 全绿

```powershell
powershell -File verify-all.ps1
```

- 首步即 python 环境预检（`jsonschema` 可导入性）——缺模块按提示
  `python -m pip install jsonschema` 后重跑。
- 任一步 FAIL 即终止修复，不允许带红提交；`server 内嵌副本一致性` 步骤
  在兄弟检出布局下自动执行（check-only）。

### 第 3 步：副本同步（双仓提交）

```powershell
# 检查（verify-all 已含 check-only；此处为主动同步）
python ..\evorule-server\scripts\check_schema_sync.py --sync
```

- 母本与 server 副本**同批提交、同批推送**（双仓各自的 commit + 防泄露扫描 + CI 绿灯）。
- 只跑 `--sync` 单边 = 重新制造漂移；`check_schema_sync.py` 默认 check-only，
  `--sync` 方向为**母本 → server 副本**，勿反向覆盖母本。

## 提交前自查清单

1. 母本 diff 是否只含描述/校验层变更（红线复核）。
2. `verify-all.ps1` exit 0。
3. server 副本已同步且双仓提交号成对留痕。
4. 文档（README/ADR/CHANGELOG）中涉及的字段口径是否随动——**文档同步是施工完毕的一部分，不是可选**。

## 历史教训索引

- 2026-09-22：历史施工曾在 server 副本添加条目级 `additionalProperties:false` 防御，母本未同步回灌
  （副本一致性检查实测 exit=1，同批闭环）；`_shared/v1.0.json` 头注「6 元指令」与正文 5 元枚举
  矛盾长期并存（同批闭环）。两缝均为本 SOP 立法动因。

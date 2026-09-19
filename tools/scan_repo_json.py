#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_repo_json.py —— 根仓数据格式门禁（宪法落地 E1-1）

扫描目标仓的 JSON 资产，落实"进入根仓的系统 JSON 必须带壳（$schema 合法）
或登记豁免"的约束。见 ISSUES_LEDGER R5 与 docs/explanation/04-governance-scope.md。

判定规则：
  1. 带 `https://evorule.org/schemas/` $schema 的文件 → 经 evorule-migrate validate
     做全量 schema 校验；
  2. 带"待迁移映射"私造 $schema 的文件 → [MAP] 登记（WARN 级,不 FAIL）:
     私造 DSL 迁移到正式 kind 需执行语义变更（另立小方案）,迁移前在此登记,
     防止私造 URI 无声扩散;
  3. 不带壳的文件 → 对照豁免清单（EXEMPT_PATTERNS，路径片段匹配）；
  4. 其余 → 违规，exit 1。

用法：
    python tools/scan_repo_json.py --repo D:/evorule
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATE = REPO_ROOT / "tools" / "evorule-migrate"

SKIP_DIRS = {"target", ".git", "node_modules", ".cargo", "dist"}

# 豁免清单：路径片段匹配（与 docs/explanation/04-governance-scope.md 登记保持一致）。
# 每条必须能回答判据三问：谁加载 / 是否参与生产执行链路 / 生命周期谁自管。
# 2026-09-15 存量清零专项：缓办事项的 53+6 条全部终裁——20 条目带壳整改，
# 其余按下述判据补登记（详见 ISSUES_LEDGER 存量豁免清零条目）。
EXEMPT_PATTERNS = [
    "tests/fixtures/",       # evorule-cli 等测试夹具（负向夹具依赖无壳语义本身）
    "tests/testdata/",
    "/tests/",               # 各 crate 内嵌测试目录
    "acceptance/",           # 验收夹具（随测试套自管）
    # ── schema 权威文件自身（自指：schema 不能引用自己；由 check_schema_sync
    #    + verify_schemas 守护，生命周期随本仓版本演进自管）──
    "core/rule_schema/schemas/",
    # ── 工具/开发配置（只被开发工具读取，不经任何引擎/服务加载路径）──
    ".markdownlint.json",
    "sdk/nodejs/package.json",
    # ── 合规签署台账（法律记录，顶层是签署条目数组；生命周期由合规流程自管）──
    "signatures/version1/cla.json",
    # ── server 工具内部资产：决策 #3（04-governance-scope 豁免表既有登记，
    #    此前工具漏同步）；由坑位守卫脚本读取，不经引擎 ──
    "docs/PITFALLS.json",
    # ── server 插件系统自有契约资产：plugin.json contract_version 体系 +
    #    pack 装载 6 项硬校验 + r2_gate 属地执法（加载门禁比 schema 壳更细），
    #    生命周期由插件系统契约演进自管 ──
    "plugins/",
    "plugin_manifest.json",
    "service_registry.json",
    # ── bundle 落盘溯源 manifest：bundle_land.rs 明确「不参与 loader 加载路径」，
    #    仅溯源/运行配置元数据；条目文件已于 2026-09-15 全部带壳并补 回归验证
    #    批次F 条目哈希基线（顶层 content_hash 为导入时溯源记录）──
    "bundle_manifest.json",
    # ── evo-agent 属地执法形态：agent_def/workflow_dag 运行时经
    #    constitution.rs 用 v1.0 schema 校验裸 body（04-governance-scope
    #    「属地执法义务」表 evo-agent 行 ✅）；带壳反而与裸 body 契约冲突 ──
    "agents/",
    "rules/workflows/",
    # ── 根仓 wasm 演示测试向量（bench/test 脚本夹具，不经引擎；构建产物
    #    rules_merged.json 已 gitignore 退出门禁面）──
    "evorule-wasm-demo/plan.json",
]

# 待迁移映射登记表（C6）：私造 $schema URI → 正式 kind 的迁移承诺。
# 背景：应用层 demo 仓（私名不公开）的 demo 规则是私造 DSL（trigger/condition/action,
# 由 application 仓自有解释器执行），与引擎原生 transform 不同构；迁移为
# rule_set v1.0 需执行语义变更，另立小方案。迁移完成前在此登记映射关系,
# 扫描以 [MAP] WARN 提示（不 FAIL）,但 URI 不得新增扩散（不在表内的
# 私造 URI 照常判违规）。
PENDING_MIGRATION_URIS = {
    "https://evorule.com/schema/v1/rule.json": {
        "target_kind": "rule_set",
        "scope": "application-layer demo (agent-guard / compliance-gate)",
        "note": "私造 DSL, 待执行语义变更小方案后迁移 rule_set v1.0",
    },
}


def is_exempt(rel_path: str) -> bool:
    p = rel_path.replace("\\", "/")
    return any(pat in ("/" + p.lstrip("/")) or p.startswith(pat) for pat in EXEMPT_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描仓库 JSON 资产的门禁合规性")
    parser.add_argument("--repo", required=True, help="待扫描的目标仓库路径")
    parser.add_argument(
        "--all-files", action="store_true",
        help="扫描文件系统全部 JSON（缺省仅扫 git 门禁面：已跟踪 + 未忽略未跟踪）",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[FAIL] 目标仓不存在:{repo}", file=sys.stderr)
        return 1

    print(f"[SCAN] {repo}")
    # 门禁面（缺省）：git 已跟踪 + 未被 .gitignore 忽略的未跟踪文件。
    # 语义 = "已进仓 + 即将进仓" 的系统 JSON 全集；构建产物/运行数据进
    # .gitignore 后自动出局（防止 payload/web/data 等产物噪音淹没真违规）。
    gate: set[str] | None = None
    if not args.all_files:
        r = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--cached", "--others",
             "--exclude-standard", "-z"],
            capture_output=True,
        )
        if r.returncode == 0:
            gate = {
                p.replace("\\", "/")
                for p in r.stdout.decode("utf-8", "surrogateescape").split("\0")
                if p.endswith(".json")
            }
        else:
            print("[WARN] git 不可用或非 git 仓——回退全文件系统扫描", file=sys.stderr)

    violations: list[str] = []
    shelled_ok = 0
    exempted = 0
    mapped = 0

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".json"):
                continue
            full = Path(root) / f
            rel = str(full.relative_to(repo)).replace("\\", "/")
            if gate is not None and rel not in gate:
                continue
            try:
                doc = json.loads(full.read_text(encoding="utf-8-sig"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                violations.append(f"{rel}: JSON 解析失败({e})")
                continue
            if not isinstance(doc, dict):
                # 顶层非对象（数组/标量）不可能是系统 JSON；豁免与否照常判定
                if is_exempt(rel):
                    exempted += 1
                else:
                    violations.append(f"{rel}: 无壳且不在豁免清单(顶层非对象)")
                continue

            schema_url = doc.get("$schema", "")
            if isinstance(schema_url, str) and schema_url.startswith("https://evorule.org/schemas/"):
                r = subprocess.run(
                    ["python", str(MIGRATE), "validate", str(full)],
                    capture_output=True, text=True,
                )
                if r.returncode == 0:
                    shelled_ok += 1
                    print(f"  [OK ] {rel} → {schema_url.rsplit('/', 1)[-1]}")
                else:
                    violations.append(f"{rel}: 有壳但校验失败\n{r.stdout}{r.stderr}")
            elif isinstance(schema_url, str) and schema_url in PENDING_MIGRATION_URIS:
                mapped += 1
                info = PENDING_MIGRATION_URIS[schema_url]
                print(f"  [MAP] {rel} → 待迁移 {info['target_kind']} ({info['note']})")
            elif is_exempt(rel):
                exempted += 1
                print(f"  [EXM] {rel} (豁免)")
            else:
                violations.append(f"{rel}: 无 $schema 且不在豁免清单——新进根仓的系统 JSON 必须带壳或先在 governance-scope 豁免表登记")

    print()
    print(f"带壳且校验通过: {shelled_ok}  |  豁免: {exempted}  |  待迁移映射: {mapped}  |  违规: {len(violations)}")
    if violations:
        print("\n[FAIL] 门禁违规:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("[OK] 全部合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())

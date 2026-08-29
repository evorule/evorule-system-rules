#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_repo_json.py —— 根仓数据格式门禁（宪法落地 E1-1）

扫描目标仓的 JSON 资产，落实"进入根仓的系统 JSON 必须带壳（$schema 合法）
或登记豁免"的约束。见 ISSUES_LEDGER R5 与 docs/explanation/04-governance-scope.md。

判定规则：
  1. 带 `https://evorule.org/schemas/` $schema 的文件 → 经 evorule-migrate validate
     做全量 schema 校验；
  2. 不带壳的文件 → 对照豁免清单（EXEMPT_PATTERNS，路径片段匹配）；
  3. 既无壳又不在豁免清单 → 违规，exit 1。

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
EXEMPT_PATTERNS = [
    "tests/fixtures/",       # evorule-cli 等测试夹具（负向夹具依赖无壳语义本身）
    "tests/testdata/",
    "/tests/",               # 各 crate 内嵌测试目录
    "acceptance/",           # 验收夹具（随测试套自管）
]


def is_exempt(rel_path: str) -> bool:
    p = rel_path.replace("\\", "/")
    return any(pat in ("/" + p.lstrip("/")) or p.startswith(pat) for pat in EXEMPT_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描仓库 JSON 资产的门禁合规性")
    parser.add_argument("--repo", required=True, help="待扫描的目标仓库路径")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[FAIL] 目标仓不存在:{repo}", file=sys.stderr)
        return 1

    print(f"[SCAN] {repo}")
    violations: list[str] = []
    shelled_ok = 0
    exempted = 0

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".json"):
                continue
            full = Path(root) / f
            rel = str(full.relative_to(repo))
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
            elif is_exempt(rel):
                exempted += 1
                print(f"  [EXM] {rel} (豁免)")
            else:
                violations.append(f"{rel}: 无 $schema 且不在豁免清单——新进根仓的系统 JSON 必须带壳或先在 governance-scope 豁免表登记")

    print()
    print(f"带壳且校验通过: {shelled_ok}  |  豁免: {exempted}  |  违规: {len(violations)}")
    if violations:
        print("\n[FAIL] 门禁违规:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("[OK] 全部合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())

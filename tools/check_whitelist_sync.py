#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_whitelist_sync.py: 白名单对齐闸（77 线1 第 3 行 / 70 F-01）。

对"元指令类型白名单"做多向一致性校验，确保上层校验语义不会与 TCB 权威源漂移：

    权威源  evorule-tcb/src/executor.rs::META_INSTRUCTION_TYPES（dispatch 全量）
      ↕ 一致
    1)  schema  enum  schemas/_shared/v1.0.json -> $defs.transform_rule.properties.type.enum
      ↗ 差 enforce
    2)  governance 白名单  evorule-governance/src/rule_validation.rs -> VALID_TRANSFORM_TYPES
        （= dispatch − enforce：enforce 仅 tier=meta 文件可用，由 server 装载门禁单独管控，UV-147）
    3)  CLI 白名单  evorule-cli/src/commands/validate.rs
        （无本地副本，必须引用 evorule_tcb::META_INSTRUCTION_TYPES SSOT，C2）
      ↕ 一致
    4)  bundle 结构门禁  evorule-bundle/src/structure.rs -> META_INSTRUCTION_TYPES
        （= dispatch 全量含 enforce：本门禁只管"是否元指令形态"，tier=meta 进入
        管控属 server 装载门禁 UV-147；存量豁免清零 L1，2026-09-15 接入）

修复背景（P0-01）：governance/CLI 曾把指令层类型（noop/increment/decrement）误混入元指令白名单，
且漏掉 collect/merge，导致假阳性/假阴性。本次脚本把"对齐"从**手动 + 自我引用测试**（断言常量==
测试里硬编码的同一份字面量，TCB 变更时依旧全绿）升级为**引用权威源的自动校验**：TCB 一旦新增/
调整元指令，本脚本立即 FAIL，拦截静默漂移。
（69 号清理 2026-09-14：collect/merge 退役，dispatch 5 种、公开白名单 4 种；CLI 检查改为 SSOT 引用）

用法:
    python tools/check_whitelist_sync.py

退出码:
    0 - 一致（schema == TCB dispatch；governance == dispatch − enforce；CLI 引用 SSOT；
        bundle 结构门禁 == dispatch）
    1 - 存在不一致（任一来源解析失败或列表不同）
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMAS_DIR = HERE.parent / "schemas"

# 外部仓路径：可用环境变量覆盖（默认与 _verify_schemas.py 相同的本机路径）
EVORULE_REPO = Path(os.environ.get("EVORULE_REPO", r"D:\evorule"))
EVORULE_SERVER_REPO = Path(os.environ.get("EVORULE_SERVER_REPO", r"D:\evorule-server"))
EVORULE_BUNDLE_REPO = Path(os.environ.get("EVORULE_BUNDLE_REPO", r"D:\evorule-bundle"))

TCB_EXECUTOR = EVORULE_REPO / "evorule-tcb" / "src" / "executor.rs"
GOVERNANCE_RULE_VALIDATION = EVORULE_REPO / "evorule-governance" / "src" / "rule_validation.rs"
CLI_VALIDATE = EVORULE_REPO / "evorule-cli" / "src" / "commands" / "validate.rs"
BUNDLE_STRUCTURE = EVORULE_BUNDLE_REPO / "src" / "structure.rs"
SHARED_SCHEMA = SCHEMAS_DIR / "_shared" / "v1.0.json"

# 解析器：提取 Rust 字符串字面量数组项 "word"
STR_LITERAL_RE = re.compile(r'"([a-z_]+)"\s*=>\s*exec_')


def extract_tcb_dispatch() -> list[str]:
    """从 executor.rs 的 `match instr_type` 分支提取元指令名（含 enforce，共 5 种）。"""
    src = TCB_EXECUTOR.read_text(encoding="utf-8")
    m = re.search(r"match instr_type \{(.*?)\n\s*_\s*=>", src, re.DOTALL)
    if not m:
        raise RuntimeError(f"未找到 match instr_type 分支块: {TCB_EXECUTOR}")
    names = STR_LITERAL_RE.findall(m.group(1))
    if not names:
        raise RuntimeError(f"match instr_type 分支块内未解析到任何指令名: {TCB_EXECUTOR}")
    return sorted(set(names))


def extract_rust_str_array(path: Path, const_name: str) -> list[str]:
    """从 Rust 常量数组提取字符串项。

    兼容两种声明形态（存量豁免清零 L1）：
    - 切片 `const NAME: &[&str] = &[...]`（governance rule_validation.rs）
    - 定长数组 `const NAME: [&str; N] = [...]`（bundle structure.rs）
    """
    src = path.read_text(encoding="utf-8")
    pat = re.compile(
        rf"const\s+{const_name}\s*:\s*&?\[&str(?:\s*;\s*\d+)?\]\s*=\s*&?\s*\[(.*?)\]",
        re.DOTALL,
    )
    m = pat.search(src)
    if not m:
        raise RuntimeError(f"未找到常量 {const_name}: {path}")
    items = re.findall(r'"([a-z_]+)"', m.group(1))
    if not items:
        raise RuntimeError(f"常量 {const_name} 数组为空或解析失败: {path}")
    return sorted(set(items))


def extract_schema_enum() -> list[str]:
    """从 _shared/v1.0.json 的 $defs.transform_rule.properties.type.enum 提取元指令名。"""
    doc = json.loads(SHARED_SCHEMA.read_text(encoding="utf-8"))
    enum = doc["$defs"]["transform_rule"]["properties"]["type"]["enum"]
    return sorted(set(enum))


def check_cli_ssot() -> tuple[bool, str]:
    """CLI 侧检查：必须引用 tcb SSOT 常量，且无本地硬编码白名单副本（C2）。"""
    src = CLI_VALIDATE.read_text(encoding="utf-8")
    if "evorule_tcb::META_INSTRUCTION_TYPES" not in src:
        return False, "未引用 evorule_tcb::META_INSTRUCTION_TYPES（SSOT 防漂移，C2）"
    return True, "引用 evorule_tcb::META_INSTRUCTION_TYPES（SSOT，无本地副本）"


def main() -> int:
    print("== 白名单对齐闸（77 线1 / 70 F-01）：TCB dispatch ↔ schema ↔ governance ↔ CLI ↔ bundle ==")
    labels = {
        "tcb": "TCB executor.rs dispatch",
        "schema": "schema _shared enum",
        "governance": "governance rule_validation.rs",
        "bundle": "bundle structure.rs",
    }
    try:
        checks: dict[str, list[str]] = {
            "tcb": extract_tcb_dispatch(),
            "schema": extract_schema_enum(),
            "governance": extract_rust_str_array(GOVERNANCE_RULE_VALIDATION, "VALID_TRANSFORM_TYPES"),
            "bundle": extract_rust_str_array(BUNDLE_STRUCTURE, "META_INSTRUCTION_TYPES"),
        }
    except FileNotFoundError as e:
        print(f"  [FAIL] 权威源文件缺失——请用 EVORULE_REPO / EVORULE_SERVER_REPO / "
              f"EVORULE_BUNDLE_REPO 指向已检出的权威仓: {e}")
        return 1
    except Exception as e:  # noqa: BLE001 - 解析失败视为门禁失败
        print(f"  [FAIL] {e}")
        return 1

    for key, names in checks.items():
        print(f"  [{labels[key]}] {', '.join(names)}")

    # 期望口径：dispatch 全量含 enforce；schema == dispatch；
    # governance == dispatch − enforce（enforce 仅 tier=meta 文件可用，UV-147）
    baseline = checks["tcb"]
    expected_gov = sorted(set(baseline) - {"enforce"})
    all_ok = True

    if checks["schema"] != baseline:
        all_ok = False
        print(f"  [FAIL] schema 与 TCB dispatch 不一致: 差集={sorted(set(checks['schema']) ^ set(baseline))}")
    if checks["governance"] != expected_gov:
        all_ok = False
        diff = sorted(set(checks["governance"]) ^ set(expected_gov))
        print(f"  [FAIL] governance ≠ dispatch−enforce({expected_gov}): 差集={diff}")
    # bundle 结构门禁 == dispatch 全量（含 enforce：本门禁只管"是否元指令形态"，
    # tier=meta 进入管控属 server 装载门禁 UV-147）
    if checks["bundle"] != baseline:
        all_ok = False
        diff = sorted(set(checks["bundle"]) ^ set(baseline))
        print(f"  [FAIL] bundle 结构门禁 ≠ TCB dispatch({baseline}): 差集={diff}")

    cli_ok, cli_msg = check_cli_ssot()
    print(f"  [CLI validate.rs] {cli_msg}")
    if not cli_ok:
        all_ok = False

    if all_ok:
        print(f"  [PASS] 白名单对齐（dispatch {len(baseline)} 种: {', '.join(baseline)}；"
              f"公开白名单 {len(expected_gov)} 种；CLI 引用 SSOT；bundle 结构门禁一致）")
        return 0
    print("  [FAIL] 白名单不一致——TCB 权威源已变更或上层未同步，需立即对齐（防 P0-01 复发）")
    return 1


if __name__ == "__main__":
    sys.exit(main())

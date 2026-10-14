# -*- coding: utf-8 -*-
"""[CON-R-004]/[CON-K3-001] 金样例覆盖率与 schema 双向断言（SR-15 件3）。

职责：
1. 覆盖率判据（条文原文口径）：每个 $def 名至少出现于一对样例文件名
   （<def>.valid.json + <def>.invalid.json）。目标 100%，未达 = exit 1。
2. schema 双向断言：每份合法样例过目标 schema；每份非法样例被目标 schema
   拒绝。任一侧不满足 = exit 1（conformance 的 schema 档）。

目标 schema 解析规则：
- golden/rule_set/<def>.*.json 且 def ∈ LOADER_DEFS → 完整 rule_set 文档，
  对 schemas/rule_set/v1.0.json 全文档校验（装载档金样例，conformance 的
  Rust 侧测试消费同批文件跑真实 load_rule_set——[CON-R-005]）。
- 其余 → def 级载荷，对「含该 def 的最新版本 schema」的 $defs/<def> 校验。
  def 名跨版本重复时（如 node）取最新版——覆盖口径按名（条文判据原文）。

用法: python tools/check_golden_coverage.py
"""
import json
import os
import re
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas")
GOLDEN_DIR = os.path.join(REPO_ROOT, "acceptance", "golden")
PASS, FAIL = 0, 1

# 装载档 def：样例=完整 rule_set 文档（经 load_rule_set 真装载路径）
LOADER_DEFS = {
    "path", "payload_attr_path", "path_or_literal",
    "domain", "instruction", "transform_rule",
}


def load_registry():
    resources = {}
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            sid = doc.get("$id")
            if not sid:
                continue
            resources[sid] = Resource.from_contents(doc)
    return Registry(resources=resources)


def build_def_inventory():
    """def 名 → 按版本降序的 (kind, version, schema_id) 列表（最新在前）。"""
    inv = {}
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            sid = doc.get("$id")
            m = re.match(r"^https://evorule\.org/schemas/([a-z_]+)/v(\d+)\.(\d+)\.json$", sid or "")
            if not m:
                continue
            kind, vmaj, vmin = m.group(1), int(m.group(2)), int(m.group(3))
            for name in doc.get("$defs", {}):
                inv.setdefault(name, []).append((kind, (vmaj, vmin), sid))
    for name in inv:
        inv[name].sort(key=lambda t: t[1], reverse=True)
    return inv


def target_for(def_name, kind_dir, inv):
    """返回 (target_schema, target_label)。找不到 def → None。"""
    if kind_dir == "rule_set" and def_name in LOADER_DEFS:
        return ({"allOf": [{"$ref": "https://evorule.org/schemas/rule_set/v1.0.json"}]},
                "rule_set/v1.0.json (full document)")
    if def_name not in inv:
        return None
    kind, _ver, sid = inv[def_name][0]
    return ({"allOf": [{"$ref": sid + "#/$defs/" + def_name}]},
            sid + "#/$defs/" + def_name)


def validate(schema, doc, registry):
    validator = Draft202012Validator(schema, registry=registry)
    return sorted(validator.iter_errors(doc), key=lambda e: list(e.path))


def main():
    registry = load_registry()
    inv = build_def_inventory()

    # 收集金样例：<def 名> → {"valid": [...], "invalid": [...]}
    found = {}
    problems = []
    for root, _dirs, files in os.walk(GOLDEN_DIR):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            m = re.match(r"^([A-Za-z0-9_]+)\.(valid|invalid)\.json$", f)
            if not m:
                problems.append(f"文件名不合口径（应 <def>.valid|invalid.json）: {os.path.relpath(os.path.join(root, f), GOLDEN_DIR)}")
                continue
            def_name, side = m.group(1), m.group(2)
            found.setdefault(def_name, {"valid": [], "invalid": []})[side].append(
                os.path.join(root, f))

    # 1) 覆盖率（按 $def 名）
    all_defs = sorted(inv.keys())
    uncovered = [d for d in all_defs if d not in found
                 or not found[d]["valid"] or not found[d]["invalid"]]
    covered = len(all_defs) - len(uncovered)
    print(f"[CON-R-004] 金样例覆盖率: {covered}/{len(all_defs)} defs")
    for d in uncovered:
        print(f"  [MISS] $def '{d}'（无成对样例文件名）")
    for p in problems:
        print(f"  [WARN] {p}")

    # 2) schema 双向断言
    bad = 0
    checked = 0
    for def_name, sides in sorted(found.items()):
        if def_name not in inv:
            print(f"  [WARN] 样例 def '{def_name}' 在 schemas/ 无对应 $defs（覆盖率按名忽略）")
            continue
        kind_dir = os.path.basename(os.path.dirname(sides["valid"][0])) if sides["valid"] \
            else os.path.basename(os.path.dirname(sides["invalid"][0]))
        tgt = target_for(def_name, kind_dir, inv)
        if tgt is None:
            print(f"  [FAIL] def '{def_name}' 目标 schema 解析失败")
            bad += 1
            continue
        schema, label = tgt
        for side, expect_valid in (("valid", True), ("invalid", False)):
            for path in sides[side]:
                checked += 1
                with open(path, "r", encoding="utf-8") as fh:
                    doc = json.load(fh)
                errors = validate(schema, doc, registry)
                ok = (len(errors) == 0) == expect_valid
                if not ok:
                    bad += 1
                    rel = os.path.relpath(path, REPO_ROOT)
                    print(f"  [FAIL] {rel} 期望{'通过' if expect_valid else '被拒'} 实际{'通过' if len(errors)==0 else '被拒'} @ {label}")
                    for e in errors[:5]:
                        print(f"      - {'/'.join(str(x) for x in e.path) or '<root>'}: {e.message}")
    print(f"[双向断言] 检查 {checked} 份样例, 违例 {bad}")
    if uncovered or bad or problems:
        print("[CON-R-004] FAIL（覆盖率未达 100% 或双向断言违例）")
        return FAIL
    print("[CON-R-004] PASS（覆盖率 100% + 双向断言全绿）")
    return PASS


if __name__ == "__main__":
    sys.exit(main())

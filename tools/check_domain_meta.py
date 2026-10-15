# -*- coding: utf-8 -*-
"""check_domain_meta.py：扩展层领域 schema 元纪律门（[CON-D-001]/[CON-D-003]，SR-17 件3/B3）。

判据（ SR-17 修订版，evorule-rule 恢复方案总设计 §四）：
    - 对 evorule-rule 仓 data/domain_schemas/*.json（除迁移映射表）逐件校验：
      1. 元 schema 校验：schemas/domain/domain_schema.meta.v1.json（必备件 $id/version/
         owner/reviewed_by/consumer，$id 须挂 domain 命名域）——jsonschema 全文校验；
      2. 命名域合规（双保险显式报错）：$id 以 https://evorule.org/schemas/domain/ 开头，
         宪法本域权威路径（/schemas/ 非 domain 段）不得被扩展层实体占用；
      3. 迁移映射表承接：data/domain_schemas/id-migration-map.json 在场，mappings 覆盖
         全部件（file 对应）、new_id 与该件实际 $id 一致、old_id 不再被任何件占用
         （迁移完成语义 = 旧 $id 永久退役）。
    - 任一件违规或映射表缺失 → 红灯 exit 1（CI 必挂）；全绿 exit 0。

落点：宪法仓 verify-all 第十四步（RG-1 件A3 rule 仓步之后，SR-17 件3/B3）。
用法: python tools/check_domain_meta.py
退出码: 0 = 全绿；1 = 存在违规；2 = 工具自身错（rule 仓/元 schema 不可得）
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
META_SCHEMA = REPO_ROOT / "schemas" / "domain" / "domain_schema.meta.v1.json"
PASS, FAIL, TOOL_ERR = 0, 1, 2
DOMAIN_PREFIX = "https://evorule.org/schemas/domain/"
MAP_NAME = "id-migration-map.json"


def locate_rule_repo() -> Path | None:
    """定位 evorule-rule 仓根（env 覆盖，缺省兄弟仓布局，与 verify_schemas 同约定）。"""
    env = os.environ.get("EVORULE_RULE_REPO")
    candidates = [Path(env)] if env else []
    candidates.append(REPO_ROOT.parent / "evorule-rule")
    for c in candidates:
        if (c / "data" / "domain_schemas").is_dir():
            return c
    return None


def main() -> int:
    rule_root = locate_rule_repo()
    if rule_root is None:
        print("[ERROR] 找不到 evorule-rule 仓（设 EVORULE_RULE_REPO 或按兄弟仓布局检出）", file=sys.stderr)
        return TOOL_ERR
    domain_dir = rule_root / "data" / "domain_schemas"
    if not META_SCHEMA.exists():
        print(f"[ERROR] 元 schema 缺失: {META_SCHEMA}", file=sys.stderr)
        return TOOL_ERR

    with open(META_SCHEMA, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    try:
        Draft202012Validator.check_schema(meta)
    except jsonschema.SchemaError as e:
        print(f"[ERROR] 元 schema 自身非法: {e}", file=sys.stderr)
        return TOOL_ERR
    validator = Draft202012Validator(meta)

    map_path = domain_dir / MAP_NAME
    schema_files = sorted(p for p in domain_dir.glob("*.json") if p.name != MAP_NAME)
    if not schema_files:
        print(f"[FAIL] data/domain_schemas/ 下未发现领域 schema 件（应 7 件）: {domain_dir}")
        return FAIL
    if not map_path.exists():
        print(f"[FAIL] 迁移映射表缺失: {map_path}（301 式旧 $id→新 $id 承接，SR-17 B2）")
        return FAIL
    with open(map_path, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    map_by_file = {m.get("file"): m for m in mapping.get("mappings", [])}

    print(f"== 扩展层元纪律门：{len(schema_files)} 件 × 元 schema（domain_schema.meta.v1）+ 命名域 + 映射承接 ==")
    all_ok = True
    old_ids_in_use: list[str] = []
    for p in schema_files:
        with open(p, "r", encoding="utf-8") as fh:
            try:
                doc = json.load(fh)
            except json.JSONDecodeError as e:
                print(f"  [FAIL] {p.name}: JSON 解析失败 {e}")
                all_ok = False
                continue
        errs: list[str] = []
        for e in sorted(validator.iter_errors(doc), key=lambda x: list(x.path)):
            errs.append(f"元schema: {'/'.join(str(s) for s in e.path) or '<root>'}: {e.message}")
        sid = doc.get("$id", "")
        if not sid.startswith(DOMAIN_PREFIX):
            errs.append(f"命名域: $id 未挂 domain 命名域（实际 {sid or '<缺>'}）——宪法本域权威路径不得被扩展层实体占用")
        m = map_by_file.get(p.name)
        if m is None:
            errs.append("映射承接: 迁移映射表无本件条目（mappings[].file 未覆盖）")
        else:
            if m.get("new_id") != sid:
                errs.append(f"映射承接: new_id={m.get('new_id')} 与实际 $id={sid} 不一致")
            old = m.get("old_id")
            if old:
                old_ids_in_use.append((p.name, old))
        if errs:
            all_ok = False
            print(f"  [FAIL] {p.name}（$id={sid}）")
            for msg in errs:
                print(f"    - {msg}")
        else:
            print(f"  [PASS] {p.name} -> {sid}")

    # 旧 $id 永久退役语义：任何件不得再占用映射表登记的旧值
    live_ids = set()
    for p in schema_files:
        with open(p, "r", encoding="utf-8") as fh:
            try:
                live_ids.add(json.load(fh).get("$id", ""))
            except json.JSONDecodeError:
                pass
    retired_hits = [(name, old) for name, old in old_ids_in_use if old in live_ids]
    if retired_hits:
        all_ok = False
        print(f"  [FAIL] 旧 $id 复活占用（迁移未完成语义）: {retired_hits}")

    print(f"== 结论: {len(schema_files)} 件，映射表条目 {len(map_by_file)}，旧 $id 复活 {len(retired_hits)} ==")
    print("ALL OK" if all_ok else "HAS FAILURES")
    return PASS if all_ok else FAIL


if __name__ == "__main__":
    sys.exit(main())

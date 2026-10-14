# -*- coding: utf-8 -*-
"""[CON-R-008]/[CON-L0-001] 宪法仓文件头自检（SR-15 件2）。

条文面：
- [CON-R-008] schemas/ 下每个 JSON 文件**必须**首字段为 $schema（自描述）
  且 $id 与路径一致；**应该**附 description 中文一句话。
- [CON-L0-001] 金样例中的系统 JSON 文档（装载档完整 rule_set 文档）必须以
  $schema 字段开头且指向宪法仓对应 schema URL。

判定分级：$schema 首字段/$id 一致=error（exit 1）；description 缺失或无
中文=warning（提示不红灯，条文「应该」面）。

用法: python tools/check_schema_headers.py
"""
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas")
GOLDEN_DIR = os.path.join(REPO_ROOT, "acceptance", "golden")
DRAFT_URL = "https://json-schema.org/draft/2020-12/schema"
PASS, FAIL = 0, 1
# 装载档 def（完整系统文档样例，须带头）——与 tools/check_golden_coverage.py 保持同表
LOADER_DEFS = {
    "path", "payload_attr_path", "path_or_literal",
    "domain", "instruction", "transform_rule",
}
CJK = re.compile(r"[\u4e00-\u9fff]")


def has_cjk(text):
    return bool(CJK.search(text or ""))


def check_schemas():
    errors, warnings, n = [], [], 0
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            n += 1
            p = os.path.join(root, f)
            rel = os.path.relpath(p, REPO_ROOT).replace(os.sep, "/")
            with open(p, "r", encoding="utf-8") as fh:
                try:
                    doc = json.load(fh, object_pairs_hook=lambda pairs: dict(pairs))
                except json.JSONDecodeError as e:
                    errors.append(f"{rel}: JSON 解析失败 {e}")
                    continue
            # 首字段 = $schema（保持键序读取）
            with open(p, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            keys = list(raw.keys())
            if not keys or keys[0] != "$schema":
                errors.append(f"{rel}: 首字段应为 $schema，实际为 {keys[0] if keys else '<空>'}")
                continue
            if raw["$schema"] != DRAFT_URL:
                errors.append(f"{rel}: $schema 应为 {DRAFT_URL}，实际 {raw['$schema']}")
            expect_id = "https://evorule.org/schemas/" + rel.split("schemas/", 1)[1]
            if raw.get("$id") != expect_id:
                errors.append(f"{rel}: $id 应为 {expect_id}，实际 {raw.get('$id')}")
            desc = raw.get("description")
            if not desc:
                warnings.append(f"{rel}: 缺 description（[CON-R-008] 应该面）")
            elif not has_cjk(desc):
                warnings.append(f"{rel}: description 非中文（[CON-R-008] 应该面）")
    return errors, warnings, n


def check_golden_headers():
    """[CON-L0-001] 金样例中系统文档（装载档）首字段=$schema 指向宪法 URL。"""
    errors, n = [], 0
    rule_set_dir = os.path.join(GOLDEN_DIR, "rule_set")
    for f in sorted(os.listdir(rule_set_dir)):
        if not f.endswith(".json"):
            continue
        def_name = f.rsplit(".", 2)[0] if f.count(".") >= 2 else f[:-5]
        if def_name not in LOADER_DEFS:
            continue
        n += 1
        p = os.path.join(rule_set_dir, f)
        with open(p, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        keys = list(doc.keys())
        if not keys or keys[0] != "$schema":
            errors.append(f"acceptance/golden/rule_set/{f}: 系统文档首字段应为 $schema，实际 {keys[0] if keys else '<空>'}")
            continue
        if not str(doc["$schema"]).startswith("https://evorule.org/schemas/"):
            errors.append(f"acceptance/golden/rule_set/{f}: $schema 未指向宪法仓 URL: {doc['$schema']}")
    return errors, n


def main():
    s_errors, s_warnings, n_schemas = check_schemas()
    g_errors, n_golden = check_golden_headers()
    for e in s_errors + g_errors:
        print(f"  [ERROR] {e}")
    for w in s_warnings:
        print(f"  [WARN]  {w}")
    print(f"[CON-R-008] schemas/ 自检 {n_schemas} 文件: error {len(s_errors)}, warning {len(s_warnings)}")
    print(f"[CON-L0-001] 金样例系统文档头检查 {n_golden} 文件: error {len(g_errors)}")
    if s_errors or g_errors:
        print("[CON-R-008/L0-001] FAIL")
        return FAIL
    print("[CON-R-008/L0-001] PASS（error 面 0；warning 为应该面提示）")
    return PASS


if __name__ == "__main__":
    sys.exit(main())

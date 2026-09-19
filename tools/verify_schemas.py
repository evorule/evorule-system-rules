# -*- coding: utf-8 -*-
"""闭环验收脚本（CI 门禁）：验证 v1.0 schema 合法 + 真实文件符合度 + 白名单对齐闸。
用法: python tools/verify_schemas.py
（2026-08-27 由根目录 _verify_schemas.py 收编至此；根目录保留薄 shim 兼容旧调用）
"""
import json
import os
import sys

import jsonschema
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas")
PASS, FAIL = 0, 1

# 外部仓路径：可用环境变量覆盖（CI 传参），默认按兄弟仓布局推导（<检出根>/<repo>，与 tools/check_whitelist_sync.py 同约定）
_CHECKOUT_ROOT = os.path.dirname(REPO_ROOT)
EVORULE_REPO = os.environ.get("EVORULE_REPO") or os.path.join(_CHECKOUT_ROOT, "evorule")
EVORULE_SERVER_REPO = os.environ.get("EVORULE_SERVER_REPO") or os.path.join(_CHECKOUT_ROOT, "evorule-server")
YUANZE_DEMOS = os.environ.get("YUANZE_DEMOS") or os.path.join(_CHECKOUT_ROOT, "yuanze-demos")


def load_registry():
    """加载 schemas/ 下所有 schema 文件，按 $id 注册为 Registry。"""
    resources = {}
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for f in files:
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


def validate_doc(doc, schema_path, registry):
    """返回 (errors_absent, errors)。errors_absent=True 表示校验通过（无错误）。"""
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    return (len(errors) == 0), errors


def case(doc, schema_path, registry, label, expect_valid):
    """执行一个用例。expect_valid=True 期望通过；False 期望被拒。"""
    ok, errors = validate_doc(doc, schema_path, registry)
    result = (ok == expect_valid)
    status = "PASS" if result else "FAIL"
    print(f"  [{status}] {label}")
    if not result:
        for e in errors[:20]:
            print(f"    - {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
    return result


def load_real(path, label, required=True):
    """加载外部仓真实 JSON 文件。缺失时 required=True → FAIL；required=False → SKIP。
    返回 (ok, doc)。"""
    if not os.path.exists(path):
        if required:
            print(f"  [FAIL] {label}: 真实文件不存在 {path}")
        else:
            print(f"  [SKIP] {label}: 外部仓可选，未提供 {path}")
        return False, None
    with open(path, "r", encoding="utf-8-sig") as fh:
        return True, json.load(fh)


def check_schema_valid(schema_path, registry):
    with open(schema_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    try:
        Draft202012Validator.check_schema(doc)
        print(f"  [PASS] schema 合法: {os.path.relpath(schema_path, SCHEMAS_DIR)}")
        return True
    except Exception as e:
        print(f"  [FAIL] schema 非法: {os.path.relpath(schema_path, SCHEMAS_DIR)}: {e}")
        return False


def main():
    registry = load_registry()
    all_ok = True

    print("== 1. schema 文件自身合法性 ==")
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            all_ok &= check_schema_valid(os.path.join(root, f), registry)

    rs_schema = os.path.join(SCHEMAS_DIR, "rule_set", "v1.0.json")
    sr_schema = os.path.join(SCHEMAS_DIR, "service_registry", "v1.0.json")

    print("\n== 2. 真实文件闭环验收（正向 = 期望通过；负向 = 期望被拒）==")

    # --- rule_set 正向 ---
    ok, core_eval = load_real(os.path.join(EVORULE_REPO, "evorule-tcb", "core_eval.json"), "core_eval.json")
    all_ok &= ok
    if ok:
        annotated = dict(core_eval)
        annotated.update({
            "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
            "kind": "rule_set",
            "id": "com.evorule.tcb.core_eval",
            "version": "0.3.1",
        })
        all_ok &= case(annotated, rs_schema, registry, "core_eval.json + 5 标注字段 (rule_set v1.0)", True)

    ok, demo = load_real(os.path.join(EVORULE_SERVER_REPO, "rules", "10_role13_demo.json"), "10_role13_demo.json")
    all_ok &= ok
    if ok:
        demo_ann = dict(demo)
        demo_ann.update({
            "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
            "kind": "rule_set",
            "id": "com.evorule.demo.role13",
            "version": "0.1.0",
        })
        all_ok &= case(demo_ann, rs_schema, registry, "10_role13_demo.json + 5 标注字段 (rule_set v1.0)", True)

    ok, yuanze = load_real(os.path.join(YUANZE_DEMOS, "server-config", "rules", "yuanze_rules.json"), "yuanze_rules.json", required=False)
    if ok:
        y_ann = dict(yuanze)
        y_ann.update({
            "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
            "kind": "rule_set",
            "id": "com.yuanze.robot.quality_control",
            "version": "1.0.0",
        })
        all_ok &= case(y_ann, rs_schema, registry, "yuanze_rules.json 对象 + 5 顶层字段 (rule_set v1.0)", True)

    # --- service_registry 正向（合并视图）---
    ok, sr_yuanze = load_real(os.path.join(YUANZE_DEMOS, "server-config", "service_registry.json"), "yuanze service_registry", required=False)
    if ok:
        merged = dict(sr_yuanze)
        merged.update({
            "$schema": "https://evorule.org/schemas/service_registry/v1.0.json",
            "kind": "service_registry",
            "id": "com.evorule.demo.service_registry",
            "version": "0.1.0",
            "metadata": {"title": "yuanze-demos 服务注册"},
        })
        all_ok &= case(merged, sr_schema, registry, "yuanze service_registry 合并视图 (service_registry v1.0)", True)

    ok, sr_server = load_real(os.path.join(EVORULE_SERVER_REPO, "service_registry.json"), "evorule-server service_registry")
    all_ok &= ok
    if ok:
        merged2 = dict(sr_server)
        merged2.update({
            "$schema": "https://evorule.org/schemas/service_registry/v1.0.json",
            "kind": "service_registry",
            "id": "com.evorule.server.service_registry",
            "version": "0.1.0",
            "metadata": {"title": "evorule-server 服务注册"},
        })
        all_ok &= case(merged2, sr_schema, registry, "evorule-server service_registry 合并视图 (service_registry v1.0)", True)

    # --- rule_set 负向 ---
    bad_domain = {
        "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
        "kind": "rule_set", "id": "com.evorule.neg.bad_domain", "version": "0.1.0",
        "metadata": {"title": "负向"},
        "transform": [{"type": "branch", "params": {
            "domain": {"type": "not", "domain": {"type": "eq", "path": "x", "value": 1}},
            "on_true": []}}],
    }
    all_ok &= case(bad_domain, rs_schema, registry, "负向：not.domain（应 inner）→ 期望被拒", False)

    bad_pseudo = {
        "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
        "kind": "rule_set", "id": "com.evorule.neg.pseudo", "version": "0.1.0",
        "metadata": {"title": "负向"},
        "rules": [{"id": "R001", "when": {"expr": "x>0"}, "then": {"set": "y=1"}}],
    }
    all_ok &= case(bad_pseudo, rs_schema, registry, "负向：rules[]+when/then 伪语言 → 期望被拒", False)

    bad_mix = {
        "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
        "kind": "rule_set", "id": "com.evorule.neg.mix", "version": "0.1.0",
        "metadata": {"title": "负向"},
        "transform": [{"type": "increment", "params": {"attr": "x", "operation": "add", "value": 1}}],
    }
    all_ok &= case(bad_mix, rs_schema, registry, "负向：元指令层出现 increment（混层）→ 期望被拒", False)

    bad_when = {
        "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
        "kind": "rule_set", "id": "com.evorule.neg.when", "version": "0.1.0",
        "metadata": {"title": "负向"},
        "transform": [{"type": "branch", "params": {
            "domain": {"type": "all", "inner": []},
            "on_true": [], "on_false": []}}],
    }
    all_ok &= case(bad_when, rs_schema, registry, "正向：all([]) 空 inner 兜底（应为合法）", True)

    # --- v1.0 固化专项（对照 TCB 源码：set.value / __ 前缀 / 退役原语拒载）---
    def rs(transform):
        return {
            "$schema": "https://evorule.org/schemas/rule_set/v1.0.json",
            "kind": "rule_set", "id": "com.evorule.neg.x", "version": "0.1.0",
            "metadata": {"title": "专项"},
            "transform": transform,
        }

    # set 缺 value → 引擎 MissingField（exec_set resolve_path_or_literal(None)）→ 应被拒
    all_ok &= case(rs([{"type": "set", "params": {"attr": "x", "operation": "set"}}]),
                   rs_schema, registry, "负向：set 缺 value（引擎 MissingField）→ 期望被拒", False)

    # collect/merge 已退役（69 号清理计划 2026-09-14）→ schema 枚举移除 → 应被拒
    all_ok &= case(rs([{"type": "merge", "params": {
        "messages": "__exec__.payload.llm_response.messages",
        "tool_results": "__exec__.payload.service_results",
        "next_instruction": {"type": "call_external", "params": {"messages": "{{messages}}"}}}}]),
        rs_schema, registry, "负向：merge 已退役（69 号，枚举移除）→ 期望被拒", False)

    all_ok &= case(rs([{"type": "merge", "params": {
        "messages": "__exec__.payload.llm_response.messages",
        "next_instruction": {"type": "noop"}}}]),
        rs_schema, registry, "负向：merge 已退役（69 号，枚举移除）→ 期望被拒", False)

    # branch.domain 字符串非 __ 前缀 → resolve_path_or_literal 当字面量 → 运行时报错 → 应被拒
    all_ok &= case(rs([{"type": "branch", "params": {
        "domain": "payload.flag", "on_true": []}}]),
        rs_schema, registry, "负向：domain 字符串无 __ 前缀（运行时报 MissingField）→ 期望被拒", False)

    # push.instructions 数组内非 __ 前缀字符串 → 被当字面量指令 → 应被拒
    all_ok &= case(rs([{"type": "push", "params": {"instructions": ["payload.then"]}}]),
        rs_schema, registry, "负向：push.instructions 内无 __ 前缀字符串 → 期望被拒", False)

    # collect 已退役（69 号清理计划 2026-09-14）→ schema 枚举移除 → 应被拒
    all_ok &= case(rs([{"type": "collect", "params": {
        "from": "__exec__.payload.llm_response.tool_calls",
        "each": {"type": "noop"},
        "after": {"type": "noop"}}}]),
        rs_schema, registry, "负向：collect 已退役（69 号，枚举移除）→ 期望被拒", False)

    # ===== Opt1 + Opt2：路径语法 + __io_results__ 复数强制（yuanze-demos 实证）=====
    # 权威源：evorule-tcb/src/path.rs（Opt1）、P1-03 复数协议（Opt2）。
    # 正向=期望通过（防假阳性）；负向=期望被拒（防假阴性，拦截运行时 PathResolutionFailed）。
    print("\n== Opt1/2：路径语法 + __io_results__ 复数（yuanze-demos 实证）==")

    demos_dir = os.path.join(YUANZE_DEMOS, "tests")

    # --- Opt2 正向：demos 已全部修正为复数 __io_results__（单数拦截由下方内联负向用例承担）---
    demos_fixed = {
        "08.json": "sampling_decider: exists __io_result__ 单数",
        "012.json": "generate_patch: exists __io_result__ 单数",
        "013.json": "sandbox_validate: exists __io_result__ 单数",
        "014.json": "hotload_patch: exists __io_result__ 单数",
        "016.json": "conflict_scanner: __io_result__ 单数 + save_memory 非法元指令",
    }
    for fname, why in demos_fixed.items():
        ok_load, doc = load_real(os.path.join(demos_dir, fname), f"demos/{fname}", required=False)
        if ok_load:
            all_ok &= case(rs([doc]), rs_schema, registry,
                           f"正向：demos/{fname}（{why}）→ 期望通过", True)

    # --- Opt2 正向：修正为复数后应通过（无假阳性；基于 08.json 仅替换单数为复数）---
    ok_load, doc08 = load_real(os.path.join(demos_dir, "08.json"), "demos/08.json", required=False)
    if ok_load:
        fixed = json.loads(json.dumps(doc08))  # 深拷贝
        def fix_paths(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(v, str) and "__io_result__" in v:
                        node[k] = v.replace("__io_result__", "__io_results__")
                    else:
                        fix_paths(v)
            elif isinstance(node, list):
                for item in node:
                    fix_paths(item)
        fix_paths(fixed)
        all_ok &= case(rs([fixed]), rs_schema, registry,
                       "正向：demos/08 修正为复数 __io_results__ → 期望通过", True)

    # --- Opt1 正向：demos 中路径合法的规则应通过（无假阳性）---
    ok_load, doc09 = load_real(os.path.join(demos_dir, "09.json"), "demos/09.json", required=False)
    if ok_load:
        all_ok &= case(rs([doc09]), rs_schema, registry,
                       "正向：demos/09.json（路径合法 branch）→ 期望通过", True)

    # --- Opt1 负向：路径语法错误（set.attr / domain.path / io_request 参数）---
    for bad_path in ["x.", ".x", "x..y", "items[0]..name", "[0", "[]", "[abc]", "[0]abc", "foo bar"]:
        all_ok &= case(rs([{"type": "set", "params": {"attr": bad_path, "operation": "set", "value": 1}}]),
                       rs_schema, registry, f"负向：set.attr 路径语法 {bad_path!r} → 期望被拒", False)

    all_ok &= case(rs([{"type": "branch", "params": {
        "domain": {"type": "exists", "path": "payload.audit."},
        "on_true": []}}]),
        rs_schema, registry, "负向：domain.path 尾部空段 'payload.audit.' → 期望被拒", False)

    all_ok &= case(rs([{"type": "io_request", "params": {
        "io_type": "call_service", "service_name": "svc", "args": "__exec__.payload._args."}}]),
        rs_schema, registry, "负向：io_request args 路径尾部空段 → 期望被拒", False)

    # --- Opt1 正向：合法特殊路径（$ / 索引 / 纯索引段 / 复数 I/O 结果）---
    # （UV-146 方案 a：set.attr 禁 payload. 前缀——相对路径或 __exec__.payload. 显式全形式）
    for good in ["__exec__.payload.$schema", "data[0]", "data.[0]", "a.b[2].c",
                 "__exec__.payload.__io_results__.call_service"]:
        all_ok &= case(rs([{"type": "set", "params": {"attr": good, "operation": "set", "value": 1}}]),
                       rs_schema, registry, f"正向：set.attr 合法路径 {good!r} → 期望通过", True)
    # --- Opt1 负向：payload. 前缀双重嵌套写歪（UV-146 方案 a，payload_attr_path 拒载）---
    all_ok &= case(rs([{"type": "set", "params": {"attr": "payload.a.b[2].c", "operation": "set", "value": 1}}]),
                   rs_schema, registry, "负向：set.attr payload. 前缀双重嵌套（UV-146）→ 期望被拒", False)

    # --- Opt2 显式：单数 vs 复数 I/O 结果字段 ---
    all_ok &= case(rs([{"type": "branch", "params": {
        "domain": {"type": "exists", "path": "__exec__.payload.__io_results__.call_service"},
        "on_true": []}}]),
        rs_schema, registry, "正向：exists __exec__.payload.__io_results__（复数）→ 期望通过", True)

    all_ok &= case(rs([{"type": "branch", "params": {
        "domain": {"type": "exists", "path": "__exec__.payload.__io_result__.call_service"},
        "on_true": []}}]),
        rs_schema, registry, "负向：exists __exec__.payload.__io_result__（单数）→ 期望被拒", False)

    all_ok &= case(rs([{"type": "set", "params": {"attr": "x", "operation": "set",
                                                  "value": "__exec__.payload.__io_result__.trigger"}}]),
        rs_schema, registry, "负向：set.value 引用单数 __io_result__ → 期望被拒", False)

    # ===== Opt3：指令层结构门禁（sequence/conditional/set attr）=====
    # instruction $defs 覆盖控制流结构；此处用 push.instructions 触发指令层递归校验。
    # --- sequence 结构负向：instructions 缺项 / 非数组 ---
    all_ok &= case(rs([{"type": "push", "params": {"instructions": [
        {"type": "sequence", "params": {}}]}}]),
        rs_schema, registry, "负向：sequence 缺 instructions（指令层结构）→ 期望被拒", False)

    all_ok &= case(rs([{"type": "push", "params": {"instructions": [
        {"type": "conditional", "params": {"domain": {"type": "eq", "path": "x", "value": 1}}}
    ]}}]),
        rs_schema, registry, "负向：conditional 缺 then/else（指令层结构）→ 期望被拒", False)

    # --- set 指令层 attr 路径负向（防 x. 运行时错误）---
    all_ok &= case(rs([{"type": "push", "params": {"instructions": [
        {"type": "set", "params": {"attr": "payload.x.", "operation": "set", "value": 1}}]}}]),
        rs_schema, registry, "负向：指令层 set.attr 尾部空段 → 期望被拒", False)

    # --- while_loop 结构负向：缺 condition/body ---
    all_ok &= case(rs([{"type": "push", "params": {"instructions": [
        {"type": "while_loop", "params": {"condition": {"type": "lt", "path": "x", "value": 3}}}
    ]}}]),
        rs_schema, registry, "负向：while_loop 缺 body（指令层结构）→ 期望被拒", False)

    # ===== knowledge 双形态（Q12 数据资产化：文档条目 + 数据条目互斥契约）=====
    # 权威源：schemas/knowledge/v1.0.json（2026-08-30 升格重设计）。
    # 正向=期望通过（防假阳性）；负向=期望被拒（防假阴性，拦截二义条目）。
    print("\n== knowledge 双形态（Q12 数据资产化）==")

    def kn(entries):
        return {
            "$schema": "https://evorule.org/schemas/knowledge/v1.0.json",
            "kind": "knowledge", "id": "com.evorule.neg.kn", "version": "1.0.0",
            "metadata": {"title": "knowledge 专项"},
            "entries": entries,
        }

    kn_schema = os.path.join(SCHEMAS_DIR, "knowledge", "v1.0.json")

    # 正向：文档条目（content）
    all_ok &= case(kn([{"id": "P001", "content": "知识正文。", "severity": "info"}]),
                   kn_schema, registry, "正向：文档条目 content → 期望通过", True)

    # 正向：数据条目（payload + schema_ref，payload 任意 JSON 含 null/标量）
    all_ok &= case(kn([{"id": "D001", "payload": {"k": [1, 2.5, None]}, "schema_ref": "https://rpsm.evorule.org/schemas/scenario/v1.0.json"}]),
                   kn_schema, registry, "正向：数据条目 payload+schema_ref → 期望通过", True)

    # 正向：双形态混排
    all_ok &= case(kn([{"id": "P001", "content": "文档。"}, {"id": "D001", "payload": {"x": 1}, "schema_ref": "uri:x"}]),
                   kn_schema, registry, "正向：文档+数据混排 → 期望通过", True)

    # 负向：content 与 payload 共存（二义）→ 期望被拒
    all_ok &= case(kn([{"id": "X001", "content": "文档。", "payload": {"x": 1}, "schema_ref": "uri:x"}]),
                   kn_schema, registry, "负向：content+payload 共存（二义）→ 期望被拒", False)

    # 负向：content 与 schema_ref 共存（无 payload 的悬空引用）→ 期望被拒
    all_ok &= case(kn([{"id": "X002", "content": "文档。", "schema_ref": "uri:x"}]),
                   kn_schema, registry, "负向：content+schema_ref 悬空引用 → 期望被拒", False)

    # 负向：数据条目缺 schema_ref（D3 强校验：无领域 schema 的 payload 不得入库）→ 期望被拒
    all_ok &= case(kn([{"id": "X003", "payload": {"x": 1}}]),
                   kn_schema, registry, "负向：payload 缺 schema_ref（D3 强校验）→ 期望被拒", False)

    # 负向：数据条目缺 payload（悬空 schema_ref）→ 期望被拒
    all_ok &= case(kn([{"id": "X004", "schema_ref": "uri:x"}]),
                   kn_schema, registry, "负向：schema_ref 缺 payload → 期望被拒", False)

    # 负向：既无 content 也无 payload（空条目）→ 期望被拒
    all_ok &= case(kn([{"id": "X005", "title": "空条目"}]),
                   kn_schema, registry, "负向：无 content 无 payload（空条目）→ 期望被拒", False)

    print("\n== 结论 ==")
    print("ALL OK" if all_ok else "HAS FAILURES")
    return 0 if all_ok else 1


def main_examples():
    """examples/ 下每个示例按 $schema 指向的本地 schema 闭环验证。"""
    registry = load_registry()
    all_ok = True
    examples_dir = os.path.join(REPO_ROOT, "examples")
    print("\n== 3. examples 闭环（按 $schema 指向本地 schema 验证）==")
    for f in sorted(os.listdir(examples_dir)):
        if not f.endswith(".json") or f.endswith(".meta.json"):
            continue
        p = os.path.join(examples_dir, f)
        with open(p, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        url = doc.get("$schema", "")
        # 把 https://evorule.org/schemas/<kind>/vX.Y.json 映射到本地 schemas/<kind>/vX.Y.json
        if not url.startswith("https://evorule.org/schemas/"):
            print(f"  [SKIP] {f}: 无 evorule 本地 schema URL")
            continue
        rel = url[len("https://evorule.org/schemas/"):]
        schema_path = os.path.join(SCHEMAS_DIR, rel)
        if not os.path.exists(schema_path):
            print(f"  [FAIL] {f}: schema 文件不存在 {schema_path}")
            all_ok = False
            continue
        ok, errors = validate_doc(doc, schema_path, registry)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {f} -> {rel}")
        if not ok:
            for e in errors[:20]:
                print(f"    - {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
            all_ok = False
    print("  ALL OK" if all_ok else "  HAS FAILURES")
    return all_ok


if __name__ == "__main__":
    # 本文件已位于 tools/，与 check_whitelist_sync 同目录即可导入
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_whitelist_sync  # 白名单对齐闸（77 线1 / 70 F-01）

    ok_main = main()  # 返回 0（成功）/ 1（失败）
    ok_ex = main_examples()  # 返回 True/False
    print("\n== 4. 白名单对齐闸 ==")
    ok_ws = (check_whitelist_sync.main() == 0)
    sys.exit(0 if (ok_main == 0 and ok_ex and ok_ws) else 1)

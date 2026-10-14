#!/usr/bin/env python3
"""check_version_discipline.py：宪法 schema 版本号纪律门（[CON-G-003] 禁无声版本）。

判级规则（SR-15 件10 宪法 G 系条文）：
    - 存量版本文件（schemas/**.json 修改）：剥 description 后结构等价 = 描述级，
      版本不动合法；结构面变化 = 红灯——结构变化必须落**新版本文件**，禁止原地改版。
    - 文件新增：合法（版本演进 = 新版本文件落新文件）；附 advisory 提示
      （与同 kind 前一版本对比判 major/minor，major 须附迁移器检查项 [CON-K5-001]）。
    - 文件删除：结构内容与任一新增文件等价 → 视为版本演进（旧文件被新版本取代）合法；
      否则红灯（版本废弃须走 schema 演进 SOP，不得静默删除）。

结构面判定：递归剥除各级 "description" 键后比较 JSON 等价——description-only
变更属描述级轻流程（[CON-G-001]），其余一切变化（required/enum/properties/$defs/
$id 等）均为结构面。

用法：
    python tools/check_version_discipline.py [--base origin/main] [--json]

退出码：
    0 - 无违规
    1 - 存在无声版本/静默删除（红灯）
    2 - 工具自身错（git 失败 / 基准分支不可得）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCOPE = "schemas/"

VER_RE = re.compile(r"^v(\d+)\.(\d+)(?:\.(\d+))?\.json$")


def strip_descriptions(node, drop=("description",)):
    """递归剥除指定键（默认 description），返回可比较的规范化结构。"""
    if isinstance(node, dict):
        return {k: strip_descriptions(v, drop) for k, v in node.items() if k not in drop}
    if isinstance(node, list):
        return [strip_descriptions(v, drop) for v in node]
    return node


def inheritance_struct(content: str):
    """承接比对用：版本 bump 必然改 $id，故比对时额外剥除顶层 $id。"""
    struct = strip_descriptions(json.loads(content) if content.strip() else None)
    if isinstance(struct, dict):
        struct.pop("$id", None)
    return struct


def structural(content: str):
    try:
        return strip_descriptions(json.loads(content))
    except json.JSONDecodeError:
        return None  # 语法坏档不在此门判，交由 verify_schemas 红灯


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {result.stderr.strip()}")
    return result.stdout


def resolve_base(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("origin/main", "main"):
        try:
            run_git(["rev-parse", "--verify", candidate])
            return candidate
        except RuntimeError:
            continue
    raise RuntimeError("找不到基准分支（origin/main 与 main 均不可用）")


def repo_toplevel() -> Path:
    """锚定被测 git 仓根（非脚本所在仓）——支持从任意检出/临时仓运行。"""
    try:
        return Path(run_git(["rev-parse", "--show-toplevel"]).strip())
    except RuntimeError:
        return Path(__file__).resolve().parent.parent


def changed_schema_files(base: str) -> tuple[list[str], list[str], list[str]]:
    """返回 (added, deleted, modified) 三清单（--no-renames 使改名呈 A+D 对）。"""
    out = run_git(["diff", "--no-renames", "--name-status", base, "--", SCOPE])
    added: list[str] = []
    deleted: list[str] = []
    modified: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0][0], parts[-1]
        if not path.endswith(".json"):
            continue
        if status == "A":
            added.append(path)
        elif status == "D":
            deleted.append(path)
        elif status == "M":
            modified.append(path)
    return added, deleted, modified


def git_show(base: str, path: str) -> str | None:
    try:
        return run_git(["show", f"{base}:{path}"])
    except RuntimeError:
        return None


def version_key(path: str):
    m = VER_RE.match(Path(path).name)
    if not m:
        return None
    return tuple(int(g or 0) for g in m.groups())


def advisory_level(added_path: str) -> str | None:
    """对新增版本文件给 major/minor advisory（不影响退出码）。"""
    kind_dir = Path(added_path).parent
    new_content = Path(added_path).read_text(encoding="utf-8")
    new_struct = structural(new_content)
    if new_struct is None:
        return None
    prev_files = [
        p for p in kind_dir.glob("*.json")
        if p.as_posix() != added_path and version_key(p.as_posix()) is not None
    ]
    if not prev_files:
        return None
    prev = max(prev_files, key=lambda p: version_key(p.as_posix()))
    old_struct = structural(prev.read_text(encoding="utf-8"))
    if old_struct is None:
        return None
    old_defs = set(old_struct.get("$defs", {}))
    new_defs = set(new_struct.get("$defs", {}))
    if new_defs - old_defs:
        return f"minor（新增 $def: {sorted(new_defs - old_defs)}）"
    if old_struct == new_struct:
        return "无结构变化（与前一版本等价，确认是否有必要升版）"
    # 逐 kind 顶层比较 required / enum / properties
    old_props = old_struct.get("properties", {})
    new_props = new_struct.get("properties", {})
    old_req = set(old_struct.get("required", []))
    new_req = set(new_struct.get("required", []))
    if new_req - old_req:
        return f"major（required 新增: {sorted(new_req - old_req)}，breaking 须附迁移器 [CON-K5-001]）"
    if set(new_props) - set(old_props):
        return f"minor（新增字段: {sorted(set(new_props) - set(old_props))}）"
    if set(old_props) - set(new_props):
        return f"major（字段删除: {sorted(set(old_props) - set(new_props))}，breaking 须附迁移器 [CON-K5-001]）"
    for name in set(old_props) & set(new_props):
        old_enum = old_props[name].get("enum")
        new_enum = new_props[name].get("enum")
        if isinstance(old_enum, list) and isinstance(new_enum, list):
            if set(new_enum) < set(old_enum):
                return f"major（{name} enum 收窄: {sorted(set(old_enum) - set(new_enum))}，breaking 须附迁移器 [CON-K5-001]）"
            if set(new_enum) - set(old_enum):
                return f"minor（{name} enum 扩充: {sorted(set(new_enum) - set(old_enum))}）"
    return "minor（结构性调整，人工核对判级表）"


def main() -> int:
    parser = argparse.ArgumentParser(description="宪法 schema 版本号纪律门（CON-G-003）")
    parser.add_argument("--base", default=None, help="diff 基准（默认 origin/main，缺则回退 main）")
    parser.add_argument("--json", action="store_true", dest="as_json", help="以 JSON 输出")
    args = parser.parse_args()

    repo_root = repo_toplevel()

    try:
        base = resolve_base(args.base)
        added, deleted, modified = changed_schema_files(base)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    violations: list[str] = []
    advisories: list[str] = []
    ok_lines: list[str] = []
    deleted_structs = []
    for path in deleted:
        old = git_show(base, path)
        deleted_structs.append(inheritance_struct(old) if old is not None else None)
    added_structs = []
    for path in added:
        content = (repo_root / path).read_text(encoding="utf-8")
        added_structs.append(inheritance_struct(content))

    for path, added_struct in zip(added, added_structs):
        level = advisory_level(path)
        if level:
            advisories.append(f"  [ADV] {path}: {level}")
        ok_lines.append(f"  [OK] 新增 {path}（版本演进落新文件）")

    for path, del_struct in zip(deleted, deleted_structs):
        if del_struct is not None and del_struct in added_structs:
            ok_lines.append(f"  [OK] 删除 {path}（结构内容由新版本文件承接）")
        else:
            violations.append(
                f"  [RED] {path}: 版本文件被静默删除——版本废弃须走 schema 演进 SOP"
                "（或以新版本文件承接后删除，见 [CON-G-003]）"
            )

    for path in modified:
        old = git_show(base, path)
        new = (repo_root / path).read_text(encoding="utf-8")
        old_struct, new_struct = (structural(old) if old else None), structural(new)
        if old_struct is None or new_struct is None:
            violations.append(f"  [RED] {path}: JSON 不可解析，先修复语法再提审")
            continue
        if old_struct == new_struct:
            ok_lines.append(f"  [OK] {path}: 描述级变更（description-only），版本不动合法")
        else:
            violations.append(
                f"  [RED] {path}: 结构面变化而版本未动（无声版本禁令 [CON-G-003]）——"
                "结构变化必须落新版本文件（如 schemas/<kind>/vX.Y.Z.json），存量版本文件仅许 description 级变更"
            )

    if args.as_json:
        print(json.dumps({
            "base": base,
            "violations": [v.strip() for v in violations],
            "advisories": [a.strip() for a in advisories],
            "passed": len(violations) == 0,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"[GATE] 宪法 schema 版本号纪律（[CON-G-003]，diff vs {base}）")
        for line in ok_lines:
            print(line)
        for line in advisories:
            print(line)
        for line in violations:
            print(line)

    if violations:
        print(f"[FAIL] 版本号纪律违规 {len(violations)} 项（无声版本禁令 [CON-G-003]）")
        return 1
    print("[PASS] 版本号纪律检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

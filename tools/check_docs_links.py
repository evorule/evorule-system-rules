#!/usr/bin/env python3
"""
check_docs_links.py:检查 docs/ 内 .md 文件的相对链接是否指向 404。

用法:
    python tools/check_docs_links.py [--docs-dir docs] [--summary docs/SUMMARY.md]

退出码:
    0 - 所有链接 OK
    1 - 有死链
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def extract_links(md_path: Path) -> list[tuple[str, str, int]]:
    """从 .md 文件提取所有 (text, target, line_no) 三元组。"""
    links = []
    for i, line in enumerate(md_path.read_text(encoding="utf-8").splitlines(), 1):
        for m in LINK_RE.finditer(line):
            text, target = m.group(1), m.group(2)
            # 跳过 URL / 锚点 / 邮件
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            links.append((text, target, i))
    return links


def check_links(docs_dir: Path, summary_path: Path | None) -> int:
    """检查 docs_dir 下所有 .md 文件的相对链接。"""
    errors: list[str] = []
    checked = 0

    md_files = sorted(docs_dir.rglob("*.md"))
    if summary_path:
        md_files.append(summary_path)

    for md in md_files:
        for text, target, line_no in extract_links(md):
            # 解析相对路径(去掉 #anchor)
            anchor = ""
            if "#" in target:
                target, anchor = target.split("#", 1)
            if not target:
                continue  # 纯锚点链接
            target_path = (md.parent / target).resolve()
            checked += 1
            if not target_path.exists():
                errors.append(
                    f"  [DEAD] {md.relative_to(docs_dir.parent)}:{line_no}  "
                    f"-> {target}  (text: {text!r})"
                )

    if errors:
        print(f"[FAIL] 发现 {len(errors)} 个死链(共检查 {checked} 个链接):")
        for e in errors:
            print(e)
        return 1

    print(f"[OK] 全部 {checked} 个链接通过")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 docs/ 内 .md 相对链接")
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="docs 目录(默认 <仓库根>/docs,自动锚定脚本位置,不受 cwd 影响)",
    )
    parser.add_argument("--summary", default=None, help="SUMMARY.md 路径(默认随之锚定)")
    args = parser.parse_args()

    # 2026-08-27 修复：默认值改为相对本脚本定位仓根，杜绝取证时 cwd 污染
    # （曾因在错误目录执行，把 evo-agent/docs 当成本仓扫描产生误报）。
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = (
        Path(args.docs_dir).resolve()
        if args.docs_dir
        else repo_root / "docs"
    )
    summary_path = (
        Path(args.summary).resolve()
        if args.summary
        else repo_root / "docs" / "SUMMARY.md"
    )

    if not docs_dir.exists():
        print(f"[FAIL] docs 目录不存在:{docs_dir}", file=sys.stderr)
        return 1

    return check_links(docs_dir, summary_path if summary_path.exists() else None)


if __name__ == "__main__":
    sys.exit(main())

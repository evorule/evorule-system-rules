#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M7-B 预检：用修订后的 v1.0 schema 校验 evo-agent 真实资产。

真实资产无壳——按 quick-start 路径，把 5 标注字段作为独立标注层合成
（等价于 sidecar 合并视图），再走 jsonschema 全量校验。
此脚本是 B1/B2 接入前的真值回归：三个 agents/*.json + 一个 workflow。
"""
import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

REPO = Path(__file__).resolve().parent.parent
EA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\evo-agent")


def load_registry() -> Registry:
    reg = Registry()
    for p in (REPO / "schemas").rglob("*.json"):
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
        if isinstance(doc, dict) and "$id" in doc:
            reg = reg.with_resource(doc["$id"], Resource.from_contents(doc))
    return reg


def shelved(doc: dict, schema_url: str, kid: str, pid: str) -> dict:
    """给裸文档合成 5 标注字段(合并视图)。"""
    out = {
        "$schema": schema_url,
        "kind": kid,
        "id": pid,
        **doc,
    }
    # version 字段冲突:agent_def 自带内容版本号,id 层 semver 用资产现值
    out.setdefault("version", doc.get("version", "1.0.0"))
    out["metadata"] = {"title": doc.get("description", "")[:200], "authors": ["mavis@evorulelab.com"]}
    return out


def main() -> int:
    reg = load_registry()
    cases = [
        ("agents/general.json", "agent_def", "com.evoagent.agent.general", "schemas/agent_def/v1.0.json"),
        ("agents/researcher.json", "agent_def", "com.evoagent.agent.researcher", "schemas/agent_def/v1.0.json"),
        ("agents/rule-copilot.json", "agent_def", "com.evoagent.agent.rule_copilot", "schemas/agent_def/v1.0.json"),
        ("rules/workflows/research_and_write.json", "workflow_dag", "com.evoagent.workflow.research_and_write", "schemas/workflow_dag/v1.0.json"),
    ]
    failures = 0
    for rel, kid, pid, schema_rel in cases:
        raw = json.loads((EA / rel).read_text(encoding="utf-8-sig"))
        doc = shelved(raw, f"https://evorule.org/schemas/{kid}/v1.0.json", kid, pid)
        schema = json.loads((REPO / schema_rel).read_text(encoding="utf-8-sig"))
        errs = sorted(jsonschema.Draft202012Validator(schema, registry=reg).iter_errors(doc), key=lambda e: list(e.path))
        if errs:
            failures += 1
            print(f"[FAIL] {rel}")
            for e in errs[:5]:
                print(f"   - {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:160]}")
        else:
            print(f"[OK]   {rel}")
    print()
    print("RESULT:", "ALL PASS" if failures == 0 else f"{failures} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

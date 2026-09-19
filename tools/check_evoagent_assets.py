#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M7-B 预检：用修订后的 v1.0 schema 校验 evo-agent 等真实资产。

evo-agent 的 agents/*.json + workflow 为裸文档——按 quick-start 路径，把
5 标注字段作为独立标注层合成（等价于 sidecar 合并视图），再走 jsonschema
全量校验。
检出根下的 rule_set 资产仓（core_eval/agent_core_eval.json，已按 C7 换壳为
rule_set v1.0 完整壳，参照 evo-agent agent_constitution.json 范式）直接全量校验。
此脚本是 B1/B2 接入前的真值回归。
"""
import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO.parent  # 多仓检出根（兄弟仓布局）


def _find_rule_set_repo():
    """在检出根下自动发现含 core_eval/agent_core_eval.json 的兄弟仓（避免公开文件携带私有仓名）。"""
    for cand in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        if (cand / "core_eval" / "agent_core_eval.json").is_file():
            return cand
    return None


EA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evo-agent"
ERA = Path(sys.argv[2]) if len(sys.argv) > 2 else _find_rule_set_repo()


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
    out["metadata"] = {"title": doc.get("description", "")[:200], "authors": ["evorulelab@gmail.com"]}
    return out


def main() -> int:
    reg = load_registry()
    # (路径, kind, 治理 id, schema) —— 裸文档自动合成壳; 已带 $schema+kind 的直接校验
    cases = [
        (EA / "agents/general.json", "agent_def", "com.evoagent.agent.general", "schemas/agent_def/v1.0.json"),
        (EA / "agents/researcher.json", "agent_def", "com.evoagent.agent.researcher", "schemas/agent_def/v1.0.json"),
        (EA / "agents/rule-copilot.json", "agent_def", "com.evoagent.agent.rule_copilot", "schemas/agent_def/v1.0.json"),
        (EA / "rules/workflows/research_and_write.json", "workflow_dag", "com.evoagent.workflow.research_and_write", "schemas/workflow_dag/v1.0.json"),
    ]
    if ERA is not None:
        cases.append((ERA / "core_eval/agent_core_eval.json", "rule_set", "app.evorule.agent", "schemas/rule_set/v1.0.json"))
    else:
        print("[SKIP] 检出根下未发现 rule_set 资产仓（可用第二个命令行参数显式指定）")
    failures = 0
    for path, kid, pid, schema_rel in cases:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if "$schema" in raw and "kind" in raw:
            doc = raw  # C7 固化壳资产: 完整 5 标注字段已在文档内
        else:
            doc = shelved(raw, f"https://evorule.org/schemas/{kid}/v1.0.json", kid, pid)
        schema = json.loads((REPO / schema_rel).read_text(encoding="utf-8-sig"))
        errs = sorted(jsonschema.Draft202012Validator(schema, registry=reg).iter_errors(doc), key=lambda e: list(e.path))
        if errs:
            failures += 1
            print(f"[FAIL] {path}")
            for e in errs[:5]:
                print(f"   - {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:160]}")
        else:
            print(f"[OK]   {path}")
    print()
    print("RESULT:", "ALL PASS" if failures == 0 else f"{failures} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

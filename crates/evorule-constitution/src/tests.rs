// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 EvoRule 元则 Project
// This file is part of EvoRule, licensed under GNU Affero General Public License v3 or later.
//! 共享校验组件测试。全部用程序构造文档,不落盘 fixture——
//! 避免被本仓扫描门禁(scan_repo_json.py)当成无壳资产拦截。

use super::*;
use serde_json::json;

/// 宪法仓 schemas 目录(crate 位于 <repo>/crates/evorule-constitution)
fn repo_schemas() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("schemas")
}

fn valid_agent_body() -> Value {
    json!({
        "agent_type": "researcher", "version": "0.1.0",
        "description": "d", "system_prompt": "s", "model": "m",
        "temperature": 0.3, "max_steps": 20, "step_timeout_secs": 60,
        "tools": ["file_read"]
    })
}

#[test]
fn test_loaded_status_with_repo_dir() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    assert_eq!(c.status("agent_def"), SchemaStatus::Loaded);
    assert_eq!(c.status("workflow_dag"), SchemaStatus::Loaded);
    assert_eq!(c.schemas_dir().as_deref(), Some(repo_schemas().as_path()));
}

#[test]
fn test_validate_rejects_temperature_out_of_range() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    let mut bad = valid_agent_body();
    bad["temperature"] = json!(99.0);
    let errs = c.validate("agent_def", &bad).expect_err("must reject");
    let rendered: Vec<String> = errs.iter().map(|v| v.to_string()).collect();
    assert!(
        rendered
            .iter()
            .any(|s| s.contains("temperature") && s.contains("99")),
        "violation must point at temperature, got: {rendered:?}"
    );
}

#[test]
fn test_validate_accepts_real_shape() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    assert!(c.validate("agent_def", &valid_agent_body()).is_ok());
    let wf = json!({
        "workflow_id": "wf1", "description": "",
        "nodes": [{"id": "a", "agent_type": "researcher", "task": "t"}],
        "output_node": "a"
    });
    assert!(c.validate("workflow_dag", &wf).is_ok());
}

#[test]
fn test_workflow_empty_nodes_rejected() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    let bad = json!({"workflow_id": "w", "nodes": [], "output_node": "x"});
    let errs = c.validate("workflow_dag", &bad).expect_err("empty nodes");
    assert!(!errs.is_empty());
}

#[test]
fn test_fallback_when_dir_missing() {
    let c = Constitution::with_schemas_dir(PathBuf::from("/definitely/not/here"));
    assert_eq!(c.status("agent_def"), SchemaStatus::Fallback);
    // 降级语义:不硬失败——结构门卫兜底由调用方负责
    assert!(c.validate("agent_def", &valid_agent_body()).is_ok());
    assert!(c.schemas_dir().is_none());
}

#[test]
fn test_bad_version_in_body_is_rejected() {
    // body 自带 version 时透传进壳;semver 不合法应被 _meta 拒收
    let c = Constitution::with_schemas_dir(repo_schemas());
    let mut bad = valid_agent_body();
    bad["version"] = json!("not-a-semver");
    assert!(c.validate("agent_def", &bad).is_err());
}

#[test]
fn test_shelve_sanitizes_id_with_hyphen() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    let mut body = valid_agent_body();
    body["agent_type"] = json!("rule-copilot"); // 连字符非法,_meta id pattern 会拒收裸透传
                                                // 合成壳必须消毒后通过
    assert!(c.validate("agent_def", &body).is_ok());
}

#[test]
fn test_missing_required_field_rejected() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    let bad = json!({
        "agent_type": "x", "version": "1.0.0", "description": "",
        "model": "m", "temperature": 0.5, "max_steps": 1,
        "step_timeout_secs": 1, "tools": []
        // system_prompt 缺失
    });
    let errs = c.validate("agent_def", &bad).expect_err("missing field");
    assert!(
        errs.iter().any(|v| v.to_string().contains("system_prompt")),
        "got: {errs:?}"
    );
}

#[test]
fn test_unknown_kind_falls_back_gracefully() {
    let c = Constitution::with_schemas_dir(PathBuf::from("/definitely/not/here"));
    assert_eq!(c.status("some_future_kind"), SchemaStatus::Fallback);
    assert!(c.validate("some_future_kind", &json!({})).is_ok());
}

#[test]
fn test_violation_display_format() {
    let v = Violation {
        path: "nodes/0/id".into(),
        message: "bad".into(),
    };
    assert_eq!(v.to_string(), "nodes/0/id: bad");
    let root = Violation {
        path: String::new(),
        message: "root msg".into(),
    };
    assert_eq!(root.to_string(), "root msg");
}

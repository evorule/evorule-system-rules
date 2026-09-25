// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 EvoRule 元则 Project
// This file is part of EvoRule, licensed under GNU Affero General Public License v3 or later.
//! 共享校验组件测试。全部用程序构造文档,不落盘 fixture——
//! 避免被本仓扫描门禁(scan_repo_json.py)当成无壳资产拦截。

use super::*;
use serde_json::json;

/// 宪法仓 schemas 目录(crate 位于 <repo>/crates/evorule-constitution)——
/// 供显式目录模式用例使用
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

// ===== 内嵌模式(缺省数据源)=====

#[test]
fn test_policy_default_is_strict() {
    assert_eq!(Policy::default(), Policy::Strict);
    assert_eq!(Constitution::new().policy, Policy::Strict);
}

#[test]
fn test_embedded_default_works_without_disk() {
    // 内嵌模式:无需磁盘宪法仓——默认构造即可校验(部署零依赖核心卖点)
    let c = Constitution::new();
    assert_eq!(c.status("agent_def"), SchemaStatus::Loaded);
    assert_eq!(c.status("workflow_dag"), SchemaStatus::Loaded);
    assert_eq!(c.status("rule_set"), SchemaStatus::Loaded);
    assert!(c.validate("agent_def", &valid_agent_body()).is_ok());
    // 内嵌模式无磁盘依赖:schemas_dir 如实为 None
    assert!(c.schemas_dir().is_none());
}

#[test]
fn test_embedded_covers_all_v1_kinds() {
    let c = Constitution::new();
    for kind in [
        "agent_def",
        "workflow_dag",
        "service_registry",
        "rule_set",
        "knowledge",
        "migration",
    ] {
        assert_eq!(
            c.status(kind),
            SchemaStatus::Loaded,
            "kind={kind} 应内嵌可用"
        );
    }
}

#[test]
fn test_workflow_dag_v11_via_version_param() {
    let c = Constitution::new();
    assert_eq!(
        c.status_version("workflow_dag", "v1.1"),
        SchemaStatus::Loaded
    );
    let wf = json!({
        "workflow_id": "w", "description": "",
        "nodes": [
            {"id": "a", "agent_type": "researcher", "task": "t"},
            {"id": "b", "agent_type": "writer", "task": "t", "depends_on": ["a"],
             "run_when": {"node": "a", "op": "contains", "value": "APPROVE"}}
        ],
        "output_node": "b"
    });
    assert!(c.validate_version("workflow_dag", "v1.1", &wf).is_ok());
    // 同一文档按 v1.0 校验:run_when 是 v1.1 增量,v1.0 schema 未定义该键
    // (未封口则放行/封口则拒绝——此处仅断言版本参数确实分派了不同 schema:
    //  v1.0 对 op 枚举无约束,含 starts_with 的文档 v1.1 必拒而 v1.0 不拒)
    let v11_only = json!({
        "workflow_id": "w", "description": "",
        "nodes": [
            {"id": "a", "agent_type": "researcher", "task": "t"},
            {"id": "b", "agent_type": "writer", "task": "t", "depends_on": ["a"],
             "run_when": {"node": "a", "op": "starts_with", "value": "APPROVE"}}
        ],
        "output_node": "b"
    });
    assert!(c
        .validate_version("workflow_dag", "v1.1", &v11_only)
        .is_err());
}

// ===== 显式目录模式 =====

#[test]
fn test_loaded_status_with_repo_dir() {
    let c = Constitution::with_schemas_dir(repo_schemas());
    assert_eq!(c.status("agent_def"), SchemaStatus::Loaded);
    assert_eq!(c.status("workflow_dag"), SchemaStatus::Loaded);
    assert_eq!(c.schemas_dir().as_deref(), Some(repo_schemas().as_path()));
}

#[test]
fn test_dir_mode_meta_ref_resolves_from_disk() {
    // 目录模式:跨文件 $ref(_meta)经检索器从磁盘解析
    let c = Constitution::with_schemas_dir(repo_schemas());
    let mut bad = valid_agent_body();
    bad["temperature"] = json!(99.0);
    let errs = c.validate("agent_def", &bad).expect_err("must reject");
    assert!(!errs.is_empty());
}

// ===== 校验行为(与模式无关)=====

#[test]
fn test_validate_rejects_temperature_out_of_range() {
    let c = Constitution::new();
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
    let c = Constitution::new();
    assert!(c.validate("agent_def", &valid_agent_body()).is_ok());
    let wf = json!({
        "workflow_id": "wf1", "description": "",
        "nodes": [{"id": "a", "agent_type": "researcher", "task": "t"}],
        "output_node": "a"
    });
    assert!(c.validate("workflow_dag", &wf).is_ok());
}

// ===== agent_def v1.1:capability_boundary 增量 =====

#[test]
fn test_agent_def_v11_via_version_param() {
    let c = Constitution::new();
    assert_eq!(c.status_version("agent_def", "v1.1"), SchemaStatus::Loaded);
    // v1.1:带 capability_boundary 的文档合法
    let mut with_boundary = valid_agent_body();
    with_boundary["capability_boundary"] = json!({
        "mode": "read_only",
        "sandbox_root": "D:/evo-agent",
        "tools": ["file_read"]
    });
    assert!(c
        .validate_version("agent_def", "v1.1", &with_boundary)
        .is_ok());
    // 三键任一缺失 → 拒
    let mut missing_root = with_boundary.clone();
    missing_root["capability_boundary"]
        .as_object_mut()
        .unwrap()
        .remove("sandbox_root");
    assert!(c
        .validate_version("agent_def", "v1.1", &missing_root)
        .is_err());
    // mode 取值越界 → 拒
    let mut bad_mode = with_boundary.clone();
    bad_mode["capability_boundary"]["mode"] = json!("read_write_all");
    assert!(c.validate_version("agent_def", "v1.1", &bad_mode).is_err());
    // 同一文档按 v1.0 校验:v1.0 无该键定义(未封口放行),仅断言版本分派有效——
    // v1.0 存量文档零迁移(不写 capability_boundary 即可)
    assert!(c
        .validate_version("agent_def", "v1.0", &with_boundary)
        .is_ok());
}

#[test]
fn test_workflow_empty_nodes_rejected() {
    let c = Constitution::new();
    let bad = json!({"workflow_id": "w", "nodes": [], "output_node": "x"});
    let errs = c.validate("workflow_dag", &bad).expect_err("empty nodes");
    assert!(!errs.is_empty());
}

#[test]
fn test_bad_version_in_body_is_rejected() {
    // body 自带 version 时透传进壳;semver 不合法应被 _meta 拒收
    let c = Constitution::new();
    let mut bad = valid_agent_body();
    bad["version"] = json!("not-a-semver");
    assert!(c.validate("agent_def", &bad).is_err());
}

#[test]
fn test_shelve_sanitizes_id_with_hyphen() {
    let c = Constitution::new();
    let mut body = valid_agent_body();
    body["agent_type"] = json!("rule-copilot"); // 连字符非法,_meta id pattern 会拒收裸透传
                                                // 合成壳必须消毒后通过
    assert!(c.validate("agent_def", &body).is_ok());
}

#[test]
fn test_missing_required_field_rejected() {
    let c = Constitution::new();
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

// ===== 降级策略(裁定一:Strict 缺省 fail-fast / Lenient 显式放行)=====

#[test]
fn test_strict_rejects_when_dir_missing() {
    let c = Constitution::with_schemas_dir(PathBuf::from("/definitely/not/here"));
    assert_eq!(c.status("agent_def"), SchemaStatus::Fallback);
    // 缺省 Strict:门禁语义——schema 不可得即拒绝(fail-fast),违规含修复指引
    let errs = c
        .validate("agent_def", &valid_agent_body())
        .expect_err("strict must reject when schema unavailable");
    assert!(
        errs.iter().any(|v| v.message.contains("with_schemas_dir")),
        "拒绝信息须含修复指引: {errs:?}"
    );
    assert!(c.schemas_dir().is_none());
}

#[test]
fn test_lenient_falls_back_when_dir_missing() {
    let c = Constitution::with_schemas_dir(PathBuf::from("/definitely/not/here"))
        .with_policy(Policy::Lenient);
    assert_eq!(c.status("agent_def"), SchemaStatus::Fallback);
    // 显式 Lenient:告警后放行——结构门卫兜底由调用方负责
    assert!(c.validate("agent_def", &valid_agent_body()).is_ok());
}

#[test]
fn test_unknown_kind_strict_rejects() {
    // 未随本 crate 发布的 kind:Strict 下拒绝(升级 crate 才可校验新 kind,
    // 正是"schema 演进随 crate 版本触达消费方"的义务语义)
    let c = Constitution::new();
    assert_eq!(c.status("some_future_kind"), SchemaStatus::Fallback);
    assert!(c.validate("some_future_kind", &json!({})).is_err());
}

#[test]
fn test_unknown_kind_lenient_falls_back() {
    let c = Constitution::new().with_policy(Policy::Lenient);
    assert_eq!(c.status("some_future_kind"), SchemaStatus::Fallback);
    assert!(c.validate("some_future_kind", &json!({})).is_ok());
}

#[test]
fn test_explicit_dir_does_not_silently_fall_back_to_embedded() {
    // 显式目录无效时拒绝静默回退内嵌:"所测"与"生效"必须一致
    let c = Constitution::with_schemas_dir(PathBuf::from("/definitely/not/here"));
    // 若回退内嵌,status 会是 Loaded;如实 Fallback 才是对的
    assert_eq!(c.status("agent_def"), SchemaStatus::Fallback);
}

// ===== 展示格式 =====

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

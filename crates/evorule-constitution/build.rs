// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 EvoRule 元则 Project
// This file is part of EvoRule, licensed under GNU Affero General Public License v3 or later.
//! 编译期内嵌宪法 schema 健康闸。
//!
//! src/lib.rs 以 include_str! 把 schemas/ 母本编译期嵌入组件;本脚本在构建期
//! 逐份解析并校验 `$id` 与路径自洽——坏 JSON 或 $id 漂移直接编译失败,
//! "宪法损坏"在运行时不可能发生。
//!
//! ⚠️ SCHEMAS 清单须与 src/lib.rs 的 EMBEDDED 表保持同步(演进 SOP:
//! 母本改 → verify-all 绿 → 本 crate 版本随动)。

fn main() {
    const SCHEMAS: &[&str] = &[
        "agent_def/v1.0.json",
        "workflow_dag/v1.0.json",
        "workflow_dag/v1.1.json",
        "workflow_dag/v1.2.json",
        "service_registry/v1.0.json",
        "rule_set/v1.0.json",
        "knowledge/v1.0.json",
        "migration/v1.0.json",
        "_meta/v1.0.json",
        "_shared/v1.0.json",
    ];

    let manifest = std::env::var("CARGO_MANIFEST_DIR")
        .unwrap_or_else(|e| panic!("build.rs 需要 CARGO_MANIFEST_DIR: {e}"));
    for rel in SCHEMAS {
        let path = std::path::Path::new(&manifest)
            .join("..")
            .join("..")
            .join("schemas")
            .join(rel);
        let text = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("内嵌宪法 schema 缺失 {}: {e}", path.display()));
        let doc: serde_json::Value = serde_json::from_str(&text)
            .unwrap_or_else(|e| panic!("内嵌宪法 schema 非法 JSON {}: {e}", path.display()));
        let id = doc
            .get("$id")
            .and_then(|v| v.as_str())
            .unwrap_or_else(|| panic!("内嵌宪法 schema 缺 $id: {}", path.display()));
        let expected = format!("https://evorule.org/schemas/{rel}");
        assert_eq!(
            id, &expected,
            "内嵌宪法 schema $id 与路径不一致: {rel} ($id={id}, expected={expected})"
        );
    }

    // schemas/ 母本变更 → 触发本 crate 重编(内嵌数据随动,同仓 SSOT 机制保证)
    println!("cargo:rerun-if-changed=../../schemas");
}

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
        "agent_def/v1.1.json",
        "workflow_dag/v1.0.json",
        "workflow_dag/v1.1.json",
        "workflow_dag/v1.2.json",
        "workflow_dag/v1.3.json",
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

    // 覆盖率断言（CON-D-03 收口）：schemas/ 实体全集必须被显式归类——
    // 内嵌（SCHEMAS）或显式不内嵌（NOT_EMBEDDED，附理由）。新增 schema 文件
    // 未归类即编译失败，杜绝「加了文件忘了内嵌/忘了归类」的静默漂移。
    const NOT_EMBEDDED: &[&str] = &[
        // v0.9 历史版本：仅迁移/对照引用，不进入组件内嵌
        "_meta/v0.9.json",
        "agent_def/v0.9.json",
        "knowledge/v0.9.json",
        "migration/v0.9.json",
        "rule_set/v0.9.json",
        "service_registry/v0.9.json",
        "workflow_dag/v0.9.json",
        // 元 schema：领域命名域（domain/*）纪律件，消费方=tools/check_domain_meta.py，
        // 非组件运行时契约
        "domain/domain_schema.meta.v1.json",
    ];

    let schemas_dir = std::path::Path::new(&manifest)
        .join("..")
        .join("..")
        .join("schemas");
    let mut uncovered: Vec<String> = Vec::new();
    let mut stack = vec![schemas_dir.clone()];
    while let Some(dir) = stack.pop() {
        let entries = std::fs::read_dir(&dir)
            .unwrap_or_else(|e| panic!("读取 schemas 目录失败 {}: {e}", dir.display()));
        for entry in entries {
            let path = entry
                .unwrap_or_else(|e| panic!("schemas 目录项读取失败: {e}"))
                .path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }
            if path.extension().and_then(|v| v.to_str()) != Some("json") {
                continue;
            }
            let rel = path
                .strip_prefix(&schemas_dir)
                .unwrap_or_else(|e| panic!("schemas 相对路径推导失败: {e}"))
                .display()
                .to_string()
                .replace('\\', "/");
            if !SCHEMAS.contains(&rel.as_str()) && !NOT_EMBEDDED.contains(&rel.as_str()) {
                uncovered.push(rel);
            }
        }
    }
    if !uncovered.is_empty() {
        uncovered.sort();
        panic!(
            "schemas/ 存在未归类文件（既不在内嵌清单 SCHEMAS，也不在显式不内嵌 \
             清单 NOT_EMBEDDED）：{uncovered:?}——新增 schema 须同步本文件归类，\
             内嵌者另同步 src/lib.rs 的 EMBEDDED 表"
        );
    }

    // schemas/ 母本变更 → 触发本 crate 重编(内嵌数据随动,同仓 SSOT 机制保证)
    println!("cargo:rerun-if-changed=../../schemas");
}

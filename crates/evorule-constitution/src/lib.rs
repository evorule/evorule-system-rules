// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 EvoRule 元则 Project
// This file is part of EvoRule, licensed under GNU Affero General Public License v3 or later.
#![forbid(unsafe_code)]

//! # evorule-constitution —— 宪法 jsonschema 校验共享组件
//!
//! 属地执法义务的统一实现(见宪法仓 `docs/explanation/04-governance-scope.md`
//! "属地执法义务"节):凡消费受治系统 JSON 的应用,都应在自身加载路径挂接
//! 宪法校验;判定代码必须是本组件,禁止复制第二份。
//!
//! ## 三条设计约束(与治理原则一一对应)
//!
//! 1. **schema 数据走 SSOT**:从宪法仓 `schemas/` 目录运行时读取;
//!    跨文件 `$ref`(如 `_meta`)在装载时内联展开,不落副本。
//! 2. **降级语义合规**:宪法仓不可得或单份 schema 损坏时,
//!    [`SchemaStatus::Fallback`] 如实暴露 + tracing 告警;调用方以结构级
//!    门卫兜底继续运行。绝不静默空窗,也绝不把环境缺陷升级为硬失败。
//! 3. **纯函数封闭性**:校验输入仅为(被检文档, 政策/schema 文档),
//!    不读时钟、网络、外部状态;结果确定可重放。
//!
//! ## 最小接入示例
//!
//! ```no_run
//! use serde_json::json;
//! use evorule_constitution::Constitution;
//!
//! let c = Constitution::new();
//! let doc = json!({ "nodes": [] });
//! match c.validate("agent_def", &doc) {
//!     Ok(()) => { /* 通过(或该 kind 处于 Fallback 降级) */ }
//!     Err(violations) => eprintln!("constitution violations: {violations:?}"),
//! }
//! ```

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::{OnceLock, RwLock};

use serde_json::Value;

/// 单条校验违规
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Violation {
    /// 实例文档内的 JSON 路径(如 `nodes/0/agent_type`),根为空串
    pub path: String,
    /// 违规描述
    pub message: String,
}

impl std::fmt::Display for Violation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if self.path.is_empty() {
            write!(f, "{}", self.message)
        } else {
            write!(f, "{}: {}", self.path, self.message)
        }
    }
}

/// 某 kind 的 schema 可用性状态
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SchemaStatus {
    /// 已从宪法仓成功编译
    Loaded,
    /// 不可得——调用方应仅依赖自己的结构级门卫并保留告警日志
    Fallback,
}

/// 单个 kind 的装载槽:Ready=可用 schema;Fallback=不可得(原因已告警)
type Slot = Option<std::sync::Arc<jsonschema::JSONSchema>>;

struct Inner {
    schemas_dir: Option<PathBuf>,
    compiled: RwLock<BTreeMap<String, Slot>>,
}

/// 宪法校验器。进程内建议持有单例(`Constitution::global()` / `OnceLock`)。
///
/// 线程安全:`compiled` 为 `RwLock`;首次访问某 kind 时同步加载并缓存。
pub struct Constitution {
    inner: OnceLock<Inner>,
    explicit_dir: Option<PathBuf>,
}

impl Default for Constitution {
    fn default() -> Self {
        Self::new()
    }
}

impl Constitution {
    /// 创建实例(惰性:首次 validate 才触达磁盘)
    pub fn new() -> Self {
        Self { inner: OnceLock::new(), explicit_dir: None }
    }

    /// 以显式目录创建(优先于自动定位;供测试与嵌入式部署使用)
    pub fn with_schemas_dir(dir: PathBuf) -> Self {
        Self { inner: OnceLock::new(), explicit_dir: Some(dir) }
    }

    /// 进程级全局单例
    pub fn global() -> &'static Constitution {
        static GLOBAL: OnceLock<Constitution> = OnceLock::new();
        GLOBAL.get_or_init(Self::new)
    }

    fn locate_schemas_dir(explicit: &Option<PathBuf>) -> Option<PathBuf> {
        // 1) 显式配置优先;若指定了但无效,**拒绝静默回退**到自动定位
        if let Some(dir) = explicit {
            if dir.is_dir() {
                return Some(dir.clone());
            }
            emit_fallback_warn(
                "<explicit-schemas-dir>",
                &format!("explicit schemas dir '{}' not found; refusing to auto-locate", dir.display()),
            );
            return None;
        }
        // 2) 环境变量
        if let Ok(root) = std::env::var("EVORULE_SYSTEM_RULES") {
            let p = PathBuf::from(root).join("schemas");
            if p.is_dir() {
                return Some(p);
            }
        }
        // 3) exe 向上祖先中的兄弟目录约定:<ancestor>/evorule-system-rules/schemas
        let Ok(exe) = std::env::current_exe() else { return None };
        let mut cur: Option<&Path> = exe.parent();
        while let Some(dir) = cur {
            let candidate = dir.join("evorule-system-rules").join("schemas");
            if candidate.is_dir() {
                return Some(candidate);
            }
            cur = dir.parent();
        }
        None
    }

    fn init_inner(&self) -> Inner {
        let dir = Self::locate_schemas_dir(&self.explicit_dir);
        if dir.is_none() {
            emit_fallback_warn("<unknown>", "constitution repo not found (set EVORULE_SYSTEM_RULES or checkout as sibling directory)");
        }
        Inner { schemas_dir: dir, compiled: RwLock::new(BTreeMap::new()) }
    }

    fn get_slot(&self, kind: &str) -> Slot {
        let inner = self.inner.get_or_init(|| self.init_inner());
        // fast path: 读锁命中
        if let Ok(map) = inner.compiled.read() {
            if let Some(slot) = map.get(kind) {
                return slot.clone();
            }
        }
        // slow path: 装载并写缓存(未命中即 miss;重复并发装载幂等且廉价)
        let file = format!("{kind}/v1.0.json");
        let label = kind.to_string();
        let slot =
            load_and_compile(inner.schemas_dir.as_deref(), &file, &label);
        if let Ok(mut map) = inner.compiled.write() {
            map.entry(kind.to_string()).or_insert_with(|| slot.clone());
        }
        inner
            .compiled
            .read()
            .ok()
            .and_then(|m| m.get(kind).cloned())
            .unwrap_or_else(|| slot)
    }

    /// 校验一个 **裸 body** 文档(无壳)。壳由内部按 _meta 要求合成占位层,
    /// 发布形态的壳合规由宪法仓扫描门禁负责,不属于运行时职责。
    ///
    /// 返回 `Ok(())` 包括两种情形:全部通过,或该 kind 处于 Fallback
    /// (此时调用方可先经 [`Self::status`] 区分)。
    pub fn validate(&self, kind: &str, body: &Value) -> Result<(), Vec<Violation>> {
        let Some(schema) = self.get_slot(kind) else {
            emit_fallback_warn(kind, "schema unavailable");
            return Ok(());
        };
        let shelved = shelve(body, kind);
        // 先行收集为 owned 值,避免借用进入返回路径的生命周期
        let outcome = schema.validate(&shelved);
        if outcome.is_ok() {
            return Ok(());
        }
        let iter = match outcome {
            Err(it) => it,
            Ok(()) => return Ok(()),
        };
        let violations: Vec<Violation> = iter
            .take(10)
            .map(|e| Violation {
                path: render_instance_path(&e),
                // jsonschema 0.18 的 Display 即纯 message,不含实例路径前缀
                message: e.to_string(),
            })
            .collect();
        Err(violations)
    }

    /// 报告某 kind 的 schema 可用性(供测试断言"非降级"用例生效前提)
    pub fn status(&self, kind: &str) -> SchemaStatus {
        match self.get_slot(kind) {
            Some(_) => SchemaStatus::Loaded,
            None => SchemaStatus::Fallback,
        }
    }

    /// 自动定位到的宪法 schemas 目录(诊断用)
    pub fn schemas_dir(&self) -> Option<PathBuf> {
        self.inner.get_or_init(|| self.init_inner()).schemas_dir.clone()
    }
}

fn load_and_compile(
    dir: Option<&Path>,
    file: &str,
    label: &str,
) -> Slot {
    let Some(dir) = dir else {
        return None;
    };
    let path = dir.join(file);
    let content = match std::fs::read_to_string(&path) {
        Ok(c) => c,
        Err(e) => {
            emit_fallback_warn(label, &format!("failed to read {}: {}", path.display(), e));
            return None;
        }
    };
    let mut doc: Value = match serde_json::from_str(&content) {
        Ok(v) => v,
        Err(e) => {
            emit_fallback_warn(label, &format!("failed to parse {}: {}", path.display(), e));
            return None;
        }
    };
    if let Err(e) = inline_meta_ref(&mut doc, dir) {
        emit_fallback_warn(label, &format!("inline _meta failed: {}", e));
        return None;
    }
    match jsonschema::JSONSchema::compile(&doc) {
        Ok(s) => Some(std::sync::Arc::new(s)),
        Err(e) => {
            emit_fallback_warn(label, &format!("failed to compile {}: {}", path.display(), e));
            None
        }
    }
}

/// 把 schema 中指向 `../_meta/v1.0.json` 的 `$ref` 内联展开(一层,_meta 自身无外链)。
///
/// jsonschema 0.18 无跨文件 registry 基建;内联保持 JSON Schema allOf 语义等价,
/// SSOT 不受影响(_meta 仍是磁盘单一权威源,展开仅发生在内存)。
fn inline_meta_ref(doc: &mut Value, schemas_dir: &Path) -> Result<(), String> {
    const META_REF: &str = "../_meta/v1.0.json";
    let meta_doc = || -> Result<Value, String> {
        let p = schemas_dir.join("_meta/v1.0.json");
        let text = std::fs::read_to_string(&p).map_err(|e| format!("read {}: {}", p.display(), e))?;
        serde_json::from_str(&text).map_err(|e| format!("parse _meta: {}", e))
    };

    let Some(obj) = doc.as_object_mut() else { return Ok(()) };
    // allOf 分支替换
    if let Some(items) = obj.get_mut("allOf").and_then(|v| v.as_array_mut()) {
        let needs = items.iter().any(|i| i.get("$ref").and_then(|r| r.as_str()) == Some(META_REF));
        if needs {
            let meta = meta_doc()?;
            for item in items.iter_mut() {
                if item.get("$ref").and_then(|r| r.as_str()) == Some(META_REF) {
                    *item = meta.clone();
                }
            }
        }
    }
    Ok(())
}

/// 给裸 body 合成最小标注壳以满足 _meta 五字段存在性要求。
///
/// 版本派生:body 自带合法 semver 则透传,否则占位 `0.0.0`——真实资产的
/// 内容版本属于发布管线职责,运行时只关心 body 结构。
fn shelve(body: &Value, kind: &str) -> Value {
    use serde_json::json;

    let id_raw = ["agent_type", "workflow_id", "dataset_id", "id"]
        .iter()
        .find_map(|k| body.get(*k).and_then(|v| v.as_str()))
        .unwrap_or("placeholder");
    // 消毒到 _meta id 语法([a-z][a-z0-9_]* 段):非法字符一律折叠为下划线
    let sanitized: String = id_raw
        .chars()
        .map(|c| {
            if c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_' || c == '.' {
                c
            } else {
                '_'
            }
        })
        .collect();

    let mut doc = serde_json::Map::new();
    doc.insert(
        "$schema".into(),
        json!(format!("https://evorule.org/schemas/{kind}/v1.0.json")),
    );
    doc.insert("kind".into(), json!(kind));
    doc.insert("id".into(), json!(format!("com.evorule.runtime.{sanitized}")));
    doc.insert(
        "version".into(),
        body.get("version").cloned().unwrap_or_else(|| json!("0.0.0")),
    );
    doc.insert("metadata".into(), json!({}));
    if let Some(obj) = body.as_object() {
        for (k, v) in obj {
            doc.entry(k.clone()).or_insert_with(|| v.clone());
        }
    }
    Value::Object(doc)
}

fn render_instance_path(err: &jsonschema::ValidationError<'_>) -> String {
    err.instance_path
        .iter()
        .map(|chunk| match chunk {
            jsonschema::paths::PathChunk::Property(p) => p.to_string(),
            jsonschema::paths::PathChunk::Index(i) => i.to_string(),
            jsonschema::paths::PathChunk::Keyword(k) => (*k).to_string(),
        })
        .collect::<Vec<_>>()
        .join("/")
}

fn emit_fallback_warn(label: &str, reason: &str) {
    #[cfg(feature = "tracing")]
    tracing::warn!(
        kind = %label,
        reason = %reason,
        "evorule-constitution falling back to struct-level guards only"
    );
    #[cfg(not(feature = "tracing"))]
    {
        let _ = (label, reason);
    }
}

#[cfg(test)]
mod tests;

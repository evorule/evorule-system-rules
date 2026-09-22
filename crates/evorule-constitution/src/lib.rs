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
//!    跨文件 `$ref`(如 `_meta`/`_shared`)按 `$id` 运行时检索解析,不落副本。
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

use jsonschema::{Draft, Retrieve, UriRef, Validator};
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
type Slot = Option<std::sync::Arc<jsonschema::Validator>>;

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
        Self {
            inner: OnceLock::new(),
            explicit_dir: None,
        }
    }

    /// 以显式目录创建(优先于自动定位;供测试与嵌入式部署使用)
    pub fn with_schemas_dir(dir: PathBuf) -> Self {
        Self {
            inner: OnceLock::new(),
            explicit_dir: Some(dir),
        }
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
                &format!(
                    "explicit schemas dir '{}' not found; refusing to auto-locate",
                    dir.display()
                ),
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
        let Ok(exe) = std::env::current_exe() else {
            return None;
        };
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
        Inner {
            schemas_dir: dir,
            compiled: RwLock::new(BTreeMap::new()),
        }
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
        let slot = load_and_compile(inner.schemas_dir.as_deref(), &file, &label);
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
                path: e.instance_path.to_string(),
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
        self.inner
            .get_or_init(|| self.init_inner())
            .schemas_dir
            .clone()
    }
}

/// 把宪法 schema URI（`$id` 前缀）映射回 schemas 磁盘文件的运行时检索器。
///
/// jsonschema 0.21 起支持跨文件 `$ref`：相对引用基于文档 `$id` 解析为绝对
/// URI（如 `../_meta/v1.0.json` → `https://evorule.org/schemas/_meta/v1.0.json`），
/// 本检索器再把 URI 反查回磁盘 SSOT 文件——`_meta`/`_shared` 无需再运行时
/// 内联展开（0.18 时代的 inline_meta_ref hack 退役）。
struct DiskRetriever {
    schemas_dir: PathBuf,
}

impl Retrieve for DiskRetriever {
    fn retrieve(
        &self,
        uri: &UriRef<&str>,
    ) -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
        const ID_PREFIX: &str = "https://evorule.org/schemas/";
        let id = uri.as_str();
        let rel = id
            .strip_prefix(ID_PREFIX)
            .ok_or_else(|| format!("not a constitution schema id: {id}"))?;
        if rel.split(['/', '\\']).any(|seg| seg == "..") {
            return Err(format!("schema id must not traverse paths: {id}").into());
        }
        let path = self.schemas_dir.join(rel);
        let text = std::fs::read_to_string(&path)
            .map_err(|e| format!("read {}: {}", path.display(), e))?;
        Ok(serde_json::from_str(&text).map_err(|e| format!("parse {}: {}", path.display(), e))?)
    }
}

fn load_and_compile(dir: Option<&Path>, file: &str, label: &str) -> Slot {
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
    let doc: Value = match serde_json::from_str(&content) {
        Ok(v) => v,
        Err(e) => {
            emit_fallback_warn(label, &format!("failed to parse {}: {}", path.display(), e));
            return None;
        }
    };
    let retriever = DiskRetriever {
        schemas_dir: dir.to_path_buf(),
    };
    match Validator::options()
        .with_draft(Draft::Draft202012)
        .with_retriever(retriever)
        .build(&doc)
    {
        Ok(s) => Some(std::sync::Arc::new(s)),
        Err(e) => {
            emit_fallback_warn(
                label,
                &format!("failed to compile {}: {}", path.display(), e),
            );
            None
        }
    }
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
    doc.insert(
        "id".into(),
        json!(format!("com.evorule.runtime.{sanitized}")),
    );
    doc.insert(
        "version".into(),
        body.get("version")
            .cloned()
            .unwrap_or_else(|| json!("0.0.0")),
    );
    doc.insert("metadata".into(), json!({}));
    if let Some(obj) = body.as_object() {
        for (k, v) in obj {
            doc.entry(k.clone()).or_insert_with(|| v.clone());
        }
    }
    Value::Object(doc)
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

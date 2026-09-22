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
//! 1. **schema 数据内嵌 SSOT**:schema 文档以 `include_str!` 编译期嵌入本组件
//!    (与宪法仓 `schemas/` 母本同仓,零跨仓同步成本),部署零依赖——消费方挂
//!    本 crate 即得,校验行为是 crate 版本的纯函数,不受部署机磁盘漂移影响。
//!    0.1.0 的"运行时读磁盘"降级为可选的显式目录模式
//!    ([`Constitution::with_schemas_dir`],供测试/嵌入式/预览未发布 schema 使用)。
//! 2. **降级策略双模式**:[`Policy::Strict`](缺省)=schema 不可得即 fail-fast,
//!    门禁不可降级;[`Policy::Lenient`]=告警后放行,供非门禁场景显式选用,
//!    调用方以自己的结构级门卫兜底。缺省安全:忘配置即 fail-closed 侧。
//! 3. **纯函数封闭性**:校验输入仅为(被检文档, 政策/schema 文档),
//!    不读时钟、网络、外部状态;结果确定可重放。
//!
//! ## 最小接入示例
//!
//! ```no_run
//! use serde_json::json;
//! use evorule_constitution::Constitution;
//!
//! let c = Constitution::new(); // 内嵌 schema + 缺省 Strict
//! let doc = json!({ "nodes": [] });
//! match c.validate("agent_def", &doc) {
//!     Ok(()) => { /* 通过 */ }
//!     Err(violations) => eprintln!("constitution violations: {violations:?}"),
//! }
//! ```

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::{OnceLock, RwLock};

use jsonschema::{Draft, Retrieve, UriRef, Validator};
use serde_json::Value;

// ============================================================================
// 内嵌 schema(同仓 SSOT:include_str! 直读宪法仓 schemas/ 母本)
// ============================================================================

const AGENT_DEF_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/agent_def/v1.0.json"
));
const WORKFLOW_DAG_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/workflow_dag/v1.0.json"
));
const WORKFLOW_DAG_V1_1: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/workflow_dag/v1.1.json"
));
const SERVICE_REGISTRY_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/service_registry/v1.0.json"
));
const RULE_SET_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/rule_set/v1.0.json"
));
const KNOWLEDGE_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/knowledge/v1.0.json"
));
const MIGRATION_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/migration/v1.0.json"
));
const META_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/_meta/v1.0.json"
));
const SHARED_V1_0: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../schemas/_shared/v1.0.json"
));

/// 内嵌 schema 清单:`(kind, 版本段, 文档文本)`。
///
/// ⚠️ 清单须与 build.rs 的 SCHEMAS 保持同步(build.rs 编译期健康闸:
/// 坏 JSON / `$id` 与路径漂移直接编译失败)。v0.9 历史版本不内嵌,
/// 需要时走显式目录模式。
const EMBEDDED: &[(&str, &str, &str)] = &[
    ("agent_def", "v1.0", AGENT_DEF_V1_0),
    ("workflow_dag", "v1.0", WORKFLOW_DAG_V1_0),
    ("workflow_dag", "v1.1", WORKFLOW_DAG_V1_1),
    ("service_registry", "v1.0", SERVICE_REGISTRY_V1_0),
    ("rule_set", "v1.0", RULE_SET_V1_0),
    ("knowledge", "v1.0", KNOWLEDGE_V1_0),
    ("migration", "v1.0", MIGRATION_V1_0),
    ("_meta", "v1.0", META_V1_0),
    ("_shared", "v1.0", SHARED_V1_0),
];

/// 宪法 schema `$id` 前缀(检索 URI 与磁盘布局共用此映射:
/// `https://evorule.org/schemas/<kind>/<version>.json`)
const ID_PREFIX: &str = "https://evorule.org/schemas/";

// ============================================================================
// 公共类型
// ============================================================================

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
    /// schema 已成功编译
    Loaded,
    /// 不可得——Strict 下 validate 会拒绝;Lenient 下已告警并放行
    Fallback,
}

/// 降级策略:schema 不可得时的行为(治理裁定:门禁不可降级 vs 不把环境
/// 缺陷升级为硬失败的双规范并存,由调用方按场景显式分派)。
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Policy {
    /// 缺省:fail-fast——`validate` 返回 `Err`(拒绝),门禁语义。
    /// 忘配置时向安全侧收敛(fail-closed)。
    #[default]
    Strict,
    /// 显式选用:告警后放行 `Ok(())`,供非门禁场景(工具/演示/文档生成)
    /// 使用;调用方须以自身结构级门卫兜底,并保留告警日志。
    Lenient,
}

// ============================================================================
// Constitution
// ============================================================================

/// 单个 kind/version 的装载槽:Ready=可用 schema;Fallback=不可得(原因已告警)
type Slot = Option<std::sync::Arc<jsonschema::Validator>>;

/// schema 数据源(显式三态:防止"显式目录无效"被静默回退到内嵌)
enum Source {
    /// 内嵌模式(缺省,数据恒可得)
    Embedded,
    /// 显式目录模式(已验证存在)
    Dir(PathBuf),
    /// 不可得:显式目录指定但无效——拒绝静默回退内嵌("所测"与"生效"须一致)
    Unavailable(String),
}

struct Inner {
    source: Source,
    compiled: RwLock<BTreeMap<String, Slot>>,
}

/// 宪法校验器。进程内建议持有单例([`Constitution::global()`] / `OnceLock`)。
///
/// 线程安全:`compiled` 为 `RwLock`;首次访问某 kind 时同步装载并缓存。
pub struct Constitution {
    inner: OnceLock<Inner>,
    explicit_dir: Option<PathBuf>,
    policy: Policy,
}

impl Default for Constitution {
    fn default() -> Self {
        Self::new()
    }
}

impl Constitution {
    /// 创建实例(内嵌模式:缺省数据源,不触达磁盘)
    pub fn new() -> Self {
        Self {
            inner: OnceLock::new(),
            explicit_dir: None,
            policy: Policy::Strict,
        }
    }

    /// 以显式目录创建(覆盖内嵌数据源;供测试/嵌入式/预览未发布 schema 使用)。
    ///
    /// 指定的目录无效时**拒绝静默回退**到内嵌——显式指定意味着调用方要校验
    /// 的就是这份磁盘数据,静默换数据源会让"所测"与"生效"不一致。
    pub fn with_schemas_dir(dir: PathBuf) -> Self {
        Self {
            inner: OnceLock::new(),
            explicit_dir: Some(dir),
            policy: Policy::Strict,
        }
    }

    /// 设置降级策略(builder 链式;缺省 [`Policy::Strict`])
    pub fn with_policy(mut self, policy: Policy) -> Self {
        self.policy = policy;
        self
    }

    /// 进程级全局单例(内嵌模式 + 缺省 Strict)
    pub fn global() -> &'static Constitution {
        static GLOBAL: OnceLock<Constitution> = OnceLock::new();
        GLOBAL.get_or_init(Self::new)
    }

    fn init_inner(&self) -> Inner {
        // 显式目录无效:拒绝静默回退(内嵌),如实暴露为不可得
        let source = match &self.explicit_dir {
            Some(dir) if dir.is_dir() => Source::Dir(dir.clone()),
            Some(dir) => {
                emit_fallback_warn(
                    "<explicit-schemas-dir>",
                    &format!(
                        "explicit schemas dir '{}' not found; refusing to fall back to embedded data",
                        dir.display()
                    ),
                );
                Source::Unavailable(format!(
                    "explicit schemas dir '{}' not found",
                    dir.display()
                ))
            }
            None => Source::Embedded, // 内嵌模式(缺省):无需磁盘
        };
        Inner {
            source,
            compiled: RwLock::new(BTreeMap::new()),
        }
    }

    fn get_slot(&self, kind: &str, version: &str) -> Slot {
        let inner = self.inner.get_or_init(|| self.init_inner());
        let key = format!("{kind}/{version}");
        // fast path: 读锁命中
        if let Ok(map) = inner.compiled.read() {
            if let Some(slot) = map.get(&key) {
                return slot.clone();
            }
        }
        // slow path: 装载并写缓存(未命中即 miss;重复并发装载幂等且廉价)
        let slot = match &inner.source {
            Source::Embedded => compile_embedded(kind, version),
            Source::Dir(dir) => compile_from_dir(dir, kind, version),
            Source::Unavailable(reason) => {
                emit_fallback_warn(kind, &format!("schema source unavailable: {reason}"));
                None
            }
        };
        if let Ok(mut map) = inner.compiled.write() {
            map.entry(key.clone()).or_insert_with(|| slot.clone());
        }
        inner
            .compiled
            .read()
            .ok()
            .and_then(|m| m.get(&key).cloned())
            .unwrap_or(slot)
    }

    /// 校验一个 **裸 body** 文档(无壳,按该 kind 的 v1.0)。
    /// 壳由内部按 _meta 要求合成占位层,发布形态的壳合规由宪法仓扫描门禁
    /// 负责,不属于运行时职责。
    pub fn validate(&self, kind: &str, body: &Value) -> Result<(), Vec<Violation>> {
        self.validate_version(kind, "v1.0", body)
    }

    /// 校验裸 body,显式指定 schema 版本段(如 `workflow_dag` 的 `v1.1`)。
    ///
    /// 返回 `Ok(())` 包括两种情形:全部通过,或 Lenient 模式下该 kind 处于
    /// 不可得状态(此时调用方可先经 [`Self::status_version`] 区分)。
    /// Strict(缺省)下不可得即 `Err`(拒绝,违规条目含修复指引)。
    pub fn validate_version(
        &self,
        kind: &str,
        version: &str,
        body: &Value,
    ) -> Result<(), Vec<Violation>> {
        let Some(schema) = self.get_slot(kind, version) else {
            return match self.policy {
                Policy::Strict => Err(vec![Violation {
                    path: String::new(),
                    message: format!(
                        "constitution schema ({kind}/{version}) unavailable — refusing to \
                         validate without schema-level checks. Fix: use the default embedded \
                         data (Constitution::new(), always carries v1.x schemas), or point \
                         with_schemas_dir() at a valid evorule-system-rules schemas/ directory."
                    ),
                }]),
                Policy::Lenient => {
                    emit_fallback_warn(
                        kind,
                        &format!("schema {kind}/{version} unavailable; falling back to struct-level guards"),
                    );
                    Ok(())
                }
            };
        };
        let shelved = shelve(body, kind, version);
        let iter = match schema.validate(&shelved) {
            Ok(()) => return Ok(()),
            Err(it) => it,
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

    /// 报告某 kind(v1.0)的 schema 可用性
    pub fn status(&self, kind: &str) -> SchemaStatus {
        self.status_version(kind, "v1.0")
    }

    /// 报告某 kind/version 的 schema 可用性(供测试断言"非降级"用例生效前提)
    pub fn status_version(&self, kind: &str, version: &str) -> SchemaStatus {
        match self.get_slot(kind, version) {
            Some(_) => SchemaStatus::Loaded,
            None => SchemaStatus::Fallback,
        }
    }

    /// 显式目录模式下的 schemas 目录(诊断用);内嵌模式返回 None
    /// (语义:无磁盘依赖)
    pub fn schemas_dir(&self) -> Option<PathBuf> {
        match &self.inner.get_or_init(|| self.init_inner()).source {
            Source::Dir(dir) => Some(dir.clone()),
            _ => None,
        }
    }
}

// ============================================================================
// 装载与编译
// ============================================================================

fn compile_embedded(kind: &str, version: &str) -> Slot {
    let Some((_, _, text)) = EMBEDDED
        .iter()
        .find(|(k, v, _)| *k == kind && *v == version)
    else {
        emit_fallback_warn(kind, &format!("no embedded schema for {kind}/{version}"));
        return None;
    };
    let doc: Value = match serde_json::from_str(text) {
        Ok(v) => v,
        Err(e) => {
            // build.rs 健康闸已保证合法;此分支为纵深防御
            emit_fallback_warn(
                kind,
                &format!("embedded {kind}/{version} not valid JSON: {e}"),
            );
            return None;
        }
    };
    compile_doc(
        doc,
        kind,
        &format!("{kind}/{version} (embedded)"),
        SchemaRetriever { dir: None },
    )
}

fn compile_from_dir(dir: &Path, kind: &str, version: &str) -> Slot {
    let file = format!("{kind}/{version}.json");
    let path = dir.join(&file);
    let content = match std::fs::read_to_string(&path) {
        Ok(c) => c,
        Err(e) => {
            emit_fallback_warn(kind, &format!("failed to read {}: {}", path.display(), e));
            return None;
        }
    };
    let doc: Value = match serde_json::from_str(&content) {
        Ok(v) => v,
        Err(e) => {
            emit_fallback_warn(kind, &format!("failed to parse {}: {}", path.display(), e));
            return None;
        }
    };
    compile_doc(
        doc,
        kind,
        &file,
        SchemaRetriever {
            dir: Some(dir.to_path_buf()),
        },
    )
}

fn compile_doc(doc: Value, kind: &str, label: &str, retriever: SchemaRetriever) -> Slot {
    match Validator::options()
        .with_draft(Draft::Draft202012)
        .with_retriever(retriever)
        .build(&doc)
    {
        Ok(v) => Some(std::sync::Arc::new(v)),
        Err(e) => {
            emit_fallback_warn(kind, &format!("failed to compile {label}: {e}"));
            None
        }
    }
}

/// 跨文件 `$ref` 检索器:宪法 schema 的相对引用(`../_meta/v1.0.json` 等)
/// 基于文档 `$id` 解析为绝对 URI,本检索器把 URI 反查回数据源
/// (内嵌查表 / 磁盘 SSOT 文件)。
struct SchemaRetriever {
    /// Some(dir)=目录模式按文件解析;None=内嵌查表
    dir: Option<PathBuf>,
}

impl Retrieve for SchemaRetriever {
    fn retrieve(
        &self,
        uri: &UriRef<&str>,
    ) -> Result<Value, Box<dyn std::error::Error + Send + Sync>> {
        let id = uri.as_str();
        let rel = id
            .strip_prefix(ID_PREFIX)
            .ok_or_else(|| format!("not a constitution schema id: {id}"))?;
        if rel.split(['/', '\\']).any(|seg| seg == "..") {
            return Err(format!("schema id must not traverse paths: {id}").into());
        }
        match &self.dir {
            None => {
                let (kind, version) = parse_rel(rel)?;
                let (_, _, text) = EMBEDDED
                    .iter()
                    .find(|(k, v, _)| *k == kind && *v == version)
                    .ok_or_else(|| format!("no embedded schema for {rel}"))?;
                Ok(serde_json::from_str(text)?)
            }
            Some(dir) => {
                let path = dir.join(rel);
                let text = std::fs::read_to_string(&path)
                    .map_err(|e| format!("read {}: {}", path.display(), e))?;
                Ok(serde_json::from_str(&text)
                    .map_err(|e| format!("parse {}: {}", path.display(), e))?)
            }
        }
    }
}

/// `agent_def/v1.0.json` → `("agent_def", "v1.0")`
fn parse_rel(rel: &str) -> Result<(&str, &str), String> {
    let (kind, file) = rel
        .split_once('/')
        .ok_or_else(|| format!("bad schema rel: {rel}"))?;
    let version = file
        .strip_suffix(".json")
        .ok_or_else(|| format!("bad schema file: {rel}"))?;
    Ok((kind, version))
}

// ============================================================================
// 壳合成与告警
// ============================================================================

/// 给裸 body 合成最小标注壳以满足 _meta 五字段存在性要求。
///
/// 版本派生:body 自带合法 semver 则透传,否则占位 `0.0.0`——真实资产的
/// 内容版本属于发布管线职责,运行时只关心 body 结构。
fn shelve(body: &Value, kind: &str, version: &str) -> Value {
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
        json!(format!("{ID_PREFIX}{kind}/{version}.json")),
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

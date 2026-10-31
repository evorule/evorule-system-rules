# evorule-system-rules

The system constitution of the evorule ecosystem: the schema, versioning, and upgrade authority for all "system JSON" loaded by evorule platform components.

[![CI][badge-ci]][ci-link]
[![License: AGPL-3.0-or-later][badge-license]][license-link]

**License**: [AGPL-3.0-or-later](LICENSE) with [dual licensing](DUAL_LICENSE.md); schemas are [CC0-1.0](schemas/LICENSE-SCHEMAS.md)

Every system JSON in the ecosystem is governed by this repo — it defines what each file type looks like, how it is versioned, and how old files migrate when a schema is upgraded. evorule-rule is its downstream implementation, and all evorule system files must align with it. Governance is three-tiered: this repo is Tier 1 (the constitution), the evorule / evorule-server / evo-agent / evorule-rule repos are Tier 2 consumers, and project-side business rules managed through evorule-rule are Tier 3 — see [the governance model](docs/explanation/01-three-tier-governance.md).

## Schema Overview

Six `kind` values cover everything the platform loads:

| kind | Purpose | Examples |
|---|---|---|
| `rule_set` | business rule sets / TCB rule sets | `core_eval.json`, `yuanze_rules.json` |
| `agent_def` | agent definitions | `evo-agent/agents/*.json` |
| `workflow_dag` | DAG workflows | `evo-agent/rules/workflows/*.json` |
| `service_registry` | service registry / HTTP routes | `service_registry.json` |
| `knowledge` | knowledge bases | `examples/knowledge.example.json` (draft status; the server's `docs/PITFALLS.json` is an exempt reference artifact, not an instance of this kind) |
| `migration` | `$schema` upgrade rules | produced in this repo |

Every system JSON carries five fixed top-level fields plus a kind-specific body:

```json
{
  "$schema": "https://evorule.org/schemas/<kind>/<version>.json",
  "kind": "<kind>",
  "id": "<org>.<scope>.<name>",
  "version": "<semver>",
  "metadata": { "title": "...", "created": "...", "updated": "..." },
  "<body>": "..."
}
```

The schema set is small and explicit:

```
schemas/
  _shared/v1.0.json           shared $defs (transform_rule etc., SSOT)
  _meta/v1.0.json             the five fixed top-level fields (a v0.9 historical version also exists)
  rule_set/v1.0.json
  agent_def/v1.0.json         (draft, pending field verification)
  workflow_dag/v1.0.json
  workflow_dag/v1.1.json      (run_when conditional branches; coexists with v1.0)
  service_registry/v1.0.json  (optional .meta.json sidecar mode)
  knowledge/v1.0.json         (draft, pending field verification)
  migration/v1.0.json
migrations/                   $schema upgrade rules (v0.0-to-v0.9, v0.9-to-v1.0)
```

## Compatibility

| Schema version | Status |
|---|---|
| v1.0 | current frozen baseline |
| v0.9 | coexists for legacy assets |
| v0.9-to-v1.0 | migration line, see [`migrations/`](migrations) |

The `agent_def` and `knowledge` schemas are drafts pending field verification; all other v1.0 schemas are frozen. Version history lives in [CHANGELOG.md](CHANGELOG.md).

## Validation

One-shot full precheck (recommended entry point):

```bash
powershell -File verify-all.ps1
```

Runs twelve checks in sequence — environment precheck, schema closure acceptance, file-header self-check, golden-sample coverage with bidirectional assertions, version discipline, docs link check, interception evidence matrix, server embedded-copy consistency, conformance round-trip, repo-wide data-format gates, evo-agent asset validation, and rule-repo `data/` guard (the last six skip gracefully when a sibling repo is absent); any failure exits non-zero.

Validate a single system JSON:

```bash
python tools/evorule-migrate validate path/to/your.json
```

> A `service_registry` document may omit `$schema` when a same-named `.meta.json` sidecar exists — the pair is merged for validation.

Upgrade a v0.9 JSON to v1.0:

```bash
python tools/evorule-migrate upgrade path/to/old.json \
  --from-schema v0.9 --to-schema v1.0 \
  -o path/to/new.json
```

The `rule_set` `rules[] → transform[]` step is a semantic translation: the upgrade output carries a `<derived-by-rule_translate>` placeholder and asks for human confirmation.

## Change Process

Schema changes follow a three-step SOP ([schema-evolution-sop.md](docs/operations/schema-evolution-sop.md)): change the master here only — never altering machine semantics the engine already consumes — run `verify-all.ps1` green, then sync the server's embedded copy in the same batch (dual-repo commits). Tightening changes require a zero-hit assessment across all consumer repos before landing.

## Documentation

Public documentation lives in [`docs/`](docs) with a Diátaxis layout (tutorial / how-to / reference / explanation, plus ADRs and operations guides). Start at [docs/introduction.md](docs/introduction.md), or run `mdbook serve docs` for a local book.

## Contributing

evorule team and invited contributors; PRs go through standard review.

## License

Layered licensing model:

| Assets | License |
|---|---|
| `schemas/` (all JSON Schemas) | **CC0-1.0 public domain** — see [schemas/LICENSE-SCHEMAS.md](schemas/LICENSE-SCHEMAS.md) |
| Everything else (`tools/` / `docs/` / `examples/` / ADRs) | **AGPL-3.0-or-later + commercial dual licensing** |

- Open source: [LICENSE](LICENSE)
- Dual licensing FAQ: [DUAL_LICENSE.md](DUAL_LICENSE.md) · [FREE_COMMERCIAL_LICENSE.md](FREE_COMMERCIAL_LICENSE.md) (free waiver for eligible entities) · [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- Third-party notices: [NOTICE.md](NOTICE.md) · trademark policy: [TRADEMARK.md](TRADEMARK.md) · repo-specific notes: [LEGAL_NOTES.md](LEGAL_NOTES.md)
- Commercial / FCL inquiries: <evorulelab@gmail.com>

The layering mirrors the main repo: normative-layer assets are CC0-1.0 (this repo's `schemas/`, like the engine constitution `core_eval.json`), implementation-layer assets are AGPL-3.0-or-later plus commercial — governance authority comes from the governance model and process, not from license terms.

Content you author against these schemas is yours: the schemas are formats (CC0-1.0), your system JSON is your work, licensed as you choose via the `metadata.license` field with no contamination in either direction — see [docs/adr/scope-split-ip-model.md](docs/adr/scope-split-ip-model.md).

[badge-ci]: https://github.com/evorule/evorule-system-rules/actions/workflows/ci.yml/badge.svg
[ci-link]: https://github.com/evorule/evorule-system-rules/actions/workflows/ci.yml
[badge-license]: https://img.shields.io/badge/license-AGPL--3.0--or--later-blue?style=flat-square
[license-link]: LICENSE

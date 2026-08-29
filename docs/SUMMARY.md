# Summary

[介绍](introduction.md)

# 用户指南

- [教程](tutorial/README.md)
  - [01 快速开始:校验你的第一个 system JSON](tutorial/01-quickstart-validate.md)
  - [02 写你的第一个 system JSON:rule_set 示例](tutorial/02-write-first-system-json.md)
  - [03 把 v0 JSON 升级到 v0.9](tutorial/03-upgrade-v0-to-v0.9.md)
- [任务式指南](how-to/README.md)
  - [如何校验 system JSON](how-to/validate-system-json.md)
  - [如何升级已有 JSON 到新 schema](how-to/upgrade-existing-json.md)
  - [如何接入 evorule-rule 对齐](how-to/integrate-with-evorule-rule.md)
- [参考手册](reference/README.md)
  - [6 个 kind 的 schema 字段](reference/schema-reference.md)
  - [evorule-migrate CLI](reference/cli-reference.md)
  - [双版本协议](reference/version-protocol.md)
  - [规则设计与非法限制手册](reference/illegal-restrictions-manual.md)
- [原理与设计](explanation/README.md)
  - [立场总纲:evorule 解释 evorule](explanation/00-evorule-explains-evorule.md)
  - [立场篇:3 层治理模型](explanation/01-three-tier-governance.md)
  - [立场篇:自举的边界](explanation/02-bootstrap-boundary.md)
  - [立场篇:与 evorule-rule 的关系](explanation/03-evorule-rule-alignment.md)
  - [管辖边界:什么受治、什么豁免](explanation/04-governance-scope.md)

# 项目

- [设计规范(adr/)](adr/README.md)
  - [设计规范模板](adr/template.md)
  - [五顶层字段规范](adr/five-top-level-fields.md)
  - [顶层 body 字段语义化](adr/semantic-body-fields.md)
  - [双版本协议](adr/double-version-protocol.md)
  - [evorule-rule 必须对齐](adr/evorule-rule-must-align.md)
  - [自举终止条件](adr/bootstrap-termination.md)
- [运维与发布](operations/README.md)
  - [发版流程](operations/release-process.md)
  - [CI 与校验流水线](operations/ci-pipeline.md)

---

[文档约定与边界](explanation/doc-boundaries.md)

# Pull Request

## 变更说明
<!-- 简述本次 PR 改了什么、为什么。 -->

## 变更级别（必选其一，[CON-G-001]）
- [ ] 语义级：$defs 结构 / 指令集 / 域变化（semver minor+）→ 必须完成下方「语义级五件齐」
- [ ] 描述级：description / 文档文案（版本号不动）→ 轻流程（PR + 一人评审 + CI）

## 语义级五件齐（语义级 PR 必填，[CON-G-002]）
- [ ] ① 动机与影响面：说明动机，并列出受影响的 kind / $defs
- [ ] ② TCB 联动声明：evorule-tcb / evorule-discipline 同批语义变更的 PR/commit 链接（[CON-R-003]）
- [ ] ③ 金样例同步：受影响 $def 的 acceptance/golden/ 合法+非法对已更新（[CON-R-004]/[CON-K3-001]）
- [ ] ④ conformance 全绿：verify-all.ps1 全 PASS（含跨仓装载环测试 [CON-R-005]）
- [ ] ⑤ breaking 变更附迁移器：migrations/ 已补对应迁移档（[CON-K5-001]）

## 检查清单
- [ ] 已通过 `cargo test --workspace --all-targets` 与 `cargo clippy --workspace --all-targets -- -D warnings`
- [ ] 门-钥配对：新增门（校验/拦截面）必有配套钥匙（样例/脚手架/导览）随之合入，无裸门（[CON-X-002]）
- [ ] 已更新相关文档（README / CHANGELOG / docs）
- [ ] 已阅读并同意 [Individual CLA](CLA-individual.md) —— 签署方式：在 PR 评论
      `I have read the CLA Document and I hereby sign the CLA`

## 备注
<!-- 任何需要 reviewer 注意的点 -->

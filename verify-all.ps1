# verify-all.ps1 —— system-rules 一键预检（宪法自身健康闭环）
#
# 任一步失败即以非零码退出。server 副本同步检查仅在 server 仓存在时执行。
# 用法: powershell -File verify-all.ps1        （建议在本仓根目录执行）
#       或任意 cwd 执行亦可——各脚本已锚定仓根，不受当前目录影响。
#
# 2026-08-27 建立：落地 规划定稿 M4-A3。
#   过渡态守卫闭环；待 G1"门禁即规则"设计定稿后，政策性检查项将迁移为热加载规则集。

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

$results = [System.Collections.Generic.List[object]]::new()
$failed = $false

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host ""
    Write-Host ("=" * 72)
    Write-Host "[STEP] $Name"
    Write-Host ("=" * 72)
    try {
        & $Action
        if ($LASTEXITCODE -ne 0) { throw "退出码 $LASTEXITCODE" }
        $script:results.Add([PSCustomObject]@{ Step = $Name; Result = 'PASS' })
    } catch {
        $script:results.Add([PSCustomObject]@{ Step = $Name; Result = "FAIL ($($_.Exception.Message))" })
        $script:failed = $true
    }
}

Invoke-Step 'python 环境预检 (jsonschema/referencing 可导入性)' {
    # 防「存在但不可运行」的隐蔽失效：PATH 解析到的 python 若缺 jsonschema/referencing 模块，
    # 后续步骤会以裸 ModuleNotFoundError 中断且不指明解释器来源——预检显式暴露两者。
    $probe = & python -c "import sys, jsonschema, referencing; print(sys.executable)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $pyver = (& python --version 2>&1) -join ''
        throw "当前 python（$pyver）缺少 jsonschema/referencing 模块——执行 'python -m pip install jsonschema referencing' 后重跑；若为托管环境解释器，请先确认 PATH 指向预期 python"
    }
    Write-Host "[OK] python 解释器: $probe"
}
if ($failed) {
    # 预检失败即终止：环境缺依赖时后续步骤注定连环 FAIL，无运行价值
    $results | Format-Table -AutoSize
    Pop-Location
    Write-Host "VERIFY-ALL: FAIL（python 环境预检未通过，先修复环境再重跑）" -ForegroundColor Red
    exit 1
}
Invoke-Step 'schema 闭环验收 (tools/verify_schemas.py)' {
    python (Join-Path $root 'tools\verify_schemas.py')
}
Invoke-Step '宪法文件头自检 (tools/check_schema_headers.py, CON-R-008/L0-001)' {
    python (Join-Path $root 'tools\check_schema_headers.py')
}
Invoke-Step '金样例覆盖率+双向断言 (tools/check_golden_coverage.py, CON-R-004/K3-001)' {
    python (Join-Path $root 'tools\check_golden_coverage.py')
}
Invoke-Step '版本号纪律 (tools/check_version_discipline.py, CON-G-003)' {
    # 禁无声版本：存量版本文件仅许 description 级变更，结构面变化必须落新版本文件
    python (Join-Path $root 'tools\check_version_discipline.py')
}
Invoke-Step 'docs 链接检查 (tools/check_docs_links.py)' {
    python (Join-Path $root 'tools\check_docs_links.py')
}
$empirical = Join-Path $root '_empirical_interception.py'
if (Test-Path $empirical) {
    Invoke-Step 'Opt1-4 拦截实证 (_empirical_interception.py)' {
        python $empirical
    }
} else {
    Write-Host "`n[SKIP] 拦截实证脚本不在仓内(内部工具,存于 knowledge vault),跳过"
}
$siblingRoot = Split-Path -Parent $root   # 兄弟仓检出根（与各仓检出布局一致）
$serverSync = Join-Path $siblingRoot 'evorule-server\scripts\check_schema_sync.py'
if (Test-Path $serverSync) {
    Invoke-Step 'server 内嵌副本一致性 (check_schema_sync.py, check-only)' {
        python $serverSync
    }
} else {
    Write-Host "`n[SKIP] server 仓不存在($serverSync)，跳过副本同步检查"
}
$serverRoot = Join-Path $siblingRoot 'evorule-server'
$loaderManifest = Join-Path $serverRoot 'core\rule_loader\Cargo.toml'
if (Test-Path $loaderManifest) {
    Invoke-Step 'conformance 环测试 (cargo test -p evorule-rule-loader, CON-R-005)' {
        # 真装载路径环测试：金样例装载档合法集全过/非法集全拒（跨仓闭环件，server 仓在时执行）
        Push-Location $serverRoot
        try {
            cargo test -p evorule-rule-loader --test conformance
            if ($LASTEXITCODE -ne 0) { throw "cargo test 退出码 $LASTEXITCODE" }
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "`n[SKIP] server 仓不存在($loaderManifest)，跳过 conformance 环测试 (CON-R-005)"
}
$rootRepo = Join-Path $siblingRoot 'evorule'
if (Test-Path $rootRepo) {
    Invoke-Step '根仓数据格式门禁 (scan_repo_json.py → evorule)' {
        python (Join-Path $root 'tools\scan_repo_json.py') --repo $rootRepo
    }
} else {
    Write-Host "`n[SKIP] 根仓不存在($rootRepo)，跳过根仓门禁扫描"
}
$evoAgent = Join-Path $siblingRoot 'evo-agent'
if (Test-Path $evoAgent) {
    Invoke-Step 'evo-agent 资产 schema 校验 (tools/check_evoagent_assets.py)' {
        python (Join-Path $root 'tools\check_evoagent_assets.py') $evoAgent
    }
} else {
    Write-Host "`n[SKIP] evo-agent 仓不存在($evoAgent)，跳过资产校验"
}
$ruleRepo = Join-Path $siblingRoot 'evorule-rule'
$ruleGuard = Join-Path $ruleRepo 'tools\check_data_assets.py'
if (Test-Path $ruleGuard) {
    # RG-1 件A3：宪法十二步之后补 rule 仓步——data/ 90 件资产守护（少件红灯/多件警告/live 只读试连），
    # 跨仓守护闭环，rule 仓从「宪法纸面管辖」推进到「机器守护落地」（见 evorule-rule docs/asset-inventory.md）
    Invoke-Step 'rule 仓 data/ 资产守护 (check_data_assets.py, RG-1 件A3)' {
        python $ruleGuard
    }
} else {
    Write-Host "`n[SKIP] rule 仓不存在($ruleRepo)，跳过 data/ 资产守护 (RG-1)"
}
$domainMeta = Join-Path $root 'tools\check_domain_meta.py'
if (Test-Path $ruleRepo) {
    # SR-17 件3（B3）：verify-all 第十四步——扩展层领域 schema 元纪律（[CON-D-001]/[CON-D-003]）：
    # rule 仓 data/domain_schemas 7 件过元 schema（必备件+domain 命名域）+301 映射表承接；
    # 双权威消失的机器判据之一（另一=check_schema_sync 扩展层段，SR-17 件4/B4）
    Invoke-Step '扩展层领域 schema 元纪律 (check_domain_meta.py, SR-17 件3)' {
        python $domainMeta
    }
} else {
    Write-Host "`n[SKIP] rule 仓不存在($ruleRepo)，跳过扩展层元纪律 (SR-17 件3)"
}

Write-Host ""
Write-Host ("=" * 72)
$results | Format-Table -AutoSize
Pop-Location

if ($failed) {
    Write-Host "VERIFY-ALL: FAIL（存在失败步骤，逐项排查后重跑）" -ForegroundColor Red
    exit 1
} else {
    Write-Host "VERIFY-ALL: ALL PASS" -ForegroundColor Green
    exit 0
}

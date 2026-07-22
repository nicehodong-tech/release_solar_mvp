[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")

function Assert-Path {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    $path = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required release path is missing: $RelativePath"
    }
}

Write-Host "1/6 Release files"
@(
    "Dockerfile",
    ".dockerignore",
    ".gcloudignore",
    "saju_web\app.py",
    "saju_web\static\index.html",
    "saju_web\static\app-v2.js",
    "saju_analysis_engine\data\명리 핵심어 파일 2",
    "saju_birth_engine",
    "tests\test_release_contract.py",
    "scripts\operational_check.py",
    "scripts\cloudrun_parity_check.py"
) | ForEach-Object { Assert-Path $_ }

Write-Host "2/6 Source state"
$git = Get-GitExecutable
$branch = (& $git -C $repoRoot branch --show-current).Trim()
$revision = (& $git -C $repoRoot rev-parse --short HEAD).Trim()
$dirty = @(& $git -C $repoRoot status --porcelain)
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect the Git release source."
}
if ($dirty.Count -gt 0 -and -not $AllowDirty) {
    Write-Host ($dirty -join [Environment]::NewLine)
    throw "The release source has uncommitted changes. Commit them or rerun with -AllowDirty for staging only."
}
Write-Host "Git: $branch@$revision; dirty files: $($dirty.Count)"

Write-Host "3/6 Local compile and release tests"
$python = Get-PythonExecutable
Push-Location $repoRoot
try {
    & $python -m compileall -q saju_analysis_engine saju_birth_engine saju_web scripts
    if ($LASTEXITCODE -ne 0) {
        throw "Python compilation failed."
    }
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw "Release regression tests failed."
    }
} finally {
    Pop-Location
}

Write-Host "4/6 Google Cloud account and billing"
Assert-GCloudSession -ProjectId $ProjectId
$billingEnabled = (& $script:GCloud billing projects describe $ProjectId `
    --format="value(billingEnabled)").Trim()
if ($LASTEXITCODE -ne 0 -or $billingEnabled -ne "True") {
    throw "Billing is not enabled for project '$ProjectId'."
}

Write-Host "5/6 Required APIs"
$requiredApis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "certificatemanager.googleapis.com"
)
$enabledApis = @(& $script:GCloud services list `
    --project $ProjectId `
    --enabled `
    --format="value(config.name)")
$missingApis = @($requiredApis | Where-Object { $_ -notin $enabledApis })
if ($missingApis.Count -gt 0) {
    throw "Required APIs are not enabled: $($missingApis -join ', '). Run bootstrap.ps1."
}

Write-Host "6/6 Current DNS rollback baseline"
$apex = Resolve-DnsName aisajuleehyeon.com -Type CNAME -Server 8.8.8.8 -ErrorAction Stop |
    Select-Object -First 1
$www = Resolve-DnsName www.aisajuleehyeon.com -Type CNAME -Server 8.8.8.8 -ErrorAction Stop |
    Select-Object -First 1
$expectedRollback = "mqquvbd6c9bd03f8.sel3.cloudtype.app"
if ($apex.NameHost.TrimEnd(".") -ne $expectedRollback -or $www.NameHost.TrimEnd(".") -ne $expectedRollback) {
    throw "The current DNS baseline no longer points both hosts to Cloudtype."
}
Write-Host "@ CNAME $($apex.NameHost) TTL=$($apex.TTL)"
Write-Host "www CNAME $($www.NameHost) TTL=$($www.TTL)"

Write-Host "PREFLIGHT PASSED: source, engine tests, Google project, APIs, billing, and rollback DNS are ready."
Write-Host "Region: $Region"

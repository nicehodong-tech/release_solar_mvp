[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$ProductionService = "aisaju-leehyeon-production",
    [string]$Domain = "aisajuleehyeon.com",
    [string]$WwwDomain = "www.aisajuleehyeon.com",
    [string]$AddressName = "aisaju-web-ip",
    [string]$CertificateName = "aisaju-web-cert",
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
$keywordDataDirectory = -join @(
    [char]0xBA85, [char]0xB9AC, [char]0x20,
    [char]0xD575, [char]0xC2EC, [char]0xC5B4, [char]0x20,
    [char]0xD30C, [char]0xC77C, [char]0x20, [char]0x32
)
@(
    "Dockerfile",
    ".dockerignore",
    ".gcloudignore",
    "saju_web\app.py",
    "saju_web\static\index.html",
    "saju_web\static\app-v2.js",
    ("saju_analysis_engine\data\{0}" -f $keywordDataDirectory),
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
$billingEnabled = Get-GCloudValue billing projects describe $ProjectId `
    --format="value(billingEnabled)"
if ($billingEnabled -ne "True") {
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

Write-Host "6/6 Cloud Run public edge"
$expectedIp = Get-GCloudValue compute addresses describe $AddressName `
    --project $ProjectId `
    --global `
    --format="value(address)"
if (-not $expectedIp) {
    throw "The Cloud Run load balancer address '$AddressName' is unavailable."
}

$apexIps = @(Resolve-DnsName $Domain -Type A -Server 8.8.8.8 -ErrorAction Stop |
    Where-Object { $_.IPAddress } |
    ForEach-Object { [string]$_.IPAddress })
$wwwIps = @(Resolve-DnsName $WwwDomain -Type A -Server 8.8.8.8 -ErrorAction Stop |
    Where-Object { $_.IPAddress } |
    ForEach-Object { [string]$_.IPAddress })
if ($expectedIp -notin $apexIps -or $expectedIp -notin $wwwIps) {
    throw "Both public hosts must resolve to the Cloud Run load balancer IP $expectedIp."
}

$certificateState = Get-GCloudValue certificate-manager certificates describe $CertificateName `
    --project $ProjectId `
    --format="value(managed.state)"
if ($certificateState -ne "ACTIVE") {
    throw "Certificate '$CertificateName' is not ACTIVE. Current state: $certificateState"
}

$health = Invoke-RestMethod -Uri "https://$Domain/health" -TimeoutSec 30
if (-not $health.ok -or $health.status -ne "healthy") {
    throw "The public Cloud Run health endpoint is not healthy."
}
if ($health.runtime.service -ne $ProductionService) {
    throw "The public domain is not served by '$ProductionService'. Current: $($health.runtime.service)"
}
Write-Host "$Domain, $WwwDomain -> $expectedIp"
Write-Host "Certificate: $certificateState; revision: $($health.runtime.revision)"

Write-Host "PREFLIGHT PASSED: source, engine tests, Google project, APIs, billing, DNS, TLS, and production health are ready."
Write-Host "Region: $Region"

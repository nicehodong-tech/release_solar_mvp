[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Service = "aisaju-leehyeon-production",
    [string]$Domain = "aisajuleehyeon.com",
    [string]$Prefix = "aisaju-web",
    [string]$LegacyUrl = "https://port-0-release-solar-mvp-mqquvbd6c9bd03f8.sel3.cloudtype.app"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

$ipAddress = (& $script:GCloud compute addresses describe "$Prefix-ip" `
    --project $ProjectId `
    --global `
    --format="value(address)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $ipAddress) {
    throw "Could not read the load balancer IP address."
}

$productionUrl = (& $script:GCloud run services describe $Service `
    --project $ProjectId `
    --region $Region `
    --format="value(status.url)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $productionUrl) {
    throw "Could not read the Cloud Run production URL."
}

$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    throw "curl.exe is required for pre-DNS TLS verification."
}

Write-Host "1/3 Load balancer TLS and health with forced DNS"
$healthText = & $curl.Source --silent --show-error --fail --compressed `
    --resolve "${Domain}:443:${ipAddress}" `
    "https://${Domain}/healthz"
if ($LASTEXITCODE -ne 0) {
    throw "The load balancer health request failed."
}
$health = $healthText | ConvertFrom-Json
if (-not $health.ok -or $health.status -ne "healthy") {
    throw "The load balancer returned an unhealthy service."
}

$indexText = (& $curl.Source --silent --show-error --fail --compressed `
    --resolve "${Domain}:443:${ipAddress}" `
    "https://${Domain}/") -join "`n"
$localIndex = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot "saju_web\static\index.html")
$releaseMarker = [regex]::Match($localIndex, "production-release-v[0-9]+").Value
if (-not $releaseMarker) {
    throw "The local product shell has no release marker."
}
if ($LASTEXITCODE -ne 0 -or $indexText -notmatch [regex]::Escape($releaseMarker)) {
    throw "The load balancer did not return the current product shell."
}

Push-Location $repoRoot
try {
    Write-Host "2/3 Cloud Run production operational contract"
    & $python scripts\operational_check.py $productionUrl --concurrency 2 --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Cloud Run production operational verification failed."
    }

    Write-Host "3/3 Legacy and Cloud Run full engine parity"
    & $python scripts\cloudrun_parity_check.py `
        $LegacyUrl `
        $productionUrl `
        --sample-count 4 `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Legacy and Cloud Run engine parity failed."
    }
} finally {
    Pop-Location
}

Write-Host "EDGE VERIFICATION PASSED. DNS is still unchanged."
Write-Host "At cutover, replace both Cloudtype CNAME records with:"
Write-Host "@    A    $ipAddress    TTL 300"
Write-Host "www  A    $ipAddress    TTL 300"
Write-Host "Rollback baseline: @ and www CNAME mqquvbd6c9bd03f8.sel3.cloudtype.app. TTL 600"

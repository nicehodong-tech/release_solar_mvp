[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Service = "aisaju-leehyeon-staging",
    [string]$ProductionUrl = "https://aisajuleehyeon.com",
    [int]$SampleCount = 4
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

$stagingUrl = Get-GCloudValue run services describe $Service `
    --project $ProjectId `
    --region $Region `
    --format "value(status.url)"
if (-not $stagingUrl) {
    throw "Could not read the Cloud Run staging URL."
}

Push-Location $repoRoot
try {
    Write-Host "1/2 Operational contract: $stagingUrl"
    & $python scripts\operational_check.py $stagingUrl --concurrency 2 --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Cloud Run operational check failed."
    }

    Write-Host "2/2 Engine result parity: $ProductionUrl <-> $stagingUrl"
    & $python scripts\cloudrun_parity_check.py `
        $ProductionUrl `
        $stagingUrl `
        --sample-count $SampleCount `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Cloudtype and Cloud Run result parity failed."
    }
} finally {
    Pop-Location
}

Write-Host "Staging verification passed. No DNS or public traffic was changed."

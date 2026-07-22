[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$StagingService = "aisaju-leehyeon-staging",
    [string]$ProductionService = "aisaju-leehyeon-production",
    [string]$LegacyUrl = "https://port-0-release-solar-mvp-mqquvbd6c9bd03f8.sel3.cloudtype.app"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

Write-Host "Re-verifying the staging service before promotion."
& (Join-Path $PSScriptRoot "verify-staging.ps1") `
    -ProjectId $ProjectId `
    -Region $Region `
    -Service $StagingService `
    -ProductionUrl $LegacyUrl
if ($LASTEXITCODE -ne 0) {
    throw "Staging verification did not pass."
}

$image = Get-GCloudValue run services describe $StagingService `
    --project $ProjectId `
    --region $Region `
    --format="value(spec.template.spec.containers[0].image)"
if (-not $image) {
    throw "Could not read the verified staging image."
}

$revision = ($image -split "[:@]")[-1]
$environment = @(
    "PYTHONHASHSEED=0",
    "SAJU_ANALYSIS_WORKERS=2",
    "SAJU_JOB_MAX_PENDING=12",
    "SAJU_JOB_STALE_SECONDS=600",
    "SAJU_JOB_ESTIMATED_SECONDS=15",
    "SAJU_JOB_HARD_TIMEOUT_SECONDS=120",
    "SAJU_LOG_LEVEL=INFO",
    "SAJU_RELEASE_REVISION=$revision"
) -join ","

Write-Host "Promoting the exact verified image: $image"
Invoke-GCloud run deploy $ProductionService `
    --image $image `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --execution-environment gen2 `
    --allow-unauthenticated `
    --ingress all `
    --port 8080 `
    --cpu 2 `
    --memory 2Gi `
    --concurrency 20 `
    --min-instances 1 `
    --max-instances 1 `
    --timeout 300 `
    --no-cpu-throttling `
    --cpu-boost `
    --set-env-vars $environment `
    --labels "app=aisaju-leehyeon,environment=production"

$productionUrl = Get-GCloudValue run services describe $ProductionService `
    --project $ProjectId `
    --region $Region `
    --format="value(status.url)"
if (-not $productionUrl) {
    throw "The production service was deployed, but its URL could not be read."
}

Push-Location $repoRoot
try {
    Write-Host "Operational verification: $productionUrl"
    & $python scripts\operational_check.py $productionUrl --concurrency 2 --timeout 300 --health-path /health
    if ($LASTEXITCODE -ne 0) {
        throw "Production operational verification failed."
    }

    Write-Host "Full engine parity: $LegacyUrl <-> $productionUrl"
    & $python scripts\cloudrun_parity_check.py `
        $LegacyUrl `
        $productionUrl `
        --sample-count 4 `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Production engine parity failed."
    }
} finally {
    Pop-Location
}

Write-Host "Production promotion passed. Public DNS was not changed."
Write-Host "Cloud Run URL: $productionUrl"
Write-Host "Next: .\deploy\cloudrun\prepare-edge.ps1 -ProjectId $ProjectId"

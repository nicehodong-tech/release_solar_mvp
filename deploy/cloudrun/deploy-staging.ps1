[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Repository = "aisaju",
    [string]$Service = "aisaju-leehyeon-staging",
    [string]$ImageTag = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId

if (-not $ImageTag) {
    $ImageTag = Get-Date -Format "yyyyMMdd-HHmmss"
}

$image = "$Region-docker.pkg.dev/$ProjectId/$Repository/saju-web:$ImageTag"
$environment = @(
    "PYTHONHASHSEED=0",
    "SAJU_ANALYSIS_WORKERS=2",
    "SAJU_JOB_MAX_PENDING=12",
    "SAJU_JOB_STALE_SECONDS=600",
    "SAJU_JOB_ESTIMATED_SECONDS=15",
    "SAJU_JOB_HARD_TIMEOUT_SECONDS=120",
    "SAJU_LOG_LEVEL=INFO",
    "SAJU_RELEASE_REVISION=$ImageTag"
) -join ","

Write-Host "Building image: $image"
Push-Location $repoRoot
try {
    Invoke-GCloud builds submit . `
        --tag $image `
        --project $ProjectId
} finally {
    Pop-Location
}

Write-Host "Deploying isolated staging service: $Service"
Invoke-GCloud run deploy $Service `
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
    --labels "app=aisaju-leehyeon,environment=staging"

$serviceUrl = Get-GCloudValue run services describe $Service `
    --project $ProjectId `
    --region $Region `
    --format "value(status.url)"
if (-not $serviceUrl) {
    throw "The staging service was deployed, but its URL could not be read."
}

Write-Host "Staging URL: $serviceUrl"
Write-Host "The public production service and DNS were not changed."
Write-Host "Verify: .\deploy\cloudrun\verify-staging.ps1 -ProjectId $ProjectId"

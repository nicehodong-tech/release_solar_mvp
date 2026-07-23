[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$StagingService = "aisaju-leehyeon-staging",
    [string]$ProductionService = "aisaju-leehyeon-production",
    [string]$PublicUrl = "https://aisajuleehyeon.com"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

Write-Host "1/5 Re-verifying staging against the current public production service."
& (Join-Path $PSScriptRoot "verify-staging.ps1") `
    -ProjectId $ProjectId `
    -Region $Region `
    -Service $StagingService `
    -ProductionUrl $PublicUrl
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

$previousRevision = Get-GCloudValue run services describe $ProductionService `
    --project $ProjectId `
    --region $Region `
    --format="value(status.latestReadyRevisionName)"
if (-not $previousRevision) {
    throw "Could not read the current production revision."
}

$releaseId = ($image -split "[:@]")[-1]
$timestamp = Get-Date -Format "yyMMdd-HHmmss"
$candidateSuffix = "release-$timestamp"
$candidateTag = "candidate"
$environment = @(
    "PYTHONHASHSEED=0",
    "SAJU_ANALYSIS_WORKERS=2",
    "SAJU_JOB_MAX_PENDING=12",
    "SAJU_JOB_STALE_SECONDS=600",
    "SAJU_JOB_ESTIMATED_SECONDS=15",
    "SAJU_JOB_HARD_TIMEOUT_SECONDS=120",
    "SAJU_LOG_LEVEL=INFO",
    "SAJU_RELEASE_REVISION=$releaseId"
) -join ","

Write-Host "2/5 Deploying the verified image as a zero-traffic candidate: $image"
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
    --labels "app=aisaju-leehyeon,environment=production" `
    --revision-suffix $candidateSuffix `
    --tag $candidateTag `
    --no-traffic

$serviceStateText = Get-GCloudValue run services describe $ProductionService `
    --project $ProjectId `
    --region $Region `
    --format="json"
$serviceState = $serviceStateText | ConvertFrom-Json
$candidateRevision = [string]$serviceState.status.latestCreatedRevisionName
$candidateRoute = @($serviceState.status.traffic |
    Where-Object { $_.revisionName -eq $candidateRevision -and $_.url } |
    Select-Object -First 1)
$candidateUrl = [string]$candidateRoute.url
if (-not $candidateRevision -or -not $candidateUrl) {
    throw "The zero-traffic candidate revision or tagged URL could not be read."
}

Push-Location $repoRoot
try {
    Write-Host "3/5 Verifying the candidate revision before public traffic changes."
    & $python scripts\operational_check.py $candidateUrl --concurrency 2 --timeout 300 --health-path /health
    if ($LASTEXITCODE -ne 0) {
        throw "Candidate operational verification failed."
    }
    & $python scripts\cloudrun_parity_check.py `
        (Get-GCloudValue run services describe $StagingService --project $ProjectId --region $Region --format="value(status.url)") `
        $candidateUrl `
        --sample-count 4 `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Candidate and staging engine parity failed."
    }

    Write-Host "4/5 Routing public traffic to the verified candidate."
    Invoke-GCloud run services update-traffic $ProductionService `
        --project $ProjectId `
        --region $Region `
        --to-revisions "$candidateRevision=100"

    try {
        Write-Host "5/5 Verifying the public domain after traffic switch."
        & $python scripts\operational_check.py $PublicUrl --concurrency 2 --timeout 300 --health-path /health
        if ($LASTEXITCODE -ne 0) {
            throw "Public production operational verification failed."
        }
        & $python scripts\cloudrun_parity_check.py `
            $candidateUrl `
            $PublicUrl `
            --sample-count 4 `
            --timeout 300
        if ($LASTEXITCODE -ne 0) {
            throw "Public production does not match the verified candidate."
        }
    } catch {
        Write-Warning "Post-switch verification failed. Restoring $previousRevision."
        Invoke-GCloud run services update-traffic $ProductionService `
            --project $ProjectId `
            --region $Region `
            --to-revisions "$previousRevision=100"
        throw
    }
} finally {
    Pop-Location
}

Write-Host "Production promotion passed without changing DNS."
Write-Host "Previous revision: $previousRevision"
Write-Host "Current revision: $candidateRevision"
Write-Host "Public URL: $PublicUrl"

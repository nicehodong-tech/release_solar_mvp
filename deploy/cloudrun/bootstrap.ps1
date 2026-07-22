[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Repository = "aisaju"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
Invoke-GCloud config set project $ProjectId
Invoke-GCloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    compute.googleapis.com `
    certificatemanager.googleapis.com `
    --project $ProjectId

& $script:GCloud artifacts repositories describe $Repository `
    --location $Region `
    --project $ProjectId *> $null
if ($LASTEXITCODE -ne 0) {
    Invoke-GCloud artifacts repositories create $Repository `
        --repository-format docker `
        --location $Region `
        --description "AI Saju Leehyeon container images" `
        --project $ProjectId
}

Write-Host "Cloud Run prerequisites are ready."
Write-Host "Next: .\deploy\cloudrun\deploy-staging.ps1 -ProjectId $ProjectId"

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Service = "aisaju-leehyeon-staging"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId

& $script:GCloud run services update $Service `
    --project $ProjectId `
    --region $Region `
    --min-instances 0 `
    --max-instances 1
if ($LASTEXITCODE -ne 0) {
    throw "Could not lower the staging minimum instances."
}

Write-Host "Staging minimum instances are now 0."
Write-Host "The service remains available and will start again on the next request."
Write-Host "A new deploy restores the validation setting of min-instances=1."

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Service = "aisaju-leehyeon-production"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId

Invoke-GCloud run services update $Service `
    --project $ProjectId `
    --region $Region `
    --ingress internal-and-cloud-load-balancing

Write-Host "Production ingress now accepts public traffic only through the load balancer."
Write-Host "The custom domain remains public; the direct run.app endpoint is blocked externally."

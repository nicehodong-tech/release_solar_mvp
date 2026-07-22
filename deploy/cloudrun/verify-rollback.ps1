[CmdletBinding()]
param(
    [string]$Domain = "aisajuleehyeon.com",
    [string]$WwwDomain = "www.aisajuleehyeon.com",
    [string]$CloudtypeTarget = "mqquvbd6c9bd03f8.sel3.cloudtype.app"
)

$ErrorActionPreference = "Stop"

foreach ($hostName in @($Domain, $WwwDomain)) {
    $record = Resolve-DnsName $hostName -Type CNAME -Server 8.8.8.8 -ErrorAction Stop |
        Select-Object -First 1
    if ($record.NameHost.TrimEnd(".") -ne $CloudtypeTarget) {
        throw "$hostName has not returned to the Cloudtype CNAME. Current: $($record.NameHost)"
    }
}

$health = Invoke-RestMethod -Uri "https://$Domain/healthz" -TimeoutSec 30
if (-not $health.ok -or $health.status -ne "healthy") {
    throw "The restored Cloudtype domain is not healthy."
}

Write-Host "ROLLBACK VERIFIED: both hosts resolve to Cloudtype and /healthz is healthy."

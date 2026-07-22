[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Domain = "aisajuleehyeon.com",
    [string]$WwwDomain = "www.aisajuleehyeon.com",
    [string]$Prefix = "aisaju-web"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId

$apexAuthorization = "$Prefix-apex-auth"
$wwwAuthorization = "$Prefix-www-auth"
$certificate = "$Prefix-cert"
$certificateMap = "$Prefix-cert-map"
$apexEntry = "$Prefix-apex-entry"
$wwwEntry = "$Prefix-www-entry"

function Ensure-DnsAuthorization {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$TargetDomain
    )
    if (-not (Test-GCloudResource -Arguments @(
        "certificate-manager", "dns-authorizations", "describe", $Name,
        "--project", $ProjectId
    ))) {
        Invoke-GCloud certificate-manager dns-authorizations create $Name `
            --project $ProjectId `
            --domain $TargetDomain `
            --type FIXED_RECORD
    }
}

Ensure-DnsAuthorization -Name $apexAuthorization -TargetDomain $Domain
Ensure-DnsAuthorization -Name $wwwAuthorization -TargetDomain $WwwDomain

if (-not (Test-GCloudResource -Arguments @(
    "certificate-manager", "certificates", "describe", $certificate,
    "--project", $ProjectId
))) {
    Invoke-GCloud certificate-manager certificates create $certificate `
        --project $ProjectId `
        --domains "$Domain,$WwwDomain" `
        --dns-authorizations "$apexAuthorization,$wwwAuthorization"
}

if (-not (Test-GCloudResource -Arguments @(
    "certificate-manager", "maps", "describe", $certificateMap,
    "--project", $ProjectId
))) {
    Invoke-GCloud certificate-manager maps create $certificateMap --project $ProjectId
}

if (-not (Test-GCloudResource -Arguments @(
    "certificate-manager", "maps", "entries", "describe", $apexEntry,
    "--map", $certificateMap, "--project", $ProjectId
))) {
    Invoke-GCloud certificate-manager maps entries create $apexEntry `
        --project $ProjectId `
        --map $certificateMap `
        --certificates $certificate `
        --hostname $Domain
}

if (-not (Test-GCloudResource -Arguments @(
    "certificate-manager", "maps", "entries", "describe", $wwwEntry,
    "--map", $certificateMap, "--project", $ProjectId
))) {
    Invoke-GCloud certificate-manager maps entries create $wwwEntry `
        --project $ProjectId `
        --map $certificateMap `
        --certificates $certificate `
        --hostname $WwwDomain
}

Write-Host "Add these two CNAME records in Gabia. They do not move web traffic:"
foreach ($authorization in @($apexAuthorization, $wwwAuthorization)) {
    $json = & $script:GCloud certificate-manager dns-authorizations describe $authorization `
        --project $ProjectId `
        --format json
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read DNS authorization '$authorization'."
    }
    $record = ($json | ConvertFrom-Json).dnsResourceRecord
    Write-Host "HOST: $($record.name.TrimEnd('.'))"
    Write-Host "TYPE: $($record.type)"
    Write-Host "VALUE: $($record.data)"
    Write-Host "TTL: 300"
    Write-Host ""
}

$certificateState = (& $script:GCloud certificate-manager certificates describe $certificate `
    --project $ProjectId `
    --format="value(managed.state)").Trim()
if (-not $certificateState) {
    $certificateState = "PROVISIONING"
}
Write-Host "Certificate state: $certificateState"
if ($certificateState -ne "ACTIVE") {
    Write-Host "After the CNAME records propagate, rerun this script until the state is ACTIVE."
} else {
    Write-Host "Certificate is ACTIVE and can be attached before the traffic DNS switch."
}

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "asia-northeast3",
    [string]$Service = "aisaju-leehyeon-production",
    [string]$Domain = "aisajuleehyeon.com",
    [string]$WwwDomain = "www.aisajuleehyeon.com",
    [string]$Prefix = "aisaju-web"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

$ipAddress = Get-GCloudValue compute addresses describe "$Prefix-ip" `
    --project $ProjectId `
    --global `
    --format="value(address)"
if (-not $ipAddress) {
    throw "Could not read the load balancer IP address."
}

$certificateState = Get-GCloudValue certificate-manager certificates describe "$Prefix-cert" `
    --project $ProjectId `
    --format="value(managed.state)"
if ($certificateState -ne "ACTIVE") {
    throw "The managed certificate is not ACTIVE. Current state: $certificateState"
}

$productionUrl = Get-GCloudValue run services describe $Service `
    --project $ProjectId `
    --region $Region `
    --format="value(status.url)"
if (-not $productionUrl) {
    throw "Could not read the Cloud Run production URL."
}

$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    throw "curl.exe is required for TLS verification."
}

$localIndex = Get-Content -Raw -Encoding utf8 (Join-Path $repoRoot "saju_web\static\index.html")
$releaseMarker = [regex]::Match($localIndex, "production-release-v[0-9]+").Value
if (-not $releaseMarker) {
    throw "The local product shell has no release marker."
}

Write-Host "1/3 TLS, certificate, and product shell"
foreach ($hostName in @($Domain, $WwwDomain)) {
    $healthText = & $curl.Source --silent --show-error --fail --location --compressed `
        --resolve "${hostName}:443:${ipAddress}" `
        "https://${hostName}/health"
    if ($LASTEXITCODE -ne 0) {
        throw "The forced-DNS health request failed for $hostName."
    }
    $health = $healthText | ConvertFrom-Json
    if (-not $health.ok -or $health.status -ne "healthy" -or $health.runtime.service -ne $Service) {
        throw "$hostName is not serving the expected Cloud Run production service."
    }

    $indexText = (& $curl.Source --silent --show-error --fail --location --compressed `
        --resolve "${hostName}:443:${ipAddress}" `
        "https://${hostName}/") -join "`n"
    if ($LASTEXITCODE -ne 0 -or $indexText -notmatch [regex]::Escape($releaseMarker)) {
        throw "$hostName did not return the current product shell."
    }
}

Write-Host "2/3 Public DNS"
foreach ($hostName in @($Domain, $WwwDomain)) {
    $addresses = @(Resolve-DnsName $hostName -Type A -Server 8.8.8.8 -ErrorAction Stop |
        Where-Object { $_.IPAddress } |
        ForEach-Object { [string]$_.IPAddress })
    if ($ipAddress -notin $addresses) {
        throw "$hostName does not resolve to $ipAddress. Current: $($addresses -join ', ')"
    }
}

Push-Location $repoRoot
try {
    Write-Host "3/3 Public edge and direct service parity"
    & $python scripts\operational_check.py "https://$Domain" --concurrency 2 --timeout 300 --health-path /health
    if ($LASTEXITCODE -ne 0) {
        throw "Public production operational verification failed."
    }
    & $python scripts\cloudrun_parity_check.py `
        $productionUrl `
        "https://$Domain" `
        --sample-count 4 `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "The public edge and direct Cloud Run service differ."
    }
} finally {
    Pop-Location
}

Write-Host "EDGE VERIFICATION PASSED."
Write-Host "$Domain and $WwwDomain -> $ipAddress"
Write-Host "Certificate: $certificateState"

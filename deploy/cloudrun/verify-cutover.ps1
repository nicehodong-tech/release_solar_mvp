[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Domain = "aisajuleehyeon.com",
    [string]$WwwDomain = "www.aisajuleehyeon.com",
    [string]$Prefix = "aisaju-web",
    [string]$LegacyUrl = "https://port-0-release-solar-mvp-mqquvbd6c9bd03f8.sel3.cloudtype.app"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId
$python = Get-PythonExecutable

$expectedIp = (& $script:GCloud compute addresses describe "$Prefix-ip" `
    --project $ProjectId `
    --global `
    --format="value(address)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $expectedIp) {
    throw "Could not read the expected load balancer IP."
}

Write-Host "1/4 Public DNS"
foreach ($hostName in @($Domain, $WwwDomain)) {
    $resolvedIps = @(Resolve-DnsName $hostName -Type A -Server 8.8.8.8 -ErrorAction Stop |
        Where-Object { $_.IPAddress } |
        ForEach-Object { $_.IPAddress })
    if ($expectedIp -notin $resolvedIps) {
        throw "$hostName does not resolve to the load balancer IP $expectedIp. Current: $($resolvedIps -join ', ')"
    }
    Write-Host "$hostName -> $expectedIp"
}

$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    throw "curl.exe is required for public endpoint verification."
}

Write-Host "2/4 HTTPS for apex and www"
foreach ($hostName in @($Domain, $WwwDomain)) {
    & $curl.Source --silent --show-error --fail --compressed `
        --max-time 30 `
        "https://${hostName}/healthz" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "HTTPS health failed for $hostName."
    }
}

Push-Location $repoRoot
try {
    Write-Host "3/4 Public operational contract"
    & $python scripts\operational_check.py "https://$Domain" --concurrency 2 --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Public operational verification failed."
    }

    Write-Host "4/4 Legacy-to-public full engine parity"
    & $python scripts\cloudrun_parity_check.py `
        $LegacyUrl `
        "https://$Domain" `
        --sample-count 4 `
        --timeout 300
    if ($LASTEXITCODE -ne 0) {
        throw "Post-cutover engine parity failed."
    }
} finally {
    Pop-Location
}

Write-Host "CUTOVER VERIFICATION PASSED."
Write-Host "Keep Cloudtype running through the DNS TTL grace period."
Write-Host "After at least 30 stable minutes: .\deploy\cloudrun\lock-production.ps1 -ProjectId $ProjectId"

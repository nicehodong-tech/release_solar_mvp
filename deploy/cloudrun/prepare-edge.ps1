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
. (Join-Path $PSScriptRoot "common.ps1")
Assert-GCloudSession -ProjectId $ProjectId

$certificate = "$Prefix-cert"
$certificateMap = "$Prefix-cert-map"
$address = "$Prefix-ip"
$neg = "$Prefix-neg"
$backend = "$Prefix-backend"
$urlMap = "$Prefix-url-map"
$httpsProxy = "$Prefix-https-proxy"
$httpsRule = "$Prefix-https-rule"
$redirectMap = "$Prefix-http-redirect-map"
$httpProxy = "$Prefix-http-proxy"
$httpRule = "$Prefix-http-rule"

$certificateState = (& $script:GCloud certificate-manager certificates describe $certificate `
    --project $ProjectId `
    --format="value(managed.state)").Trim()
if ($LASTEXITCODE -ne 0 -or $certificateState -ne "ACTIVE") {
    throw "Certificate '$certificate' is not ACTIVE. Run prepare-certificate.ps1 and add its CNAME records first."
}

if (-not (Test-GCloudResource -Arguments @(
    "run", "services", "describe", $Service,
    "--project", $ProjectId, "--region", $Region
))) {
    throw "Cloud Run production service '$Service' does not exist."
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "addresses", "describe", $address,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute addresses create $address `
        --project $ProjectId `
        --global `
        --ip-version IPV4 `
        --network-tier PREMIUM
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "network-endpoint-groups", "describe", $neg,
    "--project", $ProjectId, "--region", $Region
))) {
    Invoke-GCloud compute network-endpoint-groups create $neg `
        --project $ProjectId `
        --region $Region `
        --network-endpoint-type serverless `
        --cloud-run-service $Service
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "backend-services", "describe", $backend,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute backend-services create $backend `
        --project $ProjectId `
        --global `
        --load-balancing-scheme EXTERNAL_MANAGED `
        --timeout 300s `
        --enable-logging `
        --logging-sample-rate 1.0
}

$backendJson = & $script:GCloud compute backend-services describe $backend `
    --project $ProjectId `
    --global `
    --format json
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect backend service '$backend'."
}
$backendState = $backendJson | ConvertFrom-Json
$negAttached = @($backendState.backends) | Where-Object {
    $_.group -and $_.group.EndsWith("/networkEndpointGroups/$neg")
}
if (-not $negAttached) {
    Invoke-GCloud compute backend-services add-backend $backend `
        --project $ProjectId `
        --global `
        --network-endpoint-group $neg `
        --network-endpoint-group-region $Region
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "url-maps", "describe", $urlMap,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute url-maps create $urlMap `
        --project $ProjectId `
        --global `
        --default-service $backend
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "target-https-proxies", "describe", $httpsProxy,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute target-https-proxies create $httpsProxy `
        --project $ProjectId `
        --global `
        --url-map $urlMap `
        --certificate-map $certificateMap
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "forwarding-rules", "describe", $httpsRule,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute forwarding-rules create $httpsRule `
        --project $ProjectId `
        --global `
        --load-balancing-scheme EXTERNAL_MANAGED `
        --network-tier PREMIUM `
        --address $address `
        --target-https-proxy $httpsProxy `
        --ports 443
}

$redirectYaml = Join-Path ([System.IO.Path]::GetTempPath()) "$redirectMap.yaml"
$redirectConfig = @"
name: $redirectMap
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
"@
[System.IO.File]::WriteAllText($redirectYaml, $redirectConfig, [System.Text.UTF8Encoding]::new($false))
try {
    Invoke-GCloud compute url-maps import $redirectMap `
        --project $ProjectId `
        --global `
        --source $redirectYaml `
        --quiet
} finally {
    Remove-Item -LiteralPath $redirectYaml -ErrorAction SilentlyContinue
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "target-http-proxies", "describe", $httpProxy,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute target-http-proxies create $httpProxy `
        --project $ProjectId `
        --global `
        --url-map $redirectMap
}

if (-not (Test-GCloudResource -Arguments @(
    "compute", "forwarding-rules", "describe", $httpRule,
    "--project", $ProjectId, "--global"
))) {
    Invoke-GCloud compute forwarding-rules create $httpRule `
        --project $ProjectId `
        --global `
        --load-balancing-scheme EXTERNAL_MANAGED `
        --network-tier PREMIUM `
        --address $address `
        --target-http-proxy $httpProxy `
        --ports 80
}

$ipAddress = (& $script:GCloud compute addresses describe $address `
    --project $ProjectId `
    --global `
    --format="value(address)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $ipAddress) {
    throw "Could not read the load balancer IP address."
}

Write-Host "Edge infrastructure is ready. Public DNS was not changed."
Write-Host "Load balancer IP: $ipAddress"
Write-Host "Verify before DNS: .\deploy\cloudrun\verify-edge.ps1 -ProjectId $ProjectId"
Write-Host "Cutover records for Gabia after verification:"
Write-Host "@    A    $ipAddress    TTL 300"
Write-Host "www  A    $ipAddress    TTL 300"
Write-Host "Remove the existing @ and www Cloudtype CNAME records only at cutover time."

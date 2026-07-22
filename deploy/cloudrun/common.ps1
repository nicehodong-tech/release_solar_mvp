$ErrorActionPreference = "Stop"

function Get-GCloudExecutable {
    $command = Get-Command gcloud.cmd -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command gcloud -ErrorAction SilentlyContinue
    }
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"),
        (Join-Path $env:ProgramFiles "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"),
        (Join-Path ${env:ProgramFiles(x86)} "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "Google Cloud CLI is not installed. Install Google.CloudSDK first."
}

function Invoke-GCloud {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & $script:GCloud @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed: gcloud $($Arguments -join ' ')"
    }
}

function Get-GCloudValue {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    $lines = @(& $script:GCloud @Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed: gcloud $($Arguments -join ' ')"
    }
    return (($lines | ForEach-Object { [string]$_ }) -join "`n").Trim()
}

function Test-GCloudResource {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & $script:GCloud @Arguments *> $null
    return $LASTEXITCODE -eq 0
}

function Assert-GCloudSession {
    param([Parameter(Mandatory = $true)][string]$ProjectId)

    $script:GCloud = Get-GCloudExecutable
    $accountJson = (@(& $script:GCloud auth list --format=json) -join "`n")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect the Google Cloud login state."
    }
    $accounts = @($accountJson | ConvertFrom-Json)
    $activeAccount = @($accounts | Where-Object { $_.status -eq "ACTIVE" }) |
        Select-Object -ExpandProperty account -First 1
    if (-not $activeAccount) {
        throw "No active Google Cloud account. Run: gcloud auth login"
    }

    & $script:GCloud projects describe $ProjectId --format="value(projectId)" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "The Google Cloud project '$ProjectId' is unavailable to $activeAccount."
    }

    Write-Host "Google account: $activeAccount"
    Write-Host "Google project: $ProjectId"
}

function Get-PythonExecutable {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python is not installed or python is not on PATH."
    }
    return $python.Source
}

function Get-GitExecutable {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git) {
        return $git.Source
    }

    $desktopRoot = Join-Path $env:LOCALAPPDATA "GitHubDesktop"
    if (Test-Path -LiteralPath $desktopRoot) {
        $candidate = Get-ChildItem -LiteralPath $desktopRoot -Directory -Filter "app-*" |
            Sort-Object Name -Descending |
            ForEach-Object {
                Join-Path $_.FullName "resources\app\git\cmd\git.exe"
            } |
            Where-Object { Test-Path -LiteralPath $_ } |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }

    throw "Git is not installed or could not be found."
}

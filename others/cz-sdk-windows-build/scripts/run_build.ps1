param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('paycenter', 'all')]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$Jdk8Home,

    [Parameter(Mandatory = $true)]
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$checkEnv = Join-Path $scriptDir 'check_env.ps1'
$diagnose = Join-Path $scriptDir 'diagnose_build_failure.ps1'

if (-not (Test-Path $RepoRoot)) {
    Write-Error "RepoRoot not found: $RepoRoot"
    exit 30
}

& $checkEnv -Jdk8Home $Jdk8Home
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Push-Location $RepoRoot
try {
    $logDir = Join-Path $RepoRoot '.codex-logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $logPath = Join-Path $logDir "build_$Mode`_$timestamp.log"

    if ($Mode -eq 'paycenter') {
        $mvnArgs = @(
            '-o'
            '-Dmaven.repo.local=.m2-temp'
            '-f'
            'czsdk-parent/pom.xml'
            '-pl'
            '../czsdk-paycenter'
            '-am'
            '-DskipTests'
            'compile'
        )
    }
    else {
        $mvnArgs = @(
            '-o'
            '-Dmaven.repo.local=.m2-temp'
            '-f'
            'czsdk-parent/pom.xml'
            '-DskipTests'
            'compile'
        )
    }

    Write-Host "RepoRoot=$RepoRoot"
    Write-Host "Mode=$Mode"
    Write-Host "LogPath=$logPath"
    Write-Host "Running: mvn $($mvnArgs -join ' ')"

    $output = & mvn @mvnArgs 2>&1
    $output | Tee-Object -FilePath $logPath

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build succeeded. Log saved to: $logPath"
        exit 0
    }

    Write-Warning "Build failed. Running diagnosis..."
    & $diagnose -LogPath $logPath
    exit 1
}
finally {
    Pop-Location
}

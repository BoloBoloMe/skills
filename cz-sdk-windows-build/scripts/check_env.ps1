param(
    [Parameter(Mandatory = $true)]
    [string]$Jdk8Home
)

$ErrorActionPreference = 'Stop'

$javaExe = Join-Path $Jdk8Home 'bin\java.exe'
if (-not (Test-Path $javaExe)) {
    Write-Error "java.exe not found under JDK home: $Jdk8Home"
    exit 10
}

$env:JAVA_HOME = $Jdk8Home
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

Write-Host "JAVA_HOME=$env:JAVA_HOME"
Write-Host 'Running mvn -version ...'

$mvnOutput = & mvn -version 2>&1
$mvnText = ($mvnOutput | Out-String)
Write-Host $mvnText

if ($LASTEXITCODE -ne 0) {
    Write-Error 'mvn -version failed.'
    exit 11
}

if ($mvnText -notmatch 'Java version:\s*1\.8\.') {
    Write-Error 'mvn -version did not confirm Java 8. Stop build.'
    exit 12
}

Write-Host 'Environment validation passed: Maven is using Java 8.'
exit 0

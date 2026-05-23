param()

$ErrorActionPreference = 'Stop'

function Test-Jdk8Home {
    param(
        [Parameter(Mandatory = $true)]
        [string]$JdkHome
    )

    $javaExe = Join-Path $JdkHome 'bin\java.exe'
    if (-not (Test-Path $javaExe)) {
        return $null
    }

    try {
        $output = & $javaExe -version 2>&1
        $text = ($output | Out-String)
        $isJdk8 = $false

        if ($text -match 'version "1\.8\.0[_\.\d]*"') {
            $isJdk8 = $true
        }

        [pscustomobject]@{
            Home     = $JdkHome
            JavaExe  = $javaExe
            IsJdk8   = $isJdk8
            Version  = ($text -replace '\r', '').Trim()
        }
    }
    catch {
        return [pscustomobject]@{
            Home     = $JdkHome
            JavaExe  = $javaExe
            IsJdk8   = $false
            Version  = "Failed to inspect: $($_.Exception.Message)"
        }
    }
}

$candidateRoots = @()

if ($env:USERPROFILE) {
    $candidateRoots += (Join-Path $env:USERPROFILE '.jdks')
}

$candidateRoots += @(
    'C:\Program Files\Java',
    'C:\Program Files\Eclipse Adoptium',
    'C:\Program Files\Temurin'
)

$homes = New-Object System.Collections.Generic.List[string]

foreach ($root in $candidateRoots) {
    if (Test-Path $root) {
        Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $homes.Add($_.FullName)
        }
    }
}

$results = foreach ($candidateHome in ($homes | Sort-Object -Unique)) {
    Test-Jdk8Home -JdkHome $candidateHome
}

$valid = $results | Where-Object { $_ -and $_.IsJdk8 }

if (-not $valid) {
    Write-Host 'No JDK 8 candidates detected.'
    Write-Host 'Suggested places to check manually:'
    Write-Host '  - C:\Users\<user>\.jdks\temurin-1.8.0_xxx'
    Write-Host '  - C:\Program Files\Java\jdk1.8.*'
    Write-Host '  - C:\Program Files\Eclipse Adoptium\*'
    Write-Host '  - C:\Program Files\Temurin\*'
    exit 2
}

$valid | Select-Object Home, JavaExe, Version | Format-List
exit 0

param(
    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $LogPath)) {
    Write-Error "Log file not found: $LogPath"
    exit 20
}

$text = Get-Content -Path $LogPath -Raw -Encoding UTF8

function Emit-Diagnosis {
    param(
        [string]$Category,
        [string]$Evidence,
        [string]$Advice
    )

    [pscustomobject]@{
        Category = $Category
        Evidence = $Evidence
        Advice   = $Advice
    } | ConvertTo-Json -Depth 3
}

if ($text -match 'IllegalAccessError' -or $text -match 'NoSuchFieldError') {
    if ($text -match 'lombok' -or $text -match 'javac' -or $text -match 'JCTree|JCImport') {
        Emit-Diagnosis `
            -Category 'lombok_javac_compatibility' `
            -Evidence 'Detected IllegalAccessError / NoSuchFieldError with Lombok/Javac internals.' `
            -Advice 'Switch to JDK 8, rerun mvn -version, then retry compile.'
        exit 0
    }

    Emit-Diagnosis `
        -Category 'jdk_version_mismatch' `
        -Evidence 'Detected IllegalAccessError / NoSuchFieldError during Java compile flow.' `
        -Advice 'Verify JAVA_HOME and ensure Maven is running on JDK 8.'
    exit 0
}

if ($text -match 'Could not resolve dependencies' -or
    $text -match 'Failure to find .+ in .+ was cached' -or
    $text -match 'Cannot access .* in offline mode' -or
    $text -match 'offline mode') {
    Emit-Diagnosis `
        -Category 'offline_dependency_missing' `
        -Evidence 'Detected missing dependency resolution under offline/local-cache workflow.' `
        -Advice 'Check whether dependencies exist in local cache or retry without -o if allowed.'
    exit 0
}

if ($text -match 'Non-resolvable parent POM' -or
    $text -match 'Child module .+ does not exist' -or
    $text -match 'Could not find the selected project in the reactor' -or
    $text -match 'The goal you specified requires a project to execute but there is no POM in this directory') {
    Emit-Diagnosis `
        -Category 'pom_or_relative_path_error' `
        -Evidence 'Detected POM, module selection, reactor, or relative path issue.' `
        -Advice 'Check RepoRoot, current working directory, -f target, and -pl relative module path.'
    exit 0
}

if ($text -match 'COMPILATION ERROR' -or
    $text -match '\[ERROR\].+cannot find symbol' -or
    $text -match '\[ERROR\].+incompatible types' -or
    $text -match '\[ERROR\].+package .+ does not exist') {
    Emit-Diagnosis `
        -Category 'source_compile_error' `
        -Evidence 'Detected standard Java source compilation errors.' `
        -Advice 'Treat this as a real code-level compile issue after environment validation is already correct.'
    exit 0
}

Emit-Diagnosis `
    -Category 'unknown' `
    -Evidence 'No known pattern matched.' `
    -Advice 'Review full log manually and confirm JDK 8, Maven version, repo root, and local dependency cache.'
exit 0

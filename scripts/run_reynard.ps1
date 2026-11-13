param(
    [ValidateSet('register-ser', 'register-no-ser', 'patterns-ser', 'patterns-no-ser')]
    [string]$Case = 'register-ser',
    [string]$JavaHome = "$PSScriptRoot/../.runtime/jdk17/jdk-17.0.20.1+1",
    [string]$Maven = 'C:/Users/YuRui/Tools/apache-maven-3.9.16/bin/mvn.cmd',
    [string]$ResultsRoot = "$PSScriptRoot/../results"
)
$ErrorActionPreference = 'Stop'
$ResultsRoot = [System.IO.Path]::GetFullPath($ResultsRoot)
$taskRoot = (Resolve-Path "$PSScriptRoot/..").Path
$source = Join-Path $taskRoot 'baselines/sources/reynard'
$output = [System.IO.Path]::GetFullPath((Join-Path $ResultsRoot "reynard/$Case"))
$class = if ($Case.StartsWith('register')) { 'MetaSuiteIT' } else { 'ResiliencePatternsIT' }
$method = if ($Case.StartsWith('register')) { 'testRegister' } else { 'testCsOpt' }
$expected = if ($Case.StartsWith('register')) { 729 } elseif ($Case -eq 'patterns-ser') { 543 } else { 1849 }
$env:JAVA_HOME = (Resolve-Path $JavaHome).Path
$env:PATH = "$env:JAVA_HOME/bin;$env:PATH"
$env:OUTPUT_DIR = $output
$env:OUTPUT_TAG = $Case
$env:PROXY_IMAGE = 'fit-proxy:latest'
$env:CONTROLLER_IMAGE = 'fit-controller:latest'
$env:USE_SER = if ($Case.EndsWith('no-ser')) { 'false' } else { 'true' }
$env:DOCKER_API_VERSION = '1.44'
New-Item -ItemType Directory -Force $output | Out-Null
Push-Location $source
try {
    $runLog = Join-Path $ResultsRoot "reynard-$Case.log"
    & $Maven -B -ntp test "-Dtest=$class#$method" '-Dsurefire.failIfNoSpecifiedTests=false' '-Dapi.version=1.44' *> $runLog
    if ($LASTEXITCODE -ne 0) { throw "Reynard failed; see $runLog" }
    Copy-Item "library/target/surefire-reports/*$class*" $output -Force
    $reports = @(Get-ChildItem $output -Filter 'TEST-*.xml')
    if ($reports.Count -ne 1) { throw "Expected one suite report in $output" }
    [xml]$xml = Get-Content -LiteralPath $reports[0].FullName -Raw
    if ([int]$xml.testsuite.tests -ne $expected -or [int]$xml.testsuite.failures -ne 0 -or [int]$xml.testsuite.errors -ne 0 -or [int]$xml.testsuite.skipped -ne 0) {
        throw "Results differ from the recorded baseline. Inspect $output"
    }
    Write-Output "$Case : $expected tests, 0 failures, 0 errors, 0 skipped"
} finally { Pop-Location }

param(
    [string]$Output = "results/commercial/appcat/$(Get-Date -Format yyyyMMdd-HHmmss)",
    [string]$AppcatHome = '.runtime/appcat/azure-migrate-appcat-for-java-cli-windows-amd64-7.7.0.11',
    [string]$Jdk = '.runtime/jdk17/jdk-17.0.20.1+1'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:JAVA_HOME = (Resolve-Path $Jdk).Path
$appcatExe = Join-Path (Resolve-Path $AppcatHome).Path 'appcat.exe'
New-Item -ItemType Directory -Path $Output | Out-Null
foreach ($phase in @('before', 'after')) {
    & $appcatExe analyze --input "baselines/fixtures/appcat/$phase" --output "$Output/$phase" --target azure-aks --mode source-only --disable-telemetry --output-format json *> "$Output/$phase-cli.log"
    if ($LASTEXITCODE -ne 0) { throw "AppCAT $phase failed; inspect $Output/$phase-cli.log" }
}
python scripts/verify_appcat.py $Output --jdk $env:JAVA_HOME
if ($LASTEXITCODE -ne 0) { throw 'Native report or business verification failed' }

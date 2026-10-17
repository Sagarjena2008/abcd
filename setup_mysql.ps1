#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'

$server = 'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe'
$serviceName = 'MySQL84'
$mysqlRoot = Join-Path $env:ProgramData 'MySQL\MySQL Server 8.4'
$dataDir = Join-Path $mysqlRoot 'Data'
$config = Join-Path $mysqlRoot 'my.ini'

if (-not (Test-Path $server)) {
    throw "MySQL Server was not found at $server. Install MySQL Server 8.4 first."
}
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    if ($existingService.Status -ne 'Stopped') {
        throw "Stop the $serviceName service before changing its configuration."
    }
    & sc.exe delete $serviceName
    if ($LASTEXITCODE -ne 0) {
        throw "Could not replace the existing $serviceName service."
    }
}
$initialized = Test-Path (Join-Path $dataDir 'auto.cnf')
if ((Test-Path $dataDir) -and -not $initialized -and (Get-ChildItem $dataDir -Force | Select-Object -First 1)) {
    throw "The MySQL data folder already contains files but is not initialized. No data was changed."
}

New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
$configText = @"
[mysqld]
basedir="$($server | Split-Path | Split-Path)"
datadir="$dataDir"
port=3306
bind-address=127.0.0.1
mysqlx=0
"@
Set-Content -Path $config -Value $configText -Encoding ASCII

if (-not $initialized) {
    & $server "--defaults-file=$config" --initialize-insecure --console
    if ($LASTEXITCODE -ne 0) {
        throw "MySQL data initialization failed with exit code $LASTEXITCODE."
    }
}

& $server --install $serviceName "--defaults-file=$config"
if ($LASTEXITCODE -ne 0) {
    throw "MySQL Windows service installation failed with exit code $LASTEXITCODE."
}
Start-Service -Name $serviceName
Write-Output "MySQL Server is initialized and running as the local-only $serviceName service."

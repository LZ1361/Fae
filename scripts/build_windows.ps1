param(
  [string]$Python = "python",
  [string]$Name = "MingYun",
  [string]$PipIndexUrl = "https://pypi.org/simple"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if (-not (Test-Path ".venv-build")) {
  & $Python -m venv .venv-build
}

$VenvPython = Join-Path $ProjectRoot ".venv-build\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install --index-url $PipIndexUrl -r requirements-build.txt

$addData = @(
  "mingyun_app/static;mingyun_app/static",
  "mingyun_app/model_registry.json;mingyun_app",
  "mingyun_app/.env.example;mingyun_app"
)

$args = @(
  "-m", "PyInstaller",
  "--name", $Name,
  "--clean",
  "--noconfirm",
  "--onefile",
  "--console",
  "--icon",
  "mingyun_app/static/assets/mingyun-destiny-icon.ico"
)

foreach ($item in $addData) {
  $args += @("--add-data", $item)
}

$args += "mingyun_app/app.py"

& $VenvPython @args

$ExePath = Join-Path $ProjectRoot "dist\$Name.exe"
if (-not (Test-Path $ExePath)) {
  throw "Build finished but executable was not found: $ExePath"
}

Write-Host "Build complete: $ExePath"
Write-Host "Run it and keep the window open. It will open http://127.0.0.1:8787/ automatically."

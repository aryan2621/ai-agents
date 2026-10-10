# Windows version of `npm run build:sidecar`: builds the Python backend with PyInstaller and
# copies it to src-tauri/binaries/python-backend/, which the installer ships as a resource.
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Binaries = Join-Path $Root 'src-tauri\binaries'

Push-Location $Backend
try {
  python -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python virtual environment' }
  $Python = Join-Path $Backend '.venv\Scripts\python.exe'
  $env:PIP_REQUIRE_HASHES = '0'
  & $Python -m pip install -r requirements.txt pyinstaller
  if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }
  & $Python -m PyInstaller --noconfirm python-backend.spec
  if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
} finally {
  Pop-Location
}

$Dest = Join-Path $Binaries 'python-backend'
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
New-Item -ItemType Directory -Force -Path $Binaries | Out-Null
Copy-Item -Recurse (Join-Path $Backend 'dist\python-backend') $Dest
Set-Content -Path (Join-Path $Binaries '.build-id') -Value 'builtin-llm-v1'

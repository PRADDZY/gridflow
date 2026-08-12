$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$vendorDirectory = Join-Path $projectRoot "python_modules"
$lockfile = Join-Path $projectRoot "pylock.toml"

New-Item -ItemType Directory -Force -Path $vendorDirectory | Out-Null
& uv pip install `
  --target $vendorDirectory `
  --python-version 3.13 `
  --python-platform wasm32-pyodide2025 `
  --no-build `
  -r $lockfile `
  --preview-features pylock
if ($LASTEXITCODE -ne 0) {
  throw "Failed to prepare the Cloudflare Python vendor bundle."
}

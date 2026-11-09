# Compiles the Inno Setup installer. Requires Inno Setup 6 and a prior PyInstaller build.
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$exe = Join-Path $root "dist\PCRemoteControl.exe"
if (-not (Test-Path $exe)) {
    throw "dist\PCRemoteControl.exe not found. Run 'pyinstaller PCRemoteControl.spec' first."
}

$candidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source,
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $candidates) {
    throw "ISCC.exe not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php"
}

& $candidates[0] (Join-Path $PSScriptRoot "PCRemoteControl.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC failed with exit code $LASTEXITCODE" }
Write-Host "Installer written to dist\installer"

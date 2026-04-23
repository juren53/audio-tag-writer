# Audio Tag Writer - PyInstaller build script
# Usage: .\build_exe.ps1
# Output: dist\audio-tag-writer.exe

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$VenvPip    = Join-Path $ScriptDir "venv\Scripts\pip.exe"
$SpecFile   = Join-Path $ScriptDir "audio-tag-writer.spec"

# ── Verify venv exists ────────────────────────────────────────────
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Run .\run.ps1 first to create it."
    exit 1
}

# ── Install PyInstaller if needed ─────────────────────────────────
$piCheck = & $VenvPython -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    & $VenvPip install pyinstaller --quiet
}

# ── Clean previous build artefacts ───────────────────────────────
foreach ($dir in @("build", "dist")) {
    $fullPath = Join-Path $ScriptDir $dir
    if (Test-Path $fullPath) {
        Write-Host "Removing $dir\ ..."
        Remove-Item -Recurse -Force $fullPath
    }
}

# ── Run PyInstaller ───────────────────────────────────────────────
Write-Host "Building audio-tag-writer.exe ..."
& $VenvPython -m PyInstaller $SpecFile --noconfirm

if ($LASTEXITCODE -eq 0) {
    $ExePath = Join-Path $ScriptDir "dist\audio-tag-writer.exe"
    $Size    = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Build succeeded: $ExePath  ($Size MB)"
} else {
    Write-Error "PyInstaller build failed (exit code $LASTEXITCODE)."
    exit $LASTEXITCODE
}

# Audio Tag Writer - PyInstaller build script
# Usage: .\build_exe.ps1
# Output: dist\audio-tag-writer.exe

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$VenvPip    = Join-Path $ScriptDir "venv\Scripts\pip.exe"
$SpecFile   = Join-Path $ScriptDir "audio-tag-writer.spec"

# ── Verify venv exists ────────────────────────────────────────────
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Run .\run.ps1 first to create it."
    exit 1
}

# ── Ensure PyInstaller is installed (pip is a no-op if already present) ──────
Write-Host "Ensuring PyInstaller is installed..."
& $VenvPip install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install PyInstaller."
    exit 1
}

# ── Generate Windows EXE version metadata ────────────────────────
Write-Host "Generating version_info.txt ..."
& $VenvPython generate_version_info.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate version_info.txt."
    exit 1
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

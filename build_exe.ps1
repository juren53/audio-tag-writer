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

# ── Self-test the EXE ────────────────────────────────────────────
# The windowed EXE has no console, so it writes a JSON report. It checks that every
# runtime-imported module is bundled (the v0.7.14a "No module named 'theme_manager'"
# crash), Mutagen works, the docs/icons are bundled and the main window builds.
$Report = Join-Path $ScriptDir "build\selftest.json"
if (Test-Path $Report) { Remove-Item -Force $Report }
Write-Host "Running EXE self-test ..."
$proc = Start-Process -FilePath $ExePath -ArgumentList "--self-test", "`"$Report`"" -PassThru
# A crash at import time shows PyInstaller's "Unhandled exception" dialog and never exits
$proc | Wait-Process -Timeout 120 -ErrorAction SilentlyContinue
if (-not $proc.HasExited) {
    # Kill the bootloader and its child (onefile runs the app in a child process)
    Get-CimInstance Win32_Process -Filter "ParentProcessId=$($proc.Id)" |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Write-Error "EXE self-test did not finish in 120 s; the EXE probably crashed at startup (error dialog). Run dist\audio-tag-writer.exe to see the error."
    exit 1
}
if (-not (Test-Path $Report)) {
    Write-Error "EXE self-test wrote no report (exit code $($proc.ExitCode)); the EXE probably crashed at startup."
    exit 1
}
$st = Get-Content $Report -Raw -Encoding UTF8 | ConvertFrom-Json
$failed = @()
foreach ($p in $st.checks.PSObject.Properties) {
    $mark = if ($p.Value) { "[ OK ]" } else { $failed += $p.Name; "[FAIL]" }
    Write-Host "  $mark $($p.Name)"
}
if ($failed.Count -gt 0 -or $proc.ExitCode -ne 0) {
    Write-Error "EXE self-test failed: $($failed -join ', '). Details: $Report"
    exit 1
}
Write-Host "EXE self-test passed ($(@($st.checks.PSObject.Properties).Count) checks)."

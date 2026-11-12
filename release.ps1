# Audio Tag Writer - GitHub release script
#
# Publishes the version in src/audio_tag_writer/constants.py (APP_VERSION) as a GitHub
# release "vX.Y.Z" with dist\audio-tag-writer.exe (+ a .sha256 file) attached.
#
# Usage:
#   .\release.ps1 -Title "Fix X" -DryRun   # run every check and build, write the notes, publish nothing
#   .\release.ps1 -Title "Fix X"           # check, test, build, show summary, ask before publishing
#   .\release.ps1 -Title "Fix X" -Yes      # same, without the confirmation prompt
#   .\release.ps1 -SkipBuild               # reuse the existing dist\ EXE (its version must match)
#   .\release.ps1 -Draft                   # create the release as a draft (publish later on GitHub)
#   .\release.ps1 -NotesFile x.md
#   .\release.ps1 -SkipCI                  # EMERGENCY ONLY: publish even if CI is not green
#
# The release title is "vX.Y.Z — <Title>" (ATW convention). Without -Title you are asked.
# The commit being released must have a green GitHub Actions CI run (it waits for a
# run still in progress), and the local test suite must pass.
# Release notes = notes/release/vX.Y.Z.md if present, otherwise the CHANGELOG.md
# section for X.Y.Z; a Download section (size, SHA-256) and a "Full Changelog"
# compare link are always appended.
#
# Full procedure: docs/RELEASING.md

param(
    [string]$Title = "",
    [switch]$DryRun,
    [switch]$SkipBuild,
    [switch]$Draft,
    [switch]$Yes,
    [switch]$SkipCI,
    [string]$NotesFile = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Repo       = "juren53/audio-tag-writer"
$ExeName    = "audio-tag-writer.exe"
$ExePath    = Join-Path $Root "dist\$ExeName"
$VenvPython = Join-Path $Root "venv\Scripts\python.exe"
$Dash       = [char]0x2014   # em dash; not written literally so Windows PowerShell 5.1 reads this file correctly

function Step($msg) { Write-Host "`n== $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  [ OK ] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "RELEASE STOPPED: $msg" -ForegroundColor Red; exit 1 }

function Invoke-Git {
    # Local "Continue": under Windows PowerShell 5.1 + Stop, git's stderr would abort the script
    $ErrorActionPreference = "Continue"
    $out = & git.exe @args 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { Fail "git $args failed:`n$($out -join "`n")" }
    return $out
}

# ── Version ──────────────────────────────────────────────────────
$constants = Get-Content "src\audio_tag_writer\constants.py" -Raw -Encoding UTF8
if ($constants -notmatch '(?m)^APP_VERSION\s*=\s*"([^"]+)"') { Fail "APP_VERSION not found in constants.py" }
$Version = $Matches[1]
$Tag = "v$Version"
Write-Host "Releasing Audio Tag Writer $Tag" -ForegroundColor White

# ── Pre-flight checks ────────────────────────────────────────────
Step "Pre-flight checks"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Fail "GitHub CLI (gh) not found. Install from https://cli.github.com" }
& gh auth status *> $null
if ($LASTEXITCODE -ne 0) { Fail "gh is not logged in. Run: gh auth login" }
Ok "gh installed and authenticated"

if (-not (Test-Path $VenvPython)) { Fail "venv not found. Run .\run.ps1 once to create it." }

# Untracked files (e.g. screenshots in notes/) don't go into the release; modified tracked files do
$dirty = Invoke-Git status --porcelain --untracked-files=no
if ($dirty) { Fail "Working tree has uncommitted changes:`n$($dirty -join "`n")`nCommit or stash them first." }
Ok "no uncommitted changes to tracked files"

$branch = (Invoke-Git rev-parse --abbrev-ref HEAD).Trim()
Invoke-Git fetch --quiet origin | Out-Null
$local  = (Invoke-Git rev-parse HEAD).Trim()
$remote = (& git rev-parse "origin/$branch" 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $remote) { Fail "Branch '$branch' has no origin/$branch. Push it first." }
if ($local -ne $remote.Trim()) { Fail "HEAD ($($local.Substring(0,7))) differs from origin/$branch. Push or pull first." }
Ok "branch '$branch' in sync with origin ($($local.Substring(0,7)))"
if ($branch -ne "master") { Warn "releasing from '$branch', not master" }

if (& git tag --list $Tag) { Fail "Tag $Tag already exists locally. Bump APP_VERSION for a new release." }
& gh release view $Tag --repo $Repo *> $null
if ($LASTEXITCODE -eq 0) { Fail "Release $Tag already exists on GitHub. Bump APP_VERSION (point release: add a/b)." }
Ok "tag/release $Tag not used yet"

$changelog = Get-Content "CHANGELOG.md" -Raw -Encoding UTF8
$hdr = "(?m)^## \[" + [regex]::Escape($Version) + "\] - .+$"
if ($changelog -notmatch $hdr) { Fail "CHANGELOG.md has no '## [$Version] - Ddd DD Mon YYYY HH:MM CDT' header." }
Ok "CHANGELOG.md has a $Version entry"

$readme = Get-Content "README.md" -Raw -Encoding UTF8
if ($readme -notmatch [regex]::Escape("releases/tag/$Tag")) { Warn "README.md 'Latest release' does not link $Tag" }

# ── CI must be green for this exact commit ───────────────────────
# GitHub Actions (.github/workflows/ci.yml) runs the suite on Python 3.11 and 3.12.
# CI was red from June to October 2026 while releases went out; this stops that.
$short = $local.Substring(0, 7)
if ($SkipCI) {
    Warn "CI check skipped (-SkipCI) for $short"
} else {
    $run = $null
    for ($i = 0; $i -lt 7 -and -not $run; $i++) {
        # A just-pushed commit can take a few seconds to get its CI run registered
        if ($i -gt 0) { Start-Sleep -Seconds 10 }
        $json = & gh run list --repo $Repo --workflow ci.yml --commit $local --limit 1 `
                    --json databaseId,status,conclusion,url --jq '.[0]' 2>$null
        if ($LASTEXITCODE -eq 0 -and $json -and $json -ne 'null') { $run = $json | ConvertFrom-Json }
    }
    if (-not $run) { Fail "No CI run found for $short on GitHub. Was it pushed? See https://github.com/$Repo/actions" }

    if ($run.status -ne "completed") {
        Write-Host "  [WAIT] CI for $short is '$($run.status)' - waiting for it to finish ($($run.url))" -ForegroundColor Yellow
        & gh run watch $run.databaseId --repo $Repo --interval 20 *> $null
        $run = & gh run view $run.databaseId --repo $Repo --json status,conclusion,url | ConvertFrom-Json
    }
    if ($run.conclusion -ne "success") {
        Fail "CI for $short finished as '$($run.conclusion)': $($run.url)`nFix the failure and push again (or use -SkipCI in an emergency)."
    }
    Ok "CI passed for $short"
}

# ── Local tests (Windows, with the HSTL test corpus when present) ─
Step "Running the test suite"
& $VenvPython -m pytest tests -q -rs
if ($LASTEXITCODE -ne 0) { Fail "Tests failed." }
Ok "tests passed"

# ── Build ────────────────────────────────────────────────────────
if ($SkipBuild) {
    Step "Using existing EXE (-SkipBuild)"
    if (-not (Test-Path $ExePath)) { Fail "$ExePath not found. Run without -SkipBuild." }
} else {
    Step "Building (build_exe.ps1: PyInstaller + EXE self-test)"
    try { & (Join-Path $Root "build_exe.ps1") } catch { Fail "build_exe.ps1 failed: $_" }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $ExePath)) { Fail "build_exe.ps1 failed." }
}

$exeVersion = (Get-Item $ExePath).VersionInfo.ProductVersion
if ($exeVersion -ne $Version) { Fail "EXE ProductVersion is '$exeVersion', expected '$Version'. Rebuild." }
Ok "EXE version $exeVersion"

$exeTime = (Get-Item $ExePath).LastWriteTime
$commitTime = [DateTime]::Parse((Invoke-Git log -1 --format=%cI).Trim())
if ($exeTime -lt $commitTime) { Fail "EXE is older than the last commit. Rebuild (omit -SkipBuild)." }

# ── Title ────────────────────────────────────────────────────────
if (-not $Title) {
    if ($DryRun) { Warn "no -Title given (required to publish)" }
    elseif ($Yes) { Fail "-Title is required with -Yes, e.g. -Title `"Fix EXE startup crash`"" }
    else {
        $Title = (Read-Host "`nRelease title (shown as '$Tag $Dash <title>')").Trim()
        if (-not $Title) { Fail "A release title is required." }
    }
}
$fullTitle = if ($Title) { "$Tag $Dash $Title" } else { $Tag }

# ── Release notes ────────────────────────────────────────────────
Step "Preparing release notes"
$hash = (Get-FileHash $ExePath -Algorithm SHA256).Hash.ToLower()
$sizeMB = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)

$highlights = Join-Path $Root "notes\release\$Tag.md"
if ($NotesFile) {
    if (-not (Test-Path $NotesFile)) { Fail "Notes file not found: $NotesFile" }
    $body = Get-Content $NotesFile -Raw -Encoding UTF8
    $source = $NotesFile
} elseif (Test-Path $highlights) {
    $body = Get-Content $highlights -Raw -Encoding UTF8
    $source = "notes\release\$Tag.md"
} else {
    # CHANGELOG section: from this version's header up to the next '## ' header,
    # minus the '---' separator ATW puts between entries
    $m = [regex]::Match($changelog, "$hdr\r?\n(?<s>[\s\S]*?)(?=\r?\n## |\z)")
    $body = ($m.Groups['s'].Value.Trim() -replace '(\r?\n)*-{3,}\s*$', '').Trim()
    $source = "CHANGELOG.md"
}

$prevTag = (& gh release list --repo $Repo --exclude-drafts --limit 1 --json tagName --jq '.[0].tagName' 2>$null)
$compare = if ($prevTag) { "https://github.com/$Repo/compare/$prevTag...$Tag" } else { "" }

$notes = @"
$($body.Trim())

### Download
``$ExeName`` is a single-file Windows executable ($sizeMB MB). No install is needed.
- SHA-256: ``$hash`` (also attached as ``$ExeName.sha256``)

"@
if ($compare) { $notes += "`n**Full Changelog**: $compare`n" }

New-Item -ItemType Directory -Force -Path (Join-Path $Root "build") | Out-Null
$notesOut = Join-Path $Root "build\release_notes_$Tag.md"
$shaOut   = Join-Path $Root "build\$ExeName.sha256"
[IO.File]::WriteAllText($notesOut, $notes, (New-Object Text.UTF8Encoding $false))
[IO.File]::WriteAllText($shaOut, "$hash  $ExeName`n", (New-Object Text.UTF8Encoding $false))
Ok "notes from $source  ->  build\release_notes_$Tag.md"

# ── Summary / confirm ────────────────────────────────────────────
Step "Summary"
Write-Host "  Release : $fullTitle  ($(if ($Draft) {'draft'} else {'public'}))"
Write-Host "  Commit  : $local  ($branch)"
Write-Host "  Asset   : $ExeName  $sizeMB MB"
Write-Host "  SHA-256 : $hash"
Write-Host "  Notes   : $notesOut"

if ($DryRun) {
    Write-Host "`nDry run complete. Nothing was published." -ForegroundColor Yellow
    exit 0
}
if (-not $Yes) {
    $answer = Read-Host "`nPublish $Tag to https://github.com/$Repo ? (y/N)"
    if ($answer -notmatch '^(y|yes)$') { Write-Host "Cancelled. Nothing was published."; exit 0 }
}

# ── Publish ──────────────────────────────────────────────────────
Step "Publishing"
$ghArgs = @("release", "create", $Tag, $ExePath, $shaOut,
          "--repo", $Repo, "--target", $local,
          "--title", $fullTitle, "--notes-file", $notesOut)
if ($Draft) { $ghArgs += "--draft" }
& gh @ghArgs
if ($LASTEXITCODE -ne 0) { Fail "gh release create failed." }

Invoke-Git fetch --quiet --tags origin | Out-Null
$url = (& gh release view $Tag --repo $Repo --json url --jq .url)
Write-Host "`nReleased: $url" -ForegroundColor Green

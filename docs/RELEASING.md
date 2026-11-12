# Releasing Audio Tag Writer

A release is a GitHub release `vX.Y.Z` titled `vX.Y.Z — <summary>`, with
`audio-tag-writer.exe` and its `.sha256` attached.
`release.ps1` does the checking, testing, building and publishing. You only prepare the version and notes.

## 1. Prepare the version

1. **Bump the version** in `src/audio_tag_writer/constants.py`: `APP_VERSION` and `APP_TIMESTAMP` (Central Time).
   Also update the header comment in `src/main.py` and the version comment in `audio-tag-writer.spec`.
2. **CHANGELOG.md**: add the entry. `release.ps1` refuses to run without it.
   ```
   ## [X.Y.Z] - Ddd DD Mon YYYY HH:MM CDT
   ```
3. **README.md**: point the "Latest release" line at the new tag (`releases/tag/vX.Y.Z`).
   The script warns if you forget.
4. *(Optional)* **Hand-written notes**: create `notes/release/vX.Y.Z.md`.
   Without it, the release notes are the CHANGELOG section for X.Y.Z.
5. **Commit and push** everything. The script requires HEAD to equal `origin/<branch>` and no
   uncommitted changes to tracked files (untracked files, such as screenshots in `notes/`, are ignored).

## 2. Rehearse

```powershell
.\release.ps1 -Title "Fix EXE startup crash" -DryRun
```

This runs every check, the test suite and the full PyInstaller build. It writes
`build\release_notes_vX.Y.Z.md` but publishes nothing. Read the notes file.

## 3. Publish

```powershell
.\release.ps1 -Title "Fix EXE startup crash"          # shows a summary, asks y/N before publishing
.\release.ps1 -Title "Fix EXE startup crash" -Draft   # create as a draft; press Publish on GitHub later
```

Without `-Title` the script asks for one.

Other options:

| Option | Effect |
|---|---|
| `-Yes` | Skip the y/N confirmation (`-Title` is then required) |
| `-SkipBuild` | Reuse the existing `dist\audio-tag-writer.exe`. It must report the same version and be newer than the last commit |
| `-NotesFile path.md` | Use this file for the notes instead of `notes/release/` or the CHANGELOG |
| `-SkipCI` | **Emergency only.** Publish even if CI for the commit isn't green. Prints a warning |

## What the script checks (it stops on any failure)

- `gh` is installed and logged in; the `venv` exists
- No uncommitted changes to tracked files, and HEAD equals `origin/<branch>`
- Tag `vX.Y.Z` doesn't exist locally or on GitHub
- CHANGELOG.md has the `[X.Y.Z]` header
- **CI is green for this exact commit.** The GitHub Actions run of `ci.yml` (Python 3.11 and 3.12) must
  have succeeded. If it's still running, the script waits for it. Right after a push it retries for up
  to a minute until the run appears. If the run failed, it stops and prints the run's link.
- The local test suite passes (on this machine it uses the HSTL test MP3 when present)
- The PyInstaller build succeeds and the **EXE self-test** passes. `build_exe.ps1` runs
  `audio-tag-writer.exe --self-test build\selftest.json`. It checks that every runtime-imported
  module loads from inside the EXE, Mutagen round-trips an ID3 tag, README/CHANGELOG are bundled
  and the main window builds. A crash at startup is caught by a 120-second timeout.
- The EXE's ProductVersion equals `APP_VERSION`

The notes get a Download section (size, SHA-256) and a **Full Changelog** compare link to the
previous release. The tag is created on GitHub at the exact commit that was checked and built (`--target <sha>`).

## Fixing a release

- **Notes or title wrong:** `gh release edit vX.Y.Z --repo juren53/audio-tag-writer --notes-file new.md --title "..."`
- **Bad EXE:** don't replace assets on a published release. Release a point release `vX.Y.Za`.
- **Undo a release published by mistake:** `gh release delete vX.Y.Z --repo juren53/audio-tag-writer --cleanup-tag`

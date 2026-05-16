# Bug: "Could not create temporary directory" — File Manager right-click launch

**Date:** 2026-05-16
**Version:** v0.7.7
**Symptom:** Right-clicking an MP3 in File Manager → Open with → ATW fails immediately with
"Could not create temporary directory". Launching the EXE directly works fine.

---

## Root Cause

`audio-tag-writer.spec` contains:

```python
runtime_tmpdir='.',   # extract next to exe; no temp-dir cleanup → no AV-lock error on exit
```

PyInstaller's one-file bootloader must unpack all bundled DLLs and modules into a
`_MEIxxxxxx` folder before the Python app can start. `runtime_tmpdir='.'` tells it to
create that folder in the **current working directory (CWD)** at launch time.

| Launch method | CWD at launch | Result |
|---|---|---|
| Double-click EXE in Explorer | EXE's own directory (`C:\Users\juren\bin`) | Writable — works |
| Taskbar / desktop shortcut | EXE's own directory | Writable — works |
| File Manager "Open with" ATW | **Audio file's parent directory** | May be read-only — **fails** |

Windows sets CWD to the selected file's parent folder when invoking an "Open with" handler.
If that folder is read-only, a network share, a protected system path, or a USB drive,
PyInstaller cannot create `_MEIxxxxxx` there and aborts with the error before any Python
code runs.

---

## Why `runtime_tmpdir='.'` Was Introduced (v0.7.7)

The default (`None`) uses `%TEMP%`. On the development machine, Windows Defender held a
lock on extracted DLLs in `%TEMP%` at process shutdown, causing a
"Failed to remove temporary directory" error dialog on every exit.
Setting `runtime_tmpdir='.'` moved extraction next to the EXE; PyInstaller does not
attempt cleanup there, so the error dialog disappeared.

---

## Options

### Option A — Revert to `runtime_tmpdir=None` (use `%TEMP%`)

**Change in spec:**
```python
runtime_tmpdir=None,   # default: extract to %TEMP%
```

- `%TEMP%` is always writable for the current user — fixes the File Manager launch failure
- The v0.7.7 AV exit dialog may return (Windows Defender locking DLLs on exit)
- That dialog is cosmetic and dismissible; the app itself exits cleanly
- Simplest change; requires only a spec edit and rebuild

---

### Option B — Wrapper script (`launch-atw.bat` or `.ps1`) in `C:\Users\juren\bin`

Create a small launcher next to the EXE that changes to its own directory before
invoking the real EXE:

```bat
@echo off
cd /d "%~dp0"
start "" "%~dp0audio-tag-writer.exe" %*
```

- Re-register "Open with" to point to the wrapper instead of the EXE
- `%~dp0` always resolves to the batch file's own directory, so `runtime_tmpdir='.'`
  resolves to `C:\Users\juren\bin` regardless of what File Manager sets as CWD
- Keeps the v0.7.7 AV fix in place
- Requires re-doing the "Open with" registration to point to the `.bat`, not the `.exe`
- Windows may not allow registering a `.bat` as a handler; a compiled launcher or
  PowerShell wrapper with `-windowstyle hidden` would avoid the CMD flash

---

### Option C — Switch to `--onedir` (folder-based) build

Change `exe = EXE(...)` to a `COLLECT()`-based spec (`--onedir` mode).

- No extraction needed at launch — all files live beside the EXE permanently
- Eliminates both the AV issue and the CWD issue entirely
- Distribution changes: instead of a single `audio-tag-writer.exe` you distribute a
  folder (`dist\audio-tag-writer\`) containing the EXE and its dependencies
- The "Open with" registration still points to the EXE inside the folder — works fine
- Requires updating `.gitignore`, the build script, and any distribution steps

---

## Recommendation

**Short-term:** Option A — revert `runtime_tmpdir` to `None` and rebuild.
The AV exit dialog (if it returns) is a cosmetic nuisance; a hard launch failure from
File Manager is the worse regression to live with.

**Long-term:** Option C — `--onedir` eliminates both problems permanently and is the
more conventional PyInstaller deployment for a Windows desktop app.

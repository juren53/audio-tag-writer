# Audio Tag Writer Changelog

All notable changes to the Audio Tag Writer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Tue 21 Apr 2026 02:00:00 PM CDT

### Added
- **venv launcher (`run.ps1`)** — PowerShell script following the project-standard pattern
  used across all `~\Projects` apps; auto-creates the virtual environment, validates that
  the base Python executable still exists (recreates if broken), installs/updates
  dependencies from `requirements.txt` only when the file is newer than the
  `venv\.deps_installed` marker, then launches `src\main.py`

### Fixed
- **PyQt6 version pin** — removed `PyQt6==6.4.2` / `PyQt6-sip==13.4.1` hard pins from
  `requirements.txt`; the 6.4.2 bindings are incompatible with the current `PyQt6-Qt6`
  runtime (6.11.0), causing a DLL load failure on import. Changed to `PyQt6>=6.4.2` so
  pip installs a consistent bindings + runtime pair. Verified: mutagen 1.47.0 and
  PyQt6/Qt 6.11.0 import cleanly; GUI shell launches successfully via `.\run.ps1`
- **pip self-upgrade error** — `run.ps1` was calling `pip install --upgrade pip` which
  fails because pip cannot replace itself while running; changed to
  `python -m pip install --upgrade pip`

### Technical
- venv located at `venv\` (excluded from git via `.gitignore`)
- Dependency install marker at `venv\.deps_installed`; touch `requirements.txt` to force
  a reinstall on next `.\run.ps1` run

---

## [0.0.1] - Tue 21 Apr 2026 01:00:00 PM CDT

### Added
- **Project scaffold** — full directory structure created under `src/audio_tag_writer/`
  - `src/main.py` — application entry point; bare `MainWindow(QMainWindow)` shell launches with
    title bar, placeholder label, and status bar showing version and Mutagen ready message
  - `src/audio_tag_writer/constants.py` — `APP_NAME`, `APP_VERSION`, `APP_TIMESTAMP`,
    `APP_ORGANIZATION`, `APP_USER_MODEL_ID`, `GITHUB_REPO`, `AUDIO_EXTENSIONS`,
    and `DEFAULT_MODES` with full field specs for all three built-in modes
  - `src/audio_tag_writer/config.py` — `Config` singleton (JSON persistence to
    `~/.audio_tag_writer_config.json`) + `SingleInstanceChecker` (cross-platform file locking);
    mode helpers: `get_active_mode()`, `set_active_mode()`, `get_mode_fields()`,
    `reset_mode_to_default()`; new built-in modes from `DEFAULT_MODES` are merged in
    automatically on first run or when absent from saved config
  - `src/audio_tag_writer/platform.py` — Windows `AppUserModelID` registration +
    taskbar icon integration (`ICON_atw.ico`/`.png`)
  - `src/audio_tag_writer/mutagen_utils.py` — `AudioFileError` exception;
    `open_audio(path)` opens any supported audio file via `mutagen.File()`;
    `safe_get_text(tags, frame_id)` handles standard frames, `COMM`, and `TXXX:desc` keys;
    `check_mutagen_available()` pre-flight with install hint
  - `src/audio_tag_writer/file_utils.py` — `get_audio_files(directory)` returns a
    case-insensitive sorted list of `.mp3`, `.wav`, `.ogg`, `.flac` files
  - `src/audio_tag_writer/widgets/__init__.py` — empty stub; populated in Phase 2
  - `requirements.txt` — `mutagen>=1.47.0`, `PyQt6==6.4.2`, `PyQt6-sip==13.4.1`,
    `pyqt-app-info`
  - `.gitignore` — excludes `__pycache__/`, bytecode, build artifacts, and `.exe`
  - `assets/` directory scaffolded (`.gitkeep`); icon files added in Phase 5
  - `tests/__init__.py` stub

- **Mode system foundation** — `DEFAULT_MODES` in `constants.py` defines the full field
  specifications (label, frame_id, widget type, max_chars) for three built-in modes:
  Archival Recording (10 fields), Music (10 fields), Scientific (10 fields).
  `Config` seeds and merges these on load so user customisations are preserved while
  new built-in modes appear automatically after upgrades.

- **Single-instance guard** — `SingleInstanceChecker` prevents multiple simultaneous
  instances using `msvcrt` locking on Windows and `fcntl` on Linux/macOS.

- **Mutagen pre-flight check** — `main()` calls `check_mutagen_available()` at startup;
  a modal error dialog with an install hint is shown if `mutagen` is missing.

### Technical
- Package: `src/audio_tag_writer/` with strict dependency ordering:
  `constants` → `config` → `mutagen_utils` / `file_utils` / `platform` → `main`
- Mixin files (`menu`, `navigation`, `file_ops`, `theme_mixin`, `help`, `updates`,
  `window`) are created in Phases 2–5; stubs are not pre-created to keep the scaffold clean
- `Config.load_config()` merges saved `modes` dict over `DEFAULT_MODES` so adding a
  new built-in mode in a future version does not require a config reset

---

## Version History Summary

- **v0.1.0** - Tue 21 Apr 2026: venv launcher, PyQt6 version fix, pip self-upgrade fix;
  GUI shell confirmed launching via `.\run.ps1`
- **v0.0.1** - Tue 21 Apr 2026: Initial scaffold — project structure, core utilities,
  Mutagen pre-flight, Mode system foundation, working shell window

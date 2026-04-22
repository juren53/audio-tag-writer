# Audio Tag Writer Changelog

All notable changes to the Audio Tag Writer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - Wed 22 Apr 2026

### Added
- **`run.sh`** — Bash launcher for Linux/macOS mirroring `run.ps1`; auto-creates the
  virtual environment, validates that the base Python executable still exists (recreates
  if broken), installs/updates dependencies from `requirements.txt` only when the file
  is newer than the `venv/.deps_installed` marker, then launches `src/main.py`; passes
  through any extra arguments via `"$@"`

---

## [0.4.0] - Tue 21 Apr 2026 09:25:00 PM CDT

### Added
- **Phase 4 — Navigation + Full Menu**

- **`navigation.py`** — `NavigationMixin` providing: `on_open()` (file dialog),
  `on_open_directory()` (directory dialog → first audio file), `on_previous()` /
  `on_next()` with directory looping, `load_file()` (replaces Phase 3 inline version —
  now scans directory, tracks `current_file_index`, shows `filename · format · size [N/M]`
  in status bar), `on_refresh()` (reload from disk), `on_clear()` (clear all fields),
  `on_copy_path()` (FQFN to clipboard), `update_recent_menu()` /
  `update_recent_directories_menu()` / `open_directory()` with clear-list actions

- **`window.py`** — `WindowMixin` providing: `keyPressEvent()` (← → navigate,
  F5 refresh), `save_window_geometry()` / `restore_window_geometry()` (persisted via
  `config.window_geometry`; clamped to screen bounds), `closeEvent()` (saves geometry
  + config, prevents double-close via `_is_closing` flag)

- **`menu.py`** — `MenuMixin` providing `create_menu_bar()` and `create_toolbar()`:
  - **File**: Open, Open Directory, ─, Recent Files ▶, Recent Directories ▶, ─,
    Save Metadata (Ctrl+S), ─, Export/Import JSON, ─, Quit (Ctrl+Q)
  - **Edit**: Clear Fields (Ctrl+L), ─, Copy Path to Clipboard (Ctrl+Shift+C)
  - **View**: Refresh (F5), ─, View All Tags (Ctrl+T)
  - **Help**: About, Changelog
  - **Toolbar**: ◀ Prev | Open | Next ▶ | Save | Export JSON | Import JSON | View Tags
    | [filename label]

- **`main.py`** — `MainWindow` now inherits
  `NavigationMixin, FileOpsMixin, MenuMixin, WindowMixin, QMainWindow`; inline menu,
  toolbar, `load_file`, and key-handler code removed in favour of the mixins; window
  geometry restored on startup; About and Changelog dialogs stubbed (Phase 5 wires
  `help.py`)

### Technical
- Status bar left side now shows `filename · format · file_size [N/M]` on load
- `set_status()` also updates the toolbar filename label
- Config `directory_audio_files` populated on every `load_file()` call; `current_file_index`
  set from the file's position in the sorted list
- `_is_closing` guard prevents duplicate `closeEvent` handling

---

## [0.3.1] - Tue 21 Apr 2026 09:25:00 PM CDT

### Added
- **Play button** — `▶  Play` button added immediately below the album art frame
  in `AudioPanel`; disabled until a file is loaded, then enabled by `display_audio()`;
  uses `QDesktopServices.openUrl(QUrl.fromLocalFile())` to hand off to the OS-designated
  audio player (Windows Media Player, VLC, Groove Music, etc.); shows a warning dialog
  if the OS reports the open failed

### Fixed
- **Date Recorded not saving** — `TRDA` (ID3v2.3 Recording Dates frame) is silently
  dropped by mutagen's default `update_to_v24()` translation on file load (no v2.4
  equivalent). Changed frame mapping to `TXXX:DateRecorded` in Archival Recording and
  Scientific modes; TXXX frames are version-agnostic and survive all translation passes
- **Speakers not saving** — `IPLS` (v2.3 Involved People List) is converted to `TIPL`
  (v2.4) by mutagen's default load translation. Data was written correctly to disk but
  could not be read back. Fixed `_read_frame` to check both `IPLS` and `TIPL` so the
  value is found regardless of which form mutagen presents after load
- **Location frame skipped** — saved config (from Phase 2) retained `frame_id: TLOC`
  for the Location field; `load_config()` was merging saved modes over defaults so the
  stale spec persisted. Fixed by always overwriting built-in modes from `DEFAULT_MODES`
  on load (user-added custom modes are still preserved)
- **WAV files saving to ID3v2.4** — WAV save path was calling `audio.save()` without
  `v2_version=3`, defaulting to ID3v2.4 and silently dropping v2.3-only frames. Changed
  to `update_to_v23()` + `save(v2_version=3)` for both MP3 and WAV

---

## [0.3.0] - Tue 21 Apr 2026 04:00:00 PM CDT

### Added
- **Phase 3 — Metadata write, JSON export/import, View All Tags**

- **`metadata.py`** — `MetadataManager.save_to_file(path)` now fully implemented:
  builds Mutagen frame objects for every field in the active mode; handles standard
  text frames (`TIT2`, `TALB`, `TPE1`, etc.), `COMM` (lang=eng), `TXXX:desc` user-defined
  frames, and `IPLS` (parses "role: name; …" display string back to `[[role, name], …]`
  pairs); enforces ID3v2.3 on MP3 (`update_to_v23()` + `save(v2_version=3)`) and plain
  save for WAV; raises `AudioFileError` with a clear message for OGG/FLAC (ID3 write
  not supported for those formats); `add_tags()` called automatically when the file
  has no existing tag header

- **`file_ops.py`** — new `FileOpsMixin` class providing:
  - `on_save()` — calls `update_manager_from_ui()` then `save_to_file()` with full error
    dialog on `AudioFileError` or unexpected exception; updates status bar on success
  - `on_export()` — prompts for JSON path (pre-filled with `<stem>_metadata.json`);
    delegates to `MetadataManager.export_to_json()`
  - `on_import()` — prompts for JSON path; imports via `MetadataManager.import_from_json()`;
    refreshes `MetadataPanel` after import
  - `on_view_all_tags()` — opens `AllTagsDialog`: searchable `QTableWidget` listing every
    raw Mutagen frame (ID + decoded value) for the current file; binary frames (e.g. APIC)
    shown as `<binary data N bytes>`

- **`main.py`** — `MainWindow` now inherits `FileOpsMixin`; File menu extended with
  Save Metadata (Ctrl+S), Export Metadata to JSON, Import Metadata from JSON; new Tools
  menu with View All Tags (Ctrl+T); toolbar extended with Save, Export JSON, Import JSON,
  and View Tags buttons

- **`widgets/metadata_panel.py`** — `_on_write()` now calls `save_to_file()` with proper
  `try/except AudioFileError` handling and success status message via `_set_main_status()`

### Fixed
- **`TLOC` frame** — `TLOC` is not a real ID3v2 frame (not in mutagen's frame registry).
  Changed Location field in Archival Recording and Scientific modes from `frame_id: TLOC`
  to `frame_id: TXXX:Location` (the correct TXXX user-defined text approach)

---

## [0.2.0] - Tue 21 Apr 2026 03:00:00 PM CDT

### Added
- **Phase 2 — Audio info + metadata read**

- **`audio_utils.py`** — `get_audio_info(path)` returns a dict of human-readable
  audio stream properties (duration, bitrate, sample rate, channels, format, file size,
  modified date) sourced from `mutagen.File().info` and `os.stat`

- **`metadata.py`** — `MetadataManager` with mode-aware field mappings built dynamically
  from the active mode spec in `config`; `load_from_file(path)` reads ID3 frames via
  Mutagen handling standard frames, `COMM`, `TXXX:desc`, and `IPLS` (flattened to
  "role: name; …" string); `_sanitize_value()` ported from tag-writer; `export_to_json()`
  and `import_from_json()` stubs; `save_to_file()` stubbed for Phase 3

- **`widgets/audio_panel.py`** — `AudioPanel` right-column panel mirroring tag-writer's
  `ImageViewer`; APIC frame extracted via `tags.getall('APIC')` → `QPixmap.loadFromData()`,
  scaled with `KeepAspectRatio`; music-note `♪` placeholder when no art is present; green/grey
  status indicator dot; scrollable HTML file info table (duration, bitrate, sample rate,
  channels, format, file size, modified date)

- **`widgets/metadata_panel.py`** — `MetadataPanel` form fields built dynamically from the
  active mode's field spec (`QLineEdit` for `"widget":"line"`, `QTextEdit` for `"widget":"text"`);
  character counter with orange/red warning thresholds for text fields; arrow-key event filter
  (prevents Up/Down from propagating to main window); `update_from_manager()` and
  `update_manager_from_ui()`; Write Metadata button (shows Phase 3 notice until implemented)

- **Splitter UI** — `main.py` rebuilt around `QSplitter(Horizontal)` with `MetadataPanel`
  (left, 660px) and `AudioPanel` (right, 440px); `load_file(path)` wires both panels;
  File › Open menu item and toolbar Open button (Ctrl+O); arrow-key stubs for Phase 4
  navigation; restores last-used file on startup

### Technical
- `widgets/__init__.py` now exports `AudioPanel` and `MetadataPanel`
- `MetadataManager._rebuild_from_mode()` called on init and on mode switch; new built-in
  modes merge automatically without a config reset
- IPLS frame special-cased in `MetadataManager._read_frame()` — `frame.people` list
  flattened to a display string; all other frames delegated to `safe_get_text()`

---

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

- **v0.4.1** - Wed 22 Apr 2026: Bash launcher `run.sh` for Linux/macOS (mirrors `run.ps1`)
- **v0.4.0** - Tue 21 Apr 2026: Phase 4 — NavigationMixin, WindowMixin, MenuMixin; ←→ navigation,
  directory scanning, Recent Files/Dirs menus, geometry save/restore
- **v0.3.1** - Tue 21 Apr 2026: Play button; fixes for Date Recorded (TRDA→TXXX), Speakers
  (IPLS/TIPL), Location (TLOC stale config), WAV ID3v2.4 save
- **v0.3.0** - Tue 21 Apr 2026: Phase 3 — metadata write (`save_to_file`), JSON export/import,
  View All Tags dialog, Save/Export/Import toolbar + menu actions, TLOC→TXXX:Location fix
- **v0.2.0** - Tue 21 Apr 2026: Phase 2 — audio info panel, metadata read, splitter UI,
  AudioPanel with album art (APIC), MetadataPanel with dynamic mode-driven form fields
- **v0.1.0** - Tue 21 Apr 2026: venv launcher, PyQt6 version fix, pip self-upgrade fix;
  GUI shell confirmed launching via `.\run.ps1`
- **v0.0.1** - Tue 21 Apr 2026: Initial scaffold — project structure, core utilities,
  Mutagen pre-flight, Mode system foundation, working shell window

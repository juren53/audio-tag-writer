# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Audio Tag Writer is a PyQt6 desktop application for viewing and editing ID3 metadata tags in audio files (MP3, WAV, OGG, FLAC). It uses the Mutagen library for all metadata operations. Current version: v0.7.12.

A key feature is **three operational modes** — Archival Recording, Music, and Scientific — each showing a different set of ID3 fields tailored to that use case. The active mode is auto-detected from the file's ID3 frames or can be set manually.

## Development Commands

### Running the Application
```powershell
# Preferred — handles venv creation, dep install, and launch automatically
.\run.ps1

# Direct (with venv active)
python src/main.py

# Open a specific file
python src/main.py path/to/audio.mp3
```

### Building Executable
```powershell
.\build_exe.ps1
# Output: dist/audio-tag-writer.exe
```

### Running Tests
```bash
pytest tests/
```

### Dependencies
```bash
pip install -r requirements.txt
# mutagen, PyQt6, pyqt-app-info (from GitHub)
```

## Critical Project Rules

### Timezone Convention
**ALL timestamps MUST use Central Time USA (CST/CDT), NEVER UTC.**

This applies to:
- Changelog entries
- Version labels (APP_TIMESTAMP in `src/audio_tag_writer/constants.py`)
- Documentation timestamps

### Version Numbering
- Production releases: `v0.X.Y` (e.g., v0.7.0)
- Point releases/patches: `v0.X.Ya`, `v0.X.Yb` (e.g., v0.7.12a)
- Update version in: `src/audio_tag_writer/constants.py` (APP_VERSION, APP_TIMESTAMP), `src/main.py` (header comment), `audio-tag-writer.spec` (version comment), `README.md`, `CHANGELOG.md`

## Architecture

### Modular Package Structure (v0.7.x)

The application uses a mixin-based architecture under `src/audio_tag_writer/`. The entry point `src/main.py` imports `main()` directly from the package.

```python
# MainWindow composition in src/main.py
class MainWindow(MenuMixin, FileOpsMixin, NavigationMixin,
                 WindowMixin, ThemeMixin, HelpMixin, QMainWindow):
```

### Module Dependency Flow
constants → config → mutagen_utils → metadata → audio_utils/file_utils → widgets/dialogs → mixins → main

**Do not introduce circular imports.**

### Key Modules

| Module | Purpose |
|--------|---------|
| `constants.py` | APP_NAME, APP_VERSION, APP_TIMESTAMP, AUDIO_EXTENSIONS, mode definitions (DEFAULT_MODES, DEFAULT_DETECT_FRAMES) |
| `config.py` | Config singleton, persisted via QSettings |
| `mutagen_utils.py` | Low-level mutagen wrappers — `open_audio()`, `safe_get_text()`, `AudioFileError` |
| `metadata.py` | MetadataManager — ID3 read/write using mutagen |
| `audio_utils.py` | Audio file utilities |
| `file_utils.py` | File scanning and directory helpers |
| `file_ops.py` | FileOpsMixin — save, export, import metadata |
| `navigation.py` | NavigationMixin — open, prev/next, load_file, recent files/dirs |
| `menu.py` | MenuMixin — menu bar and toolbar |
| `window.py` | WindowMixin — geometry save/restore, closeEvent |
| `help.py` | HelpMixin — About dialog, issue log |
| `theme.py` | ThemeManager integration |
| `theme_mixin.py` | ThemeMixin — apply_theme, dark mode |
| `platform.py` | Windows AppUserModelID, taskbar icon stub |
| `widgets/metadata_panel.py` | MetadataPanel — dynamic field form driven by active mode |
| `widgets/audio_panel.py` | AudioPanel — file info and waveform display |
| `widgets/manage_modes_dialog.py` | Dialog for customizing mode field sets |
| `widgets/theme_dialog.py` | Theme selection dialog |

### Three-Mode System

Modes determine which ID3 fields appear in the metadata panel. Defined in `constants.py`:

| Mode | Discriminating Frame | Typical Use |
|------|---------------------|-------------|
| **Scientific** | `TXXX:Equipment` | Field recordings with researcher/equipment/species fields |
| **Music** | `TRCK` (Track Number) | Standard music tags — title, artist, album, etc. |
| **Archival Recording** | *(fallback/default)* | HSTL-style archival audio with accession, speakers, date |

Auto-detection: the first mode whose discriminating frame is non-empty and present in the file wins. `TRCK` was chosen over `TPE1` for Music because HSTL archival files carry `TPE1 = "Harry S. Truman Library"`, which caused false Music matches.

### Shared Modules (external)
- **Icon Manager Module** (`~/Projects/Icon_Manager_Module`) — icon loading, Windows taskbar AUMID
- **ThemeManager** (`~/Projects/ThemeManager`) — built-in themes
- **pyqt-app-info** (`~/Projects/pyqt-app-info`) — About dialog

## Directory Structure

```
audio-tag-writer/
├── src/
│   ├── main.py                        # MainWindow + main() entry point
│   └── audio_tag_writer/              # Package
│       ├── constants.py               # Version, modes, AUDIO_EXTENSIONS
│       ├── config.py                  # Config singleton (QSettings)
│       ├── mutagen_utils.py           # Low-level mutagen helpers
│       ├── metadata.py                # MetadataManager (ID3 read/write)
│       ├── audio_utils.py             # Audio file utilities
│       ├── file_utils.py              # File scanning helpers
│       ├── file_ops.py                # FileOpsMixin
│       ├── navigation.py              # NavigationMixin
│       ├── menu.py                    # MenuMixin
│       ├── window.py                  # WindowMixin
│       ├── help.py                    # HelpMixin
│       ├── theme.py                   # ThemeManager integration
│       ├── theme_mixin.py             # ThemeMixin
│       ├── platform.py                # Windows taskbar stub
│       └── widgets/                   # MetadataPanel, AudioPanel, dialogs
├── tests/                             # pytest test suite
├── assets/                            # Icons, desktop file
├── resources/icons/                   # IMM-managed icon set
├── tools/                             # Build utilities
├── audio-tag-writer.spec              # PyInstaller build spec
├── build_exe.ps1                      # Full build script
├── generate_version_info.py           # Generates version_info.txt for EXE properties
├── requirements.txt                   # mutagen, PyQt6, pyqt-app-info
├── run.ps1                            # Dev launcher (manages venv automatically)
├── run.sh                             # Dev launcher (Linux/macOS)
├── CHANGELOG.md
└── README.md
```

## Common Issues

**venv has broken Python reference**: Delete the `venv/` directory and re-run `.\run.ps1` to recreate it.

**`pyqt-app-info` not found**: It installs from GitHub (`pip install -r requirements.txt`). Requires network access at install time.

**Mode auto-detects incorrectly**: Check which ID3 frames are present in the file. The detection order in `DEFAULT_DETECT_FRAMES` (constants.py) determines priority. Scientific wins over Music wins over Archival.

# Audio Tag Writer — System Architecture Document

**Product:** Audio Tag Writer (ATW)  
**Organization:** SynchroSoft  
**Version:** 0.7.6  
**Date:** 2026-04-25  

---

## 1. Purpose

ATW is a desktop metadata editor for audio files, optimized for the HSTL (Harry S. Truman Library) archival workflow. Its primary function is to read and write the complete HSTL ID3v2.3 metadata profile — the same frame set produced by the institution's FFmpeg tagging pipeline (`audio-tags-12d.py`) — using the Python `mutagen` library directly, without invoking external tools.

---

## 2. High-Level Architecture

ATW is a single-process PyQt6 desktop application built on a mixin composition pattern. The `MainWindow` class inherits from a chain of mixins, each owning a distinct concern:

```
MainWindow
  ├── NavigationMixin    file open, prev/next, load_file, recent menus
  ├── FileOpsMixin       save, export/import JSON, rename, view all tags, mode switch
  ├── MenuMixin          menu bar, toolbar
  ├── ThemeMixin         dark mode, theme selection, zoom
  ├── HelpMixin          README, CHANGELOG, about dialog
  └── WindowMixin        keyboard nav, window geometry, close handler
        └── QMainWindow  (Qt base class)
```

The central UI is a horizontal `QSplitter`:

```
┌──────────────────────────────────┬──────────────────┐
│  MetadataPanel (left)            │  AudioPanel       │
│  Dynamic ID3 form fields         │  Album art        │
│  (rebuilt on mode change)        │  Technical info   │
└──────────────────────────────────┴──────────────────┘
```

---

## 3. Module Inventory

| Module | Responsibility |
|--------|---------------|
| `src/main.py` | Application entry point; `MainWindow` class; single-instance guard |
| `constants.py` | `APP_VERSION`, `DEFAULT_MODES` spec, `DEFAULT_DETECT_FRAMES`, `AUDIO_EXTENSIONS` |
| `config.py` | `Config` singleton — persists to `~/.audio_tag_writer_config.json`; `SingleInstanceChecker` |
| `metadata.py` | `MetadataManager` — ID3 read/write, JSON export/import, field spec interpretation |
| `mutagen_utils.py` | `open_audio`, `safe_get_text`, `detect_mode`, `AudioFileError` |
| `audio_utils.py` | `get_audio_info` — stream properties (duration, bitrate, channels, …) via mutagen |
| `file_utils.py` | `get_audio_files` — sorted directory scan for audio files; `backup_file` |
| `navigation.py` | `NavigationMixin` — file navigation, `load_file` orchestrator |
| `file_ops.py` | `FileOpsMixin` — save, export/import, rename, mode switch, `AllTagsDialog` |
| `menu.py` | `MenuMixin` — full menu bar and toolbar |
| `window.py` | `WindowMixin` — keyboard events, geometry persistence, close handler |
| `platform.py` | Windows taskbar icon / App User Model ID integration |
| `theme.py` | `ThemeManager` — CSS theme library |
| `theme_mixin.py` | `ThemeMixin` — dark mode, theme picker, UI zoom |
| `help.py` | `HelpMixin` — README, CHANGELOG, about, issue log |
| `widgets/metadata_panel.py` | `MetadataPanel` — dynamically builds ID3 form from mode spec |
| `widgets/audio_panel.py` | `AudioPanel` — APIC album art display + technical stream info table |
| `widgets/manage_modes_dialog.py` | `ManageModesDialog` — add/rename/reorder/delete modes at runtime |

---

## 4. Data Flow

### 4.1 File Load

```
on_open()  ──►  load_file(path)
                  │
                  ├── open_audio(path)          [mutagen_utils]
                  │     └── mutagen.File(path)
                  │
                  ├── _auto_detect_mode(tags)   [navigation]
                  │     └── detect_mode(tags, detect_frames, default)
                  │
                  ├── get_audio_info(path)       [audio_utils]
                  │
                  ├── metadata_manager.load_from_file(path)
                  │     └── _read_frame() per field spec
                  │           ├── safe_get_text(tags, frame_id)
                  │           └── alias fallback loop
                  │
                  ├── metadata_panel.update_from_manager()
                  └── audio_panel.display_audio(path, info, tags)
```

### 4.2 File Save

```
on_save()
  │
  ├── metadata_panel.update_manager_from_ui()
  └── metadata_manager.save_to_file(path)
        │
        ├── Per field spec:
        │     ├── hidden fields  →  resolve auto_value (including __app_version__ sentinel)
        │     ├── _write_frame(tags, frame_id, value)
        │     ├── alias fanout:  _write_frame() for each alias
        │     └── date_field:    _write_date_derived(tags, value)
        │
        ├── tags.update_to_v23()
        └── audio.save(v2_version=3)
```

---

## 5. Field Spec Format

Each mode is defined as a list of field spec dicts in `constants.py → DEFAULT_MODES`. `MetadataManager` interprets these specs for both reading and writing.

```python
{
    "label":     str,          # UI label and internal key
    "frame_id":  str,          # Primary ID3 frame (e.g. "TIT2", "TXXX:TLOC")
    "widget":    str,          # "line" | "text" | "hidden"
    "max_chars": int,          # Truncation limit on read (default 2000)
    "aliases":   [str, ...],   # Additional frames written with same value; read fallback
    "date_field": bool,        # Triggers _write_date_derived() derivation on save
    "auto_value": str,         # Value for hidden fields; "__app_version__" is a sentinel
}
```

### widget types

| Value | Behavior |
|-------|----------|
| `"line"` | Single-line `QLineEdit` |
| `"text"` | Multi-line `QTextEdit` |
| `"hidden"` | Not rendered; auto-written on save using `auto_value`; skipped on load |

---

## 6. Archival Recording Mode — Full Frame Map

The Archival Recording mode implements the complete HSTL metadata profile for cross-schema compatibility with iTunes, Windows Media Player, XMP-aware tools, and FFmpeg-tagged archives.

### 6.1 Visible Fields

| UI Label | Primary Frame | Aliases Written on Save | Notes |
|---|---|---|---|
| Title | `TIT2` | | |
| Description | `TIT3` | `COMM`, `TXXX:COMM`, `TXXX:ISBJ`, `TXXX:dc:description`, `TXXX:xmpDM:logComment`, `TXXX:©cmt` | Read fallback: tries each alias if TIT3 absent |
| Accession Number | `TALB` | `TXXX:IPRD` | |
| Speakers | `IPLS` | `TXXX:IPLS` | IPLS stored as role/name pairs; display: "role: name; …" |
| Date Recorded | `TRDA` | `TYER`, `TORY`, `TDAT` (DDMM), `TXXX:ICRD` | ISO date input; derivation via `_write_date_derived()` |
| Restrictions | `TCOP` | | |
| Location | `TXXX:TLOC` | | |
| Production/Copyright | `TPUB` | `TXXX:©pub`, `TXXX:dc:publisher` | |
| Original Filename | `TOFN` | | |
| Collection | `TXXX:grouping` | | |
| Source URL | `TXXX:WOAS` | | |
| NAC URL | `TXXX:WXXX` | | |
| Institution ID | `TXXX:ISRC` | | |

### 6.2 Hidden Auto-Written Fields

| UI Label | Frame | Auto Value |
|---|---|---|
| Artist | `TPE1` | `"Harry S. Truman Library"` |
| Genre | `TCON` | `"speech"` |
| Tagging Software | `TEXT` | `"Audio Tag Writer vX.X.X"` |

### 6.3 Date Derivation (`_write_date_derived`)

Input: ISO date string (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`)

| Frame | Content | ID3 Version |
|---|---|---|
| `TRDA` | Full date string (primary) | v2.3 |
| `TYER` | Year (`YYYY`) | v2.3 |
| `TORY` | Original release year (same as TYER) | v2.3 |
| `TDAT` | Day+Month as `DDMM` | v2.3 |
| `TXXX:ICRD` | Full ISO date string | v2.3 |

### 6.4 ID3v2.3 ↔ v2.4 Conversion

Mutagen loads all files normalizing to ID3v2.4. These v2.3 frames are silently remapped on load:

| v2.3 Frame | v2.4 Equivalent | `_V23_TO_V24` fallback |
|---|---|---|
| `TRDA` | `TDRC` | ✓ |
| `TORY` | `TDOR` | ✓ |
| `IPLS` | `TIPL` | Handled in `_read_frame` |

On save, `tags.update_to_v23()` is called before `audio.save(v2_version=3)` to write a proper ID3v2.3 file.

---

## 7. Mode Auto-Detection

Auto-detection runs on every file load when `config.auto_detect_mode` is `True`. The detection table is ordered; the first mode whose discriminator frame is non-empty in the file wins.

| Mode | Discriminator Frame | Rationale |
|---|---|---|
| Scientific | `TXXX:Equipment` | Unique to scientific recordings |
| Music | `TRCK` | Track numbers appear only on music; reliable (TPE1 was unreliable because archival files carry a static TPE1 value) |
| Archival Recording | *(none — fallback)* | Default when no discriminator matches |

Configuration is stored in `config.mode_detect_frames` (ordered dict) and `config.mode_detect_default`. Users can customize detection rules via Tools > Manage Modes.

---

## 8. Configuration Persistence

The config file is `~/.audio_tag_writer_config.json`. Key fields:

| Key | Type | Description |
|---|---|---|
| `active_mode` | str | Currently selected mode name |
| `modes` | dict | Full mode spec (DEFAULT_MODES merged with user edits) |
| `mode_detect_frames` | dict | Ordered detection rules |
| `mode_detect_default` | str | Fallback mode name |
| `auto_detect_mode` | bool | Auto-detect enabled on file load |
| `selected_file` | str | Last open file (restored on startup) |
| `last_directory` | str | Last browsed directory |
| `recent_files` | list[str] | Up to 10 recent files |
| `recent_directories` | list[str] | Up to 10 recent directories |
| `window_geometry` | [x, y, w, h] | Saved window position/size |
| `window_maximized` | bool | Saved maximized state |
| `current_theme` | str | Active theme name |
| `dark_mode` | bool | Dark mode toggle |
| `ui_zoom_factor` | float | UI scale factor (default 1.0) |

On load, `Config.load_config()` merges saved modes with `DEFAULT_MODES` — built-in mode field specs always overwrite stale entries from the saved config, while user-added custom modes are preserved.

---

## 9. Build System

### 9.1 Development launcher

```
.\run.ps1         # Windows PowerShell — creates venv, installs deps, runs src/main.py
./run.sh          # bash — same for Linux/macOS
```

### 9.2 Executable build

```
.\build_exe.ps1
```

Steps performed by `build_exe.ps1`:
1. Verify venv exists
2. Install PyInstaller into venv
3. Run `generate_version_info.py` → writes `version_info.txt`
4. Remove previous `build/` and `dist/`
5. Run `pyinstaller audio-tag-writer.spec --noconfirm`
6. Output: `dist/audio-tag-writer.exe`

### 9.3 Windows EXE Properties/Details tab

`generate_version_info.py` reads `APP_VERSION` from `constants.py` and writes `version_info.txt` in PyInstaller VSVersionInfo format. The `.spec` file references this file via `version='version_info.txt'` in the `EXE()` block, embedding version metadata visible in Windows Explorer Properties > Details:

| Property | Value |
|---|---|
| Product name | Audio Tag Writer |
| File description | Audio Tag Writer |
| Company | SynchroSoft |
| Copyright | Copyright (c) 2026 SynchroSoft |
| Product / File version | *current APP_VERSION* |

---

## 10. Testing

Automated tests live in `tests/` and are run with pytest:

```
venv\Scripts\python.exe -m pytest tests/ -q
```

| Module | Coverage area |
|---|---|
| `test_audio_utils.py` | `get_audio_info` — file stats, stream properties, real MP3 |
| `test_config.py` | Config singleton, mode merge, save/load roundtrip |
| `test_file_utils.py` | Directory scan, extension filtering, sort order |
| `test_metadata.py` | `MetadataManager` — sanitize, read/write frames, JSON roundtrip |
| `test_mutagen_utils.py` | `open_audio`, `safe_get_text`, `detect_mode`, COMM/TXXX handling |

CI runs via `.github/workflows/ci.yml` on push to master against Python 3.11 and 3.12 (ubuntu-latest).

Acceptance test reports are saved to `reports/` as `REPORT_ATW-acceptance-test-YYYY-MM-DD-HHMM.txt`.

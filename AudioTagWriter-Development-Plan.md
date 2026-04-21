# audio-tag-writer — Development Plan

## Project Overview

`audio-tag-writer` is a PyQt6 desktop application for viewing and editing **ID3 metadata** in
audio files (MP3, WAV, OGG, FLAC). It is the audio counterpart to
`C:\Users\juren\Projects\tag-writer`, which performs the same function for IPTC/XMP/EXIF
metadata in image files.

The app provides a form-based UI where an archivist can:
- Load an audio file via file browser or directory navigation
- View audio file info (duration, bitrate, sample rate, format) in a side panel
- Edit a curated set of ID3 fields matching the HSTL archival metadata standard
- Save edited metadata back to the file in-place using Mutagen
- Export/import metadata as JSON
- Navigate between audio files in a directory

---

## Relationship to tag-writer

The architecture directly mirrors tag-writer. Modules are ported where applicable and adapted
where audio-specific behavior differs.

| Aspect | tag-writer | audio-tag-writer |
|--------|-----------|-----------------|
| GUI framework | PyQt6 | PyQt6 (same) |
| Metadata backend | ExifTool (IPTC/XMP) | **Mutagen** (ID3) |
| File types | JPG, TIFF, PNG | MP3, WAV, OGG, FLAC |
| Side panel | Image thumbnail + resolution | Album art (APIC) + audio info (duration, bitrate, etc.) |
| Metadata standard | 11 IPTC fields | 10 ID3 fields (see table below) |
| Config file | `~/.tag_writer_config.json` | `~/.audio_tag_writer_config.json` |
| Package name | `tag_writer` | `audio_tag_writer` |
| Architecture | Mixin composition | Mixin composition (same pattern) |
| External binary | `exiftool.exe` (bundled) | **None** — Mutagen is pure Python |

**Reused verbatim (with minor renames):**
- `config.py` — Config singleton + SingleInstanceChecker
- `constants.py` — APP_VERSION, APP_TIMESTAMP, timeouts
- `theme.py` — ThemeManager + 8 themes
- `theme_mixin.py` — apply_theme, zoom_ui, dark mode
- `updates.py` — GitHub version checker
- `help.py` — About/changelog dialogs (updated app name)
- `window.py` — WindowMixin (geometry save/restore)
- `menu.py` — MenuMixin (adapted for audio-specific actions)

**Adapted (audio-specific changes):**
- `metadata.py` → ID3 field_mappings (10 fields) with Mutagen frame objects instead of ExifTool tags
- `file_utils.py` → filters for `.mp3`, `.wav`, `.ogg`, `.flac` instead of images
- `navigation.py` → same logic, calls `load_file()` for audio files
- `file_ops.py` → save/export/import adapted; rotate/rename removed; add "View All Tags"
- `platform.py` → port verbatim (Windows taskbar icon)

**Replaced (new implementation):**
- `exiftool_utils.py` → **`mutagen_utils.py`** — thin Mutagen wrapper with error handling
- `image_utils.py` → **`audio_utils.py`** — reads duration, bitrate, format from `mutagen.File().info`
- `widgets/image_viewer.py` → `widgets/audio_panel.py` — displays album art (APIC frame) thumbnail + audio file info below
- `widgets/full_image_viewer.py` → removed (no full-size viewer equivalent for audio)
- `widgets/metadata_panel.py` → new field set (10 ID3 fields instead of 11 IPTC)

---

## Metadata Backend: Mutagen

Mutagen is a pure-Python library for reading and writing audio metadata. It replaces ExifTool
as the metadata backend for this project. See `TOOL_COMPARISON_exiftool-vs-ffmpeg.md` for the
full rationale. Key reasons for this choice:

- **In-place writes** — Mutagen rewrites only the tag block; the audio stream is never touched.
  No temp files, no file-replace dance, no subprocess.
- **Full ID3 frame fidelity** — Direct frame-level access (TIT2, TALB, IPLS, TLOC, TOFN, etc.)
  with no normalisation loss. All 9 HSTL fields survive a round-trip.
- **No external binary** — `pip install mutagen`; no `exiftool.exe` to bundle. PyInstaller EXE
  is smaller and simpler.
- **Cover art support** — Mutagen can read and write APIC frames (album art), which ExifTool
  cannot write for audio files.
- **Audio stream info** — `mutagen.File(path).info` exposes `length`, `bitrate`,
  `sample_rate`, `channels` without a separate tool call.

FFmpeg remains the correct tool for the **HSTL Audio Framework batch pipeline** (thumbnail
text-overlay via `drawtext` requires FFmpeg). The two tools serve different roles:

| Tool | Used in | Reason |
|------|---------|--------|
| **Mutagen** | audio-tag-writer GUI | In-place tag editing, no binary, cover art |
| **FFmpeg** | HSTL Audio Framework CLI | Thumbnail overlay + batch metadata embedding |

---

## Module Architecture

```
C:\Users\juren\Projects\audio-tag-writer\
├── src/
│   ├── main.py                             # MainWindow mixin composition + entry point
│   └── audio_tag_writer/
│       ├── __init__.py
│       ├── constants.py                    # APP_VERSION, APP_NAME
│       ├── config.py                       # Config singleton, SingleInstanceChecker
│       ├── platform.py                     # Windows taskbar icon (AppUserModelID)
│       ├── mutagen_utils.py                # open_audio(), safe_get_tag(), AudioFileError
│       ├── file_utils.py                   # get_audio_files(), directory scanning
│       ├── audio_utils.py                  # get_audio_info() — duration, bitrate, format
│       ├── metadata.py                     # MetadataManager — ID3 load/save/export/import
│       ├── theme.py                        # ThemeManager — 8 themes, stylesheet generation
│       ├── menu.py                         # MenuMixin — menu bar + toolbar
│       ├── window.py                       # WindowMixin — geometry save/restore
│       ├── navigation.py                   # NavigationMixin — open, prev/next, load_file
│       ├── file_ops.py                     # FileOpsMixin — save, export, import, view all tags
│       ├── theme_mixin.py                  # ThemeMixin — apply_theme, zoom_ui, dark mode
│       ├── help.py                         # HelpMixin — about, changelog
│       └── updates.py                      # UpdatesMixin — GitHub version checker
│       └── widgets/
│           ├── audio_panel.py              # AudioPanel — album art (APIC) + file info display
│           └── metadata_panel.py           # MetadataPanel — ID3 form (10 fields) + write button
├── assets/
│   └── ICON_atw.ico / ICON_atw.png         # App icon
├── tests/
│   ├── test_metadata.py
│   ├── test_audio_utils.py
│   ├── test_mutagen_utils.py
│   ├── test_file_utils.py
│   └── test_config.py
├── requirements.txt
├── audio-tag-writer.spec                   # PyInstaller spec
├── build_exe.ps1                           # Build script
├── DEVELOPMENT_PLAN.md
└── TOOL_COMPARISON_exiftool-vs-ffmpeg.md
```

Note: no `tools/` directory. No external binary is bundled.

---

## ID3 Field Mappings

These 10 fields form the metadata edit form. They are derived from `audio-tags-09.py` v0.09 and
represent the most user-editable archival fields (static/computed fields are excluded from the UI).

| Form Label | ID3 Frame | Mutagen Class | Source CSV Column |
|-----------|-----------|--------------|------------------|
| **Title** | `TIT2` | `mutagen.id3.TIT2` | `title` |
| **Description** | `COMM` | `mutagen.id3.COMM` | `Description` |
| **Accession Number** | `TALB` | `mutagen.id3.TALB` | `Accession Number` |
| **Speakers** | `IPLS` | `mutagen.id3.IPLS` | `Speakers` |
| **Date Recorded** | `TRDA` | `mutagen.id3.TRDA` | `Date` (ISO 8601) |
| **Restrictions** | `TCOP` | `mutagen.id3.TCOP` | `Restrictions` |
| **Location** | `TLOC` | `mutagen.id3.TLOC` | `Place` |
| **Production/Copyright** | `TPUB` | `mutagen.id3.TPUB` | `Production and Copyright` |
| **Original Filename** | `TOFN` | `mutagen.id3.TOFN` | `Accession Number` + `.mp3` |
| **Credit** | `TXXX:Credit` | `mutagen.id3.TXXX` | `Credit` |

**Static fields** (written by the batch tool, readable but not in the edit form):
- `TIT1` — Grouping: "NARA-HST-SRC Sound Recordings Collection"
- `TPE1` — Artist: "Harry S. Truman Library"
- `ISRC` — Source: "Harry S. Truman Library"
- `WOAS` / `WXXX` — URLs
- `TDAT`, `TYER`, `TORY` — Computed date fragments

### MetadataManager Implementation Notes

- `field_mappings` maps form field names to their primary Mutagen frame class and a list of
  fallback frame IDs to check on read (e.g. `{'description': (COMM, ['TIT3', 'ISBJ'])}`).
- **Read:** `audio = mutagen.mp3.MP3(path)` → `audio.tags['TIT2'].text[0]`
- **Write:** `audio.tags['TIT2'] = TIT2(encoding=3, text=value)` → `audio.tags.update_to_v23()` → `audio.save(v2_version=3)`
- ID3v2.3 enforced on save for maximum player compatibility.
- COMM frames require a `lang` parameter: `COMM(encoding=3, lang='eng', desc='', text=value)`.
- Date stored/displayed as ISO 8601 (`YYYY-MM-DD`); date conversion from `DD-MMM-YY` is the
  batch tool's concern, not this GUI.
- `_sanitize_value()` ported from tag-writer: strip null bytes, normalize line endings,
  strip leading/trailing whitespace, cap at 2000 characters.

---

## mutagen_utils.py

Thin wrapper providing consistent error handling and format detection. Replaces
`exiftool_utils.py`.

```python
class AudioFileError(Exception): ...

def open_audio(path: str) -> mutagen.FileType:
    """Open any supported audio file; raises AudioFileError on failure."""

def safe_get_text(tags, frame_id: str, default: str = '') -> str:
    """Return first text value from an ID3 frame, or default if absent."""

def check_mutagen_available() -> None:
    """Pre-flight: import mutagen; raise AudioFileError with install hint if missing."""
```

No persistent process, no subprocess, no timeouts needed.

---

## audio_utils.py

Reads audio stream properties from `mutagen.File(path).info`:

```python
def get_audio_info(path: str) -> dict:
    return {
        'duration':    '3:42',          # formatted from info.length (seconds)
        'bitrate':     '128 kbps',      # from info.bitrate
        'sample_rate': '44100 Hz',      # from info.sample_rate
        'channels':    'Mono',          # from info.channels (1=Mono, 2=Stereo)
        'format':      'MP3',           # from type(audio).__name__ or path suffix
        'file_size':   '3.6 MB',        # from os.path.getsize()
        'modified':    '2023-11-02',    # from os.path.getmtime()
    }
```

No ExifTool call needed. All data comes from Mutagen + `os.path`.

---

## AudioPanel Widget

Replaces `image_viewer.py`. Mirrors the tag-writer thumbnail panel — album art on top,
file info below — occupying the right column of the main window.

```
┌──────────────────────────┐
│                          │
│      [Album Art]         │  ← APIC frame extracted via Mutagen,
│   scaled to fit ~220px   │    scaled with aspect ratio preserved.
│                          │    Falls back to a generic audio icon
│                          │    if no APIC frame is present.
└──────────────────────────┘
● Art embedded             │  ← status indicator (green dot = art present,
                           │    grey = no art)
SR59-185.mp3
Duration:    3:42
Bitrate:     128 kbps
Sample Rate: 44100 Hz
Channels:    Mono
Format:      MP3
File Size:   3.6 MB
Modified:    2023-11-02
```

**Album art extraction:**
- Read APIC frame via `audio.tags.getall('APIC')` — use first frame if multiple exist.
- Convert raw bytes to `QPixmap` via `QPixmap.loadFromData(apic.data)`.
- Scale with `Qt.KeepAspectRatio` to fit the panel width (~220 px).
- If no APIC frame: display a generic audio file icon from `assets/`.

**File info** sourced from `audio_utils.get_audio_info()` (Mutagen + `os.path`).

**Optional (Phase 5+):** Play/Stop button using `QMediaPlayer` / `QAudioOutput` from
`PyQt6.QtMultimedia`. Defer to a future phase; leave a clearly marked stub.

---

## UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Menu Bar (File, Edit, View, Tools, Help)                         │
├──────────────────────────────────────────────────────────────────┤
│ Toolbar (Open, Save, Export, Import, Theme)                      │
├─────────────────────────────────────┬────────────────────────────┤
│  MetadataPanel (Form)               │  AudioPanel (Right)        │
│                                     │  ┌──────────────────────┐  │
│  Title:       [__________________]  │  │                      │  │
│  Description: [__________________]  │  │    [Album Art]       │  │
│               0/1000 characters     │  │    APIC frame        │  │
│  Accession #: [__________________]  │  │    thumbnail         │  │
│  Speakers:    [__________________]  │  │                      │  │
│  Date:        [__________________]  │  └──────────────────────┘  │
│  Restrictions:[__________________]  │  ● Art embedded / No art   │
│  Location:    [__________________]  │                            │
│  Production:  [__________________]  │  SR59-185.mp3              │
│  Orig File:   [__________________]  │  Duration:    3:42         │
│  Credit:      [__________________]  │  Bitrate:     128 kbps     │
│                                     │  Sample Rate: 44100 Hz     │
│  [  Write Metadata  ]               │  Channels:    Mono         │
│                                     │  Format:      MP3          │
│                                     │  File Size:   3.6 MB       │
│                                     │  Modified:    2023-11-02   │
├─────────────────────────────────────┴────────────────────────────┤
│ Status bar (filename · format · file size)                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Config Persistence

`~/.audio_tag_writer_config.json` stores:
```json
{
  "selected_file": "...",
  "last_directory": "...",
  "recent_files": [],
  "recent_directories": [],
  "dark_mode": false,
  "current_theme": "Default Light",
  "ui_zoom_factor": 1.0,
  "window_geometry": [100, 100, 1024, 640],
  "auto_check_updates": true,
  "skipped_versions": []
}
```

---

## Development Phases

### Phase 1 — Scaffold + Core (working shell)

**Goal:** App launches, Mutagen is available, a file can be opened.

1. Create project directory structure (see Module Architecture above)
2. `constants.py` — APP_VERSION=`0.1.0`, APP_NAME=`audio-tag-writer`
3. `config.py` — port from tag-writer; change config filename to `audio_tag_writer_config.json`;
   remove ExifTool-specific state keys
4. `mutagen_utils.py` — `open_audio()`, `safe_get_text()`, `check_mutagen_available()`
5. `platform.py` — port verbatim from tag-writer
6. `file_utils.py` — `get_audio_files(directory)` filtering `.mp3 .wav .ogg .flac`
7. `main.py` — bare MainWindow shell (mixin stubs), app start, Mutagen pre-flight check
8. `requirements.txt` — PyQt6, mutagen, pyqt-app-info

**Deliverable:** `python src/main.py` launches an empty window; Mutagen import confirmed.

---

### Phase 2 — Audio Info + Metadata Read

**Goal:** Load an audio file and display its technical info and current tags.

1. `audio_utils.py` — `get_audio_info(path)` → dict with duration, bitrate, sample rate,
   channels, format, file size, modified date (via Mutagen + os.path)
2. `metadata.py` — `MetadataManager` with `field_mappings` for 9 ID3 fields;
   `load_from_file(path)` reads frames via Mutagen; `_sanitize_value()` ported from tag-writer
3. `widgets/audio_panel.py` — `AudioPanel(QWidget)` with album art display (APIC frame →
   `QPixmap.loadFromData`; fallback to generic icon) + status indicator + file info labels;
   `display_audio(path, info_dict, tags)` updates art and labels
4. `widgets/metadata_panel.py` — `MetadataPanel(QWidget)` with 10 `QLineEdit` / `QTextEdit`
   fields; `update_from_manager(manager)` populates form (read-only display for now)
5. Wire `NavigationMixin.load_file()` stub: calls `MetadataManager.load_from_file()`,
   `AudioPanel.display_audio()`, `MetadataPanel.update_from_manager()`

**Deliverable:** Open an MP3 → audio info panel and metadata form are populated from file.

---

### Phase 3 — Metadata Write + Export/Import

**Goal:** Edit fields and save tags back to the file in-place.

1. `MetadataPanel` — enable editing; add "Write Metadata" button;
   `update_manager_from_ui()` pushes form values back to manager;
   character count on Description field (0/1000)
2. `MetadataManager.save_to_file(path)` — builds Mutagen frame objects for all 9 fields;
   calls `audio.tags.update_to_v23()` and `audio.save(v2_version=3)`
3. `file_ops.py` — `on_save()`, `on_export()` (JSON), `on_import()` (JSON),
   `on_view_all_tags()` (table dialog listing all raw Mutagen frames with values)
4. Connect toolbar/menu Save, Export, Import actions

**Deliverable:** Full round-trip: open → change title → Write Metadata → reopen → verify.

---

### Phase 4 — Navigation + Full Menu

**Goal:** Browse a directory of audio files with keyboard navigation.

1. `navigation.py` — port from tag-writer: `on_open()`, `on_previous()`, `on_next()` with
   looping; `load_file()` wired to `audio_utils` + `metadata`
2. `menu.py` — full menu bar (File > Open/Save/Export/Import/Recent Files; Edit; View >
   Theme/Zoom; Tools > View All Tags; Help > About/Changelog)
3. `window.py` — geometry save/restore on close
4. Arrow-key navigation in main window
5. Recent files (max 10) and recent directories (max 10) menus
6. Status bar: current filename · format · file size

**Deliverable:** Can page through a folder of MP3s with ← → keys; recent files persist.

---

### Phase 5 — Themes + Polish

**Goal:** Full visual parity with tag-writer.

1. `theme.py` — port ThemeManager verbatim from tag-writer (all 8 themes)
2. `theme_mixin.py` — port ThemeMixin; apply_theme, zoom_ui (Ctrl+/Ctrl-), Ctrl+D dark mode
3. `help.py` — About dialog (pyqt-app-info), Changelog dialog
4. `updates.py` — port GitHub version checker; update repo URL to audio-tag-writer
5. `config.py` — SingleInstanceChecker (lock file at `%TEMP%/audio-tag-writer.lock`)
6. `platform.py` — Windows AppUserModelID for taskbar icon

**Deliverable:** All 8 themes work; zoom works; about dialog shows correct version.

---

### Phase 6 — Tests + Distribution

**Goal:** Passing test suite and distributable EXE.

1. Unit tests:
   - `test_mutagen_utils.py` — open_audio() error handling, safe_get_text() edge cases
   - `test_metadata.py` — field_mappings coverage, sanitize_value, JSON round-trip,
     ID3v2.3 enforcement on save (using real test MP3s from `HST-Metadata/Audio/Test-mp3s/`)
   - `test_audio_utils.py` — duration formatting, bitrate string formatting, mono/stereo label
   - `test_file_utils.py` — extension filtering, directory scan ordering
   - `test_config.py` — singleton, read/write, defaults
2. `audio-tag-writer.spec` — PyInstaller spec; no binary to bundle; include `assets/`
3. `build_exe.ps1` — `pyinstaller audio-tag-writer.spec`
4. GitHub Actions CI — version-check workflow (mirror tag-writer's `.github/workflows/`)

**Deliverable:** `pytest` green; `audio-tag-writer.exe` runs standalone without any
external tools installed.

---

## Key Design Decisions

### Mutagen as metadata backend (not ExifTool, not FFmpeg)

See `TOOL_COMPARISON_exiftool-vs-ffmpeg.md` for the full analysis. Summary:

- ExifTool cannot write cover art (APIC frames) — a blocking limitation for future use.
- FFmpeg requires a full remux per write (slow, subprocess-heavy, risk of silent frame loss
  for non-standard ID3 frames like IPLS, TLOC, TOFN).
- Mutagen writes in-place, handles all 9 HSTL ID3 frames natively, needs no external binary,
  and is the standard Python library for this task.

FFmpeg remains the correct tool for the HSTL Audio Framework batch pipeline (thumbnail
text-overlay is unique to FFmpeg).

### ID3v2.3 enforced on save (not v2.4)

ID3v2.4 has broader encoding support but inconsistent player compatibility (Windows Explorer,
iTunes, VLC all have edge-case v2.4 bugs). v2.3 is the safer choice for archival files
destined for NARA upload. Mutagen makes this explicit: `audio.tags.update_to_v23(); audio.save(v2_version=3)`.

### No audio playback in Phase 1–5

PyQt6 ships `QMediaPlayer`/`QAudioOutput` with no extra deps, so playback is feasible.
Deferred because it adds testing complexity and is not needed for the core tagging use case.
Leave a clearly marked stub in `AudioPanel`.

### 10 fields, not all 22

The `audio-tags-09.py` tag set includes static/computed fields (URLs, script name, DDMM date
fragments) that an archivist would never manually edit. The form exposes only the 10 fields
relevant to record-by-record correction. The "View All Tags" dialog surfaces the rest read-only.

---

## Dependencies

```
mutagen>=1.47.0
PyQt6==6.4.2
PyQt6-sip==13.4.1
pyqt-app-info @ git+https://github.com/juren53/pyqt-app-info.git
```

No Pillow (no image thumbnailing). No PyExifTool. No external binary.

---

## Relationship to HSTL Audio Framework

`audio-tag-writer` and the HSTL Audio Framework (`HST-Metadata/Audio`) serve **different roles**:

| Tool | Purpose | Backend |
|------|---------|---------|
| **HSTL Audio Framework** | Batch CLI — CSV → ID3 tags + thumbnails → 3,757 files | FFmpeg |
| **audio-tag-writer** | Single-file GUI — inspect and correct individual files post-batch | Mutagen |

Typical workflow: run the batch framework to tag all files, then use audio-tag-writer to
spot-check and correct individual records where the CSV data was incomplete or incorrect.

---

Updated: 2026-04-21
